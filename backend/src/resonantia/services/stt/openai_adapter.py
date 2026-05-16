"""OpenAI STT adapter."""

from __future__ import annotations

import time
from typing import AsyncIterator

from openai import AsyncOpenAI

from resonantia.config import get_settings
from resonantia.middleware import log_stage_latency
from resonantia.services.circuit_breaker import CircuitBreaker
from resonantia.telemetry import record_span_exception, set_span_attributes, start_span


_STT_BREAKER = CircuitBreaker("openai_stt")


class OpenAISTTProvider:
    def __init__(self, *, api_key: str | None = None, default_model: str | None = None) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)
        self._default_model = default_model or settings.stt_model

    async def transcribe(self, audio_file, *, model: str | None = None) -> str:
        start = time.monotonic()
        selected_model = model or self._default_model
        with start_span("voice.stt", {"stt.provider": "openai", "stt.model": selected_model}) as span:
            try:
                result = await _STT_BREAKER.call(
                    lambda: self._client.audio.transcriptions.create(
                        model=selected_model,
                        file=audio_file,
                    ),
                    timeout_seconds=10.0,
                )
            except Exception as exc:
                record_span_exception(span, exc)
                raise
        elapsed_ms = (time.monotonic() - start) * 1000
        set_span_attributes(span, {"stt.latency_ms": round(elapsed_ms, 2)})
        log_stage_latency("stt", elapsed_ms, model=selected_model)
        return result.text.strip()

    async def transcribe_stream(self, audio_file, *, model: str | None = None) -> AsyncIterator[str]:
        yield await self.transcribe(audio_file, model=model)
