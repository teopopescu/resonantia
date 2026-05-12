"""OpenAI TTS adapter."""

from __future__ import annotations

import time
from typing import AsyncIterator

from openai import AsyncOpenAI

from resonantia.config import get_settings
from resonantia.middleware import log_stage_latency


class OpenAITTSProvider:
    def __init__(self, *, api_key: str | None = None, default_model: str | None = None) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)
        self._default_model = default_model or settings.tts_model
        self._default_voice = settings.tts_voice

    async def synthesize(self, text: str, *, model: str | None = None, voice: str | None = None) -> bytes:
        start = time.monotonic()
        response = await self._client.audio.speech.create(
            model=model or self._default_model,
            voice=voice or self._default_voice,
            input=text,
        )
        audio = response.content
        log_stage_latency(
            "tts",
            (time.monotonic() - start) * 1000,
            model=model or self._default_model,
            bytes=len(audio),
        )
        return audio

    async def synthesize_stream(
        self, text: str, *, model: str | None = None, voice: str | None = None
    ) -> AsyncIterator[bytes]:
        audio = await self.synthesize(text, model=model, voice=voice)
        yield audio
