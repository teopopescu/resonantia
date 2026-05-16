"""Tests for durable file-based data processing workflows."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.models.file_upload import FileUpload
from resonantia.models.processing_result import ProcessingResult
from tests.conftest import _test_session_factory


@pytest.mark.asyncio
async def test_file_processing_activities_parse_fit_and_persist(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    from resonantia.db import session as db_session_module
    from resonantia.workflows.data_activities import (
        load_uploaded_file_activity,
        parse_uploaded_file_activity,
        persist_file_processing_result_activity,
        run_file_processing_activity,
    )

    monkeypatch.setattr(db_session_module, "async_session_factory", _test_session_factory)
    file_id = uuid.uuid4()
    db_session.add(
        FileUpload(
            id=file_id,
            org_id="org_processing",
            uploaded_by="user-1",
            filename="dose.csv",
            content_type="text/csv",
            size_bytes=64,
            storage_path=f"files/{file_id}.csv",
            storage_backend="local",
            content_bytes=(
                b"concentration,response\n"
                b"0.001,99\n"
                b"0.01,94\n"
                b"0.1,72\n"
                b"1,44\n"
                b"10,17\n"
                b"100,5\n"
            ),
        )
    )
    await db_session.commit()

    payload = await load_uploaded_file_activity(str(file_id), "org_processing")
    parsed = await parse_uploaded_file_activity(payload, "dose_response", {})
    result = await run_file_processing_activity(parsed, "dose_response", {})
    processing_result_id = await persist_file_processing_result_activity(
        str(file_id),
        "org_processing",
        "user-1",
        "dose_response",
        {},
        result,
    )

    assert result["success"] is True
    record = await db_session.get(ProcessingResult, uuid.UUID(processing_result_id))
    assert record is not None
    assert record.file_upload_id == file_id
    assert record.analysis_type == "dose_response"


@pytest.mark.asyncio
async def test_start_file_processing_workflow_passes_file_input(monkeypatch: pytest.MonkeyPatch):
    from resonantia.services import temporal_client
    from resonantia.workflows.data_processing_workflow import FileProcessingInput

    captured = {}

    class _FakeClient:
        async def start_workflow(self, workflow, inp, *, id, task_queue):
            captured["workflow"] = workflow
            captured["input"] = inp
            captured["id"] = id
            captured["task_queue"] = task_queue

            class _Handle:
                id = "workflow-1"

            return _Handle()

    async def _fake_client():
        return _FakeClient()

    monkeypatch.setattr(temporal_client, "get_temporal_client", _fake_client)

    handle = await temporal_client.start_file_processing_workflow(
        file_upload_id="file-1",
        processing_type="plate_normalization",
        org_id="org_processing",
        user_id="user-1",
        params={"method": "z-score"},
    )

    assert handle.id == "workflow-1"
    assert isinstance(captured["input"], FileProcessingInput)
    assert captured["input"].file_upload_id == "file-1"
    assert captured["input"].org_id == "org_processing"
    assert captured["input"].user_id == "user-1"
    assert captured["input"].processing_type == "plate_normalization"


@pytest.mark.asyncio
async def test_agent_file_processing_tool_starts_temporal_workflow(monkeypatch: pytest.MonkeyPatch):
    from resonantia.services import temporal_client, tool_executor
    from resonantia.services.tool_executor import _fit_dose_response_tool

    async def _no_cached(*args, **kwargs):
        return None

    class _Handle:
        id = "process-file-1"

    async def _start_file_processing_workflow(**kwargs):
        assert kwargs["file_upload_id"] == "file-1"
        assert kwargs["processing_type"] == "dose_response"
        assert kwargs["org_id"] == "org_processing"
        return _Handle()

    monkeypatch.setattr(tool_executor, "_get_cached_processing_result", _no_cached)
    monkeypatch.setattr(temporal_client, "start_file_processing_workflow", _start_file_processing_workflow)

    result = await _fit_dose_response_tool(
        {"file_upload_id": "file-1", "created_by": "user-1"},
        org_id="org_processing",
    )

    assert result == {
        "status": "processing",
        "workflow_id": "process-file-1",
        "file_upload_id": "file-1",
        "processing_type": "dose_response",
    }


def test_worker_registers_file_processing_workflow_and_activities():
    from resonantia.workflows.data_activities import (
        load_uploaded_file_activity,
        parse_uploaded_file_activity,
        persist_file_processing_result_activity,
        run_file_processing_activity,
    )
    from resonantia.workflows.data_processing_workflow import DataProcessingWorkflow
    from resonantia.workflows.worker import ALL_ACTIVITIES, ALL_WORKFLOWS

    assert DataProcessingWorkflow in ALL_WORKFLOWS
    assert load_uploaded_file_activity in ALL_ACTIVITIES
    assert parse_uploaded_file_activity in ALL_ACTIVITIES
    assert run_file_processing_activity in ALL_ACTIVITIES
    assert persist_file_processing_result_activity in ALL_ACTIVITIES
