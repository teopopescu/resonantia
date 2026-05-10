"""Tests for the A2A (Agent-to-Agent) protocol layer.

Covers:
- Manifest generation from SPECIALISTS config
- Envelope serialization round-trip
- Registry register/discover/get
- LocalTransport round-trip (envelope -> run_specialist -> envelope)
- Agent API endpoints exist
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from resonantia.services.a2a.envelope import A2AEnvelope
from resonantia.services.a2a.manifest import AgentCapability, AgentManifest
from resonantia.services.a2a.registry import (
    AgentRegistry,
    _manifest_from_specialist,
    get_registry,
)
from resonantia.services.a2a.transport import LocalTransport
from resonantia.services.multi_agent.messages import TaskAssignment, TaskResult
from resonantia.services.multi_agent.subagents import SPECIALISTS


# ---------------------------------------------------------------------------
# Manifest generation from SPECIALISTS config
# ---------------------------------------------------------------------------


class TestManifestGeneration:
    """Manifest generation from SPECIALISTS config."""

    def test_all_specialists_produce_valid_manifests(self):
        """Every specialist in SPECIALISTS produces a valid AgentManifest."""
        for name, config in SPECIALISTS.items():
            manifest = _manifest_from_specialist(name, config)
            assert manifest.agent_id == name
            assert manifest.protocol == "a2a/1.0"
            assert manifest.version == "1.0.0"
            assert len(manifest.capabilities) >= 1

    def test_plate_designer_has_correct_capabilities(self):
        """plate_designer advertises plate_mapping and microscopy."""
        manifest = _manifest_from_specialist(
            "plate_designer", SPECIALISTS["plate_designer"]
        )
        cap_names = {c.name for c in manifest.capabilities}
        assert "plate_mapping" in cap_names
        assert "microscopy" in cap_names

    def test_general_specialist_has_general_capability(self):
        """general specialist advertises a 'general' capability."""
        manifest = _manifest_from_specialist("general", SPECIALISTS["general"])
        assert len(manifest.capabilities) == 1
        assert manifest.capabilities[0].name == "general"
        assert manifest.capabilities[0].gate_kind == "none"

    def test_specialist_capabilities_use_critic_gate(self):
        """Non-general specialists use 'critic' gate_kind."""
        manifest = _manifest_from_specialist(
            "data_analyst", SPECIALISTS["data_analyst"]
        )
        for cap in manifest.capabilities:
            assert cap.gate_kind == "critic"

    def test_local_agents_have_no_endpoint(self):
        """Internal agents have endpoint=None."""
        for name, config in SPECIALISTS.items():
            manifest = _manifest_from_specialist(name, config)
            assert manifest.endpoint is None
            assert manifest.auth is None


# ---------------------------------------------------------------------------
# Envelope serialization round-trip
# ---------------------------------------------------------------------------


class TestEnvelopeSerialization:
    """A2AEnvelope serialization and deserialization."""

    def test_envelope_round_trip(self):
        """Envelope serializes to JSON and deserializes back identically."""
        envelope = A2AEnvelope(
            from_agent="orchestrator",
            to_agent="data_analyst",
            org_id="org_123",
            conversation_id="conv_456",
            payload_type="task_assignment",
            payload={
                "task_id": "t1",
                "assigned_agent": "data_analyst",
                "objective": "Fit dose-response curve",
                "inputs": {"concentrations": [1, 10, 100]},
                "constraints": ["Use 4PL model"],
            },
            trace_id="trace_abc",
        )

        json_str = envelope.model_dump_json()
        restored = A2AEnvelope.model_validate_json(json_str)

        assert restored.protocol == "a2a/1.0"
        assert restored.from_agent == "orchestrator"
        assert restored.to_agent == "data_analyst"
        assert restored.org_id == "org_123"
        assert restored.conversation_id == "conv_456"
        assert restored.payload_type == "task_assignment"
        assert restored.payload["objective"] == "Fit dose-response curve"
        assert restored.trace_id == "trace_abc"
        assert restored.message_id == envelope.message_id

    def test_envelope_defaults(self):
        """Envelope assigns defaults for message_id, timestamp, protocol."""
        envelope = A2AEnvelope(
            from_agent="a",
            to_agent="b",
            org_id="org",
            payload_type="ping",
        )
        assert envelope.protocol == "a2a/1.0"
        assert len(envelope.message_id) == 32  # uuid hex
        assert envelope.timestamp  # non-empty ISO string
        assert envelope.expects_callback is False
        assert envelope.in_reply_to is None

    def test_envelope_dict_round_trip(self):
        """Envelope dict export and import are symmetric."""
        envelope = A2AEnvelope(
            from_agent="x",
            to_agent="y",
            org_id="org",
            payload_type="test",
            payload={"key": "value"},
        )
        data = envelope.model_dump()
        restored = A2AEnvelope(**data)
        assert restored == envelope


# ---------------------------------------------------------------------------
# Registry register/discover/get
# ---------------------------------------------------------------------------


class TestAgentRegistry:
    """AgentRegistry operations."""

    def test_register_and_get(self):
        """Register an agent and retrieve it by ID."""
        registry = AgentRegistry()
        manifest = AgentManifest(
            agent_id="test_agent",
            capabilities=[
                AgentCapability(name="analysis", description="Data analysis")
            ],
        )
        registry.register(manifest)
        retrieved = registry.get("test_agent")
        assert retrieved is not None
        assert retrieved.agent_id == "test_agent"

    def test_get_returns_none_for_unknown(self):
        """get() returns None for unregistered agent_id."""
        registry = AgentRegistry()
        assert registry.get("nonexistent") is None

    def test_discover_by_capability(self):
        """discover() finds agents with a matching capability."""
        registry = AgentRegistry()
        manifest_a = AgentManifest(
            agent_id="agent_a",
            capabilities=[
                AgentCapability(name="plate_mapping", description="Plates")
            ],
        )
        manifest_b = AgentManifest(
            agent_id="agent_b",
            capabilities=[
                AgentCapability(name="data_processing", description="Data")
            ],
        )
        registry.register(manifest_a)
        registry.register(manifest_b)

        results = registry.discover("plate_mapping")
        assert len(results) == 1
        assert results[0].agent_id == "agent_a"

    def test_discover_returns_empty_for_unknown_capability(self):
        """discover() returns empty list when no agent matches."""
        registry = AgentRegistry()
        registry.register(
            AgentManifest(
                agent_id="x",
                capabilities=[AgentCapability(name="foo", description="f")],
            )
        )
        assert registry.discover("bar") == []

    def test_list_all(self):
        """list_all() returns all registered manifests."""
        registry = AgentRegistry()
        registry.register(AgentManifest(agent_id="a", capabilities=[]))
        registry.register(AgentManifest(agent_id="b", capabilities=[]))
        assert len(registry.list_all()) == 2

    def test_auto_register_internal(self):
        """auto_register_internal populates from SPECIALISTS dict."""
        registry = AgentRegistry()
        registry.auto_register_internal()
        assert len(registry.list_all()) == len(SPECIALISTS)
        for name in SPECIALISTS:
            assert registry.get(name) is not None

    def test_register_overwrites_existing(self):
        """Registering same agent_id overwrites the previous manifest."""
        registry = AgentRegistry()
        v1 = AgentManifest(agent_id="x", version="1.0.0", capabilities=[])
        v2 = AgentManifest(agent_id="x", version="2.0.0", capabilities=[])
        registry.register(v1)
        registry.register(v2)
        assert registry.get("x").version == "2.0.0"
        assert len(registry.list_all()) == 1


# ---------------------------------------------------------------------------
# LocalTransport round-trip
# ---------------------------------------------------------------------------


class TestLocalTransport:
    """LocalTransport: envelope -> run_specialist -> envelope."""

    @pytest.mark.asyncio
    async def test_local_transport_round_trip(self):
        """LocalTransport converts envelope to TaskAssignment, calls
        run_specialist, and wraps result back into envelope."""
        task_payload = {
            "task_id": "t1",
            "assigned_agent": "sample_agent",
            "objective": "Look up anti-GFP",
            "inputs": {},
            "constraints": [],
        }
        envelope = A2AEnvelope(
            from_agent="orchestrator",
            to_agent="sample_agent",
            org_id="org_test",
            conversation_id="conv_test",
            payload_type="task_assignment",
            payload=task_payload,
            trace_id="trace_001",
        )

        mock_result = TaskResult(
            task_id="t1",
            assigned_agent="sample_agent",
            status="completed",
            output="Lot AB123, expires 2026-12-01.",
            confidence=0.8,
        )

        with patch(
            "resonantia.services.a2a.transport.run_specialist",
            new=AsyncMock(return_value=mock_result),
        ) as mock_run:
            transport = LocalTransport()
            response = await transport.send(envelope)

        # Verify run_specialist was called with correct args
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        task_arg = call_args[0][0]
        assert isinstance(task_arg, TaskAssignment)
        assert task_arg.task_id == "t1"
        assert task_arg.assigned_agent == "sample_agent"
        assert call_args[1]["org_id"] == "org_test"
        assert call_args[1]["conversation_id"] == "conv_test"

        # Verify response envelope
        assert response.protocol == "a2a/1.0"
        assert response.from_agent == "sample_agent"
        assert response.to_agent == "orchestrator"
        assert response.org_id == "org_test"
        assert response.payload_type == "task_result"
        assert response.in_reply_to == envelope.message_id
        assert response.trace_id == "trace_001"
        assert response.payload["status"] == "completed"
        assert response.payload["output"] == "Lot AB123, expires 2026-12-01."

    @pytest.mark.asyncio
    async def test_local_transport_rejects_non_task_assignment(self):
        """LocalTransport raises ValueError for non-task_assignment payloads."""
        envelope = A2AEnvelope(
            from_agent="x",
            to_agent="y",
            org_id="org",
            payload_type="unknown_type",
            payload={},
        )
        transport = LocalTransport()
        with pytest.raises(ValueError, match="task_assignment"):
            await transport.send(envelope)

    @pytest.mark.asyncio
    async def test_local_transport_send_async(self):
        """send_async delegates to send and returns message_id."""
        task_payload = {
            "task_id": "t2",
            "assigned_agent": "general",
            "objective": "hello",
            "inputs": {},
            "constraints": [],
        }
        envelope = A2AEnvelope(
            from_agent="orchestrator",
            to_agent="general",
            org_id="org_test",
            payload_type="task_assignment",
            payload=task_payload,
        )

        mock_result = TaskResult(
            task_id="t2",
            assigned_agent="general",
            status="completed",
            output="Hello!",
        )

        with patch(
            "resonantia.services.a2a.transport.run_specialist",
            new=AsyncMock(return_value=mock_result),
        ):
            transport = LocalTransport()
            msg_id = await transport.send_async(envelope)

        # Returns a valid message_id (32 hex chars)
        assert len(msg_id) == 32


# ---------------------------------------------------------------------------
# Agent API endpoints exist
# ---------------------------------------------------------------------------


class TestAgentAPIEndpoints:
    """Integration tests for the /api/v1/agents endpoints."""

    @pytest.mark.asyncio
    async def test_list_agents_endpoint(self, client):
        """GET /api/v1/agents returns registered agents."""
        # Reset registry singleton to ensure clean state
        import resonantia.services.a2a.registry as reg_mod

        reg_mod._registry = None

        resp = await client.get("/api/v1/agents")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == len(SPECIALISTS)
        agent_ids = {a["agent_id"] for a in data}
        for name in SPECIALISTS:
            assert name in agent_ids

    @pytest.mark.asyncio
    async def test_get_manifest_endpoint(self, client):
        """GET /api/v1/agents/{agent_id}/manifest returns manifest."""
        import resonantia.services.a2a.registry as reg_mod

        reg_mod._registry = None

        resp = await client.get("/api/v1/agents/data_analyst/manifest")
        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_id"] == "data_analyst"
        assert data["protocol"] == "a2a/1.0"
        assert len(data["capabilities"]) >= 1

    @pytest.mark.asyncio
    async def test_get_manifest_404_for_unknown(self, client):
        """GET /api/v1/agents/{unknown}/manifest returns 404."""
        import resonantia.services.a2a.registry as reg_mod

        reg_mod._registry = None

        resp = await client.get("/api/v1/agents/nonexistent/manifest")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_register_external_agent(self, client):
        """POST /api/v1/agents/register adds a new agent."""
        import resonantia.services.a2a.registry as reg_mod

        reg_mod._registry = None

        manifest_data = {
            "agent_id": "external_analyzer",
            "version": "2.0.0",
            "protocol": "a2a/1.0",
            "capabilities": [
                {
                    "name": "mass_spec",
                    "description": "Mass spectrometry analysis",
                    "accepts": ["task_assignment"],
                    "returns": ["task_result"],
                    "gate_kind": "none",
                }
            ],
            "endpoint": "https://external.example.com/agent",
            "auth": "bearer",
            "max_concurrent": 3,
            "timeout_seconds": 120.0,
        }
        resp = await client.post("/api/v1/agents/register", json=manifest_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "registered"
        assert data["agent_id"] == "external_analyzer"

        # Verify it's now discoverable
        resp2 = await client.get("/api/v1/agents/external_analyzer/manifest")
        assert resp2.status_code == 200
        assert resp2.json()["endpoint"] == "https://external.example.com/agent"

    @pytest.mark.asyncio
    async def test_send_message_endpoint(self, client):
        """POST /api/v1/agents/{agent_id}/message processes envelope."""
        import resonantia.services.a2a.registry as reg_mod

        reg_mod._registry = None

        mock_result = TaskResult(
            task_id="t1",
            assigned_agent="sample_agent",
            status="completed",
            output="Found sample.",
        )

        envelope_data = {
            "from_agent": "orchestrator",
            "to_agent": "sample_agent",
            "org_id": "org_test",
            "payload_type": "task_assignment",
            "payload": {
                "task_id": "t1",
                "assigned_agent": "sample_agent",
                "objective": "Look up sample",
                "inputs": {},
                "constraints": [],
            },
        }

        with patch(
            "resonantia.services.a2a.transport.run_specialist",
            new=AsyncMock(return_value=mock_result),
        ):
            resp = await client.post(
                "/api/v1/agents/sample_agent/message", json=envelope_data
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["from_agent"] == "sample_agent"
        assert data["to_agent"] == "orchestrator"
        assert data["payload_type"] == "task_result"
        assert data["payload"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_send_message_mismatched_agent_returns_400(self, client):
        """POST /api/v1/agents/{id}/message with wrong to_agent returns 400."""
        import resonantia.services.a2a.registry as reg_mod

        reg_mod._registry = None

        envelope_data = {
            "from_agent": "orchestrator",
            "to_agent": "data_analyst",  # mismatch with URL
            "org_id": "org_test",
            "payload_type": "task_assignment",
            "payload": {},
        }

        resp = await client.post(
            "/api/v1/agents/sample_agent/message", json=envelope_data
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Singleton registry helper
# ---------------------------------------------------------------------------


class TestGetRegistry:
    """get_registry() singleton behavior."""

    def test_get_registry_returns_populated_registry(self):
        """get_registry() auto-registers internal agents on first call."""
        import resonantia.services.a2a.registry as reg_mod

        reg_mod._registry = None  # Reset singleton
        registry = get_registry()
        assert len(registry.list_all()) == len(SPECIALISTS)

    def test_get_registry_is_singleton(self):
        """get_registry() returns the same instance on repeated calls."""
        import resonantia.services.a2a.registry as reg_mod

        reg_mod._registry = None
        r1 = get_registry()
        r2 = get_registry()
        assert r1 is r2
