# Production Runbook

Last updated: 2026-05-16

## Deploy

1. Confirm CI is green: backend tests, frontend tests/build, Docker config, and
   Docker image builds.
2. Confirm secrets are present in the target environment or secret manager.
3. Run database migrations:

   ```bash
   cd backend
   uv run alembic upgrade head
   ```

4. Deploy API, Temporal worker, and frontend images.
5. Verify health checks:

   - Backend `/health`
   - Frontend home/lab route
   - Temporal worker connected to the configured task queue
   - Redis reachable
   - Postgres reachable

## Rollback

1. Identify the last known-good image tag.
2. Redeploy API and worker services to that tag.
3. If a migration caused the issue, review the migration downgrade and restore
   from backup if downgrade is unsafe.
4. Confirm `/health`, login, chat, upload, and worker smoke checks.

## Secret Rotation

Rotate any credential that was committed, shared outside the secret manager, or
suspected of exposure.

Minimum rotation set:

- OpenAI
- Anthropic
- Clerk
- Contentful
- Langfuse
- Database credentials
- Redis auth if enabled
- AWS credentials or role trust policies

After rotation, update the environment/secret manager and restart affected
services.

## Incident Triage

1. Check API 5xx and latency dashboards.
2. Check Temporal workflow failures and worker restarts.
3. Check provider errors and rate limits.
4. Check database saturation and connection pool errors.
5. Check Redis connectivity.
6. Check storage errors and signed URL failures.
7. Record the timeline, customer impact, mitigation, and follow-up tasks.

## Required Alerts

- API 5xx rate above threshold
- API p95 latency regression
- Backend/worker crash loop
- Temporal workflow failure spike
- Postgres CPU, storage, and connection saturation
- Redis unavailable
- LLM provider error/rate-limit spike
- Storage upload/download failure spike
