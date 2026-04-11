"""FastAPI application entry point for Resonantia."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from resonantia.api.router import api_router
from resonantia.config import get_settings
from resonantia.db.session import close_db, init_db

logger = logging.getLogger("resonantia")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown lifecycle."""
    settings = get_settings()
    logger.info("Starting Resonantia backend (debug=%s)", settings.debug)

    # Create tables for local dev; in production use Alembic migrations.
    await init_db()

    # Seed demo data on first run (empty database)
    try:
        from resonantia.db.session import async_session_factory
        from resonantia.seed import seed_if_empty

        async with async_session_factory() as session:
            await seed_if_empty(session)
    except Exception as exc:
        logger.warning("Could not seed demo data: %s", exc)

    # Seed default agentic tools into Redis
    try:
        from resonantia.services.tool_registry import seed_default_tools

        await seed_default_tools()
        logger.info("Tool registry seeded successfully")
    except Exception as exc:
        logger.warning("Could not seed tool registry (Redis may be unavailable): %s", exc)

    yield

    # Cleanup Redis connection pool
    try:
        from resonantia.services.tool_registry import close_redis

        await close_redis()
    except Exception:
        pass

    # Shutdown Langfuse tracing
    try:
        from resonantia.services.tracing import shutdown_langfuse

        shutdown_langfuse()
    except Exception:
        pass

    await close_db()
    logger.info("Resonantia backend shut down.")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Agentic OS for Lab Informatics",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(api_router)

    # Health check
    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "resonantia"}

    return app


app = create_app()
