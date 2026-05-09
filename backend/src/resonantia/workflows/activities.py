"""Temporal activity implementations for all Resonantia workflows.

Each function decorated with @activity.defn is registered with the Temporal
worker and executed as an activity inside a workflow.  Activities contain the
*real* side-effecting logic (LLM calls, DB queries, tool execution, etc.).

SECURITY NOTE: The generate_code, execute_in_sandbox, and
review_for_hallucinations activities have been deliberately removed.
Code generation + subprocess execution is unsafe and unauditable.
All tool execution now goes through registered TOOL_HANDLERS only.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any

from temporalio import activity

logger = logging.getLogger(__name__)


# ============================================================================
# Helper types (plain dicts / dataclass-compatible for Temporal serialisation)
# ============================================================================

class ToolDescription(dict):
    """Thin wrapper around dict for clarity; serialised as JSON-compatible dict."""


# ============================================================================
# Agent workflow activities (safe — no code generation / subprocess)
# ============================================================================


@activity.defn
async def call_llm_activity(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
) -> dict[str, Any]:
    """Call the LLM with messages and tool definitions.

    Returns a dict with ``content`` (str) and ``tool_calls`` (list of dicts).
    All values are JSON-serializable for Temporal.
    """
    from openai import AsyncOpenAI

    from resonantia.config import get_settings
    from resonantia.services.guardrails import GUARDRAIL_SYSTEM_PROMPT

    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    full_messages = [{"role": "system", "content": GUARDRAIL_SYSTEM_PROMPT}] + messages

    kwargs: dict[str, Any] = {
        "model": settings.llm_model,
        "max_tokens": 4096,
        "messages": full_messages,
    }

    # Convert tool schemas to OpenAI function format if provided
    if tools:
        openai_tools = []
        for t in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                },
            })
        kwargs["tools"] = openai_tools

    response = await client.chat.completions.create(**kwargs)
    choice = response.choices[0]

    result: dict[str, Any] = {
        "content": choice.message.content or "",
        "tool_calls": [],
    }

    if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
        for tc in choice.message.tool_calls:
            result["tool_calls"].append({
                "id": tc.id,
                "name": tc.function.name,
                "arguments": json.loads(tc.function.arguments),
            })

    return result


@activity.defn
async def execute_tool_activity(
    tool_name: str,
    tool_args: dict[str, Any],
    org_id: str,
) -> str:
    """Execute a registered tool handler and return the JSON result.

    Uses the TOOL_HANDLERS registry from tool_executor — no arbitrary
    code execution.
    """
    from resonantia.services.tool_executor import execute_tool

    logger.info("execute_tool_activity: tool=%s, org_id=%s", tool_name, org_id)
    result = await execute_tool(tool_name, tool_args, org_id=org_id)
    return result


@activity.defn
async def persist_conversation_activity(
    conversation_id: str,
    org_id: str,
    messages: list[dict[str, Any]],
) -> None:
    """Persist conversation messages to the database.

    This ensures the Temporal path writes the same DB records as the
    direct path in agent.py.
    """
    from resonantia.db.session import async_session_factory
    from resonantia.models.conversation import Conversation, ConversationMessage

    logger.info(
        "persist_conversation_activity: conv=%s, org=%s, msgs=%d",
        conversation_id, org_id, len(messages),
    )

    async with async_session_factory() as session:
        conv = await session.get(Conversation, uuid.UUID(conversation_id))
        if not conv:
            logger.warning("Conversation %s not found, skipping persist", conversation_id)
            return

        # Only persist messages not already in the DB.  Count existing
        # messages and persist the tail.
        from sqlalchemy import select, func

        existing_count_result = await session.execute(
            select(func.count()).select_from(ConversationMessage).where(
                ConversationMessage.conversation_id == conv.id
            )
        )
        existing_count = existing_count_result.scalar() or 0

        new_messages = messages[existing_count:]
        for msg in new_messages:
            role = msg.get("role", "user")
            content = msg.get("content")
            tool_calls = msg.get("tool_calls")
            tool_call_id = msg.get("tool_call_id")

            db_msg = ConversationMessage(
                conversation_id=conv.id,
                role=role,
                content=content if isinstance(content, str) else json.dumps(content) if content else None,
                tool_calls=tool_calls,
                tool_call_id=tool_call_id,
            )
            session.add(db_msg)

        await session.commit()


@activity.defn
async def evaluate_result(step: dict[str, Any], output: str) -> dict[str, Any]:
    """Evaluate whether the execution output satisfies the plan step."""
    from openai import AsyncOpenAI

    from resonantia.config import get_settings

    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    response = await client.chat.completions.create(
        model=settings.llm_model,
        max_tokens=1024,
        messages=[
            {
                "role": "system",
                "content": (
                    "You evaluate code execution results. Respond with JSON: "
                    '{"success": bool, "output": "summary", "revised_step": null | step_dict}'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Step: {json.dumps(step)}\n"
                    f"Execution output:\n{output[:3000]}\n\n"
                    "Evaluate. Respond ONLY with JSON."
                ),
            },
        ],
    )

    text = response.choices[0].message.content or ""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"success": True, "output": output[:500], "revised_step": None}


@activity.defn
async def compile_results(outputs: list[str]) -> str:
    """Compile all step outputs into a coherent final response."""
    from openai import AsyncOpenAI

    from resonantia.config import get_settings

    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    combined = "\n---\n".join(outputs)

    response = await client.chat.completions.create(
        model=settings.llm_model,
        max_tokens=4096,
        messages=[
            {
                "role": "system",
                "content": (
                    "You synthesise multiple step outputs into a single, clear, "
                    "well-structured response for a scientist. Include relevant data, "
                    "tables, and conclusions."
                ),
            },
            {"role": "user", "content": f"Step outputs:\n{combined}\n\nCompile."},
        ],
    )

    return response.choices[0].message.content or ""


# ============================================================================
# Plate mapping workflow activities
# ============================================================================


@activity.defn
async def validate_source_plates(plate_ids: list[str]) -> dict[str, Any]:
    """Check that all source plates exist in inventory.

    Returns a ValidationResult-compatible dict.
    """
    logger.info("validate_source_plates: %s", plate_ids)
    errors: list[str] = []
    warnings: list[str] = []

    if not plate_ids:
        errors.append("No source plates provided")
    else:
        for idx, pid in enumerate(plate_ids):
            if not isinstance(pid, str) or not pid.strip():
                errors.append(f"Plate ID at index {idx} is empty or invalid")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


@activity.defn
async def generate_mapping(
    source_ids: list[str],
    destination_id: str,
    mode: str,
) -> list[dict[str, Any]]:
    """Generate well-to-well mappings based on the requested mode.

    Supported modes: direct, cherry_pick, serial_dilution, quadrant.
    """
    logger.info(
        "generate_mapping: sources=%s, dest=%s, mode=%s",
        source_ids, destination_id, mode,
    )

    rows = "ABCDEFGH"
    cols = range(1, 13)  # 96-well default
    mappings: list[dict[str, Any]] = []

    if mode == "direct":
        # 1:1 mapping — first source plate wells to destination
        for r in rows:
            for c in cols:
                well = f"{r}{c}"
                mappings.append(
                    {
                        "source_plate": source_ids[0] if source_ids else "",
                        "source_well": well,
                        "destination_well": well,
                        "volume_ul": 10.0,
                        "sample_id": None,
                    }
                )
    elif mode == "quadrant":
        # Four 96-well sources into one 384-well destination
        quadrant_offsets = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for idx, src_id in enumerate(source_ids[:4]):
            r_off, c_off = quadrant_offsets[idx]
            for ri, r in enumerate(rows):
                for ci, c in enumerate(cols):
                    dest_row = chr(ord("A") + ri * 2 + r_off)
                    dest_col = ci * 2 + c_off + 1
                    mappings.append(
                        {
                            "source_plate": src_id,
                            "source_well": f"{r}{c}",
                            "destination_well": f"{dest_row}{dest_col}",
                            "volume_ul": 5.0,
                            "sample_id": None,
                        }
                    )
    elif mode == "cherry_pick":
        from resonantia.services.plate_mapper import cherry_pick as _cherry_pick

        # Build source_plates structure expected by the service
        source_plates = [
            {"plate_name": sid, "wells": {f"{r}{c}": {"sample": f"{sid}_{r}{c}"} for r in rows for c in cols}}
            for sid in source_ids
        ]
        # Use hit_list from caller or default to first column
        hit_list = [f"{r}1" for r in rows]  # default: column 1
        result = _cherry_pick(source_plates, hit_list)
        for wm in result.get("well_mappings", []):
            mappings.append(
                {
                    "source_plate": wm.get("source_plate", ""),
                    "source_well": wm.get("source_well", ""),
                    "destination_well": wm.get("destination_well", ""),
                    "volume_ul": 10.0,
                    "sample_id": None,
                }
            )

    elif mode == "serial_dilution":
        from resonantia.services.plate_mapper import serial_dilution as _serial_dilution

        compound = source_ids[0] if source_ids else "COMPOUND"
        result = _serial_dilution(
            compound=compound,
            start_concentration=10000.0,
            dilution_factor=3.0,
            num_points=min(12, len(cols)),
            replicates=1,
        )
        for entry in result.get("layout", []):
            mappings.append(
                {
                    "source_plate": source_ids[0] if source_ids else "",
                    "source_well": entry.get("well", ""),
                    "destination_well": entry.get("well", ""),
                    "volume_ul": 10.0,
                    "sample_id": entry.get("compound"),
                }
            )

    else:
        # Unknown mode — fall back to direct 1:1 copy
        for r in rows:
            for c in cols:
                well = f"{r}{c}"
                mappings.append(
                    {
                        "source_plate": source_ids[0] if source_ids else "",
                        "source_well": well,
                        "destination_well": well,
                        "volume_ul": 10.0,
                        "sample_id": None,
                    }
                )

    return mappings


@activity.defn
async def validate_mapping(mappings: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate mappings for conflicts (duplicate destinations, etc.)."""
    logger.info("validate_mapping: %d mappings", len(mappings))
    errors: list[str] = []
    warnings: list[str] = []

    seen_dest: set[str] = set()
    for m in mappings:
        dw = m.get("destination_well", "")
        if dw in seen_dest:
            errors.append(f"Duplicate destination well: {dw}")
        seen_dest.add(dw)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


