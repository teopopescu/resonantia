"""Pydantic schemas for the agent chat interface."""

from __future__ import annotations

from datetime import datetime
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
    model_config = {"extra": "forbid"}

    message: str = Field(..., min_length=1, max_length=32_000)
    conversation_id: str | None = None
    context: dict[str, Any] | None = Field(
        None,
        description="Optional context like current plate map, experiment, etc.",
    )
    attachments: list[str] | None = Field(
        None,
        max_length=10,
        description="Optional list of file IDs uploaded via /api/v1/files/upload. "
        "Image-typed files are passed to the agent as vision content blocks. "
        "Non-image files are referenced as URLs in the message text and "
        "read on demand via the read_file_contents tool. Capped at 10 IDs; "
        "the multimodal layer further caps actual image inlining per turn.",
    )


class CriticVerdictView(BaseModel):
    """Public view of a single critic verdict for the chat response."""

    task_id: str
    decision: str
    reason: str = ""


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    tool_calls: list[dict[str, Any]] | None = None
    workflow_id: str | None = None
    status: str | None = None
    routed_to: list[str] | None = Field(
        None,
        description="Names of specialist subagents that answered. "
        "Only set when multi-agent mode is on.",
    )
    critic_verdicts: list[CriticVerdictView] | None = None


class ChatHistoryResponse(BaseModel):
    conversation_id: str
    messages: list[ChatMessage]


# --- Conversation CRUD schemas ---


class ConversationMessageResponse(BaseModel):
    id: str
    role: str
    content: str | None = None
    tool_calls: list | dict | None = None
    tool_call_id: str | None = None
    token_usage: dict | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: str
    clerk_user_id: str
    org_id: str
    title: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    messages: list[ConversationMessageResponse] = []

    model_config = {"from_attributes": True}


class ConversationListItem(BaseModel):
    id: str
    title: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ConversationRenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
