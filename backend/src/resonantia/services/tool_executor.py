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

async def _create_eln_entry(params: dict, org_id: str = "org_default") -> dict:
    """Create an ELN entry, optionally auto-generating from an experiment."""
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
        if experiment_id:
            import uuid as _uuid
            exp = await session.get(Experiment, _uuid.UUID(experiment_id))
            if exp and exp.org_id != org_id:
                return {"error": "Experiment not found or not accessible"}
            if exp:
                sections = [f"# {exp.name}\n", f"## Objective\n{exp.description or ''}\n", f"## Protocol\n{exp.protocol or ''}\n"]
                if exp.results:
                    sections.append("## Results\n")
                    for k, v in exp.results.items():
                        sections.append(f"- **{k}**: {v}")
                content = "\n".join(sections)
                title = f"ELN — {exp.name}"
                tags = tags or ["auto-generated"]

        entry = ELNEntry(
            title=title,
            entry_number=entry_number,
            content_markdown=content,
            status="draft",
            tags=tags,
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
    """Fit a 4PL dose-response curve and compute IC50."""
    from resonantia.services.data_processor import fit_dose_response
    concentrations = params.get("concentrations", [])
    responses = params.get("responses", [])
    if not concentrations or not responses:
        return {"error": "Both 'concentrations' and 'responses' arrays are required."}
    if len(concentrations) != len(responses):
        return {"error": f"Array length mismatch: {len(concentrations)} concentrations vs {len(responses)} responses."}
    try:
        result = fit_dose_response(concentrations, responses)
        return result
    except Exception as e:
        return {"error": f"Curve fitting failed: {str(e)}"}


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
    "propose_follow_up_experiment": None,  # populated below
    # Worklist
    "generate_worklist": None,  # populated below
    "create_plate_map": None,  # populated below via plate handlers
    "cherry_pick": None,
    "serial_dilution": None,
    # Generic
    "design_protocol": _query_experiments,
    "search_literature": _query_experiments,
}

# Late import to avoid circular dependency
from resonantia.services.experiment_designer import get_design_tool_handler  # noqa: E402
TOOL_HANDLERS["design_next_experiment"] = get_design_tool_handler()


# ---------------------------------------------------------------------------
# P1.4b: Agent-driven follow-up proposal
# ---------------------------------------------------------------------------

