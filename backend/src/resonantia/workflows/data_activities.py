"""Temporal activities for durable file-based data processing."""

from __future__ import annotations

import csv
import io
import logging
import uuid
from typing import Any

from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def load_uploaded_file_activity(file_upload_id: str, org_id: str) -> dict[str, Any]:
    """Load an org-scoped uploaded file from durable storage."""
    from resonantia.db.session import async_session_factory
    from resonantia.models.file_upload import FileUpload
    from resonantia.services.storage import get_storage

    async with async_session_factory() as session:
        upload = await session.get(FileUpload, uuid.UUID(file_upload_id))
        if not upload or upload.org_id != org_id:
            raise ValueError("File not found")
        content = upload.content_bytes
        if content is None:
            content = await get_storage().load(upload.storage_path)
        return {
            "file_upload_id": str(upload.id),
            "filename": upload.filename,
            "content_type": upload.content_type,
            "content": content.decode("utf-8-sig", errors="replace"),
        }


@activity.defn
async def parse_uploaded_file_activity(
    file_payload: dict[str, Any],
    processing_type: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """Parse CSV content into the structure expected by the processing step."""
    text = str(file_payload.get("content") or "")
    if not text.strip():
        raise ValueError("Uploaded file is empty")

    if processing_type == "dose_response":
        rows = list(csv.DictReader(io.StringIO(text)))
        if not rows:
            raise ValueError("CSV file has no rows")
        columns = list(rows[0].keys())
        concentration_col = _pick_column(
            columns,
            parameters.get("concentration_column"),
            ["concentration", "concentration_nm", "concentration_um", "conc", "dose"],
        )
        response_col = _pick_column(
            columns,
            parameters.get("response_column"),
            ["response", "response_%", "response_pct", "viability", "inhibition", "activity"],
        )
        concentrations: list[float] = []
        responses: list[float] = []
        for row in rows:
            concentration = row.get(concentration_col)
            response = row.get(response_col)
            if concentration in (None, "") and response in (None, ""):
                continue
            if concentration in (None, "") or response in (None, ""):
                raise ValueError("Dose-response columns must have matching values")
            concentrations.append(float(concentration))
            responses.append(float(response))
        return {
            "file_upload_id": file_payload["file_upload_id"],
            "processing_type": processing_type,
            "concentrations": concentrations,
            "responses": responses,
            "columns": {
                "concentration": concentration_col,
                "response": response_col,
            },
        }

    if processing_type == "plate_normalization":
        matrix: list[list[float]] = []
        for row in csv.reader(io.StringIO(text)):
            if not any(cell.strip() for cell in row):
                continue
            try:
                matrix.append([float(cell) for cell in row if cell.strip()])
            except ValueError:
                continue
        if not matrix:
            raise ValueError("CSV file has no numeric plate values")
        widths = {len(row) for row in matrix}
        if len(widths) != 1:
            raise ValueError("Plate CSV rows must have the same width")
        return {
            "file_upload_id": file_payload["file_upload_id"],
            "processing_type": processing_type,
            "raw_data": matrix,
            "rows": len(matrix),
            "columns": len(matrix[0]),
        }

    raise ValueError(f"Unsupported processing type: {processing_type}")


@activity.defn
async def run_file_processing_activity(
    parsed: dict[str, Any],
    processing_type: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """Run the requested processing algorithm on parsed file data."""
    if processing_type == "dose_response":
        from resonantia.services.data_processor import fit_dose_response

        return fit_dose_response(parsed["concentrations"], parsed["responses"])

    if processing_type == "plate_normalization":
        from resonantia.services.data_processor import normalize_plate

        result = normalize_plate(parsed["raw_data"], method=parameters.get("method", "z-score"))
        result["rows"] = parsed["rows"]
        result["columns"] = parsed["columns"]
        return result

    raise ValueError(f"Unsupported processing type: {processing_type}")


@activity.defn
async def persist_file_processing_result_activity(
    file_upload_id: str,
    org_id: str,
    user_id: str | None,
    processing_type: str,
    parameters: dict[str, Any],
    result: dict[str, Any],
) -> str:
    """Persist a processing result and return its durable record ID."""
    from resonantia.db.session import async_session_factory
    from resonantia.models.request_context import RequestContext
    from resonantia.repositories.audit_log import append_audit_log
    from resonantia.repositories.processing_result import ProcessingResultRepository, make_idempotency_key

    async with async_session_factory() as session:
        idempotency_key = make_idempotency_key(
            file_upload_id=file_upload_id,
            analysis_type=processing_type,
            parameters=parameters,
        )
        repo = ProcessingResultRepository(session)
        existing = await repo.get_by_idempotency_key(org_id=org_id, idempotency_key=idempotency_key)
        if existing:
            return str(existing.id)

        record = await repo.create(
            org_id=org_id,
            created_by=user_id,
            idempotency_key=idempotency_key,
            analysis_type=processing_type,
            parameters=parameters,
            result=result,
            file_upload_id=file_upload_id,
        )
        await append_audit_log(
            session,
            ctx=RequestContext(
                user_id=user_id or "temporal",
                org_id=org_id,
                roles=["org:member"],
                permissions=[],
            ),
            action="processing.temporal.persist",
            target_type="processing_result",
            target_id=str(record.id),
            metadata={
                "file_upload_id": file_upload_id,
                "processing_type": processing_type,
            },
        )
        await session.commit()
        return str(record.id)


def _pick_column(columns: list[str], explicit: str | None, candidates: list[str]) -> str:
    if explicit:
        if explicit not in columns:
            raise ValueError(f"Column not found: {explicit}")
        return explicit
    lower_map = {col.strip().lower(): col for col in columns}
    for candidate in candidates:
        if candidate in lower_map:
            return lower_map[candidate]
    for candidate in candidates:
        for normalized, column in lower_map.items():
            if candidate in normalized:
                return column
    raise ValueError(f"Could not infer required column from {columns}")
