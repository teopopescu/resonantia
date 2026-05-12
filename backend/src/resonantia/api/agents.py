"""A2A Agent Protocol API endpoints.

Provides REST endpoints for agent discovery, manifest retrieval,
message sending, and external agent registration.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from resonantia.services.a2a.envelope import A2AEnvelope
from resonantia.services.a2a.manifest import AgentManifest
from resonantia.services.a2a.registry import get_registry
from resonantia.services.a2a.transport import LocalTransport

router = APIRouter()


@router.get("")
async def list_agents() -> list[AgentManifest]:
    """List all registered agents."""
    registry = get_registry()
    return registry.list_all()


@router.get("/{agent_id}/manifest")
async def get_manifest(agent_id: str) -> AgentManifest:
    """Get the manifest of a specific agent."""
    registry = get_registry()
    manifest = registry.get(agent_id)
    if manifest is None:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return manifest


@router.post("/{agent_id}/message")
async def send_message(agent_id: str, envelope: A2AEnvelope) -> A2AEnvelope:
    """Send an envelope to a specific agent and get a response.

    Currently only supports local agents via LocalTransport.
    """
    registry = get_registry()
    manifest = registry.get(agent_id)
    if manifest is None:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    # Ensure envelope is addressed to the correct agent
    if envelope.to_agent != agent_id:
        raise HTTPException(
            status_code=400,
            detail=f"Envelope to_agent '{envelope.to_agent}' does not match endpoint agent '{agent_id}'",
        )

    # Route based on whether agent is local or remote
    if manifest.endpoint is None:
        transport = LocalTransport()
        response = await transport.send(envelope)
        return response
    else:
        raise HTTPException(
            status_code=501,
            detail="Remote agent forwarding not yet implemented",
        )


@router.post("/register")
async def register_agent(manifest: AgentManifest) -> dict[str, str]:
    """Register an external agent."""
    registry = get_registry()
    registry.register(manifest)
    return {"status": "registered", "agent_id": manifest.agent_id}
