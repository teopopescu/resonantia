"""Pydantic schemas for protocols."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# --- Step schemas ---

class StepCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    step_order: int = Field(..., ge=1)
    duration_minutes: float | None = None
    temperature_celsius: float | None = None
    equipment: str | None = None
    reagents: list[dict[str, Any]] | None = None
    parameters: dict[str, Any] | None = None
    notes: str | None = None


class StepUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    step_order: int | None = None
    duration_minutes: float | None = None
    temperature_celsius: float | None = None
    equipment: str | None = None
    reagents: list[dict[str, Any]] | None = None
    parameters: dict[str, Any] | None = None
    notes: str | None = None


class StepResponse(BaseModel):
    id: uuid.UUID
    protocol_id: uuid.UUID
    step_order: int
    title: str
    description: str | None
    duration_minutes: float | None
    temperature_celsius: float | None
    equipment: str | None
    reagents: list[dict[str, Any]] | None
    parameters: dict[str, Any] | None
    notes: str | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


# --- Protocol schemas ---

class ProtocolCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    is_template: bool = False
    experiment_id: uuid.UUID | None = None
    author_id: str | None = None
    tags: list[str] | None = None
    steps: list[StepCreate] | None = None


class ProtocolUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_template: bool | None = None
    tags: list[str] | None = None


class ProtocolResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    version: int
    status: str
    is_template: bool
    parent_protocol_id: uuid.UUID | None
    author_id: str | None
    experiment_id: uuid.UUID | None
    tags: list[str] | None
    steps: list[StepResponse] = []
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class ProtocolListResponse(BaseModel):
    id: uuid.UUID
    name: str
    version: int
    status: str
    is_template: bool
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


# --- Inventory check ---

class InventoryCheckResponse(BaseModel):
    protocol_id: uuid.UUID
    protocol_name: str
    reagents: list[dict[str, Any]]
    all_available: bool


# --- Dilution calculator ---

class DilutionRequest(BaseModel):
    c1: float = Field(..., gt=0, description="Initial concentration")
    v1: float | None = Field(None, gt=0, description="Initial volume (solve if None)")
    c2: float = Field(..., gt=0, description="Final concentration")
    v2: float | None = Field(None, gt=0, description="Final volume (solve if None)")
    unit_concentration: str = "uM"
    unit_volume: str = "uL"


class DilutionResponse(BaseModel):
    c1: float
    v1: float
    c2: float
    v2: float
    unit_concentration: str
    unit_volume: str
    formula: str
