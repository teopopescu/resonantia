"""Temporal worker process — registers all workflows and activities."""

from __future__ import annotations

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from resonantia.config import get_settings
from resonantia.workflows.activities import (
    call_llm_activity,
    compile_results,
    evaluate_result,
    execute_tool_activity,
    generate_figures,
    generate_mapping,
    generate_worklist,
    load_experiment_data,
    persist_conversation_activity,
    run_processing,
    save_plate_map,
    save_results,
    validate_mapping,
    validate_source_plates,
)
from resonantia.workflows.agent_workflow import AgentToolCallWorkflow
from resonantia.workflows.plate_workflow import PlateMapWorkflow
from resonantia.workflows.processing_workflow import DataProcessingWorkflow

logger = logging.getLogger(__name__)

ALL_WORKFLOWS = [
    AgentToolCallWorkflow,
    PlateMapWorkflow,
    DataProcessingWorkflow,
]

ALL_ACTIVITIES = [
    # Agent activities (safe — no code generation / subprocess)
    call_llm_activity,
    execute_tool_activity,
    persist_conversation_activity,
    evaluate_result,
    compile_results,
    # Plate mapping activities
    validate_source_plates,
    generate_mapping,
    validate_mapping,
    generate_worklist,
    save_plate_map,
    # Data processing activities
    load_experiment_data,
    run_processing,
    generate_figures,
    save_results,
]


async def run_worker() -> None:
    """Connect to Temporal and run the worker until interrupted."""
    settings = get_settings()

    logger.info(
        "Connecting to Temporal at %s (namespace=%s)",
        settings.temporal_host,
        settings.temporal_namespace,
    )

    client = await Client.connect(
        settings.temporal_host,
        namespace=settings.temporal_namespace,
    )

    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=ALL_WORKFLOWS,
        activities=ALL_ACTIVITIES,
    )

    logger.info("Starting Temporal worker on queue '%s'", settings.temporal_task_queue)
    await worker.run()


def main() -> None:
    """Entry-point for ``python -m resonantia.workflows.worker``."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
