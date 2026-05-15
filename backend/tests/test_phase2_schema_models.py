"""Phase 2 schema model coverage."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_phase2_models_create_and_roundtrip(db_session: AsyncSession):
    from resonantia.models.audit_log import AuditLog
    from resonantia.models.file_upload import FileUpload
    from resonantia.models.pending_approval import PendingApprovalRecord
    from resonantia.models.processing_result import ProcessingResult

    upload = FileUpload(
        org_id="org_schema",
        uploaded_by="user_1",
        filename="data.csv",
        content_type="text/csv",
        size_bytes=12,
        storage_path="csv/data.csv",
        checksum_sha256="a" * 64,
        storage_backend="local",
        content_bytes=b"a,b\n1,2\n",
        detected_format="tabular",
        parsed_metadata={"columns": ["a", "b"]},
    )
    db_session.add(upload)
    await db_session.flush()

    processing = ProcessingResult(
        org_id="org_schema",
        created_by="user_1",
        idempotency_key="fit:" + uuid.uuid4().hex,
        analysis_type="dose_response",
        parameters={"model": "4pl"},
        result={"ic50": 42.0},
        file_upload_id=upload.id,
    )
    audit = AuditLog(
        org_id="org_schema",
        actor_user_id="user_1",
        action="file.upload",
        target_type="file_upload",
        target_id=str(upload.id),
        request_id="req_1",
        metadata_extra={"filename": "data.csv"},
    )
    approval = PendingApprovalRecord(
        token="tok_" + uuid.uuid4().hex,
        org_id="org_schema",
        requested_by="user_1",
        tool_name="submit_eln_entry",
        tool_args={"entry_id": str(uuid.uuid4())},
        preview={"title": "Submit ELN"},
        gate_kind="hard_approval",
        status="pending",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db_session.add_all([processing, audit, approval])
    await db_session.commit()

    result = await db_session.execute(select(ProcessingResult).where(ProcessingResult.file_upload_id == upload.id))
    assert result.scalar_one().result["ic50"] == 42.0

    result = await db_session.execute(select(AuditLog).where(AuditLog.target_id == str(upload.id)))
    assert result.scalar_one().metadata_extra["filename"] == "data.csv"

    result = await db_session.execute(select(PendingApprovalRecord).where(PendingApprovalRecord.token == approval.token))
    assert result.scalar_one().status == "pending"


def test_phase2_tables_and_columns_registered():
    from resonantia.models import Base

    tables = Base.metadata.tables
    assert "file_uploads" in tables
    assert "processing_results" in tables
    assert "audit_log" in tables
    assert "pending_approvals" in tables

    file_columns = set(tables["file_uploads"].columns.keys())
    assert {
        "uploaded_by",
        "checksum_sha256",
        "storage_backend",
        "content_bytes",
        "detected_format",
    }.issubset(file_columns)

    processing_constraints = {
        constraint.name
        for constraint in tables["processing_results"].constraints
    }
    assert "uq_processing_results_org_idempotency" in processing_constraints

    pending_columns = set(tables["pending_approvals"].columns.keys())
    assert {"token", "status", "expires_at", "decided_at", "result"}.issubset(pending_columns)
