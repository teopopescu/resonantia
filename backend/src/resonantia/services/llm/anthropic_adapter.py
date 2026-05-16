"""Anthropic adapter — wraps ``AsyncAnthropic`` behind the ``LLMProvider`` interface."""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

from anthropic import AsyncAnthropic

from resonantia.services.llm.provider import LLMProvider, LLMResponse, ToolCall
from resonantia.telemetry import record_span_exception, set_span_attributes, start_span

logger = logging.getLogger(__name__)


def _to_anthropic_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert provider-agnostic tool dicts to Anthropic tool-use format.

    Accepts either:
    - Anthropic format: ``{"name": ..., "description": ..., "input_schema": ...}``
    - OpenAI format: ``{"type": "function", "function": {...}}``
    """
    converted: list[dict[str, Any]] = []
    for t in tools:
        if "input_schema" in t and "name" in t:
            converted.append(t)
        elif t.get("type") == "function" and "function" in t:
            fn = t["function"]
            converted.append(
                {
                    "name": fn["name"],
                    "description": fn.get("description", ""),
                    "input_schema": fn.get("parameters", {}),
                }
            )
        else:
            converted.append(t)
    return converted


def _with_cache_control(block: dict[str, Any], cache_control: dict[str, str] | None) -> dict[str, Any]:
    if cache_control:
        block = {**block, "cache_control": cache_control}
    return block


def _extract_messages(
    messages: list[dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    """Split an OpenAI-style message list into (system_prompt, user_messages).

    Anthropic requires the system prompt as a separate ``system`` kwarg and
    the messages list must start with a ``user`` turn.
    """
    system_parts: list[str] = []
    conversation: list[dict[str, Any]] = []

    for msg in messages:
        role = msg.get("role", "")
        if role == "system":
            system_parts.append(msg.get("content", "") or "")
            continue

        if role == "tool":
            # Anthropic expects tool results as user messages with
            # ``tool_result`` content blocks.
            conversation.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.get("tool_call_id", ""),
                            "content": msg.get("content", ""),
                        }
                    ],
                }
            )
            continue

        if role == "assistant" and msg.get("tool_calls"):
            # Convert OpenAI-style assistant tool_calls to Anthropic
            # content blocks (text + tool_use).
            content_blocks: list[dict[str, Any]] = []
            if msg.get("content"):
                content_blocks.append({"type": "text", "text": msg["content"]})
            for tc in msg["tool_calls"]:
                fn = tc.get("function", tc)
                args = fn.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                content_blocks.append(
                    {
                        "type": "tool_use",
                        "id": tc.get("id", ""),
                        "name": fn.get("name", ""),
                        "input": args,
                    }
                )
            conversation.append({"role": "assistant", "content": content_blocks})
            continue

        # Regular user / assistant messages.
        content = msg.get("content", "")
        if isinstance(content, list):
            # Convert OpenAI-style image blocks to Anthropic format.
            anthropic_blocks: list[dict[str, Any]] = []
            for block in content:
                if block.get("type") == "image_url":
                    url = block.get("image_url", {}).get("url", "")
                    if url.startswith("data:"):
                        parts = url.split(",", 1)
                        header = parts[0]  # data:image/png;base64
                        b64_data = parts[1] if len(parts) > 1 else ""
                        media_type = header.replace("data:", "").replace(";base64", "")
                        anthropic_blocks.append({
                            "type": "image",
                            "source": {"type": "base64", "media_type": media_type, "data": b64_data},
                        })
                    else:
                        anthropic_blocks.append({"type": "image", "source": {"type": "url", "url": url}})
                else:
                    anthropic_blocks.append(block)
            conversation.append({"role": role, "content": anthropic_blocks})
        else:
            conversation.append({"role": role, "content": str(content or "")})

    # Merge consecutive same-role messages (Anthropic disallows them).
    merged: list[dict[str, Any]] = []
    for m in conversation:
        if merged and merged[-1]["role"] == m["role"]:
            prev_content = merged[-1]["content"]
            cur_content = m["content"]

            # Normalise both to lists.
            if isinstance(prev_content, str):
                prev_content = [{"type": "text", "text": prev_content}]
            if isinstance(cur_content, str):
                cur_content = [{"type": "text", "text": cur_content}]

            merged[-1]["content"] = prev_content + cur_content
        else:
            merged.append(m)

    return "\n\n".join(system_parts), merged


def _parse_tool_calls(content_blocks: list[Any]) -> list[ToolCall]:
    """Extract ``ToolCall`` objects from Anthropic content blocks."""
    result: list[ToolCall] = []
    for block in content_blocks:
        if getattr(block, "type", None) == "tool_use":
            result.append(
                ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input if isinstance(block.input, dict) else {},
                )
            )
    return result


class AnthropicAdapter(LLMProvider):
    """Thin wrapper around the Anthropic Python SDK."""

    provider_name = "anthropic"

    def __init__(self, *, api_key: str, default_model: str = "claude-sonnet-4-20250514") -> None:
        self._client = AsyncAnthropic(api_key=api_key)
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
        system_prompt, anthropic_messages = _extract_messages(messages)
        cache_control = cache_control or {"type": "ephemeral"}

        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": anthropic_messages,
        }
        if temperature > 0:
            kwargs["temperature"] = temperature
        if system_prompt:
            kwargs["system"] = [
                _with_cache_control({"type": "text", "text": system_prompt}, cache_control)
            ]
        if tools:
            kwargs["tools"] = [
                _with_cache_control(tool, cache_control)
                for tool in _to_anthropic_tools(tools)
            ]

        with start_span(
            "voice.agent.llm",
            {
                "llm.provider": self.provider_name,
                "llm.model": model,
                "llm.tool_count": len(tools or []),
                "llm.streaming": False,
            },
        ) as span:
            try:
                response = await self._client.messages.create(**kwargs)
            except Exception as exc:
                record_span_exception(span, exc)
                raise

        # Extract text content.
        text_parts: list[str] = []
        for block in response.content:
            if getattr(block, "type", None) == "text":
                text_parts.append(block.text)

        tool_calls = _parse_tool_calls(response.content)
        cache_read = getattr(response.usage, "cache_read_input_tokens", 0) or 0
        logger.info(
            "anthropic_completion cache_read_input_tokens=%s input_tokens=%s output_tokens=%s",
            cache_read,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )
        set_span_attributes(
            span,
            {
                "llm.input_tokens": response.usage.input_tokens,
                "llm.output_tokens": response.usage.output_tokens,
                "llm.cache_read_input_tokens": cache_read,
                "llm.tool_calls": len(tool_calls),
            },
        )

        return LLMResponse(
            content="\n".join(text_parts) if text_parts else None,
            tool_calls=tool_calls,
            model=model,
            provider=self.provider_name,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cache_read_input_tokens=cache_read,
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
        system_prompt, anthropic_messages = _extract_messages(messages)

        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": anthropic_messages,
        }
        if temperature > 0:
            kwargs["temperature"] = temperature
        if system_prompt:
            kwargs["system"] = system_prompt
        if tools:
            kwargs["tools"] = _to_anthropic_tools(tools)

        # Accumulate tool_use blocks.
        current_tool: dict[str, Any] | None = None

        with start_span(
            "voice.agent.llm",
            {
                "llm.provider": self.provider_name,
                "llm.model": model,
                "llm.tool_count": len(tools or []),
                "llm.streaming": True,
            },
        ) as span:
            try:
                async with self._client.messages.stream(**kwargs) as stream:
                    async for event in stream:
                        if event.type == "content_block_start":
                            block = event.content_block
                            if getattr(block, "type", None) == "tool_use":
                                current_tool = {
                                    "id": block.id,
                                    "name": block.name,
                                    "arguments": "",
                                }

                        elif event.type == "content_block_delta":
                            delta = event.delta
                            if getattr(delta, "type", None) == "text_delta":
                                yield delta.text
                            elif getattr(delta, "type", None) == "input_json_delta":
                                if current_tool is not None:
                                    current_tool["arguments"] += delta.partial_json

                        elif event.type == "content_block_stop":
                            if current_tool is not None:
                                try:
                                    args = json.loads(current_tool["arguments"]) if current_tool["arguments"] else {}
                                except json.JSONDecodeError:
                                    args = {}
                                yield ToolCall(
                                    id=current_tool["id"],
                                    name=current_tool["name"],
                                    arguments=args,
                                )
                                current_tool = None
            except Exception as exc:
                record_span_exception(span, exc)
                raise
