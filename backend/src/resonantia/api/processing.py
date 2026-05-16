"""Data processing endpoints (dose-response, normalization, qPCR)."""

from __future__ import annotations

import csv
import io
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.db.session import get_db
from resonantia.dependencies import get_request_context
from resonantia.models.file_upload import FileUpload
from resonantia.models.request_context import RequestContext
from resonantia.repositories.audit_log import append_audit_log
from resonantia.repositories.processing_result import ProcessingResultRepository, make_idempotency_key
from resonantia.services.data_processor import (
    calculate_z_prime,
    fit_dose_response,
    normalize_plate,
)
from resonantia.services.storage import get_storage

router = APIRouter()


# ---------------------------------------------------------------------------
# Request schemas (endpoint-specific)
# ---------------------------------------------------------------------------

class DoseResponseRequest(BaseModel):
    concentrations: list[float]
    responses: list[float]


class PlateNormalizationRequest(BaseModel):
    raw_data: list[list[float]]
    method: str = "z-score"
    positive_control_wells: list[tuple[int, int]] | None = None
    negative_control_wells: list[tuple[int, int]] | None = None


class ZPrimeRequest(BaseModel):
    positive_controls: list[float]
    negative_controls: list[float]


class QPCRSample(BaseModel):
    name: str
    ct_values: list[float]


class QPCRRequest(BaseModel):
    reference_gene: str
    target_gene: str
    control_group: str
    samples: list[QPCRSample]


class DoseResponseFromFileRequest(BaseModel):
    file_id: str
    concentration_column: str | None = None
    response_column: str | None = None


class PlateNormalizationFromFileRequest(BaseModel):
    file_id: str
    method: str = "z-score"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

def _parse_uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise HTTPException(status_code=404, detail="File not found") from None


async def _load_upload(
    db: AsyncSession,
    *,
    file_id: str,
    org_id: str,
) -> tuple[FileUpload, bytes]:
    upload = await db.get(FileUpload, _parse_uuid(file_id))
    if not upload or upload.org_id != org_id:
        raise HTTPException(status_code=404, detail="File not found")
    content = upload.content_bytes
    if content is None:
        content = await get_storage().load(upload.storage_path)
    return upload, content


def _csv_rows(content: bytes) -> list[dict[str, str]]:
    text = content.decode("utf-8-sig", errors="replace")
    return list(csv.DictReader(io.StringIO(text)))


def _pick_column(columns: list[str], explicit: str | None, candidates: list[str]) -> str:
    if explicit:
        if explicit not in columns:
            raise HTTPException(status_code=400, detail=f"Column not found: {explicit}")
        return explicit
    lower_map = {col.strip().lower(): col for col in columns}
    for candidate in candidates:
        if candidate in lower_map:
            return lower_map[candidate]
    for candidate in candidates:
        for normalized, column in lower_map.items():
            if candidate in normalized:
                return column
    raise HTTPException(status_code=400, detail=f"Could not infer required column from {columns}")


def _dose_response_from_csv(
    content: bytes,
    body: DoseResponseFromFileRequest,
) -> tuple[list[float], list[float], str, str]:
    rows = _csv_rows(content)
    if not rows:
        raise HTTPException(status_code=400, detail="CSV file has no rows")
    columns = list(rows[0].keys())
    concentration_column = _pick_column(
        columns,
        body.concentration_column,
        ["concentration", "concentration_nm", "concentration_um", "conc", "dose"],
    )
    response_column = _pick_column(
        columns,
        body.response_column,
        ["response", "response_%", "response_pct", "viability", "inhibition", "activity"],
    )
    concentrations: list[float] = []
    responses: list[float] = []
    for row in rows:
        concentration = row.get(concentration_column)
        response = row.get(response_column)
        if concentration in (None, "") and response in (None, ""):
            continue
        if concentration in (None, "") or response in (None, ""):
            raise HTTPException(status_code=400, detail="Dose-response columns must have matching numeric values")
        try:
            concentrations.append(float(concentration))
            responses.append(float(response))
        except ValueError:
            raise HTTPException(status_code=400, detail="Dose-response columns must be numeric") from None
    if not concentrations:
        raise HTTPException(status_code=400, detail="Dose-response columns must have matching numeric values")
    return concentrations, responses, concentration_column, response_column


