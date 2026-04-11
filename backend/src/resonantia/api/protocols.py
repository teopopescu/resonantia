"""Protocol management endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.db.session import get_db
from resonantia.models.protocol import Protocol, ProtocolStep
from resonantia.models.sample import Sample
from resonantia.schemas.protocol import (
    DilutionRequest,
    DilutionResponse,
    InventoryCheckResponse,
    ProtocolCreate,
    ProtocolListResponse,
    ProtocolResponse,
    ProtocolUpdate,
    StepCreate,
    StepResponse,
    StepUpdate,
)

router = APIRouter()


@router.post("/", response_model=ProtocolResponse, status_code=201)
async def create_protocol(
    body: ProtocolCreate,
    db: AsyncSession = Depends(get_db),
) -> Protocol:
    protocol = Protocol(
        name=body.name,
        description=body.description,
        is_template=body.is_template,
        experiment_id=body.experiment_id,
        author_id=body.author_id,
        tags=body.tags,
    )
    db.add(protocol)
    await db.flush()

    # Add steps if provided
    if body.steps:
        for step_data in body.steps:
            step = ProtocolStep(
                protocol_id=protocol.id,
                step_order=step_data.step_order,
                title=step_data.title,
                description=step_data.description,
                duration_minutes=step_data.duration_minutes,
                temperature_celsius=step_data.temperature_celsius,
                equipment=step_data.equipment,
                reagents=step_data.reagents,
                parameters=step_data.parameters,
                notes=step_data.notes,
            )
            db.add(step)
        await db.flush()

    await db.refresh(protocol)
    return protocol


@router.get("/", response_model=list[ProtocolListResponse])
async def list_protocols(
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
    is_template: bool | None = None,
    tag: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[Protocol]:
    stmt = select(Protocol).order_by(Protocol.created_at.desc())
    if status:
        stmt = stmt.where(Protocol.status == status)
    if is_template is not None:
        stmt = stmt.where(Protocol.is_template == is_template)
    if tag:
        stmt = stmt.where(Protocol.tags.contains([tag]))
    result = await db.execute(stmt.offset(skip).limit(limit))
    return list(result.scalars().all())


@router.get("/{protocol_id}", response_model=ProtocolResponse)
async def get_protocol(
    protocol_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Protocol:
    protocol = await db.get(Protocol, protocol_id)
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    return protocol


@router.patch("/{protocol_id}", response_model=ProtocolResponse)
async def update_protocol(
    protocol_id: uuid.UUID,
    body: ProtocolUpdate,
    db: AsyncSession = Depends(get_db),
) -> Protocol:
    protocol = await db.get(Protocol, protocol_id)
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    if protocol.status == "published":
        raise HTTPException(
            status_code=409,
            detail="Cannot edit a published protocol. Create a new version instead.",
        )
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(protocol, k, v)
    await db.flush()
    await db.refresh(protocol)
    return protocol


@router.delete("/{protocol_id}", status_code=204)
async def delete_protocol(
    protocol_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    protocol = await db.get(Protocol, protocol_id)
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    await db.delete(protocol)


@router.post("/{protocol_id}/publish", response_model=ProtocolResponse)
async def publish_protocol(
    protocol_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Protocol:
    protocol = await db.get(Protocol, protocol_id)
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    if protocol.status == "published":
        raise HTTPException(status_code=409, detail="Protocol is already published")
    protocol.status = "published"
    await db.flush()
    await db.refresh(protocol)
    return protocol


@router.post("/{protocol_id}/new-version", response_model=ProtocolResponse, status_code=201)
async def new_version(
    protocol_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Protocol:
    """Clone a protocol into a new draft version."""
    original = await db.get(Protocol, protocol_id)
    if not original:
        raise HTTPException(status_code=404, detail="Protocol not found")

    new_proto = Protocol(
        name=original.name,
        description=original.description,
        version=original.version + 1,
        status="draft",
        is_template=original.is_template,
        parent_protocol_id=original.id,
        author_id=original.author_id,
        experiment_id=original.experiment_id,
        tags=original.tags,
    )
    db.add(new_proto)
    await db.flush()

    # Clone steps
    for step in original.steps:
        new_step = ProtocolStep(
            protocol_id=new_proto.id,
            step_order=step.step_order,
            title=step.title,
            description=step.description,
            duration_minutes=step.duration_minutes,
            temperature_celsius=step.temperature_celsius,
            equipment=step.equipment,
            reagents=step.reagents,
            parameters=step.parameters,
            notes=step.notes,
        )
        db.add(new_step)
    await db.flush()
    await db.refresh(new_proto)
    return new_proto


@router.get("/{protocol_id}/versions", response_model=list[ProtocolListResponse])
async def get_versions(
    protocol_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[Protocol]:
    """Get version history for a protocol."""
    protocol = await db.get(Protocol, protocol_id)
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")

    # Find the root protocol by walking up parent chain
    root_id = protocol.id
    current = protocol
    while current.parent_protocol_id:
        parent = await db.get(Protocol, current.parent_protocol_id)
        if not parent:
            break
        root_id = parent.id
        current = parent

    # Find all versions descending from root
    versions = [current]
    stmt = select(Protocol).where(Protocol.parent_protocol_id == root_id)
    result = await db.execute(stmt)
    versions.extend(result.scalars().all())

    # Also find descendants of descendants (simple 2-level)
    child_ids = [v.id for v in versions]
    stmt2 = select(Protocol).where(Protocol.parent_protocol_id.in_(child_ids))
    result2 = await db.execute(stmt2)
    versions.extend(result2.scalars().all())

    # Deduplicate and sort
    seen = set()
    unique = []
    for v in versions:
        if v.id not in seen:
            seen.add(v.id)
            unique.append(v)
    return sorted(unique, key=lambda p: p.version)


# --- Steps CRUD ---

@router.post("/{protocol_id}/steps", response_model=StepResponse, status_code=201)
async def add_step(
    protocol_id: uuid.UUID,
    body: StepCreate,
    db: AsyncSession = Depends(get_db),
) -> ProtocolStep:
    protocol = await db.get(Protocol, protocol_id)
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    step = ProtocolStep(
        protocol_id=protocol_id,
        step_order=body.step_order,
        title=body.title,
        description=body.description,
        duration_minutes=body.duration_minutes,
        temperature_celsius=body.temperature_celsius,
        equipment=body.equipment,
        reagents=body.reagents,
        parameters=body.parameters,
        notes=body.notes,
    )
    db.add(step)
    await db.flush()
    await db.refresh(step)
    return step


@router.patch("/{protocol_id}/steps/{step_id}", response_model=StepResponse)
async def update_step(
    protocol_id: uuid.UUID,
    step_id: uuid.UUID,
    body: StepUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProtocolStep:
    step = await db.get(ProtocolStep, step_id)
    if not step or step.protocol_id != protocol_id:
        raise HTTPException(status_code=404, detail="Step not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(step, k, v)
    await db.flush()
    await db.refresh(step)
    return step


@router.delete("/{protocol_id}/steps/{step_id}", status_code=204)
async def delete_step(
    protocol_id: uuid.UUID,
    step_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    step = await db.get(ProtocolStep, step_id)
    if not step or step.protocol_id != protocol_id:
        raise HTTPException(status_code=404, detail="Step not found")
    await db.delete(step)


# --- Inventory check ---

@router.post("/{protocol_id}/inventory-check", response_model=InventoryCheckResponse)
async def inventory_check(
    protocol_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Check reagent availability for all steps in a protocol."""
    protocol = await db.get(Protocol, protocol_id)
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")

    reagent_results = []
    all_available = True

    for step in protocol.steps:
        if not step.reagents:
            continue
        for reagent in step.reagents:
            reagent_name = reagent.get("name", "")
            if not reagent_name:
                continue
            # Check against Sample table
            stmt = select(Sample).where(Sample.name.ilike(f"%{reagent_name}%")).limit(5)
            result = await db.execute(stmt)
            samples = result.scalars().all()

            available = len(samples) > 0
            if not available:
                all_available = False

            reagent_results.append({
                "step": step.title,
                "step_order": step.step_order,
                "reagent_name": reagent_name,
                "required_volume": reagent.get("volume"),
                "required_unit": reagent.get("unit"),
                "available": available,
                "inventory_matches": [
                    {
                        "name": s.name,
                        "quantity": s.quantity,
                        "unit": s.unit,
                        "location": s.location,
                        "expiry_date": s.expiry_date.isoformat() if s.expiry_date else None,
                    }
                    for s in samples
                ],
            })

    return {
        "protocol_id": protocol.id,
        "protocol_name": protocol.name,
        "reagents": reagent_results,
        "all_available": all_available,
    }


