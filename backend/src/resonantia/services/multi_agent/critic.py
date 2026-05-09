"""Critic agent -- reviews specialist outputs before they reach the user.

Per docs/agentic-architecture.md S2: pharma scientists won't trust an
agent twice if they catch it lying once. The critic is a separate LLM
call with no tools, lower temperature, and a purely adversarial prompt.
"""

from __future__ import annotations

import json
import logging

from resonantia.config import get_settings
from resonantia.services.llm import LLMProvider, get_provider
from resonantia.services.multi_agent.messages import CriticVerdict, TaskResult
from resonantia.services.multi_agent.prompts import CRITIC_PROMPT

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


def _has_high_stakes_tool(result: TaskResult) -> bool:
    return any(tc.get("name") in HIGH_STAKES_TOOLS for tc in result.tool_calls)


async def review(
    user_request: str,
    result: TaskResult,
    *,
    provider: LLMProvider | None = None,
) -> CriticVerdict:
    """Run the critic. Failures degrade to ``soft_warn`` so the user is
    never blocked by an unavailable critic -- but they are warned that
    the answer was not reviewed.
    """
    settings = get_settings()
    fail_closed = _has_high_stakes_tool(result)

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

    return CriticVerdict(
        task_id=result.task_id,
        decision=decision,
        reason=reason,
    )
