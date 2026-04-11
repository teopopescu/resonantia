"""Temporal worker process — registers all workflows and activities."""

from __future__ import annotations

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from resonantia.config import get_settings
from resonantia.workflows.activities import (
    compile_results,
    evaluate_result,
    execute_in_sandbox,
    generate_code,
    generate_figures,
    generate_mapping,
    generate_worklist,
    llm_plan,
    load_experiment_data,
    retrieve_relevant_tools,
    review_for_hallucinations,
    run_processing,
    save_plate_map,
    save_results,
    validate_mapping,
    validate_source_plates,
)
from resonantia.workflows.agent_workflow import AgentRunWorkflow
from resonantia.workflows.plate_workflow import PlateMapWorkflow
from resonantia.workflows.processing_workflow import DataProcessingWorkflow

logger = logging.getLogger(__name__)

ALL_WORKFLOWS = [
    AgentRunWorkflow,
    PlateMapWorkflow,
    DataProcessingWorkflow,
]

ALL_ACTIVITIES = [
    # Agent activities
    retrieve_relevant_tools,
    llm_plan,
    generate_code,
    execute_in_sandbox,
    evaluate_result,
    compile_results,
    review_for_hallucinations,
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
