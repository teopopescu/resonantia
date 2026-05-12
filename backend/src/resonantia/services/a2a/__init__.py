"""A2A (Agent-to-Agent) protocol layer.

Provides structured envelope-based communication between agents,
supporting local function calls, HTTP, and (future) Temporal transports.
"""

from resonantia.services.a2a.envelope import A2AEnvelope
from resonantia.services.a2a.manifest import AgentCapability, AgentManifest
from resonantia.services.a2a.registry import AgentRegistry
from resonantia.services.a2a.transport import (
    AgentTransport,
    HTTPTransport,
    LocalTransport,
)

__all__ = [
    "A2AEnvelope",
    "AgentCapability",
    "AgentManifest",
    "AgentRegistry",
    "AgentTransport",
    "HTTPTransport",
    "LocalTransport",
]
