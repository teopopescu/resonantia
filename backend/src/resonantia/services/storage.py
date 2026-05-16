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
from typing import Any

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


class S3Storage(StorageBackend):
    """Store files in S3 and serve them through pre-signed URLs."""

    def __init__(
        self,
        *,
        bucket: str | None = None,
        region: str | None = None,
        prefix: str | None = None,
        expires_seconds: int | None = None,
        client: Any | None = None,
    ) -> None:
        settings = get_settings()
        self.bucket = bucket or settings.s3_bucket
        self.region = region or settings.s3_region
        self.prefix = (prefix if prefix is not None else settings.s3_prefix).strip("/")
        self.expires_seconds = expires_seconds or settings.s3_signed_url_expires_seconds
        if not self.bucket:
            raise RuntimeError("S3 storage requires S3_BUCKET")
        if client is None:
            try:
                import boto3
            except ImportError as exc:
                raise RuntimeError("S3 storage requires boto3") from exc
            client = boto3.client("s3", region_name=self.region)
        self._client = client

    def _key(self, path: str) -> str:
        clean = path.lstrip("/")
        return f"{self.prefix}/{clean}" if self.prefix else clean

    async def save(self, path: str, content: bytes, content_type: str) -> str:
        self._client.put_object(
            Bucket=self.bucket,
            Key=self._key(path),
            Body=content,
            ContentType=content_type,
            ServerSideEncryption="AES256",
        )
        return self.url(path)

    async def load(self, path: str) -> bytes:
        response = self._client.get_object(Bucket=self.bucket, Key=self._key(path))
        return response["Body"].read()

    async def delete(self, path: str) -> None:
        self._client.delete_object(Bucket=self.bucket, Key=self._key(path))

    def url(self, path: str) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": self._key(path)},
            ExpiresIn=self.expires_seconds,
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_storage_instances: dict[str, StorageBackend] = {}
_storage_instance: StorageBackend | None = None


def _storage_cache_key(selected: str) -> str:
    settings = get_settings()
    if selected == "local":
        return f"local:{Path(settings.upload_dir).resolve()}"
    if selected == "s3":
        return "s3:{bucket}:{region}:{prefix}:{expires}".format(
            bucket=settings.s3_bucket,
            region=settings.s3_region,
            prefix=settings.s3_prefix,
            expires=settings.s3_signed_url_expires_seconds,
        )
    return selected


def get_storage(backend: str | None = None) -> StorageBackend:
    """Return a singleton storage backend."""
    global _storage_instance
    settings = get_settings()
    selected = (backend or settings.storage_backend or "local").lower()
    if selected == "s3" and not settings.s3_bucket:
        selected = "local"
    if backend is None and _storage_instance is not None:
        return _storage_instance
    cache_key = _storage_cache_key(selected)
    if cache_key not in _storage_instances:
        _storage_instances[cache_key] = S3Storage() if selected == "s3" else LocalStorage()
    if backend is None:
        _storage_instance = _storage_instances[cache_key]
    return _storage_instances[cache_key]


def choose_storage_backend(size_bytes: int) -> str:
    """Use S3 for large files when S3 storage is configured."""
    settings = get_settings()
    if settings.storage_backend.lower() == "s3" and settings.s3_bucket and size_bytes >= 5 * 1024 * 1024:
        return "s3"
    return "local"


def is_signed_url(url: str) -> bool:
    return url.startswith(("http://", "https://"))
