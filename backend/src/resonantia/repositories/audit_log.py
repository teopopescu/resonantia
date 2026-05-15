"""Append-only audit log repository."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.models.audit_log import AuditLog
from resonantia.models.request_context import RequestContext


class AuditLogRepository:
    """Write-only audit log repository.

    This class intentionally exposes only ``append``. Audit rows are immutable
    from the application layer; schema-level UPDATE/DELETE revocation is added
    in the Phase 2.1 migration for PostgreSQL.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(
        self,
        *,
        org_id: str,
        action: str,
        actor_user_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        request_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        message: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            org_id=org_id,
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            request_id=request_id,
            metadata_extra=metadata or {},
            message=message,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry


async def append_audit_log(
    session: AsyncSession,
    *,
    ctx: RequestContext | None = None,
    org_id: str | None = None,
    action: str,
    actor_user_id: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    message: str | None = None,
) -> AuditLog:
    return await AuditLogRepository(session).append(
        org_id=org_id or (ctx.org_id if ctx else "org_default"),
        actor_user_id=actor_user_id or (ctx.user_id if ctx else None),
        action=action,
        target_type=target_type,
        target_id=target_id,
        request_id=request_id or (ctx.request_id if ctx else None),
        metadata=metadata,
        message=message,
    )
