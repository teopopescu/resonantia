# SPEC: Production Infrastructure Basics

**ID:** P3.5
**Phase:** 3 — Design Partner Hardening
**Branch:** `feat/prod-infra-basics`
**Priority:** P2
**Effort:** 3 days
**Dependencies:** Phase 0 complete

---

## Problem Statement

Design partners need a stable deployment — not just features. Health checks, database migrations, rate limiting, and CORS config are prerequisites, not nice-to-haves. Codex review flagged these as missing from the first plan iteration.

---

## Scope

### In Scope
- Granular health check endpoints
- Alembic migration chain (clean from empty DB)
- Rate limiting on chat endpoint
- CORS production configuration

### Out of Scope
- SSL/TLS (Vercel handles frontend; ALB handles backend)
- Sentry integration (Phase 5)
- Advanced monitoring/alerting (Phase 4 — Langfuse)

---

## Architecture

### Health Checks

```python
GET /health           → { "status": "ok" }  # existing
GET /health/db        → { "status": "ok", "latency_ms": 2 }  # test DB query
GET /health/redis     → { "status": "ok", "latency_ms": 1 }  # test Redis ping
GET /health/temporal  → { "status": "ok" } or { "status": "degraded", "fallback": "direct" }
```

### Rate Limiting

```python
# 10 requests/second per org for chat endpoint (LLM calls are expensive)
# 100 requests/second per org for read endpoints
# Using slowapi or custom middleware with Redis counter
```

### Alembic Migration

```
alembic/
  versions/
    001_initial_schema.py      # All tables: samples, experiments, plates, etc.
    002_add_audit_events.py    # Audit log table (Phase 3.1)
    003_add_file_uploads.py    # File upload tracking (Phase 1.1)
    004_add_org_members.py     # Role-based membership (Phase 3.3)
```

---

## Acceptance Criteria

- [ ] `GET /health/db` returns status + latency (or error if DB unreachable)
- [ ] `GET /health/redis` returns status + latency
- [ ] `GET /health/temporal` returns status (ok or degraded with fallback mode)
- [ ] `alembic upgrade head` runs cleanly from empty database
- [ ] `alembic downgrade base` followed by `upgrade head` runs cleanly (reversible)
- [ ] Chat endpoint rate limited: 11th request in 1 second from same org returns 429
- [ ] Read endpoints rate limited: 101st request in 1 second returns 429
- [ ] CORS allows production frontend domain
- [ ] CORS blocks unknown origins
- [ ] All health checks return within 5 seconds (or timeout with error)
