"""add voice turns table

Revision ID: 20260515_voice_turns
Revises: 20260515_phase2
Create Date: 2026-05-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260515_voice_turns"
down_revision = "20260515_phase2"
branch_labels = None
depends_on = None


def _json_type():
    bind = op.get_bind()
    if bind is not None and bind.dialect.name == "postgresql":
        return postgresql.JSONB(astext_type=sa.Text())
    return sa.JSON()


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    return bool(bind is not None and sa.inspect(bind).has_table(table_name))


def _indexes(table_name: str) -> set[str]:
    bind = op.get_bind()
    if bind is None:
        return set()
    inspector = sa.inspect(bind)
    if not inspector.has_table(table_name):
        return set()
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    if not _has_table("voice_turns"):
        op.create_table(
            "voice_turns",
            sa.Column("org_id", sa.String(length=255), nullable=False),
            sa.Column("created_by", sa.String(length=255), nullable=True),
            sa.Column("idempotency_key", sa.String(length=128), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("workflow_id", sa.String(length=255), nullable=True),
            sa.Column("conversation_id", sa.String(length=255), nullable=True),
            sa.Column("input_audio_path", sa.Text(), nullable=True),
            sa.Column("transcript", sa.Text(), nullable=True),
            sa.Column("response_text", sa.Text(), nullable=True),
            sa.Column("output_audio_id", sa.String(length=255), nullable=True),
            sa.Column("intent_class", sa.String(length=100), nullable=True),
            sa.Column("tool_calls", _json_type(), nullable=True),
            sa.Column("stt_latency_ms", sa.Integer(), nullable=True),
            sa.Column("agent_latency_ms", sa.Integer(), nullable=True),
            sa.Column("tts_latency_ms", sa.Integer(), nullable=True),
            sa.Column("total_latency_ms", sa.Integer(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("org_id", "idempotency_key", name="uq_voice_turns_org_idempotency"),
        )

    indexes = _indexes("voice_turns")
    if "ix_voice_turns_org_id" not in indexes:
        op.create_index("ix_voice_turns_org_id", "voice_turns", ["org_id"])
    if "ix_voice_turns_created_by" not in indexes:
        op.create_index("ix_voice_turns_created_by", "voice_turns", ["created_by"])
    if "ix_voice_turns_status" not in indexes:
        op.create_index("ix_voice_turns_status", "voice_turns", ["status"])
    if "ix_voice_turns_workflow_id" not in indexes:
        op.create_index("ix_voice_turns_workflow_id", "voice_turns", ["workflow_id"])
    if "ix_voice_turns_conversation_id" not in indexes:
        op.create_index("ix_voice_turns_conversation_id", "voice_turns", ["conversation_id"])
    if "ix_voice_turns_output_audio_id" not in indexes:
        op.create_index("ix_voice_turns_output_audio_id", "voice_turns", ["output_audio_id"])
    if "ix_voice_turns_intent_class" not in indexes:
        op.create_index("ix_voice_turns_intent_class", "voice_turns", ["intent_class"])


def downgrade() -> None:
    op.drop_index("ix_voice_turns_intent_class", table_name="voice_turns")
    op.drop_index("ix_voice_turns_output_audio_id", table_name="voice_turns")
    op.drop_index("ix_voice_turns_conversation_id", table_name="voice_turns")
    op.drop_index("ix_voice_turns_workflow_id", table_name="voice_turns")
    op.drop_index("ix_voice_turns_status", table_name="voice_turns")
    op.drop_index("ix_voice_turns_created_by", table_name="voice_turns")
    op.drop_index("ix_voice_turns_org_id", table_name="voice_turns")
    op.drop_table("voice_turns")
