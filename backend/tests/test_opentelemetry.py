"""Tests for OpenTelemetry integration wiring."""

from __future__ import annotations

import inspect


def test_telemetry_helpers_degrade_without_collector():
    from resonantia.telemetry import current_trace_context, start_span

    with start_span("test.span", {"key": "value"}) as span:
        assert span is None or hasattr(span, "set_attribute")

    assert isinstance(current_trace_context(), dict)


def test_provider_adapters_define_required_voice_spans():
    from resonantia.services.llm import anthropic_adapter
    from resonantia.services.stt import openai_adapter as stt_adapter
    from resonantia.services.tts import openai_adapter as tts_adapter

    llm_source = inspect.getsource(anthropic_adapter.AnthropicAdapter)
    stt_source = inspect.getsource(stt_adapter.OpenAISTTProvider)
    tts_source = inspect.getsource(tts_adapter.OpenAITTSProvider)

    assert "voice.agent.llm" in llm_source
    assert "voice.stt" in stt_source
    assert "voice.tts" in tts_source
    assert "voice.tts.first_chunk" in tts_source


def test_request_middleware_and_tool_executor_define_trace_spans():
    from resonantia import middleware
    from resonantia.services import tool_executor

    middleware_source = inspect.getsource(middleware.RequestContextMiddleware)
    tool_source = inspect.getsource(tool_executor.execute_tool_typed)

    assert "voice.total" in middleware_source
    assert "http.request" in middleware_source
    assert "voice.agent.tool." in tool_source


def test_temporal_client_propagates_trace_context():
    from resonantia.services import temporal_client

    source = inspect.getsource(temporal_client.start_agent_workflow)

    assert "_trace_context" in source
    assert "current_trace_context()" in source
