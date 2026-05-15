"""Agent chat endpoints (Anthropic Claude).

Supports two execution modes:
- **Temporal** (default): starts an ``AgentToolCallWorkflow`` for durable execution.
- **Direct** (fallback): calls the LLM inline when Temporal is unreachable.

Includes conversation CRUD for persistent chat history.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from resonantia.db.session import get_db
from resonantia.dependencies import get_request_context
from resonantia.models.conversation import Conversation, ConversationMessage
from resonantia.models.request_context import RequestContext
from resonantia.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    ConversationListItem,
    ConversationRenameRequest,
    ConversationResponse,
    ConversationMessageResponse,
)
from resonantia.services import agent, agent_router

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
async def send_message(
    request: Request,
    body: ChatRequest,
    ctx: RequestContext = Depends(get_request_context),
) -> ChatResponse:
    """Send a user message.

    Attempts to start an ``AgentToolCallWorkflow`` via Temporal.  If the
    Temporal server is unavailable the request falls back to the direct
    LLM call so development and demos work without infrastructure.
    """
    conversation_id = body.conversation_id or uuid.uuid4().hex

    # --- Try Temporal first ---
    try:
        from resonantia.services.temporal_client import start_agent_workflow

        handle = await start_agent_workflow(
            message=body.message,
            conversation_id=conversation_id,
            user_id=ctx.user_id,
            org_id=ctx.org_id,
            context=body.context,
            roles=ctx.roles,
            permissions=ctx.permissions,
        )

        # Wait for the workflow to complete with a 30-second timeout
        result = await asyncio.wait_for(handle.result(), timeout=30.0)

        return ChatResponse(
            message=result.response,
            conversation_id=result.conversation_id,
            tool_calls=None,
        )

    except asyncio.TimeoutError:
        # Workflow is still running — tell user to wait
        logger.warning("Temporal workflow timed out after 30s for conversation %s", conversation_id)
        return ChatResponse(
            message="Processing is taking longer than expected. Check back shortly.",
            conversation_id=conversation_id,
            tool_calls=None,
        )

    except (RPCError, ServiceError) as exc:
        # Temporal is actually unavailable — fall back to direct mode
        logger.warning(
            "Temporal unavailable (%s: %s), falling back to direct mode",
            type(exc).__name__, exc,
        )

    except ValueError as exc:
        # Cross-org conversation access or similar validation error
        logger.warning("Validation error in Temporal workflow: %s", exc)
        raise HTTPException(status_code=403, detail=str(exc))

    # All other exceptions propagate as 500 — do NOT catch and hide

    # --- Direct fallback (multi-agent orchestrator if flag is on) ---
    try:
        result = await agent_router.chat(
            message=body.message,
            conversation_id=conversation_id,
            context=body.context,
            request_context=ctx,
            attachments=body.attachments,
            request_id=getattr(request.state, "request_id", None),
        )
    except ValueError as exc:
        if "not accessible" in str(exc):
            raise HTTPException(status_code=403, detail="Conversation not accessible")
        raise
    return ChatResponse(
        message=result["message"],
        conversation_id=result["conversation_id"],
        tool_calls=result.get("tool_calls"),
        routed_to=result.get("routed_to"),
        critic_verdicts=result.get("critic_verdicts"),
    )


# ---------------------------------------------------------------------------
# POST /message/stream  — streaming remains direct (SSE is not Temporal-native)
# ---------------------------------------------------------------------------

@router.post("/message/stream")
async def stream_message(
    request: Request,
    body: ChatRequest,
    ctx: RequestContext = Depends(get_request_context),
) -> EventSourceResponse:
    return EventSourceResponse(
        agent.chat_stream(
            message=body.message,
            conversation_id=body.conversation_id,
            context=body.context,
            request_context=ctx,
            request_id=getattr(request.state, "request_id", None),
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
# GET /history/{conversation_id}  — legacy endpoint
# ---------------------------------------------------------------------------

@router.get("/history/{conversation_id}", response_model=ChatHistoryResponse)
async def get_history(conversation_id: str) -> ChatHistoryResponse:
    messages = agent.get_history(conversation_id)
    return ChatHistoryResponse(
        conversation_id=conversation_id,
        messages=messages,
    )


# ---------------------------------------------------------------------------
# Conversation CRUD endpoints
# ---------------------------------------------------------------------------

@router.get("/conversations", response_model=list[ConversationListItem])
async def list_conversations(
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> list[ConversationListItem]:
    """List all conversations for a user in an org."""
    stmt = (
        select(Conversation)
        .where(Conversation.clerk_user_id == ctx.user_id, Conversation.org_id == ctx.org_id)
        .order_by(Conversation.updated_at.desc())
    )
    result = await db.execute(stmt)
    convs = result.scalars().all()
    return [
        ConversationListItem(
            id=str(c.id),
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in convs
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """Get a conversation with all its messages."""
    conv = await db.get(Conversation, conversation_id)
    if not conv or conv.org_id != ctx.org_id or conv.clerk_user_id != ctx.user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse(
        id=str(conv.id),
        clerk_user_id=conv.clerk_user_id,
        org_id=conv.org_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[
            ConversationMessageResponse(
                id=str(m.id),
                role=m.role,
                content=m.content,
                tool_calls=m.tool_calls,
                tool_call_id=m.tool_call_id,
                token_usage=m.token_usage,
                created_at=m.created_at,
            )
            for m in conv.messages
        ],
    )


@router.patch("/conversations/{conversation_id}", response_model=ConversationListItem)
async def rename_conversation(
    conversation_id: uuid.UUID,
    body: ConversationRenameRequest,
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> ConversationListItem:
    """Rename a conversation."""
    conv = await db.get(Conversation, conversation_id)
    if not conv or conv.org_id != ctx.org_id or conv.clerk_user_id != ctx.user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv.title = body.title
    await db.flush()
    await db.refresh(conv)
    return ConversationListItem(
        id=str(conv.id),
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
    )


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: uuid.UUID,
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a conversation and all its messages."""
    conv = await db.get(Conversation, conversation_id)
    if not conv or conv.org_id != ctx.org_id or conv.clerk_user_id != ctx.user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conv)


