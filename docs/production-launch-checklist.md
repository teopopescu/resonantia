# Production Launch Checklist

Last updated: 2026-05-16

## P0 Gates

- [x] No real secrets in tracked files or Docker Compose.
- [ ] Exposed credentials rotated.
- [x] Backend full test suite passes.
- [x] Frontend tests and production build pass.
- [x] `docker compose config` passes.
- [x] API, worker, and frontend Docker images build.
- [x] `uv run alembic upgrade head` works from `backend/`.
- [x] Deploy workflow references existing files only.
- [x] Production config fails fast when required env vars are missing.
- [x] Demo mode is disabled in production.

Validated locally on 2026-05-16:

- `cd backend && uv run pytest tests/ -q`: 472 passed, 4 skipped.
- `cd frontend && npm test -- --run`: 53 passed.
- `cd frontend && npm run build`: passed.
- `cd frontend && npm audit --audit-level=moderate`: 0 vulnerabilities.
- `docker compose config`: passed.
- `docker compose build backend temporal-worker frontend`: passed.
- `cd backend && uv run alembic upgrade head`: passed against a fresh local SQLite database.

## Staging Smoke Test

- [ ] Login with the production-equivalent Clerk app.
- [ ] Chat request succeeds with configured provider.
- [ ] At least one tool-backed chat flow succeeds.
- [ ] File upload/download works.
- [ ] Voice transcription and TTS work when `OPENAI_API_KEY` is configured.
- [ ] Temporal worker processes a workflow.
- [ ] Redis-backed tool registry is seeded.
- [ ] Tenant isolation checked with two orgs.
- [ ] Retention cleanup deletes expired voice artifacts.
- [ ] S3 signed URL path works if `STORAGE_BACKEND=s3`.

## Operations

- [ ] Dashboards exist for API, worker, database, Redis, Temporal, provider, and storage health.
- [ ] Alerts route to the on-call owner.
- [ ] Backup and restore process documented.
- [ ] Rollback process tested.
- [ ] Secret rotation process tested.
