"""Storage abstraction layer.

Provides a pluggable backend for storing and serving files (CSVs, plots,
worklists, etc.).  The ``LocalStorage`` implementation writes to the local
filesystem and serves via the FastAPI ``/api/v1/files/serve/`` route.

Future implementations (e.g. S3Storage) implement the same
``StorageBackend`` interface so the rest of the application never cares
*where* files live.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

from resonantia.config import get_settings

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract interface every storage backend must implement."""

    @abstractmethod
    async def save(self, path: str, content: bytes, content_type: str) -> str:
        """Persist *content* at *path* and return an access URL."""

    @abstractmethod
    async def load(self, path: str) -> bytes:
        """Load raw bytes from *path*."""

    async def delete(self, path: str) -> None:
        """Delete stored bytes at *path* if present."""

    @abstractmethod
    def url(self, path: str) -> str:
        """Return a URL (relative or signed) for *path*."""


class LocalStorage(StorageBackend):
    """Store files on the local filesystem under *base_dir*."""

    def __init__(self, base_dir: str | None = None) -> None:
        if base_dir is None:
            base_dir = get_settings().upload_dir
        self.base_dir = Path(base_dir)

    async def save(self, path: str, content: bytes, content_type: str) -> str:
        full_path = self.base_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        logger.debug("Saved %d bytes to %s", len(content), full_path)
        return self.url(path)

    async def load(self, path: str) -> bytes:
        full_path = self.base_dir / path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")
        return full_path.read_bytes()

    async def delete(self, path: str) -> None:
        full_path = self.base_dir / path
        if full_path.exists():
            full_path.unlink()

    def url(self, path: str) -> str:
        return f"/api/v1/files/serve/{path}"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_storage_instance: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """Return the singleton storage backend (``LocalStorage`` for now)."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = LocalStorage()
    return _storage_instance
