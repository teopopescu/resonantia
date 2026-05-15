"""Tests for durable voice turn workflow primitives."""

from __future__ import annotations

import inspect
import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.models.voice_turn import VoiceTurn
from tests.conftest import _test_session_factory


class _FakeSTT:
    async def transcribe(self, audio_file, *, model: str | None = None) -> str:
        return "Find sample A1"


class _FakeTTS:
    async def synthesize(self, text: str, *, model: str | None = None, voice: str | None = None) -> bytes:
        return b"fake-mp3"


async def _fake_agent_chat(*, message, conversation_id, request_context):
    return {
        "message": f"Found result for: {message}",
        "conversation_id": conversation_id or str(uuid.uuid4()),
        "tool_calls": [{"name": "lookup_sample", "input": {"query": "A1"}}],
    }


@pytest.fixture
def voice_activity_fakes(tmp_path, monkeypatch):
    from resonantia.config import get_settings
    from resonantia.workflows import voice_activities

    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path), raising=False)
    monkeypatch.setattr(voice_activities, "async_session_factory", _test_session_factory)
    monkeypatch.setattr(voice_activities, "_get_stt_provider", lambda: _FakeSTT())
    monkeypatch.setattr(voice_activities, "_get_tts_provider", lambda: _FakeTTS())
    monkeypatch.setattr(voice_activities, "_agent_chat", _fake_agent_chat)
    return tmp_path


@pytest.mark.asyncio
async def test_voice_turn_activities_complete_end_to_end(
    db_session: AsyncSession,
    voice_activity_fakes,
):
    from resonantia.workflows.voice_activities import (
        complete_voice_turn_activity,
        create_voice_turn_activity,
        run_voice_agent_activity,
        synthesize_voice_turn_activity,
        transcribe_voice_turn_activity,
    )

    audio_path = voice_activity_fakes / "input.webm"
    audio_path.write_bytes(b"audio")
    create = await create_voice_turn_activity(
        "org_voice",
        "user_voice",
        "turn-key-1",
        "conversation-1",
        str(audio_path),
        "workflow-1",
    )
    stt = await transcribe_voice_turn_activity(create["turn_id"], str(audio_path))
    agent = await run_voice_agent_activity(
        create["turn_id"],
        stt["transcript"],
        "conversation-1",
        {"user_id": "user_voice", "org_id": "org_voice", "roles": ["org:admin"], "permissions": []},
    )
    tts = await synthesize_voice_turn_activity(create["turn_id"], agent["response_text"])
    done = await complete_voice_turn_activity(
        create["turn_id"],
        stt["transcript"],
        agent["response_text"],
        tts["audio_id"],
        agent["conversation_id"],
        agent["tool_calls"],
        agent["intent_class"],
        stt["stt_latency_ms"],
        agent["agent_latency_ms"],
        tts["tts_latency_ms"],
    )

    assert done["status"] == "completed"
    turn = await db_session.get(VoiceTurn, uuid.UUID(create["turn_id"]))
    assert turn is not None
    assert turn.status == "completed"
    assert turn.transcript == "Find sample A1"
    assert turn.response_text.startswith("Found result")
    assert turn.output_audio_id == tts["audio_id"]
    assert turn.stt_latency_ms is not None
    assert turn.agent_latency_ms is not None
    assert turn.tts_latency_ms is not None
    assert turn.total_latency_ms is not None
    assert turn.intent_class == "tool"
    assert turn.tool_calls and turn.tool_calls[0]["name"] == "lookup_sample"


@pytest.mark.asyncio
async def test_voice_turn_create_is_idempotent_after_worker_restart(
    db_session: AsyncSession,
    voice_activity_fakes,
):
    from resonantia.workflows.voice_activities import create_voice_turn_activity

    audio_path = voice_activity_fakes / "input.webm"
    audio_path.write_bytes(b"audio")
    first = await create_voice_turn_activity(
        "org_voice",
        "user_voice",
        "restart-key",
        None,
        str(audio_path),
        "workflow-1",
    )
    second = await create_voice_turn_activity(
        "org_voice",
        "user_voice",
        "restart-key",
        None,
        str(audio_path),
        "workflow-1-retry",
    )

    assert second["reused"] is True
    assert second["turn_id"] == first["turn_id"]
    count = await db_session.scalar(select(func.count()).select_from(VoiceTurn))
    assert count == 1


def test_voice_turn_workflow_uses_required_activity_timeouts():
    from resonantia.workflows.voice_turn_workflow import VoiceTurnWorkflow

    source = inspect.getsource(VoiceTurnWorkflow.run)
    assert "transcribe_voice_turn_activity" in source
    assert "run_voice_agent_activity" in source
    assert "synthesize_voice_turn_activity" in source
    assert "timedelta(seconds=10)" in source
    assert "timedelta(seconds=30)" in source
