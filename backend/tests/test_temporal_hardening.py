"""Tests for Phase 5 Temporal hardening."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.models.conversation import Conversation, ConversationMessage
from tests.conftest import _test_session_factory


@pytest.mark.asyncio
async def test_persist_conversation_activity_creates_missing_conversation(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    from resonantia.db import session as db_session_module
    from resonantia.workflows.activities import persist_conversation_activity

    monkeypatch.setattr(db_session_module, "async_session_factory", _test_session_factory)
    conversation_id = uuid.uuid4()

    await persist_conversation_activity(
        str(conversation_id),
        "org_temporal",
        "user_temporal",
        [
            {"role": "user", "content": "Please process this file"},
            {"role": "assistant", "content": "Done"},
        ],
    )

    conversation = await db_session.get(Conversation, conversation_id)
    assert conversation is not None
    assert conversation.org_id == "org_temporal"
    assert conversation.clerk_user_id == "user_temporal"
    assert conversation.title == "Please process this file"

    message_count = await db_session.scalar(
        select(func.count()).select_from(ConversationMessage).where(
            ConversationMessage.conversation_id == conversation_id
        )
    )
    assert message_count == 2


def test_agent_tool_call_input_has_user_id():
    from resonantia.workflows.agent_workflow import AgentToolCallInput

    inp = AgentToolCallInput(
        messages=[{"role": "user", "content": "hello"}],
        tools=[],
        org_id="org_temporal",
        user_id="user_temporal",
    )

    assert inp.user_id == "user_temporal"


def test_agent_workflow_uses_expected_activity_timeouts():
    from pathlib import Path

    source = Path("src/resonantia/workflows/agent_workflow.py").read_text()
    assert "start_to_close_timeout=timedelta(seconds=30)" in source
    assert "start_to_close_timeout=timedelta(seconds=60)" in source
    assert "start_to_close_timeout=timedelta(seconds=10)" in source
    assert "maximum_attempts=3" in source


@pytest.mark.asyncio
async def test_chat_timeout_returns_workflow_polling_payload(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    from resonantia.api import chat
    from resonantia.services import temporal_client

    class _Handle:
        id = "agent-conv-timeout"

        async def result(self):
            return None

    async def _start_agent_workflow(**kwargs):
        assert kwargs["user_id"] == "test-user"
        return _Handle()

    async def _timeout(awaitable, timeout):
        awaitable.close() if hasattr(awaitable, "close") else None
        raise asyncio.TimeoutError

    monkeypatch.setattr(temporal_client, "start_agent_workflow", _start_agent_workflow)
    monkeypatch.setattr(chat.asyncio, "wait_for", _timeout)

    response = await client.post(
        "/api/v1/chat/message",
        json={"message": "Long running request", "conversation_id": str(uuid.uuid4())},
        headers={"X-Org-Id": "org_temporal"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["workflow_id"] == "agent-conv-timeout"
    assert body["status"] == "processing"
