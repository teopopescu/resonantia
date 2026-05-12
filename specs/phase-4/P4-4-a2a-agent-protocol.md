# SPEC: A2A Agent Protocol — From Function Calls to Network Agents

**ID:** P4.4
**Phase:** 4 — Multi-Agent + Observability
**Branch:** `feat/a2a-protocol`
**Priority:** P2
**Effort:** 8-10 days
**Dependencies:** P4.1 (multi-agent stabilize), P0.1 (provider abstraction)

---

## Problem Statement

The multi-agent system works but agents communicate via direct Python function calls in the same process. This means:
- No external agent can participate (Automata LINQ, Benchling agents, partner agents)
- No agent can discover what Resonantia offers (no capability manifest)
- No durable handoff — if the process crashes mid-orchestration, all state is lost
- No agent can call Resonantia asynchronously (everything is request-scoped)

The message protocol (`TaskAssignment → TaskResult → CriticVerdict`) already has the right **shape** for A2A. The missing piece is the **transport layer** and **discovery protocol**.

### Current State

```python
# orchestrator.py — direct function call, same process
result = await run_specialist(assignment)  # Python function call
verdict = await critic.review(result)       # Python function call
```

### Target State

```python
# orchestrator.py — network call, any process/machine
result = await agent_client.send(assignment, to="plate_designer")  # HTTP/WS/Temporal
verdict = await agent_client.send(result, to="critic")              # HTTP/WS/Temporal

# External agent (Automata LINQ)
result = await agent_client.send(worklist_task, to="automata-linq")  # Cross-org ACP
```

---

## Scope

### In Scope
- Agent manifest / discovery endpoint (what capabilities does each agent have)
- A2A message envelope wrapping existing Pydantic models
- HTTP transport layer (agents communicate over HTTP, not function calls)
- Internal agent registry (register/discover agents at startup)
- Callback mechanism (async agent completion notifications)
- Temporal workflow integration for durable multi-agent orchestration

### Out of Scope (Phase 3+ per roadmap)
- Automata LINQ integration (needs LINQ API access)
- Multi-org federation (needs org-boundary enforcement)
- Agent versioning and canary routing
- Consensus/voting across agents
- Custom agent SDKs for third parties

---

## Architecture

### 1. Agent Manifest

Each agent (internal or external) publishes a manifest describing its capabilities:

```python
# backend/src/resonantia/services/a2a/manifest.py

class AgentCapability(BaseModel):
    name: str                    # "fit_dose_response", "design_plate"
    description: str
    accepts: list[str]           # input field names
    returns: list[str]           # output field names
    gate_kind: str = "none"      # "none" | "soft_review" | "hard_approval"

class AgentManifest(BaseModel):
    agent_id: str                # "resonantia:plate_designer"
    version: str                 # "1.0"
    protocol: str = "a2a/1.0"
    capabilities: list[AgentCapability]
    endpoint: str                # "http://localhost:8000/api/v1/agents/plate_designer"
    auth: str = "bearer"         # auth mechanism
    max_concurrent: int = 5
    timeout_seconds: int = 30
```

### 2. A2A Message Envelope

Wraps existing `TaskAssignment` and `TaskResult` with transport metadata:

```python
# backend/src/resonantia/services/a2a/envelope.py

class A2AEnvelope(BaseModel):
    protocol: str = "a2a/1.0"
    message_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    from_agent: str              # "resonantia:orchestrator"
    to_agent: str                # "resonantia:plate_designer" or "automata:linq"
    org_id: str
    conversation_id: str | None = None
    timestamp: datetime
    
    # The actual payload — polymorphic
    payload_type: str            # "task_assignment" | "task_result" | "critic_verdict"
    payload: dict[str, Any]      # Serialized TaskAssignment, TaskResult, etc.
    
    # Async callback (for long-running agent tasks)
    callback_url: str | None = None
    expects_callback: bool = False
    
    # Correlation
    in_reply_to: str | None = None  # message_id of the request this responds to
    trace_id: str | None = None     # Langfuse trace for cross-agent observability
```

### 3. Agent Transport Interface

