"""Data processing endpoints (dose-response, normalization, qPCR)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from resonantia.dependencies import get_request_context
from resonantia.models.request_context import RequestContext
from resonantia.services.data_processor import (
    calculate_z_prime,
    fit_dose_response,
    normalize_plate,
)

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


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

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
