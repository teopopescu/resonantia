# SPEC: Data Export Endpoints

**ID:** P3.2
**Phase:** 3 — Design Partner Hardening
**Branch:** `feat/data-export`
**Priority:** P2
**Effort:** 3 days
**Dependencies:** P3.1 (audit log)

---

## Problem Statement

Enterprise procurement requires data portability — partners won't adopt without an exit strategy. Currently only ELN has PDF export and worklists have CSV. Need bulk export for all major entities.

---

## Scope

### In Scope
- CSV export for: samples, experiments, plate maps, audit log
- PDF export for ELN entries (enhance existing)
- All exports scoped by org_id

### Out of Scope
- XLSX export (CSV is sufficient for design partners)
- Full database dump
- Import from other systems (Phase 3.4 handles eLabFTW)

---

## Architecture

```
GET /api/v1/export/samples?format=csv         → CSV of all samples
GET /api/v1/export/experiments?format=csv      → CSV of experiments + results
GET /api/v1/export/eln/{entry_id}?format=pdf   → PDF of single ELN entry
GET /api/v1/export/audit?format=csv&from=&to=  → CSV of audit events
GET /api/v1/export/plates/{plate_id}?format=csv → CSV of well mappings
```

---

## Acceptance Criteria

- [ ] CSV exports include headers and correct data types
- [ ] PDF ELN export renders markdown content with embedded plot images
- [ ] All exports scoped by org_id (cannot export other org's data)
- [ ] Export endpoints return `Content-Disposition: attachment; filename=...`
- [ ] Audit export supports date range filtering
- [ ] Frontend has export buttons on samples, experiments, and ELN pages
