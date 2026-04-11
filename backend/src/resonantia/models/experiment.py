"""Experiment ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from resonantia.models.base import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from resonantia.models.plate import PlateMap


class Experiment(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "experiments"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    protocol: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="draft"
    )  # draft | running | completed | failed
    results: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    plate_maps: Mapped[list["PlateMap"]] = relationship(
        back_populates="experiment",
        lazy="selectin",
    )
