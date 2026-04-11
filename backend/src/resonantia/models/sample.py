"""Sample / reagent ORM model."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from resonantia.models.base import Base, TimestampMixin, UUIDPrimaryKey


class Sample(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "samples"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    barcode: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True, index=True
    )
    sample_type: Mapped[str] = mapped_column(
        String(64), nullable=False, default="reagent"
    )  # reagent, compound, cell_line, etc.
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_temp: Mapped[float | None] = mapped_column(Float, nullable=True)
    freeze_thaw_count: Mapped[int] = mapped_column(default=0)
    lot_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_extra: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
