"""add production phase 2 tables

Revision ID: 20260515_phase2
Revises:
Create Date: 2026-05-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260515_phase2"
down_revision = None
branch_labels = None
depends_on = None


def _json_type():
    bind = op.get_bind()
    if bind is not None and bind.dialect.name == "postgresql":
        return postgresql.JSONB(astext_type=sa.Text())
    return sa.JSON()


def _columns(table_name: str) -> set[str]:
    bind = op.get_bind()
    if bind is None:
        return set()
    inspector = sa.inspect(bind)
    if not inspector.has_table(table_name):
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _indexes(table_name: str) -> set[str]:
    bind = op.get_bind()
    if bind is None:
        return set()
    inspector = sa.inspect(bind)
    if not inspector.has_table(table_name):
        return set()
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    return bool(bind is not None and sa.inspect(bind).has_table(table_name))


def _ensure_current_schema_for_fresh_database() -> None:
    """Bootstrap a blank database so local `alembic upgrade head` works.

    The original project used SQLAlchemy `create_all` for the initial schema and
    added Alembic after tables already existed. Before external production use,
    a blank database should still be migratable, so this migration creates the
    current metadata only when no baseline tables are present. The rest of this
    file is idempotent and will skip objects that already exist.
    """
    bind = op.get_bind()
    if bind is None or _has_table("file_uploads"):
        return

    from resonantia.models import Base

    Base.metadata.create_all(bind=bind)


def upgrade() -> None:
    _ensure_current_schema_for_fresh_database()

    file_columns = _columns("file_uploads")
    if "uploaded_by" not in file_columns:
        op.add_column("file_uploads", sa.Column("uploaded_by", sa.String(length=255), nullable=True))
    if "checksum_sha256" not in file_columns:
        op.add_column("file_uploads", sa.Column("checksum_sha256", sa.String(length=64), nullable=True))
    if "storage_backend" not in file_columns:
        op.add_column(
            "file_uploads",
            sa.Column("storage_backend", sa.String(length=50), nullable=False, server_default="local"),
        )
    if "content_bytes" not in file_columns:
        op.add_column("file_uploads", sa.Column("content_bytes", sa.LargeBinary(), nullable=True))
    if "detected_format" not in file_columns:
        op.add_column("file_uploads", sa.Column("detected_format", sa.String(length=100), nullable=True))

    file_indexes = _indexes("file_uploads")
    if "ix_file_uploads_uploaded_by" not in file_indexes:
        op.create_index("ix_file_uploads_uploaded_by", "file_uploads", ["uploaded_by"])
    if "ix_file_uploads_checksum_sha256" not in file_indexes:
        op.create_index("ix_file_uploads_checksum_sha256", "file_uploads", ["checksum_sha256"])
    if "ix_file_uploads_detected_format" not in file_indexes:
        op.create_index("ix_file_uploads_detected_format", "file_uploads", ["detected_format"])

    if not _has_table("processing_results"):
        op.create_table(
            "processing_results",
            sa.Column("org_id", sa.String(length=255), nullable=False),
            sa.Column("created_by", sa.String(length=255), nullable=True),
            sa.Column("idempotency_key", sa.String(length=128), nullable=False),
            sa.Column("analysis_type", sa.String(length=100), nullable=False),
            sa.Column("parameters", _json_type(), nullable=False),
            sa.Column("result", _json_type(), nullable=False),
            sa.Column("file_upload_id", sa.UUID(), nullable=True),
            sa.Column("experiment_id", sa.UUID(), nullable=True),
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["file_upload_id"], ["file_uploads.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("org_id", "idempotency_key", name="uq_processing_results_org_idempotency"),
        )
    processing_indexes = _indexes("processing_results")
    if "ix_processing_results_org_id" not in processing_indexes:
        op.create_index("ix_processing_results_org_id", "processing_results", ["org_id"])
    if "ix_processing_results_created_by" not in processing_indexes:
        op.create_index("ix_processing_results_created_by", "processing_results", ["created_by"])
    if "ix_processing_results_analysis_type" not in processing_indexes:
        op.create_index("ix_processing_results_analysis_type", "processing_results", ["analysis_type"])
    if "ix_processing_results_file_upload_id" not in processing_indexes:
        op.create_index("ix_processing_results_file_upload_id", "processing_results", ["file_upload_id"])
    if "ix_processing_results_experiment_id" not in processing_indexes:
        op.create_index("ix_processing_results_experiment_id", "processing_results", ["experiment_id"])

    if not _has_table("audit_log"):
        op.create_table(
            "audit_log",
            sa.Column("org_id", sa.String(length=255), nullable=False),
            sa.Column("actor_user_id", sa.String(length=255), nullable=True),
            sa.Column("action", sa.String(length=100), nullable=False),
            sa.Column("target_type", sa.String(length=100), nullable=True),
            sa.Column("target_id", sa.String(length=255), nullable=True),
            sa.Column("request_id", sa.String(length=255), nullable=True),
            sa.Column("metadata_extra", _json_type(), nullable=False),
            sa.Column("message", sa.Text(), nullable=True),
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
    audit_indexes = _indexes("audit_log")
    if "ix_audit_log_org_id" not in audit_indexes:
        op.create_index("ix_audit_log_org_id", "audit_log", ["org_id"])
    if "ix_audit_log_actor_user_id" not in audit_indexes:
        op.create_index("ix_audit_log_actor_user_id", "audit_log", ["actor_user_id"])
    if "ix_audit_log_action" not in audit_indexes:
        op.create_index("ix_audit_log_action", "audit_log", ["action"])
    if "ix_audit_log_target_type" not in audit_indexes:
        op.create_index("ix_audit_log_target_type", "audit_log", ["target_type"])
    if "ix_audit_log_target_id" not in audit_indexes:
        op.create_index("ix_audit_log_target_id", "audit_log", ["target_id"])
    if "ix_audit_log_request_id" not in audit_indexes:
        op.create_index("ix_audit_log_request_id", "audit_log", ["request_id"])
    bind = op.get_bind()
    if bind is not None and bind.dialect.name == "postgresql":
        op.execute("REVOKE UPDATE, DELETE ON audit_log FROM PUBLIC")

    if not _has_table("pending_approvals"):
        op.create_table(
            "pending_approvals",
            sa.Column("token", sa.String(length=255), nullable=False),
            sa.Column("org_id", sa.String(length=255), nullable=False),
            sa.Column("requested_by", sa.String(length=255), nullable=False),
            sa.Column("decided_by", sa.String(length=255), nullable=True),
            sa.Column("tool_name", sa.String(length=255), nullable=False),
            sa.Column("tool_args", _json_type(), nullable=False),
            sa.Column("preview", _json_type(), nullable=False),
            sa.Column("gate_kind", sa.String(length=50), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("result", _json_type(), nullable=True),
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token", name="uq_pending_approvals_token"),
        )
    pending_indexes = _indexes("pending_approvals")
    if "ix_pending_approvals_token" not in pending_indexes:
        op.create_index("ix_pending_approvals_token", "pending_approvals", ["token"])
    if "ix_pending_approvals_org_id" not in pending_indexes:
        op.create_index("ix_pending_approvals_org_id", "pending_approvals", ["org_id"])
    if "ix_pending_approvals_requested_by" not in pending_indexes:
        op.create_index("ix_pending_approvals_requested_by", "pending_approvals", ["requested_by"])
    if "ix_pending_approvals_decided_by" not in pending_indexes:
        op.create_index("ix_pending_approvals_decided_by", "pending_approvals", ["decided_by"])
    if "ix_pending_approvals_tool_name" not in pending_indexes:
        op.create_index("ix_pending_approvals_tool_name", "pending_approvals", ["tool_name"])
    if "ix_pending_approvals_status" not in pending_indexes:
        op.create_index("ix_pending_approvals_status", "pending_approvals", ["status"])
    if "ix_pending_approvals_expires_at" not in pending_indexes:
        op.create_index("ix_pending_approvals_expires_at", "pending_approvals", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_pending_approvals_expires_at", table_name="pending_approvals")
    op.drop_index("ix_pending_approvals_status", table_name="pending_approvals")
    op.drop_index("ix_pending_approvals_tool_name", table_name="pending_approvals")
    op.drop_index("ix_pending_approvals_decided_by", table_name="pending_approvals")
    op.drop_index("ix_pending_approvals_requested_by", table_name="pending_approvals")
    op.drop_index("ix_pending_approvals_org_id", table_name="pending_approvals")
    op.drop_index("ix_pending_approvals_token", table_name="pending_approvals")
    op.drop_table("pending_approvals")

    op.drop_index("ix_audit_log_request_id", table_name="audit_log")
    op.drop_index("ix_audit_log_target_id", table_name="audit_log")
    op.drop_index("ix_audit_log_target_type", table_name="audit_log")
    op.drop_index("ix_audit_log_action", table_name="audit_log")
    op.drop_index("ix_audit_log_actor_user_id", table_name="audit_log")
    op.drop_index("ix_audit_log_org_id", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_processing_results_experiment_id", table_name="processing_results")
    op.drop_index("ix_processing_results_file_upload_id", table_name="processing_results")
    op.drop_index("ix_processing_results_analysis_type", table_name="processing_results")
    op.drop_index("ix_processing_results_created_by", table_name="processing_results")
    op.drop_index("ix_processing_results_org_id", table_name="processing_results")
    op.drop_table("processing_results")

    op.drop_index("ix_file_uploads_detected_format", table_name="file_uploads")
    op.drop_index("ix_file_uploads_checksum_sha256", table_name="file_uploads")
    op.drop_index("ix_file_uploads_uploaded_by", table_name="file_uploads")
    op.drop_column("file_uploads", "detected_format")
    op.drop_column("file_uploads", "content_bytes")
    op.drop_column("file_uploads", "storage_backend")
    op.drop_column("file_uploads", "checksum_sha256")
    op.drop_column("file_uploads", "uploaded_by")
