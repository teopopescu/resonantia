"""Tests for processing and voice-turn idempotency enforcement."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.models.voice_turn import VoiceTurn
from resonantia.repositories.processing_result import ProcessingResultRepository


@pytest.mark.asyncio
async def test_processing_result_repository_duplicate_key_returns_existing(db_session: AsyncSession):
    repo = ProcessingResultRepository(db_session)
    key = f"idem-{uuid.uuid4()}"

    first = await repo.create(
        org_id="org_idem",
        created_by="user-1",
        idempotency_key=key,
        analysis_type="dose_response",
        parameters={"model": "4pl"},
        result={"success": True},
    )
    second = await repo.create(
        org_id="org_idem",
        created_by="user-1",
        idempotency_key=key,
        analysis_type="dose_response",
        parameters={"model": "4pl"},
        result={"success": True},
    )

    assert second.id == first.id
    count = await db_session.scalar(select(func.count()).select_from(type(first)))
    assert count == 1


@pytest.mark.asyncio
async def test_voice_turn_partial_idempotency_allows_null_keys(db_session: AsyncSession):
    db_session.add_all([
        VoiceTurn(
            org_id="org_voice",
            created_by="user-1",
            idempotency_key=None,
            status="processing",
        ),
        VoiceTurn(
            org_id="org_voice",
            created_by="user-1",
            idempotency_key=None,
            status="processing",
        ),
    ])
    await db_session.commit()

    count = await db_session.scalar(select(func.count()).select_from(VoiceTurn))
    assert count == 2


def test_voice_turn_idempotency_uses_partial_unique_index():
    indexes = {index.name: index for index in VoiceTurn.__table__.indexes}
    index = indexes["uq_voice_turns_org_idempotency"]

    assert index.unique is True
    assert [column.name for column in index.columns] == ["org_id", "idempotency_key"]
    assert index.dialect_options["postgresql"]["where"] is not None
    assert index.dialect_options["sqlite"]["where"] is not None
