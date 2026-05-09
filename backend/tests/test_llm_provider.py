"""Tests for the LLM provider abstraction layer.

Covers: provider factory, tool schema conversion, response normalisation,
and basic streaming contract (mocked SDKs -- no real API calls).
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from resonantia.services.llm.provider import (
    LLMProvider,
    LLMResponse,
    ToolCall,
    get_provider,
)

# The factory imports get_settings lazily from resonantia.config, so we
# patch it at source rather than at the call-site module.
_SETTINGS_PATCH_TARGET = "resonantia.config.get_settings"
from resonantia.services.llm.openai_adapter import (
    OpenAIAdapter,
    _to_openai_tools,
    _parse_tool_calls,
)
from resonantia.services.llm.anthropic_adapter import (
    AnthropicAdapter,
    _to_anthropic_tools,
    _extract_messages,
)


# ============================================================================
# Factory
# ============================================================================


class TestFactory:
    def test_get_provider_returns_openai_adapter(self):
        with patch(
            _SETTINGS_PATCH_TARGET,
            return_value=SimpleNamespace(
                default_provider="openai",
                openai_api_key="test-key",
                anthropic_api_key="",
                llm_model="gpt-4o",
                planner_model="gpt-4o",
            ),
        ):
            p = get_provider("openai")
            assert isinstance(p, OpenAIAdapter)
            assert p.provider_name == "openai"

    def test_get_provider_returns_anthropic_adapter(self):
        with patch(
            _SETTINGS_PATCH_TARGET,
            return_value=SimpleNamespace(
                default_provider="anthropic",
                openai_api_key="",
                anthropic_api_key="test-key",
                llm_model="gpt-4o",
                planner_model="claude-sonnet-4-20250514",
            ),
        ):
            p = get_provider("anthropic")
            assert isinstance(p, AnthropicAdapter)
            assert p.provider_name == "anthropic"

    def test_get_provider_uses_default_when_none(self):
        with patch(
            _SETTINGS_PATCH_TARGET,
            return_value=SimpleNamespace(
                default_provider="anthropic",
                openai_api_key="",
                anthropic_api_key="test-key",
                llm_model="gpt-4o",
                planner_model="claude-sonnet-4-20250514",
            ),
        ):
            p = get_provider(None)
            assert isinstance(p, AnthropicAdapter)

    def test_get_provider_raises_on_unknown(self):
        with patch(
            _SETTINGS_PATCH_TARGET,
            return_value=SimpleNamespace(
                default_provider="unknown",
                openai_api_key="",
                anthropic_api_key="",
                llm_model="",
                planner_model="",
            ),
        ):
            with pytest.raises(ValueError, match="Unknown LLM provider"):
                get_provider("unknown")


# ============================================================================
# Tool schema conversion
# ============================================================================


class TestToolSchemaConversion:
    """Test that tool schemas convert correctly between formats."""

    def test_anthropic_to_openai(self):
        anthropic_tool = {
            "name": "fit_dose_response",
            "description": "Fit a curve",
            "input_schema": {
                "type": "object",
                "properties": {"x": {"type": "array"}},
                "required": ["x"],
            },
        }
        result = _to_openai_tools([anthropic_tool])
        assert len(result) == 1
        assert result[0]["type"] == "function"
        assert result[0]["function"]["name"] == "fit_dose_response"
        assert result[0]["function"]["parameters"]["type"] == "object"

    def test_openai_passthrough(self):
        openai_tool = {
            "type": "function",
            "function": {
                "name": "test",
                "description": "Test tool",
                "parameters": {"type": "object"},
            },
        }
        result = _to_openai_tools([openai_tool])
        assert result[0] is openai_tool

    def test_openai_to_anthropic(self):
        openai_tool = {
            "type": "function",
            "function": {
                "name": "lookup_sample",
                "description": "Look up a sample",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
        }
        result = _to_anthropic_tools([openai_tool])
        assert len(result) == 1
        assert result[0]["name"] == "lookup_sample"
        assert result[0]["input_schema"]["type"] == "object"

    def test_anthropic_passthrough(self):
        anthropic_tool = {
            "name": "test",
            "description": "Test",
            "input_schema": {"type": "object"},
        }
        result = _to_anthropic_tools([anthropic_tool])
        assert result[0] is anthropic_tool


# ============================================================================
# Message format conversion (Anthropic adapter)
# ============================================================================


class TestMessageExtraction:
    """Test OpenAI-style messages -> Anthropic format conversion."""

    def test_system_message_extracted(self):
        messages = [
            {"role": "system", "content": "You are a helper."},
            {"role": "user", "content": "Hello"},
        ]
        system, conv = _extract_messages(messages)
        assert "helper" in system
        assert len(conv) == 1
        assert conv[0]["role"] == "user"

    def test_tool_messages_converted(self):
        messages = [
            {"role": "user", "content": "Call the tool"},
            {
                "role": "assistant",
                "content": "Calling",
                "tool_calls": [
                    {
                        "id": "tc1",
                        "type": "function",
                        "function": {"name": "test", "arguments": "{}"},
                    }
                ],
            },
            {"role": "tool", "tool_call_id": "tc1", "content": "result"},
        ]
        system, conv = _extract_messages(messages)
        assert system == ""
        assert len(conv) == 3
        # Assistant message should have tool_use blocks
        assert conv[1]["role"] == "assistant"
        content_blocks = conv[1]["content"]
        assert any(b["type"] == "tool_use" for b in content_blocks)
        # Tool result should be user message with tool_result block
        assert conv[2]["role"] == "user"
        assert conv[2]["content"][0]["type"] == "tool_result"

    def test_consecutive_same_role_merged(self):
        messages = [
            {"role": "user", "content": "part 1"},
            {"role": "user", "content": "part 2"},
        ]
        _system, conv = _extract_messages(messages)
        assert len(conv) == 1

    def test_multiple_system_messages_joined(self):
        messages = [
            {"role": "system", "content": "Rule 1."},
            {"role": "system", "content": "Rule 2."},
            {"role": "user", "content": "Go"},
        ]
        system, conv = _extract_messages(messages)
        assert "Rule 1." in system
        assert "Rule 2." in system
        assert len(conv) == 1


# ============================================================================
# OpenAI adapter completion (mocked SDK)
# ============================================================================


class TestOpenAIAdapterCompletion:
    @pytest.mark.asyncio
    async def test_completion_text_response(self):
        adapter = OpenAIAdapter(api_key="test", default_model="gpt-4o")

        mock_response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="Hello!", tool_calls=None),
                    finish_reason="stop",
                )
            ],
            usage=SimpleNamespace(prompt_tokens=5, completion_tokens=3),
        )
        adapter._client = MagicMock()
        adapter._client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await adapter.completion(
            messages=[{"role": "user", "content": "Hi"}]
        )

        assert isinstance(result, LLMResponse)
        assert result.content == "Hello!"
        assert result.tool_calls == []
        assert result.model == "gpt-4o"
        assert result.provider == "openai"
        assert result.input_tokens == 5
        assert result.output_tokens == 3

    @pytest.mark.asyncio
    async def test_completion_with_tool_calls(self):
        adapter = OpenAIAdapter(api_key="test", default_model="gpt-4o")

        mock_response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=None,
                        tool_calls=[
                            SimpleNamespace(
                                id="call_1",
                                function=SimpleNamespace(
                                    name="lookup_sample",
                                    arguments='{"query": "anti-GFP"}',
                                ),
                            )
                        ],
                    ),
                    finish_reason="tool_calls",
                )
            ],
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=15),
        )
        adapter._client = MagicMock()
        adapter._client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await adapter.completion(
            messages=[{"role": "user", "content": "Look up anti-GFP"}],
            tools=[{"name": "lookup_sample", "description": "x", "input_schema": {}}],
        )

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "lookup_sample"
        assert result.tool_calls[0].arguments == {"query": "anti-GFP"}


# ============================================================================
# Anthropic adapter completion (mocked SDK)
# ============================================================================


class TestAnthropicAdapterCompletion:
    @pytest.mark.asyncio
    async def test_completion_text_response(self):
        adapter = AnthropicAdapter(api_key="test", default_model="claude-sonnet-4-20250514")

        mock_response = SimpleNamespace(
            content=[SimpleNamespace(type="text", text="Hello from Claude!")],
            usage=SimpleNamespace(input_tokens=8, output_tokens=4),
        )
        adapter._client = MagicMock()
        adapter._client.messages.create = AsyncMock(return_value=mock_response)

        result = await adapter.completion(
            messages=[
                {"role": "system", "content": "Be helpful."},
                {"role": "user", "content": "Hi"},
            ]
        )

        assert isinstance(result, LLMResponse)
        assert result.content == "Hello from Claude!"
        assert result.tool_calls == []
        assert result.provider == "anthropic"
        assert result.input_tokens == 8

    @pytest.mark.asyncio
    async def test_completion_with_tool_calls(self):
        adapter = AnthropicAdapter(api_key="test", default_model="claude-sonnet-4-20250514")

        mock_response = SimpleNamespace(
            content=[
                SimpleNamespace(type="text", text="Let me look that up."),
                SimpleNamespace(
                    type="tool_use",
                    id="tu_1",
                    name="check_inventory",
                    input={"reagent_name": "DMSO"},
                ),
            ],
            usage=SimpleNamespace(input_tokens=12, output_tokens=20),
        )
        adapter._client = MagicMock()
        adapter._client.messages.create = AsyncMock(return_value=mock_response)

        result = await adapter.completion(
            messages=[{"role": "user", "content": "Check DMSO stock"}],
            tools=[{"name": "check_inventory", "description": "x", "input_schema": {}}],
        )

        assert result.content == "Let me look that up."
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "check_inventory"
        assert result.tool_calls[0].arguments == {"reagent_name": "DMSO"}


# ============================================================================
# LLMResponse and ToolCall models
# ============================================================================


class TestModels:
    def test_llm_response_defaults(self):
        r = LLMResponse()
        assert r.content is None
        assert r.tool_calls == []
        assert r.model == ""
        assert r.input_tokens == 0

    def test_tool_call_serialisation(self):
        tc = ToolCall(id="x", name="test", arguments={"key": "val"})
        d = tc.model_dump()
        assert d["name"] == "test"
        assert d["arguments"]["key"] == "val"

    def test_openai_parse_tool_calls_handles_bad_json(self):
        raw = [
            SimpleNamespace(
                id="tc1",
                function=SimpleNamespace(name="test", arguments="not-json"),
            )
        ]
        result = _parse_tool_calls(raw)
        assert len(result) == 1
        assert result[0].arguments == {}

    def test_openai_parse_tool_calls_handles_empty(self):
        raw = [
            SimpleNamespace(
                id="tc1",
                function=SimpleNamespace(name="test", arguments=""),
            )
        ]
        result = _parse_tool_calls(raw)
        assert result[0].arguments == {}


# ============================================================================
# Provider switching
# ============================================================================


class TestProviderSwitching:
    """Verify that changing DEFAULT_PROVIDER config changes which adapter is used."""

    def test_switching_to_openai(self):
        with patch(
            _SETTINGS_PATCH_TARGET,
            return_value=SimpleNamespace(
                default_provider="openai",
                openai_api_key="key",
                anthropic_api_key="",
                llm_model="gpt-4o",
                planner_model="gpt-4o",
            ),
        ):
            p = get_provider()
            assert isinstance(p, OpenAIAdapter)

    def test_switching_to_anthropic(self):
        with patch(
            _SETTINGS_PATCH_TARGET,
            return_value=SimpleNamespace(
                default_provider="anthropic",
                openai_api_key="",
                anthropic_api_key="key",
                llm_model="gpt-4o",
                planner_model="claude-sonnet-4-20250514",
            ),
        ):
            p = get_provider()
            assert isinstance(p, AnthropicAdapter)
