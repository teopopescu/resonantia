"""Protocol and ProtocolStep ORM models."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from resonantia.models.base import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from resonantia.models.experiment import Experiment


class Protocol(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "protocols"

    org_id: Mapped[str] = mapped_column(String(255), index=True, default="org_default")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="draft"
    )  # draft | published | archived
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_protocol_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("protocols.id", ondelete="SET NULL"),
        nullable=True,
    )
    author_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    experiment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="SET NULL"),
        nullable=True,
    )
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Relationships
    experiment: Mapped["Experiment | None"] = relationship(lazy="selectin")
    steps: Mapped[list["ProtocolStep"]] = relationship(
        back_populates="protocol",
        lazy="selectin",
        order_by="ProtocolStep.step_order",
        cascade="all, delete-orphan",
    )
    parent_protocol: Mapped["Protocol | None"] = relationship(
        remote_side="Protocol.id",
        lazy="selectin",
    )


class ProtocolStep(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "protocol_steps"

    protocol_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("protocols.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature_celsius: Mapped[float | None] = mapped_column(Float, nullable=True)
    equipment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reagents: Mapped[list | None] = mapped_column(JSON, nullable=True)
    parameters: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    protocol: Mapped["Protocol"] = relationship(back_populates="steps")
