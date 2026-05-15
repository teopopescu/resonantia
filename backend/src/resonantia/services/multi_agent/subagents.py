"""Specialist subagents.

Each specialist runs the same agentic-loop primitive as the legacy
``services/agent.py`` but with:
- a constitutional system prompt (see ``prompts.py``),
- a scoped tool subset (filtered by tool category from the registry),
- a task-shaped objective (a ``TaskAssignment``) rather than free-form chat.

This file deliberately re-implements the loop instead of importing from
``agent.py`` so the legacy single-agent code path stays untouched and we
can iterate on the multi-agent loop without regressions.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from resonantia.config import get_settings
from resonantia.models.request_context import RequestContext
from resonantia.services.llm import LLMProvider, get_provider
from resonantia.services.multi_agent.messages import (
    AgentName,
    TaskAssignment,
    TaskResult,
)
from resonantia.services.multi_agent.prompts import SPECIALIST_PROMPTS
from resonantia.services.tool_executor import execute_tool
from resonantia.services.tool_registry import get_tools_as_anthropic
from resonantia.services.tracing import trace_specialist_call

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 5


@dataclass(frozen=True)
class SpecialistConfig:
    name: AgentName
    tool_categories: tuple[str, ...]
    """Tool categories from the registry this specialist can use.
    Empty tuple means all categories (used by `general`)."""


SPECIALISTS: dict[AgentName, SpecialistConfig] = {
    "plate_designer": SpecialistConfig(
        name="plate_designer",
        tool_categories=("plate_mapping", "microscopy"),
    ),
    "data_analyst": SpecialistConfig(
        name="data_analyst",
        tool_categories=("data_processing",),
    ),
    "eln_scribe": SpecialistConfig(
        name="eln_scribe",
        tool_categories=("eln",),
    ),
    "protocol_agent": SpecialistConfig(
        name="protocol_agent",
        tool_categories=("protocol",),
    ),
    "sample_agent": SpecialistConfig(
        name="sample_agent",
        tool_categories=("sample_management",),
    ),
    "general": SpecialistConfig(
        name="general",
        tool_categories=(),
    ),
}


async def _scoped_tools(categories: tuple[str, ...]) -> list[dict[str, Any]]:
    """Return tools filtered by category, in provider-agnostic format.

    An empty ``categories`` tuple returns all tools.
    The provider adapter handles format conversion.
    """
    if not categories:
        return await get_tools_as_anthropic()

    all_tools: list[dict[str, Any]] = []
    for cat in categories:
        all_tools.extend(await get_tools_as_anthropic(category=cat))
    # de-dupe by name in case of overlap
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for t in all_tools:
        if t["name"] in seen:
            continue
        seen.add(t["name"])
        result.append(t)
    return result


def _format_assignment(task: TaskAssignment) -> str:
    """Render a TaskAssignment as the user-turn message for the specialist."""
    parts = [f"OBJECTIVE: {task.objective}"]
    if task.inputs:
        parts.append(f"INPUTS: {json.dumps(task.inputs)}")
    if task.constraints:
        parts.append("CONSTRAINTS:\n- " + "\n- ".join(task.constraints))
    return "\n\n".join(parts)


async def run_specialist(
    task: TaskAssignment,
    org_id: str,
    *,
    provider: LLMProvider | None = None,
    conversation_id: str | None = None,
    request_context: RequestContext | None = None,
) -> TaskResult:
    """Run a single specialist subagent against a TaskAssignment.

    Returns a TaskResult -- never raises for tool errors, those become
    `status="failed"` with a rationale.
    """
    config = SPECIALISTS[task.assigned_agent]

    settings = get_settings()
    provider = provider or get_provider()
    tools = await _scoped_tools(config.tool_categories)
    system_prompt = SPECIALIST_PROMPTS[task.assigned_agent]

    history: list[dict[str, Any]] = [
        {"role": "user", "content": _format_assignment(task)},
    ]
    tool_calls_seen: list[dict[str, Any]] = []

    start_time = time.monotonic()

    for _ in range(MAX_TOOL_ROUNDS):
        messages = [{"role": "system", "content": system_prompt}, *history]

        try:
            llm_response = await provider.completion(
                messages,
                tools=tools if tools else None,
                model=settings.specialist_model,
                max_tokens=2048,
            )
        except Exception as exc:
            exc_name = exc.__class__.__name__
            if "auth" in exc_name.lower():
                return TaskResult(
                    task_id=task.task_id,
                    assigned_agent=task.assigned_agent,
                    status="failed",
                    output="Invalid API key.",
                    rationale="auth_error",
                )
            if "rate" in exc_name.lower():
                return TaskResult(
                    task_id=task.task_id,
                    assigned_agent=task.assigned_agent,
                    status="failed",
                    output="LLM provider rate limit exceeded -- try again shortly.",
                    rationale="rate_limited",
                )
            return TaskResult(
                task_id=task.task_id,
                assigned_agent=task.assigned_agent,
                status="failed",
                output=f"Could not reach the LLM provider ({exc_name}).",
                rationale="api_connection_error",
            )

        if not llm_response.tool_calls:
            text = llm_response.content or ""
            latency_ms = (time.monotonic() - start_time) * 1000
            result = TaskResult(
                task_id=task.task_id,
                assigned_agent=task.assigned_agent,
                status="completed",
                output=text,
                rationale="",
                tool_calls=tool_calls_seen,
                confidence=0.8 if tool_calls_seen else 0.6,
            )
            # Langfuse span for the specialist call
            trace_specialist_call(
                agent_role=task.assigned_agent,
                objective=task.objective,
                response=text,
                model=settings.specialist_model,
                org_id=org_id,
                conversation_id=conversation_id,
                tool_calls=[tc["name"] for tc in tool_calls_seen],
                latency_ms=latency_ms,
                token_usage={
                    "input_tokens": llm_response.input_tokens,
                    "output_tokens": llm_response.output_tokens,
                },
            )
            return result

        # tool_calls round
        tool_calls_for_history = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.name,
                    "arguments": json.dumps(tc.arguments),
                },
            }
            for tc in llm_response.tool_calls
        ]
        history.append(
            {
                "role": "assistant",
                "content": llm_response.content,
                "tool_calls": tool_calls_for_history,
            }
        )

        for tc in llm_response.tool_calls:
            tool_input = tc.arguments
            tool_calls_seen.append(
                {"id": tc.id, "name": tc.name, "input": tool_input}
            )
            tool_result = await execute_tool(
                tc.name,
                tool_input,
                org_id=org_id,
                source="multi_agent",
                request_context=request_context,
            )
            history.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": tool_result,
                }
            )

    latency_ms = (time.monotonic() - start_time) * 1000
    failed_result = TaskResult(
        task_id=task.task_id,
        assigned_agent=task.assigned_agent,
        status="failed",
        output="Reached max tool rounds without producing a final answer.",
        rationale="max_rounds_reached",
        tool_calls=tool_calls_seen,
    )
    trace_specialist_call(
        agent_role=task.assigned_agent,
        objective=task.objective,
        response=failed_result.output,
        model=settings.specialist_model,
        org_id=org_id,
        conversation_id=conversation_id,
        tool_calls=[tc["name"] for tc in tool_calls_seen],
        latency_ms=latency_ms,
        metadata={"status": "failed", "rationale": "max_rounds_reached"},
    )
    return failed_result
