"""Langfuse v4 tracing for Resonantia Lab — traces all LLM interactions."""

import logging
import os
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


def trace_llm_call(
    user_message: str,
    system_prompt: str,
    response: str,
    model: str,
    user_id: str | None = None,
    conversation_id: str | None = None,
    tools_used: list[str] | None = None,
    guardrail_result: tuple[bool, str] | None = None,
    latency_ms: float | None = None,
    token_usage: dict[str, int] | None = None,
    metadata: dict[str, Any] | None = None,
) -> str | None:
    """Trace a single LLM call to Langfuse. Returns trace_id or None."""
    lf = _get_client()
    if lf is None:
        return None

    try:
        trace_metadata = {
            "guardrail_allowed": guardrail_result[0] if guardrail_result else True,
            "guardrail_reason": guardrail_result[1] if guardrail_result else "",
            "tools_used": tools_used or [],
            "user_id": user_id,
            "conversation_id": conversation_id,
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
                metadata={"latency_ms": latency_ms},
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


def shutdown_langfuse():
    """Flush and close Langfuse client."""
    try:
        lf = _get_client()
        if lf is not None:
            lf.flush()
            lf.shutdown()
    except Exception:
        pass
