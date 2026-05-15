"""Tests for output_validator and the typed tool execution pipeline.

Covers:
- Schema validation (wrong types, missing required fields, enum violations)
- Cross-tenant entity reference blocking
- System errors don't expose internals
- ToolResult has source_refs
- All ToolError types (validation, forbidden, system)
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from resonantia.services.output_validator import (
    ToolError,
    ToolResult,
    check_tenant_refs,
    validate_tool_args,
)


# ---------------------------------------------------------------------------
# ToolResult / ToolError model tests
# ---------------------------------------------------------------------------

class TestToolResult:
    def test_success_status(self):
        r = ToolResult(tool_name="lookup_sample", data={"found": 1})
        assert r.status == "success"
        assert r.tool_name == "lookup_sample"
        assert r.data == {"found": 1}

    def test_source_refs_default_empty(self):
        r = ToolResult(tool_name="t", data={})
        assert r.source_refs == []

    def test_source_refs_populated(self):
        refs = [str(uuid.uuid4()), str(uuid.uuid4())]
        r = ToolResult(tool_name="t", data={}, source_refs=refs)
        assert r.source_refs == refs
        assert len(r.source_refs) == 2

    def test_serializes_to_dict(self):
        r = ToolResult(tool_name="test", data={"key": "val"}, source_refs=["ref-1"])
        d = r.model_dump()
        assert d["status"] == "success"
        assert d["source_refs"] == ["ref-1"]


class TestToolError:
    def test_validation_error(self):
        e = ToolError(
            tool_name="fit_dose_response",
            error_type="validation",
            message="Field 'data' expected array, got str",
            retry_allowed=True,
        )
        assert e.status == "error"
        assert e.error_type == "validation"
        assert e.retry_allowed is True

    def test_forbidden_error(self):
        e = ToolError(
            tool_name="create_eln_entry",
            error_type="forbidden",
            message="Entity not accessible",
            retry_allowed=False,
        )
        assert e.error_type == "forbidden"
        assert e.retry_allowed is False

    def test_system_error(self):
        e = ToolError(
            tool_name="query_experiments",
            error_type="system",
            message="Internal error",
            retry_allowed=False,
        )
        assert e.error_type == "system"
        assert "traceback" not in e.message.lower()
        assert "connection" not in e.message.lower()

    def test_timeout_error(self):
        e = ToolError(
            tool_name="long_tool",
            error_type="timeout",
            message="Tool execution timed out",
            retry_allowed=True,
        )
        assert e.error_type == "timeout"

    def test_retry_allowed_defaults_false(self):
        e = ToolError(tool_name="t", error_type="system", message="err")
        assert e.retry_allowed is False


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

SAMPLE_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Search term"},
        "search_by": {
            "type": "string",
            "description": "Field to search",
            "enum": ["barcode", "name", "lot"],
        },
        "limit": {"type": "number", "description": "Max results"},
    },
    "required": ["query"],
}


class TestValidateToolArgs:
    def test_valid_args_pass_through(self):
        result = validate_tool_args(
            "lookup_sample",
            {"query": "aspirin", "search_by": "name"},
            SAMPLE_SCHEMA,
        )
        assert isinstance(result, dict)
        assert result["query"] == "aspirin"

    def test_missing_required_field(self):
        result = validate_tool_args("lookup_sample", {}, SAMPLE_SCHEMA)
        assert isinstance(result, ToolError)
        assert result.error_type == "validation"
        assert "query" in result.message
        assert result.retry_allowed is True

    def test_wrong_type_string_expected_number(self):
        result = validate_tool_args(
            "lookup_sample",
            {"query": "test", "limit": "not-a-number"},
            SAMPLE_SCHEMA,
        )
        assert isinstance(result, ToolError)
        assert result.error_type == "validation"
        assert "limit" in result.message
        assert "number" in result.message

    def test_wrong_type_number_expected_string(self):
        result = validate_tool_args(
            "lookup_sample",
            {"query": 123},
            SAMPLE_SCHEMA,
        )
        assert isinstance(result, ToolError)
        assert "query" in result.message
        assert "string" in result.message

    def test_boolean_not_accepted_as_number(self):
        result = validate_tool_args(
            "lookup_sample",
            {"query": "test", "limit": True},
            SAMPLE_SCHEMA,
        )
        assert isinstance(result, ToolError)
        assert "limit" in result.message

    def test_enum_violation(self):
        result = validate_tool_args(
            "lookup_sample",
            {"query": "test", "search_by": "invalid_field"},
            SAMPLE_SCHEMA,
        )
        assert isinstance(result, ToolError)
        assert "search_by" in result.message
        assert "invalid_field" in result.message
        assert result.retry_allowed is True

    def test_extra_fields_tolerated(self):
        result = validate_tool_args(
            "lookup_sample",
            {"query": "test", "unknown_field": "whatever"},
            SAMPLE_SCHEMA,
        )
        assert isinstance(result, dict)

    def test_multiple_errors_joined(self):
        result = validate_tool_args(
            "lookup_sample",
            {"limit": "bad"},  # missing required + wrong type
            SAMPLE_SCHEMA,
        )
        assert isinstance(result, ToolError)
        # Should contain both errors
        assert "query" in result.message
        assert "limit" in result.message

    def test_empty_schema_passes_anything(self):
        result = validate_tool_args(
            "get_sample_stats",
            {},
            {"type": "object", "properties": {}, "required": []},
        )
        assert isinstance(result, dict)

    def test_array_type_validated(self):
        schema = {
            "type": "object",
            "properties": {
                "concentrations": {"type": "array", "description": "values"},
            },
            "required": ["concentrations"],
        }
        result = validate_tool_args(
            "fit_dose_response",
            {"concentrations": "not-a-list"},
            schema,
        )
        assert isinstance(result, ToolError)
        assert "array" in result.message


# ---------------------------------------------------------------------------
# Cross-tenant entity reference check
# ---------------------------------------------------------------------------

class TestCheckTenantRefs:
    @pytest.mark.asyncio
    async def test_no_id_fields_passes(self):
        session = AsyncMock()
        result = await check_tenant_refs(
            {"query": "aspirin", "search_by": "name"},
            "org_1",
            session,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_non_uuid_id_field_skipped(self):
        session = AsyncMock()
        result = await check_tenant_refs(
            {"experiment_id": "not-a-uuid"},
            "org_1",
            session,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_entity_not_found_returns_forbidden(self):
        session = AsyncMock()
        session.get = AsyncMock(return_value=None)

        fake_id = str(uuid.uuid4())
        result = await check_tenant_refs(
            {"experiment_id": fake_id},
            "org_1",
            session,
        )
        assert result is not None
        assert isinstance(result, ToolError)
        assert result.error_type == "forbidden"
        assert result.retry_allowed is False

    @pytest.mark.asyncio
    async def test_wrong_org_returns_forbidden(self):
        fake_id = str(uuid.uuid4())

        # Mock entity that belongs to a different org
        entity = MagicMock()
        entity.org_id = "org_other"

        session = AsyncMock()
        session.get = AsyncMock(return_value=entity)

        result = await check_tenant_refs(
            {"experiment_id": fake_id},
            "org_1",
            session,
        )
        assert result is not None
        assert isinstance(result, ToolError)
        assert result.error_type == "forbidden"
        assert "not accessible" in result.message.lower()

    @pytest.mark.asyncio
    async def test_correct_org_passes(self):
        fake_id = str(uuid.uuid4())

        entity = MagicMock()
        entity.org_id = "org_1"

        session = AsyncMock()
        session.get = AsyncMock(return_value=entity)

        result = await check_tenant_refs(
            {"experiment_id": fake_id},
            "org_1",
            session,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_unknown_id_field_skipped(self):
        session = AsyncMock()
        fake_id = str(uuid.uuid4())
        result = await check_tenant_refs(
            {"completely_unknown_id": fake_id},
            "org_1",
            session,
        )
        # Unknown _id field types are skipped, not blocked
        assert result is None


# ---------------------------------------------------------------------------
# execute_tool_typed integration (mocked handlers)
# ---------------------------------------------------------------------------

class TestExecuteToolTyped:
    @pytest.mark.asyncio
    async def test_unknown_tool_returns_validation_error(self):
        from resonantia.services.tool_executor import execute_tool_typed

        result = await execute_tool_typed("nonexistent_tool", {}, "org_1")
        assert isinstance(result, ToolError)
        assert result.error_type == "validation"
        assert "Unknown tool" in result.message

    @pytest.mark.asyncio
    async def test_successful_execution_returns_tool_result(self):
        from resonantia.services.tool_executor import execute_tool_typed

        async def _mock_handler(params, org_id):
            return {"found": 1, "items": [{"name": "Aspirin"}]}

        with patch.dict(
            "resonantia.services.tool_executor.TOOL_HANDLERS",
            {"test_tool": _mock_handler},
        ), patch(
            "resonantia.services.tool_executor._get_tool_schema",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await execute_tool_typed("test_tool", {"query": "test"}, "org_1")

        assert isinstance(result, ToolResult)
        assert result.status == "success"
        assert result.data["found"] == 1

    @pytest.mark.asyncio
    async def test_system_error_does_not_expose_internals(self):
        from resonantia.services.tool_executor import execute_tool_typed

        async def _crashing_handler(params, org_id):
            raise ConnectionError("Connection refused to postgres://secret:pw@db:5432")

        with patch.dict(
            "resonantia.services.tool_executor.TOOL_HANDLERS",
            {"crashing_tool": _crashing_handler},
        ), patch(
            "resonantia.services.tool_executor._get_tool_schema",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await execute_tool_typed("crashing_tool", {}, "org_1")

        assert isinstance(result, ToolError)
        assert result.error_type == "system"
        assert result.message == "Internal error"
        # Must not expose connection string, traceback, or exception type
        assert "postgres" not in result.message
        assert "secret" not in result.message
        assert "Connection refused" not in result.message

    @pytest.mark.asyncio
    async def test_source_refs_extracted_from_args(self):
        from resonantia.services.tool_executor import execute_tool_typed

        fake_exp_id = str(uuid.uuid4())

        async def _mock_handler(params, org_id):
            return {"created": True}

        with patch.dict(
            "resonantia.services.tool_executor.TOOL_HANDLERS",
            {"test_tool": _mock_handler},
        ), patch(
            "resonantia.services.tool_executor._get_tool_schema",
            new_callable=AsyncMock,
            return_value=None,
        ), patch(
            "resonantia.services.tool_executor.check_tenant_refs",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await execute_tool_typed(
                "test_tool", {"experiment_id": fake_exp_id}, "org_1"
            )

        assert isinstance(result, ToolResult)
        assert fake_exp_id in result.source_refs

    @pytest.mark.asyncio
    async def test_schema_validation_blocks_execution(self):
        from resonantia.services.tool_executor import execute_tool_typed

        call_count = 0

        async def _handler(params, org_id):
            nonlocal call_count
            call_count += 1
            return {"ok": True}

        schema = {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        }

        with patch.dict(
            "resonantia.services.tool_executor.TOOL_HANDLERS",
            {"guarded_tool": _handler},
        ), patch(
            "resonantia.services.tool_executor._get_tool_schema",
            new_callable=AsyncMock,
            return_value=schema,
        ):
            result = await execute_tool_typed(
                "guarded_tool", {"query": 42}, "org_1"
            )

        assert isinstance(result, ToolError)
        assert result.error_type == "validation"
        assert call_count == 0  # handler must NOT have been called


# ---------------------------------------------------------------------------
# Backward-compatible execute_tool (JSON string)
# ---------------------------------------------------------------------------

class TestExecuteToolBackwardCompat:
    @pytest.mark.asyncio
    async def test_success_returns_json_string(self):
        from resonantia.services.tool_executor import execute_tool

        async def _handler(params, org_id):
            return {"found": 0, "message": "No results"}

        with patch.dict(
            "resonantia.services.tool_executor.TOOL_HANDLERS",
            {"test_tool": _handler},
        ), patch(
            "resonantia.services.tool_executor._get_tool_schema",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await execute_tool("test_tool", {}, "org_1")

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["found"] == 0

    @pytest.mark.asyncio
    async def test_error_returns_json_with_error_type(self):
        from resonantia.services.tool_executor import execute_tool

        async def _crashing_handler(params, org_id):
            raise RuntimeError("kaboom")

        with patch.dict(
            "resonantia.services.tool_executor.TOOL_HANDLERS",
            {"crash": _crashing_handler},
        ), patch(
            "resonantia.services.tool_executor._get_tool_schema",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await execute_tool("crash", {}, "org_1")

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "error" in parsed
        assert parsed["error_type"] == "system"
        assert parsed["error"] == "Internal error"
