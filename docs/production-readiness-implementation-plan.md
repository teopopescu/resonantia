# Production Readiness Findings and Implementation Plan

Last updated: 2026-05-16

This document captures the post-Phase 6 readiness audit. The implementation
plan is complete at the PR checklist level, but the repository is not yet ready
for customer-facing production use.

## Current Verdict

Resonantia is suitable for local development, internal demos, and staging once
environment variables are configured. It is not yet production-ready for a
startup with external users because the deploy path, secret hygiene, migration
strategy, and full regression suite still have blocking gaps.

Implementation note: this document is the source plan. The concrete launch gate
checklist lives in `docs/production-launch-checklist.md`, and operational
procedures live in `docs/runbook.md`.

## Findings

### P0 Blockers

| Finding | Evidence | Required Outcome |
| --- | --- | --- |
| Real-looking secrets are present in local env/config files | `.env`-style files and Compose had concrete provider/auth tokens | Remove committed secrets, rotate exposed credentials, and use environment variables or a secret manager |
| Full backend regression suite is not green | `466 passed, 4 skipped, 2 failed` | Full backend suite must pass before launch |
| Deploy workflow references a missing worker Dockerfile | `.github/workflows/deploy.yml` uses `backend/Dockerfile.worker`, but only `backend/Dockerfile` exists | Deploy workflow must build valid API and worker images |
| Database migrations are not production-grade | Migration files exist, but standard Alembic wiring was not present; startup uses `Base.metadata.create_all` | Add runnable Alembic config and make migrations the production schema path |
| Provider env wiring is inconsistent | Backend defaults to Anthropic while Compose only passed OpenAI | Compose, docs, and settings must agree on `DEFAULT_PROVIDER` and provider keys |

## Implementation Status

Completed in this production-readiness pass:

- Compose now passes `APP_ENVIRONMENT`, `DEMO_MODE`, `DEFAULT_PROVIDER`,
  `OPENAI_API_KEY`, and `ANTHROPIC_API_KEY` to backend and worker services.
- Hardcoded frontend Clerk and Contentful values were removed from Compose.
- `.env.example` now documents safe placeholders for local provider, auth,
  observability, demo-mode, and frontend settings.
- Backend production startup validates required configuration and refuses
  production demo mode.
- Production startup no longer runs automatic `Base.metadata.create_all`; use
  Alembic migrations instead.
- Alembic runtime wiring was added with `backend/alembic.ini` and
  `backend/alembic/env.py`.
- Backend Docker images now include Alembic files.
- The deploy workflow no longer references a missing `backend/Dockerfile.worker`.
- Storage caching was corrected so test/runtime upload directories are respected.
- Frontend demo/mock fallbacks are gated behind explicit demo mode instead of
  silently appearing in production mode.
- Clerk, Axios, Next, and PostCSS dependency advisories were remediated or
  overridden to audited patched versions.
- CI now runs backend migrations, frontend dependency audit, Docker Compose
  validation, and API/worker/frontend image builds.
- Current local validation results are recorded in
  `docs/production-launch-checklist.md`.

Still external/manual before launch:

- Rotate any credentials that may have appeared in prior committed files or
  shared local env files.
- Run the staging smoke test with real Clerk, provider, Temporal, Redis,
  Postgres, and storage credentials.
- Configure production dashboards, alert routing, backups, and incident owners.

### P1 Production Gaps

| Area | Gap | Required Outcome |
| --- | --- | --- |
| Documentation | Root/backend docs are stale and do not match current architecture, providers, or test counts | Accurate local, staging, and production runbooks |
| Demo behavior | Demo/mock/synthetic fallbacks remain in product paths | Demo paths must be gated by explicit demo mode and disabled in production |
| Observability | OpenTelemetry exists in code, but production collector, dashboards, and alert routing need verification | Request, Temporal, LLM, and storage paths observable with alerts |
| Auth and tenancy | Clerk/JWT and tenant isolation need deployed end-to-end validation | Production auth flow verified against real Clerk app and tenant boundaries |
| Storage | Local storage works for development; S3 signed URL and retention paths need staging validation | Production storage backend validated with retention cleanup |
| Operations | Backups, restore drills, incident runbooks, and smoke tests need formalization | Documented and tested operating procedures |

