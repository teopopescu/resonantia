"""Pydantic schemas for microscopy images."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MicroscopyImageCreate(BaseModel):
    experiment_id: uuid.UUID | None = None
    plate_id: uuid.UUID | None = None
    well: str | None = None
    channel: str | None = None
    fov: int | None = None
    metadata: dict[str, Any] | None = None


class MicroscopyImageResponse(BaseModel):
    id: uuid.UUID
    experiment_id: uuid.UUID | None
    plate_id: uuid.UUID | None
    well: str | None
    channel: str | None
    fov: int | None
    image_path: str
    thumbnail_path: str | None
    metadata: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, obj: Any) -> "MicroscopyImageResponse":
        return cls(
            id=obj.id,
            experiment_id=obj.experiment_id,
            plate_id=obj.plate_id,
            well=obj.well,
            channel=obj.channel,
            fov=obj.fov,
            image_path=obj.image_path,
            thumbnail_path=obj.thumbnail_path,
            metadata=obj.metadata_extra,
            created_at=obj.created_at,
        )


class MicroscopyFilterParams(BaseModel):
    experiment_id: uuid.UUID | None = None
    plate_id: uuid.UUID | None = None
    well: str | None = None
    channel: str | None = None
    fov: int | None = None


class MontageRequest(BaseModel):
    image_ids: list[uuid.UUID] = Field(..., min_length=1)
    columns: int = Field(default=4, ge=1, le=24)
