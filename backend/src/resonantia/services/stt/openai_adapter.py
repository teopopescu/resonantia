"""OpenAI STT adapter."""

from __future__ import annotations

import time
from typing import AsyncIterator

from openai import AsyncOpenAI

from resonantia.config import get_settings
from resonantia.middleware import log_stage_latency


class OpenAISTTProvider:
    def __init__(self, *, api_key: str | None = None, default_model: str | None = None) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)
        self._default_model = default_model or settings.stt_model

    async def transcribe(self, audio_file, *, model: str | None = None) -> str:
        start = time.monotonic()
        result = await self._client.audio.transcriptions.create(
            model=model or self._default_model,
            file=audio_file,
        )
        log_stage_latency("stt", (time.monotonic() - start) * 1000, model=model or self._default_model)
        return result.text.strip()

    async def transcribe_stream(self, audio_file, *, model: str | None = None) -> AsyncIterator[str]:
        yield await self.transcribe(audio_file, model=model)
