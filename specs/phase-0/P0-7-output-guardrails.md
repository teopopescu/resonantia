# SPEC: Output Guardrails (Structured Validation)

**ID:** P0.7
**Phase:** 0 — Stabilize
**Branch:** `feat/output-guardrails`
**Priority:** P0
**Effort:** 3 days
**Dependencies:** P0.1 (provider abstraction)

---

## Problem Statement

Currently, tool calls execute whatever the LLM returns with no validation. The only guardrail is keyword filtering on inbound messages (`services/guardrails.py`). `execute_tool` catches all exceptions and returns JSON error strings — callers cannot distinguish validation failure from system failure from partial mutation.

This creates three risks:
1. Malformed tool arguments execute and produce garbage results
2. Cross-tenant entity references slip through (LLM hallucinates an entity_id from another org)
3. Error handling is opaque — the agent loop can't self-correct because errors look like results

---

## Scope

### In Scope
- Validate tool call arguments against registered JSON Schema before execution
- Return typed result/error envelopes (not JSON strings)
- Block cross-tenant entity references at validation layer
- Allow the agent one retry on validation failure (with structured error feedback)

### Out of Scope
- Response content moderation (LLM output text filtering)
- Hallucination detection against source data (defer to critic agent, Phase 4)
- Rate limiting tool calls (Phase 3)

---

## Architecture

### Validation Pipeline

```
LLM returns tool_call(name, arguments)
    │
    ├── 1. Schema validation: arguments match tool's input_schema (Pydantic)
    │       → If invalid: return ToolError(validation) to LLM for self-correction
    │
    ├── 2. Tenant validation: any entity_id in arguments belongs to current org_id
    │       → If cross-tenant: return ToolError(forbidden) — do NOT execute
    │
    ├── 3. Execute tool
    │       → Success: return ToolResult(data, source_refs)
    │       → System error: return ToolError(system) — log, do not expose internals
    │
    └── 4. Return to agent loop
```

### Typed Envelopes

```python
# backend/src/resonantia/services/output_validator.py

from pydantic import BaseModel
from typing import Literal

class ToolResult(BaseModel):
    status: Literal["success"] = "success"
    tool_name: str
    data: dict
    source_refs: list[str] = []  # entity IDs used to produce this result

class ToolError(BaseModel):
    status: Literal["error"] = "error"
    tool_name: str
    error_type: Literal["validation", "forbidden", "system", "timeout"]
    message: str
    retry_allowed: bool = False

# The agent loop receives ToolResult | ToolError, not raw strings
```

### File Changes

```
NEW:  backend/src/resonantia/services/output_validator.py
MODIFY: backend/src/resonantia/services/tool_executor.py
MODIFY: backend/src/resonantia/services/agent.py
NEW:  backend/tests/test_output_validator.py
```

---

## Implementation

### Step 1: Define typed envelopes (hour 1)
- Create `ToolResult` and `ToolError` Pydantic models
- Define `validate_tool_args(tool_name, args, org_id) -> args | ToolError`

### Step 2: Schema validation (day 1)
- Load tool's `input_schema` from Redis registry
- Validate args against schema using Pydantic or jsonschema
- Return `ToolError(validation, message="field X expected int, got str", retry_allowed=True)`

### Step 3: Tenant validation (day 1)
- Identify fields that reference entity IDs: any field ending in `_id` (e.g., `experiment_id`, `plate_map_id`, `sample_id`)
- For each referenced entity, check existence AND org_id match in DB
- Return `ToolError(forbidden, message="Entity not accessible")` — no retry

### Step 4: Refactor execute_tool (day 2)
- Replace `try/except → return json.dumps({"error": ...})` with typed returns
- `execute_tool() -> ToolResult | ToolError`
- System errors (DB connection, unexpected exception) → `ToolError(system)` with generic message
- Partial mutations: if a tool writes then fails, log the partial state (don't hide it)

### Step 5: Wire into agent loop (day 2-3)
- In `agent.py` agentic loop: when tool returns `ToolError(retry_allowed=True)`, feed error back to LLM as tool result with correction hint
- Max 1 retry per tool call (prevent infinite loops)
- `ToolError(retry_allowed=False)` → feed error to LLM as final (LLM should tell user)

### Step 6: Tests (day 3)
- Test schema validation catches wrong types
- Test cross-tenant entity reference is blocked
- Test retry mechanism (LLM self-corrects after validation error)
- Test system errors don't expose internals

---

## Expected Behavior

| Scenario | Before | After |
|----------|--------|-------|
| LLM sends `fit_dose_response(data="not-a-list")` | Executes, crashes internally, returns JSON error string | Validation catches: returns ToolError, LLM retries with correct type |
| LLM sends `create_eln_entry(experiment_id="other-org-uuid")` | Loads experiment from other org | Tenant check: returns ToolError(forbidden), LLM tells user "experiment not found" |
| Database connection drops during tool execution | Returns `{"error": "Connection refused..."}` (exposes internals) | Returns ToolError(system, "Internal error processing request") |
| Tool executes successfully | Returns JSON string | Returns ToolResult with data + source_refs |

---

## Acceptance Criteria

- [ ] `execute_tool()` returns `ToolResult | ToolError`, never raw strings
- [ ] Malformed tool arguments are caught BEFORE execution (no side effects)
- [ ] Agent gets one retry opportunity on validation errors
- [ ] Cross-tenant entity references return `ToolError(forbidden)` — tool does NOT execute
- [ ] System errors return generic message — no stack traces or connection strings exposed
- [ ] `ToolResult.source_refs` contains entity IDs used (for future hallucination detection)
- [ ] `backend/tests/test_output_validator.py` covers all 4 error types + success path
- [ ] All existing tests pass (tool_executor tests may need updates to expect new return type)

---

## Risks

- **Breaking change to agent loop.** The agent loop in `agent.py` currently expects string tool results. Must update the tool result → message conversion to handle typed envelopes.
- **Entity ID field detection may be imperfect.** Some tools pass entity references in nested structures (e.g., `{"plate_maps": [{"id": "..."}]}`). Start with top-level `*_id` fields; expand later.
- **Retry mechanism adds latency.** One retry = one extra LLM round trip (~2-3s). Acceptable for correctness.
