# SPEC: Multi-Tenancy Security Fix

**ID:** P0.0
**Phase:** 0 — Stabilize
**Branch:** `fix/tenant-security`
**Priority:** P0 (first, parallel — security blocker)
**Effort:** 3 days
**Dependencies:** None

---

## Problem Statement

Codex code review confirmed three cross-tenant data access vulnerabilities:

1. **Conversation history leak:** `_get_or_create_conversation` in `agent.py:80` loads conversations by UUID without checking `org_id`. Any user who guesses or intercepts a conversation ID can read another org's chat history.

2. **Org impersonation:** `ChatRequest` in `chat.py:71` accepts `org_id` from the request body. A malicious client can set any org_id and interact as that organization.

3. **Tool-level tenant bypass:** `tool_executor.py` file tools use a global `_file_registry` dict without org scoping. `_create_eln_entry` (line 542) loads an Experiment by UUID and uses it before checking `exp.org_id`.

These are security blockers — a design partner could access another partner's data.

---

## Scope

### In Scope
- Fix conversation loading to require org_id match
- Derive org_id from authenticated session (Clerk), not request body
- Scope all tool entity loads by org_id
- Scope file registry by org_id
- Add tenant isolation test suite

### Out of Scope
- Full RBAC (Phase 3)
- Clerk session validation middleware (assumed already in place via `get_org_context`)
- Database-level row-level security (defer)

---

## Architecture

### Current Flow (Broken)
```
Client → POST /api/v1/chat { org_id: "attacker-chosen", message: "..." }
       → chat.py reads org_id from body
       → agent.py loads conversation by UUID (no org check)
       → tool_executor loads entities by UUID (no org check)
```

### Target Flow (Fixed)
```
Client → POST /api/v1/chat { message: "..." }
       → chat.py extracts org_id from get_org_context() (Clerk session + X-Org-Id header, validated)
       → agent.py loads conversation by UUID AND org_id
       → tool_executor loads entities by UUID AND org_id (or returns 403)
```

### Key Design Decisions
- `org_id` is NEVER accepted from request body for chat endpoint
- Every database query that loads by UUID must also filter by org_id
- File registry keyed by `(org_id, file_id)` tuple, not just `file_id`
- Return 403 (not 404) when org_id doesn't match — makes auth failures explicit

---

## Implementation

### 1. Fix chat.py — remove org_id from request body

```python
# backend/src/resonantia/api/chat.py

@router.post("/")
async def chat(
    request: ChatRequest,  # Remove org_id field from ChatRequest schema
    org_context: OrgContext = Depends(get_org_context),  # org_id from auth
    db: AsyncSession = Depends(get_db),
):
    org_id = org_context.org_id  # From Clerk session, not body
    # ... pass org_id to agent
```

### 2. Fix agent.py — add org_id to conversation loading

```python
# backend/src/resonantia/services/agent.py

async def _get_or_create_conversation(
    self, conversation_id: str | None, org_id: str, db: AsyncSession
) -> Conversation:
    if conversation_id:
        conv = await db.get(Conversation, conversation_id)
        if conv is None or conv.org_id != org_id:
            raise HTTPException(status_code=403, detail="Conversation not accessible")
        return conv
    # Create new conversation with org_id
    conv = Conversation(org_id=org_id, ...)
    ...
```

### 3. Fix tool_executor.py — scope entity loads

```python
# For every tool handler that loads an entity by ID:
async def _create_eln_entry(params, org_id, db):
    if params.get("experiment_id"):
        exp = await db.get(Experiment, params["experiment_id"])
        if exp is None or exp.org_id != org_id:
            return {"error": "Experiment not found or not accessible"}
    ...

# Scope file registry
_file_registry: dict[tuple[str, str], FileInfo] = {}  # (org_id, file_id) → FileInfo

def register_file(org_id: str, file_id: str, info: FileInfo):
    _file_registry[(org_id, file_id)] = info

def get_file(org_id: str, file_id: str) -> FileInfo | None:
    return _file_registry.get((org_id, file_id))
```

### 4. Add tenant isolation test suite

```python
# backend/tests/test_tenant_isolation.py

async def test_conversation_cross_tenant_blocked():
    # Create conversation in org_A
    # Try to load it with org_B context → expect 403

async def test_chat_ignores_body_org_id():
    # Send request with org_id in body different from auth context
    # Verify response uses auth org_id, not body org_id

async def test_tool_entity_cross_tenant_blocked():
    # Create experiment in org_A
    # Execute tool referencing that experiment_id from org_B → expect error

async def test_file_registry_scoped():
    # Register file in org_A
    # Try to access from org_B → expect None/error
```

---

## Expected Behavior

| Scenario | Before | After |
|----------|--------|-------|
| User in org_B requests conversation from org_A | Returns conversation content | 403 Forbidden |
| Client sends `{org_id: "fake-org"}` in chat body | Uses fake org_id | Ignores body, uses auth context |
| Tool loads experiment from different org | Returns experiment data | Error: "not found or not accessible" |
| File registered by org_A accessed by org_B | Returns file | Returns None/error |

---

## Acceptance Criteria

- [ ] `ChatRequest` schema no longer accepts `org_id` field (or field is ignored)
- [ ] `chat.py` derives org_id exclusively from `get_org_context()` dependency
- [ ] `_get_or_create_conversation` checks `conv.org_id == org_id` before returning
- [ ] Wrong org_id on conversation load returns HTTP 403
- [ ] `_file_registry` is keyed by `(org_id, file_id)` — cross-org file access impossible
- [ ] Every tool handler that loads an entity by UUID also checks org_id
- [ ] `backend/tests/test_tenant_isolation.py` exists with 4+ test cases
- [ ] All tenant isolation tests pass
- [ ] Existing tests still pass (no regression)

---

## Risks

- Changing `ChatRequest` schema is a breaking API change for the frontend. Frontend must stop sending `org_id` in chat requests. Coordinate with P0.2 (API contracts) or ensure frontend already sends org_id via header.
- Some tool handlers may load multiple entities in a chain (e.g., experiment → plate_maps). Each hop must check org_id.
- Global `_file_registry` is likely used in tests — tests may need updating to pass org_id.
