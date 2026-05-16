"""Tighten idempotency enforcement for processing and voice turns.

Revision ID: 20260516_idempotency
Revises: 20260515_voice_turns
Create Date: 2026-05-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260516_idempotency"
down_revision = "20260515_voice_turns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_voice_turns_org_idempotency", "voice_turns", type_="unique")
    op.alter_column(
        "voice_turns",
        "idempotency_key",
        existing_type=sa.String(length=128),
        nullable=True,
    )
    op.create_index(
        "uq_voice_turns_org_idempotency",
        "voice_turns",
        ["org_id", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_voice_turns_org_idempotency", table_name="voice_turns")
    op.alter_column(
        "voice_turns",
        "idempotency_key",
        existing_type=sa.String(length=128),
        nullable=False,
    )
    op.create_unique_constraint(
        "uq_voice_turns_org_idempotency",
        "voice_turns",
        ["org_id", "idempotency_key"],
    )
