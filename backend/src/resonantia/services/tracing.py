"""Langfuse v4 tracing for Resonantia Lab — traces all LLM interactions.

Every LLM call includes structured trace metadata for operational
visibility: org_id, conversation_id, model, tokens, latency, cost,
agent_role, and tool_calls. Multi-agent routing decisions are traced
so Langfuse dashboards surface cost-per-org, latency p50/p95, error
rate, and tool usage distribution.
"""

import logging
import os
import time
from typing import Any

from resonantia.config import get_settings

logger = logging.getLogger(__name__)

_initialized = False


def _ensure_env():
    """Set Langfuse env vars from app config so get_client() picks them up."""
    global _initialized
    if _initialized:
        return
    settings = get_settings()
    if settings.langfuse_public_key:
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.langfuse_public_key)
    if settings.langfuse_secret_key:
        os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.langfuse_secret_key)
    if settings.langfuse_host:
        os.environ.setdefault("LANGFUSE_HOST", settings.langfuse_host)
    _initialized = True


def _get_client():
    """Get the Langfuse client, or None if not configured."""
    _ensure_env()
    settings = get_settings()
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None
    try:
        from langfuse import get_client
        return get_client()
    except Exception as e:
        logger.warning("Could not get Langfuse client: %s", e)
        return None


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Rough cost estimation for known Claude/GPT models (USD)."""
    # Pricing as of 2025 (per 1M tokens)
    pricing: dict[str, tuple[float, float]] = {
        "claude-sonnet-4-20250514": (3.0, 15.0),
        "claude-haiku-4-5-20251001": (0.80, 4.0),
        "gpt-4o": (2.50, 10.0),
        "gpt-4o-mini": (0.15, 0.60),
    }
    in_price, out_price = pricing.get(model, (3.0, 15.0))
    return (input_tokens * in_price + output_tokens * out_price) / 1_000_000


def trace_llm_call(
    user_message: str,
    system_prompt: str,
    response: str,
    model: str,
    user_id: str | None = None,
    conversation_id: str | None = None,
    org_id: str | None = None,
    agent_role: str | None = None,
    tool_calls: list[str] | None = None,
    tools_used: list[str] | None = None,
    guardrail_result: tuple[bool, str] | None = None,
    latency_ms: float | None = None,
    token_usage: dict[str, int] | None = None,
    metadata: dict[str, Any] | None = None,
) -> str | None:
    """Trace a single LLM call to Langfuse. Returns trace_id or None.

    Mandatory trace metadata per P4.2 spec:
    - org_id, conversation_id, model, input_tokens, output_tokens,
      latency_ms, cost_usd, agent_role, tool_calls
    """
    lf = _get_client()
    if lf is None:
        return None

    # Resolve tool_calls — callers may pass via either param name
    resolved_tools = tool_calls or tools_used or []

    # Token counts from usage dict or zeros
    input_tokens = (token_usage or {}).get("input_tokens", 0)
    output_tokens = (token_usage or {}).get("output_tokens", 0)
    cost_usd = _estimate_cost(model, input_tokens, output_tokens)

    try:
        trace_metadata = {
            # P4.2 mandatory fields
            "org_id": org_id or (metadata or {}).get("org_id"),
            "conversation_id": conversation_id,
            "model": model,
            "agent_role": agent_role or "single_agent",
            "tool_calls": resolved_tools,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency_ms,
            "cost_usd": cost_usd,
            # Legacy fields
            "guardrail_allowed": guardrail_result[0] if guardrail_result else True,
            "guardrail_reason": guardrail_result[1] if guardrail_result else "",
            "tools_used": resolved_tools,
            "user_id": user_id,
            "provider": (metadata or {}).get("provider", ""),
            **(metadata or {}),
        }

        # Create the top-level agent span
        with lf.start_as_current_observation(
            name="resonantia-chat",
            as_type="agent",
            input=user_message,
            output=response,
            metadata=trace_metadata,
        ) as agent_span:
            # Nested generation span for the LLM call
            with lf.start_as_current_observation(
                name="chat-completion",
                as_type="generation",
                model=model,
                input=[
                    {"role": "system", "content": system_prompt[:500]},
                    {"role": "user", "content": user_message},
                ],
                output=response,
                metadata={"latency_ms": latency_ms, "agent_role": agent_role},
                usage_details=token_usage,
            ):
                pass

            # Guardrail span if blocked
            if guardrail_result and not guardrail_result[0]:
                with lf.start_as_current_observation(
                    name="guardrail-check",
                    as_type="guardrail",
                    input=user_message,
                    output=guardrail_result[1],
                    metadata={"blocked": True, "reason": guardrail_result[1]},
                ):
                    pass

            trace_id = lf.get_current_trace_id()

        lf.flush()
        logger.debug("Traced LLM call: %s", trace_id)
        return trace_id
    except Exception as e:
        logger.warning("Langfuse tracing failed: %s", e)
        return None


def trace_specialist_call(
    *,
    agent_role: str,
    objective: str,
    response: str,
    model: str,
    org_id: str | None = None,
    conversation_id: str | None = None,
    tool_calls: list[str] | None = None,
    latency_ms: float | None = None,
    token_usage: dict[str, int] | None = None,
    metadata: dict[str, Any] | None = None,
) -> str | None:
    """Trace an individual specialist subagent call.

    Creates a span with agent_role = "specialist:<name>" so Langfuse
    dashboards can show per-specialist latency and cost breakdowns.
    """
    return trace_llm_call(
        user_message=objective,
        system_prompt=f"[specialist:{agent_role}]",
        response=response,
        model=model,
        org_id=org_id,
        conversation_id=conversation_id,
        agent_role=f"specialist:{agent_role}",
        tool_calls=tool_calls or [],
        latency_ms=latency_ms,
        token_usage=token_usage,
        metadata=metadata,
    )


def trace_routing_decision(
    *,
    user_message: str,
    rationale: str,
    assigned_agents: list[str],
    can_run_parallel: bool,
    model: str,
    org_id: str | None = None,
    conversation_id: str | None = None,
    latency_ms: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> str | None:
    """Trace a multi-agent routing decision (which specialist was chosen and why).

    This makes Langfuse dashboards surface routing patterns: which
    specialists are chosen most often, what rationale the orchestrator gives,
    and how parallel vs sequential decisions distribute.
    """
    return trace_llm_call(
        user_message=user_message,
        system_prompt="[orchestrator:routing]",
        response=rationale,
        model=model,
        org_id=org_id,
        conversation_id=conversation_id,
        agent_role="orchestrator",
        tool_calls=[],
        latency_ms=latency_ms,
        metadata={
            "routing_decision": True,
            "assigned_agents": assigned_agents,
            "can_run_parallel": can_run_parallel,
            "num_assignments": len(assigned_agents),
            **(metadata or {}),
        },
    )


def trace_critic_call(
    *,
    task_id: str,
    specialist: str,
    decision: str,
    reason: str,
    model: str,
    org_id: str | None = None,
    conversation_id: str | None = None,
    latency_ms: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> str | None:
    """Trace a critic review decision."""
    return trace_llm_call(
        user_message=f"[critic review of {specialist}:{task_id}]",
        system_prompt="[critic]",
        response=f"{decision}: {reason}",
        model=model,
        org_id=org_id,
        conversation_id=conversation_id,
        agent_role="critic",
        tool_calls=[],
        latency_ms=latency_ms,
        metadata={
            "critic_task_id": task_id,
            "critic_specialist": specialist,
            "critic_decision": decision,
            **(metadata or {}),
        },
    )


def shutdown_langfuse():
    """Flush and close Langfuse client."""
    try:
        lf = _get_client()
        if lf is not None:
            lf.flush()
            lf.shutdown()
    except Exception:
        pass
