# Resonantia Backend

FastAPI backend for Resonantia. It provides REST APIs, agent/tool execution,
file storage, voice endpoints, Temporal workflow activities, SQLAlchemy models,
and Alembic migrations.

## Setup

```bash
uv sync
cp ../.env.example ../.env
```

For local OpenAI chat and voice:

```env
DEFAULT_PROVIDER=openai
OPENAI_API_KEY=<your-openai-api-key>
```

For Anthropic chat:

```env
DEFAULT_PROVIDER=anthropic
ANTHROPIC_API_KEY=<your-anthropic-api-key>
```

## Run Locally

```bash
uv run alembic upgrade head
uv run uvicorn resonantia.main:app --reload
```

The API will be available at `http://localhost:8000`.

## Tests

```bash
uv run pytest tests/ -q
```

## Migrations

Alembic is the production schema path:

```bash
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "describe change"
```

Development startup may create tables for convenience. Production startup does
not create or mutate schema automatically; run migrations before deployment.

## Production Configuration

Set `APP_ENVIRONMENT=production` or `OTEL_ENVIRONMENT=production` to enable
fail-fast validation. Production requires database, Redis, Temporal, Clerk, and
the configured chat provider key. If `STORAGE_BACKEND=s3`, `S3_BUCKET` is also
required.
