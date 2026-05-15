"""LLM agent service with agentic tool execution loop.

The agent calls the configured LLM provider, and when the model decides
to use a tool, we execute it against the real database and feed the result
back so the model can generate a final answer grounded in real data.

Conversations are persisted to PostgreSQL for history/multi-tenancy.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any, AsyncGenerator

from resonantia.config import get_settings
from resonantia.db.session import async_session_factory
from resonantia.models.conversation import Conversation, ConversationMessage
from resonantia.models.request_context import RequestContext
from resonantia.middleware import log_stage_latency
from resonantia.services.guardrails import GUARDRAIL_SYSTEM_PROMPT, check_guardrails
from resonantia.services.llm import LLMProvider, ToolCall, get_provider
from resonantia.services.multimodal import build_user_content
from resonantia.services.tool_executor import execute_tool
from resonantia.services.tracing import trace_llm_call

SYSTEM_PROMPT = GUARDRAIL_SYSTEM_PROMPT

MAX_TOOL_ROUNDS = 5  # prevent infinite loops


async def _load_tools() -> list[dict[str, Any]]:
    """Load tool schemas from Redis in provider-agnostic (Anthropic) format."""
    try:
        from resonantia.services.tool_registry import get_tools_as_anthropic

        anthropic_tools = await get_tools_as_anthropic()
        if anthropic_tools:
            return anthropic_tools
    except Exception:
        pass
    return []


def _get_provider() -> LLMProvider:
    return get_provider()


def _is_valid_uuid(val: str | None) -> bool:
    """Check if a string is a valid UUID."""
    if not val:
        return False
    try:
        uuid.UUID(val)
        return True
    except (ValueError, AttributeError):
        return False


async def _get_or_create_conversation(
    conversation_id: str | None,
    clerk_user_id: str,
    org_id: str,
) -> tuple[uuid.UUID, list[dict[str, Any]]]:
    """Load or create a conversation and return (uuid, history_as_openai_messages)."""
    async with async_session_factory() as session:
        # Try loading existing conversation
        if _is_valid_uuid(conversation_id):
            conv = await session.get(Conversation, uuid.UUID(conversation_id))
            if conv and conv.org_id == org_id:
                # Build history from persisted messages
                history: list[dict[str, Any]] = []
                for msg in conv.messages:
                    entry: dict[str, Any] = {"role": msg.role}
                    if msg.content is not None:
                        entry["content"] = msg.content
                    if msg.tool_calls:
                        entry["tool_calls"] = msg.tool_calls
                    if msg.tool_call_id:
                        entry["tool_call_id"] = msg.tool_call_id
                    history.append(entry)
                return conv.id, history
            if conv and conv.org_id != org_id:
                raise ValueError("Conversation not accessible")

        # Create new conversation
        conv = Conversation(
            clerk_user_id=clerk_user_id,
            org_id=org_id,
            title="New conversation",
        )
        session.add(conv)
        await session.commit()
        await session.refresh(conv)
        return conv.id, []


async def _persist_message(
    conversation_id: uuid.UUID,
    role: str,
    content: str | None = None,
    tool_calls: dict | None = None,
    tool_call_id: str | None = None,
    token_usage: dict | None = None,
) -> None:
    """Persist a single message to the database."""
    async with async_session_factory() as session:
        msg = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            token_usage=token_usage,
        )
        session.add(msg)
        await session.commit()


async def _update_conversation_title(conversation_id: uuid.UUID, first_message: str) -> None:
    """Auto-generate title from first user message (first 50 chars)."""
    title = first_message[:50].strip()
    if len(first_message) > 50:
        title += "..."
    async with async_session_factory() as session:
        conv = await session.get(Conversation, conversation_id)
        if conv and conv.title == "New conversation":
            conv.title = title
            await session.commit()


async def chat(
    message: str,
    conversation_id: str | None = None,
    context: dict[str, Any] | None = None,
    clerk_user_id: str | None = None,
    org_id: str | None = None,
    attachments: list[str] | None = None,
    source: str = "text",
    request_id: str | None = None,
    request_context: RequestContext | None = None,
) -> dict[str, Any]:
    """Send a user message and return the assistant's response.

    Implements a full agentic loop: if the LLM calls tools, we execute
    them and feed results back until we get a text response.
    """
    user_id = request_context.user_id if request_context else (clerk_user_id or "anonymous")
    org = request_context.org_id if request_context else (org_id or "org_default")
    request_id = request_id or (request_context.request_id if request_context else None)

    conv_uuid, history = await _get_or_create_conversation(conversation_id, user_id, org)
    cid = str(conv_uuid)

    # --- Guardrails ---
    guardrail_result = check_guardrails(message)
    if not guardrail_result[0]:
        trace_llm_call(
            user_message=message, system_prompt=SYSTEM_PROMPT,
            response=guardrail_result[1], model=get_settings().llm_model,
            conversation_id=cid, guardrail_result=guardrail_result,
        )
        return {"message": guardrail_result[1], "conversation_id": cid, "tool_calls": None}

    text_content = message
    if context:
        text_content = f"[Context: {json.dumps(context)}]\n\n{message}"

    # Resolve image attachments into multimodal content blocks. Returns
    # a plain string when there are no images so non-multimodal turns
    # are byte-identical to the pre-multimodal code path. The org_id
    # scope here is the security boundary: only files owned by the
    # caller's org are eligible to be encoded.
    user_content = build_user_content(
        text_content, attachments=attachments, org_id=org,
    )

    history.append({"role": "user", "content": user_content})

    # Persist the text representation; binary image bytes are NOT
    # written to the conversation row — the file registry is the source
    # of truth for image bytes. Tracing below also receives the text-only
    # form so image bytes don't egress to Langfuse.
    await _persist_message(conv_uuid, "user", content=text_content)

    # Auto-generate title from first message
    if len(history) == 1:
        await _update_conversation_title(conv_uuid, message)

    settings = get_settings()

    # Check for API key based on the configured provider.
    provider_name = settings.default_provider
    has_key = (
        (provider_name == "openai" and settings.openai_api_key)
        or (provider_name == "anthropic" and settings.anthropic_api_key)
        or settings.openai_api_key  # fallback check
    )
    if not has_key:
        no_key_msg = (
            "I'm Resonantia Lab Assistant. The LLM API key is not configured yet. "
            "You can still use all lab tools directly via the sidebar tabs.\n\n"
            f"To enable AI chat, set the API key for the '{provider_name}' provider."
        )
        history.append({"role": "assistant", "content": no_key_msg})
        await _persist_message(conv_uuid, "assistant", content=no_key_msg)
        return {"message": no_key_msg, "conversation_id": cid, "tool_calls": None}

    provider = _get_provider()
    tools = await _load_tools()
    all_tool_calls: list[dict[str, Any]] = []

    start_time = time.monotonic()

    # --- Agentic loop: call LLM -> execute tools -> repeat until text response ---
    for round_num in range(MAX_TOOL_ROUNDS):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

        try:
            llm_start = time.monotonic()
            llm_response = await provider.completion(
                messages, tools=tools if tools else None, max_tokens=4096,
            )
            log_stage_latency("llm", (time.monotonic() - llm_start) * 1000)
        except Exception as exc:
            exc_name = exc.__class__.__name__
            if "auth" in exc_name.lower():
                history.pop()
                return {"message": "Invalid API key.", "conversation_id": cid, "tool_calls": None}
            history.pop()
            return {"message": f"Could not connect to LLM provider ({exc_name}).", "conversation_id": cid, "tool_calls": None}

        # If no tool calls, return the text
        if not llm_response.tool_calls:
            assistant_text = llm_response.content or ""
            history.append({"role": "assistant", "content": assistant_text})

            latency_ms = (time.monotonic() - start_time) * 1000
            token_usage = None
            if llm_response.input_tokens or llm_response.output_tokens:
                token_usage = {"input": llm_response.input_tokens, "output": llm_response.output_tokens}

            # Persist assistant message
            await _persist_message(conv_uuid, "assistant", content=assistant_text, token_usage=token_usage)

            trace_llm_call(
                user_message=message, system_prompt=SYSTEM_PROMPT,
                response=assistant_text, model=llm_response.model,
                conversation_id=cid,
                tools_used=[tc["name"] for tc in all_tool_calls],
                guardrail_result=guardrail_result,
                latency_ms=latency_ms, token_usage=token_usage,
                metadata={"provider": llm_response.provider},
            )

            return {"message": assistant_text, "conversation_id": cid, "tool_calls": all_tool_calls or None}

        # --- The LLM wants to call tools --- execute them ---
        tool_calls_data = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
            }
            for tc in llm_response.tool_calls
        ]
        history.append({
            "role": "assistant",
            "content": llm_response.content,
            "tool_calls": tool_calls_data,
        })

        # Persist assistant message with tool calls
        await _persist_message(
            conv_uuid, "assistant",
            content=llm_response.content,
            tool_calls=tool_calls_data,
        )

        # Execute each tool and add results
        for tc in llm_response.tool_calls:
            tool_name = tc.name
            tool_input = tc.arguments
            all_tool_calls.append({"id": tc.id, "name": tool_name, "input": tool_input})

            # Execute the tool against the real database, scoped to org_id
            tool_start = time.monotonic()
            tool_result = await execute_tool(
                tool_name,
                tool_input,
                org_id=org,
                user_id=user_id,
                source=source,
                request_id=request_id,
                request_context=request_context,
            )
            log_stage_latency("tool", (time.monotonic() - tool_start) * 1000, tool_name=tool_name)

            # Add tool result to history for the next LLM round
            history.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": tool_result,
            })

            # Persist tool result message
            await _persist_message(
                conv_uuid, "tool",
                content=tool_result,
                tool_call_id=tc.id,
            )

    # Max rounds reached
    return {
        "message": "I've gathered the data but reached the processing limit. Please try a more specific query.",
        "conversation_id": cid,
        "tool_calls": all_tool_calls,
    }


async def chat_stream(
    message: str,
    conversation_id: str | None = None,
    context: dict[str, Any] | None = None,
    clerk_user_id: str | None = None,
    org_id: str | None = None,
    request_id: str | None = None,
    request_context: RequestContext | None = None,
) -> AsyncGenerator[str, None]:
    """Stream the assistant response. Falls back to non-streaming for tool calls."""
    result = await chat(
        message, conversation_id, context,
        clerk_user_id=clerk_user_id, org_id=org_id, request_id=request_id,
        request_context=request_context,
    )
    text = result.get("message", "")

    chunk_size = 8
    for i in range(0, len(text), chunk_size):
        yield f"data: {json.dumps({'text': text[i:i+chunk_size]})}\n\n"

    yield f"data: {json.dumps({'done': True, 'conversation_id': result.get('conversation_id')})}\n\n"


def get_history(conversation_id: str) -> list[dict[str, Any]]:
    """Return message history for a conversation.

    NOTE: This is now a legacy sync helper. Prefer the async DB-backed
    endpoints at /api/v1/chat/conversations/{id}.
    """
    return []
