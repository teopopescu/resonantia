"""Tests for ELN draft creation from processing results."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.models.experiment import Experiment
from resonantia.models.file_upload import FileUpload
from resonantia.models.processing_result import ProcessingResult


async def _source_records(db_session: AsyncSession, *, org_id: str) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    file_id = uuid.uuid4()
    db_session.add(
        FileUpload(
            id=file_id,
            org_id=org_id,
            uploaded_by="user-1",
            filename="dose.csv",
            content_type="text/csv",
            size_bytes=10,
            storage_path=f"files/{file_id}.csv",
            storage_backend="local",
            content_bytes=b"concentration,response\n1,90\n",
        )
    )
    experiment = Experiment(
        org_id=org_id,
        name="Dose response",
        protocol="4PL fit",
        status="completed",
        results={},
    )
    db_session.add(experiment)
    await db_session.flush()

    processing = ProcessingResult(
        org_id=org_id,
        created_by="user-1",
        idempotency_key=f"key-{uuid.uuid4()}",
        analysis_type="dose_response_from_file",
        parameters={"file_id": str(file_id)},
        result={
            "success": True,
            "parameters": {"ec50": 12.5, "bottom": 1.0, "top": 98.0},
            "r_squared": 0.9876,
        },
        file_upload_id=file_id,
        experiment_id=experiment.id,
    )
    db_session.add(processing)
    await db_session.commit()
    return processing.id, experiment.id, file_id


@pytest.mark.asyncio
async def test_draft_from_result_with_correct_ic50_passes_validation(
    client: AsyncClient,
    db_session: AsyncSession,
):
    processing_id, experiment_id, file_id = await _source_records(db_session, org_id="org_eln")

    response = await client.post(
        "/api/v1/eln/draft-from-result",
        headers={"X-Org-Id": "org_eln"},
        json={
            "processing_result_id": str(processing_id),
            "experiment_id": str(experiment_id),
            "file_id": str(file_id),
            "title": "Validated draft",
            "content_markdown": "# Validated draft\n\nIC50: 12.5\nR-squared: 0.9876",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "draft"
    assert body["linked_references"]["validation"]["status"] == "passed"
    assert body["linked_references"]["processing_results"] == [str(processing_id)]


@pytest.mark.asyncio
async def test_draft_from_result_with_wrong_ic50_is_flagged(
    client: AsyncClient,
    db_session: AsyncSession,
):
    processing_id, experiment_id, file_id = await _source_records(db_session, org_id="org_eln")

    response = await client.post(
        "/api/v1/eln/draft-from-result",
        headers={"X-Org-Id": "org_eln"},
        json={
            "processing_result_id": str(processing_id),
            "experiment_id": str(experiment_id),
            "file_id": str(file_id),
            "content_markdown": "# Draft\n\nIC50: 99\nLD50: 10",
        },
    )

    assert response.status_code == 201
    validation = response.json()["linked_references"]["validation"]
    assert validation["status"] == "review_required"
    assert any(issue["claim"] == "ic50" and issue["reason"] == "numeric_mismatch" for issue in validation["issues"])
    assert any(issue["reason"] == "unsupported_claim_requires_review" for issue in validation["issues"])


@pytest.mark.asyncio
async def test_draft_from_result_rejects_cross_org_reference(
    client: AsyncClient,
    db_session: AsyncSession,
):
    processing_id, experiment_id, file_id = await _source_records(db_session, org_id="org_eln")
    _ = (experiment_id, file_id)

    response = await client.post(
        "/api/v1/eln/draft-from-result",
        headers={"X-Org-Id": "org_other"},
        json={"processing_result_id": str(processing_id)},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_draft_from_result_never_submits_entry(client: AsyncClient, db_session: AsyncSession):
    processing_id, _, _ = await _source_records(db_session, org_id="org_eln")

    response = await client.post(
        "/api/v1/eln/draft-from-result",
        headers={"X-Org-Id": "org_eln"},
        json={
            "processing_result_id": str(processing_id),
            "title": "Must remain draft",
            "linked_references": {"status": "submitted"},
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "draft"