# --- Dilution calculator ---

@router.post("/dilution-calculator", response_model=DilutionResponse)
async def dilution_calculator(body: DilutionRequest) -> dict:
    """C1V1 = C2V2 dilution calculator."""
    c1, v1, c2, v2 = body.c1, body.v1, body.c2, body.v2

    if v1 is None and v2 is not None:
        # Solve for V1
        v1 = (c2 * v2) / c1
        formula = f"V1 = (C2 x V2) / C1 = ({c2} x {v2}) / {c1} = {v1:.4f}"
    elif v2 is None and v1 is not None:
        # Solve for V2
        v2 = (c1 * v1) / c2
        formula = f"V2 = (C1 x V1) / C2 = ({c1} x {v1}) / {c2} = {v2:.4f}"
    elif v1 is not None and v2 is not None:
        # Verify
        formula = f"C1V1 = {c1 * v1:.4f}, C2V2 = {c2 * v2:.4f}"
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one of v1 or v2 to solve the equation.",
        )

    return {
        "c1": c1,
        "v1": v1,
        "c2": c2,
        "v2": v2,
        "unit_concentration": body.unit_concentration,
        "unit_volume": body.unit_volume,
        "formula": formula,
    }


# --- Generate protocol ---

@router.post("/generate", response_model=ProtocolResponse, status_code=201)
async def generate_protocol(
    experiment_type: str = "general",
    cell_line: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> Protocol:
    """Generate a protocol scaffold from experiment type description."""
    # Build a template protocol based on experiment type
    templates = {
        "cytotoxicity": {
            "name": f"Cytotoxicity Assay Protocol{f' — {cell_line}' if cell_line else ''}",
            "description": f"Standard cytotoxicity assay protocol{f' for {cell_line} cells' if cell_line else ''}",
            "steps": [
                {"order": 1, "title": "Cell Seeding", "description": "Seed cells in 96-well plate at appropriate density", "duration": 30, "temp": 37.0, "equipment": "Biosafety Cabinet, Incubator", "reagents": [{"name": "DMEM + 10% FBS", "volume": 100, "unit": "uL"}]},
                {"order": 2, "title": "Incubation (24h)", "description": "Allow cells to attach and reach 70-80% confluency", "duration": 1440, "temp": 37.0, "equipment": "CO2 Incubator"},
                {"order": 3, "title": "Compound Treatment", "description": "Add compound dilutions to wells in triplicate", "duration": 60, "temp": 22.0, "equipment": "Liquid Handler"},
                {"order": 4, "title": "Incubation (48h)", "description": "Incubate with compound for 48 hours", "duration": 2880, "temp": 37.0, "equipment": "CO2 Incubator"},
                {"order": 5, "title": "Viability Readout", "description": "Add CellTiter-Glo reagent and read luminescence", "duration": 30, "temp": 22.0, "equipment": "Plate Reader"},
                {"order": 6, "title": "Data Analysis", "description": "Fit 4PL dose-response curves, calculate IC50", "duration": 60},
            ],
        },
        "transfection": {
            "name": f"Transfection Protocol{f' — {cell_line}' if cell_line else ''}",
            "description": f"Lipofection protocol{f' for {cell_line}' if cell_line else ''}",
            "steps": [
                {"order": 1, "title": "Cell Seeding", "description": "Seed cells at 60-70% confluency", "duration": 30, "temp": 37.0, "equipment": "Biosafety Cabinet"},
                {"order": 2, "title": "Prepare Complexes", "description": "Mix DNA and Lipofectamine in Opti-MEM", "duration": 25, "temp": 22.0, "reagents": [{"name": "Lipofectamine 3000", "volume": 3.75, "unit": "uL"}]},
                {"order": 3, "title": "Transfect", "description": "Add DNA-lipid complexes to cells", "duration": 15, "temp": 22.0},
                {"order": 4, "title": "Incubation", "description": "Incubate for 24-48h", "duration": 1440, "temp": 37.0, "equipment": "CO2 Incubator"},
                {"order": 5, "title": "Analysis", "description": "Assess transfection efficiency", "duration": 60, "equipment": "Fluorescence Microscope"},
            ],
        },
    }

    template = templates.get(experiment_type, {
        "name": f"Protocol — {experiment_type}",
        "description": f"Generated protocol for {experiment_type} experiment",
        "steps": [
            {"order": 1, "title": "Preparation", "description": "Prepare all reagents and equipment", "duration": 30},
            {"order": 2, "title": "Execution", "description": f"Execute {experiment_type} protocol steps", "duration": 120},
            {"order": 3, "title": "Analysis", "description": "Analyze results and document findings", "duration": 60},
        ],
    })

    protocol = Protocol(
        name=template["name"],
        description=template["description"],
        status="draft",
        is_template=True,
        tags=["auto-generated", experiment_type],
    )
    db.add(protocol)
    await db.flush()

    for s in template["steps"]:
        step = ProtocolStep(
            protocol_id=protocol.id,
            step_order=s["order"],
            title=s["title"],
            description=s.get("description"),
            duration_minutes=s.get("duration"),
            temperature_celsius=s.get("temp"),
            equipment=s.get("equipment"),
            reagents=s.get("reagents"),
        )
        db.add(step)
    await db.flush()
    await db.refresh(protocol)
    return protocol
