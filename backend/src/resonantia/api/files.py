"""General-purpose file upload / download endpoints."""

from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from resonantia.config import get_settings
from resonantia.dependencies import get_org_context

router = APIRouter()

# Whitelist of file extensions accepted by upload. Anything else is
# normalized to a safe extension on disk; the original filename is
# preserved separately in the registry.
_SAFE_EXT_RE = re.compile(r"^\.[A-Za-z0-9]{1,8}$")

# ---------------------------------------------------------------------------
# In-memory file registry (keyed by file-id).  A production version would
# persist this to Postgres, but for the prototype an in-process dict is fine
# because the upload_dir already provides durable storage.
# ---------------------------------------------------------------------------

_file_registry: dict[str, dict[str, Any]] = {}


class FileMetadata(BaseModel):
    id: str
    filename: str
    size: int
    content_type: str
    uploaded_at: str
    download_url: str


def _ensure_upload_dir() -> str:
    settings = get_settings()
    upload_dir = os.path.join(settings.upload_dir, "files")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def _build_download_url(file_id: str) -> str:
    return f"/api/v1/files/{file_id}/download"


# ---------------------------------------------------------------------------
# POST /upload  –  accept one or more files via multipart/form-data
# ---------------------------------------------------------------------------
@router.post("/upload", response_model=list[FileMetadata], status_code=201)
async def upload_files(
    files: list[UploadFile] = File(...),
    org_id: str = Depends(get_org_context),
) -> list[FileMetadata]:
    upload_dir = _ensure_upload_dir()
    upload_dir_real = os.path.realpath(upload_dir)
    results: list[FileMetadata] = []

    for f in files:
        file_id = str(uuid.uuid4())
        # Normalize the extension: only accept short alphanumeric. Anything
        # else (path traversal, NUL bytes, multi-dot, etc.) is dropped so
        # the on-disk name is fully derived from server-controlled values.
        raw_ext = os.path.splitext(f.filename or "")[1]
        ext = raw_ext if _SAFE_EXT_RE.match(raw_ext) else ""
        stored_name = f"{file_id}{ext}"
        dest_path = os.path.join(upload_dir, stored_name)

        # Defense in depth: refuse to write outside upload_dir even
        # though the components above are now safe.
        dest_real = os.path.realpath(dest_path)
        if os.path.commonpath([upload_dir_real, dest_real]) != upload_dir_real:
            raise HTTPException(status_code=400, detail="Invalid file path")

        contents = await f.read()
        with open(dest_path, "wb") as fp:
            fp.write(contents)

        meta: dict[str, Any] = {
            "id": file_id,
            "filename": f.filename or "file",
            "size": len(contents),
            "content_type": f.content_type or "application/octet-stream",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "download_url": _build_download_url(file_id),
            "stored_path": dest_path,
            "org_id": org_id,
        }
        _file_registry[file_id] = meta
        results.append(FileMetadata(**{k: v for k, v in meta.items()
                                       if k not in ("stored_path", "org_id")}))

    return results


def _strip_internal(meta: dict[str, Any]) -> dict[str, Any]:
    """Remove server-only fields before returning metadata to clients."""
    return {k: v for k, v in meta.items() if k not in ("stored_path", "org_id")}


def _get_meta_or_404(file_id: str, org_id: str) -> dict[str, Any]:
    """Look up a file and enforce org_id ownership.

    Returns 404 (not 403) on cross-tenant access so the existence of a
    file ID in another tenant cannot be probed.
    """
    meta = _file_registry.get(file_id)
    if not meta or meta.get("org_id") != org_id:
        raise HTTPException(status_code=404, detail="File not found")
    return meta


# ---------------------------------------------------------------------------
# GET /  –  list all uploaded files in the caller's org
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[FileMetadata])
async def list_files(
    org_id: str = Depends(get_org_context),
) -> list[FileMetadata]:
    return [
        FileMetadata(**_strip_internal(m))
        for m in _file_registry.values()
        if m.get("org_id") == org_id
    ]


# ---------------------------------------------------------------------------
# GET /{file_id}  –  file metadata
# ---------------------------------------------------------------------------
@router.get("/{file_id}", response_model=FileMetadata)
async def get_file_metadata(
    file_id: str,
    org_id: str = Depends(get_org_context),
) -> FileMetadata:
    meta = _get_meta_or_404(file_id, org_id)
    return FileMetadata(**_strip_internal(meta))


# ---------------------------------------------------------------------------
# GET /{file_id}/download  –  serve the actual file bytes
# ---------------------------------------------------------------------------
@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    org_id: str = Depends(get_org_context),
) -> FileResponse:
    meta = _get_meta_or_404(file_id, org_id)
    path = meta["stored_path"]
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File missing from storage")
    return FileResponse(
        path,
        media_type=meta["content_type"],
        filename=meta["filename"],
    )


# ---------------------------------------------------------------------------
# DELETE /{file_id}  –  remove file from storage and registry
# ---------------------------------------------------------------------------
@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: str,
    org_id: str = Depends(get_org_context),
) -> None:
    meta = _get_meta_or_404(file_id, org_id)
    _file_registry.pop(file_id, None)
    path = meta["stored_path"]
    if os.path.exists(path):
        os.remove(path)
