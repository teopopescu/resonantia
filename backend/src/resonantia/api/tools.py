"""Agentic tool schema registry endpoints."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from resonantia.services.tool_registry import (
    ToolParameter,
    ToolSchema,
    get_tool,
    list_tools,
    register_tool,
    remove_tool,
    search_tools,
    tool_schema_to_anthropic,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class ToolParameterIn(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True
    enum: list[str] | None = None
    default: Any = None


class ToolSchemaIn(BaseModel):
    name: str
    description: str
    category: str
    parameters: list[ToolParameterIn]
    version: str = "1.0"
    enabled: bool = True


class ToolSchemaOut(BaseModel):
    name: str
    description: str
    category: str
    parameters: list[dict[str, Any]]
    version: str
    enabled: bool
    anthropic_format: dict[str, Any] | None = None


def _to_response(tool: ToolSchema) -> ToolSchemaOut:
    return ToolSchemaOut(
        name=tool.name,
        description=tool.description,
        category=tool.category,
        parameters=[asdict(p) for p in tool.parameters],
        version=tool.version,
        enabled=tool.enabled,
        anthropic_format=tool_schema_to_anthropic(tool),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/search", response_model=list[ToolSchemaOut])
async def search_tools_endpoint(
    q: str = Query(..., min_length=1, description="Search query"),
) -> list[ToolSchemaOut]:
    """Search tools by keyword match on name and description."""
    results = await search_tools(q)
    return [_to_response(t) for t in results]


@router.get("/", response_model=list[ToolSchemaOut])
async def list_tools_endpoint(
    category: str | None = Query(default=None, description="Filter by category"),
) -> list[ToolSchemaOut]:
    """List all registered tools, optionally filtered by category."""
    tools = await list_tools(category)
    return [_to_response(t) for t in tools]


@router.get("/{name}", response_model=ToolSchemaOut)
async def get_tool_endpoint(name: str) -> ToolSchemaOut:
    """Get a single tool schema by name."""
    tool = await get_tool(name)
    if tool is None:
        raise HTTPException(status_code=404, detail=f"Tool '{name}' not found")
    return _to_response(tool)


@router.post("/", response_model=ToolSchemaOut, status_code=201)
async def register_tool_endpoint(body: ToolSchemaIn) -> ToolSchemaOut:
    """Register a new tool or update an existing one."""
    tool = ToolSchema(
        name=body.name,
        description=body.description,
        category=body.category,
        parameters=[
            ToolParameter(
                name=p.name,
                type=p.type,
                description=p.description,
                required=p.required,
                enum=p.enum,
                default=p.default,
            )
            for p in body.parameters
        ],
        version=body.version,
        enabled=body.enabled,
    )
    await register_tool(tool)
    return _to_response(tool)


@router.delete("/{name}", status_code=204)
async def remove_tool_endpoint(name: str) -> None:
    """Remove a tool from the registry."""
    existed = await remove_tool(name)
    if not existed:
        raise HTTPException(status_code=404, detail=f"Tool '{name}' not found")
