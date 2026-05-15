"""Tests for durable voice turn API endpoints."""

from __future__ import annotations

import io
import logging
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.models.voice_turn import VoiceTurn


@pytest.fixture
def voice_upload_dir(tmp_path, monkeypatch):
    from resonantia.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path), raising=False)
    return tmp_path


@pytest.mark.asyncio
async def test_post_voice_turn_returns_immediate_stream_url(
    client: AsyncClient,
    db_session: AsyncSession,
    voice_upload_dir,
    monkeypatch,
):
    from resonantia.api import voice

    started = {}

    async def _fake_start(inp):
        started["workflow_id"] = inp.workflow_id
        started["input_audio_path"] = inp.input_audio_path
        return inp.workflow_id

    monkeypatch.setattr(voice, "_start_voice_turn_workflow", _fake_start)
    response = await client.post(
        "/api/v1/voice/turn",
        files={"audio": ("speech.webm", io.BytesIO(b"audio"), "audio/webm")},
        data={"conversation_id": "conv-1"},
        headers={"X-Org-Id": "org_voice"},
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["turn_id"]
    assert payload["stream_url"] == f"/api/v1/voice/turns/{payload['turn_id']}/events"
    assert started["workflow_id"] == f"voice-{payload['turn_id']}"

    turn = await db_session.get(VoiceTurn, uuid.UUID(payload["turn_id"]))
    assert turn is not None
    assert turn.org_id == "org_voice"
    assert turn.status == "processing"
    assert turn.conversation_id == "conv-1"
    assert turn.input_audio_path == started["input_audio_path"]


@pytest.mark.asyncio
async def test_voice_turn_events_stream_transcript_and_done(
    client: AsyncClient,
    db_session: AsyncSession,
):
    turn_id = uuid.uuid4()
    db_session.add(
        VoiceTurn(
            id=turn_id,
            org_id="org_voice",
            created_by="test-user",
            idempotency_key="events-key",
            status="completed",
            transcript="hello lab",
            response_text="hello back",
            output_audio_id="audio-1",
            tool_calls=[{"name": "lookup_sample", "result": {"found": True}}],
            stt_latency_ms=1,
            agent_latency_ms=2,
            tts_latency_ms=3,
            total_latency_ms=6,
        )
    )
    await db_session.commit()

    async with client.stream(
        "GET",
        f"/api/v1/voice/turns/{turn_id}/events",
        headers={"X-Org-Id": "org_voice"},
    ) as response:
        body = await response.aread()

    text = body.decode()
    assert response.status_code == 200
    assert "event: transcript" in text
    assert "hello lab" in text
    assert "event: audio_ready" in text
    assert "event: done" in text


@pytest.mark.asyncio
async def test_voice_audio_endpoint_returns_binary(
    client: AsyncClient,
    voice_upload_dir,
):
    audio_id = "binary-audio"
    audio_dir = voice_upload_dir / "voice"
    audio_dir.mkdir()
    (audio_dir / f"{audio_id}.mp3").write_bytes(b"mp3-bytes")

    response = await client.get(f"/api/v1/voice/audio/{audio_id}")
    assert response.status_code == 200
    assert response.content == b"mp3-bytes"
    assert response.headers["content-type"].startswith("audio/mpeg")


@pytest.mark.asyncio
async def test_legacy_voice_chat_logs_deprecation_warning(
    client: AsyncClient,
    voice_upload_dir,
    monkeypatch,
    caplog,
):
    from resonantia.api import voice

    class _FakeSTT:
        async def transcribe(self, audio_file):
            return "hello"

    class _FakeTTS:
        async def synthesize(self, text, *, voice=None):
            return b"mp3"

    async def _fake_chat(**kwargs):
        return {"message": "hi", "conversation_id": "conv-1", "tool_calls": None}

    monkeypatch.setattr(voice, "OpenAISTTProvider", lambda **kwargs: _FakeSTT())
    monkeypatch.setattr(voice, "OpenAITTSProvider", lambda **kwargs: _FakeTTS())
    monkeypatch.setattr(voice, "agent_chat", _fake_chat)

    with caplog.at_level(logging.WARNING):
        response = await client.post(
            "/api/v1/voice/chat",
            files={"audio": ("speech.webm", io.BytesIO(b"audio"), "audio/webm")},
            data={"conversation_id": "conv-1"},
        )

    assert response.status_code == 200
    assert "Deprecated endpoint /api/v1/voice/chat used" in caplog.text
