"""LLM agent service with agentic tool execution loop.

The agent calls OpenAI, and when the LLM decides to use a tool,
we execute it against the real database and feed the result back
so the LLM can generate a final answer grounded in real data.

Conversations are persisted to PostgreSQL for history/multi-tenancy.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any, AsyncGenerator

from openai import AsyncOpenAI, AuthenticationError, APIConnectionError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from resonantia.config import get_settings
from resonantia.db.session import async_session_factory
from resonantia.models.conversation import Conversation, ConversationMessage
from resonantia.services.guardrails import GUARDRAIL_SYSTEM_PROMPT, check_guardrails
from resonantia.services.tool_executor import execute_tool
from resonantia.services.tracing import trace_llm_call

SYSTEM_PROMPT = GUARDRAIL_SYSTEM_PROMPT

MAX_TOOL_ROUNDS = 5  # prevent infinite loops


async def _load_tools() -> list[dict[str, Any]]:
    """Load tool schemas from Redis, convert to OpenAI function format."""
    try:
        from resonantia.services.tool_registry import get_tools_as_anthropic

        anthropic_tools = await get_tools_as_anthropic()
        if anthropic_tools:
            return [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["input_schema"],
                    },
                }
                for t in anthropic_tools
            ]
    except Exception:
        pass
    return []


def _get_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.openai_api_key)


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
            if conv:
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
) -> dict[str, Any]:
    """Send a user message and return the assistant's response.

    Implements a full agentic loop: if the LLM calls tools, we execute
    them and feed results back until we get a text response.
    """
    user_id = clerk_user_id or "anonymous"
    org = org_id or "org_default"

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

    user_content = message
    if context:
        user_content = f"[Context: {json.dumps(context)}]\n\n{message}"

    history.append({"role": "user", "content": user_content})

    # Persist user message
    await _persist_message(conv_uuid, "user", content=user_content)

    # Auto-generate title from first message
    if len(history) == 1:
        await _update_conversation_title(conv_uuid, message)

    settings = get_settings()

    if not settings.openai_api_key:
        no_key_msg = (
            "I'm Resonantia Lab Assistant. The OpenAI API key is not configured yet. "
            "You can still use all lab tools directly via the sidebar tabs.\n\n"
            "To enable AI chat, set `OPENAI_API_KEY` in your environment."
        )
        history.append({"role": "assistant", "content": no_key_msg})
        await _persist_message(conv_uuid, "assistant", content=no_key_msg)
        return {"message": no_key_msg, "conversation_id": cid, "tool_calls": None}

    client = _get_client()
    tools = await _load_tools()
    all_tool_calls: list[dict[str, Any]] = []

    start_time = time.monotonic()

    # --- Agentic loop: call LLM -> execute tools -> repeat until text response ---
    for round_num in range(MAX_TOOL_ROUNDS):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

        try:
            kwargs: dict[str, Any] = {"model": settings.llm_model, "max_tokens": 4096, "messages": messages}
            if tools:
                kwargs["tools"] = tools
            response = await client.chat.completions.create(**kwargs)
        except AuthenticationError:
            history.pop()
            return {"message": "Invalid OpenAI API key.", "conversation_id": cid, "tool_calls": None}
        except APIConnectionError:
            history.pop()
            return {"message": "Could not connect to OpenAI API.", "conversation_id": cid, "tool_calls": None}

        choice = response.choices[0]

        # If the LLM finished (no tool calls), return the text
        if choice.finish_reason != "tool_calls" or not choice.message.tool_calls:
            assistant_text = choice.message.content or ""
            history.append({"role": "assistant", "content": assistant_text})

            latency_ms = (time.monotonic() - start_time) * 1000
            token_usage = None
            if response.usage:
                token_usage = {"input": response.usage.prompt_tokens, "output": response.usage.completion_tokens}

            # Persist assistant message
            await _persist_message(conv_uuid, "assistant", content=assistant_text, token_usage=token_usage)

            trace_llm_call(
                user_message=message, system_prompt=SYSTEM_PROMPT,
                response=assistant_text, model=settings.llm_model,
                conversation_id=cid,
                tools_used=[tc["name"] for tc in all_tool_calls],
                guardrail_result=guardrail_result,
                latency_ms=latency_ms, token_usage=token_usage,
            )

            return {"message": assistant_text, "conversation_id": cid, "tool_calls": all_tool_calls or None}

        # --- The LLM wants to call tools --- execute them ---
        tool_calls_data = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in choice.message.tool_calls
        ]
        history.append({
            "role": "assistant",
            "content": choice.message.content,
            "tool_calls": tool_calls_data,
        })

        # Persist assistant message with tool calls
        await _persist_message(
            conv_uuid, "assistant",
            content=choice.message.content,
            tool_calls=tool_calls_data,
        )

        # Execute each tool and add results
        for tc in choice.message.tool_calls:
            tool_name = tc.function.name
            tool_input = json.loads(tc.function.arguments)
            all_tool_calls.append({"id": tc.id, "name": tool_name, "input": tool_input})

            # Execute the tool against the real database, scoped to org_id
            tool_result = await execute_tool(tool_name, tool_input, org_id=org)

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
) -> AsyncGenerator[str, None]:
    """Stream the assistant response. Falls back to non-streaming for tool calls."""
    result = await chat(
        message, conversation_id, context,
        clerk_user_id=clerk_user_id, org_id=org_id,
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
