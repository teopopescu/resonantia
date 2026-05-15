"""Orchestrator — entry point for the multi-agent chat path.

Flow:
1. Load conversation history (shares persistence with the legacy agent).
2. Run guardrails on the user message.
3. Ask an LLM to decompose the message into ``TaskAssignment`` objects.
4. Run each assignment via ``run_specialist`` (parallel when safe).
5. Run the critic on each result.
6. Synthesize a single user-facing reply that cites specialists and
   surfaces critic warnings.

The single-agent code path in ``services/agent.py`` is unchanged. This
module is wired in via ``services.agent_router.chat`` behind the
``multi_agent_enabled`` settings flag.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Any

from resonantia.config import get_settings
from resonantia.services.guardrails import (
    GUARDRAIL_SYSTEM_PROMPT,
    check_guardrails,
)
from resonantia.services.llm import LLMProvider, get_provider
from resonantia.services.multi_agent import critic as critic_module
from resonantia.services.multi_agent.messages import (
    AgentName,
    CriticVerdict,
    OrchestrationPlan,
    OrchestratorReply,
    TaskAssignment,
    TaskResult,
)
from resonantia.services.multi_agent.prompts import ORCHESTRATOR_PROMPT
from resonantia.services.multi_agent.subagents import SPECIALISTS, run_specialist
from resonantia.services.tracing import trace_llm_call, trace_routing_decision

logger = logging.getLogger(__name__)


def _get_provider() -> LLMProvider:
    return get_provider()


async def _decompose(message: str, provider: LLMProvider) -> OrchestrationPlan:
    """Ask the orchestrator LLM to emit a structured plan."""
    settings = get_settings()
    try:
        response = await provider.completion(
            messages=[
                {"role": "system", "content": ORCHESTRATOR_PROMPT},
                {"role": "user", "content": message},
            ],
            model=settings.planner_model,
            temperature=0.0,
            max_tokens=600,
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        logger.warning("Orchestrator decompose failed: %s", exc)
        return OrchestrationPlan(rationale="orchestrator_unavailable", assignments=[])

    raw = response.content or "{}"
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Orchestrator returned invalid JSON: %r", raw[:200])
        return OrchestrationPlan(rationale="invalid_decomposition", assignments=[])

    # Coerce assignments — the LLM may omit task_ids or use slightly
    # wrong field names. We re-validate via Pydantic and drop bad ones.
    raw_assignments = parsed.get("assignments") or []
    assignments: list[TaskAssignment] = []
    for raw_a in raw_assignments:
        if not isinstance(raw_a, dict):
            continue
        if not raw_a.get("task_id"):
            raw_a["task_id"] = uuid.uuid4().hex
        agent_name = raw_a.get("assigned_agent")
        if agent_name not in SPECIALISTS:
            logger.info("Dropping unknown specialist %r", agent_name)
            continue
        try:
            assignments.append(TaskAssignment(**raw_a))
        except Exception as exc:
            logger.info("Dropping invalid assignment %s: %s", raw_a, exc)

    return OrchestrationPlan(
        rationale=str(parsed.get("rationale", ""))[:600],
        assignments=assignments,
        can_run_parallel=bool(parsed.get("can_run_parallel", False)),
    )


async def _execute_assignments(
    plan: OrchestrationPlan,
    org_id: str,
    provider: LLMProvider,
    conversation_id: str | None = None,
) -> list[TaskResult]:
    """Run specialist assignments either in parallel or sequentially.

    In sequential mode, each assignment receives the previous results
    appended to its ``inputs`` under the ``upstream`` key so downstream
    specialists can reason over them. Parallel mode runs assignments
    concurrently and is only safe when there are no data dependencies
    between them — the orchestrator prompt sets ``can_run_parallel``.
    """
    if not plan.assignments:
        return []
    if plan.can_run_parallel and len(plan.assignments) > 1:
        return await asyncio.gather(
            *(
                run_specialist(a, org_id, provider=provider, conversation_id=conversation_id)
                for a in plan.assignments
            )
        )

    results: list[TaskResult] = []
    for assignment in plan.assignments:
        if results:
            assignment = assignment.model_copy(
                update={
                    "inputs": {
                        **assignment.inputs,
                        "upstream": [
                            {
                                "task_id": r.task_id,
                                "agent": r.assigned_agent,
                                "output": r.output,
                            }
                            for r in results
                        ],
                    }
                }
            )
        results.append(
            await run_specialist(assignment, org_id, provider=provider, conversation_id=conversation_id)
        )
    return results


async def _critic_pass(
    user_request: str,
    results: list[TaskResult],
    provider: LLMProvider,
    org_id: str | None = None,
    conversation_id: str | None = None,
) -> list[CriticVerdict]:
    if not results:
        return []
    return await asyncio.gather(
        *(
            critic_module.review(
                user_request, r, provider=provider,
                org_id=org_id, conversation_id=conversation_id,
            )
            for r in results
        )
    )


async def _synthesize_answer(
    user_message: str,
    results: list[TaskResult],
    verdicts: list[CriticVerdict],
    provider: LLMProvider,
) -> str:
    """Compose a single reply from the specialists' outputs and the critic."""
    settings = get_settings()
    rejections = [v for v in verdicts if v.decision == "reject"]
    warnings = [v for v in verdicts if v.decision == "soft_warn"]

    if not results:
        # No specialist was selected -- fall back to a direct LLM reply with
        # the standard guardrail prompt so the answer still goes through
        # Resonantia's tone/safety policy.
        try:
            response = await provider.completion(
                messages=[
                    {"role": "system", "content": GUARDRAIL_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                model=settings.planner_model,
                temperature=0.3,
                max_tokens=800,
            )
        except Exception as exc:
            return f"I couldn't reach the language model ({exc.__class__.__name__})."
        return response.content or ""

    # Single-specialist short-circuit: only when the critic explicitly
    # passed. An empty verdict list (e.g. critic skipped) is NOT the same
    # as a passing review and must not bypass the synthesis path.
    if (
        len(results) == 1
        and len(verdicts) == 1
        and verdicts[0].decision == "pass"
    ):
        return results[0].output

    sections = []
    for r in results:
        verdict = next((v for v in verdicts if v.task_id == r.task_id), None)
        header = f"### {r.assigned_agent}"
        if verdict and verdict.decision == "reject":
            header += "  [rejected by critic]"
        elif verdict and verdict.decision == "soft_warn":
            header += "  [critic note]"
        sections.append(f"{header}\n{r.output.strip()}")
        if verdict and verdict.reason and verdict.decision != "pass":
            sections.append(f"_Critic: {verdict.reason}_")

    body = "\n\n".join(sections)
    if rejections:
        body += (
            "\n\n_One or more specialists were rejected by the critic. "
            "Review the flagged sections before acting on them._"
        )
    return body


async def chat(
    message: str,
    *,
    conversation_id: str | None = None,
    context: dict[str, Any] | None = None,
    clerk_user_id: str | None = None,
    org_id: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Multi-agent equivalent of ``services.agent.chat``.

    Returns a dict matching the legacy shape so the FastAPI layer doesn't
    need to know which agent path served the request.
    """
    # Persistence layer is shared with the legacy agent.
    from resonantia.services.agent import (
        _get_or_create_conversation,
        _persist_message,
        _update_conversation_title,
    )

    user_id = clerk_user_id or "anonymous"
    org = org_id or "org_default"

    conv_uuid, _history = await _get_or_create_conversation(conversation_id, user_id, org)
    cid = str(conv_uuid)

    guardrail_result = check_guardrails(message)
    if not guardrail_result[0]:
        return {
            "message": guardrail_result[1],
            "conversation_id": cid,
            "tool_calls": None,
            "routed_to": [],
        }

    user_content = message
    if context:
        user_content = f"[Context: {json.dumps(context)}]\n\n{message}"

    await _persist_message(conv_uuid, "user", content=user_content)
    if not _history:
        await _update_conversation_title(conv_uuid, message)

    settings = get_settings()
    provider_name = settings.default_provider
    has_key = (
        (provider_name == "openai" and settings.openai_api_key)
        or (provider_name == "anthropic" and settings.anthropic_api_key)
        or settings.openai_api_key
    )
    if not has_key:
        msg = f"Multi-agent mode requires an LLM API key. Configure the key for '{provider_name}' provider."
        await _persist_message(conv_uuid, "assistant", content=msg)
        return {"message": msg, "conversation_id": cid, "tool_calls": None, "routed_to": []}

    provider = _get_provider()
    start = time.monotonic()

    plan = await _decompose(message, provider)

    # Trace the routing decision (P4.2)
    decompose_latency = (time.monotonic() - start) * 1000
    trace_routing_decision(
        user_message=message,
        rationale=plan.rationale,
        assigned_agents=[a.assigned_agent for a in plan.assignments],
        can_run_parallel=plan.can_run_parallel,
        model=settings.planner_model,
        org_id=org,
        conversation_id=cid,
        latency_ms=decompose_latency,
    )

    results = await _execute_assignments(plan, org, provider, conversation_id=cid)
    verdicts = await _critic_pass(message, results, provider, org_id=org, conversation_id=cid)
    final_text = await _synthesize_answer(message, results, verdicts, provider)

    routed: list[AgentName] = [r.assigned_agent for r in results]
    all_tool_calls = [tc for r in results for tc in r.tool_calls]

    # Persistence mirrors the legacy single-agent shape: tool_calls is
    # the actual list of {id, name, input}. Multi-agent metadata
    # (which specialists ran, critic verdicts) is returned in the live
    # response but not persisted in v1 -- replay/audit needs a dedicated
    # column, tracked as a follow-up rather than overloading existing
    # JSON columns.
    await _persist_message(
        conv_uuid,
        "assistant",
        content=final_text,
        tool_calls=all_tool_calls or None,
    )

    latency_ms = (time.monotonic() - start) * 1000
    trace_llm_call(
        user_message=message,
        system_prompt=ORCHESTRATOR_PROMPT,
        response=final_text,
        model=settings.planner_model,
        org_id=org,
        conversation_id=cid,
        agent_role="orchestrator",
        tool_calls=[tc["name"] for tc in all_tool_calls],
        tools_used=[tc["name"] for tc in all_tool_calls],
        guardrail_result=guardrail_result,
        latency_ms=latency_ms,
        metadata={
            "provider": provider.provider_name,
            "routed_to": list(routed),
            "num_specialists": len(results),
        },
    )

    reply = OrchestratorReply(
        message=final_text,
        conversation_id=cid,
        routed_to=routed,
        sub_results=results,
        critic_verdicts=verdicts,
        tool_calls=all_tool_calls,
    )

    return {
        "message": reply.message,
        "conversation_id": reply.conversation_id,
        "tool_calls": all_tool_calls or None,
        "routed_to": list(reply.routed_to),
        "critic_verdicts": [v.model_dump() for v in reply.critic_verdicts],
    }
