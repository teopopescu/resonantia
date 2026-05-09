# SPEC: Docs Sync + Langfuse Wiring

**ID:** P0.6
**Phase:** 0 — Stabilize
**Branch:** `docs/sync-and-observability`
**Priority:** P0 (last in phase)
**Effort:** 2 days
**Dependencies:** All other P0 PRs

---

## Problem Statement

Documentation describes an architecture that no longer exists (pre-refactor state). Tool counts are wrong. The production plan references features as "demo-only" that are now wired. Langfuse tracing needs verification across all agent paths after the provider abstraction.

---

## Scope

### In Scope
- Update architecture docs to match post-P0 state
- Update tool count references
- Verify Langfuse traces work for: single-agent, multi-agent, Temporal, direct mode
- Update README with current test counts and setup instructions

### Out of Scope
- Writing new architectural decision records
- Langfuse dashboard creation (Phase 4)
- Marketing copy updates

---

## Implementation

1. Update `docs/architecture.md`: reflect provider abstraction, safe Temporal, output guardrails
2. Update `docs/tools.md`: match actual tools in `TOOL_HANDLERS` (likely 33)
3. Update `docs/production-plan.md`: remove stale "simulation/dummy" items that are now real
4. Update `README.md`: test count, architecture diagram description, quickstart
5. Verify Langfuse: send a test chat message through each path, confirm traces appear with model/tokens/latency

---

## Acceptance Criteria

- [ ] Every file path mentioned in `docs/` exists in the codebase
- [ ] Tool count in docs matches `len(TOOL_HANDLERS)` in tool_executor.py
- [ ] `docs/architecture.md` describes the provider abstraction and safe Temporal workflow
- [ ] `README.md` test counts match actual (`uv run pytest --co -q | tail -1` and `npm test -- --reporter=verbose 2>&1 | grep "Tests"`)
- [ ] Langfuse dashboard shows traces for a chat message sent via Temporal path
- [ ] Langfuse dashboard shows traces for a chat message sent via direct path
- [ ] Langfuse traces include: model name, provider, input_tokens, output_tokens, latency_ms
