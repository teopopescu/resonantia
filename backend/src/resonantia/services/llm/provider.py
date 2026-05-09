"""Provider interface and shared types for LLM abstraction.

The interface accepts messages in a normalised format (OpenAI-style
``role``/``content`` dicts). Each adapter converts to the SDK-specific
format internally. Tool schemas are stored provider-agnostic in Redis;
the adapter converts them on the fly.
"""

from __future__ import annotations

import abc
from typing import Any, AsyncIterator

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """A single tool invocation returned by the model."""

    id: str
    name: str
    arguments: dict[str, Any]


class LLMResponse(BaseModel):
    """Normalised response from any LLM provider."""

    content: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    model: str = ""
    provider: str = ""
    input_tokens: int = 0
    output_tokens: int = 0


class LLMProvider(abc.ABC):
    """Thin wrapper that normalises OpenAI and Anthropic into one interface."""

    provider_name: str = ""

    @abc.abstractmethod
    async def completion(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict[str, str] | None = None,
    ) -> LLMResponse:
        """Non-streaming completion."""
        ...

    @abc.abstractmethod
    async def completion_stream(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str | ToolCall]:
        """Streaming completion yielding text chunks or tool calls."""
        ...
        # Make the abstract method an async generator so subclasses can
        # ``yield`` without issues.
        yield  # type: ignore[misc]  # pragma: no cover


def get_provider(provider_name: str | None = None) -> LLMProvider:
    """Factory: return the requested provider adapter.

    When *provider_name* is ``None``, falls back to
    ``settings.default_provider``.
    """
    from resonantia.config import get_settings

    settings = get_settings()
    name = (provider_name or settings.default_provider).lower()

    if name == "openai":
        from resonantia.services.llm.openai_adapter import OpenAIAdapter

        return OpenAIAdapter(api_key=settings.openai_api_key, default_model=settings.llm_model)

    if name == "anthropic":
        from resonantia.services.llm.anthropic_adapter import AnthropicAdapter

        return AnthropicAdapter(api_key=settings.anthropic_api_key, default_model=settings.planner_model)

    raise ValueError(f"Unknown LLM provider: {name!r}. Expected 'openai' or 'anthropic'.")
