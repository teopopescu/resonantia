"""Tenant isolation tests — verify cross-org data access is blocked."""

from __future__ import annotations

import inspect
import uuid

import pytest

from resonantia.models.file_upload import FileUpload
from tests.conftest import _test_session_factory


class TestFileUploadTenantIsolation:
    """Verify file tools filter by org_id."""

    async def _add_file(self, db_session, *, org_id: str, filename: str, content: bytes = b"a,b\n1,2\n") -> str:
        file_id = uuid.uuid4()
        db_session.add(
            FileUpload(
                id=file_id,
                org_id=org_id,
                uploaded_by="test-user",
                filename=filename,
                content_type="text/csv",
                size_bytes=len(content),
                storage_path=f"files/{file_id}.csv",
                storage_backend="local",
                content_bytes=content,
            )
        )
        await db_session.commit()
        return str(file_id)

    @pytest.mark.asyncio
    async def test_list_files_scoped_by_org(self, db_session, monkeypatch):
        from resonantia.services import tool_executor
        from resonantia.services.tool_executor import _list_files

        monkeypatch.setattr(tool_executor, "async_session_factory", _test_session_factory)
        file_a = await self._add_file(db_session, org_id="org_A", filename="data_a.csv")
        file_b = await self._add_file(db_session, org_id="org_B", filename="data_b.csv")

        result_a = await _list_files({}, org_id="org_A")
        assert result_a["found"] == 1
        assert result_a["files"][0]["id"] == file_a

        result_b = await _list_files({}, org_id="org_B")
        assert result_b["found"] == 1
        assert result_b["files"][0]["id"] == file_b

    @pytest.mark.asyncio
    async def test_get_file_info_blocks_cross_org(self, db_session, monkeypatch):
        from resonantia.services import tool_executor
        from resonantia.services.tool_executor import _get_file_info

        monkeypatch.setattr(tool_executor, "async_session_factory", _test_session_factory)
        file_a = await self._add_file(db_session, org_id="org_A", filename="data_a.csv")

        result = await _get_file_info({"file_id": file_a}, org_id="org_B")
        assert result["found"] is False

        result_same = await _get_file_info({"file_id": file_a}, org_id="org_A")
        assert result_same["found"] is True

    @pytest.mark.asyncio
    async def test_get_file_info_blocks_cross_org_by_filename(self, db_session, monkeypatch):
        from resonantia.services import tool_executor
        from resonantia.services.tool_executor import _get_file_info

        monkeypatch.setattr(tool_executor, "async_session_factory", _test_session_factory)
        await self._add_file(db_session, org_id="org_A", filename="secret_data.csv")

        result = await _get_file_info({"filename": "secret"}, org_id="org_B")
        assert result["found"] is False

    @pytest.mark.asyncio
    async def test_read_file_blocks_cross_org(self, db_session, monkeypatch):
        from resonantia.services import tool_executor
        from resonantia.services.tool_executor import _read_file_contents

        monkeypatch.setattr(tool_executor, "async_session_factory", _test_session_factory)
        file_a = await self._add_file(db_session, org_id="org_A", filename="data.csv")

        result = await _read_file_contents({"file_id": file_a}, org_id="org_B")
        assert "error" in result or "not" in str(result).lower()


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
