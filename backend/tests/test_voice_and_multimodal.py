"""Phase 2 completion tests — voice safety, voice-to-ELN flow, multimodal."""

from __future__ import annotations

import inspect

import pytest

from resonantia.services.voice_safety import (
    VOICE_SAFE_TOOLS,
    VOICE_BLOCKED_TOOLS,
    is_voice_safe,
    voice_block_message,
)


class TestVoiceSafety:
    def test_all_safe_tools_are_read_only(self):
        write_verbs = {"create", "submit", "add", "design", "propose"}
        read_exceptions = {"generate_montage"}
        for tool in VOICE_SAFE_TOOLS:
            if tool in read_exceptions:
                continue
            parts = tool.split("_")
            assert parts[0] not in write_verbs, f"{tool} starts with a write verb but is marked safe"

    def test_all_blocked_tools_are_write_operations(self):
        for tool in VOICE_BLOCKED_TOOLS:
            assert is_voice_safe(tool) is False

    def test_safe_tools_count(self):
        assert len(VOICE_SAFE_TOOLS) >= 15

    def test_blocked_tools_count(self):
        assert len(VOICE_BLOCKED_TOOLS) >= 8

    def test_voice_block_message_actionable(self):
        msg = voice_block_message("create_eln_entry")
        assert "text confirmation" in msg.lower()
        assert "create_eln_entry" in msg


class TestVoiceToELNFlow:
    def test_create_eln_is_voice_blocked(self):
        assert not is_voice_safe("create_eln_entry")

    def test_submit_eln_is_voice_blocked(self):
        assert not is_voice_safe("submit_eln_entry")

    def test_query_eln_is_voice_safe(self):
        assert is_voice_safe("query_eln_entries")

    def test_tool_executor_has_voice_safety_gate(self):
        source = inspect.getsource(
            __import__("resonantia.services.tool_executor", fromlist=["execute_tool_typed"])
        )
        assert "is_voice_safe" in source
        assert "create_pending" in source


class TestMultimodalImageConversion:
    def test_openai_image_url_to_anthropic(self):
        from resonantia.services.llm.anthropic_adapter import _extract_messages

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this"},
                    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,/9j/4AAQ"}},
                ],
            }
        ]
        _, conv = _extract_messages(messages)
        blocks = conv[0]["content"]
        assert len(blocks) == 2
        assert blocks[0]["type"] == "text"
        assert blocks[1]["type"] == "image"
        assert blocks[1]["source"]["media_type"] == "image/jpeg"

    def test_plain_string_unchanged(self):
        from resonantia.services.llm.anthropic_adapter import _extract_messages

        messages = [{"role": "user", "content": "plain text"}]
        _, conv = _extract_messages(messages)
        assert conv[0]["content"] == "plain text"

    def test_multiple_images(self):
        from resonantia.services.llm.anthropic_adapter import _extract_messages

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Compare these"},
                    {"type": "image_url", "image_url": {"url": "data:image/png;base64,abc"}},
                    {"type": "image_url", "image_url": {"url": "data:image/png;base64,def"}},
                ],
            }
        ]
        _, conv = _extract_messages(messages)
        blocks = conv[0]["content"]
        assert len(blocks) == 3
        assert blocks[1]["source"]["data"] == "abc"
        assert blocks[2]["source"]["data"] == "def"
