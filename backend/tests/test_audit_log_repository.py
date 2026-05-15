"""Audit log repository and wiring tests."""

from __future__ import annotations

import io
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def test_audit_repository_is_append_only():
    from resonantia.repositories.audit_log import AuditLogRepository

    assert hasattr(AuditLogRepository, "append")
    assert not hasattr(AuditLogRepository, "update")
    assert not hasattr(AuditLogRepository, "delete")


def test_audit_migration_revokes_update_delete():
    migration = "alembic/versions/20260515_add_production_phase2_tables.py"
    from pathlib import Path

    text = Path(migration).read_text()
    assert "REVOKE UPDATE, DELETE ON audit_log" in text


@pytest.mark.asyncio
async def test_tool_execution_appends_audit_log(db_session: AsyncSession):
    import tests.conftest as test_conftest
    from resonantia.models.audit_log import AuditLog
    from resonantia.models.request_context import RequestContext
    from resonantia.services.tool_executor import execute_tool_typed

    async def _handler(params, org_id):
        return {"ok": True}

    ctx = RequestContext(user_id="user_1", org_id="org_audit", roles=["org:admin"], request_id="req_1")

    with patch.dict(
        "resonantia.services.tool_executor.TOOL_HANDLERS",
        {"audit_test_tool": _handler},
    ), patch(
        "resonantia.services.tool_executor._get_tool_schema",
        new_callable=AsyncMock,
        return_value=None,
    ), patch(
        "resonantia.services.tool_executor.async_session_factory",
        test_conftest._test_session_factory,
    ):
        result = await execute_tool_typed("audit_test_tool", {"query": "x"}, request_context=ctx)

    assert result.status == "success"
    rows = await db_session.execute(select(AuditLog).where(AuditLog.action == "tool.execution"))
    audit = rows.scalar_one()
    assert audit.org_id == "org_audit"
    assert audit.actor_user_id == "user_1"
    assert audit.target_id == "audit_test_tool"
    assert audit.metadata_extra["status"] == "success"


@pytest.mark.asyncio
async def test_file_upload_appends_audit_log(client: AsyncClient, db_session: AsyncSession):
    from resonantia.models.audit_log import AuditLog

    files = {"files": ("audit.csv", io.BytesIO(b"a,b\n1,2\n"), "text/csv")}
    response = await client.post("/api/v1/files/upload", files=files, headers={"X-Org-Id": "org_audit"})

    assert response.status_code == 201
    rows = await db_session.execute(select(AuditLog).where(AuditLog.action == "file.upload"))
    audit = rows.scalar_one()
    assert audit.org_id == "org_audit"
    assert audit.metadata_extra["filename"] == "audit.csv"


@pytest.mark.asyncio
async def test_eln_create_and_submit_append_audit_logs(client: AsyncClient, db_session: AsyncSession):
    from resonantia.models.audit_log import AuditLog

    created = await client.post(
        "/api/v1/eln/",
        json={"title": "Audit ELN", "content_markdown": "content"},
        headers={"X-Org-Id": "org_audit"},
    )
    assert created.status_code == 201
    entry_id = created.json()["id"]

    submitted = await client.post(f"/api/v1/eln/{entry_id}/submit", headers={"X-Org-Id": "org_audit"})
    assert submitted.status_code == 200

    rows = await db_session.execute(
        select(AuditLog.action).where(AuditLog.target_id == entry_id).order_by(AuditLog.created_at)
    )
    assert rows.scalars().all() == ["eln.create", "eln.submit"]
