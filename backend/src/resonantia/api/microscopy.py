"""Microscopy image endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.db.session import get_db
from resonantia.dependencies import get_org_context
from resonantia.models.microscopy import MicroscopyImage
from resonantia.schemas.microscopy import (
    MicroscopyImageResponse,
    MontageRequest,
)
from resonantia.services.microscopy import generate_montage, save_image

router = APIRouter()


@router.post("/upload", response_model=MicroscopyImageResponse, status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    experiment_id: uuid.UUID | None = Form(None),
    plate_id: uuid.UUID | None = Form(None),
    well: str | None = Form(None),
    channel: str | None = Form(None),
    fov: int | None = Form(None),
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> MicroscopyImageResponse:
    contents = await file.read()
    image_path, thumbnail_path = await save_image(contents, file.filename or "image.png")

    img = MicroscopyImage(
        experiment_id=experiment_id,
        plate_id=plate_id,
        well=well,
        channel=channel,
        fov=fov,
        image_path=image_path,
        thumbnail_path=thumbnail_path,
        org_id=org_id,
    )
    db.add(img)
    await db.flush()
    await db.refresh(img)
    return MicroscopyImageResponse.from_orm_model(img)


@router.get("/images", response_model=list[MicroscopyImageResponse])
async def list_images(
    experiment_id: uuid.UUID | None = Query(None),
    plate_id: uuid.UUID | None = Query(None),
    well: str | None = Query(None),
    channel: str | None = Query(None),
    fov: int | None = Query(None),
    skip: int = 0,
    limit: int = 50,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> list[MicroscopyImageResponse]:
    stmt = select(MicroscopyImage).where(MicroscopyImage.org_id == org_id).order_by(MicroscopyImage.created_at.desc())
    if experiment_id:
        stmt = stmt.where(MicroscopyImage.experiment_id == experiment_id)
    if plate_id:
        stmt = stmt.where(MicroscopyImage.plate_id == plate_id)
    if well:
        stmt = stmt.where(MicroscopyImage.well == well)
    if channel:
        stmt = stmt.where(MicroscopyImage.channel == channel)
    if fov is not None:
        stmt = stmt.where(MicroscopyImage.fov == fov)
    result = await db.execute(stmt.offset(skip).limit(limit))
    return [MicroscopyImageResponse.from_orm_model(i) for i in result.scalars().all()]


@router.get("/images/{image_id}", response_model=MicroscopyImageResponse)
async def get_image(
    image_id: uuid.UUID,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> MicroscopyImageResponse:
    img = await db.get(MicroscopyImage, image_id)
    if not img or img.org_id != org_id:
        raise HTTPException(status_code=404, detail="Image not found")
    return MicroscopyImageResponse.from_orm_model(img)


@router.get("/images/{image_id}/file")
async def get_image_file(
    image_id: uuid.UUID,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    img = await db.get(MicroscopyImage, image_id)
    if not img or img.org_id != org_id:
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(img.image_path)


@router.get("/images/{image_id}/thumbnail")
async def get_thumbnail(
    image_id: uuid.UUID,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    img = await db.get(MicroscopyImage, image_id)
    if not img or img.org_id != org_id or not img.thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return FileResponse(img.thumbnail_path)


@router.post("/montage")
async def create_montage(
    body: MontageRequest,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    paths: list[str] = []
    for img_id in body.image_ids:
        img = await db.get(MicroscopyImage, img_id)
        if not img or img.org_id != org_id:
            raise HTTPException(status_code=404, detail=f"Image {img_id} not found")
        paths.append(img.image_path)

    montage_path = await generate_montage(paths, columns=body.columns)
    return FileResponse(montage_path, media_type="image/png")
