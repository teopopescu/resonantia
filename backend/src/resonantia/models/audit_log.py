"""Append-only audit log model."""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from resonantia.models.base import Base, TimestampMixin, UUIDPrimaryKey


class AuditLog(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "audit_log"

    org_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    metadata_extra: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
