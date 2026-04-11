"""Pydantic schemas for experiments."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from resonantia.schemas.plate import PlateMapResponse


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExperimentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    protocol: str | None = None
    status: ExperimentStatus = ExperimentStatus.DRAFT


class ExperimentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    protocol: str | None = None
    status: ExperimentStatus | None = None
    results: dict[str, Any] | None = None


class ExperimentResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    protocol: str | None
    status: str
    results: dict[str, Any] | None
    plate_maps: list[PlateMapResponse]
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class ExperimentListResponse(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}