def _matrix_from_csv(content: bytes) -> list[list[float]]:
    text = content.decode("utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        raise HTTPException(status_code=400, detail="CSV file has no rows")

    def _parse_row(row: list[str]) -> list[float] | None:
        if not any(cell.strip() for cell in row):
            return None
        try:
            return [float(cell) for cell in row if cell.strip()]
        except ValueError:
            return None

    matrix: list[list[float]] = []
    for row in rows:
        numeric_row = _parse_row(row)
        if numeric_row is not None:
            matrix.append(numeric_row)
    if not matrix:
        raise HTTPException(status_code=400, detail="CSV file has no numeric plate values")
    row_widths = {len(row) for row in matrix}
    if len(row_widths) != 1:
        raise HTTPException(status_code=400, detail="Plate CSV rows must have the same number of numeric values")
    return matrix


async def _persist_file_processing_result(
    db: AsyncSession,
    *,
    ctx: RequestContext,
    upload: FileUpload,
    analysis_type: str,
    parameters: dict[str, Any],
    result: dict[str, Any],
) -> tuple[str, bool]:
    key = make_idempotency_key(
        file_upload_id=str(upload.id),
        analysis_type=analysis_type,
        parameters=parameters,
    )
    repo = ProcessingResultRepository(db)
    existing = await repo.get_by_idempotency_key(org_id=ctx.org_id, idempotency_key=key)
    if existing:
        await append_audit_log(
            db,
            ctx=ctx,
            action="processing.from_file.cached",
            target_type="processing_result",
            target_id=str(existing.id),
            metadata={
                "file_upload_id": str(upload.id),
                "analysis_type": analysis_type,
            },
        )
        await db.flush()
        return str(existing.id), True
    record = await repo.create(
        org_id=ctx.org_id,
        created_by=ctx.user_id,
        idempotency_key=key,
        analysis_type=analysis_type,
        parameters=parameters,
        result=result,
        file_upload_id=upload.id,
    )
    await append_audit_log(
        db,
        ctx=ctx,
        action="processing.from_file",
        target_type="processing_result",
        target_id=str(record.id),
        metadata={
            "file_upload_id": str(upload.id),
            "analysis_type": analysis_type,
        },
    )
    await db.flush()
    return str(record.id), False

@router.post("/dose-response")
async def dose_response(
    body: DoseResponseRequest,
    ctx: RequestContext = Depends(get_request_context),
) -> dict[str, Any]:
    _ = ctx
    return fit_dose_response(body.concentrations, body.responses)


@router.post("/plate-normalization")
async def plate_normalization(
    body: PlateNormalizationRequest,
    ctx: RequestContext = Depends(get_request_context),
) -> dict[str, Any]:
    _ = ctx
    return normalize_plate(
        raw_data=body.raw_data,
        method=body.method,
        positive_control_wells=body.positive_control_wells,
        negative_control_wells=body.negative_control_wells,
    )


@router.post("/z-prime")
async def z_prime(
    body: ZPrimeRequest,
    ctx: RequestContext = Depends(get_request_context),
) -> dict[str, Any]:
    _ = ctx
    return calculate_z_prime(body.positive_controls, body.negative_controls)


@router.post("/qpcr")
async def qpcr_analysis(
    body: QPCRRequest,
    ctx: RequestContext = Depends(get_request_context),
) -> dict[str, Any]:
    """Delta-delta Ct (Livak) method for relative gene expression."""
    _ = ctx
    import numpy as np

    results: list[dict[str, Any]] = []
    control_delta_cts: list[float] = []

    # First pass: compute delta Ct for each sample
    sample_deltas: dict[str, float] = {}
    for sample in body.samples:
        # Split Ct values: assume first half is target, second half is reference
        # In a real implementation, samples would carry gene labels.
        # Here we expect ct_values = [target_ct, reference_ct]
        if len(sample.ct_values) < 2:
            continue
        target_ct = sample.ct_values[0]
        ref_ct = sample.ct_values[1]
        delta_ct = target_ct - ref_ct
        sample_deltas[sample.name] = delta_ct
        if sample.name == body.control_group:
            control_delta_cts.append(delta_ct)

    if not control_delta_cts:
        return {"error": f"Control group '{body.control_group}' not found"}

    control_mean = float(np.mean(control_delta_cts))

    for sample in body.samples:
        dct = sample_deltas.get(sample.name)
        if dct is None:
            continue
        ddct = dct - control_mean
        fold_change = 2.0 ** (-ddct)
        results.append({
            "sample": sample.name,
            "delta_ct": round(dct, 4),
            "delta_delta_ct": round(ddct, 4),
            "fold_change": round(fold_change, 4),
        })

    return {
        "method": "delta_delta_ct",
        "reference_gene": body.reference_gene,
        "target_gene": body.target_gene,
        "control_group": body.control_group,
        "control_delta_ct_mean": round(control_mean, 4),
        "results": results,
    }


@router.post("/dose-response/from-file")
async def dose_response_from_file(
    body: DoseResponseFromFileRequest,
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if not ctx.can_write():
        raise HTTPException(status_code=403, detail="Member role required for processing")
    upload, content = await _load_upload(db, file_id=body.file_id, org_id=ctx.org_id)
    concentrations, responses, concentration_column, response_column = _dose_response_from_csv(content, body)
    result = fit_dose_response(concentrations, responses)
    processing_result_id, cached = await _persist_file_processing_result(
        db,
        ctx=ctx,
        upload=upload,
        analysis_type="dose_response_from_file",
        parameters={
            "file_id": body.file_id,
            "concentration_column": concentration_column,
            "response_column": response_column,
        },
        result=result,
    )
    return {"processing_result_id": processing_result_id, "cached": cached, "result": result}


@router.post("/plate-normalization/from-file")
async def plate_normalization_from_file(
    body: PlateNormalizationFromFileRequest,
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if not ctx.can_write():
        raise HTTPException(status_code=403, detail="Member role required for processing")
    upload, content = await _load_upload(db, file_id=body.file_id, org_id=ctx.org_id)
    matrix = _matrix_from_csv(content)
    result = normalize_plate(matrix, method=body.method)
    result["rows"] = len(matrix)
    result["columns"] = len(matrix[0])
    processing_result_id, cached = await _persist_file_processing_result(
        db,
        ctx=ctx,
        upload=upload,
        analysis_type="plate_normalization_from_file",
        parameters={"file_id": body.file_id, "method": body.method},
        result=result,
    )
    return {"processing_result_id": processing_result_id, "cached": cached, "result": result}
