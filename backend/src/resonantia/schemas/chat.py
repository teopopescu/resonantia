"""Pydantic schemas for the agent chat interface."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: str | None = None
    context: dict[str, Any] | None = Field(
        None,
        description="Optional context like current plate map, experiment, etc.",
    )


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    tool_calls: list[dict[str, Any]] | None = None


class ChatHistoryResponse(BaseModel):
    conversation_id: str
    messages: list[ChatMessage]
