"""Repository helpers for durable processing tool outputs."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.models.processing_result import ProcessingResult


def make_idempotency_key(
    *,
    file_upload_id: str | None,
    analysis_type: str,
    parameters: dict[str, Any],
) -> str:
    payload = {
        "file_upload_id": file_upload_id,
        "analysis_type": analysis_type,
        "parameters": parameters,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def parse_optional_uuid(value: str | uuid.UUID | None) -> uuid.UUID | None:
    if value is None or value == "":
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except ValueError:
        return None


class ProcessingResultRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_idempotency_key(
        self,
        *,
        org_id: str,
        idempotency_key: str,
    ) -> ProcessingResult | None:
        return await self._session.scalar(
            select(ProcessingResult).where(
                ProcessingResult.org_id == org_id,
                ProcessingResult.idempotency_key == idempotency_key,
            )
        )

    async def create(
        self,
        *,
        org_id: str,
        created_by: str | None,
        idempotency_key: str,
        analysis_type: str,
        parameters: dict[str, Any],
        result: dict[str, Any],
        file_upload_id: str | uuid.UUID | None = None,
        experiment_id: str | uuid.UUID | None = None,
    ) -> ProcessingResult:
        record = ProcessingResult(
            org_id=org_id,
            created_by=created_by,
            idempotency_key=idempotency_key,
            analysis_type=analysis_type,
            parameters=parameters,
            result=result,
            file_upload_id=parse_optional_uuid(file_upload_id),
            experiment_id=parse_optional_uuid(experiment_id),
        )
        self._session.add(record)
        await self._session.flush()
        return record