## Plan 1: Missing Parts for Production Readiness

### PR 1: Production Configuration Contract

- Define required environment variables for local, staging, and production.
- Add explicit `DEFAULT_PROVIDER` handling across Compose, deployment, and docs.
- Separate chat provider requirements from voice STT/TTS requirements.
- Remove any hardcoded provider, Clerk, Contentful, Langfuse, or app secrets from committed config.
- Add a startup validation path that reports missing required production env vars.

Acceptance criteria:

- `docker compose config` succeeds with placeholders.
- Production config fails fast when required env vars are missing.
- Local config can run with either `DEFAULT_PROVIDER=openai` or `DEFAULT_PROVIDER=anthropic`.

### PR 2: Production Database Migrations

- Add `backend/alembic.ini`.
- Add `backend/alembic/env.py`.
- Ensure existing migration files are discoverable by Alembic.
- Copy Alembic files into Docker images.
- Add migration commands to docs and CI.
- Keep `create_all` only for explicit local/demo fallback, not production startup.

Acceptance criteria:

- `uv run alembic upgrade head` works from `backend/`.
- Docker image contains migration files.
- Production startup does not mutate schema through `Base.metadata.create_all`.

### PR 3: Deployment Pipeline Repair

- Either add `backend/Dockerfile.worker` or update the deploy workflow to reuse
  `backend/Dockerfile` with a worker command override.
- Add CI checks for API image build, worker image build, and frontend image build.
- Validate deployment workflow references existing files.

Acceptance criteria:

- GitHub deploy workflow no longer references missing files.
- API, worker, and frontend images build from a clean checkout.

### PR 4: Production Observability and Runbooks

- Verify OpenTelemetry exporter configuration in staging.
- Add or document dashboards for HTTP errors, latency, worker failures, LLM errors,
  storage errors, Redis/Postgres health, and Temporal workflow failures.
- Add alert routing.
- Add incident and rollback runbooks.

Acceptance criteria:

- A staged request can be traced across API and worker where applicable.
- Alerts exist for API 5xx, worker crash loops, DB saturation, and queue/workflow failures.
- Runbooks exist for deploy, rollback, secret rotation, and incident response.

### PR 5: Production Validation Pass

- Run a staging smoke test covering login, chat, tool execution, uploads, voice,
  Temporal worker activity, and retention cleanup.
- Validate tenant isolation against real auth tokens.
- Validate S3 storage and signed URLs if production storage is enabled.
- Record results in a launch checklist.

Acceptance criteria:

- Launch checklist is complete.
- No P0 production blockers remain.

## Plan 2: Cleanup Work

### PR 1: Secrets and Environment Cleanup

- Remove committed env files containing real-looking secrets.
- Replace hardcoded Docker Compose frontend tokens with `${...}` variables.
- Expand `.env.example` with all local keys and safe placeholders.
- Document which keys are optional, local-only, or required for production.
- Rotate any credentials that may have been committed.

Acceptance criteria:

- No real-looking API keys or service tokens remain in tracked config.
- `.env.example` is sufficient to prepare a local `.env`.

### PR 2: Documentation Refresh

- Rewrite the root README to match the current architecture.
- Replace the incorrect backend README content.
- Add current commands for backend tests, frontend tests, Docker, and local services.
- Document provider setup for OpenAI and Anthropic.
- Document Temporal, Redis, Postgres, Clerk, Contentful, Langfuse, and voice requirements.

Acceptance criteria:

- A new developer can run the project locally from the docs.
- Test counts and architecture descriptions match the current repo.

### PR 3: Demo Mode Audit

