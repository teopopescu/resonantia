"""OpenAI adapter — wraps ``AsyncOpenAI`` behind the ``LLMProvider`` interface."""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

from openai import AsyncOpenAI

from resonantia.services.llm.provider import LLMProvider, LLMResponse, ToolCall

logger = logging.getLogger(__name__)


def _to_openai_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert provider-agnostic tool dicts to OpenAI function-calling format.

    Accepts either:
    - Already-OpenAI format: ``{"type": "function", "function": {...}}``
    - Anthropic format: ``{"name": ..., "description": ..., "input_schema": ...}``
    """
    converted: list[dict[str, Any]] = []
    for t in tools:
        if t.get("type") == "function" and "function" in t:
            converted.append(t)
        else:
            converted.append(
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "parameters": t.get("input_schema", t.get("parameters", {})),
                    },
                }
            )
    return converted


def _parse_tool_calls(raw_tool_calls: list[Any]) -> list[ToolCall]:
    """Normalise OpenAI tool_calls into ``ToolCall`` objects."""
    result: list[ToolCall] = []
    for tc in raw_tool_calls:
        try:
            args = json.loads(tc.function.arguments) if tc.function.arguments else {}
        except json.JSONDecodeError:
            args = {}
        result.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))
    return result


class OpenAIAdapter(LLMProvider):
    """Thin wrapper around the OpenAI Python SDK."""

    provider_name = "openai"

    def __init__(self, *, api_key: str, default_model: str = "gpt-4o") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._default_model = default_model

    async def completion(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict[str, str] | None = None,
        cache_control: dict[str, str] | None = None,
    ) -> LLMResponse:
        model = model or self._default_model

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = _to_openai_tools(tools)
        if response_format:
            kwargs["response_format"] = response_format

        response = await self._client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        tool_calls: list[ToolCall] = []
        if choice.message.tool_calls:
            tool_calls = _parse_tool_calls(choice.message.tool_calls)

        input_tokens = 0
        output_tokens = 0
        if response.usage:
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

        return LLMResponse(
            content=choice.message.content,
            tool_calls=tool_calls,
            model=model,
            provider=self.provider_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    async def completion_stream(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str | ToolCall]:
        model = model or self._default_model

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = _to_openai_tools(tools)

        # Accumulate tool call fragments for reassembly.
        tool_call_acc: dict[int, dict[str, str]] = {}

        stream = await self._client.chat.completions.create(**kwargs)
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue

            # Text content
            if delta.content:
                yield delta.content

            # Tool call deltas
            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_call_acc:
                        tool_call_acc[idx] = {
                            "id": tc_delta.id or "",
                            "name": "",
                            "arguments": "",
                        }
                    if tc_delta.id:
                        tool_call_acc[idx]["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            tool_call_acc[idx]["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            tool_call_acc[idx]["arguments"] += tc_delta.function.arguments

        # Emit accumulated tool calls at the end of the stream.
        for _idx in sorted(tool_call_acc):
            acc = tool_call_acc[_idx]
            try:
                args = json.loads(acc["arguments"]) if acc["arguments"] else {}
            except json.JSONDecodeError:
                args = {}
            yield ToolCall(id=acc["id"], name=acc["name"], arguments=args)
