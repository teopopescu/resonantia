"""Speech-to-text providers."""

from resonantia.services.stt.openai_adapter import OpenAISTTProvider
from resonantia.services.stt.provider import STTProvider

__all__ = ["OpenAISTTProvider", "STTProvider"]
