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


async def execute_tool(tool_name: str, tool_input: dict[str, Any], org_id: str = "org_default") -> str:
    """Execute a tool by name and return a JSON string result."""
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    try:
        result = await handler(tool_input, org_id)
        return json.dumps(_serialize(result), default=str)
    except Exception as e:
        logger.exception("Tool execution failed: %s", tool_name)
        return json.dumps({"error": str(e)})


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
    """List all uploaded files."""
    from resonantia.api.files import _file_registry
    files = list(_file_registry.values())
    return {
        "found": len(files),
        "files": [
            {"id": f["id"], "filename": f["filename"], "size": f["size"],
             "content_type": f.get("content_type", ""), "uploaded_at": f.get("uploaded_at", "")}
            for f in files
        ],
    }


async def _get_file_info(params: dict, org_id: str = "org_default") -> dict:
    """Get details about a specific uploaded file."""
    from resonantia.api.files import _file_registry
    file_id = params.get("file_id", "")
    if file_id in _file_registry:
        f = _file_registry[file_id]
        return {"found": True, **f}
    # Search by filename
    for f in _file_registry.values():
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

    # Search by ID
    if file_id and file_id in _file_registry:
        matched_file = _file_registry[file_id]
        path = matched_file.get("stored_path") or matched_file.get("path")

    # Search by filename
    if not path and filename:
        for f in _file_registry.values():
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
    # Generic
    "design_protocol": _query_experiments,
    "search_literature": _query_experiments,
}
