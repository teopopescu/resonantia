"""Data processing workflow — loads, analyses, and persists experiment results."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from resonantia.workflows.activities import (
        generate_figures,
        load_experiment_data,
        run_processing,
        save_results,
    )


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ProcessingInput:
    experiment_id: str
    processing_type: str  # dose_response | plate_normalization | qpcr
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingOutput:
    experiment_id: str
    result_id: str
    processing_type: str
    summary: dict[str, Any] = field(default_factory=dict)
    figure_keys: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------

RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_attempts=3,
    maximum_interval=timedelta(seconds=30),
)


@workflow.defn
class DataProcessingWorkflow:
    """Runs experiment data through a processing pipeline and persists results."""

    @workflow.run
    async def run(self, inp: ProcessingInput) -> ProcessingOutput:
        # 1. Load raw experiment data
        data: dict[str, Any] = await workflow.execute_activity(
            load_experiment_data,
            args=[inp.experiment_id],
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RETRY_POLICY,
        )

        # 2. Run the requested processing
        #    - dose_response: 4PL curve fitting
        #    - plate_normalization: Z-score, PoC
        #    - qpcr: delta-delta Ct
        results: dict[str, Any] = await workflow.execute_activity(
            run_processing,
            args=[data, inp.processing_type, inp.parameters],
            start_to_close_timeout=timedelta(seconds=300),
            heartbeat_timeout=timedelta(seconds=60),
            retry_policy=RETRY_POLICY,
        )

        # 3. Generate figures / plots
        figure_keys: list[str] = await workflow.execute_activity(
            generate_figures,
            args=[results],
            start_to_close_timeout=timedelta(seconds=120),
            retry_policy=RETRY_POLICY,
        )

        # 4. Persist results and figures
        result_id: str = await workflow.execute_activity(
            save_results,
            args=[inp.experiment_id, results, figure_keys],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RETRY_POLICY,
        )

        return ProcessingOutput(
            experiment_id=inp.experiment_id,
            result_id=result_id,
            processing_type=inp.processing_type,
            summary=results.get("summary", {}),
            figure_keys=figure_keys,
        )