```python
# backend/src/resonantia/services/a2a/transport.py

class AgentTransport(ABC):
    @abstractmethod
    async def send(self, envelope: A2AEnvelope) -> A2AEnvelope | None:
        """Send a message and optionally wait for a response."""
    
    @abstractmethod
    async def send_async(self, envelope: A2AEnvelope) -> str:
        """Send without waiting. Returns message_id. Response comes via callback."""

class LocalTransport(AgentTransport):
    """In-process transport — wraps existing run_specialist() for backward compat."""
    
    async def send(self, envelope: A2AEnvelope) -> A2AEnvelope:
        assignment = TaskAssignment(**envelope.payload)
        result = await run_specialist(assignment)
        return A2AEnvelope(
            from_agent=envelope.to_agent,
            to_agent=envelope.from_agent,
            payload_type="task_result",
            payload=result.model_dump(),
            in_reply_to=envelope.message_id,
            ...
        )

class HTTPTransport(AgentTransport):
    """HTTP transport — POST envelope to agent's endpoint."""
    
    async def send(self, envelope: A2AEnvelope) -> A2AEnvelope:
        manifest = agent_registry.get(envelope.to_agent)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                manifest.endpoint,
                json=envelope.model_dump(),
                headers={"Authorization": f"Bearer {get_agent_token(envelope.org_id)}"},
                timeout=manifest.timeout_seconds,
            )
            return A2AEnvelope(**resp.json())

class TemporalTransport(AgentTransport):
    """Temporal transport — durable, survives crashes."""
    
    async def send_async(self, envelope: A2AEnvelope) -> str:
        handle = await temporal_client.start_workflow(
            AgentMessageWorkflow.run,
            AgentMessageInput(envelope=envelope),
            id=f"a2a-{envelope.message_id}",
            task_queue="agent-queue",
        )
        return envelope.message_id
```

### 4. Agent Registry

```python
# backend/src/resonantia/services/a2a/registry.py

class AgentRegistry:
    """Discover and resolve agent endpoints."""
    
    _agents: dict[str, AgentManifest] = {}
    
    def register(self, manifest: AgentManifest) -> None:
        self._agents[manifest.agent_id] = manifest
    
    def discover(self, capability: str) -> list[AgentManifest]:
        """Find agents that can handle a given capability."""
        return [
            m for m in self._agents.values()
            if any(c.name == capability for c in m.capabilities)
        ]
    
    def get(self, agent_id: str) -> AgentManifest | None:
        return self._agents.get(agent_id)
```

### 5. API Endpoints

```python
# backend/src/resonantia/api/agents.py

# Discovery
GET  /api/v1/agents                          → list all registered agents
GET  /api/v1/agents/{agent_id}/manifest      → agent manifest (capabilities)

# Message passing
POST /api/v1/agents/{agent_id}/message       → send A2AEnvelope, get response
POST /api/v1/agents/{agent_id}/message/async → send without waiting, get message_id
POST /api/v1/agents/callback/{message_id}    → receive async callback from external agent

# Registration (for external agents)
POST /api/v1/agents/register                 → register external agent manifest
```

### 6. File Changes

```
NEW:  backend/src/resonantia/services/a2a/__init__.py
NEW:  backend/src/resonantia/services/a2a/manifest.py
NEW:  backend/src/resonantia/services/a2a/envelope.py
NEW:  backend/src/resonantia/services/a2a/transport.py
NEW:  backend/src/resonantia/services/a2a/registry.py
NEW:  backend/src/resonantia/api/agents.py
MODIFY: backend/src/resonantia/services/multi_agent/orchestrator.py — use transport layer
MODIFY: backend/src/resonantia/api/router.py — include agents router
NEW:  backend/tests/test_a2a.py
```

---

## Implementation

### Step 1: Define models (day 1-2)
- `AgentManifest`, `AgentCapability` Pydantic models
- `A2AEnvelope` with correlation, callback, trace fields
- Generate manifests from existing specialist configs in `subagents.py`

### Step 2: Agent registry (day 2-3)
- In-memory registry at startup
- Auto-register internal agents from `SPECIALISTS` dict
- Discovery endpoint: `GET /api/v1/agents`
- Manifest endpoint: `GET /api/v1/agents/{id}/manifest`

### Step 3: Transport layer (day 3-5)
- `LocalTransport` wrapping existing `run_specialist()` — zero behavior change, just adds the envelope
- `HTTPTransport` for external agents — POST to agent endpoint, parse response
- Factory: `get_transport(agent_id) -> AgentTransport` (local for internal, HTTP for external)

### Step 4: Wire orchestrator (day 5-7)
- Replace `await run_specialist(assignment)` with `await transport.send(envelope)`
- Existing behavior preserved via LocalTransport (same function call under the hood)
- External agents route through HTTPTransport when registered

### Step 5: Callback mechanism (day 7-8)
- `POST /api/v1/agents/callback/{message_id}` — receives async results
- Store pending callbacks in Redis with TTL
- Temporal workflow variant: `workflow.wait_condition` for durable callbacks

### Step 6: Tests (day 8-10)
- LocalTransport round-trip: envelope → run_specialist → envelope
- Manifest generation from SPECIALISTS config
- Registry discovery by capability
- Envelope serialization/deserialization
- Callback lifecycle (send async → receive callback → correlate)
- HTTPTransport with mocked external agent

---

