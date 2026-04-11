"""ELN Entry and Appendix ORM models."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from resonantia.models.base import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from resonantia.models.experiment import Experiment


class ELNEntry(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "eln_entries"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    entry_number: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    content_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="draft"
    )  # draft | submitted | archived
    version: Mapped[int] = mapped_column(Integer, default=1)
    experiment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="SET NULL"),
        nullable=True,
    )
    author_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    embedded_figures: Mapped[list | None] = mapped_column(JSON, nullable=True)
    linked_references: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Relationships
    experiment: Mapped["Experiment | None"] = relationship(
        lazy="selectin",
    )
    appendices: Mapped[list["ELNAppendix"]] = relationship(
        back_populates="eln_entry",
        lazy="selectin",
        order_by="ELNAppendix.appendix_number",
    )


class ELNAppendix(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "eln_appendices"

    eln_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("eln_entries.id", ondelete="CASCADE"),
        nullable=False,
    )
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    appendix_number: Mapped[int] = mapped_column(Integer, nullable=False)

    eln_entry: Mapped["ELNEntry"] = relationship(
        back_populates="appendices",
    )