# ---------------------------------------------------------------------------
# Approval gates
# ---------------------------------------------------------------------------

@router.post("/approve/{token}")
async def approve_tool_call(
    token: str,
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Approve a pending tool call and execute it."""
    from resonantia.services.approval import (
        ApprovalStatus,
        claim_for_approval,
        get_pending_record,
        is_expired,
        mark_expired,
        pending_from_record,
    )
    from resonantia.services.tool_executor import execute_tool

    record = await get_pending_record(db, token, for_update=True)
    if record is None:
        raise HTTPException(status_code=410, detail="Approval expired or not found")
    if record.org_id != ctx.org_id or not ctx.can_approve():
        raise HTTPException(status_code=403, detail="Not authorized to approve this action")
    if is_expired(record):
        await mark_expired(db, record)
        raise HTTPException(status_code=410, detail="Approval expired or not found")
    if record.status != ApprovalStatus.PENDING.value:
        raise HTTPException(status_code=409, detail="Approval has already been decided")

    await claim_for_approval(db, record, decided_by=ctx.user_id)
    pending = pending_from_record(record)
    result = await execute_tool(
        pending.tool_name,
        pending.tool_args,
        request_context=ctx,
        skip_gate=True,
    )
    try:
        record.result = json.loads(result)
    except json.JSONDecodeError:
        record.result = {"raw": result}
    await db.flush()
    return {"status": "approved", "tool_name": pending.tool_name, "result": result}


@router.post("/reject/{token}")
async def reject_tool_call(
    token: str,
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Reject a pending tool call."""
    from resonantia.services.approval import (
        ApprovalStatus,
        get_pending_record,
        is_expired,
        mark_expired,
        reject_pending,
    )

    record = await get_pending_record(db, token, for_update=True)
    if record is None:
        raise HTTPException(status_code=410, detail="Approval expired or not found")
    if record.org_id != ctx.org_id or not ctx.can_approve():
        raise HTTPException(status_code=403, detail="Not authorized to reject this action")
    if is_expired(record):
        await mark_expired(db, record)
        raise HTTPException(status_code=410, detail="Approval expired or not found")
    if record.status != ApprovalStatus.PENDING.value:
        raise HTTPException(status_code=409, detail="Approval has already been decided")
    await reject_pending(db, record, decided_by=ctx.user_id)
    return {"status": "rejected"}


# ---------------------------------------------------------------------------
# Temporal error imports (deferred to avoid import errors when Temporal
# SDK is not installed in lightweight test environments)
# ---------------------------------------------------------------------------

try:
    from grpc import RpcError as RPCError  # type: ignore[import-untyped]
    from temporalio.service import ServiceError
except ImportError:
    # Define fallback classes that will never match if Temporal is not
    # installed — the except clause in send_message will simply not
    # trigger, and the error will propagate as a generic exception.
    class RPCError(Exception):  # type: ignore[no-redef]
        pass

    class ServiceError(Exception):  # type: ignore[no-redef]
        pass
