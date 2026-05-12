"""Tests for the approval gate service."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import pytest

from resonantia.services.approval import (
    GateKind,
    PendingApproval,
    TOOL_GATES,
    approve,
    create_pending,
    get_gate,
    get_pending,
    is_gated,
    reject,
    _pending,
)


class TestGateClassification:
    def test_lookup_tools_are_ungated(self):
        ungated = ["lookup_sample", "check_inventory", "query_experiments",
                    "calculate_dilution", "fit_dose_response", "normalize_plate",
                    "calculate_z_prime", "qpcr_analysis", "read_file_contents"]
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


class TestPendingApprovals:
    def setup_method(self):
        _pending.clear()

    def test_create_pending_returns_token(self):
        p = create_pending("create_eln_entry", {"title": "Test"}, "org_A", "user_1", {"markdown": "..."})
        assert p.token
        assert p.tool_name == "create_eln_entry"
        assert p.org_id == "org_A"
        assert p.user_id == "user_1"

    def test_get_pending_returns_created(self):
        p = create_pending("create_eln_entry", {}, "org_A", "user_1", {})
        loaded = get_pending(p.token)
        assert loaded is not None
        assert loaded.token == p.token

    def test_get_pending_returns_none_for_unknown(self):
        assert get_pending("nonexistent-token") is None

    def test_approve_removes_and_returns(self):
        p = create_pending("create_plate_map", {}, "org_A", "user_1", {})
        approved = approve(p.token)
        assert approved is not None
        assert approved.token == p.token
        assert get_pending(p.token) is None

    def test_approve_returns_none_for_unknown(self):
        assert approve("nonexistent") is None

    def test_reject_removes(self):
        p = create_pending("create_eln_entry", {}, "org_A", "user_1", {})
        assert reject(p.token) is True
        assert get_pending(p.token) is None

    def test_reject_returns_false_for_unknown(self):
        assert reject("nonexistent") is False

    def test_expired_approval_returns_none(self):
        p = create_pending("create_eln_entry", {}, "org_A", "user_1", {})
        _pending[p.token].expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        assert get_pending(p.token) is None

    def test_double_approve_fails(self):
        p = create_pending("create_eln_entry", {}, "org_A", "user_1", {})
        assert approve(p.token) is not None
        assert approve(p.token) is None


class TestApprovalEndpoints:
    def test_approve_endpoint_exists(self):
        import inspect
        from resonantia.api.chat import approve_tool_call
        sig = inspect.signature(approve_tool_call)
        assert "token" in sig.parameters
        assert "ctx" in sig.parameters

    def test_reject_endpoint_exists(self):
        import inspect
        from resonantia.api.chat import reject_tool_call
        sig = inspect.signature(reject_tool_call)
        assert "token" in sig.parameters
