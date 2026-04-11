"""General-purpose file upload / download endpoints."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from resonantia.config import get_settings

router = APIRouter()

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
) -> list[FileMetadata]:
    upload_dir = _ensure_upload_dir()
    results: list[FileMetadata] = []

    for f in files:
        file_id = str(uuid.uuid4())
        ext = os.path.splitext(f.filename or "file")[1]
        stored_name = f"{file_id}{ext}"
        dest_path = os.path.join(upload_dir, stored_name)

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
        }
        _file_registry[file_id] = meta
        results.append(FileMetadata(**{k: v for k, v in meta.items() if k != "stored_path"}))

    return results


# ---------------------------------------------------------------------------
# GET /  –  list all uploaded files
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[FileMetadata])
async def list_files() -> list[FileMetadata]:
    return [
        FileMetadata(**{k: v for k, v in m.items() if k != "stored_path"})
        for m in _file_registry.values()
    ]


# ---------------------------------------------------------------------------
# GET /{file_id}  –  file metadata
# ---------------------------------------------------------------------------
@router.get("/{file_id}", response_model=FileMetadata)
async def get_file_metadata(file_id: str) -> FileMetadata:
    meta = _file_registry.get(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="File not found")
    return FileMetadata(**{k: v for k, v in meta.items() if k != "stored_path"})


# ---------------------------------------------------------------------------
# GET /{file_id}/download  –  serve the actual file bytes
# ---------------------------------------------------------------------------
@router.get("/{file_id}/download")
async def download_file(file_id: str) -> FileResponse:
    meta = _file_registry.get(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="File not found")
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
async def delete_file(file_id: str) -> None:
    meta = _file_registry.pop(file_id, None)
    if not meta:
        raise HTTPException(status_code=404, detail="File not found")
    path = meta["stored_path"]
    if os.path.exists(path):
        os.remove(path)
