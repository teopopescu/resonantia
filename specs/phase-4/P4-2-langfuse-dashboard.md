# SPEC: Langfuse Dashboard + Alerting

**ID:** P4.2
**Phase:** 4 — Multi-Agent + Observability
**Branch:** `feat/langfuse-dashboard`
**Priority:** P3
**Effort:** 3 days
**Dependencies:** P4.1

---

## Problem Statement

Need operational visibility into: cost per org (for billing), latency distribution (for SLA), error rate (for reliability), and tool usage (for product analytics). Langfuse tracing exists but metadata is incomplete and there are no dashboards or alerts.

---

## Scope

### In Scope
- Complete trace metadata on every LLM call
- Dashboard queries for key metrics
- Alert thresholds for degraded service

### Out of Scope
- Custom Langfuse dashboard UI (use Langfuse's built-in)
- Real-time streaming dashboards
- Cost attribution to individual users (org-level is sufficient)

---

## Architecture

### Trace Metadata

Every LLM call includes:
```python
{
    "org_id": "org_123",
    "user_id": "user_456",
    "conversation_id": "conv_789",
    "agent_role": "orchestrator|specialist:data_analyst|critic",
    "tool_calls": ["fit_dose_response", "create_eln_entry"],
    "model": "claude-sonnet-4-20250514",
    "provider": "anthropic",
    "input_tokens": 1234,
    "output_tokens": 567,
    "latency_ms": 2340,
    "cost_usd": 0.0089,
}
```

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Latency p95 | > 15s | > 30s |
| Error rate | > 2% | > 5% |
| Cost per org per day | > $50 | > $100 |

---

## Acceptance Criteria

- [ ] Every LLM call has trace with: org_id, conversation_id, model, tokens, latency, cost
- [ ] Multi-agent routing decisions traced (which specialist, why)
- [ ] Langfuse dashboard shows: cost per org, latency p50/p95, error rate, tool usage distribution
- [ ] Alerts configured for latency > 30s and error rate > 5%
- [ ] Tool usage breakdown shows which tools are most used (product analytics)
