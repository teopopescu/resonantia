"""Durable pending approval model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from resonantia.models.base import Base, TimestampMixin, UUIDPrimaryKey


class PendingApprovalRecord(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "pending_approvals"
    __table_args__ = (
        UniqueConstraint("token", name="uq_pending_approvals_token"),
    )

    token: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    org_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    requested_by: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    decided_by: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    tool_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    tool_args: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    preview: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    gate_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), index=True, nullable=False, default="pending")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
