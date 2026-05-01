"""Unit tests for resonantia.services.tool_registry (no Redis required)."""

from __future__ import annotations

import json

import pytest

from resonantia.services.tool_registry import (
    ToolParameter,
    ToolSchema,
    _default_tools,
    _deserialize,
    _serialize,
    tool_schema_to_anthropic,
)


# ---------------------------------------------------------------------------
# Anthropic format conversion
# ---------------------------------------------------------------------------

class TestToolSchemaToAnthropic:
    def test_basic_conversion(self):
        tool = ToolSchema(
            name="test_tool",
            description="A test tool",
            category="general",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Search query",
                    required=True,
                ),
            ],
        )
        result = tool_schema_to_anthropic(tool)
        assert result["name"] == "test_tool"
        assert result["description"] == "A test tool"
        assert result["input_schema"]["type"] == "object"
        assert "query" in result["input_schema"]["properties"]
        assert "query" in result["input_schema"]["required"]

    def test_optional_parameter_not_in_required(self):
        tool = ToolSchema(
            name="opt_tool",
            description="Tool with optional param",
            category="general",
            parameters=[
                ToolParameter(
                    name="limit",
                    type="number",
                    description="Max results",
                    required=False,
                    default=10,
                ),
            ],
        )
        result = tool_schema_to_anthropic(tool)
        assert "limit" not in result["input_schema"]["required"]
        assert result["input_schema"]["properties"]["limit"]["default"] == 10

    def test_enum_parameter(self):
        tool = ToolSchema(
            name="enum_tool",
            description="Tool with enum",
            category="general",
            parameters=[
                ToolParameter(
                    name="format",
                    type="string",
                    description="Output format",
                    enum=["csv", "json", "xml"],
                ),
            ],
        )
        result = tool_schema_to_anthropic(tool)
        assert result["input_schema"]["properties"]["format"]["enum"] == [
            "csv",
            "json",
            "xml",
        ]


# ---------------------------------------------------------------------------
# Default tools count and categories
# ---------------------------------------------------------------------------

class TestDefaultTools:
    def test_default_tools_count(self):
        tools = _default_tools()
        assert len(tools) == 33

    def test_default_tools_categories(self):
        tools = _default_tools()
        categories = {t.category for t in tools}
        expected = {
            "plate_mapping",
            "data_processing",
            "sample_management",
            "microscopy",
            "protocol",
            "general",
            "eln",
        }
        assert categories == expected

    def test_all_default_tools_enabled(self):
        tools = _default_tools()
        assert all(t.enabled for t in tools)


# ---------------------------------------------------------------------------
# Serialization round-trip
# ---------------------------------------------------------------------------

class TestToolSerialization:
    def test_round_trip_serialize_deserialize(self):
        original = ToolSchema(
            name="round_trip",
            description="Testing round trip",
            category="general",
            parameters=[
                ToolParameter(
                    name="input",
                    type="string",
                    description="Input value",
                    required=True,
                    enum=["a", "b"],
                    default="a",
                ),
            ],
            version="2.0",
            enabled=False,
        )
        serialized = _serialize(original)
        restored = _deserialize(serialized)

        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.category == original.category
        assert restored.version == original.version
        assert restored.enabled == original.enabled
        assert len(restored.parameters) == 1
        assert restored.parameters[0].name == "input"
        assert restored.parameters[0].enum == ["a", "b"]
        assert restored.parameters[0].default == "a"

    def test_serialize_produces_valid_json(self):
        tool = ToolSchema(
            name="json_test",
            description="desc",
            category="general",
            parameters=[],
        )
        raw = _serialize(tool)
        data = json.loads(raw)
        assert data["name"] == "json_test"
