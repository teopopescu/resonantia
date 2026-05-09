"""Tests for resonantia.services.storage."""

from __future__ import annotations

import os
import tempfile

import pytest

from resonantia.services.storage import LocalStorage, StorageBackend, get_storage


class TestLocalStorage:
    @pytest.fixture
    def tmp_storage(self, tmp_path) -> LocalStorage:
        return LocalStorage(base_dir=str(tmp_path))

    @pytest.mark.asyncio
    async def test_save_creates_file(self, tmp_storage: LocalStorage, tmp_path):
        url = await tmp_storage.save("test/hello.txt", b"hello world", "text/plain")
        assert (tmp_path / "test" / "hello.txt").exists()
        assert (tmp_path / "test" / "hello.txt").read_bytes() == b"hello world"

    @pytest.mark.asyncio
    async def test_save_returns_url(self, tmp_storage: LocalStorage):
        url = await tmp_storage.save("data/file.csv", b"a,b\n1,2", "text/csv")
        assert url == "/api/v1/files/serve/data/file.csv"

    @pytest.mark.asyncio
    async def test_load_reads_file(self, tmp_storage: LocalStorage, tmp_path):
        (tmp_path / "roundtrip.bin").write_bytes(b"\x00\x01\x02")
        data = await tmp_storage.load("roundtrip.bin")
        assert data == b"\x00\x01\x02"

    @pytest.mark.asyncio
    async def test_load_missing_raises(self, tmp_storage: LocalStorage):
        with pytest.raises(FileNotFoundError):
            await tmp_storage.load("does_not_exist.csv")

    def test_url_returns_serve_path(self, tmp_storage: LocalStorage):
        assert tmp_storage.url("plots/abc.png") == "/api/v1/files/serve/plots/abc.png"

    @pytest.mark.asyncio
    async def test_save_creates_nested_dirs(self, tmp_storage: LocalStorage, tmp_path):
        await tmp_storage.save("a/b/c/deep.txt", b"deep", "text/plain")
        assert (tmp_path / "a" / "b" / "c" / "deep.txt").read_bytes() == b"deep"


class TestGetStorage:
    def test_returns_storage_backend(self):
        storage = get_storage()
        assert isinstance(storage, StorageBackend)

    def test_returns_local_storage_instance(self):
        storage = get_storage()
        assert isinstance(storage, LocalStorage)
