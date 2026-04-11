"""Pydantic schemas for plate mapping."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PlateType(str, Enum):
    PLATE_96 = "96"
    PLATE_384 = "384"


class WorklistFormat(str, Enum):
    ECHO = "echo"
    HAMILTON = "hamilton"
    OPENTRONS = "opentrons"


class WellMapping(BaseModel):
    source_plate: str
    source_well: str
    destination_well: str
    volume: float | None = None
    concentration: float | None = None


class PlateMapCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    plate_type: PlateType = PlateType.PLATE_96
    description: str | None = None
    source_plates: dict[str, Any] | None = None
    destination_plate: dict[str, Any] | None = None
    well_mappings: list[WellMapping] | None = None
    experiment_id: uuid.UUID | None = None


class PlateMapUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    source_plates: dict[str, Any] | None = None
    destination_plate: dict[str, Any] | None = None
    well_mappings: list[WellMapping] | None = None


class PlateMapResponse(BaseModel):
    id: uuid.UUID
    name: str
    plate_type: str
    description: str | None
    source_plates: dict[str, Any] | None
    destination_plate: dict[str, Any] | None
    well_mappings: list[dict[str, Any]] | None
    worklist_data: dict[str, Any] | None
    experiment_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class WorklistRequest(BaseModel):
    format: WorklistFormat = WorklistFormat.ECHO


class AutoMapRequest(BaseModel):
    """AI-assisted plate mapping request."""

    source_plates: list[dict[str, Any]]
    destination_type: PlateType = PlateType.PLATE_96
    mapping_rules: str | None = Field(
        None,
        description="Natural-language description of mapping rules, e.g. 'cherry-pick hits from column 3'",
    )


class CherryPickRequest(BaseModel):
    source_plates: list[dict[str, Any]]
    hit_list: list[str] = Field(..., description="List of well IDs to pick")
    destination_type: PlateType = PlateType.PLATE_96


class SerialDilutionRequest(BaseModel):
    compound: str
    start_concentration: float
    dilution_factor: float = 3.0
    num_points: int = 8
    replicates: int = 1
    plate_type: PlateType = PlateType.PLATE_96