@activity.defn
async def generate_worklist(
    mappings: list[dict[str, Any]],
    fmt: str = "csv",
) -> bytes:
    """Generate an instrument worklist file from mappings."""
    logger.info("generate_worklist: %d mappings, format=%s", len(mappings), fmt)

    from resonantia.services.plate_mapper import generate_worklist as _generate_worklist

    # Map the fmt parameter to the service's expected format names
    format_map = {
        "csv": "echo",
        "echo": "echo",
        "hamilton": "hamilton",
        "opentrons": "opentrons",
    }
    service_fmt = format_map.get(fmt, "echo")

    # Convert activity mapping dicts to the format expected by the service
    # (the service expects "volume" key, activity uses "volume_ul")
    service_mappings = []
    for m in mappings:
        sm = dict(m)
        if "volume_ul" in sm and "volume" not in sm:
            sm["volume"] = sm.pop("volume_ul")
        service_mappings.append(sm)

    worklist_str = _generate_worklist(service_mappings, fmt=service_fmt)
    return worklist_str.encode("utf-8")


@activity.defn
async def save_plate_map(
    mappings: list[dict[str, Any]],
    worklist: bytes,
) -> str:
    """Persist plate map and worklist to the database / file store.

    Returns the generated plate_map_id.
    """
    from resonantia.config import get_settings

    plate_map_id = uuid.uuid4().hex
    logger.info(
        "save_plate_map: id=%s, mappings=%d, worklist_bytes=%d",
        plate_map_id, len(mappings), len(worklist),
    )

    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save mappings as JSON
    mappings_path = upload_dir / f"plate_map_{plate_map_id}.json"
    with open(mappings_path, "w") as f:
        json.dump({"plate_map_id": plate_map_id, "mappings": mappings}, f, indent=2)

    # Save worklist file
    worklist_bytes = worklist if isinstance(worklist, bytes) else worklist.encode("utf-8")
    worklist_path = upload_dir / f"worklist_{plate_map_id}.csv"
    with open(worklist_path, "wb") as f:
        f.write(worklist_bytes)

    logger.info("Saved plate map to %s and worklist to %s", mappings_path, worklist_path)
    return plate_map_id


