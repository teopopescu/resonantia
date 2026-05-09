"""Critic agent -- reviews specialist outputs before they reach the user.

Per docs/agentic-architecture.md S2: pharma scientists won't trust an
agent twice if they catch it lying once. The critic is a separate LLM
call with no tools, lower temperature, and a purely adversarial prompt.

Safety hardening (P4.1):
- Validates that tool results include ``source_refs`` when tools were used.
  Specialist answers that cite no sources after calling data-producing tools
  are flagged with a soft_warn (or reject for high-stakes tools).
"""

from __future__ import annotations

import json
import logging
import time

from resonantia.config import get_settings
from resonantia.services.llm import LLMProvider, get_provider
from resonantia.services.multi_agent.messages import CriticVerdict, TaskResult
from resonantia.services.multi_agent.prompts import CRITIC_PROMPT
from resonantia.services.tracing import trace_critic_call

logger = logging.getLogger(__name__)

# Tools whose output must not surface to the user without a real critic
# review. If the critic fails for any reason while reviewing a result
# that includes one of these tools, fail closed (reject) rather than
# silently letting the answer through with a soft warning.
HIGH_STAKES_TOOLS = frozenset(
    {
        "fit_dose_response",
        "generate_worklist",
        "create_plate_map",
        "submit_eln_entry",
        "create_eln_entry",
        "qpcr_analysis",
    }
)

# Tools that produce data which should be cited with source_refs.
# If a specialist used one of these tools but the tool result in the
# conversation has no source_refs, the critic flags it.
DATA_PRODUCING_TOOLS = frozenset(
    {
        "fit_dose_response",
        "generate_worklist",
        "create_plate_map",
        "qpcr_analysis",
        "lookup_sample",
        "check_inventory",
        "query_experiments",
        "query_eln_entries",
        "get_plate_map_details",
        "normalize_plate",
    }
)


def _has_high_stakes_tool(result: TaskResult) -> bool:
    return any(tc.get("name") in HIGH_STAKES_TOOLS for tc in result.tool_calls)


def _check_source_refs(result: TaskResult) -> str | None:
    """Validate that tool results include source_refs when data-producing tools were used.

    Returns a warning reason string if source_refs are missing, None otherwise.
    """
    if not result.tool_calls:
        return None

    data_tool_used = any(
        tc.get("name") in DATA_PRODUCING_TOOLS for tc in result.tool_calls
    )
    if not data_tool_used:
        return None

    # Check if the specialist's output mentions any identifiable reference
    # pattern (UUIDs, plate IDs, experiment IDs, etc.)
    # A proper check would inspect the actual ToolResult.source_refs from
    # the tool execution, but the critic only sees the specialist's final
    # text output. We flag if the output doesn't contain any ID-like token.
    output = result.output.lower()
    has_reference = any(
        indicator in output
        for indicator in [
            "id:", "id=", "plate_", "exp_", "sample_", "lot ", "barcode",
            "-", "ref:", "source:", "#",
        ]
    )
    if not has_reference and len(result.tool_calls) > 0:
        return "no_source_refs_cited"
    return None


async def review(
    user_request: str,
    result: TaskResult,
    *,
    provider: LLMProvider | None = None,
    org_id: str | None = None,
    conversation_id: str | None = None,
) -> CriticVerdict:
    """Run the critic. Failures degrade to ``soft_warn`` so the user is
    never blocked by an unavailable critic -- but they are warned that
    the answer was not reviewed.
    """
    settings = get_settings()
    fail_closed = _has_high_stakes_tool(result)
    start_time = time.monotonic()

    def _degrade(reason: str) -> CriticVerdict:
        # When the specialist used a high-stakes tool, an unavailable
        # critic must not let the answer through silently. Reject so
        # the synthesizer marks the section and the user is forced to
        # eyeball the output before acting on it.
        return CriticVerdict(
            task_id=result.task_id,
            decision="reject" if fail_closed else "soft_warn",
            reason=reason,
        )

    # --- Source-ref validation (P4.1 safety hardening) ---
    source_ref_issue = _check_source_refs(result)
    if source_ref_issue and fail_closed:
        verdict = CriticVerdict(
            task_id=result.task_id,
            decision="reject",
            reason=f"source_ref_validation_failed: {source_ref_issue}",
        )
        trace_critic_call(
            task_id=result.task_id,
            specialist=result.assigned_agent,
            decision=verdict.decision,
            reason=verdict.reason,
            model=settings.critic_model,
            org_id=org_id,
            conversation_id=conversation_id,
            latency_ms=(time.monotonic() - start_time) * 1000,
        )
        return verdict

    # Check for API key availability.
    provider_name = settings.default_provider
    has_key = (
        (provider_name == "openai" and settings.openai_api_key)
        or (provider_name == "anthropic" and settings.anthropic_api_key)
        or settings.openai_api_key
    )
    if not has_key:
        return _degrade("critic_unavailable_no_api_key")

    provider = provider or get_provider()

    payload = {
        "user_request": user_request,
        "specialist": result.assigned_agent,
        "specialist_status": result.status,
        "specialist_answer": result.output,
        "tool_calls": result.tool_calls[-8:],  # cap context size
        "source_ref_warning": source_ref_issue,
    }

    try:
        response = await provider.completion(
            messages=[
                {"role": "system", "content": CRITIC_PROMPT},
                {"role": "user", "content": json.dumps(payload)},
            ],
            model=settings.critic_model,
            temperature=0.0,
            max_tokens=200,
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        exc_name = exc.__class__.__name__
        if "auth" in exc_name.lower():
            return _degrade("critic_auth_error")
        logger.warning("Critic failure: %s", exc)
        return _degrade(f"critic_error_{exc_name}")

    raw = response.content or "{}"
    try:
        parsed = json.loads(raw)
        decision = parsed.get("decision", "soft_warn")
        if decision not in ("pass", "soft_warn", "reject"):
            decision = "soft_warn"
        reason = str(parsed.get("reason", ""))[:300]
    except (json.JSONDecodeError, AttributeError):
        return _degrade("critic_unparseable_response")

    # If source_ref issue and LLM didn't catch it, upgrade to at least soft_warn
    if source_ref_issue and decision == "pass":
        decision = "soft_warn"
        reason = f"{reason}; {source_ref_issue}".strip("; ")

    latency_ms = (time.monotonic() - start_time) * 1000
    verdict = CriticVerdict(
        task_id=result.task_id,
        decision=decision,
        reason=reason,
    )

    # Trace the critic decision
    trace_critic_call(
        task_id=result.task_id,
        specialist=result.assigned_agent,
        decision=verdict.decision,
        reason=verdict.reason,
        model=settings.critic_model,
        org_id=org_id,
        conversation_id=conversation_id,
        latency_ms=latency_ms,
        metadata={
            "source_ref_issue": source_ref_issue,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
        },
    )

    return verdict
