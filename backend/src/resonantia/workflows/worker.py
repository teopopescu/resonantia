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
from resonantia.workflows.data_activities import (
    load_uploaded_file_activity,
    parse_uploaded_file_activity,
    persist_file_processing_result_activity,
    run_file_processing_activity,
)
from resonantia.workflows.data_processing_workflow import DataProcessingWorkflow
from resonantia.workflows.plate_workflow import PlateMapWorkflow
from resonantia.workflows.voice_activities import (
    complete_voice_turn_activity,
    create_voice_turn_activity,
    fail_voice_turn_activity,
    run_voice_agent_activity,
    synthesize_voice_turn_activity,
    transcribe_voice_turn_activity,
)
from resonantia.workflows.voice_turn_workflow import VoiceTurnWorkflow

logger = logging.getLogger(__name__)

ALL_WORKFLOWS = [
    AgentToolCallWorkflow,
    PlateMapWorkflow,
    DataProcessingWorkflow,
    VoiceTurnWorkflow,
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
    load_uploaded_file_activity,
    parse_uploaded_file_activity,
    run_file_processing_activity,
    persist_file_processing_result_activity,
    load_experiment_data,
    run_processing,
    generate_figures,
    save_results,
    # Voice turn activities
    create_voice_turn_activity,
    transcribe_voice_turn_activity,
    run_voice_agent_activity,
    synthesize_voice_turn_activity,
    complete_voice_turn_activity,
    fail_voice_turn_activity,
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