# ============================================================================
# Data processing workflow activities
# ============================================================================


@activity.defn
async def load_experiment_data(experiment_id: str) -> dict[str, Any]:
    """Fetch raw experiment data from the file store (or database when available)."""
    from resonantia.config import get_settings

    logger.info("load_experiment_data: %s", experiment_id)

    settings = get_settings()

    # Try to load from the results directory first (file-based storage)
    results_dir = os.path.join(settings.upload_dir, "results")
    experiment_path = os.path.join(results_dir, f"{experiment_id}.json")
    if os.path.isfile(experiment_path):
        with open(experiment_path) as f:
            return json.load(f)

    # Try plate_maps directory
    plate_map_path = os.path.join(settings.upload_dir, f"plate_map_{experiment_id}.json")
    if os.path.isfile(plate_map_path):
        with open(plate_map_path) as f:
            return json.load(f)

    # Nothing found — return empty structure so downstream activities can handle it
    logger.warning("No experiment data found for %s", experiment_id)
    return {
        "experiment_id": experiment_id,
        "raw_data": [],
        "metadata": {},
    }


@activity.defn
async def run_processing(
    data: dict[str, Any],
    processing_type: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Run the requested analysis on experiment data.

    Supported types:
    - dose_response: 4-parameter logistic (4PL) curve fitting
    - plate_normalization: Z-score, percent-of-control
    - qpcr: delta-delta Ct method
    """
    logger.info("run_processing: type=%s", processing_type)
    activity.heartbeat(f"starting {processing_type}")

    if processing_type == "dose_response":
        from resonantia.services.data_processor import fit_dose_response

        concentrations = params.get("concentrations") or data.get("concentrations", [])
        responses = params.get("responses") or data.get("responses", [])

        if not concentrations or not responses:
            return {
                "type": "dose_response",
                "summary": {"error": "No concentration/response data provided"},
                "curve_data": [],
            }

        fit_result = fit_dose_response(concentrations, responses)

        if not fit_result.get("success"):
            return {
                "type": "dose_response",
                "summary": {"error": fit_result.get("error", "Curve fitting failed")},
                "curve_data": [],
            }

        return {
            "type": "dose_response",
            "summary": {
                "ec50": fit_result["parameters"]["ec50"],
                "hill_slope": fit_result["parameters"]["hill_slope"],
                "top": fit_result["parameters"]["top"],
                "bottom": fit_result["parameters"]["bottom"],
                "r_squared": fit_result["r_squared"],
            },
            "curve_data": fit_result["fitted_values"],
            "concentrations": concentrations,
            "responses": responses,
            "standard_errors": fit_result.get("standard_errors", {}),
        }

    elif processing_type == "plate_normalization":
        from resonantia.services.data_processor import calculate_z_prime, normalize_plate

        method = params.get("method", "z-score")
        raw_data = params.get("raw_data") or data.get("raw_data", [])

        if not raw_data:
            return {
                "type": "plate_normalization",
                "method": method,
                "summary": {"error": "No raw plate data provided"},
                "normalized_data": [],
            }

        norm_result = normalize_plate(
            raw_data,
            method=method,
            positive_control_wells=params.get("positive_control_wells"),
            negative_control_wells=params.get("negative_control_wells"),
        )

        if "error" in norm_result:
            return {
                "type": "plate_normalization",
                "method": method,
                "summary": {"error": norm_result["error"]},
                "normalized_data": [],
            }

        # Optionally compute Z-prime if control wells are provided
        z_prime_result = None
        pos_wells = params.get("positive_control_wells")
        neg_wells = params.get("negative_control_wells")
        if pos_wells and neg_wells:
            import numpy as np
            arr = np.asarray(raw_data, dtype=float)
            pos_vals = [float(arr[r][c]) for r, c in pos_wells]
            neg_vals = [float(arr[r][c]) for r, c in neg_wells]
            z_prime_result = calculate_z_prime(pos_vals, neg_vals)

        return {
            "type": "plate_normalization",
            "method": method,
            "summary": {
                "plate_count": 1,
                "z_prime": z_prime_result.get("z_prime") if z_prime_result else None,
                "z_prime_quality": z_prime_result.get("quality") if z_prime_result else None,
            },
            "normalized_data": norm_result.get("normalized", []),
        }

    elif processing_type == "qpcr":
        reference_gene = params.get("reference_gene", "GAPDH")
        control_sample = params.get("control_sample", "")
        ct_values = params.get("ct_values") or data.get("ct_values", {})

        if not ct_values:
            return {
                "type": "qpcr",
                "summary": {"error": "No Ct values provided", "reference_gene": reference_gene},
                "delta_delta_ct": [],
                "fold_changes": [],
            }

        # Delta-delta Ct calculation
        import math

        delta_ct: dict[str, float] = {}
        for sample, genes in ct_values.items():
            if not isinstance(genes, dict):
                continue
            target_ct = None
            ref_ct = None
            for gene, ct in genes.items():
                if gene == reference_gene:
                    ref_ct = float(ct) if ct is not None else None
                else:
                    target_ct = float(ct) if ct is not None else None
            if target_ct is not None and ref_ct is not None:
                delta_ct[sample] = target_ct - ref_ct

        # Delta-delta Ct (relative to control)
        control_delta = delta_ct.get(control_sample, 0.0)
        delta_delta_ct_values = []
        fold_changes = []
        for sample, dct in delta_ct.items():
            ddct = dct - control_delta
            fc = 2.0 ** (-ddct)
            delta_delta_ct_values.append({"sample": sample, "delta_delta_ct": ddct})
            fold_changes.append({"sample": sample, "fold_change": fc})

        return {
            "type": "qpcr",
            "summary": {"reference_gene": reference_gene, "control_sample": control_sample},
            "delta_delta_ct": delta_delta_ct_values,
            "fold_changes": fold_changes,
        }

    else:
        return {
            "type": processing_type,
            "summary": {"status": "unsupported processing type"},
        }


@activity.defn
async def generate_figures(results: dict[str, Any]) -> list[str]:
    """Generate plots / figures from processing results.

    Returns a list of figure file paths (or placeholder keys when no data).
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from resonantia.config import get_settings

    logger.info("generate_figures: type=%s", results.get("type"))

    settings = get_settings()
    fig_dir = os.path.join(settings.upload_dir, "figures")
    os.makedirs(fig_dir, exist_ok=True)

    figures: list[str] = []
    proc_type = results.get("type", "")

    if proc_type == "dose_response" and results.get("curve_data"):
        fig, ax = plt.subplots(figsize=(8, 5))
        fitted = results["curve_data"]
        concentrations = results.get("concentrations", list(range(len(fitted))))
        responses = results.get("responses", [])
        if responses:
            ax.scatter(concentrations, responses, c="#D4A843", s=40, zorder=3, label="Observed")
        ax.plot(concentrations, fitted, "b-", linewidth=2, label="Fitted 4PL")
        ax.set_xlabel("Concentration")
        ax.set_ylabel("Response")
        summary = results.get("summary", {})
        ec50 = summary.get("ec50", "N/A")
        r2 = summary.get("r_squared", "N/A")
        ax.set_title(f"Dose-Response Curve (EC50={ec50}, R²={r2})")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig_path = os.path.join(fig_dir, f"dr_{uuid.uuid4().hex[:8]}.png")
        fig.savefig(fig_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        figures.append(fig_path)

    elif proc_type == "plate_normalization" and results.get("normalized_data"):
        fig, ax = plt.subplots(figsize=(8, 5))
        data = results["normalized_data"]
        if isinstance(data, list) and len(data) > 0:
            flat = [v for row in data for v in row] if isinstance(data[0], list) else data
            ax.hist(flat, bins=30, color="#D4A843", alpha=0.7, edgecolor="#333")
        method = results.get("method", "")
        ax.set_xlabel("Normalized Value")
        ax.set_ylabel("Count")
        ax.set_title(f"Plate Normalization ({method})")
        ax.grid(True, alpha=0.3)
        fig_path = os.path.join(fig_dir, f"norm_{uuid.uuid4().hex[:8]}.png")
        fig.savefig(fig_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        figures.append(fig_path)

    elif proc_type == "qpcr" and results.get("fold_changes"):
        fig, ax = plt.subplots(figsize=(8, 5))
        fc_data = results["fold_changes"]
        samples = [fc["sample"] for fc in fc_data]
        values = [fc["fold_change"] for fc in fc_data]
        bars = ax.bar(samples, values, color="#D4A843", edgecolor="#333", alpha=0.8)
        ax.axhline(y=1.0, color="red", linestyle="--", alpha=0.5, label="Baseline (1x)")
        ax.set_xlabel("Sample")
        ax.set_ylabel("Fold Change")
        ax.set_title("qPCR Fold Change (ΔΔCt)")
        ax.legend()
        ax.grid(True, alpha=0.3, axis="y")
        if len(samples) > 6:
            plt.xticks(rotation=45, ha="right")
        fig_path = os.path.join(fig_dir, f"qpcr_{uuid.uuid4().hex[:8]}.png")
        fig.savefig(fig_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        figures.append(fig_path)

    if not figures:
        figures.append(f"fig_{uuid.uuid4().hex[:8]}")  # fallback placeholder key

    return figures


@activity.defn
async def save_results(
    experiment_id: str,
    results: dict[str, Any],
    figure_keys: list[str],
) -> str:
    """Persist processing results and figure references to the file store."""
    from datetime import datetime, timezone

    from resonantia.config import get_settings

    result_id = uuid.uuid4().hex
    logger.info(
        "save_results: experiment=%s, result=%s, figures=%d",
        experiment_id, result_id, len(figure_keys),
    )

    settings = get_settings()
    results_dir = os.path.join(settings.upload_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    payload = {
        "result_id": result_id,
        "experiment_id": experiment_id,
        "results": results,
        "figure_keys": figure_keys,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    result_path = os.path.join(results_dir, f"{result_id}.json")
    with open(result_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)

    logger.info("Saved processing results to %s", result_path)
    return result_id
