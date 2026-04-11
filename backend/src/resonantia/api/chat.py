"""Agent chat endpoints (Anthropic Claude).

Supports two execution modes:
- **Temporal** (default): starts an ``AgentRunWorkflow`` for durable execution.
- **Direct** (fallback): calls the LLM inline when Temporal is unreachable.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from resonantia.schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse
from resonantia.services import agent

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas for Temporal-aware endpoints
# ---------------------------------------------------------------------------

class WorkflowStartResponse(BaseModel):
    workflow_id: str
    conversation_id: str
    status: str = "RUNNING"


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    status: str
    start_time: str | None = None
    close_time: str | None = None
    result: Any = None


# ---------------------------------------------------------------------------
# POST /message  — starts a Temporal workflow (with direct fallback)
# ---------------------------------------------------------------------------

@router.post("/message", response_model=ChatResponse)
async def send_message(body: ChatRequest) -> ChatResponse:
    """Send a user message.

    Attempts to start an ``AgentRunWorkflow`` via Temporal.  If the Temporal
    server is unavailable the request falls back to the direct LLM call so
    development and demos work without infrastructure.
    """
    conversation_id = body.conversation_id or uuid.uuid4().hex

    # --- Try Temporal first ---
    try:
        from resonantia.services.temporal_client import start_agent_workflow

        handle = await start_agent_workflow(
            message=body.message,
            conversation_id=conversation_id,
            user_id="anonymous",  # replaced by auth middleware in production
            context=body.context,
        )

        # Wait for the workflow to complete (bounded timeout for HTTP request)
        result = await handle.result()

        return ChatResponse(
            message=result.response,
            conversation_id=result.conversation_id,
            tool_calls=None,
        )

    except Exception as exc:
        logger.warning(
            "Temporal unavailable (%s), falling back to direct mode", exc
        )

    # --- Direct fallback ---
    result = await agent.chat(
        message=body.message,
        conversation_id=conversation_id,
        context=body.context,
    )
    return ChatResponse(**result)


# ---------------------------------------------------------------------------
# POST /message/stream  — streaming remains direct (SSE is not Temporal-native)
# ---------------------------------------------------------------------------

@router.post("/message/stream")
async def stream_message(body: ChatRequest) -> EventSourceResponse:
    return EventSourceResponse(
        agent.chat_stream(
            message=body.message,
            conversation_id=body.conversation_id,
            context=body.context,
        )
    )


# ---------------------------------------------------------------------------
# GET /workflow/{workflow_id}/status
# ---------------------------------------------------------------------------

@router.get("/workflow/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str) -> WorkflowStatusResponse:
    """Query the status of a Temporal workflow by ID."""
    from resonantia.services.temporal_client import get_workflow_status as _get_status

    info = await _get_status(workflow_id)
    return WorkflowStatusResponse(**info)


# ---------------------------------------------------------------------------
# GET /history/{conversation_id}
# ---------------------------------------------------------------------------

@router.get("/history/{conversation_id}", response_model=ChatHistoryResponse)
async def get_history(conversation_id: str) -> ChatHistoryResponse:
    messages = agent.get_history(conversation_id)
    return ChatHistoryResponse(
        conversation_id=conversation_id,
        messages=messages,
    )
