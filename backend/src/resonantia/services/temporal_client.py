"""Temporal client wrapper for use in FastAPI request handlers."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from temporalio.client import Client, WorkflowHandle

from resonantia.config import get_settings
from resonantia.telemetry import current_trace_context
from resonantia.workflows.agent_workflow import AgentToolCallInput, AgentToolCallWorkflow
from resonantia.workflows.data_processing_workflow import (
    DataProcessingWorkflow,
    FileProcessingInput,
)
from resonantia.workflows.plate_workflow import (
    DestinationPlate,
    PlateMapInput,
    PlateMapWorkflow,
    SourcePlate,
)

logger = logging.getLogger(__name__)

_client: Client | None = None


async def get_temporal_client() -> Client:
    """Return a cached Temporal client (lazy singleton)."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = await Client.connect(
            settings.temporal_host,
            namespace=settings.temporal_namespace,
        )
    return _client


async def start_agent_workflow(
    message: str,
    conversation_id: str,
    user_id: str,
    org_id: str = "org_default",
    context: dict[str, Any] | None = None,
    roles: list[str] | None = None,
    permissions: list[str] | None = None,
) -> WorkflowHandle:
    """Start an AgentToolCallWorkflow and return its handle."""
    client = await get_temporal_client()
    settings = get_settings()

    workflow_id = f"agent-{conversation_id}-{uuid.uuid4().hex[:8]}"

    # Load tool schemas for the LLM
    try:
        from resonantia.services.tool_registry import get_tools_as_anthropic

        tools = await get_tools_as_anthropic()
    except Exception:
        tools = []

    messages: list[dict[str, Any]] = [{"role": "user", "content": message}]

    handle = await client.start_workflow(
        AgentToolCallWorkflow.run,
        AgentToolCallInput(
            messages=messages,
            tools=tools,
            org_id=org_id,
            user_id=user_id,
            request_context={
                "user_id": user_id,
                "org_id": org_id,
                "roles": roles or ["org:viewer"],
                "permissions": permissions or [],
                "_trace_context": current_trace_context(),
            },
            conversation_id=conversation_id,
        ),
        id=workflow_id,
        task_queue=settings.temporal_task_queue,
    )
    logger.info("Started agent workflow %s (org=%s)", workflow_id, org_id)
    return handle


async def start_plate_workflow(
    mapping_request: dict[str, Any],
) -> WorkflowHandle:
    """Start a PlateMapWorkflow and return its handle."""
    client = await get_temporal_client()
    settings = get_settings()

    sources = [
        SourcePlate(
            plate_id=s.get("plate_id", ""),
            barcode=s.get("barcode", ""),
            plate_type=s.get("plate_type", "96"),
        )
        for s in mapping_request.get("sources", [])
    ]
    dest_raw = mapping_request.get("destination", {})
    destination = DestinationPlate(
        plate_id=dest_raw.get("plate_id", ""),
        barcode=dest_raw.get("barcode", ""),
        plate_type=dest_raw.get("plate_type", "96"),
    )

    inp = PlateMapInput(
        sources=sources,
        destination=destination,
        mode=mapping_request.get("mode", "direct"),
        parameters=mapping_request.get("parameters", {}),
    )

    workflow_id = f"plate-{uuid.uuid4().hex[:8]}"
    handle = await client.start_workflow(
        PlateMapWorkflow.run,
        inp,
        id=workflow_id,
        task_queue=settings.temporal_task_queue,
    )
    logger.info("Started plate workflow %s", workflow_id)
    return handle


async def start_processing_workflow(
    experiment_id: str,
    processing_type: str,
    params: dict[str, Any] | None = None,
) -> WorkflowHandle:
    """Start a file-based DataProcessingWorkflow and return its handle."""
    params = params or {}
    file_upload_id = params.get("file_upload_id") or params.get("file_id") or experiment_id
    org_id = params.get("org_id", "org_default")
    user_id = params.get("user_id") or params.get("created_by")
    return await start_file_processing_workflow(
        file_upload_id=str(file_upload_id),
        processing_type=processing_type,
        org_id=str(org_id),
        user_id=str(user_id) if user_id else None,
        params=params,
    )


async def start_file_processing_workflow(
    *,
    file_upload_id: str,
    processing_type: str,
    org_id: str,
    user_id: str | None = None,
    params: dict[str, Any] | None = None,
) -> WorkflowHandle:
    """Start a durable upload -> parse -> process -> persist workflow."""
    client = await get_temporal_client()
    settings = get_settings()
    params = params or {}

    workflow_id = f"process-{file_upload_id}-{uuid.uuid4().hex[:8]}"
    handle = await client.start_workflow(
        DataProcessingWorkflow.run,
        FileProcessingInput(
            file_upload_id=file_upload_id,
            org_id=org_id,
            user_id=user_id,
            processing_type=processing_type,
            parameters=params,
        ),
        id=workflow_id,
        task_queue=settings.temporal_task_queue,
    )
    logger.info("Started processing workflow %s", workflow_id)
    return handle


async def get_workflow_status(workflow_id: str) -> dict[str, Any]:
    """Query the status of a running or completed workflow."""
    client = await get_temporal_client()
    handle = client.get_workflow_handle(workflow_id)

    desc = await handle.describe()
    status = str(desc.status)

    result: dict[str, Any] = {
        "workflow_id": workflow_id,
        "status": status,
        "start_time": desc.start_time.isoformat() if desc.start_time else None,
        "close_time": desc.close_time.isoformat() if desc.close_time else None,
    }

    # If completed, try to fetch the result
    if desc.status and desc.status.name == "COMPLETED":
        try:
            result["result"] = await handle.result()
        except Exception:
            result["result"] = None

    return result
