"""Agent tool-call workflow — safe agentic loop via Temporal.

Replaces the old AgentRunWorkflow that generated and executed arbitrary
Python code via subprocess.  This workflow uses only registered tool
handlers from the tool_executor module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from resonantia.workflows.activities import (
        call_llm_activity,
        execute_tool_activity,
        persist_conversation_activity,
    )


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class AgentToolCallInput:
    messages: list[dict[str, Any]]
    tools: list[dict[str, Any]]
    org_id: str
    request_context: dict[str, Any] | None = None
    conversation_id: str | None = None
    max_iterations: int = 10


@dataclass
class AgentToolCallOutput:
    response: str
    tool_calls_made: list[dict[str, Any]]
    conversation_id: str


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------

RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_attempts=3,
    maximum_interval=timedelta(seconds=30),
)


@workflow.defn
class AgentToolCallWorkflow:
    """Orchestrates the agentic tool-call loop: LLM -> tool calls -> repeat.

    Each tool execution is its own Temporal activity (individually retriable,
    timed at 30s).  The loop runs until the LLM produces a text response or
    ``max_iterations`` is reached.
    """

    @workflow.run
    async def run(self, inp: AgentToolCallInput) -> AgentToolCallOutput:
        messages = list(inp.messages)
        iterations = 0
        tool_calls_log: list[dict[str, Any]] = []
        last_response_text = ""

        while iterations < inp.max_iterations:
            # 1. Call LLM via activity
            llm_result: dict[str, Any] = await workflow.execute_activity(
                call_llm_activity,
                args=[messages, inp.tools],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RETRY_POLICY,
            )

            response_text: str = llm_result.get("content", "")
            tool_calls: list[dict[str, Any]] = llm_result.get("tool_calls", [])

            if not tool_calls:
                # Final text response — no more tool calls
                last_response_text = response_text
                break

            # Append the assistant message (with tool_calls) to history
            assistant_msg: dict[str, Any] = {"role": "assistant", "content": response_text}
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            messages.append(assistant_msg)

            # 2. Execute each tool call as its own activity
            for tc in tool_calls:
                tc_name: str = tc.get("name", "")
                tc_args: dict[str, Any] = tc.get("arguments", {})
                tc_id: str = tc.get("id", "")

                tool_result: str = await workflow.execute_activity(
                    execute_tool_activity,
                    args=[tc_name, tc_args, inp.org_id, inp.request_context],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RETRY_POLICY,
                )

                # Feed tool result back into conversation
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": tool_result,
                })

                tool_calls_log.append({
                    "name": tc_name,
                    "args": tc_args,
                    "result": tool_result,
                })

            iterations += 1

        # If we exhausted iterations without a text response, use whatever
        # the last LLM call returned.
        if not last_response_text and iterations >= inp.max_iterations:
            last_response_text = (
                "I've gathered the data but reached the processing limit. "
                "Please try a more specific query."
            )

        # 3. Persist conversation
        conversation_id = inp.conversation_id or ""
        if conversation_id:
            await workflow.execute_activity(
                persist_conversation_activity,
                args=[conversation_id, inp.org_id, messages],
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RETRY_POLICY,
            )

        return AgentToolCallOutput(
            response=last_response_text,
            tool_calls_made=tool_calls_log,
            conversation_id=conversation_id,
        )
