"""Routes chat requests to either the legacy single-agent loop or the
multi-agent orchestrator, based on the ``multi_agent_enabled`` flag.

Kept deliberately tiny so api/chat.py only needs to import one symbol
and never branches on the flag itself.
"""

from __future__ import annotations

from typing import Any

from resonantia.config import get_settings


async def chat(
    message: str,
    *,
    conversation_id: str | None = None,
    context: dict[str, Any] | None = None,
    clerk_user_id: str | None = None,
    org_id: str | None = None,
    attachments: list[str] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    if get_settings().multi_agent_enabled:
        from resonantia.services.multi_agent.orchestrator import chat as multi_chat

        return await multi_chat(
            message,
            conversation_id=conversation_id,
            context=context,
            clerk_user_id=clerk_user_id,
            org_id=org_id,
            request_id=request_id,
        )

    from resonantia.services import agent as legacy_agent

    return await legacy_agent.chat(
        message=message,
        conversation_id=conversation_id,
        context=context,
        clerk_user_id=clerk_user_id,
        org_id=org_id,
        attachments=attachments,
        request_id=request_id,
    )
