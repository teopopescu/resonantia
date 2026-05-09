# SPEC: Approval Gates (Human-in-the-Loop)

**ID:** P1.0
**Phase:** 1 — Killer Workflow
**Branch:** `feat/approval-gates`
**Priority:** P1 (first in phase — all other Phase 1 PRs depend on this)
**Effort:** 4-5 days
**Dependencies:** Phase 0 complete

---

## Problem Statement

Write tools (`create_eln_entry`, `submit_eln_entry`, `create_plate_map`, `generate_worklist`) execute inline with no user confirmation. The product must feel like an "AI lab operator that behaves like a validated informatics system" — consequential actions require human approval.

Per codex-findings/02 autonomy levels:
- **Level 1 (Ask):** Immediate execution — lookups, calculations
- **Level 2 (Draft):** Show preview, wait for confirmation — creates, drafts
- **Level 3 (Execute With Approval):** Explicit warning + confirmation — submissions, instrument actions

---

## Scope

### In Scope
- Gate classification per tool (none / soft_review / hard_approval)
- Backend: approval token system (tool returns pending state, waits for approval)
- Frontend: approval card component (preview + Confirm/Edit/Cancel)
- Expiry: unconfirmed drafts expire after 10 minutes
- Agent loop: handle "pending approval" state gracefully

### Out of Scope
- Two-person approval (Level 4/5 — defer)
- Temporal workflow signals for approval (use simpler token approach first)
- Approval audit trail (Phase 3 — audit log)

---

## Architecture

### Gate Classification

| Gate | Tools | Behavior |
|------|-------|----------|
| `none` | `lookup_sample`, `query_experiments`, `check_inventory`, `calculate_dilution`, `fit_dose_response`, `normalize_plate`, `calculate_z_prime`, `qpcr_analysis`, `read_file_contents`, `browse_microscopy` | Execute immediately, return result |
| `soft_review` | `create_eln_entry`, `create_plate_map`, `create_protocol`, `serial_dilution`, `cherry_pick`, `propose_follow_up_experiment` | Return draft preview, wait for Confirm (auto-pass after 10 min timeout) |
| `hard_approval` | `submit_eln_entry`, `generate_worklist` (instrument-bound) | Return preview + explicit warning, require Confirm (NO auto-pass) |

### Approval Flow

```
Agent calls tool with gate != none
    → Backend: generate approval_token, store draft in Redis with TTL 600s
    → Return to agent: { pending_approval: true, token: "...", preview: {...} }
    → Agent responds to user: "Here's what I'll do: [preview]. Confirm?"
    → Frontend: renders ApprovalCard component
    
User clicks Confirm:
    → Frontend: POST /api/v1/chat/approve/{token}
    → Backend: load draft from Redis, execute tool, return result
    → Agent receives result, continues conversation
    
User clicks Cancel:
    → Frontend: POST /api/v1/chat/reject/{token}
    → Backend: delete draft from Redis
    → Agent receives cancellation, acknowledges

Timeout (10 min):
    → Redis TTL expires, draft deleted
    → If user tries to approve expired token → 410 Gone
```

### Data Model

```python
# backend/src/resonantia/services/approval.py

class PendingApproval(BaseModel):
    token: str
    tool_name: str
    tool_args: dict
    org_id: str
    user_id: str
    preview: dict  # Human-readable preview of what will happen
    gate_kind: Literal["soft_review", "hard_approval"]
    created_at: datetime
    expires_at: datetime

# Stored in Redis: approval:{token} → PendingApproval JSON, TTL 600s
```

### Frontend Component

```tsx
// frontend/src/components/approval-card.tsx

interface ApprovalCardProps {
  token: string;
  toolName: string;
  preview: Record<string, any>;
  gateKind: 'soft_review' | 'hard_approval';
  onConfirm: () => void;
  onCancel: () => void;
}

// Renders:
// - Tool name and description
// - Preview of the action (ELN content, plate grid, worklist rows)
// - For hard_approval: amber warning banner
// - Confirm button (green) + Cancel button (gray)
// - Countdown timer showing time remaining
```

---

## Implementation

### Step 1: Gate metadata on tools (day 1)
- Add `gate_kind` field to `ToolSchema` model in tool_registry
- Classify all 33 tools into none/soft_review/hard_approval
- Store gate_kind in Redis alongside tool schema

### Step 2: Approval service (day 2)
- Implement `create_pending_approval(tool_name, args, org_id, preview) -> token`
- Implement `approve(token) -> ToolResult` (load from Redis, execute, delete)
- Implement `reject(token)` (delete from Redis)
- Redis key: `approval:{token}`, TTL: 600 seconds

### Step 3: Wire into tool executor (day 2)
- Before executing a gated tool: create pending approval, return special response
- Agent loop recognizes pending_approval response and tells user about the draft

### Step 4: API endpoints (day 3)
- `POST /api/v1/chat/approve/{token}` — executes the pending tool call
- `POST /api/v1/chat/reject/{token}` — cancels the pending tool call
- Auth: verify requesting user matches the user who initiated the tool call

### Step 5: Frontend approval card (day 3-4)
- Build `ApprovalCard` component
- Integrate into chat message rendering (when agent response contains approval token)
- Show preview appropriate to tool type (ELN content as markdown, plate as grid, worklist as table)

### Step 6: Tests (day 4-5)
- Test: L1 tool executes immediately (no approval)
- Test: L2 tool returns pending, approve → executes
- Test: L2 tool returns pending, reject → no execution
- Test: expired token → 410 Gone
- Test: wrong user tries to approve → 403

---

## Expected Behavior

| Scenario | Before | After |
|----------|--------|-------|
| Agent calls `lookup_sample` | Executes, returns data | Same — no gate |
| Agent calls `create_eln_entry` | Executes immediately, entry created | Returns draft preview, waits for Confirm |
| User confirms ELN draft | N/A | Entry created in DB, agent continues |
| User cancels ELN draft | N/A | No entry created, agent acknowledges |
| Agent calls `generate_worklist` | Executes immediately, file generated | Shows preview + warning, requires explicit Confirm |
| 10 minutes pass without action | N/A | Approval expires, token invalid |

---

## Acceptance Criteria

- [ ] All 33 tools classified with `gate_kind` (none/soft_review/hard_approval)
- [ ] L1 tools (gate: none) execute immediately — no behavior change
- [ ] L2 tools (gate: soft_review) return draft preview, wait for user confirmation
- [ ] L3 tools (gate: hard_approval) return preview + explicit warning, wait for confirmation
- [ ] `POST /api/v1/chat/approve/{token}` executes the pending tool and returns result
- [ ] `POST /api/v1/chat/reject/{token}` cancels without execution
- [ ] Expired tokens (>10 min) return 410 Gone
- [ ] Wrong user attempting approval returns 403
- [ ] Frontend renders ApprovalCard with preview, Confirm, Cancel
- [ ] Hard approval cards show amber warning text
- [ ] Test: create_eln_entry → user cancels → no entry in DB
- [ ] Agent loop handles pending_approval response and presents draft to user

---

## Risks

- **Agent loop must understand pending state.** The LLM needs to recognize that a tool returned a "pending" state and tell the user what it's proposing (not just dump the token). This requires a system prompt addition or structured response format.
- **Preview generation differs by tool.** ELN preview is markdown; plate preview is a grid; worklist preview is a table. The approval service must support polymorphic previews.
- **Redis dependency.** If Redis is down, approvals can't be stored. Fallback: reject the tool call and tell user "approval system unavailable."
