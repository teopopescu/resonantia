"""Plate mapping workflow — validates, generates, and persists plate maps."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from resonantia.workflows.activities import (
        generate_mapping,
        generate_worklist,
        save_plate_map,
        validate_mapping,
        validate_source_plates,
    )


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class SourcePlate:
    plate_id: str
    barcode: str
    plate_type: str = "96"
    wells: dict[str, Any] = field(default_factory=dict)


@dataclass
class DestinationPlate:
    plate_id: str
    barcode: str
    plate_type: str = "96"


@dataclass
class PlateMapInput:
    sources: list[SourcePlate]
    destination: DestinationPlate
    mode: str = "direct"  # direct | cherry_pick | serial_dilution | quadrant
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class WellMapping:
    source_plate: str
    source_well: str
    destination_well: str
    volume_ul: float = 0.0
    sample_id: str | None = None


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class PlateMapOutput:
    plate_map_id: str
    mappings_count: int
    worklist_key: str
    validation: ValidationResult


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------

RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_attempts=3,
    maximum_interval=timedelta(seconds=15),
)


@workflow.defn
class PlateMapWorkflow:
    """Creates a validated plate map with worklist generation."""

    @workflow.run
    async def run(self, inp: PlateMapInput) -> PlateMapOutput:
        # 1. Validate source plates exist in inventory
        source_validation: ValidationResult = await workflow.execute_activity(
            validate_source_plates,
            args=[[s.plate_id for s in inp.sources]],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RETRY_POLICY,
        )
        if not source_validation.valid:
            return PlateMapOutput(
                plate_map_id="",
                mappings_count=0,
                worklist_key="",
                validation=source_validation,
            )

        # 2. Generate well-to-well mappings
        mappings: list[WellMapping] = await workflow.execute_activity(
            generate_mapping,
            args=[
                [s.plate_id for s in inp.sources],
                inp.destination.plate_id,
                inp.mode,
            ],
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RETRY_POLICY,
        )

        # 3. Validate the generated mappings for conflicts
        mapping_validation: ValidationResult = await workflow.execute_activity(
            validate_mapping,
            args=[mappings],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RETRY_POLICY,
        )
        if not mapping_validation.valid:
            return PlateMapOutput(
                plate_map_id="",
                mappings_count=len(mappings),
                worklist_key="",
                validation=mapping_validation,
            )

        # 4. Generate instrument worklist file
        worklist_format = inp.parameters.get("worklist_format", "csv")
        worklist: bytes = await workflow.execute_activity(
            generate_worklist,
            args=[mappings, worklist_format],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RETRY_POLICY,
        )

        # 5. Persist plate map and worklist
        plate_map_id: str = await workflow.execute_activity(
            save_plate_map,
            args=[mappings, worklist],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RETRY_POLICY,
        )

        return PlateMapOutput(
            plate_map_id=plate_map_id,
            mappings_count=len(mappings),
            worklist_key=plate_map_id,
            validation=mapping_validation,
        )
