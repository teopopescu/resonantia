"""Plate mapping endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.db.session import get_db
from resonantia.dependencies import get_request_context
from resonantia.models.plate import PlateMap
from resonantia.models.request_context import RequestContext
from resonantia.schemas.plate import (
    AutoMapRequest,
    CherryPickRequest,
    PlateMapCreate,
    PlateMapResponse,
    PlateMapUpdate,
    SerialDilutionRequest,
    WorklistFormat,
    WorklistRequest,
)
from resonantia.services import plate_mapper

router = APIRouter()


@router.post("/", response_model=PlateMapResponse, status_code=201)
async def create_plate_map(
    body: PlateMapCreate,
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> PlateMap:
    if not ctx.can_write():
        raise HTTPException(status_code=403, detail="Member role required to create plate maps")
    pm = PlateMap(
        name=body.name,
        plate_type=body.plate_type.value,
        description=body.description,
        source_plates=body.source_plates,
        destination_plate=body.destination_plate,
        well_mappings=[m.model_dump() for m in body.well_mappings] if body.well_mappings else None,
        experiment_id=body.experiment_id,
        org_id=ctx.org_id,
    )
    db.add(pm)
    await db.flush()
    await db.refresh(pm)
    return pm


@router.get("/", response_model=list[PlateMapResponse])
async def list_plate_maps(
    skip: int = 0,
    limit: int = 50,
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> list[PlateMap]:
    result = await db.execute(
        select(PlateMap)
        .where(PlateMap.org_id == ctx.org_id)
        .order_by(PlateMap.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/{plate_map_id}", response_model=PlateMapResponse)
async def get_plate_map(
    plate_map_id: uuid.UUID,
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> PlateMap:
    pm = await db.get(PlateMap, plate_map_id)
    if not pm or pm.org_id != ctx.org_id:
        raise HTTPException(status_code=404, detail="Plate map not found")
    return pm


@router.patch("/{plate_map_id}", response_model=PlateMapResponse)
async def update_plate_map(
    plate_map_id: uuid.UUID,
    body: PlateMapUpdate,
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> PlateMap:
    if not ctx.can_write():
        raise HTTPException(status_code=403, detail="Member role required to update plate maps")
    pm = await db.get(PlateMap, plate_map_id)
    if not pm or pm.org_id != ctx.org_id:
        raise HTTPException(status_code=404, detail="Plate map not found")
    update_data = body.model_dump(exclude_unset=True)
    if "well_mappings" in update_data and update_data["well_mappings"] is not None:
        update_data["well_mappings"] = [
            m.model_dump() if hasattr(m, "model_dump") else m
            for m in update_data["well_mappings"]
        ]
    for k, v in update_data.items():
        setattr(pm, k, v)
    await db.flush()
    await db.refresh(pm)
    return pm


@router.delete("/{plate_map_id}", status_code=204)
async def delete_plate_map(
    plate_map_id: uuid.UUID,
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> None:
    if not ctx.can_write():
        raise HTTPException(status_code=403, detail="Member role required to delete plate maps")
    pm = await db.get(PlateMap, plate_map_id)
    if not pm or pm.org_id != ctx.org_id:
        raise HTTPException(status_code=404, detail="Plate map not found")
    await db.delete(pm)


@router.post("/{plate_map_id}/worklist")
async def generate_worklist(
    plate_map_id: uuid.UUID,
    body: WorklistRequest,
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> PlainTextResponse:
    if not ctx.can_write():
        raise HTTPException(status_code=403, detail="Member role required to generate worklists")
    pm = await db.get(PlateMap, plate_map_id)
    if not pm or pm.org_id != ctx.org_id:
        raise HTTPException(status_code=404, detail="Plate map not found")
    if not pm.well_mappings:
        raise HTTPException(status_code=400, detail="Plate map has no well mappings")

    content = plate_mapper.generate_worklist(pm.well_mappings, fmt=body.format.value)

    ext_map = {
        WorklistFormat.ECHO: "csv",
        WorklistFormat.HAMILTON: "gwl",
        WorklistFormat.OPENTRONS: "py",
    }
    filename = f"{pm.name}_worklist.{ext_map[body.format]}"

    return PlainTextResponse(
        content,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/auto-map", response_model=dict[str, Any])
async def auto_map(
    body: AutoMapRequest,
    ctx: RequestContext = Depends(get_request_context),
) -> dict[str, Any]:
    """AI-assisted plate mapping using rule-based logic."""
    result = plate_mapper.generate_plate_map(
        sources=body.source_plates,
        destination_type=body.destination_type.value,
        mapping_rules={"description": body.mapping_rules} if body.mapping_rules else None,
    )
    errors = plate_mapper.validate_mapping(result.get("well_mappings", []))
    result["validation_errors"] = errors
    return result


@router.post("/cherry-pick", response_model=dict[str, Any])
async def cherry_pick(
    body: CherryPickRequest,
    ctx: RequestContext = Depends(get_request_context),
) -> dict[str, Any]:
    if not ctx.can_write():
        raise HTTPException(status_code=403, detail="Member role required to cherry-pick wells")
    return plate_mapper.cherry_pick(
        source_plates=body.source_plates,
        hit_list=body.hit_list,
        destination_type=body.destination_type.value,
    )


@router.post("/serial-dilution", response_model=dict[str, Any])
async def serial_dilution(
    body: SerialDilutionRequest,
    ctx: RequestContext = Depends(get_request_context),
) -> dict[str, Any]:
    if not ctx.can_write():
        raise HTTPException(status_code=403, detail="Member role required to generate serial dilutions")
    return plate_mapper.serial_dilution(
        compound=body.compound,
        start_concentration=body.start_concentration,
        dilution_factor=body.dilution_factor,
        num_points=body.num_points,
        replicates=body.replicates,
        plate_type=body.plate_type.value,
    )
