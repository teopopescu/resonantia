# SPEC: First Integration (eLabFTW Sync)

**ID:** P3.4
**Phase:** 3 — Design Partner Hardening
**Branch:** `feat/elabftw-integration`
**Priority:** P2
**Effort:** 4-5 days
**Dependencies:** Phase 0 complete

---

## Problem Statement

Design partners use existing ELN systems (eLabFTW is common in academic and mid-size biotech labs). Resonantia must sync experiment records to their existing system — not replace it. "Resonantia is the system of action; Benchling/eLabFTW is the system of record."

An eLabFTW client exists (`services/integrations/elabftw.py`) but is a stub. Need full bidirectional experiment sync.

---

## Scope

### In Scope
- Push ELN entries from Resonantia → eLabFTW
- Pull experiments from eLabFTW → Resonantia (import)
- Configuration: eLabFTW instance URL + API key in org settings
- Agent tool: `sync_to_elabftw` for one-click sync
- Idempotent sync (re-running doesn't duplicate)

### Out of Scope
- Real-time sync (push on save — use manual sync trigger)
- Benchling integration (different API, different spec)
- Dotmatics integration (stub only)
- File attachment sync (text content only for now)

---

## Architecture

### Sync Flow

```
Resonantia ELN Entry → eLabFTW Experiment
  - title → experiment title
  - content_markdown → experiment body (rendered HTML)
  - tags → experiment tags
  - status (draft/submitted) → experiment status
  - embedded_figures → attachments (file upload)
  
Mapping stored in: eln_entries.external_refs = { "elabftw": { "id": 123, "synced_at": "..." } }
```

### API

```
POST /api/v1/integrations/elabftw/sync/{eln_entry_id}  → Push one entry
GET /api/v1/integrations/elabftw/experiments             → List remote experiments
POST /api/v1/integrations/elabftw/import/{remote_id}     → Import one experiment
```

---

## Acceptance Criteria

- [ ] ELN entry synced to eLabFTW appears as experiment in eLabFTW
- [ ] Sync is idempotent (re-sync updates, doesn't duplicate)
- [ ] eLabFTW instance URL + API key configurable in org settings
- [ ] Agent tool `sync_to_elabftw` works from chat
- [ ] Authentication error shows clear message (not 500)
- [ ] Synced entries tracked via `external_refs` field
- [ ] Import from eLabFTW creates Resonantia ELN entry with attribution