- Inventory all frontend and backend mock/demo/synthetic paths.
- Gate demo data behind explicit `DEMO_MODE` or frontend equivalent.
- Ensure production mode fails closed instead of silently falling back to demo data.
- Add tests for production-mode behavior.

Acceptance criteria:

- Demo paths cannot appear in production mode.
- Production missing-data states show actionable errors rather than mock data.

### PR 4: CI Cleanup

- Ensure CI runs full backend tests, frontend tests, frontend build, and Docker config validation.
- Add image build checks for API, worker, and frontend.
- Add dependency/security scanning where practical.

Acceptance criteria:

- CI catches the current classes of issues: failing backend tests, broken compose,
  missing Dockerfile references, and frontend build regressions.

## Plan 3: Blocker Fix Plan

### Blocker 1: Fix Backend Test Failures

Scope:

- `tests/test_dose_response.py::TestFitDoseResponseFull::test_full_fit_plot_file_exists`
- `tests/test_retention.py::test_cleanup_expired_voice_audio_deletes_old_files`

Likely fixes:

- Make plot output respect the test-configured upload/output directory.
- Remove storage singleton leakage across tests or add a supported reset path.
- Ensure retention cleanup uses the active storage base directory.

Acceptance criteria:

- `cd backend && uv run pytest tests/ -q` passes.
- Any storage/config singleton changes include targeted regression tests.

### Blocker 2: Fix Worker Deployment Image

Scope:

- `.github/workflows/deploy.yml`
- Backend Dockerfile strategy

Likely fixes:

- Prefer one backend image with different runtime commands for API and worker,
  unless the worker needs a truly separate image.
- If keeping separate images, add `backend/Dockerfile.worker` and test it in CI.

Acceptance criteria:

- Deploy workflow references existing files only.
- API and worker image builds pass in CI.

### Blocker 3: Add Alembic Runtime Wiring

Scope:

- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/Dockerfile`
- deployment/runbook docs

Likely fixes:

- Configure Alembic with app metadata and async database URL support.
- Copy `alembic/` and `alembic.ini` into Docker images.
- Add migration command to deployment docs.

Acceptance criteria:

- `uv run alembic upgrade head` works locally.
- Migration command works inside the backend Docker image.

### Blocker 4: Align Provider Configuration

Scope:

- `docker-compose.yml`
- `.env.example`
- README/runbook docs

Likely fixes:

- Add `DEFAULT_PROVIDER`, `ANTHROPIC_API_KEY`, and `OPENAI_API_KEY` to backend
  and worker Compose environments.
- Set local default to OpenAI in `.env.example` because voice already requires OpenAI.
- Document Anthropic as an alternate chat provider.

Acceptance criteria:

- Local chat can run with `DEFAULT_PROVIDER=openai` and `OPENAI_API_KEY`.
- Anthropic chat can run with `DEFAULT_PROVIDER=anthropic` and `ANTHROPIC_API_KEY`.
- Voice mode documents its independent OpenAI requirement.

### Blocker 5: Remove and Rotate Secrets

Scope:

- Tracked config files
- Local developer env files
- External provider dashboards

Required actions:

- Remove secrets from tracked files.
- Rotate exposed Clerk, Contentful, OpenAI, Anthropic, Langfuse, and any other
  committed credentials.
- Prefer secret manager references in production.

Acceptance criteria:

- Secret scan passes.
- Rotated credentials are confirmed active only in intended environments.

## Local API Key Guidance

For Docker Compose, place local keys in a root `.env` file next to
`docker-compose.yml`:

```bash
DEFAULT_PROVIDER=openai
OPENAI_API_KEY=<your-openai-api-key>
ANTHROPIC_API_KEY=
```

For Anthropic chat instead:

```bash
DEFAULT_PROVIDER=anthropic
ANTHROPIC_API_KEY=<your-anthropic-api-key>
OPENAI_API_KEY=
```

Voice mode uses OpenAI STT/TTS and requires `OPENAI_API_KEY` even when chat uses
Anthropic.
