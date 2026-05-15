"""Tests for real chat streaming."""

from __future__ import annotations

import json

import pytest

from resonantia.models.request_context import RequestContext
from resonantia.services.llm import ToolCall
from tests.conftest import _test_session_factory


class _StreamingProvider:
    provider_name = "fake"
    _default_model = "fake-stream"

    def __init__(self, rounds):
        self._rounds = list(rounds)

    async def completion_stream(self, *args, **kwargs):
        for item in self._rounds.pop(0):
            yield item


def _ctx() -> RequestContext:
    return RequestContext(
        user_id="test-user",
        org_id="org_stream",
        roles=["org:admin"],
        permissions=[],
        request_id="req-stream",
    )


def _payloads(chunks: list[str]) -> list[dict]:
    payloads = []
    for chunk in chunks:
        for frame in chunk.strip().split("\n\n"):
            if frame.startswith("data: "):
                payloads.append(json.loads(frame.removeprefix("data: ")))
    return payloads


@pytest.mark.asyncio
async def test_chat_stream_yields_incremental_tokens(db_session, monkeypatch):
    from resonantia.services import agent

    monkeypatch.setattr(agent, "async_session_factory", _test_session_factory)
    monkeypatch.setattr(agent, "_get_provider", lambda: _StreamingProvider([["Hel", "lo"]]))
    monkeypatch.setattr(agent, "_load_tools", _async_empty_tools)
    monkeypatch.setattr(agent, "trace_llm_call", lambda **kwargs: None)

    chunks = [
        chunk
        async for chunk in agent.chat_stream("hello", request_context=_ctx())
    ]
    payloads = _payloads(chunks)

    assert payloads[0] == {"text": "Hel"}
    assert payloads[1] == {"text": "lo"}
    assert payloads[-1]["done"] is True


@pytest.mark.asyncio
async def test_chat_stream_executes_tool_and_resumes_streaming(db_session, monkeypatch):
    from resonantia.services import agent

    provider = _StreamingProvider([
        [ToolCall(id="tc-1", name="lookup_sample", arguments={"query": "A1"})],
        ["Sample A1 is in freezer 2."],
    ])

    async def fake_execute_tool(*args, **kwargs):
        return json.dumps({"found": True})

    monkeypatch.setattr(agent, "async_session_factory", _test_session_factory)
    monkeypatch.setattr(agent, "_get_provider", lambda: provider)
    monkeypatch.setattr(agent, "_load_tools", _async_empty_tools)
    monkeypatch.setattr(agent, "execute_tool", fake_execute_tool)
    monkeypatch.setattr(agent, "trace_llm_call", lambda **kwargs: None)

    chunks = [
        chunk
        async for chunk in agent.chat_stream("where is A1?", request_context=_ctx())
    ]
    payloads = _payloads(chunks)

    assert any("tool_call" in payload for payload in payloads)
    assert any("tool_result" in payload for payload in payloads)
    assert any(payload.get("text") == "Sample A1 is in freezer 2." for payload in payloads)
    assert payloads[-1]["done"] is True


async def _async_empty_tools():
    return []
