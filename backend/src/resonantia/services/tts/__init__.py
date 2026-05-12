"""Text-to-speech providers."""

from resonantia.services.tts.openai_adapter import OpenAITTSProvider
from resonantia.services.tts.provider import TTSProvider

__all__ = ["OpenAITTSProvider", "TTSProvider"]
