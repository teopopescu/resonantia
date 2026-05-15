"""Tests for batched per-turn chat persistence."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.models.conversation import Conversation, ConversationMessage
from resonantia.models.request_context import RequestContext
from resonantia.services.llm import LLMResponse
from tests.conftest import _test_engine, _test_session_factory


class _FakeProvider:
    async def completion(self, *args, **kwargs) -> LLMResponse:
        return LLMResponse(
            content="Batched response",
            tool_calls=[],
            model="fake-model",
            provider="fake",
            input_tokens=4,
            output_tokens=2,
        )


async def _no_tools():
    return []


async def _create_conversation(db_session: AsyncSession) -> uuid.UUID:
    conv = Conversation(
        clerk_user_id="test-user",
        org_id="org_default",
        title="Existing conversation",
    )
    db_session.add(conv)
    await db_session.commit()
    return conv.id


def _ctx() -> RequestContext:
    return RequestContext(
        user_id="test-user",
        org_id="org_default",
        roles=["org:admin"],
        permissions=[],
        request_id="req-batch",
    )


@pytest.mark.asyncio
async def test_single_agent_turn_uses_one_commit(db_session: AsyncSession, monkeypatch):
    from resonantia.services import agent

    conversation_id = await _create_conversation(db_session)
    monkeypatch.setattr(agent, "async_session_factory", _test_session_factory)
    monkeypatch.setattr(agent, "_get_provider", lambda: _FakeProvider())
    monkeypatch.setattr(agent, "_load_tools", _no_tools)
    monkeypatch.setattr(agent, "trace_llm_call", lambda **kwargs: None)

    commit_count = 0

    def _count_commit(conn):
        nonlocal commit_count
        commit_count += 1

    event.listen(_test_engine.sync_engine, "commit", _count_commit)
    try:
        result = await agent.chat(
            "hello",
            conversation_id=str(conversation_id),
            request_context=_ctx(),
        )
    finally:
        event.remove(_test_engine.sync_engine, "commit", _count_commit)

    assert result["message"] == "Batched response"
    assert commit_count == 1

    count = await db_session.scalar(
        select(func.count()).select_from(ConversationMessage).where(
            ConversationMessage.conversation_id == conversation_id
        )
    )
    assert count == 2


@pytest.mark.asyncio
async def test_failed_turn_commit_rolls_back_messages(db_session: AsyncSession, monkeypatch):
    from resonantia.services import agent

    conversation_id = await _create_conversation(db_session)
    monkeypatch.setattr(agent, "async_session_factory", _test_session_factory)
    monkeypatch.setattr(agent, "_get_provider", lambda: _FakeProvider())
    monkeypatch.setattr(agent, "_load_tools", _no_tools)
    monkeypatch.setattr(agent, "trace_llm_call", lambda **kwargs: None)

    async def _fail_audit(*args, **kwargs):
        raise RuntimeError("commit failure")

    monkeypatch.setattr(agent, "append_audit_log", _fail_audit)

    result = await agent.chat(
        "hello",
        conversation_id=str(conversation_id),
        request_context=_ctx(),
    )

    assert result["message"] == "Could not persist this chat turn. Please retry."
    count = await db_session.scalar(
        select(func.count()).select_from(ConversationMessage).where(
            ConversationMessage.conversation_id == conversation_id
        )
    )
    assert count == 0
