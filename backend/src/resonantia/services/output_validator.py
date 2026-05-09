"""Output guardrails: typed tool result envelopes and validation.

Provides ToolResult / ToolError models so callers can distinguish
success from validation failure from system failure.  Also provides
pre-execution validation: schema checks and cross-tenant entity
reference blocking.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Literal

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Typed envelopes
# ---------------------------------------------------------------------------

class ToolResult(BaseModel):
    """Successful tool execution result."""

    status: Literal["success"] = "success"
    tool_name: str
    data: dict[str, Any]
    source_refs: list[str] = []


class ToolError(BaseModel):
    """Tool execution error with typed classification."""

    status: Literal["error"] = "error"
    tool_name: str
    error_type: Literal["validation", "forbidden", "system", "timeout"]
    message: str
    retry_allowed: bool = False


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

def validate_tool_args(
    tool_name: str,
    args: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any] | ToolError:
    """Validate tool arguments against a JSON schema.

    *schema* is expected in the Anthropic/OpenAI ``input_schema`` format::

        {
            "type": "object",
            "properties": { "query": {"type": "string", ...}, ... },
            "required": ["query"],
        }

    Returns the (possibly coerced) args dict on success, or a
    ``ToolError(validation)`` on failure.
    """
    properties: dict[str, Any] = schema.get("properties", {})
    required: list[str] = schema.get("required", [])

    errors: list[str] = []

    # 1. Check required fields are present
    for field in required:
        if field not in args:
            errors.append(f"Missing required field: '{field}'")

    # 2. Type-check each provided field against the schema
    type_map: dict[str, tuple[type, ...]] = {
        "string": (str,),
        "number": (int, float),
        "integer": (int,),
        "boolean": (bool,),
        "array": (list,),
        "object": (dict,),
    }

    for field, value in args.items():
        if field not in properties:
            # Extra fields are tolerated (the LLM may send additional keys)
            continue

        expected_type = properties[field].get("type")
        if expected_type and expected_type in type_map:
            allowed = type_map[expected_type]
            # Don't count bools as ints (Python quirk)
            if expected_type in ("number", "integer") and isinstance(value, bool):
                errors.append(
                    f"Field '{field}' expected {expected_type}, got boolean"
                )
            elif not isinstance(value, allowed):
                errors.append(
                    f"Field '{field}' expected {expected_type}, got {type(value).__name__}"
                )

        # Enum check
        enum_values = properties[field].get("enum")
        if enum_values is not None and value not in enum_values:
            errors.append(
                f"Field '{field}' must be one of {enum_values}, got '{value}'"
            )

    if errors:
        return ToolError(
            tool_name=tool_name,
            error_type="validation",
            message="; ".join(errors),
            retry_allowed=True,
        )

    return args


# ---------------------------------------------------------------------------
# Cross-tenant entity reference check
# ---------------------------------------------------------------------------

# Mapping from *_id field suffix patterns to (model_class, table_name).
# Populated lazily to avoid circular imports at module level.
_ENTITY_MODEL_MAP: dict[str, type] | None = None


def _get_entity_model_map() -> dict[str, type]:
    """Build entity model map on first use (avoids circular imports)."""
    global _ENTITY_MODEL_MAP
    if _ENTITY_MODEL_MAP is None:
        from resonantia.models.experiment import Experiment
        from resonantia.models.plate import PlateMap
        from resonantia.models.sample import Sample
        from resonantia.models.protocol import Protocol
        from resonantia.models.eln_entry import ELNEntry
        from resonantia.models.microscopy import MicroscopyImage

        _ENTITY_MODEL_MAP = {
            "experiment_id": Experiment,
            "plate_map_id": PlateMap,
            "sample_id": Sample,
            "protocol_id": Protocol,
            "eln_entry_id": ELNEntry,
            "entry_id": ELNEntry,
            "image_id": MicroscopyImage,
        }
    return _ENTITY_MODEL_MAP


def _is_uuid(value: Any) -> bool:
    """Return True if *value* looks like a UUID string."""
    if not isinstance(value, str):
        return False
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


async def check_tenant_refs(
    args: dict[str, Any],
    org_id: str,
    db_session: AsyncSession,
) -> ToolError | None:
    """Check that any entity ID in *args* belongs to *org_id*.

    Only inspects top-level fields whose name ends with ``_id`` and whose
    value looks like a UUID.  Returns ``None`` on success, or a
    ``ToolError(forbidden)`` if a cross-tenant reference is detected.
    """
    model_map = _get_entity_model_map()

    for field, value in args.items():
        if not field.endswith("_id"):
            continue
        if not _is_uuid(value):
            continue

        model_cls = model_map.get(field)
        if model_cls is None:
            # Unknown _id field; skip (no model to check against)
            continue

        entity_uuid = uuid.UUID(value)
        entity = await db_session.get(model_cls, entity_uuid)

        if entity is None:
            return ToolError(
                tool_name="",  # caller fills this in
                error_type="forbidden",
                message="Entity not accessible",
                retry_allowed=False,
            )

        if hasattr(entity, "org_id") and entity.org_id != org_id:
            return ToolError(
                tool_name="",
                error_type="forbidden",
                message="Entity not accessible",
                retry_allowed=False,
            )

    return None
