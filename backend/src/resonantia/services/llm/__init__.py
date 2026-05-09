"""LLM provider abstraction — thin wrappers over OpenAI and Anthropic SDKs.

Usage::

    from resonantia.services.llm import get_provider, LLMResponse, ToolCall

    provider = get_provider()  # uses settings.default_provider
    response = await provider.completion(messages=[...], tools=[...])
"""

from resonantia.services.llm.provider import (
    LLMProvider,
    LLMResponse,
    ToolCall,
    get_provider,
)

__all__ = [
    "LLMProvider",
    "LLMResponse",
    "ToolCall",
    "get_provider",
]
