# SPEC: Gate Microscopy Behind Partner Flag

**ID:** P0-CUT-MICRO
**Phase:** 0 — Stabilize
**Branch:** `chore/strip-non-core` (amend or follow-up)
**Priority:** P0
**Effort:** 0.5 day
**Dependencies:** None

---

## Problem Statement

The microscopy browser uses synthetic demo data (`microscopy-demo.ts`). There is no real upload pipeline for microscopy images — no way for design partners to actually bring their data in. Showing this feature by default sets expectations we can't deliver.

Microscopy should only be visible to partners who specifically request it (e.g., Dewpoint with HCI workflows). For all other partners, it's noise that dilutes the core value proposition (dose-response → plate → worklist → ELN).

## Decision

**Partner-triggered only.** Microscopy is not removed from the codebase but is hidden from:
- The `/lab` sidebar navigation (default)
- The landing page features section (default)
- The agent's available tools (default)

It becomes visible when a partner org has `features.microscopy: true` in their org config (or when the workflow template includes microscopy tools — see P4.3).

## Scope

### In Scope
- Hide `/lab/microscopy` from sidebar navigation by default
- Hide microscopy from landing page features grid (or mark as "Coming for imaging labs")
- Gate `browse_microscopy` and `generate_montage` tools behind a feature flag
- Keep the code — do not delete

### Out of Scope
- Building a real microscopy upload pipeline (defer until a partner requests it)
- OMERO integration
- Image analysis / cell counting
- Removing microscopy code from the codebase

---

## Implementation

### Frontend
- In the lab sidebar navigation, conditionally show microscopy link based on org feature flag
- In landing page features grid, either remove microscopy card or label it "Available for imaging labs"

### Backend
- In `tool_executor.py`, gate `browse_microscopy` and `generate_montage` behind an org-level feature flag
- Default: disabled. Enabled per-org in org settings or via workflow template (P4.3)

---

## Acceptance Criteria

- [ ] `/lab/microscopy` not visible in sidebar for new orgs (default)
- [ ] Microscopy tools not offered by agent for default orgs
- [ ] Setting `features.microscopy: true` on an org shows the page and enables tools
- [ ] Landing page does not prominently feature microscopy as a GA capability
- [ ] Microscopy code remains in codebase (not deleted)
- [ ] Existing microscopy tests still pass

---

## Future: Real Microscopy Pipeline (partner-triggered)

When a design partner (e.g., Dewpoint) requests microscopy:
1. Build bulk image upload endpoint (TIFF/PNG, organized by plate/well/channel/FOV)
2. Store images via storage abstraction (local → S3)
3. Generate thumbnails on upload
4. Replace synthetic demo data with real uploaded images
5. Consider OMERO integration for labs that use it

This is NOT in scope for the 6-month roadmap unless a signed partner requires it.
