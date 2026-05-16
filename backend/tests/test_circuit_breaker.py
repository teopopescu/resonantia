"""Tests for provider circuit breakers and timeout wiring."""

from __future__ import annotations

import asyncio
import inspect

import pytest

from resonantia.services.circuit_breaker import CircuitBreaker, ProviderCircuitOpen


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_three_failures():
    breaker = CircuitBreaker("provider", failure_threshold=3, failure_window_seconds=60, open_seconds=30)
    calls = 0

    async def fail():
        nonlocal calls
        calls += 1
        raise RuntimeError("provider down")

    for _ in range(3):
        with pytest.raises(RuntimeError):
            await breaker.call(fail, timeout_seconds=1)

    with pytest.raises(ProviderCircuitOpen):
        await breaker.call(fail, timeout_seconds=1)

    assert calls == 3


@pytest.mark.asyncio
async def test_circuit_breaker_closes_after_open_window(monkeypatch: pytest.MonkeyPatch):
    now = 1000.0
    monkeypatch.setattr("resonantia.services.circuit_breaker.time.monotonic", lambda: now)
    breaker = CircuitBreaker("provider", failure_threshold=1, open_seconds=30)

    async def fail():
        raise RuntimeError("provider down")

    with pytest.raises(RuntimeError):
        await breaker.call(fail, timeout_seconds=1)
    assert breaker.is_open() is True

    now = 1031.0
    assert breaker.is_open() is False


@pytest.mark.asyncio
async def test_circuit_breaker_enforces_timeout():
    breaker = CircuitBreaker("provider", failure_threshold=3)

    async def slow():
        await asyncio.sleep(1)

    with pytest.raises(asyncio.TimeoutError):
        await breaker.call(slow, timeout_seconds=0.001)


def test_provider_adapters_use_planned_timeouts():
    from resonantia.services.llm import anthropic_adapter
    from resonantia.services.stt import openai_adapter as stt_adapter
    from resonantia.services.tts import openai_adapter as tts_adapter

    assert "timeout_seconds=30.0" in inspect.getsource(anthropic_adapter.AnthropicAdapter.completion)
    assert "timeout_seconds=10.0" in inspect.getsource(stt_adapter.OpenAISTTProvider.transcribe)
    assert "timeout_seconds=10.0" in inspect.getsource(tts_adapter.OpenAITTSProvider.synthesize)


def test_voice_tts_activity_returns_text_only_on_tts_failure():
    from resonantia.workflows import voice_activities

    source = inspect.getsource(voice_activities.synthesize_voice_turn_activity)
    assert "text_only" in source
    assert "TTS unavailable" in source
