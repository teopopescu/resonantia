"""Intent taxonomy for agent routing."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class IntentClass(str, Enum):
    SAMPLE_LOOKUP = "sample_lookup"
    INVENTORY_CHECK = "inventory_check"
    EXPIRING_SAMPLES = "expiring_samples"
    EXPERIMENT_QUERY = "experiment_query"
    IC50_QUERY = "ic50_query"
    FILE_LIST = "file_list"
    FILE_READ = "file_read"
    DOSE_RESPONSE = "dose_response"
    PLATE_NORMALIZATION = "plate_normalization"
    Z_PRIME = "z_prime"
    QPCR_ANALYSIS = "qpcr_analysis"
    ELN_CREATE = "eln_create"
    ELN_SUBMIT = "eln_submit"
    PROTOCOL_CREATE = "protocol_create"
    PLATE_MAP_CREATE = "plate_map_create"
    CHERRY_PICK = "cherry_pick"
    SERIAL_DILUTION = "serial_dilution"
    WORKLIST_GENERATION = "worklist_generation"
    MULTI_STEP = "multi_step"
    GENERAL_CHAT = "general_chat"


class IntentClassification(BaseModel):
    intent_class: IntentClass
    confidence: float = Field(ge=0, le=1)
    rationale: str = ""
    recommended_tool: str | None = None
    route: str = "single_agent"
