"""General-purpose file upload / download endpoints."""

from __future__ import annotations

import csv
import hashlib
import io
import os
import re
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.db.session import get_db
from resonantia.dependencies import get_request_context
from resonantia.models.file_upload import FileUpload
from resonantia.models.request_context import RequestContext
from resonantia.repositories.audit_log import append_audit_log
from resonantia.services.storage import choose_storage_backend, get_storage, is_signed_url

router = APIRouter()

# Whitelist of file extensions accepted by upload. Anything else is
# normalized to a safe extension on disk; the original filename is
# preserved separately in the registry.
_SAFE_EXT_RE = re.compile(r"^\.[A-Za-z0-9]{1,8}$")

INLINE_CONTENT_MAX_BYTES = 5 * 1024 * 1024


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


def _build_download_url(file_id: str) -> str:
    return f"/api/v1/files/{file_id}/download"


def _parse_file_id(file_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="File not found") from None


def _metadata_from_upload(upload: FileUpload) -> FileMetadata:
    return FileMetadata(
        id=str(upload.id),
        filename=upload.filename,
        size=upload.size_bytes,
        content_type=upload.content_type,
        uploaded_at=upload.created_at.isoformat() if upload.created_at else "",
        download_url=_build_download_url(str(upload.id)),
    )


async def _get_upload_or_404(
    db: AsyncSession,
    file_id: str,
    org_id: str,
) -> FileUpload:
    upload = await db.get(FileUpload, _parse_file_id(file_id))
    if not upload or upload.org_id != org_id:
        raise HTTPException(status_code=404, detail="File not found")
    return upload


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
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> list[FileMetadata]:
    if not ctx.can_write():
        raise HTTPException(status_code=403, detail="Member role required to upload files")

    results: list[FileMetadata] = []

    for f in files:
        file_id = str(uuid.uuid4())
        raw_ext = os.path.splitext(f.filename or "")[1]
        ext = raw_ext if _SAFE_EXT_RE.match(raw_ext) else ""
        storage_path = f"files/{file_id}{ext}"
        contents = await f.read()
        content_type = f.content_type or "application/octet-stream"
        storage_backend = choose_storage_backend(len(contents))
        storage = get_storage(storage_backend)
        await storage.save(storage_path, contents, content_type)

        upload_record = FileUpload(
            id=uuid.UUID(file_id),
            org_id=ctx.org_id,
            uploaded_by=ctx.user_id,
            filename=f.filename or "file",
            content_type=content_type,
            size_bytes=len(contents),
            storage_path=storage_path,
            checksum_sha256=hashlib.sha256(contents).hexdigest(),
            storage_backend=storage_backend,
            content_bytes=contents if storage_backend == "local" and len(contents) <= INLINE_CONTENT_MAX_BYTES else None,
        )
        db.add(upload_record)
        await db.flush()
        await append_audit_log(
            db,
            ctx=ctx,
            action="file.upload",
            target_type="file_upload",
            target_id=file_id,
            metadata={
                "filename": upload_record.filename,
                "size": upload_record.size_bytes,
                "content_type": upload_record.content_type,
                "checksum_sha256": upload_record.checksum_sha256,
                "storage_backend": upload_record.storage_backend,
                "storage_path": storage_path,
            },
        )
        results.append(_metadata_from_upload(upload_record))

    return results


# ---------------------------------------------------------------------------
# POST /upload-and-parse  --  upload CSV, parse structure, persist metadata
# ---------------------------------------------------------------------------
@router.post("/upload-and-parse", response_model=CSVParseResponse, status_code=201)
async def upload_and_parse(
    file: UploadFile = File(...),
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> CSVParseResponse:
    if not ctx.can_write():
        raise HTTPException(status_code=403, detail="Member role required to upload files")
    filename = file.filename or "upload.csv"
    content_type = file.content_type or "text/csv"

    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted by this endpoint")

    contents = await file.read()

    storage_backend = choose_storage_backend(len(contents))
    storage = get_storage(storage_backend)
    file_id = str(uuid.uuid4())
    storage_path = f"csv/{file_id}.csv"
    await storage.save(storage_path, contents, content_type)

    # Parse CSV
    parsed = _parse_csv(contents, filename)

    try:
        upload_record = FileUpload(
            id=uuid.UUID(file_id),
            org_id=ctx.org_id,
            uploaded_by=ctx.user_id,
            filename=filename,
            content_type=content_type,
            size_bytes=len(contents),
            storage_path=storage_path,
            checksum_sha256=hashlib.sha256(contents).hexdigest(),
            storage_backend=storage_backend,
            content_bytes=contents if storage_backend == "local" and len(contents) <= INLINE_CONTENT_MAX_BYTES else None,
            detected_format=parsed["detected_format"],
            parsed_metadata=parsed,
        )
        db.add(upload_record)
        await db.flush()
        await append_audit_log(
            db,
            ctx=ctx,
            action="file.upload",
            target_type="file_upload",
            target_id=file_id,
            metadata={
                "filename": filename,
                "size": len(contents),
                "content_type": content_type,
                "checksum_sha256": upload_record.checksum_sha256,
                "storage_backend": upload_record.storage_backend,
                "storage_path": storage_path,
            },
        )
        await append_audit_log(
            db,
            ctx=ctx,
            action="file.parse",
            target_type="file_upload",
            target_id=file_id,
            metadata={
                "detected_format": parsed["detected_format"],
                "row_count": parsed["row_count"],
                "columns": parsed["columns"],
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not persist uploaded file metadata") from exc

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
    storage = get_storage()
    signed_url = storage.url(path)
    if is_signed_url(signed_url):
        return RedirectResponse(signed_url, status_code=307)
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


# ---------------------------------------------------------------------------
# GET /  --  list all uploaded files in the caller's org
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[FileMetadata])
async def list_files(
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> list[FileMetadata]:
    result = await db.execute(
        select(FileUpload).where(FileUpload.org_id == ctx.org_id).order_by(FileUpload.created_at.desc())
    )
    return [_metadata_from_upload(f) for f in result.scalars().all()]


# ---------------------------------------------------------------------------
# GET /{file_id}  --  file metadata
# ---------------------------------------------------------------------------
@router.get("/{file_id}", response_model=FileMetadata)
async def get_file_metadata(
    file_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> FileMetadata:
    upload = await _get_upload_or_404(db, file_id, ctx.org_id)
    return _metadata_from_upload(upload)


# ---------------------------------------------------------------------------
# GET /{file_id}/download  --  serve the actual file bytes
# ---------------------------------------------------------------------------
@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> Response:
    upload = await _get_upload_or_404(db, file_id, ctx.org_id)
    storage = get_storage(upload.storage_backend)
    signed_url = storage.url(upload.storage_path)
    if upload.storage_backend == "s3" and is_signed_url(signed_url):
        return RedirectResponse(signed_url, status_code=307)
    try:
        content = upload.content_bytes
        if content is None:
            content = await storage.load(upload.storage_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File missing from storage")
    return Response(
        content=content,
        media_type=upload.content_type,
        headers={"Content-Disposition": f'attachment; filename="{upload.filename}"'},
    )


# ---------------------------------------------------------------------------
# DELETE /{file_id}  --  remove file from storage and registry
# ---------------------------------------------------------------------------
@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> None:
    if not ctx.can_write():
        raise HTTPException(status_code=403, detail="Member role required to delete files")
    upload = await _get_upload_or_404(db, file_id, ctx.org_id)
    try:
        await get_storage(upload.storage_backend).delete(upload.storage_path)
    except FileNotFoundError:
        pass
    await db.delete(upload)
