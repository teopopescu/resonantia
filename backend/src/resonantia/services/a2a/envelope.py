"""A2A message envelope.

Every inter-agent message is wrapped in an A2AEnvelope regardless of
transport mechanism. This provides:
- Provenance (from_agent, to_agent)
- Traceability (trace_id, message_id, conversation_id)
- Multi-tenancy (org_id)
- Async support (callback_url, expects_callback, in_reply_to)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex


class A2AEnvelope(BaseModel):
    """Structured envelope for agent-to-agent communication."""

    protocol: str = "a2a/1.0"
    message_id: str = Field(default_factory=_new_id)
    from_agent: str
    to_agent: str
    org_id: str
    conversation_id: str | None = None
    timestamp: str = Field(default_factory=_now_iso)
    payload_type: str
    """Identifies the payload schema, e.g. 'task_assignment', 'task_result'."""
    payload: dict = Field(default_factory=dict)
    callback_url: str | None = None
    expects_callback: bool = False
    in_reply_to: str | None = None
    trace_id: str | None = None
