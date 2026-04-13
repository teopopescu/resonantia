"""Experiment management endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.db.session import get_db
from resonantia.dependencies import get_org_context
from resonantia.models.experiment import Experiment
from resonantia.schemas.experiment import (
    ExperimentCreate,
    ExperimentListResponse,
    ExperimentResponse,
    ExperimentUpdate,
)

router = APIRouter()


@router.post("/", response_model=ExperimentResponse, status_code=201)
async def create_experiment(
    body: ExperimentCreate,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> Experiment:
    exp = Experiment(
        name=body.name,
        description=body.description,
        protocol=body.protocol,
        status=body.status.value,
        org_id=org_id,
    )
    db.add(exp)
    await db.flush()
    await db.refresh(exp)
    return exp


@router.get("/", response_model=list[ExperimentListResponse])
async def list_experiments(
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> list[Experiment]:
    stmt = select(Experiment).where(Experiment.org_id == org_id).order_by(Experiment.created_at.desc())
    if status:
        stmt = stmt.where(Experiment.status == status)
    result = await db.execute(stmt.offset(skip).limit(limit))
    return list(result.scalars().all())


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: uuid.UUID,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> Experiment:
    exp = await db.get(Experiment, experiment_id)
    if not exp or exp.org_id != org_id:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp


@router.patch("/{experiment_id}", response_model=ExperimentResponse)
async def update_experiment(
    experiment_id: uuid.UUID,
    body: ExperimentUpdate,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> Experiment:
    exp = await db.get(Experiment, experiment_id)
    if not exp or exp.org_id != org_id:
        raise HTTPException(status_code=404, detail="Experiment not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        if k == "status" and v is not None:
            v = v.value if hasattr(v, "value") else v
        setattr(exp, k, v)
    await db.flush()
    await db.refresh(exp)
    return exp


@router.delete("/{experiment_id}", status_code=204)
async def delete_experiment(
    experiment_id: uuid.UUID,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> None:
    exp = await db.get(Experiment, experiment_id)
    if not exp or exp.org_id != org_id:
        raise HTTPException(status_code=404, detail="Experiment not found")
    await db.delete(exp)


@router.post("/{experiment_id}/process", status_code=202)
async def trigger_processing(
    experiment_id: uuid.UUID,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> dict:
    exp = await db.get(Experiment, experiment_id)
    if not exp or exp.org_id != org_id:
        raise HTTPException(status_code=404, detail="Experiment not found")
    exp.status = "running"
    await db.flush()
    return {"status": "processing_started", "experiment_id": str(experiment_id)}


@router.get("/{experiment_id}/results")
async def get_results(
    experiment_id: uuid.UUID,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> dict:
    exp = await db.get(Experiment, experiment_id)
    if not exp or exp.org_id != org_id:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"experiment_id": str(experiment_id), "results": exp.results}
