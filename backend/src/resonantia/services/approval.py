"""DB-backed approval gates for human-in-the-loop tool execution."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.models.pending_approval import PendingApprovalRecord


class GateKind(str, Enum):
    NONE = "none"
    SOFT_REVIEW = "soft_review"
    HARD_APPROVAL = "hard_approval"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


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
    status: ApprovalStatus = ApprovalStatus.PENDING


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

APPROVAL_TTL_SECONDS = 600


def get_gate(tool_name: str) -> GateKind:
    return TOOL_GATES.get(tool_name, GateKind.NONE)


def is_gated(tool_name: str) -> bool:
    return get_gate(tool_name) != GateKind.NONE


def approval_card(pending: PendingApproval) -> dict[str, Any]:
    return {
        "type": "approval_card",
        "token": pending.token,
        "tool_name": pending.tool_name,
        "tool_args": pending.tool_args,
        "gate_kind": pending.gate_kind.value,
        "preview": pending.preview,
        "expires_at": pending.expires_at.isoformat(),
    }


def pending_from_record(record: PendingApprovalRecord) -> PendingApproval:
    created_at = record.created_at or datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return PendingApproval(
        token=record.token,
        tool_name=record.tool_name,
        tool_args=record.tool_args,
        org_id=record.org_id,
        user_id=record.requested_by,
        preview=record.preview,
        gate_kind=GateKind(record.gate_kind),
        created_at=created_at,
        expires_at=expires_at,
        status=ApprovalStatus(record.status),
    )


async def create_pending(
    session: AsyncSession,
    tool_name: str,
    tool_args: dict[str, Any],
    org_id: str,
    user_id: str,
    preview: dict[str, Any],
) -> PendingApproval:
    token = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    record = PendingApprovalRecord(
        token=token,
        org_id=org_id,
        requested_by=user_id,
        tool_name=tool_name,
        tool_args=tool_args,
        preview=preview,
        gate_kind=get_gate(tool_name).value,
        status=ApprovalStatus.PENDING.value,
        expires_at=now + timedelta(seconds=APPROVAL_TTL_SECONDS),
        created_at=now,
        updated_at=now,
    )
    session.add(record)
    await session.flush()
    return pending_from_record(record)


async def get_pending_record(
    session: AsyncSession,
    token: str,
    *,
    for_update: bool = False,
) -> PendingApprovalRecord | None:
    stmt = select(PendingApprovalRecord).where(PendingApprovalRecord.token == token)
    if for_update:
        stmt = stmt.with_for_update()
    return await session.scalar(stmt)


def is_expired(record: PendingApprovalRecord) -> bool:
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) > expires_at


async def mark_expired(session: AsyncSession, record: PendingApprovalRecord) -> None:
    record.status = ApprovalStatus.EXPIRED.value
    await session.flush()


async def reject_pending(
    session: AsyncSession,
    record: PendingApprovalRecord,
    *,
    decided_by: str,
) -> PendingApprovalRecord:
    record.status = ApprovalStatus.REJECTED.value
    record.decided_by = decided_by
    record.decided_at = datetime.now(timezone.utc)
    await session.flush()
    return record


async def claim_for_approval(
    session: AsyncSession,
    record: PendingApprovalRecord,
    *,
    decided_by: str,
) -> PendingApprovalRecord:
    record.status = ApprovalStatus.APPROVED.value
    record.decided_by = decided_by
    record.decided_at = datetime.now(timezone.utc)
    await session.flush()
    return record
