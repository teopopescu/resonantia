# SPEC: Usage Metering + Stripe Billing

**ID:** P5.1
**Phase:** 5 — Paid Pilot Preparation
**Branch:** `feat/usage-metering`
**Priority:** P3
**Effort:** 5 days
**Dependencies:** Phase 3 complete

---

## Problem Statement

Converting design partners to paid pilots requires billing infrastructure. Need usage tracking (what they consumed) and Stripe integration (how they pay). Pricing: Team $500/mo, Lab $2K/mo, Enterprise $5K+/mo.

---

## Scope

### In Scope
- Usage tracking: LLM tokens, tool executions, storage used per org per month
- Usage dashboard in org settings
- Stripe Checkout integration for Team and Lab tiers
- Subscription management (upgrade, cancel)

### Out of Scope
- Usage-based billing (flat monthly tiers for now)
- Enterprise custom pricing (manual invoicing)
- Metered billing (per-token charges — defer)

---

## Architecture

### Usage Model

```python
class UsageRecord(Base):
    __tablename__ = "usage_records"
    
    org_id: Mapped[str]
    period: Mapped[str]  # "2026-05"
    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)
    tool_executions: Mapped[int] = mapped_column(default=0)
    storage_bytes: Mapped[int] = mapped_column(default=0)
    conversations: Mapped[int] = mapped_column(default=0)
```

### Stripe Integration

```python
# POST /api/v1/billing/checkout — creates Stripe Checkout session
# POST /api/v1/billing/webhook — handles Stripe webhook events
# GET /api/v1/billing/subscription — returns current subscription status
# GET /api/v1/billing/usage — returns current period usage
```

---

## Acceptance Criteria

- [ ] Per-org usage tracked: tokens, tool executions, storage, conversations
- [ ] Usage dashboard shows current month breakdown
- [ ] Stripe Checkout works for Team ($500/mo) and Lab ($2K/mo) tiers
- [ ] Subscription status visible in org settings
- [ ] Cancel subscription → access reverts to free tier at period end
- [ ] Stripe webhook handles: checkout.session.completed, customer.subscription.updated/deleted
- [ ] Usage counters increment correctly (not double-counted)
