"""Tests for P2.1 voice safety filter and P2.3 multimodal provider."""

from __future__ import annotations

import pytest

from resonantia.services.voice_safety import (
    VOICE_SAFE_TOOLS,
    VOICE_BLOCKED_TOOLS,
    is_voice_safe,
    voice_block_message,
)


class TestVoiceSafetyClassification:
    def test_lookup_tools_are_safe(self):
        safe = [
            "lookup_sample", "check_inventory", "get_expiring_samples",
            "query_experiments", "query_eln_entries", "query_protocols",
            "calculate_dilution", "get_ic50_values",
        ]
        for tool in safe:
            assert is_voice_safe(tool), f"{tool} should be voice-safe"

    def test_analysis_tools_are_safe(self):
        safe = [
            "fit_dose_response", "normalize_plate", "calculate_z_prime",
            "qpcr_analysis", "read_file_contents",
        ]
        for tool in safe:
            assert is_voice_safe(tool), f"{tool} should be voice-safe"

    def test_create_tools_are_blocked(self):
        blocked = [
            "create_eln_entry", "submit_eln_entry", "create_plate_map",
            "create_protocol", "generate_worklist",
        ]
        for tool in blocked:
            assert not is_voice_safe(tool), f"{tool} should be voice-blocked"

    def test_destructive_tools_are_blocked(self):
        blocked = [
            "cherry_pick", "serial_dilution", "create_experiment",
            "propose_follow_up_experiment",
        ]
        for tool in blocked:
            assert not is_voice_safe(tool), f"{tool} should be voice-blocked"

    def test_unknown_tool_defaults_to_blocked(self):
        assert not is_voice_safe("unknown_tool_xyz")

    def test_no_overlap_between_safe_and_blocked(self):
        overlap = VOICE_SAFE_TOOLS & VOICE_BLOCKED_TOOLS
        assert len(overlap) == 0, f"Tools in both safe and blocked: {overlap}"

    def test_voice_block_message_contains_tool_name(self):
        msg = voice_block_message("submit_eln_entry")
        assert "submit_eln_entry" in msg
        assert "text confirmation" in msg.lower()


class TestVoiceSafetyExecutionGate:
    @pytest.mark.asyncio
    async def test_voice_blocked_tool_returns_pending_approval(self):
        from unittest.mock import AsyncMock, patch

        from resonantia.services.output_validator import ToolResult
        from resonantia.services.tool_executor import execute_tool_typed

        async def _handler(params, org_id):
            return {"executed": True}

        with patch.dict(
            "resonantia.services.tool_executor.TOOL_HANDLERS",
            {"submit_eln_entry": _handler},
        ), patch(
            "resonantia.services.tool_executor._get_tool_schema",
            new_callable=AsyncMock,
            return_value=None,
        ), patch(
            "resonantia.services.tool_executor.check_tenant_refs",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await execute_tool_typed(
                "submit_eln_entry",
                {"entry_id": "eln-1"},
                "org_1",
                source="voice",
                user_id="user_1",
            )

        assert isinstance(result, ToolResult)
        assert result.data["approval_required"] is True
        assert result.data["pending_approval"]["tool_name"] == "submit_eln_entry"


class TestMultimodalProviderConversion:
    def test_anthropic_adapter_converts_image_url_blocks(self):
        from resonantia.services.llm.anthropic_adapter import _extract_messages

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What cells are in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64,iVBORw0KGgo="},
                    },
                ],
            }
        ]

        system, conv = _extract_messages(messages)
        assert len(conv) == 1
        blocks = conv[0]["content"]
        assert blocks[0]["type"] == "text"
        assert blocks[1]["type"] == "image"
        assert blocks[1]["source"]["type"] == "base64"
        assert blocks[1]["source"]["media_type"] == "image/png"
        assert blocks[1]["source"]["data"] == "iVBORw0KGgo="

    def test_anthropic_adapter_passes_text_blocks_through(self):
        from resonantia.services.llm.anthropic_adapter import _extract_messages

        messages = [
            {"role": "user", "content": [{"type": "text", "text": "Hello"}]},
        ]

        _, conv = _extract_messages(messages)
        assert conv[0]["content"][0]["type"] == "text"
        assert conv[0]["content"][0]["text"] == "Hello"

    def test_anthropic_adapter_handles_plain_string_content(self):
        from resonantia.services.llm.anthropic_adapter import _extract_messages

        messages = [
            {"role": "user", "content": "Just text, no images"},
        ]

        _, conv = _extract_messages(messages)
        assert conv[0]["content"] == "Just text, no images"

    def test_anthropic_adapter_handles_non_data_url(self):
        from resonantia.services.llm.anthropic_adapter import _extract_messages

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": "https://example.com/img.png"}},
                ],
            }
        ]

        _, conv = _extract_messages(messages)
        block = conv[0]["content"][0]
        assert block["type"] == "image"
        assert block["source"]["type"] == "url"
