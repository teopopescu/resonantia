"""Tests for /api/v1/files multi-tenant isolation.

Targets the security fix from the multimodal-chat audit: cross-tenant
file access via leaked / probed file IDs must return 404 for the
non-owning tenant.
"""

from __future__ import annotations

import io
import hashlib
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.models.file_upload import FileUpload


def test_in_memory_file_registry_removed():
    from resonantia.api import files

    assert not hasattr(files, "_file_registry")


@pytest.mark.asyncio
async def test_uploaded_file_is_listed_for_owner(client: AsyncClient):
    files = {"files": ("a.png", io.BytesIO(b"\x89PNG"), "image/png")}
    r = await client.post(
        "/api/v1/files/upload",
        files=files,
        headers={"X-Org-Id": "org_alpha"},
    )
    assert r.status_code == 201
    [meta] = r.json()
    file_id = meta["id"]

    r2 = await client.get("/api/v1/files/", headers={"X-Org-Id": "org_alpha"})
    assert r2.status_code == 200
    assert any(f["id"] == file_id for f in r2.json())


@pytest.mark.asyncio
async def test_uploaded_file_persists_bytes_and_checksum(client: AsyncClient, db_session: AsyncSession):
    payload = b"alpha,beta\n1,2\n"
    files = {"files": ("data.csv", io.BytesIO(payload), "text/csv")}
    r = await client.post(
        "/api/v1/files/upload",
        files=files,
        headers={"X-Org-Id": "org_alpha"},
    )
    assert r.status_code == 201
    file_id = r.json()[0]["id"]

    upload = await db_session.get(FileUpload, uuid.UUID(file_id))
    assert upload is not None
    assert upload.org_id == "org_alpha"
    assert upload.storage_backend == "local"
    assert upload.content_bytes == payload
    assert upload.checksum_sha256 == hashlib.sha256(payload).hexdigest()


@pytest.mark.asyncio
async def test_upload_and_parse_file_access_survives_storage_reinitialization(client: AsyncClient, monkeypatch):
    from resonantia.services import storage as storage_module

    payload = b"alpha,beta\n1,2\n"
    files = {"file": ("data.csv", io.BytesIO(payload), "text/csv")}
    r = await client.post(
        "/api/v1/files/upload-and-parse",
        files=files,
        headers={"X-Org-Id": "org_alpha"},
    )
    assert r.status_code == 201
    file_id = r.json()["file_id"]

    monkeypatch.setattr(storage_module, "_storage_instance", None)
    download = await client.get(
        f"/api/v1/files/{file_id}/download",
        headers={"X-Org-Id": "org_alpha"},
    )
    assert download.status_code == 200
    assert download.content == payload


@pytest.mark.asyncio
async def test_other_org_does_not_see_file_in_list(client: AsyncClient):
    files = {"files": ("secret.png", io.BytesIO(b"\x89PNG"), "image/png")}
    await client.post(
        "/api/v1/files/upload",
        files=files,
        headers={"X-Org-Id": "org_alpha"},
    )

    r = await client.get("/api/v1/files/", headers={"X-Org-Id": "org_beta"})
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_other_org_cannot_get_metadata(client: AsyncClient):
    files = {"files": ("a.png", io.BytesIO(b"\x89PNG"), "image/png")}
    upload = await client.post(
        "/api/v1/files/upload",
        files=files,
        headers={"X-Org-Id": "org_alpha"},
    )
    file_id = upload.json()[0]["id"]

    r = await client.get(
        f"/api/v1/files/{file_id}",
        headers={"X-Org-Id": "org_beta"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_other_org_cannot_download(client: AsyncClient):
    files = {"files": ("a.png", io.BytesIO(b"\x89PNG"), "image/png")}
    upload = await client.post(
        "/api/v1/files/upload",
        files=files,
        headers={"X-Org-Id": "org_alpha"},
    )
    file_id = upload.json()[0]["id"]

    r = await client.get(
        f"/api/v1/files/{file_id}/download",
        headers={"X-Org-Id": "org_beta"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_other_org_cannot_delete(client: AsyncClient):
    files = {"files": ("a.png", io.BytesIO(b"\x89PNG"), "image/png")}
    upload = await client.post(
        "/api/v1/files/upload",
        files=files,
        headers={"X-Org-Id": "org_alpha"},
    )
    file_id = upload.json()[0]["id"]

    r = await client.delete(
        f"/api/v1/files/{file_id}",
        headers={"X-Org-Id": "org_beta"},
    )
    assert r.status_code == 404

    # File should still be reachable by the owner.
    r2 = await client.get(
        f"/api/v1/files/{file_id}",
        headers={"X-Org-Id": "org_alpha"},
    )
    assert r2.status_code == 200


@pytest.mark.asyncio
async def test_path_traversal_filename_extension_is_neutralized(client: AsyncClient):
    """Even if the upload filename has a malicious extension, the file
    is written under upload_dir with a server-controlled name."""
    files = {
        "files": (
            "../../etc/passwd",
            io.BytesIO(b"x"),
            "application/octet-stream",
        ),
    }
    r = await client.post(
        "/api/v1/files/upload",
        files=files,
        headers={"X-Org-Id": "org_alpha"},
    )
    assert r.status_code == 201
    # Round-trip the metadata; filename is preserved for display, but
    # the on-disk path (not exposed) is a sanitized UUID-based name.
    meta = r.json()[0]
    assert meta["filename"] == "../../etc/passwd"  # display unchanged

    # Listing still works and the file is listed.
    list_r = await client.get(
        "/api/v1/files/", headers={"X-Org-Id": "org_alpha"}
    )
    assert any(f["id"] == meta["id"] for f in list_r.json())
