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


def upgrade() -> None:
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
    op.create_index("ix_voice_turns_org_id", "voice_turns", ["org_id"])
    op.create_index("ix_voice_turns_created_by", "voice_turns", ["created_by"])
    op.create_index("ix_voice_turns_status", "voice_turns", ["status"])
    op.create_index("ix_voice_turns_workflow_id", "voice_turns", ["workflow_id"])
    op.create_index("ix_voice_turns_conversation_id", "voice_turns", ["conversation_id"])
    op.create_index("ix_voice_turns_output_audio_id", "voice_turns", ["output_audio_id"])
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
