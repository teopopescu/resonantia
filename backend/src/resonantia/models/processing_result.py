"""Durable processing result records with org-scoped idempotency."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from resonantia.models.base import Base, TimestampMixin, UUIDPrimaryKey


class ProcessingResult(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "processing_results"
    __table_args__ = (
        UniqueConstraint("org_id", "idempotency_key", name="uq_processing_results_org_idempotency"),
    )

    org_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    analysis_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    result: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    file_upload_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("file_uploads.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    experiment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("experiments.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
