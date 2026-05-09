"""Approval gate service for human-in-the-loop tool execution.

Tools classified as soft_review or hard_approval return a pending approval
token instead of executing immediately. The user confirms or rejects via
the /chat/approve and /chat/reject endpoints.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel


class GateKind(str, Enum):
    NONE = "none"
    SOFT_REVIEW = "soft_review"
    HARD_APPROVAL = "hard_approval"


class PendingApproval(BaseModel):
    token: str
    tool_name: str
    tool_args: dict[str, Any]
    org_id: str
    user_id: str
    preview: dict[str, Any]
    gate_kind: GateKind
    created_at: datetime
    expires_at: datetime


TOOL_GATES: dict[str, GateKind] = {
    "lookup_sample": GateKind.NONE,
    "check_inventory": GateKind.NONE,
    "get_expiring_samples": GateKind.NONE,
    "query_experiments": GateKind.NONE,
    "query_eln_entries": GateKind.NONE,
    "query_protocols": GateKind.NONE,
    "query_plate_maps": GateKind.NONE,
    "calculate_dilution": GateKind.NONE,
    "fit_dose_response": GateKind.NONE,
    "normalize_plate": GateKind.NONE,
    "calculate_z_prime": GateKind.NONE,
    "qpcr_analysis": GateKind.NONE,
    "read_file_contents": GateKind.NONE,
    "browse_microscopy": GateKind.NONE,
    "generate_montage": GateKind.NONE,
    "get_ic50_values": GateKind.NONE,
    "get_plate_map_details": GateKind.NONE,
    "get_file_info": GateKind.NONE,
    "list_files": GateKind.NONE,
    "get_sample_stats": GateKind.NONE,

    "create_eln_entry": GateKind.SOFT_REVIEW,
    "create_plate_map": GateKind.SOFT_REVIEW,
    "create_protocol": GateKind.SOFT_REVIEW,
    "serial_dilution": GateKind.SOFT_REVIEW,
    "cherry_pick": GateKind.SOFT_REVIEW,
    "create_experiment": GateKind.SOFT_REVIEW,

    "submit_eln_entry": GateKind.HARD_APPROVAL,
    "generate_worklist": GateKind.HARD_APPROVAL,
}

_pending: dict[str, PendingApproval] = {}

APPROVAL_TTL_SECONDS = 600


def get_gate(tool_name: str) -> GateKind:
    return TOOL_GATES.get(tool_name, GateKind.NONE)


def create_pending(
    tool_name: str,
    tool_args: dict[str, Any],
    org_id: str,
    user_id: str,
    preview: dict[str, Any],
) -> PendingApproval:
    token = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    pending = PendingApproval(
        token=token,
        tool_name=tool_name,
        tool_args=tool_args,
        org_id=org_id,
        user_id=user_id,
        preview=preview,
        gate_kind=get_gate(tool_name),
        created_at=now,
        expires_at=now + timedelta(seconds=APPROVAL_TTL_SECONDS),
    )
    _pending[token] = pending
    return pending


def get_pending(token: str) -> PendingApproval | None:
    pending = _pending.get(token)
    if pending is None:
        return None
    if datetime.now(timezone.utc) > pending.expires_at:
        _pending.pop(token, None)
        return None
    return pending


def approve(token: str) -> PendingApproval | None:
    pending = get_pending(token)
    if pending is None:
        return None
    _pending.pop(token, None)
    return pending


def reject(token: str) -> bool:
    return _pending.pop(token, None) is not None


def is_gated(tool_name: str) -> bool:
    return get_gate(tool_name) != GateKind.NONE
