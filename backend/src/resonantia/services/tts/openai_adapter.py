"""OpenAI TTS adapter."""

from __future__ import annotations

import time
from typing import AsyncIterator

from openai import AsyncOpenAI

from resonantia.config import get_settings
from resonantia.middleware import log_stage_latency
from resonantia.telemetry import record_span_exception, set_span_attributes, start_span


class OpenAITTSProvider:
    def __init__(self, *, api_key: str | None = None, default_model: str | None = None) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)
        self._default_model = default_model or settings.tts_model
        self._default_voice = settings.tts_voice

    async def synthesize(self, text: str, *, model: str | None = None, voice: str | None = None) -> bytes:
        start = time.monotonic()
        selected_model = model or self._default_model
        selected_voice = voice or self._default_voice
        with start_span(
            "voice.tts",
            {
                "tts.provider": "openai",
                "tts.model": selected_model,
                "tts.voice": selected_voice,
                "tts.input_chars": len(text),
            },
        ) as span:
            try:
                response = await self._client.audio.speech.create(
                    model=selected_model,
                    voice=selected_voice,
                    input=text,
                )
            except Exception as exc:
                record_span_exception(span, exc)
                raise
        audio = response.content
        elapsed_ms = (time.monotonic() - start) * 1000
        set_span_attributes(span, {"tts.bytes": len(audio), "tts.latency_ms": round(elapsed_ms, 2)})
        log_stage_latency(
            "tts",
            elapsed_ms,
            model=selected_model,
            bytes=len(audio),
        )
        return audio

    async def synthesize_stream(
        self, text: str, *, model: str | None = None, voice: str | None = None
    ) -> AsyncIterator[bytes]:
        audio = await self.synthesize(text, model=model, voice=voice)
        with start_span("voice.tts.first_chunk", {"tts.first_chunk_bytes": len(audio)}):
            pass
        yield audio
