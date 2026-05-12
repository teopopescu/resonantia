"""General-purpose file upload / download endpoints."""

from __future__ import annotations

import csv
import io
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
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


# ---------------------------------------------------------------------------
# CSV parsing response schema
# ---------------------------------------------------------------------------

class CSVParseResponse(BaseModel):
    file_id: str
    filename: str
    columns: list[str]
    row_count: int
    column_types: dict[str, str]
    preview_rows: list[dict[str, Any]]
    detected_format: str


def _ensure_upload_dir() -> str:
    settings = get_settings()
    upload_dir = os.path.join(settings.upload_dir, "files")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def _build_download_url(file_id: str) -> str:
    return f"/api/v1/files/{file_id}/download"


# ---------------------------------------------------------------------------
# CSV column type detection
# ---------------------------------------------------------------------------

_DATE_PATTERNS = [
    re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    re.compile(r"^\d{2}/\d{2}/\d{4}$"),
    re.compile(r"^\d{4}-\d{2}-\d{2}T"),
]


def _detect_column_type(values: list[str]) -> str:
    """Heuristic column type detection: integer, numeric, date, or string."""
    non_empty = [v.strip() for v in values if v.strip()]
    if not non_empty:
        return "string"

    # Check integer
    int_count = 0
    for v in non_empty:
        try:
            int(v)
            int_count += 1
        except ValueError:
            break
    if int_count == len(non_empty):
        return "integer"

    # Check numeric (float)
    num_count = 0
    for v in non_empty:
        try:
            float(v)
            num_count += 1
        except ValueError:
            break
    if num_count == len(non_empty):
        return "numeric"

    # Check date
    date_count = 0
    for v in non_empty:
        if any(p.match(v) for p in _DATE_PATTERNS):
            date_count += 1
        else:
            break
    if date_count == len(non_empty):
        return "date"

    return "string"


def _detect_format(columns: list[str]) -> str:
    """Heuristic format detection based on column names."""
    lower = {c.lower() for c in columns}

    # dose-response: needs concentration-like + response-like columns
    conc_kw = {"concentration", "conc", "dose", "concentration_nm", "concentration_um"}
    resp_kw = {"response", "response_%", "response_pct", "viability", "inhibition", "activity"}
    if lower & conc_kw and lower & resp_kw:
        return "dose_response"

    # plate reader
    if any("well" in c for c in lower) and any("value" in c or "reading" in c for c in lower):
        return "plate_reader"

    # qPCR — match standalone "ct" or "cq" columns, not substrings like "response_pct"
    qpcr_kw = {"ct", "cq", "ct_value", "cq_value", "ct_mean", "cq_mean"}
    if lower & qpcr_kw or any(c.startswith("ct_") or c.startswith("cq_") for c in lower):
        return "qpcr"

    return "tabular"


def _parse_csv(content: bytes, filename: str) -> dict[str, Any]:
    """Parse CSV content and return structured metadata."""
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)

    if not rows:
        return {
            "columns": [],
            "row_count": 0,
            "column_types": {},
            "preview_rows": [],
            "detected_format": "empty",
        }

    columns = rows[0]
    data_rows = rows[1:]

    # Transpose to get per-column value lists
    col_values: dict[str, list[str]] = {col: [] for col in columns}
    for row in data_rows:
        for i, col in enumerate(columns):
            if i < len(row):
                col_values[col].append(row[i])

    column_types = {col: _detect_column_type(vals) for col, vals in col_values.items()}

    preview = []
    for row in data_rows[:5]:
        entry = {}
        for i, col in enumerate(columns):
            entry[col] = row[i] if i < len(row) else ""
        preview.append(entry)

    return {
        "columns": columns,
        "row_count": len(data_rows),
        "column_types": column_types,
        "preview_rows": preview,
        "detected_format": _detect_format(columns),
    }


# ---------------------------------------------------------------------------
# POST /upload  --  accept one or more files via multipart/form-data
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


# ---------------------------------------------------------------------------
# POST /upload-and-parse  --  upload CSV, parse structure, persist metadata
# ---------------------------------------------------------------------------
@router.post("/upload-and-parse", response_model=CSVParseResponse, status_code=201)
async def upload_and_parse(
    file: UploadFile = File(...),
    org_id: str = Depends(get_org_context),
) -> CSVParseResponse:
    filename = file.filename or "upload.csv"
    content_type = file.content_type or "text/csv"

    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted by this endpoint")

    contents = await file.read()

    # Save via storage abstraction
    from resonantia.services.storage import get_storage

    storage = get_storage()
    file_id = str(uuid.uuid4())
    storage_path = f"csv/{file_id}.csv"
    await storage.save(storage_path, contents, content_type)

    # Parse CSV
    parsed = _parse_csv(contents, filename)

    # Persist to FileUpload DB model (best-effort; DB may not be available in tests)
    db_persisted = False
    try:
        from resonantia.db.session import async_session_factory
        from resonantia.models.file_upload import FileUpload

        async with async_session_factory() as session:
            upload_record = FileUpload(
                id=uuid.UUID(file_id),
                org_id=org_id,
                filename=filename,
                content_type=content_type,
                size_bytes=len(contents),
                storage_path=storage_path,
                parsed_metadata=parsed,
            )
            session.add(upload_record)
            await session.commit()
            db_persisted = True
    except Exception:
        # In test/dev without DB, still keep the in-memory registry
        pass

    # Also track in legacy in-memory registry for backward compat
    _file_registry[file_id] = {
        "id": file_id,
        "filename": filename,
        "size": len(contents),
        "content_type": content_type,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "download_url": _build_download_url(file_id),
        "stored_path": str(Path(get_settings().upload_dir) / storage_path),
        "org_id": org_id,
    }

    return CSVParseResponse(
        file_id=file_id,
        filename=filename,
        columns=parsed["columns"],
        row_count=parsed["row_count"],
        column_types=parsed["column_types"],
        preview_rows=parsed["preview_rows"],
        detected_format=parsed["detected_format"],
    )


# ---------------------------------------------------------------------------
# GET /serve/{path:path}  --  serve stored files (plots, CSVs, etc.)
# ---------------------------------------------------------------------------
@router.get("/serve/{path:path}")
async def serve_file(path: str) -> Response:
    """Serve a file from the storage backend."""
    from resonantia.services.storage import get_storage

    storage = get_storage()
    try:
        content = await storage.load(path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")

    # Infer content type from extension
    ext = Path(path).suffix.lower()
    content_type_map = {
        ".csv": "text/csv",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".json": "application/json",
        ".txt": "text/plain",
        ".pdf": "application/pdf",
    }
    ct = content_type_map.get(ext, "application/octet-stream")

    return Response(content=content, media_type=ct)


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
# GET /  --  list all uploaded files in the caller's org
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
# GET /{file_id}  --  file metadata
# ---------------------------------------------------------------------------
@router.get("/{file_id}", response_model=FileMetadata)
async def get_file_metadata(
    file_id: str,
    org_id: str = Depends(get_org_context),
) -> FileMetadata:
    meta = _get_meta_or_404(file_id, org_id)
    return FileMetadata(**_strip_internal(meta))


# ---------------------------------------------------------------------------
# GET /{file_id}/download  --  serve the actual file bytes
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
# DELETE /{file_id}  --  remove file from storage and registry
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
