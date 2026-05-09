# SPEC: Deployment Finalization

**ID:** P5.2
**Phase:** 5 — Paid Pilot Preparation
**Branch:** `feat/deploy-finalize`
**Priority:** P3
**Effort:** 4 days
**Dependencies:** All previous phases

---

## Problem Statement

Production deployment requires final hardening: Terraform configuration validation, error tracking, SSL/TLS verification, and a runbook for common operations. This is the "last mile" before design partners go live on a production URL.

---

## Scope

### In Scope
- Terraform config finalization (build on merged PR #12)
- Sentry error tracking integration
- SSL/TLS verification for api.resonantia.io
- Rate limiting production tuning
- Operational runbook document
- Production checklist verification

### Out of Scope
- Multi-region deployment
- Auto-scaling
- Disaster recovery plan (post-seed)

---

## Architecture

### Sentry Integration

```python
# backend/src/resonantia/main.py
import sentry_sdk

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    environment=settings.environment,  # "production" | "staging" | "development"
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
)
```

### Production Checklist

```
[ ] Backend health check returns 200 on production URL
[ ] Frontend loads on production domain
[ ] Clerk auth works with production keys
[ ] Chat returns real LLM responses
[ ] Voice mode works (Whisper STT + TTS)
[ ] File upload/download works
[ ] Conversation history persists across sessions
[ ] Multi-tenancy: two orgs see different data
[ ] Temporal workflows execute (or graceful fallback)
[ ] Langfuse traces appear
[ ] Sentry captures a test error
[ ] HTTPS enforced
[ ] CORS configured for production domain only
[ ] Rate limiting active
[ ] Database backups verified
[ ] Alembic migrations run clean
```

---

## Acceptance Criteria

- [ ] `terraform plan` shows no errors for production configuration
- [ ] Sentry captures backend errors with stack traces and context
- [ ] Production URL serves HTTPS with valid certificate
- [ ] Rate limiting enforced in production (verified by test)
- [ ] Operational runbook covers: deploy, rollback, DB migration, log access, incident response
- [ ] Production checklist passes (all items checked)
- [ ] Sentry alerts configured for: unhandled exceptions, high error rate
