"""LLM agent service with agentic tool execution loop.

The agent calls OpenAI, and when the LLM decides to use a tool,
we execute it against the real database and feed the result back
so the LLM can generate a final answer grounded in real data.
"""

from __future__ import annotations

import json
import time
import uuid
from collections import defaultdict
from typing import Any, AsyncGenerator

from openai import AsyncOpenAI, AuthenticationError, APIConnectionError

from resonantia.config import get_settings
from resonantia.services.guardrails import GUARDRAIL_SYSTEM_PROMPT, check_guardrails
from resonantia.services.tool_executor import execute_tool
from resonantia.services.tracing import trace_llm_call

_conversations: dict[str, list[dict[str, Any]]] = defaultdict(list)

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


async def chat(
    message: str,
    conversation_id: str | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Send a user message and return the assistant's response.

    Implements a full agentic loop: if the LLM calls tools, we execute
    them and feed results back until we get a text response.
    """
    cid = conversation_id or uuid.uuid4().hex
    history = _conversations[cid]

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

    settings = get_settings()

    if not settings.openai_api_key:
        no_key_msg = (
            "I'm Resonantia Lab Assistant. The OpenAI API key is not configured yet. "
            "You can still use all lab tools directly via the sidebar tabs.\n\n"
            "To enable AI chat, set `OPENAI_API_KEY` in your environment."
        )
        history.append({"role": "assistant", "content": no_key_msg})
        return {"message": no_key_msg, "conversation_id": cid, "tool_calls": None}

    client = _get_client()
    tools = await _load_tools()
    all_tool_calls: list[dict[str, Any]] = []

    start_time = time.monotonic()

    # --- Agentic loop: call LLM → execute tools → repeat until text response ---
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

            trace_llm_call(
                user_message=message, system_prompt=SYSTEM_PROMPT,
                response=assistant_text, model=settings.llm_model,
                conversation_id=cid,
                tools_used=[tc["name"] for tc in all_tool_calls],
                guardrail_result=guardrail_result,
                latency_ms=latency_ms, token_usage=token_usage,
            )

            return {"message": assistant_text, "conversation_id": cid, "tool_calls": all_tool_calls or None}

        # --- The LLM wants to call tools — execute them ---
        # Add the assistant message with tool_calls to history
        history.append({
            "role": "assistant",
            "content": choice.message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in choice.message.tool_calls
            ],
        })

        # Execute each tool and add results
        for tc in choice.message.tool_calls:
            tool_name = tc.function.name
            tool_input = json.loads(tc.function.arguments)
            all_tool_calls.append({"id": tc.id, "name": tool_name, "input": tool_input})

            # Execute the tool against the real database
            tool_result = await execute_tool(tool_name, tool_input)

            # Add tool result to history for the next LLM round
            history.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": tool_result,
            })

    # Max rounds reached — return what we have
    return {
        "message": "I've gathered the data but reached the processing limit. Please try a more specific query.",
        "conversation_id": cid,
        "tool_calls": all_tool_calls,
    }


async def chat_stream(
    message: str,
    conversation_id: str | None = None,
    context: dict[str, Any] | None = None,
) -> AsyncGenerator[str, None]:
    """Stream the assistant response. Falls back to non-streaming for tool calls."""
    # For tool-calling conversations, use the synchronous loop and stream the final result
    result = await chat(message, conversation_id, context)
    text = result.get("message", "")

    # Stream character by character for a natural feel
    chunk_size = 8
    for i in range(0, len(text), chunk_size):
        yield f"data: {json.dumps({'text': text[i:i+chunk_size]})}\n\n"

    yield f"data: {json.dumps({'done': True, 'conversation_id': result.get('conversation_id')})}\n\n"


def get_history(conversation_id: str) -> list[dict[str, Any]]:
    """Return message history for a conversation."""
    raw = _conversations.get(conversation_id, [])
    result = []
    for msg in raw:
        role = msg.get("role", "")
        if role == "tool":
            continue  # skip tool results from display history
        content = msg.get("content", "")
        if isinstance(content, str) and content:
            result.append({"role": role, "content": content})
        elif isinstance(content, list):
            text_parts = [b.get("text", "") if isinstance(b, dict) else str(b) for b in content]
            joined = " ".join(text_parts).strip()
            if joined:
                result.append({"role": role, "content": joined})
    return result
