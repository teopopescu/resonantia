"""Pydantic schemas for samples and reagents."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class SampleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    barcode: str | None = None
    sample_type: str = "reagent"
    location: str | None = None
    storage_temp: float | None = None
    lot_number: str | None = None
    expiry_date: date | None = None
    quantity: float | None = None
    unit: str | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None


class SampleUpdate(BaseModel):
    name: str | None = None
    barcode: str | None = None
    sample_type: str | None = None
    location: str | None = None
    storage_temp: float | None = None
    freeze_thaw_count: int | None = None
    lot_number: str | None = None
    expiry_date: date | None = None
    quantity: float | None = None
    unit: str | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None


class SampleResponse(BaseModel):
    id: uuid.UUID
    name: str
    barcode: str | None
    sample_type: str
    location: str | None
    storage_temp: float | None
    freeze_thaw_count: int
    lot_number: str | None
    expiry_date: date | None
    quantity: float | None
    unit: str | None
    description: str | None
    metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, obj: Any) -> "SampleResponse":
        """Map ORM model (which uses metadata_extra) to response schema."""
        return cls(
            id=obj.id,
            name=obj.name,
            barcode=obj.barcode,
            sample_type=obj.sample_type,
            location=obj.location,
            storage_temp=obj.storage_temp,
            freeze_thaw_count=obj.freeze_thaw_count,
            lot_number=obj.lot_number,
            expiry_date=obj.expiry_date,
            quantity=obj.quantity,
            unit=obj.unit,
            description=obj.description,
            metadata=obj.metadata_extra,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )


class BarcodeScanRequest(BaseModel):
    barcode: str = Field(..., min_length=1)
