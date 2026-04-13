"""Microscopy image ORM model."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from resonantia.models.base import Base, TimestampMixin, UUIDPrimaryKey


class MicroscopyImage(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "microscopy_images"

    org_id: Mapped[str] = mapped_column(String(255), index=True, default="org_default")
    experiment_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    plate_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plate_maps.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    well: Mapped[str | None] = mapped_column(String(8), nullable=True, index=True)
    channel: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fov: Mapped[int | None] = mapped_column(Integer, nullable=True)

    image_path: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_extra: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
