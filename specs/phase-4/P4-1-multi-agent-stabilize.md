# SPEC: Multi-Agent Provider + Safety Hardening

**ID:** P4.1
**Phase:** 4 — Multi-Agent + Observability
**Branch:** `feat/multi-agent-stabilize`
**Priority:** P3
**Effort:** 4 days
**Dependencies:** P0.1 (provider abstraction)

---

## Problem Statement

Multi-agent topology (orchestrator + 5 specialists + critic) was merged from PR #9, built on the split-brain infrastructure. After P0.1 unifies the provider, the multi-agent code needs to be stabilized: all specialists must use the provider interface, per-agent model assignment must come from config, and Langfuse must trace individual specialist calls.

---

## Scope

### In Scope
- All specialists use provider interface (no direct SDK imports)
- Per-agent model assignment from config
- Langfuse span per specialist call
- Critic agent validates against source data (ToolResult.source_refs)
- Routing logic validation (correct specialist for each query type)

### Out of Scope
- New specialists
- Agent-to-agent communication protocol (ACP)
- Embedding-based routing (use keyword + intent for now)

---

## Acceptance Criteria

- [ ] All specialist agents import from `services/llm/provider.py`, not SDKs directly
- [ ] Per-agent model assignment via config (`specialist_model`, `critic_model`)
- [ ] Langfuse shows per-specialist spans (orchestrator → specialist → critic)
- [ ] Critic catches fabricated data in >80% of test cases (source_ref validation)
- [ ] Complex query (dose-response analysis) routes to data analyst specialist
- [ ] Simple query (sample lookup) routes to general agent (no specialist overhead)
- [ ] Latency < 15s for single-specialist queries
- [ ] Multi-agent path can be disabled via config flag (fallback to single agent)
