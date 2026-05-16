"""Tests for from-file processing API endpoints."""

from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.api.processing import DoseResponseFromFileRequest, dose_response_from_file
from resonantia.models.audit_log import AuditLog
from resonantia.models.processing_result import ProcessingResult
from resonantia.models.request_context import RequestContext


async def _upload_csv(
    client: AsyncClient,
    *,
    org_id: str,
    filename: str,
    content: bytes,
) -> str:
    response = await client.post(
        "/api/v1/files/upload",
        files={"files": (filename, content, "text/csv")},
        headers={"X-Org-Id": org_id},
    )
    assert response.status_code == 201
    return response.json()[0]["id"]


@pytest.mark.asyncio
async def test_dose_response_from_file_returns_processing_result(
    client: AsyncClient,
    db_session: AsyncSession,
):
    file_id = await _upload_csv(
        client,
        org_id="org_processing_api",
        filename="dose.csv",
        content=(
            b"concentration,response\n"
            b"0.001,99\n"
            b"0.01,94\n"
            b"0.1,72\n"
            b"1,44\n"
            b"10,17\n"
            b"100,5\n"
        ),
    )

    response = await client.post(
        "/api/v1/processing/dose-response/from-file",
        json={"file_id": file_id},
        headers={"X-Org-Id": "org_processing_api"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["cached"] is False
    assert body["processing_result_id"]
    assert body["result"]["success"] is True

    record = await db_session.get(ProcessingResult, uuid.UUID(body["processing_result_id"]))
    assert record is not None
    assert record.org_id == "org_processing_api"
    assert record.file_upload_id == uuid.UUID(file_id)
    assert record.analysis_type == "dose_response_from_file"

    audit_entry = await db_session.scalar(
        select(AuditLog).where(
            AuditLog.target_type == "processing_result",
            AuditLog.target_id == body["processing_result_id"],
        )
    )
    assert audit_entry is not None
    assert audit_entry.action == "processing.from_file"


@pytest.mark.asyncio
async def test_plate_normalization_from_file_returns_processing_result(
    client: AsyncClient,
    db_session: AsyncSession,
):
    file_id = await _upload_csv(
        client,
        org_id="org_processing_api",
        filename="plate.csv",
        content=b"A,B,C\n1,2,3\n4,5,6\n7,8,9\n",
    )

    response = await client.post(
        "/api/v1/processing/plate-normalization/from-file",
        json={"file_id": file_id, "method": "z-score"},
        headers={"X-Org-Id": "org_processing_api"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["cached"] is False
    assert body["processing_result_id"]
    assert body["result"]["method"] == "z-score"
    assert body["result"]["rows"] == 3
    assert body["result"]["columns"] == 3

    record = await db_session.get(ProcessingResult, uuid.UUID(body["processing_result_id"]))
    assert record is not None
    assert record.file_upload_id == uuid.UUID(file_id)
    assert record.analysis_type == "plate_normalization_from_file"


@pytest.mark.asyncio
async def test_from_file_processing_denies_cross_org_file_access(client: AsyncClient):
    file_id = await _upload_csv(
        client,
        org_id="org_alpha",
        filename="dose.csv",
        content=b"concentration,response\n1,90\n10,50\n100,10\n",
    )

    response = await client.post(
        "/api/v1/processing/dose-response/from-file",
        json={"file_id": file_id},
        headers={"X-Org-Id": "org_beta"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_from_file_processing_requires_write_role(db_session: AsyncSession):
    viewer_ctx = RequestContext(
        user_id="viewer",
        org_id="org_processing_api",
        roles=["org:viewer"],
        request_id="req-processing",
    )

    with pytest.raises(HTTPException) as exc_info:
        await dose_response_from_file(
            DoseResponseFromFileRequest(file_id=str(uuid.uuid4())),
            ctx=viewer_ctx,
            db=db_session,
        )

    assert exc_info.value.status_code == 403
