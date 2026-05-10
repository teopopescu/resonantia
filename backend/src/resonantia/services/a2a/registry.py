"""Agent registry — discovery and lookup of registered agents.

At startup, internal agents from SPECIALISTS are auto-registered.
External agents can register via the API at runtime.
"""

from __future__ import annotations

import logging
from typing import Any

from resonantia.services.a2a.manifest import AgentCapability, AgentManifest
from resonantia.services.multi_agent.subagents import SPECIALISTS, SpecialistConfig

logger = logging.getLogger(__name__)


# Mapping from tool category to human-readable descriptions
_CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "plate_mapping": "Plate layout design and well mapping",
    "microscopy": "Microscopy image analysis and processing",
    "data_processing": "Data analysis, curve fitting, and statistics",
    "eln": "Electronic lab notebook entry creation and management",
    "protocol": "Protocol creation and optimization",
    "sample_management": "Sample inventory lookup and tracking",
}


def _manifest_from_specialist(name: str, config: SpecialistConfig) -> AgentManifest:
    """Generate an AgentManifest from a SpecialistConfig."""
    capabilities: list[AgentCapability] = []

    if config.tool_categories:
        for cat in config.tool_categories:
            capabilities.append(
                AgentCapability(
                    name=cat,
                    description=_CATEGORY_DESCRIPTIONS.get(cat, f"{cat} operations"),
                    accepts=["task_assignment"],
                    returns=["task_result"],
                    gate_kind="critic",
                )
            )
    else:
        # 'general' specialist handles everything
        capabilities.append(
            AgentCapability(
                name="general",
                description="General-purpose lab informatics assistant",
                accepts=["task_assignment"],
                returns=["task_result"],
                gate_kind="none",
            )
        )

    return AgentManifest(
        agent_id=name,
        version="1.0.0",
        protocol="a2a/1.0",
        capabilities=capabilities,
        endpoint=None,  # local agent
        auth=None,
        max_concurrent=5,
        timeout_seconds=60.0,
    )


class AgentRegistry:
    """In-memory registry of agent manifests.

    Thread-safe for reads; writes are append-only in practice
    (startup registration + runtime external registration).
    """

    def __init__(self) -> None:
        self._agents: dict[str, AgentManifest] = {}

    def register(self, manifest: AgentManifest) -> None:
        """Register an agent manifest. Overwrites if agent_id exists."""
        self._agents[manifest.agent_id] = manifest
        logger.info(
            "Registered agent %s (v%s, %d capabilities)",
            manifest.agent_id,
            manifest.version,
            len(manifest.capabilities),
        )

    def get(self, agent_id: str) -> AgentManifest | None:
        """Get manifest by agent_id, or None if not found."""
        return self._agents.get(agent_id)

    def discover(self, capability: str) -> list[AgentManifest]:
        """Find all agents that advertise a given capability name."""
        results: list[AgentManifest] = []
        for manifest in self._agents.values():
            for cap in manifest.capabilities:
                if cap.name == capability:
                    results.append(manifest)
                    break
        return results

    def list_all(self) -> list[AgentManifest]:
        """Return all registered manifests."""
        return list(self._agents.values())

    def auto_register_internal(self) -> None:
        """Register all internal specialists from the SPECIALISTS dict."""
        for name, config in SPECIALISTS.items():
            manifest = _manifest_from_specialist(name, config)
            self.register(manifest)


# Module-level singleton instance
_registry: AgentRegistry | None = None


def get_registry() -> AgentRegistry:
    """Get or create the singleton AgentRegistry.

    Auto-registers internal agents on first call.
    """
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
        _registry.auto_register_internal()
    return _registry
