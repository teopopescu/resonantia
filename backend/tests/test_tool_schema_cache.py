"""Tests for in-process tool schema caching."""

from __future__ import annotations

import pytest

from resonantia.services.tool_registry import (
    ToolParameter,
    ToolSchema,
    get_tools_as_anthropic,
    invalidate_tool_schema_cache,
    tool_schema_cache_metrics,
)


def _tool(name: str) -> ToolSchema:
    return ToolSchema(
        name=name,
        description=f"{name} description",
        category="general",
        parameters=[ToolParameter(name="query", type="string", description="Query")],
    )


@pytest.mark.asyncio
async def test_get_tools_as_anthropic_uses_local_cache(monkeypatch):
    from resonantia.services import tool_registry

    invalidate_tool_schema_cache()
    calls = 0

    async def fake_list_tools(category=None):
        nonlocal calls
        calls += 1
        return [_tool("lookup_sample")]

    monkeypatch.setattr(tool_registry, "list_tools", fake_list_tools)

    first = await get_tools_as_anthropic()
    second = await get_tools_as_anthropic()

    assert first == second
    assert calls == 1
    assert tool_schema_cache_metrics()["hits"] >= 1


@pytest.mark.asyncio
async def test_schema_invalidation_forces_cache_miss(monkeypatch):
    from resonantia.services import tool_registry

    invalidate_tool_schema_cache()
    calls = 0

    async def fake_list_tools(category=None):
        nonlocal calls
        calls += 1
        return [_tool(f"tool_{calls}")]

    monkeypatch.setattr(tool_registry, "list_tools", fake_list_tools)

    first = await get_tools_as_anthropic()
    invalidate_tool_schema_cache()
    second = await get_tools_as_anthropic()

    assert calls == 2
    assert first[0]["name"] == "tool_1"
    assert second[0]["name"] == "tool_2"


@pytest.mark.asyncio
async def test_agent_load_tools_uses_cached_registry(monkeypatch):
    from resonantia.services import agent, tool_registry

    invalidate_tool_schema_cache()
    calls = 0

    async def fake_list_tools(category=None):
        nonlocal calls
        calls += 1
        return [_tool("lookup_sample")]

    monkeypatch.setattr(tool_registry, "list_tools", fake_list_tools)

    await agent._load_tools()
    await agent._load_tools()

    assert calls == 1
