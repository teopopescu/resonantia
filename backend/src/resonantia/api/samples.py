"""Sample / reagent tracking endpoints."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.db.session import get_db
from resonantia.dependencies import get_org_context
from resonantia.models.sample import Sample
from resonantia.schemas.sample import (
    BarcodeScanRequest,
    SampleCreate,
    SampleResponse,
    SampleUpdate,
)

router = APIRouter()


@router.post("/", response_model=SampleResponse, status_code=201)
async def create_sample(
    body: SampleCreate,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> SampleResponse:
    sample = Sample(
        name=body.name,
        barcode=body.barcode,
        sample_type=body.sample_type,
        location=body.location,
        storage_temp=body.storage_temp,
        lot_number=body.lot_number,
        expiry_date=body.expiry_date,
        quantity=body.quantity,
        unit=body.unit,
        description=body.description,
        metadata_extra=body.metadata,
        org_id=org_id,
    )
    db.add(sample)
    await db.flush()
    await db.refresh(sample)
    return SampleResponse.from_orm_model(sample)


@router.get("/", response_model=list[SampleResponse])
async def list_samples(
    skip: int = 0,
    limit: int = 50,
    sample_type: str | None = None,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> list[SampleResponse]:
    stmt = select(Sample).where(Sample.org_id == org_id).order_by(Sample.created_at.desc())
    if sample_type:
        stmt = stmt.where(Sample.sample_type == sample_type)
    result = await db.execute(stmt.offset(skip).limit(limit))
    return [SampleResponse.from_orm_model(s) for s in result.scalars().all()]


@router.get("/expiring", response_model=list[SampleResponse])
async def get_expiring_samples(
    days: int = Query(default=30, ge=1),
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> list[SampleResponse]:
    cutoff = date.today() + timedelta(days=days)
    result = await db.execute(
        select(Sample)
        .where(Sample.org_id == org_id)
        .where(Sample.expiry_date.isnot(None))
        .where(Sample.expiry_date <= cutoff)
        .order_by(Sample.expiry_date)
    )
    return [SampleResponse.from_orm_model(s) for s in result.scalars().all()]


@router.get("/low-stock", response_model=list[SampleResponse])
async def get_low_stock(
    threshold: float = Query(default=10.0),
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> list[SampleResponse]:
    result = await db.execute(
        select(Sample)
        .where(Sample.org_id == org_id)
        .where(Sample.quantity.isnot(None))
        .where(Sample.quantity <= threshold)
        .order_by(Sample.quantity)
    )
    return [SampleResponse.from_orm_model(s) for s in result.scalars().all()]


@router.post("/scan", response_model=SampleResponse)
async def scan_barcode(
    body: BarcodeScanRequest,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> SampleResponse:
    result = await db.execute(
        select(Sample).where(Sample.org_id == org_id, Sample.barcode == body.barcode)
    )
    sample = result.scalar_one_or_none()
    if not sample:
        raise HTTPException(status_code=404, detail="No sample found for barcode")
    return SampleResponse.from_orm_model(sample)


@router.get("/{sample_id}", response_model=SampleResponse)
async def get_sample(
    sample_id: uuid.UUID,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> SampleResponse:
    sample = await db.get(Sample, sample_id)
    if not sample or sample.org_id != org_id:
        raise HTTPException(status_code=404, detail="Sample not found")
    return SampleResponse.from_orm_model(sample)


@router.patch("/{sample_id}", response_model=SampleResponse)
async def update_sample(
    sample_id: uuid.UUID,
    body: SampleUpdate,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> SampleResponse:
    sample = await db.get(Sample, sample_id)
    if not sample or sample.org_id != org_id:
        raise HTTPException(status_code=404, detail="Sample not found")
    update_data = body.model_dump(exclude_unset=True)
    if "metadata" in update_data:
        update_data["metadata_extra"] = update_data.pop("metadata")
    for k, v in update_data.items():
        setattr(sample, k, v)
    await db.flush()
    await db.refresh(sample)
    return SampleResponse.from_orm_model(sample)


@router.delete("/{sample_id}", status_code=204)
async def delete_sample(
    sample_id: uuid.UUID,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> None:
    sample = await db.get(Sample, sample_id)
    if not sample or sample.org_id != org_id:
        raise HTTPException(status_code=404, detail="Sample not found")
    await db.delete(sample)
