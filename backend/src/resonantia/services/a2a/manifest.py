"""Agent manifest and capability models.

An AgentManifest describes what an agent can do, how to reach it,
and its operational constraints. Used by the AgentRegistry for
discovery and routing.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AgentCapability(BaseModel):
    """A single capability advertised by an agent."""

    name: str
    description: str
    accepts: list[str] = Field(default_factory=list)
    returns: list[str] = Field(default_factory=list)
    gate_kind: str = "none"
    """Gate kind: 'none', 'critic', 'approval'. Controls whether the
    capability requires external review before completing."""


class AgentManifest(BaseModel):
    """Full manifest describing an agent's identity, capabilities,
    and operational parameters."""

    agent_id: str
    version: str = "1.0.0"
    protocol: str = "a2a/1.0"
    capabilities: list[AgentCapability] = Field(default_factory=list)
    endpoint: str | None = None
    """Endpoint URL for HTTP-reachable agents. None for local agents."""
    auth: str | None = None
    """Auth scheme (e.g. 'bearer', 'api_key'). None for local agents."""
    max_concurrent: int = 5
    timeout_seconds: float = 60.0
