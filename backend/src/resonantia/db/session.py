"""Async SQLAlchemy session management.

Falls back to SQLite (aiosqlite) when PostgreSQL is unavailable,
allowing the backend to run locally without Docker.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from resonantia.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

SQLITE_URL = "sqlite+aiosqlite:///./resonantia_dev.db"


def _build_engine(url: str):
    if url.startswith("sqlite"):
        return create_async_engine(url, echo=settings.debug)
    return create_async_engine(
        url,
        echo=settings.debug,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
    )


engine = _build_engine(settings.database_url)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables. Falls back to SQLite if Postgres is unreachable."""
    global engine, async_session_factory

    from resonantia.models.base import Base

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized with %s", settings.database_url)
    except Exception:
        logger.warning(
            "Could not connect to %s — falling back to SQLite (%s)",
            settings.database_url,
            SQLITE_URL,
        )
        engine = _build_engine(SQLITE_URL)
        async_session_factory.configure(bind=engine)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized with SQLite fallback")


async def close_db() -> None:
    await engine.dispose()
