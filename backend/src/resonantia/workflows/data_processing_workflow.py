"""Durable Temporal workflow for file-based data processing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from resonantia.workflows.data_activities import (
        load_uploaded_file_activity,
        parse_uploaded_file_activity,
        persist_file_processing_result_activity,
        run_file_processing_activity,
    )


@dataclass
class FileProcessingInput:
    file_upload_id: str
    org_id: str
    user_id: str | None
    processing_type: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class FileProcessingOutput:
    file_upload_id: str
    processing_type: str
    processing_result_id: str
    result: dict[str, Any]
    progress_events: list[dict[str, Any]]


RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_attempts=3,
    maximum_interval=timedelta(seconds=30),
)


@workflow.defn
class DataProcessingWorkflow:
    """Upload/file -> parse -> process -> persist workflow."""

    @workflow.run
    async def run(self, inp: FileProcessingInput) -> FileProcessingOutput:
        progress_events: list[dict[str, Any]] = []

        def progress(step: str, status: str) -> None:
            progress_events.append({
                "step": step,
                "status": status,
                "file_upload_id": inp.file_upload_id,
                "processing_type": inp.processing_type,
            })

        progress("load", "started")
        file_payload: dict[str, Any] = await workflow.execute_activity(
            load_uploaded_file_activity,
            args=[inp.file_upload_id, inp.org_id],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RETRY_POLICY,
        )
        progress("load", "completed")

        progress("parse", "started")
        parsed: dict[str, Any] = await workflow.execute_activity(
            parse_uploaded_file_activity,
            args=[file_payload, inp.processing_type, inp.parameters],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RETRY_POLICY,
        )
        progress("parse", "completed")

        progress("process", "started")
        result: dict[str, Any] = await workflow.execute_activity(
            run_file_processing_activity,
            args=[parsed, inp.processing_type, inp.parameters],
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RETRY_POLICY,
        )
        progress("process", "completed")

        progress("persist", "started")
        processing_result_id: str = await workflow.execute_activity(
            persist_file_processing_result_activity,
            args=[
                inp.file_upload_id,
                inp.org_id,
                inp.user_id,
                inp.processing_type,
                inp.parameters,
                result,
            ],
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RETRY_POLICY,
        )
        progress("persist", "completed")

        return FileProcessingOutput(
            file_upload_id=inp.file_upload_id,
            processing_type=inp.processing_type,
            processing_result_id=processing_result_id,
            result=result,
            progress_events=progress_events,
        )
