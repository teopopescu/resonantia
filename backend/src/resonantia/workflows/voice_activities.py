"""Temporal activities for the durable voice turn pipeline."""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from temporalio import activity

from resonantia.config import get_settings
from resonantia.db.session import async_session_factory
from resonantia.models.voice_turn import VoiceTurn


def _classify_intent(transcript: str, tool_calls: list[dict[str, Any]] | None) -> str:
    if tool_calls:
        return "tool"
    lower = transcript.lower()
    if any(word in lower for word in ("where", "lookup", "find", "inventory", "sample")):
        return "lookup"
    if any(word in lower for word in ("calculate", "fit", "analyze", "analyse", "z-prime", "ic50")):
        return "analysis"
    return "chat"


def _get_stt_provider():
    from resonantia.services.stt import OpenAISTTProvider

    settings = get_settings()
    return OpenAISTTProvider(api_key=settings.openai_api_key, default_model=settings.stt_model)


def _get_tts_provider():
    from resonantia.services.tts import OpenAITTSProvider

    settings = get_settings()
    return OpenAITTSProvider(api_key=settings.openai_api_key, default_model=settings.tts_model)


async def _agent_chat(
    *,
    message: str,
    conversation_id: str | None,
    request_context: dict[str, Any] | None,
):
    from resonantia.models.request_context import RequestContext
    from resonantia.services.agent import chat

    ctx = RequestContext(**request_context) if request_context else None
    return await chat(
        message=message,
        conversation_id=conversation_id,
        request_context=ctx,
        source="voice",
        request_id=request_context.get("request_id") if request_context else None,
    )


@activity.defn
async def create_voice_turn_activity(
    org_id: str,
    user_id: str,
    idempotency_key: str,
    conversation_id: str | None,
    input_audio_path: str,
    workflow_id: str | None = None,
) -> dict[str, Any]:
    async with async_session_factory() as session:
        existing = await session.scalar(
            select(VoiceTurn).where(
                VoiceTurn.org_id == org_id,
                VoiceTurn.idempotency_key == idempotency_key,
            )
        )
        if existing:
            existing.status = "processing"
            existing.error_message = None
            await session.commit()
            return {"turn_id": str(existing.id), "reused": True}

        turn = VoiceTurn(
            org_id=org_id,
            created_by=user_id,
            idempotency_key=idempotency_key,
            status="processing",
            workflow_id=workflow_id,
            conversation_id=conversation_id,
            input_audio_path=input_audio_path,
            tool_calls=[],
        )
        session.add(turn)
        try:
            await session.commit()
            await session.refresh(turn)
        except IntegrityError:
            await session.rollback()
            existing = await session.scalar(
                select(VoiceTurn).where(
                    VoiceTurn.org_id == org_id,
                    VoiceTurn.idempotency_key == idempotency_key,
                )
            )
            if existing:
                existing.status = "processing"
                existing.error_message = None
                await session.commit()
                return {"turn_id": str(existing.id), "reused": True}
            raise
        return {"turn_id": str(turn.id), "reused": False}


@activity.defn
async def transcribe_voice_turn_activity(turn_id: str, input_audio_path: str) -> dict[str, Any]:
    start = time.monotonic()
    provider = _get_stt_provider()
    with open(input_audio_path, "rb") as audio_file:
        transcript = await provider.transcribe(audio_file)
    latency_ms = int((time.monotonic() - start) * 1000)

    async with async_session_factory() as session:
        turn = await session.get(VoiceTurn, uuid.UUID(turn_id))
        if turn:
            turn.transcript = transcript
            turn.stt_latency_ms = latency_ms
            await session.commit()

    return {"transcript": transcript, "stt_latency_ms": latency_ms}


@activity.defn
async def run_voice_agent_activity(
    turn_id: str,
    transcript: str,
    conversation_id: str | None,
    request_context: dict[str, Any] | None,
) -> dict[str, Any]:
    start = time.monotonic()
    result = await _agent_chat(
        message=transcript,
        conversation_id=conversation_id,
        request_context=request_context,
    )
    latency_ms = int((time.monotonic() - start) * 1000)
    response_text = result.get("message", "")
    tool_calls = result.get("tool_calls") or []
    intent_class = _classify_intent(transcript, tool_calls)

    async with async_session_factory() as session:
        turn = await session.get(VoiceTurn, uuid.UUID(turn_id))
        if turn:
            turn.response_text = response_text
            turn.conversation_id = result.get("conversation_id") or conversation_id
            turn.tool_calls = tool_calls
            turn.intent_class = intent_class
            turn.agent_latency_ms = latency_ms
            await session.commit()

    return {
        "response_text": response_text,
        "conversation_id": result.get("conversation_id") or conversation_id,
        "tool_calls": tool_calls,
        "intent_class": intent_class,
        "agent_latency_ms": latency_ms,
    }


@activity.defn
async def synthesize_voice_turn_activity(turn_id: str, response_text: str) -> dict[str, Any]:
    start = time.monotonic()
    settings = get_settings()
    provider = _get_tts_provider()
    audio_bytes = await provider.synthesize(response_text[:4096], voice=settings.tts_voice)
    latency_ms = int((time.monotonic() - start) * 1000)

    audio_id = uuid.uuid4().hex
    voice_dir = Path(settings.upload_dir) / "voice"
    voice_dir.mkdir(parents=True, exist_ok=True)
    audio_path = voice_dir / f"{audio_id}.mp3"
    audio_path.write_bytes(audio_bytes)

    async with async_session_factory() as session:
        turn = await session.get(VoiceTurn, uuid.UUID(turn_id))
        if turn:
            turn.output_audio_id = audio_id
            turn.tts_latency_ms = latency_ms
            await session.commit()

    return {
        "audio_id": audio_id,
        "audio_path": os.fspath(audio_path),
        "tts_latency_ms": latency_ms,
    }


@activity.defn
async def complete_voice_turn_activity(
    turn_id: str,
    transcript: str,
    response_text: str,
    audio_id: str | None,
    conversation_id: str | None,
    tool_calls: list[dict[str, Any]],
    intent_class: str | None,
    stt_latency_ms: int,
    agent_latency_ms: int,
    tts_latency_ms: int,
) -> dict[str, Any]:
    total_latency_ms = stt_latency_ms + agent_latency_ms + tts_latency_ms
    async with async_session_factory() as session:
        turn = await session.get(VoiceTurn, uuid.UUID(turn_id))
        if turn is None:
            return {"turn_id": turn_id, "status": "missing"}
        turn.status = "completed"
        turn.transcript = transcript
        turn.response_text = response_text
        turn.output_audio_id = audio_id
        turn.conversation_id = conversation_id
        turn.tool_calls = tool_calls
        turn.intent_class = intent_class
        turn.stt_latency_ms = stt_latency_ms
        turn.agent_latency_ms = agent_latency_ms
        turn.tts_latency_ms = tts_latency_ms
        turn.total_latency_ms = total_latency_ms
        turn.error_message = None
        await session.commit()
        return {
            "turn_id": str(turn.id),
            "status": turn.status,
            "total_latency_ms": total_latency_ms,
        }


@activity.defn
async def fail_voice_turn_activity(turn_id: str, error_message: str) -> None:
    async with async_session_factory() as session:
        turn = await session.get(VoiceTurn, uuid.UUID(turn_id))
        if turn:
            turn.status = "failed"
            turn.error_message = error_message
            await session.commit()
