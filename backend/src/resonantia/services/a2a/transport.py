"""Agent transports — how envelopes physically travel between agents.

Three transport implementations:
- LocalTransport: wraps run_specialist() for in-process calls (zero behavior change)
- HTTPTransport: POST envelope JSON to a remote agent endpoint
- (Future) TemporalTransport: durable execution via Temporal workflows
"""

from __future__ import annotations

import abc
import logging
from typing import Any

import httpx

from resonantia.services.a2a.envelope import A2AEnvelope
from resonantia.services.multi_agent.messages import TaskAssignment, TaskResult
from resonantia.services.multi_agent.subagents import run_specialist

logger = logging.getLogger(__name__)


class AgentTransport(abc.ABC):
    """Abstract base class for agent transports."""

    @abc.abstractmethod
    async def send(self, envelope: A2AEnvelope) -> A2AEnvelope:
        """Send an envelope and wait for a synchronous response envelope."""
        ...

    @abc.abstractmethod
    async def send_async(self, envelope: A2AEnvelope) -> str:
        """Send an envelope asynchronously, return the message_id.

        The response will arrive via callback or polling.
        """
        ...


class LocalTransport(AgentTransport):
    """In-process transport that wraps run_specialist().

    Converts an A2AEnvelope with payload_type='task_assignment' into a
    TaskAssignment, calls run_specialist(), and wraps the TaskResult
    back into a response envelope. ZERO behavior change from calling
    run_specialist directly.
    """

    async def send(self, envelope: A2AEnvelope) -> A2AEnvelope:
        """Execute locally and return response envelope."""
        if envelope.payload_type != "task_assignment":
            raise ValueError(
                f"LocalTransport only handles 'task_assignment' payloads, "
                f"got '{envelope.payload_type}'"
            )

        # Convert envelope payload to TaskAssignment
        task = TaskAssignment(**envelope.payload)

        # Call the existing run_specialist — no behavior change
        result: TaskResult = await run_specialist(
            task,
            org_id=envelope.org_id,
            conversation_id=envelope.conversation_id,
        )

        # Wrap TaskResult back into an envelope
        response = A2AEnvelope(
            from_agent=envelope.to_agent,
            to_agent=envelope.from_agent,
            org_id=envelope.org_id,
            conversation_id=envelope.conversation_id,
            payload_type="task_result",
            payload=result.model_dump(),
            in_reply_to=envelope.message_id,
            trace_id=envelope.trace_id,
        )
        return response

    async def send_async(self, envelope: A2AEnvelope) -> str:
        """LocalTransport is always synchronous; this just calls send()
        and returns the message_id of the response."""
        response = await self.send(envelope)
        return response.message_id


class HTTPTransport(AgentTransport):
    """Remote transport that POSTs envelope JSON to an agent endpoint."""

    def __init__(self, endpoint: str, *, timeout: float = 60.0, auth_token: str | None = None):
        self._endpoint = endpoint
        self._timeout = timeout
        self._auth_token = auth_token

    async def send(self, envelope: A2AEnvelope) -> A2AEnvelope:
        """POST envelope to remote agent, parse response as envelope."""
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                self._endpoint,
                json=envelope.model_dump(),
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

        return A2AEnvelope(**data)

    async def send_async(self, envelope: A2AEnvelope) -> str:
        """POST envelope with expects_callback=True, return message_id."""
        envelope_copy = envelope.model_copy(update={"expects_callback": True})
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                self._endpoint,
                json=envelope_copy.model_dump(),
                headers=headers,
            )
            resp.raise_for_status()

        return envelope.message_id
