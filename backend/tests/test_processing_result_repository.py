"""Tests for durable processing result idempotency."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.models.experiment import Experiment
from resonantia.models.file_upload import FileUpload
from resonantia.models.processing_result import ProcessingResult
from tests.conftest import _test_session_factory


async def _create_file_upload(db_session: AsyncSession, org_id: str) -> uuid.UUID:
    file_id = uuid.uuid4()
    db_session.add(
        FileUpload(
            id=file_id,
            org_id=org_id,
            uploaded_by="test-user",
            filename="source.csv",
            content_type="text/csv",
            size_bytes=10,
            storage_path=f"files/{file_id}.csv",
            storage_backend="local",
            content_bytes=b"x,y\n1,2\n",
        )
    )
    await db_session.commit()
    return file_id


async def _create_experiment(db_session: AsyncSession, org_id: str) -> uuid.UUID:
    experiment = Experiment(
        org_id=org_id,
        name="Processing fixture",
        protocol="test",
        status="completed",
        results={},
    )
    db_session.add(experiment)
    await db_session.commit()
    return experiment.id


@pytest.mark.asyncio
async def test_fit_dose_response_result_is_idempotent_and_linked(db_session: AsyncSession, monkeypatch):
    from resonantia.services import tool_executor
    from resonantia.services.tool_executor import _fit_dose_response_tool

    monkeypatch.setattr(tool_executor, "async_session_factory", _test_session_factory)
    org_id = "org_processing"
    file_id = await _create_file_upload(db_session, org_id)
    params = {
        "file_upload_id": str(file_id),
        "created_by": "user-123",
        "concentrations": [0.001, 0.01, 0.1, 1, 10, 100],
        "responses": [99, 94, 72, 44, 17, 5],
        "compound_name": "Staurosporine",
    }

    first = await _fit_dose_response_tool(params, org_id=org_id)
    second = await _fit_dose_response_tool(params, org_id=org_id)

    assert first["success"] is True
    assert first["cached"] is False
    assert second["success"] is True
    assert second["cached"] is True
    assert second["processing_result_id"] == first["processing_result_id"]

    record = await db_session.get(ProcessingResult, uuid.UUID(first["processing_result_id"]))
    assert record is not None
    assert record.org_id == org_id
    assert record.created_by == "user-123"
    assert record.file_upload_id == file_id
    assert record.experiment_id is not None
    assert record.analysis_type == "fit_dose_response"

    count = await db_session.scalar(select(func.count()).select_from(ProcessingResult))
    assert count == 1


@pytest.mark.asyncio
async def test_processing_tools_return_cached_results(db_session: AsyncSession, monkeypatch):
    from resonantia.services import tool_executor
    from resonantia.services.tool_executor import (
        _calculate_z_prime_tool,
        _normalize_plate_tool,
        _qpcr_analysis_tool,
    )

    monkeypatch.setattr(tool_executor, "async_session_factory", _test_session_factory)
    org_id = "org_processing"
    file_id = await _create_file_upload(db_session, org_id)
    experiment_id = await _create_experiment(db_session, org_id)

    normalize_params = {
        "file_upload_id": str(file_id),
        "experiment_id": str(experiment_id),
        "created_by": "user-123",
        "raw_data": [1.0, 2.0, 3.0],
        "method": "z-score",
    }
    z_prime_params = {
        "file_upload_id": str(file_id),
        "experiment_id": str(experiment_id),
        "created_by": "user-123",
        "positive_values": [10, 11, 12],
        "negative_values": [1, 2, 1],
    }
    qpcr_params = {
        "file_upload_id": str(file_id),
        "experiment_id": str(experiment_id),
        "created_by": "user-123",
        "reference_gene": "GAPDH",
        "control_sample": "Control",
        "ct_values": {
            "GAPDH": [20, 20.2, 19.8],
            "Control": [22, 22.1, 21.9],
            "SampleA": [24, 24.2, 23.8],
        },
    }

    for handler, params in (
        (_normalize_plate_tool, normalize_params),
        (_calculate_z_prime_tool, z_prime_params),
        (_qpcr_analysis_tool, qpcr_params),
    ):
        first = await handler(params, org_id=org_id)
        second = await handler(params, org_id=org_id)
        assert "error" not in first
        assert first["cached"] is False
        assert second["cached"] is True
        assert second["processing_result_id"] == first["processing_result_id"]

    result = await db_session.execute(select(ProcessingResult))
    records = result.scalars().all()
    assert {r.analysis_type for r in records} == {
        "normalize_plate",
        "calculate_z_prime",
        "qpcr_analysis",
    }
    assert all(r.file_upload_id == file_id for r in records)
    assert all(r.experiment_id == experiment_id for r in records)
    assert all(r.created_by == "user-123" for r in records)
