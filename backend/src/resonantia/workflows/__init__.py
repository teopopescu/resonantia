"""Temporal workflow definitions for Resonantia lab-informatics platform."""

from resonantia.workflows.agent_workflow import AgentToolCallWorkflow
from resonantia.workflows.plate_workflow import PlateMapWorkflow
from resonantia.workflows.processing_workflow import DataProcessingWorkflow
from resonantia.workflows.voice_turn_workflow import VoiceTurnWorkflow

__all__ = [
    "AgentToolCallWorkflow",
    "PlateMapWorkflow",
    "DataProcessingWorkflow",
    "VoiceTurnWorkflow",
]
