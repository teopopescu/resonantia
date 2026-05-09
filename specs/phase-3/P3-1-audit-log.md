# SPEC: Audit Log (Append-Only)

**ID:** P3.1
**Phase:** 3 — Design Partner Hardening
**Branch:** `feat/audit-log`
**Priority:** P2
**Effort:** 4 days
**Dependencies:** Phase 0 complete

---

## Problem Statement

Every consequential action — write tool execution, gate approval, ELN submission — must be recorded for regulatory compliance and partner trust. Scientists need to answer "who did what, when, and why" for any experiment artifact. Currently, only Langfuse traces LLM calls; there is no system-wide activity log for data mutations.

---

## Scope

### In Scope
- Append-only audit_events table
- Middleware that logs all mutating tool executions
- Approval decisions logged (who approved, when)
- Read-only API endpoint for querying audit trail
- Basic audit viewer in frontend settings

### Out of Scope
- Hash chain (tamper detection) — nice-to-have, not required for design partners
- Electronic signatures (21 CFR Part 11 — deferred)
- Audit export to CSV (Phase 3.2 — data export)

---

## Architecture

### Data Model

```python
class AuditEvent(UUIDPrimaryKey, Base):
    __tablename__ = "audit_events"
    
    org_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    action: Mapped[str]  # "create", "update", "delete", "approve", "reject", "submit"
    entity_type: Mapped[str]  # "eln_entry", "plate_map", "sample", "experiment", "worklist"
    entity_id: Mapped[str]
    details: Mapped[dict] = mapped_column(JSON)  # tool_name, args, result summary
    ip_address: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    # NO updated_at — append only
    # NO delete cascade — audit events are permanent
```

### API

```
GET /api/v1/audit?org_id=X&entity_type=eln_entry&limit=50&offset=0
GET /api/v1/audit/{entity_type}/{entity_id}  # All events for one entity
```

### Integration Point

```python
# In tool_executor.py, after successful mutation:
await audit_service.log(
    org_id=org_id,
    user_id=user_id,
    action="create",
    entity_type="eln_entry",
    entity_id=entry.id,
    details={"tool": "create_eln_entry", "title": entry.title}
)
```

---

## Acceptance Criteria

- [ ] `audit_events` table exists with append-only constraint (no UPDATE/DELETE permissions)
- [ ] Every mutating tool execution generates an audit event
- [ ] Approval and rejection decisions generate audit events
- [ ] ELN submission generates an audit event
- [ ] Audit events include: org_id, user_id, action, entity_type, entity_id, timestamp
- [ ] `GET /api/v1/audit` returns events scoped by org_id
- [ ] Frontend audit viewer shows chronological list in settings
- [ ] Audit events cannot be modified or deleted via API
- [ ] Test: create ELN entry → audit event exists with correct details
