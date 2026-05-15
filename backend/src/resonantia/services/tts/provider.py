"""Text-to-speech provider interface."""

from __future__ import annotations

from typing import AsyncIterator, Protocol


class TTSProvider(Protocol):
    async def synthesize(self, text: str, *, model: str | None = None, voice: str | None = None) -> bytes:
        ...

    async def synthesize_stream(
        self, text: str, *, model: str | None = None, voice: str | None = None
    ) -> AsyncIterator[bytes]:
        ...
