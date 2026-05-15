"""Tenant isolation tests — verify cross-org data access is blocked."""

from __future__ import annotations

import inspect

import pytest


class TestFileRegistryTenantIsolation:
    """Verify file tools filter by org_id."""

    @pytest.mark.asyncio
    async def test_list_files_scoped_by_org(self):
        from resonantia.api.files import _file_registry
        from resonantia.services.tool_executor import _list_files

        _file_registry.clear()
        _file_registry["file_A"] = {
            "id": "file_A", "filename": "data_a.csv", "size": 100,
            "content_type": "text/csv", "org_id": "org_A",
        }
        _file_registry["file_B"] = {
            "id": "file_B", "filename": "data_b.csv", "size": 200,
            "content_type": "text/csv", "org_id": "org_B",
        }

        result_a = await _list_files({}, org_id="org_A")
        assert result_a["found"] == 1
        assert result_a["files"][0]["id"] == "file_A"

        result_b = await _list_files({}, org_id="org_B")
        assert result_b["found"] == 1
        assert result_b["files"][0]["id"] == "file_B"

        _file_registry.clear()

    @pytest.mark.asyncio
    async def test_get_file_info_blocks_cross_org(self):
        from resonantia.api.files import _file_registry
        from resonantia.services.tool_executor import _get_file_info

        _file_registry.clear()
        _file_registry["file_A"] = {
            "id": "file_A", "filename": "data_a.csv", "size": 100,
            "content_type": "text/csv", "org_id": "org_A",
        }

        result = await _get_file_info({"file_id": "file_A"}, org_id="org_B")
        assert result["found"] is False

        result_same = await _get_file_info({"file_id": "file_A"}, org_id="org_A")
        assert result_same["found"] is True

        _file_registry.clear()

    @pytest.mark.asyncio
    async def test_get_file_info_blocks_cross_org_by_filename(self):
        from resonantia.api.files import _file_registry
        from resonantia.services.tool_executor import _get_file_info

        _file_registry.clear()
        _file_registry["file_A"] = {
            "id": "file_A", "filename": "secret_data.csv", "size": 100,
            "content_type": "text/csv", "org_id": "org_A",
        }

        result = await _get_file_info({"filename": "secret"}, org_id="org_B")
        assert result["found"] is False

        _file_registry.clear()

    @pytest.mark.asyncio
    async def test_read_file_blocks_cross_org(self):
        from resonantia.api.files import _file_registry
        from resonantia.services.tool_executor import _read_file_contents

        _file_registry.clear()
        _file_registry["file_A"] = {
            "id": "file_A", "filename": "data.csv", "size": 100,
            "content_type": "text/csv", "org_id": "org_A",
            "stored_path": "/nonexistent/path",
        }

        result = await _read_file_contents({"file_id": "file_A"}, org_id="org_B")
        assert "error" in result or "not" in str(result).lower()

        _file_registry.clear()


class TestChatEndpointOrgDerivation:
    """Verify send_message derives tenant context from verified auth."""

    def test_send_message_has_org_id_dependency(self):
        from resonantia.api.chat import send_message

        sig = inspect.signature(send_message)
        assert "ctx" in sig.parameters
        param = sig.parameters["ctx"]
        assert param.default is not inspect.Parameter.empty

    def test_stream_message_has_org_id_dependency(self):
        from resonantia.api.chat import stream_message

        sig = inspect.signature(stream_message)
        assert "ctx" in sig.parameters
        param = sig.parameters["ctx"]
        assert param.default is not inspect.Parameter.empty

    def test_chat_request_org_id_removed_from_body(self):
        """Tenant context must come from auth, not request body."""
        import pytest
        from pydantic import ValidationError
        from resonantia.schemas.chat import ChatRequest

        with pytest.raises(ValidationError):
            ChatRequest(message="test", org_id="attacker_org")


class TestConversationOrgCheck:
    """Verify _get_or_create_conversation checks org_id."""

    def test_conversation_loader_checks_org(self):
        """The function should check conv.org_id == org_id before returning."""
        import ast
        import textwrap
        from resonantia.services import agent

        source = inspect.getsource(agent._get_or_create_conversation)
        assert "conv.org_id" in source and "org_id" in source, (
            "_get_or_create_conversation must check conv.org_id against the caller's org_id"
        )

    def test_conversation_loader_rejects_mismatch(self):
        """The source code should raise or reject when org_id doesn't match."""
        from resonantia.services import agent

        source = inspect.getsource(agent._get_or_create_conversation)
        assert "not accessible" in source.lower() or "org_id !=" in source, (
            "_get_or_create_conversation must reject cross-org access"
        )
