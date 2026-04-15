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


async def _ensure_org_id_columns(conn) -> None:
    """Add org_id column to any table that's missing it.

    SQLAlchemy's create_all only creates new tables — it won't ALTER
    existing ones to add new columns.  This ensures org_id (required
    for multi-tenancy) is present even on tables created before the
    column was added to the models.
    """
    from sqlalchemy import text

    tables_needing_org_id = [
        "experiments",
        "plate_maps",
        "samples",
        "microscopy_images",
        "eln_entries",
        "protocols",
        "user_profiles",
        # conversations already had org_id from the start
        "conversations",
    ]

    for table in tables_needing_org_id:
        # Check if the table exists and whether it has org_id
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = :table AND column_name = 'org_id'"
        ), {"table": table})
        if result.fetchone() is None:
            # Table exists but org_id is missing — add it
            table_exists = await conn.execute(text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_name = :table AND table_schema = 'public'"
            ), {"table": table})
            if table_exists.fetchone() is not None:
                await conn.execute(text(
                    f'ALTER TABLE {table} ADD COLUMN org_id VARCHAR(255) DEFAULT \'org_default\''
                ))
                await conn.execute(text(
                    f'CREATE INDEX IF NOT EXISTS ix_{table}_org_id ON {table} (org_id)'
                ))
                logger.info("Added org_id column to %s", table)


async def init_db() -> None:
    """Create all tables and ensure schema is up to date.

    Falls back to SQLite if Postgres is unreachable.
    """
    global engine, async_session_factory

    from resonantia.models.base import Base

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # Ensure org_id columns exist on tables created before multi-tenancy
            if not settings.database_url.startswith("sqlite"):
                await _ensure_org_id_columns(conn)
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
