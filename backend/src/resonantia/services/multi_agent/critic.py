"""Critic agent — reviews specialist outputs before they reach the user.

Per docs/agentic-architecture.md §2: pharma scientists won't trust an
agent twice if they catch it lying once. The critic is a separate LLM
call with no tools, lower temperature, and a purely adversarial prompt.
"""

from __future__ import annotations

import json
import logging

from openai import (
    APIConnectionError,
    AsyncOpenAI,
    AuthenticationError,
    RateLimitError,
)

from resonantia.config import get_settings
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
    client: AsyncOpenAI | None = None,
) -> CriticVerdict:
    """Run the critic. Failures degrade to ``soft_warn`` so the user is
    never blocked by an unavailable critic — but they are warned that
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

    if not settings.openai_api_key:
        return _degrade("critic_unavailable_no_api_key")

    client = client or AsyncOpenAI(api_key=settings.openai_api_key)

    payload = {
        "user_request": user_request,
        "specialist": result.assigned_agent,
        "specialist_status": result.status,
        "specialist_answer": result.output,
        "tool_calls": result.tool_calls[-8:],  # cap context size
    }

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            temperature=0.0,
            max_tokens=200,
            messages=[
                {"role": "system", "content": CRITIC_PROMPT},
                {"role": "user", "content": json.dumps(payload)},
            ],
            response_format={"type": "json_object"},
        )
    except (RateLimitError, APIConnectionError) as exc:
        # Transient — degrade per fail_closed.
        logger.warning("Critic transient failure: %s", exc)
        return _degrade(f"critic_transient_{exc.__class__.__name__}")
    except AuthenticationError:
        return _degrade("critic_auth_error")
    except Exception as exc:  # parsing / unexpected
        logger.exception("Critic unexpected failure")
        return _degrade(f"critic_error_{exc.__class__.__name__}")

    raw = response.choices[0].message.content or "{}"
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
