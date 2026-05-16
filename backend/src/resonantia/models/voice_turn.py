"""Durable voice turn records."""

from __future__ import annotations

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text

from resonantia.models.base import Base, TimestampMixin, UUIDPrimaryKey


class VoiceTurn(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "voice_turns"
    __table_args__ = (
        Index(
            "uq_voice_turns_org_idempotency",
            "org_id",
            "idempotency_key",
            unique=True,
            postgresql_where=text("idempotency_key IS NOT NULL"),
            sqlite_where=text("idempotency_key IS NOT NULL"),
        ),
    )

    org_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(50), index=True, nullable=False, default="processing")
    workflow_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    conversation_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    input_audio_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_audio_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    intent_class: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    tool_calls: Mapped[list | None] = mapped_column(JSON, nullable=True)
    stt_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    agent_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tts_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