## Expected Behavior

### Internal agents (no behavior change)

```
# Before (direct call)
result = await run_specialist(assignment)

# After (local transport — identical behavior, envelope wrapping)
envelope = A2AEnvelope(to_agent="resonantia:plate_designer", payload=assignment.dict(), ...)
response = await local_transport.send(envelope)
result = TaskResult(**response.payload)
```

### External agent registration

```
# Automata LINQ registers with Resonantia
POST /api/v1/agents/register
{
    "agent_id": "automata:linq",
    "version": "1.0",
    "protocol": "a2a/1.0",
    "capabilities": [
        {"name": "execute_worklist", "accepts": ["worklist_csv"], "returns": ["run_status", "well_data"]}
    ],
    "endpoint": "https://api.automata.tech/agents/linq",
    "timeout_seconds": 600
}
```

### Cross-agent workflow (future)

```
# Resonantia orchestrator routes to LINQ for worklist execution
envelope = A2AEnvelope(
    to_agent="automata:linq",
    payload_type="task_assignment",
    payload={"objective": "Execute worklist", "inputs": {"worklist": worklist_csv}},
    callback_url="https://api.resonantia.io/api/v1/agents/callback/{message_id}",
    expects_callback=True,
)
message_id = await http_transport.send_async(envelope)
# ... LINQ executes, calls back when done
```

---

## Acceptance Criteria

- [ ] `AgentManifest` model with capabilities, endpoint, auth, timeout
- [ ] `A2AEnvelope` model with from/to, payload, correlation, callback fields
- [ ] Internal agents auto-registered at startup from `SPECIALISTS` dict
- [ ] `GET /api/v1/agents` returns list of registered agents with capabilities
- [ ] `GET /api/v1/agents/{id}/manifest` returns full manifest
- [ ] `LocalTransport` wraps `run_specialist()` — zero behavior change for internal routing
- [ ] `HTTPTransport` sends envelope to external agent endpoint
- [ ] `POST /api/v1/agents/register` registers external agent
- [ ] `POST /api/v1/agents/callback/{message_id}` receives async results
- [ ] Orchestrator uses transport layer instead of direct function calls
- [ ] All existing multi-agent tests still pass (LocalTransport is backward compatible)
- [ ] New tests cover: manifest generation, registry, transport round-trip, envelope serialization

---

## Risks

- **Latency for internal agents.** LocalTransport adds envelope serialization overhead (~1ms). Acceptable for the architectural benefit.
- **HTTPTransport error handling.** External agents may be slow, unreachable, or return malformed responses. Need timeouts, retries, and circuit breakers.
- **Auth between agents.** Internal agents don't need auth (same process). External agents need bearer tokens scoped by org_id. Token management is out of scope — use a shared secret for design partners, upgrade to OAuth/mTLS later.
- **Message ordering.** Parallel agent execution means responses arrive out of order. The orchestrator already handles this via `task_id` correlation.
- **Breaking change.** Replacing `run_specialist()` with transport in the orchestrator is a refactor. LocalTransport ensures zero behavior change, but the test surface must verify.

---

## Relationship to Google A2A and Anthropic ACP

### Google A2A (April 2025)
Google's Agent-to-Agent protocol defines: Agent Cards (manifest), Tasks (stateful), Messages, Artifacts, Streaming. Our `AgentManifest` maps to Agent Cards; `A2AEnvelope` maps to Messages + Tasks. We should align naming with the Google spec where possible so external agents built on Google A2A can integrate.

Key differences:
- Google A2A uses JSON-RPC over HTTP. We use REST + Pydantic.
- Google A2A has push notifications via webhooks. We have `callback_url`.
- Google A2A has streaming via SSE. We can add SSE transport later.

### Anthropic ACP (Model Context Protocol)
Resonantia already has an MCP server exposing tools. MCP is tool-level (client calls server tools). ACP/A2A is agent-level (agents delegate tasks to each other). They're complementary:
- MCP: "Call this tool with these args" (stateless, synchronous)
- A2A: "Accomplish this objective using whatever tools you need" (stateful, potentially async)

The A2A layer sits above MCP. An external agent can discover Resonantia via A2A manifest, then use MCP for direct tool calls or A2A for delegated task execution.

---

## Migration Path

| Step | Change | Risk |
|------|--------|------|
| 1. Add models + registry | No behavior change | None |
| 2. Add LocalTransport | Wraps existing calls | Low (transparent wrapper) |
| 3. Wire orchestrator to transport | Refactor function calls | Medium (test coverage critical) |
| 4. Add HTTPTransport | New capability | Low (additive) |
| 5. Add agent API endpoints | New routes | Low (additive) |
| 6. Register first external agent | First real A2A usage | Medium (depends on partner) |
