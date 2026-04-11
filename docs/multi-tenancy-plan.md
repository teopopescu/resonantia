# Multi-Tenancy & Conversation History — Implementation Plan

## Context

Resonantia Lab needs two things:
1. **Conversation history per user** — chat conversations persisted to PostgreSQL, not lost on restart
2. **Multi-tenancy** — data isolation per organization for when we sell to multiple companies

These are connected: conversations belong to a user, who belongs to an organization. Building them together avoids a migration later.

---

## Phase 1: Conversation History (per user)

### New Model: `Conversation`

```
conversations table:
- id (UUID PK)
- clerk_user_id (String, indexed) — who owns this conversation
- org_id (String, indexed) — which org this belongs to (added in Phase 2)
- title (String) — auto-generated from first message or user-set
- created_at, updated_at

conversation_messages table:
- id (UUID PK)
- conversation_id (FK → conversations)
- role (String: user | assistant | tool)
- content (Text) — message text
- tool_calls (JSON, nullable) — tool calls made by assistant
- tool_call_id (String, nullable) — for tool result messages
- token_usage (JSON, nullable) — {input, output}
- created_at
```

### Changes

**Backend:**
- New models: `Conversation`, `ConversationMessage`
- New API: `GET /api/v1/chat/conversations` (list user's conversations), `GET /api/v1/chat/conversations/{id}` (get messages), `DELETE /api/v1/chat/conversations/{id}`
- Update `agent.py`: replace in-memory `_conversations` dict with DB reads/writes
- Each message persisted immediately after LLM response
- Conversation title auto-generated from first user message (first 50 chars)

**Frontend:**
- Task panel (left sidebar) becomes the conversation list — replace demo tasks with real conversations
- Click a conversation → loads its messages in the chat area
- "New Task" button → "New Chat" — starts a fresh conversation
- Conversation history persists across page reloads and sessions

### User Identification
- Extract `clerk_user_id` from the request — either via Clerk's backend SDK (`auth()`) or pass it from the frontend
- For now: frontend sends `clerk_user_id` in the request body (simple)
- Later: verify via Clerk JWT on the backend (secure)

---

## Phase 2: Organization-Based Multi-Tenancy

### Approach: Row-Level Isolation with `org_id`

Every data table gets an `org_id` column (String, indexed). All queries filter by `org_id` automatically.

### Database Changes

Add `org_id` column to ALL existing tables:

| Table | Current Rows | Change |
|---|---|---|
| `samples` | 16 | Add `org_id` (String, indexed, not null with default) |
| `plate_maps` | 3 | Add `org_id` |
| `experiments` | 3 | Add `org_id` |
| `microscopy_images` | 0 | Add `org_id` |
| `eln_entries` | 1+ | Add `org_id` |
| `eln_appendices` | 0 | Inherits from parent entry |
| `protocols` | 2 | Add `org_id` |
| `protocol_steps` | 10+ | Inherits from parent protocol |
| `user_profiles` | 1+ | Add `org_id` |
| `conversations` | new | Add `org_id` |
| `conversation_messages` | new | Inherits from parent conversation |

### Org ID Source: Clerk Organizations

Clerk has built-in Organizations:
- Each user belongs to one or more organizations
- `orgId` is available in the session/JWT
- Users can switch active organization

### Query Filtering

Create a FastAPI dependency that extracts `org_id` from the request and injects it into all queries:

```python
# Dependency
async def get_org_context(request: Request) -> str:
    # Extract from header (set by frontend from Clerk session)
    org_id = request.headers.get("X-Org-Id", "default")
    return org_id

# Usage in every endpoint
@router.get("/")
async def list_samples(
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Sample).where(Sample.org_id == org_id)
    ...
```

### Agentic Tool Queries

All tool handlers in `tool_executor.py` must also filter by `org_id`. Pass it through the agent context:

```python
# In agent.py chat():
result = await execute_tool(tool_name, tool_input, org_id=org_id)

# In tool_executor.py:
async def execute_tool(tool_name, tool_input, org_id="default"):
    handler = TOOL_HANDLERS[tool_name]
    return await handler(tool_input, org_id)

# Each handler:
async def _lookup_sample(params, org_id="default"):
    stmt = select(Sample).where(Sample.org_id == org_id, ...)
```

---

## Phase 3: Invite Flow Changes

### Current Flow
1. Admin clicks Invite → enters email
2. Calls `POST /api/invite` → Clerk `createInvitation()`
3. User signs up → lands in /lab → sees all data

### New Flow with Orgs
1. First user signs up → onboarding asks "Name your workspace" → creates Clerk Organization
2. Admin clicks Invite → enters email
3. Calls Clerk `createOrganizationInvitation()` instead of `createInvitation()`
4. User signs up → auto-joins the org → only sees that org's data
5. If user is invited to multiple orgs, they can switch between them

### Frontend Changes
- Onboarding Step 1 (new): "Name your workspace" → calls `clerk.createOrganization()`
- Invite page: changes from app invite to org invite
- Add org switcher in sidebar (if user belongs to multiple orgs) — use Clerk's `<OrganizationSwitcher />`
- All API calls include `X-Org-Id` header from Clerk's `useOrganization()` hook

### Clerk Configuration
- Enable Organizations in Clerk Dashboard (Settings → Organizations)
- Set "Require organization" so every user must belong to one
- The Clerk `<OrganizationSwitcher />` component handles the UI

---

## Phase 4: Data Migration

For existing data (created before multi-tenancy):

1. Create a default org: `org_default`
2. Backfill all existing rows: `UPDATE samples SET org_id = 'org_default' WHERE org_id IS NULL`
3. Add NOT NULL constraint after backfill
4. Seed data gets the org_id of the first user to sign up

### Migration Strategy
- Use Alembic for schema migrations
- Migration 1: Add `org_id` column as nullable with default `'org_default'`
- Migration 2: Backfill existing data
- Migration 3: Set NOT NULL constraint
- Run on deploy, before app starts

---

## Implementation Order

```
Phase 1 (2-3 days): Conversation History
├── Conversation + ConversationMessage models
├── API endpoints for conversation CRUD
├── Wire agent.py to persist conversations in DB
├── Update frontend task panel → conversation list
└── Test: messages survive backend restart

Phase 2 (3-4 days): Row-Level Isolation
├── Add org_id to all tables (Alembic migration)
├── Create get_org_context dependency
├── Update ALL API endpoints to filter by org_id
├── Update ALL tool handlers to filter by org_id
├── Backfill existing data
└── Test: two orgs see different data

Phase 3 (2-3 days): Invite + Org Flow
├── Enable Clerk Organizations
├── Update onboarding: "Name your workspace" step
├── Update invite page: org invitation
├── Add org switcher to sidebar
├── Frontend sends X-Org-Id header on all requests
└── Test: invite → join org → see org data only

Phase 4 (1 day): Migration + Cleanup
├── Alembic migration scripts
├── Backfill script for existing data
├── Remove old in-memory conversation store
└── End-to-end test
```

---

## Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Multi-tenancy model | Row-level isolation (`org_id` column) | Simple, single DB, standard for early SaaS |
| Org provider | Clerk Organizations | Already using Clerk for auth; native org support |
| Conversation storage | PostgreSQL (not Redis) | Persistence, queryability, joins with other data |
| Org ID format | Clerk org ID string (e.g. `org_2abc123`) | Direct from Clerk, no mapping needed |
| Query filtering | FastAPI dependency injection | Single place to enforce, hard to forget |
| Migration | Alembic | Standard SQLAlchemy migration tool, already in deps |

---

## Security Considerations

- **Every query must filter by org_id** — a missed filter leaks data between orgs
- **Tool executor is the riskiest area** — 20+ handlers that each open their own DB session
- **Mitigation**: create a `scoped_session(org_id)` helper that auto-applies the filter
- **Testing**: add a test that queries with wrong org_id return zero results
- **Clerk JWT verification on backend** (Phase 3): don't trust client-sent org_id; verify from JWT
