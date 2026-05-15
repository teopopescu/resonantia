"""Tests for DB-backed approval gates."""

from __future__ import annotations

import inspect
import json
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.models.pending_approval import PendingApprovalRecord
from resonantia.services.approval import (
    ApprovalStatus,
    GateKind,
    TOOL_GATES,
    claim_for_approval,
    create_pending,
    get_gate,
    get_pending_record,
    is_gated,
    is_expired,
    mark_expired,
    pending_from_record,
    reject_pending,
)
from tests.conftest import _test_session_factory


class TestGateClassification:
    def test_lookup_tools_are_ungated(self):
        ungated = [
            "lookup_sample", "check_inventory", "query_experiments",
            "calculate_dilution", "fit_dose_response", "normalize_plate",
            "calculate_z_prime", "qpcr_analysis", "read_file_contents",
        ]
        for tool in ungated:
            assert get_gate(tool) == GateKind.NONE, f"{tool} should be ungated"

    def test_create_tools_are_soft_review(self):
        soft = ["create_eln_entry", "create_plate_map", "create_protocol",
                "serial_dilution", "cherry_pick"]
        for tool in soft:
            assert get_gate(tool) == GateKind.SOFT_REVIEW, f"{tool} should be soft_review"

    def test_submit_tools_are_hard_approval(self):
        hard = ["submit_eln_entry", "generate_worklist"]
        for tool in hard:
            assert get_gate(tool) == GateKind.HARD_APPROVAL, f"{tool} should be hard_approval"

    def test_unknown_tool_defaults_to_none(self):
        assert get_gate("unknown_tool_xyz") == GateKind.NONE

    def test_is_gated(self):
        assert not is_gated("lookup_sample")
        assert is_gated("create_eln_entry")
        assert is_gated("submit_eln_entry")
        assert TOOL_GATES["submit_eln_entry"] == GateKind.HARD_APPROVAL


class TestPendingApprovals:
    @pytest.mark.asyncio
    async def test_create_pending_persists_token(self, db_session: AsyncSession):
        pending = await create_pending(
            db_session,
            "create_eln_entry",
            {"title": "Test"},
            "org_A",
            "user_1",
            {"markdown": "..."},
        )
        assert pending.token
        assert pending.tool_name == "create_eln_entry"
        assert pending.org_id == "org_A"
        assert pending.user_id == "user_1"

        loaded = await get_pending_record(db_session, pending.token)
        assert loaded is not None
        assert pending_from_record(loaded).token == pending.token

    @pytest.mark.asyncio
    async def test_claim_and_reject_update_status(self, db_session: AsyncSession):
        pending = await create_pending(db_session, "create_eln_entry", {}, "org_A", "user_1", {})
        record = await get_pending_record(db_session, pending.token)
        assert record is not None
        await claim_for_approval(db_session, record, decided_by="approver")
        assert record.status == ApprovalStatus.APPROVED.value
        assert record.decided_by == "approver"

        pending_2 = await create_pending(db_session, "create_eln_entry", {}, "org_A", "user_1", {})
        record_2 = await get_pending_record(db_session, pending_2.token)
        assert record_2 is not None
        await reject_pending(db_session, record_2, decided_by="approver")
        assert record_2.status == ApprovalStatus.REJECTED.value

    @pytest.mark.asyncio
    async def test_expired_approval_is_marked(self, db_session: AsyncSession):
        record = PendingApprovalRecord(
            token="expired-token",
            org_id="org_A",
            requested_by="user_1",
            tool_name="create_eln_entry",
            tool_args={},
            preview={},
            gate_kind=GateKind.SOFT_REVIEW.value,
            status=ApprovalStatus.PENDING.value,
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        db_session.add(record)
        await db_session.flush()
        assert is_expired(record)
        await mark_expired(db_session, record)
        assert record.status == ApprovalStatus.EXPIRED.value


class TestApprovalExecution:
    @pytest.mark.asyncio
    async def test_text_gated_tool_returns_pending_approval(self, db_session: AsyncSession, monkeypatch):
        from resonantia.services import tool_executor
        from resonantia.services.output_validator import ToolResult
        from resonantia.services.tool_executor import execute_tool_typed

        async def _handler(params, org_id):
            return {"executed": True}

        async def _no_schema(tool_name):
            return None

        async def _no_tenant_error(tool_input, org_id, session):
            return None

        monkeypatch.setattr(tool_executor, "async_session_factory", _test_session_factory)
        monkeypatch.setitem(tool_executor.TOOL_HANDLERS, "submit_eln_entry", _handler)
        monkeypatch.setattr(tool_executor, "_get_tool_schema", _no_schema)
        monkeypatch.setattr(tool_executor, "check_tenant_refs", _no_tenant_error)

        result = await execute_tool_typed(
            "submit_eln_entry",
            {"entry_id": "eln-1"},
            "org_1",
            source="text",
            user_id="user_1",
        )

        assert isinstance(result, ToolResult)
        assert result.data["approval_required"] is True
        assert result.data["pending_approval"]["tool_name"] == "submit_eln_entry"
        assert result.data["approval_card"]["type"] == "approval_card"

    @pytest.mark.asyncio
    async def test_approval_token_executes_once(self, client: AsyncClient, db_session: AsyncSession, monkeypatch):
        from resonantia.services import tool_executor

        monkeypatch.setattr(tool_executor, "async_session_factory", _test_session_factory)
        pending = await create_pending(
            db_session,
            "create_eln_entry",
            {"title": "Approved entry", "content_markdown": "body"},
            "org_default",
            "user_1",
            {"title": "Approved entry"},
        )

        first = await client.post(f"/api/v1/chat/approve/{pending.token}")
        assert first.status_code == 200
        assert first.json()["status"] == "approved"

        second = await client.post(f"/api/v1/chat/approve/{pending.token}")
        assert second.status_code == 409

    @pytest.mark.asyncio
    async def test_expired_token_returns_error(self, client: AsyncClient, db_session: AsyncSession):
        record = PendingApprovalRecord(
            token="expired-token",
            org_id="org_default",
            requested_by="user_1",
            tool_name="create_eln_entry",
            tool_args={"title": "Expired"},
            preview={},
            gate_kind=GateKind.SOFT_REVIEW.value,
            status=ApprovalStatus.PENDING.value,
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        db_session.add(record)
        await db_session.flush()

        response = await client.post("/api/v1/chat/approve/expired-token")
        assert response.status_code == 410

    @pytest.mark.asyncio
    async def test_temporal_activity_path_returns_pending_approval(self, db_session: AsyncSession, monkeypatch):
        from resonantia.services import tool_executor
        from resonantia.workflows.activities import execute_tool_activity

        monkeypatch.setattr(tool_executor, "async_session_factory", _test_session_factory)
        result = await execute_tool_activity(
            "create_eln_entry",
            {"title": "Temporal gated"},
            "org_default",
            request_context={
                "user_id": "test-user",
                "org_id": "org_default",
                "roles": ["org:admin"],
                "permissions": [],
                "request_id": "req-1",
            },
        )
        payload = json.loads(result)
        assert payload["approval_required"] is True
        assert payload["pending_approval"]["tool_name"] == "create_eln_entry"

    def test_multi_agent_path_uses_execute_tool_gate(self):
        from resonantia.services.multi_agent import subagents

        source = inspect.getsource(subagents)
        assert "execute_tool(" in source
        assert "TOOL_HANDLERS" not in source
