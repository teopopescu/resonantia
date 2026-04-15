Deployment checklist for Resonantia. Run through each step and report status.

## Pre-deploy checks

1. **Run backend tests:**
```bash
cd /Users/teopopescu/Desktop/resonantia/backend && uv run pytest tests/ -v --tb=short 2>&1 | tail -20
```

2. **Run frontend tests:**
```bash
cd /Users/teopopescu/Desktop/resonantia/frontend && npx vitest run 2>&1 | tail -20
```

3. **Lint backend:**
```bash
cd /Users/teopopescu/Desktop/resonantia/backend && uv run ruff check src/ 2>&1 | tail -10
```

4. **Check for uncommitted changes:**
```bash
git status
```

5. **Check Docker builds:**
```bash
docker compose build 2>&1 | tail -10
```

## Deploy steps (confirm with user before each)

6. **Build and push containers** (if using registry)
7. **Run database migrations:** `docker exec resonantia-backend-1 python -m alembic upgrade head`
8. **Restart services:** `docker compose up -d`
9. **Verify health:** Run /check-lab
10. **Smoke test:** Send a test chat message and verify response

Report a checklist with pass/fail for each step.
