# Resonantia

Execution layer for lab automation: Resonantia turns experiment intent into
validated plate maps, liquid-handler worklists, assay results, and auditable
run records.

## Architecture

| Layer | Stack |
| --- | --- |
| Frontend | Next.js 16, React 19, TypeScript, Zustand, Tailwind |
| Backend | FastAPI, SQLAlchemy async, Pydantic, Alembic |
| Data | PostgreSQL, Redis, local/S3 file storage |
| Workflows | Temporal API service + Temporal worker |
| AI providers | OpenAI or Anthropic for chat; OpenAI for voice STT/TTS |
| Auth | Clerk |
| Observability | OpenTelemetry hooks, Langfuse tracing |

## Local Docker Run

```bash
cp .env.example .env
# Edit .env and add provider/auth keys as needed.
docker compose up --build
```

Local URLs:

| Service | URL |
| --- | --- |
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Temporal UI | http://localhost:8080 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

For OpenAI chat:

```env
DEFAULT_PROVIDER=openai
OPENAI_API_KEY=<your-openai-api-key>
```

For Anthropic chat:

```env
DEFAULT_PROVIDER=anthropic
ANTHROPIC_API_KEY=<your-anthropic-api-key>
```

Voice mode always requires `OPENAI_API_KEY` because STT/TTS use OpenAI.

## Local Development

Backend:

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn resonantia.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

When running without Docker, provide PostgreSQL, Redis, and Temporal yourself if
you need workflow-backed paths. In development, the backend can create local
tables for convenience; production must use Alembic migrations.

## Tests and Validation

Backend:

```bash
cd backend
uv run pytest tests/ -q
```

Frontend:

```bash
cd frontend
npm test -- --run
npm run build
```

Docker/config:

```bash
docker compose config
docker compose build backend temporal-worker frontend
```

Migrations:

```bash
cd backend
uv run alembic upgrade head
```

## Environment

Start from [.env.example](.env.example). Important local variables:

| Variable | Purpose |
| --- | --- |
| `APP_ENVIRONMENT` | `development`, `staging`, or `production` |
| `DEFAULT_PROVIDER` | `openai` or `anthropic` |
| `OPENAI_API_KEY` | OpenAI chat and voice STT/TTS |
| `ANTHROPIC_API_KEY` | Anthropic chat |
| `CLERK_SECRET_KEY` | Backend auth verification |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Frontend Clerk app |
| `NEXT_PUBLIC_DEMO_MODE` | Enables frontend demo data when `true` |
| `NEXT_PUBLIC_AUTO_DEMO_ON_API_FAILURE` | Local-only automatic demo fallback |

Production startup fails fast when required production configuration is missing.
Do not commit real provider, Clerk, Contentful, Langfuse, database, or AWS
credentials.

## Production Readiness

The current readiness work is tracked in
[docs/production-readiness-implementation-plan.md](docs/production-readiness-implementation-plan.md).
That document captures blockers, cleanup work, acceptance criteria, and the
remaining launch checklist.

## Project Structure

```text
backend/                 FastAPI app, SQLAlchemy models, Alembic, pytest
frontend/                Next.js app, lab UI, Vitest tests
docs/                    Architecture, plans, runbooks, readiness notes
docker-compose.yml       Local Postgres, Redis, Temporal, backend, worker, frontend
.github/workflows/       CI, Docker build, deployment workflows
```