async def _propose_follow_up(params: dict, org_id: str = "org_default") -> dict:
    """Analyze experiment results and propose 2-3 follow-up experiments."""
    experiment_id = params.get("experiment_id", "")
    context = params.get("context", "")

    if not experiment_id:
        return {"error": "experiment_id is required"}

    async with async_session_factory() as session:
        import uuid as _uuid
        exp = await session.get(Experiment, _uuid.UUID(experiment_id))
        if not exp:
            return {"error": f"Experiment {experiment_id} not found"}
        if exp.org_id != org_id:
            return {"error": "Experiment not accessible"}

        results = exp.results or {}
        ic50 = results.get("ic50")
        hill = results.get("hill_slope")
        r_squared = results.get("r_squared")
        z_prime = results.get("z_prime")

        options = []

        if ic50 is not None:
            ic50_val = float(ic50)
            low = max(ic50_val / 10, 0.1)
            high = min(ic50_val * 10, 100000)
            options.append({
                "option_number": 1,
                "title": "Hit Confirmation",
                "rationale": f"Confirm IC50 of {ic50_val:.1f} nM with tighter range and more replicates",
                "plate_type": 384,
                "concentration_range": {
                    "start_nM": round(low, 1),
                    "end_nM": round(high, 1),
                    "points": 10,
                    "fold": 2,
                },
                "replicates": 4,
                "controls": {"positive": "DMSO", "negative": "vehicle", "positions": "columns 1 and 24"},
                "estimated_wells": 88,
                "compounds": [exp.name or "compound"],
            })

        if r_squared is not None and float(r_squared) < 0.9:
            options.append({
                "option_number": len(options) + 1,
                "title": "Re-test with Outlier Removal",
                "rationale": f"R² = {r_squared} is below 0.9. Re-test with tighter QC and outlier exclusion.",
                "plate_type": 96,
                "concentration_range": {"start_nM": 0.5, "end_nM": 10000, "points": 10, "fold": 3},
                "replicates": 4,
                "controls": {"positive": "DMSO", "negative": "vehicle", "positions": "columns 1 and 12"},
                "estimated_wells": 48,
                "compounds": [exp.name or "compound"],
            })

        if z_prime is not None and float(z_prime) < 0.5:
            options.append({
                "option_number": len(options) + 1,
                "title": "Assay Optimization",
                "rationale": f"Z' = {z_prime} is below 0.5, indicating poor assay quality. Optimize controls and signal window.",
                "plate_type": 96,
                "concentration_range": {"start_nM": 1, "end_nM": 10000, "points": 8, "fold": 3},
                "replicates": 6,
                "controls": {"positive": "DMSO", "negative": "vehicle", "positions": "columns 1 and 12"},
                "estimated_wells": 56,
                "compounds": [exp.name or "compound"],
            })

        if len(options) < 2:
            options.append({
                "option_number": len(options) + 1,
                "title": "Selectivity Panel",
                "rationale": "Test compound selectivity across related targets",
                "plate_type": 384,
                "concentration_range": {"start_nM": 1, "end_nM": 10000, "points": 5, "fold": 10},
                "replicates": 3,
                "controls": {"positive": "DMSO", "negative": "vehicle", "positions": "columns 1 and 24"},
                "estimated_wells": 120,
                "compounds": [exp.name or "compound", "target_2", "target_3", "target_4"],
            })

        if len(options) < 3:
            options.append({
                "option_number": len(options) + 1,
                "title": "Cell Line Comparison",
                "rationale": "Verify potency is not cell-line-specific",
                "plate_type": 96,
                "concentration_range": {"start_nM": 0.5, "end_nM": 10000, "points": 10, "fold": 3},
                "replicates": 3,
                "controls": {"positive": "DMSO", "negative": "vehicle", "positions": "columns 1 and 12"},
                "estimated_wells": 36,
                "compounds": [exp.name or "compound"],
            })

        return {
            "experiment_id": experiment_id,
            "summary": f"Based on results for {exp.name}: IC50={ic50}, Hill={hill}, R²={r_squared}, Z'={z_prime}",
            "options": options[:3],
            "recommended": 1,
        }


TOOL_HANDLERS["propose_follow_up_experiment"] = _propose_follow_up


# ---------------------------------------------------------------------------
# P1.5: Worklist generation with approval gate awareness
# ---------------------------------------------------------------------------

async def _generate_worklist_tool(params: dict, org_id: str = "org_default") -> dict:
    """Generate a worklist file for a liquid handler (Echo, Hamilton, Opentrons)."""
    from resonantia.services.plate_mapper import generate_worklist

    plate_map_id = params.get("plate_map_id", "")
    instrument = params.get("instrument", "echo")
    volume_nl = params.get("volume_nl", 100)

    if not plate_map_id:
        return {"error": "plate_map_id is required"}

    async with async_session_factory() as session:
        import uuid as _uuid
        plate_map = await session.get(PlateMap, _uuid.UUID(plate_map_id))
        if not plate_map:
            return {"error": f"Plate map {plate_map_id} not found"}
        if plate_map.org_id != org_id:
            return {"error": "Plate map not accessible"}

        mappings = plate_map.well_mappings or []
        if not mappings:
            return {"error": "Plate map has no well mappings"}

        try:
            worklist_content = generate_worklist(mappings, instrument, volume_nl)
        except Exception as e:
            return {"error": f"Worklist generation failed: {e}"}

        ext = {"echo": "csv", "hamilton": "gwl", "opentrons": "py"}.get(instrument, "csv")
        filename = f"worklist_{plate_map.name.replace(' ', '_')}_{instrument}.{ext}"

        preview_lines = worklist_content.strip().split("\n")[:11]

        return {
            "filename": filename,
            "instrument": instrument,
            "format": ext,
            "total_transfers": len(mappings),
            "total_volume_nl": volume_nl * len(mappings),
            "preview": "\n".join(preview_lines),
            "content": worklist_content,
            "plate_map_id": plate_map_id,
            "plate_map_name": plate_map.name,
        }


TOOL_HANDLERS["generate_worklist"] = _generate_worklist_tool
