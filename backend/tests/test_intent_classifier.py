"""Tests for intent classification and graceful routing fallback."""

from __future__ import annotations

import pytest

from resonantia.models.intent import IntentClass
from resonantia.models.request_context import RequestContext
from resonantia.services.intent_classifier import classify_intent
from tests.conftest import _test_session_factory


def _ctx() -> RequestContext:
    return RequestContext(
        user_id="test-user",
        org_id="org_intent",
        roles=["org:admin"],
        permissions=[],
        request_id="req-intent",
    )


@pytest.mark.asyncio
async def test_sample_lookup_classifies_high_confidence():
    result = await classify_intent("Where is staurosporine?", turn_id="sample-lookup")
    assert result.intent_class == IntentClass.SAMPLE_LOOKUP
    assert result.confidence > 0.85
    assert result.recommended_tool == "lookup_sample"
    assert result.route == "single_tool"


@pytest.mark.asyncio
async def test_confirmation_plate_classifies_multi_step():
    result = await classify_intent("Plan the next confirmation plate", turn_id="multi-step")
    assert result.intent_class == IntentClass.MULTI_STEP
    assert result.confidence > 0.85
    assert result.route == "multi_agent"


@pytest.mark.asyncio
async def test_classifier_failure_falls_back_gracefully(db_session, monkeypatch):
    from resonantia.services import agent

    class _FakeProvider:
        provider_name = "fake"
        _default_model = "fake"

        async def completion(self, *args, **kwargs):
            from resonantia.services.llm import LLMResponse

            return LLMResponse(content="fallback response", provider="fake", model="fake")

    async def _failing_classifier(*args, **kwargs):
        raise TimeoutError("classifier timed out")

    async def _no_tools():
        return []

    monkeypatch.setattr(agent, "async_session_factory", _test_session_factory)
    monkeypatch.setattr(agent, "classify_intent", _failing_classifier)
    monkeypatch.setattr(agent, "_get_provider", lambda: _FakeProvider())
    monkeypatch.setattr(agent, "_load_tools", _no_tools)
    monkeypatch.setattr(agent, "trace_llm_call", lambda **kwargs: None)

    result = await agent.chat("Summarize this run", request_context=_ctx())
    assert result["message"] == "fallback response"
