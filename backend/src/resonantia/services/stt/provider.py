"""Speech-to-text provider interface."""

from __future__ import annotations

from typing import AsyncIterator, Protocol


class STTProvider(Protocol):
    async def transcribe(self, audio_file, *, model: str | None = None) -> str:
        ...

    async def transcribe_stream(self, audio_file, *, model: str | None = None) -> AsyncIterator[str]:
        ...
