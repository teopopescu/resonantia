"""Shared pytest fixtures for Resonantia backend tests."""

from __future__ import annotations

import os
import sys
import types
import uuid
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi import Request
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# ---------------------------------------------------------------------------
# Set env vars before any resonantia imports
# ---------------------------------------------------------------------------
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost/test"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["CLERK_SECRET_KEY"] = "test-clerk"

# ---------------------------------------------------------------------------
# Test-only SQLite engine (created before touching the production db module)
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
_test_session_factory = async_sessionmaker(
    _test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ---------------------------------------------------------------------------
# Now import resonantia modules.  The db.session module will create its own
# Postgres engine at import time, but we never actually *use* it — we
# override the get_db dependency in every integration test.
# ---------------------------------------------------------------------------
from resonantia.models.base import Base  # noqa: E402


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create all tables, yield a session, then drop everything."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with _test_session_factory() as session:
        yield session

    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ---------------------------------------------------------------------------
# FastAPI test client — overrides DB dependency + skips lifespan
# (lifespan tries to connect to Postgres/Redis which are unavailable)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTPX async client wired to the FastAPI app with test DB."""
    from contextlib import asynccontextmanager
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    from resonantia.api.router import api_router
    from resonantia.config import get_settings
    from resonantia.db.session import get_db
    from resonantia.dependencies import get_org_context, get_request_context
    from resonantia.models.request_context import RequestContext

    settings = get_settings()

    # Build a minimal app with a no-op lifespan (skip Postgres init + Redis seed)
    @asynccontextmanager
    async def _noop_lifespan(app: FastAPI):
        yield

    app = FastAPI(title="test", lifespan=_noop_lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "resonantia"}

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def _override_request_context(request: Request) -> RequestContext:
        org_id = request.headers.get("X-Org-Id", "org_default")
        return RequestContext(
            user_id="test-user",
            org_id=org_id,
            roles=["org:admin"],
            permissions=[],
            request_id="test-request",
        )

    async def _override_org_context(request: Request) -> str:
        return request.headers.get("X-Org-Id", "org_default")

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_request_context] = _override_request_context
    app.dependency_overrides[get_org_context] = _override_org_context

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
