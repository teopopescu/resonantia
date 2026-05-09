"""Execute agentic tools against the real database.

When the LLM decides to call a tool, this module runs it and returns
structured results that get fed back into the conversation.

All handlers accept an org_id parameter for multi-tenant isolation.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Any

from sqlalchemy import select, func, cast, String, or_
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.db.session import async_session_factory
from resonantia.models.sample import Sample
from resonantia.models.plate import PlateMap
from resonantia.models.experiment import Experiment
from resonantia.models.microscopy import MicroscopyImage
from resonantia.models.eln_entry import ELNEntry
from resonantia.models.protocol import Protocol, ProtocolStep
from resonantia.services.output_validator import (
    ToolError,
    ToolResult,
    check_tenant_refs,
    validate_tool_args,
)

logger = logging.getLogger(__name__)


def _serialize(obj: Any) -> Any:
    """Make objects JSON-serializable."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if hasattr(obj, "__dict__"):
        return {k: _serialize(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [_serialize(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj


def _extract_source_refs(args: dict[str, Any]) -> list[str]:
    """Pull entity IDs from tool arguments for ToolResult.source_refs."""
    refs: list[str] = []
    for key, value in args.items():
        if key.endswith("_id") and isinstance(value, str) and value:
            refs.append(value)
    return refs


async def _get_tool_schema(tool_name: str) -> dict[str, Any] | None:
    """Load a tool's input_schema from the Redis registry."""
    try:
        from resonantia.services.tool_registry import get_tool, tool_schema_to_anthropic
        tool = await get_tool(tool_name)
        if tool is not None:
            anthropic = tool_schema_to_anthropic(tool)
            return anthropic.get("input_schema")
    except Exception:
        # Redis unavailable; skip schema validation
        logger.debug("Could not load schema for %s from registry", tool_name)
    return None


async def execute_tool_typed(
    tool_name: str,
    tool_input: dict[str, Any],
    org_id: str = "org_default",
) -> ToolResult | ToolError:
    """Execute a tool and return a typed ``ToolResult`` or ``ToolError``.

    Validation pipeline (runs before execution):
    1. Schema validation against the tool's registered JSON schema
    2. Cross-tenant entity reference check
    3. Tool execution with system-error masking
    """
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return ToolError(
            tool_name=tool_name,
            error_type="validation",
            message=f"Unknown tool: {tool_name}",
            retry_allowed=False,
        )

    # --- Step 1: Schema validation ---
    schema = await _get_tool_schema(tool_name)
    if schema is not None:
        validated = validate_tool_args(tool_name, tool_input, schema)
        if isinstance(validated, ToolError):
            return validated

    # --- Step 2: Cross-tenant entity reference check ---
    # Only check if there are any *_id fields with UUID-looking values
    id_fields = {k: v for k, v in tool_input.items() if k.endswith("_id") and isinstance(v, str)}
    if id_fields:
        try:
            async with async_session_factory() as session:
                tenant_err = await check_tenant_refs(tool_input, org_id, session)
                if tenant_err is not None:
                    tenant_err.tool_name = tool_name
                    return tenant_err
        except Exception:
            logger.exception("Tenant ref check failed for %s", tool_name)
            # Don't block execution if DB check itself fails
            pass

    # --- Step 3: Execute ---
    try:
        result = await handler(tool_input, org_id)
        serialized = _serialize(result)
        return ToolResult(
            tool_name=tool_name,
            data=serialized if isinstance(serialized, dict) else {"result": serialized},
            source_refs=_extract_source_refs(tool_input),
        )
    except Exception:
        logger.exception("Tool execution failed: %s", tool_name)
        return ToolError(
            tool_name=tool_name,
            error_type="system",
            message="Internal error",
            retry_allowed=False,
        )


async def execute_tool(tool_name: str, tool_input: dict[str, Any], org_id: str = "org_default") -> str:
    """Execute a tool by name and return a JSON string result.

    This is the backward-compatible entry point for ``agent.py``.
    Internally delegates to :func:`execute_tool_typed` and serializes the
    typed envelope back to a JSON string.
    """
    typed = await execute_tool_typed(tool_name, tool_input, org_id)

    if isinstance(typed, ToolResult):
        return json.dumps(typed.data, default=str)
    else:
        # ToolError -- return as a JSON object the agent loop can read
        return json.dumps(
            {"error": typed.message, "error_type": typed.error_type, "retry_allowed": typed.retry_allowed},
            default=str,
        )


# ---------------------------------------------------------------------------
# Tool handlers — each queries the real database, scoped by org_id
# ---------------------------------------------------------------------------

async def _lookup_sample(params: dict, org_id: str = "org_default") -> dict:
    """Look up samples by barcode, name, or lot number."""
    query = params.get("query", "")
    search_by = params.get("search_by", "barcode")

    async with async_session_factory() as session:
        if search_by == "barcode":
            stmt = select(Sample).where(Sample.org_id == org_id, Sample.barcode.ilike(f"%{query}%"))
        elif search_by == "lot":
            stmt = select(Sample).where(Sample.org_id == org_id, Sample.lot_number.ilike(f"%{query}%"))
        else:
            stmt = select(Sample).where(Sample.org_id == org_id, Sample.name.ilike(f"%{query}%"))

        result = await session.execute(stmt.limit(20))
        samples = result.scalars().all()

        if not samples:
            return {"found": 0, "message": f"No samples found matching '{query}' (searched by {search_by})"}

        return {
            "found": len(samples),
            "samples": [
                {
                    "name": s.name,
                    "barcode": s.barcode,
                    "type": s.sample_type,
                    "location": s.location,
                    "storage_temp": s.storage_temp,
                    "lot_number": s.lot_number,
                    "expiry_date": s.expiry_date,
                    "quantity": s.quantity,
                    "unit": s.unit,
                }
                for s in samples
            ],
        }


async def _check_inventory(params: dict, org_id: str = "org_default") -> dict:
    """Check stock levels and expiry for a reagent."""
    name = params.get("reagent_name", "")
    check_expiry = params.get("check_expiry", True)

    async with async_session_factory() as session:
        stmt = select(Sample).where(Sample.org_id == org_id, Sample.name.ilike(f"%{name}%"))
        result = await session.execute(stmt.limit(10))
        samples = result.scalars().all()

        if not samples:
            return {"found": 0, "message": f"No reagent found matching '{name}'"}

        items = []
        for s in samples:
            item: dict[str, Any] = {
                "name": s.name,
                "quantity": s.quantity,
                "unit": s.unit,
                "location": s.location,
                "lot_number": s.lot_number,
            }
            if check_expiry and s.expiry_date:
                days_until = (s.expiry_date - date.today()).days
                item["expiry_date"] = s.expiry_date
                item["days_until_expiry"] = days_until
                item["status"] = "expired" if days_until < 0 else "expiring_soon" if days_until < 30 else "ok"
            items.append(item)

        return {"found": len(items), "items": items}


async def _query_experiments(params: dict, org_id: str = "org_default") -> dict:
    """Query experiments — supports filtering by name, status, compound."""
    query = params.get("query", "")

    async with async_session_factory() as session:
        stmt = select(Experiment).where(
            Experiment.org_id == org_id,
            or_(
                Experiment.name.ilike(f"%{query}%"),
                Experiment.description.ilike(f"%{query}%"),
                Experiment.protocol.ilike(f"%{query}%"),
            )
        ).limit(20)

        result = await session.execute(stmt)
        experiments = result.scalars().all()

        if not experiments:
            return {"found": 0, "message": f"No experiments found matching '{query}'"}

        return {
            "found": len(experiments),
            "experiments": [
                {
                    "name": e.name,
                    "status": e.status,
                    "description": e.description,
                    "protocol": e.protocol,
                    "results": e.results,
                    "created_at": e.created_at,
                }
                for e in experiments
            ],
        }


async def _query_plate_maps(params: dict, org_id: str = "org_default") -> dict:
    """Query plate maps by name or description."""
    query = params.get("query", "")

    async with async_session_factory() as session:
        stmt = select(PlateMap).where(
            PlateMap.org_id == org_id,
            or_(
                PlateMap.name.ilike(f"%{query}%"),
                PlateMap.description.ilike(f"%{query}%"),
            )
        ).limit(20)

        result = await session.execute(stmt)
        plates = result.scalars().all()

        if not plates:
            return {"found": 0, "message": f"No plate maps found matching '{query}'"}

        return {
            "found": len(plates),
            "plate_maps": [
                {
                    "name": p.name,
                    "plate_type": p.plate_type,
                    "description": p.description,
                    "well_mappings_count": len(p.well_mappings) if p.well_mappings else 0,
                    "created_at": p.created_at,
                }
                for p in plates
            ],
        }


async def _get_ic50_values(params: dict, org_id: str = "org_default") -> dict:
    """Get IC50/EC50 values across experiments for a compound."""
    compound = params.get("compound", "")

    async with async_session_factory() as session:
        stmt = select(Experiment).where(
            Experiment.org_id == org_id,
            or_(
                Experiment.name.ilike(f"%{compound}%"),
                Experiment.description.ilike(f"%{compound}%"),
            )
        ).limit(20)

        result = await session.execute(stmt)
        experiments = result.scalars().all()

        ic50_results = []
        for e in experiments:
            if e.results and isinstance(e.results, dict):
                entry: dict[str, Any] = {
                    "experiment": e.name,
                    "status": e.status,
                    "created_at": e.created_at,
                }
                if "ec50" in e.results:
                    entry["ic50_ec50"] = e.results["ec50"]
                if "hill_slope" in e.results:
                    entry["hill_slope"] = e.results["hill_slope"]
                if "r_squared" in e.results:
                    entry["r_squared"] = e.results["r_squared"]
                if "z_prime" in e.results:
                    entry["z_prime"] = e.results["z_prime"]
                if any(k in entry for k in ("ic50_ec50", "hill_slope", "r_squared", "z_prime")):
                    ic50_results.append(entry)

        if not ic50_results:
            return {
                "found": 0,
                "message": f"No IC50/EC50 results found for '{compound}'. Found {len(experiments)} experiments matching the name but none with dose-response results.",
                "experiments_found": [e.name for e in experiments],
            }

        return {"found": len(ic50_results), "results": ic50_results}


async def _get_expiring_samples(params: dict, org_id: str = "org_default") -> dict:
    """Get all samples expiring within N days."""
    days = params.get("days", 30)

    async with async_session_factory() as session:
        cutoff = date.today()
        from datetime import timedelta
        future = cutoff + timedelta(days=days)

        stmt = select(Sample).where(
            Sample.org_id == org_id,
            Sample.expiry_date.isnot(None),
            Sample.expiry_date <= future,
        ).order_by(Sample.expiry_date)

        result = await session.execute(stmt)
        samples = result.scalars().all()

        return {
            "found": len(samples),
            "window_days": days,
            "items": [
                {
                    "name": s.name,
                    "type": s.sample_type,
                    "expiry_date": s.expiry_date,
                    "days_remaining": (s.expiry_date - cutoff).days,
                    "location": s.location,
                    "quantity": s.quantity,
                    "unit": s.unit,
                }
                for s in samples
            ],
        }


async def _get_sample_stats(params: dict, org_id: str = "org_default") -> dict:
    """Get summary statistics about the sample inventory."""
    async with async_session_factory() as session:
        total = await session.scalar(
            select(func.count()).select_from(Sample).where(Sample.org_id == org_id)
        )

        # Count by type
        type_counts_q = await session.execute(
            select(Sample.sample_type, func.count())
            .where(Sample.org_id == org_id)
            .group_by(Sample.sample_type)
        )
        type_counts = {row[0]: row[1] for row in type_counts_q.all()}

        # Expiring soon (30 days)
        from datetime import timedelta
        cutoff = date.today() + timedelta(days=30)
        expiring = await session.scalar(
            select(func.count()).select_from(Sample).where(
                Sample.org_id == org_id,
                Sample.expiry_date.isnot(None),
                Sample.expiry_date <= cutoff,
                Sample.expiry_date >= date.today(),
            )
        )

        # Already expired
        expired = await session.scalar(
            select(func.count()).select_from(Sample).where(
                Sample.org_id == org_id,
                Sample.expiry_date.isnot(None),
                Sample.expiry_date < date.today(),
            )
        )

        return {
            "total_samples": total,
            "by_type": type_counts,
            "expiring_within_30_days": expiring,
            "already_expired": expired,
        }


# ---------------------------------------------------------------------------
# File access tools
# ---------------------------------------------------------------------------

async def _list_files(params: dict, org_id: str = "org_default") -> dict:
    """List all uploaded files for the current org."""
    from resonantia.api.files import _file_registry
    files = [f for f in _file_registry.values() if f.get("org_id", "org_default") == org_id]
    return {
        "found": len(files),
        "files": [
            {"id": f["id"], "filename": f["filename"], "size": f["size"],
             "content_type": f.get("content_type", ""), "uploaded_at": f.get("uploaded_at", "")}
            for f in files
        ],
    }


async def _get_file_info(params: dict, org_id: str = "org_default") -> dict:
    """Get details about a specific uploaded file (scoped to org)."""
    from resonantia.api.files import _file_registry
    file_id = params.get("file_id", "")
    if file_id in _file_registry:
        f = _file_registry[file_id]
        if f.get("org_id", "org_default") != org_id:
            return {"found": False, "message": "File not found or not accessible"}
        return {"found": True, **f}
    for f in _file_registry.values():
        if f.get("org_id", "org_default") != org_id:
            continue
        if params.get("filename", "").lower() in f.get("filename", "").lower():
            return {"found": True, **f}
    return {"found": False, "message": f"No file found with id or name matching '{file_id or params.get('filename', '')}'"}


async def _read_file_contents(params: dict, org_id: str = "org_default") -> dict:
    """Read the actual contents of an uploaded file (CSV, TSV, TXT)."""
    from resonantia.api.files import _file_registry
    from resonantia.config import get_settings
    import os

    file_id = params.get("file_id", "")
    filename = params.get("filename", "")

    # Find the file path
    path = None
    matched_file = None

    # Search by ID (with org_id check)
    if file_id and file_id in _file_registry:
        matched_file = _file_registry[file_id]
        if matched_file.get("org_id", "org_default") != org_id:
            return {"error": "File not found or not accessible"}
        path = matched_file.get("stored_path") or matched_file.get("path")

    # Search by filename (with org_id check)
    if not path and filename:
        for f in _file_registry.values():
            if f.get("org_id", "org_default") != org_id:
                continue
            if filename.lower() in f.get("filename", "").lower():
                matched_file = f
                path = f.get("path")
                break

    # Try constructing path from file_id
    if not path and file_id:
        settings = get_settings()
        for ext in [".csv", ".txt", ".tsv", ".xlsx"]:
            candidate = os.path.join(settings.upload_dir, "files", f"{file_id}{ext}")
            if os.path.exists(candidate):
                path = candidate
                break

    if not path or not os.path.exists(path):
        return {"error": f"File not found: {file_id or filename}. Use list_files to see available files."}

    # Read the file
    try:
        with open(path, "r", errors="replace") as f:
            content = f.read()

        # Truncate very large files to avoid overwhelming the LLM context
        max_chars = 8000
        truncated = len(content) > max_chars
        if truncated:
            content = content[:max_chars]

        return {
            "filename": matched_file.get("filename", os.path.basename(path)) if matched_file else os.path.basename(path),
            "content": content,
            "truncated": truncated,
            "size_bytes": os.path.getsize(path),
            "lines": content.count("\n") + 1,
        }
    except Exception as e:
        return {"error": f"Could not read file: {str(e)}"}


# ---------------------------------------------------------------------------
# Microscopy tools
# ---------------------------------------------------------------------------

async def _list_microscopy_images(params: dict, org_id: str = "org_default") -> dict:
    """List microscopy images with optional filters."""
    async with async_session_factory() as session:
        stmt = select(MicroscopyImage).where(MicroscopyImage.org_id == org_id)
        if params.get("well"):
            stmt = stmt.where(MicroscopyImage.well == params["well"])
        if params.get("channel"):
            stmt = stmt.where(MicroscopyImage.channel == params["channel"])
        stmt = stmt.limit(50)

        result = await session.execute(stmt)
        images = result.scalars().all()

        if not images:
            return {"found": 0, "message": "No microscopy images found. Upload images via the Microscopy tab or /api/v1/microscopy/upload."}

        return {
            "found": len(images),
            "images": [
                {"well": img.well, "channel": img.channel, "fov": img.fov,
                 "image_path": img.image_path, "created_at": img.created_at}
                for img in images
            ],
        }


# ---------------------------------------------------------------------------
# Plate map detail tools
# ---------------------------------------------------------------------------

async def _get_plate_map_details(params: dict, org_id: str = "org_default") -> dict:
    """Get full details of a plate map including well mappings."""
    query = params.get("plate_map_name", "") or params.get("query", "")
    async with async_session_factory() as session:
        stmt = select(PlateMap).where(PlateMap.org_id == org_id, PlateMap.name.ilike(f"%{query}%")).limit(5)
        result = await session.execute(stmt)
        plates = result.scalars().all()

        if not plates:
            return {"found": 0, "message": f"No plate map found matching '{query}'"}

        return {
            "found": len(plates),
            "plate_maps": [
                {
                    "name": p.name,
                    "plate_type": p.plate_type,
                    "description": p.description,
                    "source_plates": p.source_plates,
                    "destination_plate": p.destination_plate,
                    "well_mappings": p.well_mappings[:20] if p.well_mappings else [],
                    "total_mappings": len(p.well_mappings) if p.well_mappings else 0,
                    "worklist_generated": p.worklist_data is not None,
                    "created_at": p.created_at,
                }
                for p in plates
            ],
        }


# ---------------------------------------------------------------------------
# Processing results tools
# ---------------------------------------------------------------------------

async def _get_processing_results(params: dict, org_id: str = "org_default") -> dict:
    """Get processing results from completed experiments."""
    async with async_session_factory() as session:
        stmt = select(Experiment).where(
            Experiment.org_id == org_id,
            Experiment.status == "completed",
            Experiment.results.isnot(None),
        ).order_by(Experiment.created_at.desc()).limit(20)

        if params.get("type"):
            stmt = stmt.where(Experiment.protocol.ilike(f"%{params['type']}%"))

        result = await session.execute(stmt)
        experiments = result.scalars().all()

        if not experiments:
            return {"found": 0, "message": "No completed processing results found."}

        return {
            "found": len(experiments),
            "results": [
                {
                    "experiment": e.name,
                    "protocol": e.protocol,
                    "status": e.status,
                    "results": e.results,
                    "created_at": e.created_at,
                }
                for e in experiments
            ],
        }


# ---------------------------------------------------------------------------
# ELN tools
# ---------------------------------------------------------------------------

def _generate_eln_content(exp: Experiment) -> str:
    """Build structured markdown ELN content from an experiment's data.

    Sections: Objective, Methods, Results, Conclusions, References.
    Handles missing fields gracefully -- sections are omitted or marked
    ``N/A`` when the underlying data is absent.
    """
    sections: list[str] = []
    results: dict = exp.results if isinstance(exp.results, dict) else {}

    # --- Title ---
    sections.append(f"# {exp.name}\n")

    # --- Objective ---
    objective = exp.description or "Characterise compound activity."
    sections.append(f"## Objective\n{objective}\n")

    # --- Methods ---
    method_lines: list[str] = []
    plate_type = results.get("plate_type") or results.get("plate_format")
    if plate_type:
        method_lines.append(f"- **Plate format:** {plate_type}-well")

    compound = results.get("compound") or results.get("compound_name")
    if compound:
        n_points = results.get("n_points", results.get("num_points", ""))
        dilution_factor = results.get("dilution_factor", "")
        conc_range = results.get("concentration_range", "")
        detail = compound
        if n_points:
            detail += f", {n_points}-point"
        if dilution_factor:
            detail += f" {dilution_factor}-fold dilution"
        if conc_range:
            detail += f" ({conc_range})"
        method_lines.append(f"- **Compound:** {detail}")

    replicates = results.get("n_replicates") or results.get("replicates")
    if replicates:
        method_lines.append(f"- **Replicates:** {replicates}")

    readout = results.get("readout_method") or results.get("readout")
    if readout:
        method_lines.append(f"- **Readout:** {readout}")

    controls: list[str] = []
    pos = results.get("pos_control") or results.get("positive_control")
    vehicle = results.get("vehicle_control") or results.get("negative_control")
    if pos:
        controls.append(f"Positive ({pos})")
    if vehicle:
        controls.append(f"Vehicle ({vehicle})")
    if controls:
        method_lines.append(f"- **Controls:** {', '.join(controls)}")

    # Fall back to the experiment's protocol text if we built nothing
    if not method_lines and exp.protocol:
        method_lines.append(exp.protocol)

    if method_lines:
        sections.append("## Methods\n" + "\n".join(method_lines) + "\n")

    # --- Results ---
    result_lines: list[str] = []
    ic50 = results.get("ec50") or results.get("ic50")
    if ic50 is not None:
        ci_lower = results.get("ci_lower")
        ci_upper = results.get("ci_upper")
        unit = results.get("concentration_unit", "nM")
        line = f"- **IC50:** {ic50} {unit}"
        if ci_lower is not None and ci_upper is not None:
            line += f" (95% CI: {ci_lower}--{ci_upper} {unit})"
        result_lines.append(line)

    hill = results.get("hill_slope")
    if hill is not None:
        result_lines.append(f"- **Hill slope:** {hill}")

    r2 = results.get("r_squared")
    if r2 is not None:
        result_lines.append(f"- **R-squared:** {r2}")

    z_prime = results.get("z_prime")
    if z_prime is not None:
        result_lines.append(f"- **Z-prime:** {z_prime}")

    outlier_count = results.get("outlier_count")
    if outlier_count is not None:
        wells = results.get("outlier_wells", "")
        result_lines.append(f"- **Outliers:** {outlier_count} points flagged"
                            + (f" at {wells}" if wells else ""))

    plot_url = results.get("plot_url") or results.get("plot_path")
    if plot_url:
        result_lines.append(f"\n![Dose-Response Curve]({plot_url})")

    # Include any other result keys that we have not already rendered
    _rendered = {
        "ec50", "ic50", "ci_lower", "ci_upper", "concentration_unit",
        "hill_slope", "r_squared", "z_prime", "outlier_count",
        "outlier_wells", "plot_url", "plot_path",
        "compound", "compound_name", "plate_type", "plate_format",
        "n_points", "num_points", "dilution_factor", "concentration_range",
        "n_replicates", "replicates", "readout_method", "readout",
        "pos_control", "positive_control", "vehicle_control",
        "negative_control",
    }
    for k, v in results.items():
        if k not in _rendered:
            result_lines.append(f"- **{k}:** {v}")

    if result_lines:
        sections.append("## Results\n" + "\n".join(result_lines) + "\n")

    # --- Conclusions ---
    conclusions: list[str] = []
    if ic50 is not None:
        conclusions.append(f"The compound shows an IC50 of {ic50}.")
    if r2 is not None:
        try:
            r2_val = float(r2)
            if r2_val >= 0.95:
                conclusions.append("Curve fit quality is excellent (R-squared >= 0.95).")
            elif r2_val >= 0.9:
                conclusions.append("Curve fit quality is good (R-squared >= 0.90).")
            else:
                conclusions.append(f"Curve fit quality is moderate (R-squared = {r2_val:.3f}); consider additional data points.")
        except (ValueError, TypeError):
            pass
    if z_prime is not None:
        try:
            zp_val = float(z_prime)
            if zp_val >= 0.5:
                conclusions.append(f"Assay quality is excellent (Z-prime = {zp_val:.3f}).")
            elif zp_val >= 0.0:
                conclusions.append(f"Assay quality is marginal (Z-prime = {zp_val:.3f}).")
            else:
                conclusions.append(f"Assay quality is poor (Z-prime = {zp_val:.3f}); troubleshoot before repeating.")
        except (ValueError, TypeError):
            pass
    if not conclusions:
        conclusions.append("Review results and determine next steps.")
    sections.append("## Conclusions\n" + " ".join(conclusions) + "\n")

    # --- References ---
    ref_lines: list[str] = []
    ref_lines.append(f"- Experiment: `{exp.name}`")
    file_id = results.get("file_upload_id") or results.get("file_id")
    if file_id:
        ref_lines.append(f"- Source data: `{file_id}`")
    plate_map_id = results.get("plate_map_id")
    if plate_map_id:
        ref_lines.append(f"- Plate map: `{plate_map_id}`")
    ref_lines.append(f"- Analysis date: {date.today().isoformat()}")
    sections.append("## References\n" + "\n".join(ref_lines) + "\n")

    return "\n".join(sections)


async def _create_eln_entry(params: dict, org_id: str = "org_default") -> dict:
    """Create an ELN entry, optionally auto-generating from an experiment.

    When ``experiment_id`` is provided the handler generates a structured
    ELN draft via :func:`_generate_eln_content` and returns a preview
    payload suitable for the approval-gate card (``content_markdown``
    is included so the frontend can render a rich preview).
    """
    title = params.get("title", "Untitled Entry")
    experiment_id = params.get("experiment_id")
    content = params.get("content_markdown", "")
    tags = params.get("tags", [])

    async with async_session_factory() as session:
        # Generate entry number
        year = date.today().year
        prefix = f"ELN-{year}-"
        count_stmt = select(func.count()).select_from(ELNEntry).where(
            ELNEntry.org_id == org_id,
            ELNEntry.entry_number.like(f"{prefix}%"),
        )
        count = await session.scalar(count_stmt) or 0
        entry_number = f"{prefix}{count + 1:04d}"

        # Auto-generate from experiment if provided
        linked_refs: dict[str, Any] = {}
        if experiment_id:
            import uuid as _uuid
            exp = await session.get(Experiment, _uuid.UUID(experiment_id))
            if exp and exp.org_id != org_id:
                return {"error": "Experiment not found or not accessible"}
            if exp:
                content = _generate_eln_content(exp)
                title = f"ELN — {exp.name}"
                tags = tags or ["auto-generated"]
                linked_refs["experiment_id"] = experiment_id
                if exp.results and isinstance(exp.results, dict):
                    fid = exp.results.get("file_upload_id") or exp.results.get("file_id")
                    if fid:
                        linked_refs["file_upload_id"] = fid
                    pmid = exp.results.get("plate_map_id")
                    if pmid:
                        linked_refs["plate_map_id"] = pmid

        entry = ELNEntry(
            title=title,
            entry_number=entry_number,
            content_markdown=content,
            status="draft",
            tags=tags,
            linked_references=linked_refs or None,
            org_id=org_id,
        )
        if experiment_id:
            import uuid as _uuid
            entry.experiment_id = _uuid.UUID(experiment_id)

        session.add(entry)
        await session.commit()
        await session.refresh(entry)

        return {
            "created": True,
            "entry_id": str(entry.id),
            "entry_number": entry.entry_number,
            "title": entry.title,
            "status": entry.status,
            "content_markdown": content,
            "linked_references": linked_refs or None,
        }


async def _query_eln_entries(params: dict, org_id: str = "org_default") -> dict:
    """Search ELN entries."""
    query = params.get("query", "")
    status = params.get("status")

    async with async_session_factory() as session:
        stmt = select(ELNEntry).where(
            ELNEntry.org_id == org_id,
            or_(
                ELNEntry.title.ilike(f"%{query}%"),
                ELNEntry.content_markdown.ilike(f"%{query}%"),
                ELNEntry.entry_number.ilike(f"%{query}%"),
            )
        )
        if status:
            stmt = stmt.where(ELNEntry.status == status)
        stmt = stmt.order_by(ELNEntry.created_at.desc()).limit(20)

        result = await session.execute(stmt)
        entries = result.scalars().all()

        if not entries:
            return {"found": 0, "message": f"No ELN entries found matching '{query}'"}

        return {
            "found": len(entries),
            "entries": [
                {
                    "id": str(e.id),
                    "entry_number": e.entry_number,
                    "title": e.title,
                    "status": e.status,
                    "tags": e.tags,
                    "created_at": e.created_at,
                }
                for e in entries
            ],
        }


async def _get_eln_entry(params: dict, org_id: str = "org_default") -> dict:
    """Get full ELN entry with appendices."""
    entry_id = params.get("entry_id", "")

    async with async_session_factory() as session:
        # Try UUID first, then entry number
        entry = None
        try:
            import uuid as _uuid
            entry = await session.get(ELNEntry, _uuid.UUID(entry_id))
        except (ValueError, AttributeError):
            pass

        if not entry:
            stmt = select(ELNEntry).where(ELNEntry.org_id == org_id, ELNEntry.entry_number == entry_id)
            result = await session.execute(stmt)
            entry = result.scalar_one_or_none()

        if not entry or entry.org_id != org_id:
            return {"found": False, "message": f"No ELN entry found for '{entry_id}'"}

        return {
            "found": True,
            "id": str(entry.id),
            "entry_number": entry.entry_number,
            "title": entry.title,
            "status": entry.status,
            "content_markdown": entry.content_markdown,
            "summary": entry.summary,
            "tags": entry.tags,
            "appendices": [
                {"number": a.appendix_number, "content": a.content_markdown}
                for a in entry.appendices
            ],
            "created_at": entry.created_at,
        }


async def _submit_eln_entry(params: dict, org_id: str = "org_default") -> dict:
    """Submit an ELN entry (make immutable)."""
    entry_id = params.get("entry_id", "")

    async with async_session_factory() as session:
        import uuid as _uuid
        try:
            entry = await session.get(ELNEntry, _uuid.UUID(entry_id))
        except (ValueError, AttributeError):
            return {"success": False, "message": f"Invalid entry ID: {entry_id}"}

        if not entry or entry.org_id != org_id:
            return {"success": False, "message": f"ELN entry {entry_id} not found"}
        if entry.status == "submitted":
            return {"success": False, "message": "Entry is already submitted"}

        entry.status = "submitted"
        await session.commit()

        return {
            "success": True,
            "entry_number": entry.entry_number,
            "title": entry.title,
            "status": "submitted",
            "message": "Entry submitted successfully. It is now immutable.",
        }


# ---------------------------------------------------------------------------
# Protocol tools
# ---------------------------------------------------------------------------

async def _create_protocol_tool(params: dict, org_id: str = "org_default") -> dict:
    """Create a protocol, optionally generating steps from experiment type."""
    name = params.get("name", "New Protocol")
    description = params.get("description", "")
    experiment_type = params.get("experiment_type")
    cell_line = params.get("cell_line")

    async with async_session_factory() as session:
        protocol = Protocol(
            name=name,
            description=description or f"Protocol for {experiment_type or 'general'} experiment",
            status="draft",
            is_template=bool(experiment_type),
            tags=[experiment_type] if experiment_type else [],
            org_id=org_id,
        )
        session.add(protocol)
        await session.flush()

        # Generate steps if experiment_type is provided
        steps_data = []
        if experiment_type == "cytotoxicity":
            steps_data = [
                (1, "Cell Seeding", "Seed cells at appropriate density", 30, 37.0),
                (2, "Incubation (24h)", "Allow cells to attach", 1440, 37.0),
                (3, "Compound Treatment", "Add compound dilutions", 60, 22.0),
                (4, "Incubation (48h)", "Incubate with compound", 2880, 37.0),
                (5, "Viability Readout", "Add CellTiter-Glo and read", 30, 22.0),
                (6, "Data Analysis", "Fit dose-response curves", 60, None),
            ]
        elif experiment_type == "transfection":
            steps_data = [
                (1, "Cell Seeding", "Seed at 60-70% confluency", 30, 37.0),
                (2, "Prepare Complexes", "Mix DNA and Lipofectamine", 25, 22.0),
                (3, "Transfect", "Add complexes to cells", 15, 22.0),
                (4, "Incubation", "Incubate 24-48h", 1440, 37.0),
                (5, "Analysis", "Assess efficiency", 60, None),
            ]
        else:
            steps_data = [
                (1, "Preparation", "Prepare reagents and equipment", 30, None),
                (2, "Execution", f"Execute {experiment_type or 'experiment'} steps", 120, None),
                (3, "Analysis", "Analyze results", 60, None),
            ]

        for order, title, desc, dur, temp in steps_data:
            step = ProtocolStep(
                protocol_id=protocol.id,
                step_order=order,
                title=title,
                description=desc,
                duration_minutes=dur,
                temperature_celsius=temp,
            )
            session.add(step)

        await session.commit()
        await session.refresh(protocol)

        return {
            "created": True,
            "protocol_id": str(protocol.id),
            "name": protocol.name,
            "steps_count": len(steps_data),
            "status": "draft",
        }


async def _query_protocols(params: dict, org_id: str = "org_default") -> dict:
    """Search protocols by name or description."""
    query = params.get("query", "")
    status = params.get("status")

    async with async_session_factory() as session:
        stmt = select(Protocol).where(
            Protocol.org_id == org_id,
            or_(
                Protocol.name.ilike(f"%{query}%"),
                Protocol.description.ilike(f"%{query}%"),
            )
        )
        if status:
            stmt = stmt.where(Protocol.status == status)
        stmt = stmt.order_by(Protocol.created_at.desc()).limit(20)

        result = await session.execute(stmt)
        protocols = result.scalars().all()

        if not protocols:
            return {"found": 0, "message": f"No protocols found matching '{query}'"}

        return {
            "found": len(protocols),
            "protocols": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "version": p.version,
                    "status": p.status,
                    "is_template": p.is_template,
                    "steps_count": len(p.steps) if p.steps else 0,
                    "tags": p.tags,
                    "created_at": p.created_at,
                }
                for p in protocols
            ],
        }


async def _check_protocol_inventory(params: dict, org_id: str = "org_default") -> dict:
    """Check reagent availability for a protocol."""
    protocol_id = params.get("protocol_id", "")

    async with async_session_factory() as session:
        import uuid as _uuid
        try:
            protocol = await session.get(Protocol, _uuid.UUID(protocol_id))
        except (ValueError, AttributeError):
            return {"success": False, "message": f"Invalid protocol ID: {protocol_id}"}

        if not protocol or protocol.org_id != org_id:
            return {"success": False, "message": f"Protocol {protocol_id} not found"}

        results = []
        all_available = True

        for step in protocol.steps:
            if not step.reagents:
                continue
            for reagent in step.reagents:
                name = reagent.get("name", "")
                if not name:
                    continue
                stmt = select(Sample).where(Sample.org_id == org_id, Sample.name.ilike(f"%{name}%")).limit(5)
                res = await session.execute(stmt)
                samples = res.scalars().all()

                available = len(samples) > 0
                if not available:
                    all_available = False

                results.append({
                    "step": step.title,
                    "reagent": name,
                    "available": available,
                    "matches": [{"name": s.name, "quantity": s.quantity, "unit": s.unit} for s in samples],
                })

        return {
            "protocol": protocol.name,
            "all_available": all_available,
            "reagents_checked": len(results),
            "details": results,
        }


async def _calculate_dilution(params: dict, org_id: str = "org_default") -> dict:
    """C1V1 = C2V2 calculator."""
    c1 = params.get("c1", 0)
    v1 = params.get("v1")
    c2 = params.get("c2", 0)
    v2 = params.get("v2")

    if v1 is None and v2 is not None:
        v1 = (c2 * v2) / c1 if c1 else 0
        formula = f"V1 = (C2 x V2) / C1 = ({c2} x {v2}) / {c1} = {v1:.4f}"
    elif v2 is None and v1 is not None:
        v2 = (c1 * v1) / c2 if c2 else 0
        formula = f"V2 = (C1 x V1) / C2 = ({c1} x {v1}) / {c2} = {v2:.4f}"
    elif v1 is not None and v2 is not None:
        formula = f"C1V1 = {c1 * v1:.4f}, C2V2 = {c2 * v2:.4f}"
    else:
        return {"error": "Provide at least one of v1 or v2"}

    return {
        "c1": c1, "v1": v1,
        "c2": c2, "v2": v2,
        "unit_concentration": params.get("unit_concentration", "uM"),
        "unit_volume": params.get("unit_volume", "uL"),
        "formula": formula,
    }


# ---------------------------------------------------------------------------
# Data processing tools
# ---------------------------------------------------------------------------

async def _fit_dose_response_tool(params: dict, org_id: str = "org_default") -> dict:
    """Fit a 4PL dose-response curve, generate plot, and persist to Experiment."""
    from resonantia.services.data_processor import fit_dose_response_full

    concentrations = params.get("concentrations", [])
    responses = params.get("responses", [])
    compound_name = params.get("compound_name", "Compound")
    positive_controls = params.get("positive_controls")
    negative_controls = params.get("negative_controls")

    if not concentrations or not responses:
        return {"error": "Both 'concentrations' and 'responses' arrays are required."}
    if len(concentrations) != len(responses):
        return {"error": f"Array length mismatch: {len(concentrations)} concentrations vs {len(responses)} responses."}

    try:
        result = await fit_dose_response_full(
            concentrations,
            responses,
            positive_controls=positive_controls,
            negative_controls=negative_controls,
            compound_name=compound_name,
        )
    except Exception as e:
        return {"error": f"Curve fitting failed: {str(e)}"}

    if not result.get("success"):
        return result

    # Persist results to Experiment model (best-effort)
    experiment_id = None
    try:
        async with async_session_factory() as session:
            experiment = Experiment(
                org_id=org_id,
                name=f"Dose-Response: {compound_name}",
                description=f"4PL curve fit for {compound_name}",
                protocol="dose-response-4pl",
                status="completed",
                results={
                    "ec50": result["ic50"],
                    "ic50_ci_lower": result["ic50_ci_lower"],
                    "ic50_ci_upper": result["ic50_ci_upper"],
                    "hill_slope": result["hill_slope"],
                    "r_squared": result["r_squared"],
                    "z_prime": result.get("z_prime"),
                    "top": result["top"],
                    "bottom": result["bottom"],
                    "n_points": result["n_points"],
                    "n_replicates": result["n_replicates"],
                    "outliers": result["outliers"],
                    "plot_url": result["plot_url"],
                },
            )
            session.add(experiment)
            await session.commit()
            await session.refresh(experiment)
            experiment_id = str(experiment.id)
    except Exception:
        logger.warning("Could not persist dose-response experiment to DB")

    result["experiment_id"] = experiment_id
    return result


async def _normalize_plate_tool(params: dict, org_id: str = "org_default") -> dict:
    """Normalize plate reader data."""
    from resonantia.services.data_processor import normalize_plate
    raw_data = params.get("raw_data", [])
    method = params.get("method", "z-score")
    if not raw_data:
        return {"error": "'raw_data' array is required."}
    try:
        result = normalize_plate(raw_data, method)
        return {"normalized_data": result.tolist() if hasattr(result, 'tolist') else list(result), "method": method, "count": len(raw_data)}
    except Exception as e:
        return {"error": f"Normalization failed: {str(e)}"}


async def _calculate_z_prime_tool(params: dict, org_id: str = "org_default") -> dict:
    """Calculate Z-prime factor for assay quality."""
    from resonantia.services.data_processor import calculate_z_prime
    positive = params.get("positive_values", [])
    negative = params.get("negative_values", [])
    if not positive or not negative:
        return {"error": "Both 'positive_values' and 'negative_values' arrays are required."}
    try:
        result = calculate_z_prime(positive, negative)
        return result
    except Exception as e:
        return {"error": f"Z-prime calculation failed: {str(e)}"}


async def _qpcr_analysis_tool(params: dict, org_id: str = "org_default") -> dict:
    """Delta-delta Ct analysis for qPCR data."""
    ct_values = params.get("ct_values", {})
    ref_gene = params.get("reference_gene", "GAPDH")
    control = params.get("control_sample", "Control")
    if not ct_values:
        return {"error": "'ct_values' object is required (mapping sample/gene names to Ct value arrays)."}
    try:
        results = {}
        if ref_gene in ct_values:
            ref_avg = sum(ct_values[ref_gene]) / len(ct_values[ref_gene])
            control_delta = 0
            if control in ct_values:
                control_avg = sum(ct_values[control]) / len(ct_values[control])
                control_delta = control_avg - ref_avg
            for sample, cts in ct_values.items():
                if sample not in (ref_gene,):
                    avg_ct = sum(cts) / len(cts)
                    delta_ct = avg_ct - ref_avg
                    delta_delta_ct = delta_ct - control_delta
                    fold_change = 2 ** (-delta_delta_ct)
                    results[sample] = {"avg_ct": round(avg_ct, 2), "delta_ct": round(delta_ct, 2), "delta_delta_ct": round(delta_delta_ct, 2), "fold_change": round(fold_change, 3)}
        return {"reference_gene": ref_gene, "control_sample": control, "results": results}
    except Exception as e:
        return {"error": f"qPCR analysis failed: {str(e)}"}


# ---------------------------------------------------------------------------
# Plate layout proposal tools (P1.4a)
# ---------------------------------------------------------------------------

# Color palette for well types in plate preview
_WELL_COLORS = {
    "control_positive": "#22c55e",
    "control_negative": "#ef4444",
    "sample": "#3b82f6",
    "empty": "#d1d5db",
}


def _plate_dimensions(plate_type: str) -> tuple[int, int]:
    """Return (rows, cols) for a plate type string."""
    if str(plate_type) == "384":
        return 16, 24
    return 8, 12


def _build_plate_preview(
    plate_type: str,
    well_assignments: list[dict[str, Any]],
    *,
    compounds: list[str] | None = None,
    replicates: int = 1,
    include_controls: bool = True,
) -> dict[str, Any]:
    """Build a structured plate preview suitable for an approval card.

    Returns a dict with ``plate_type``, ``rows``, ``cols``, ``wells``
    (list of per-well dicts with position/type/compound/color) and a
    ``summary`` sub-dict.
    """
    rows, cols = _plate_dimensions(plate_type)
    total_wells = rows * cols

    # Build occupied-well lookup
    occupied: dict[str, dict[str, Any]] = {}
    for w in well_assignments:
        pos = w.get("well") or w.get("destination_well", "")
        if pos:
            occupied[pos] = w

    # Standard control columns (first and last)
    ctrl_col_pos = 1
    ctrl_col_neg = cols
    row_labels = [chr(ord("A") + r) for r in range(rows)]

    wells: list[dict[str, Any]] = []
    used_wells = 0
    control_pos_count = 0
    control_neg_count = 0

    for r_label in row_labels:
        for c in range(1, cols + 1):
            pos = f"{r_label}{c}"
            if pos in occupied:
                entry = occupied[pos]
                well_dict: dict[str, Any] = {
                    "position": pos,
                    "type": "sample",
                    "compound": entry.get("compound", ""),
                    "color": _WELL_COLORS["sample"],
                }
                conc = entry.get("concentration") or entry.get("concentration_nM")
                if conc is not None:
                    well_dict["concentration_nM"] = conc
                rep = entry.get("replicate_row")
                if rep is not None:
                    well_dict["replicate"] = rep
                wells.append(well_dict)
                used_wells += 1
            elif include_controls and c == ctrl_col_pos:
                wells.append({
                    "position": pos,
                    "type": "control_positive",
                    "compound": "Positive Control",
                    "color": _WELL_COLORS["control_positive"],
                })
                control_pos_count += 1
                used_wells += 1
            elif include_controls and c == ctrl_col_neg:
                wells.append({
                    "position": pos,
                    "type": "control_negative",
                    "compound": "Vehicle Control",
                    "color": _WELL_COLORS["control_negative"],
                })
                control_neg_count += 1
                used_wells += 1
            else:
                wells.append({
                    "position": pos,
                    "type": "empty",
                    "compound": "",
                    "color": _WELL_COLORS["empty"],
                })

    unique_compounds = set()
    for w in well_assignments:
        cpd = w.get("compound", "")
        if cpd:
            unique_compounds.add(cpd)

    return {
        "plate_type": int(plate_type) if str(plate_type).isdigit() else plate_type,
        "rows": rows,
        "cols": cols,
        "wells": wells,
        "summary": {
            "total_wells": total_wells,
            "used_wells": used_wells,
            "compounds": len(unique_compounds) if unique_compounds else (len(compounds) if compounds else 0),
            "replicates": replicates,
            "controls": {
                "positive": control_pos_count,
                "negative": control_neg_count,
            },
        },
    }


async def _create_plate_map(params: dict, org_id: str = "org_default") -> dict:
    """Create a plate map from source-destination mapping and return preview.

    Delegates to :mod:`plate_mapper` for the actual layout computation,
    then wraps the result in a preview-friendly structure for the
    approval card.
    """
    from resonantia.services.plate_mapper import generate_plate_map

    name = params.get("name", "New Plate Map")
    description = params.get("description", "")
    plate_type = str(params.get("plate_type", "96"))
    sources = params.get("sources", [])

    layout = generate_plate_map(sources, destination_type=plate_type)
    well_assignments = layout.get("well_mappings", [])

    # Convert source->dest mappings to preview-compatible well dicts
    well_dicts: list[dict[str, Any]] = []
    for m in well_assignments:
        content = m.get("content", {})
        well_dicts.append({
            "well": m["destination_well"],
            "compound": content.get("compound", "") if isinstance(content, dict) else "",
        })

    preview = _build_plate_preview(plate_type, well_dicts, include_controls=True)

    async with async_session_factory() as session:
        plate = PlateMap(
            name=name,
            plate_type=plate_type,
            description=description,
            source_plates=sources,
            destination_plate=layout.get("destination_plate"),
            well_mappings=well_assignments,
            org_id=org_id,
        )
        session.add(plate)
        await session.commit()
        await session.refresh(plate)

        return {
            "created": True,
            "plate_map_id": str(plate.id),
            "name": plate.name,
            "plate_type": plate_type,
            "preview": preview,
        }


async def _cherry_pick_tool(params: dict, org_id: str = "org_default") -> dict:
    """Cherry-pick compounds into a destination plate with visual preview."""
    from resonantia.services.plate_mapper import cherry_pick

    source_plates = params.get("source_plates", [])
    hit_list = params.get("hit_list", [])
    plate_type = str(params.get("plate_type", "96"))
    name = params.get("name", "Cherry-Pick Plate")

    layout = cherry_pick(source_plates, hit_list, destination_type=plate_type)
    well_assignments = layout.get("well_mappings", [])

    # Build preview-compatible dicts
    compounds: list[str] = []
    well_dicts: list[dict[str, Any]] = []
    for m in well_assignments:
        content = m.get("content", {})
        cpd = content.get("compound", "") if isinstance(content, dict) else ""
        well_dicts.append({"well": m["destination_well"], "compound": cpd})
        if cpd:
            compounds.append(cpd)

    preview = _build_plate_preview(plate_type, well_dicts, compounds=compounds)

    async with async_session_factory() as session:
        plate = PlateMap(
            name=name,
            plate_type=plate_type,
            description=f"Cherry-pick of {len(hit_list)} wells",
            source_plates=source_plates,
            destination_plate=layout.get("destination_plate"),
            well_mappings=well_assignments,
            org_id=org_id,
        )
        session.add(plate)
        await session.commit()
        await session.refresh(plate)

        return {
            "created": True,
            "plate_map_id": str(plate.id),
            "name": plate.name,
            "plate_type": plate_type,
            "preview": preview,
        }


async def _serial_dilution_tool(params: dict, org_id: str = "org_default") -> dict:
    """Generate a serial dilution layout with visual preview."""
    from resonantia.services.plate_mapper import serial_dilution

    compound = params.get("compound", "Compound")
    start_concentration = params.get("start_concentration", 10000.0)
    dilution_factor = params.get("dilution_factor", 3.0)
    num_points = params.get("num_points", 8)
    replicates = params.get("replicates", 1)
    plate_type = str(params.get("plate_type", "96"))
    name = params.get("name", f"Serial Dilution — {compound}")

    layout = serial_dilution(
        compound=compound,
        start_concentration=start_concentration,
        dilution_factor=dilution_factor,
        num_points=num_points,
        replicates=replicates,
        plate_type=plate_type,
    )

    well_dicts = layout.get("layout", [])
    preview = _build_plate_preview(
        plate_type,
        well_dicts,
        compounds=[compound],
        replicates=replicates,
    )

    async with async_session_factory() as session:
        plate = PlateMap(
            name=name,
            plate_type=plate_type,
            description=(
                f"{num_points}-point {dilution_factor}-fold serial dilution of {compound}, "
                f"starting at {start_concentration} nM, {replicates} replicate(s)"
            ),
            well_mappings=well_dicts,
            org_id=org_id,
        )
        session.add(plate)
        await session.commit()
        await session.refresh(plate)

        return {
            "created": True,
            "plate_map_id": str(plate.id),
            "name": plate.name,
            "plate_type": plate_type,
            "concentrations": layout.get("concentrations", []),
            "preview": preview,
        }


# ---------------------------------------------------------------------------
# Handler registry
# ---------------------------------------------------------------------------

TOOL_HANDLERS: dict[str, Any] = {
    # Sample tools
    "lookup_sample": _lookup_sample,
    "check_inventory": _check_inventory,
    "add_sample": _lookup_sample,
    "get_expiring_samples": _get_expiring_samples,
    "get_sample_stats": _get_sample_stats,
    # Experiment tools
    "query_experiments": _query_experiments,
    "get_ic50_values": _get_ic50_values,
    "get_processing_results": _get_processing_results,
    # Plate map tools
    "query_plate_maps": _query_plate_maps,
    "get_plate_map_details": _get_plate_map_details,
    "create_plate_map": _create_plate_map,
    "cherry_pick": _cherry_pick_tool,
    "serial_dilution": _serial_dilution_tool,
    # Microscopy tools
    "browse_microscopy": _list_microscopy_images,
    "generate_montage": _list_microscopy_images,
    # File tools
    "list_files": _list_files,
    "get_file_info": _get_file_info,
    "read_file_contents": _read_file_contents,
    # ELN tools
    "create_eln_entry": _create_eln_entry,
    "query_eln_entries": _query_eln_entries,
    "get_eln_entry": _get_eln_entry,
    "submit_eln_entry": _submit_eln_entry,
    # Protocol tools
    "create_protocol": _create_protocol_tool,
    "query_protocols": _query_protocols,
    "check_protocol_inventory": _check_protocol_inventory,
    "calculate_dilution": _calculate_dilution,
    # Data processing tools
    "fit_dose_response": _fit_dose_response_tool,
    "normalize_plate": _normalize_plate_tool,
    "calculate_z_prime": _calculate_z_prime_tool,
    "qpcr_analysis": _qpcr_analysis_tool,
    # Experiment design (closed-loop)
    "design_next_experiment": None,  # populated below
    # Generic
    "design_protocol": _query_experiments,
    "search_literature": _query_experiments,
}

# Late import to avoid circular dependency
from resonantia.services.experiment_designer import get_design_tool_handler  # noqa: E402
TOOL_HANDLERS["design_next_experiment"] = get_design_tool_handler()
