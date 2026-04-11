"""Plate map ORM model."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from resonantia.models.base import Base, TimestampMixin, UUIDPrimaryKey


class PlateMap(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "plate_maps"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plate_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default="96"
    )  # "96" or "384"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_plates: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    destination_plate: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    well_mappings: Mapped[list | None] = mapped_column(JSON, nullable=True)
    worklist_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    experiment_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="SET NULL"),
        nullable=True,
    )
    experiment: Mapped["Experiment | None"] = relationship(  # noqa: F821
        back_populates="plate_maps",
        lazy="selectin",
    )
