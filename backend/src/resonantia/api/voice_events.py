"""SSE events for durable voice turns."""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from resonantia.db.session import get_db
from resonantia.dependencies import get_request_context
from resonantia.models.request_context import RequestContext
from resonantia.models.voice_turn import VoiceTurn

router = APIRouter()


def _parse_turn_id(turn_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(turn_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Voice turn not found") from None


def _event(name: str, payload: dict) -> dict[str, str]:
    return {"event": name, "data": json.dumps(payload, default=str)}


async def _load_turn(db: AsyncSession, turn_id: str, org_id: str) -> VoiceTurn:
    turn = await db.get(VoiceTurn, _parse_turn_id(turn_id))
    if not turn or turn.org_id != org_id:
        raise HTTPException(status_code=404, detail="Voice turn not found")
    return turn


@router.get("/turns/{turn_id}/events")
async def stream_voice_turn_events(
    turn_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
) -> EventSourceResponse:
    """Stream voice turn progress as Server-Sent Events."""
    await _load_turn(db, turn_id, ctx.org_id)

    async def _gen() -> AsyncGenerator[dict[str, str], None]:
        emitted: set[str] = set()
        for _ in range(120):
            await db.rollback()
            turn = await _load_turn(db, turn_id, ctx.org_id)

            if turn.transcript and "transcript" not in emitted:
                emitted.add("transcript")
                yield _event("transcript", {"turn_id": turn_id, "text": turn.transcript, "confidence": 1.0})

            if turn.tool_calls and "tool_calls" not in emitted:
                emitted.add("tool_calls")
                for index, tool_call in enumerate(turn.tool_calls):
                    event_name = "approval_required" if _is_approval_tool_result(tool_call) else "tool_call"
                    yield _event(event_name, {"turn_id": turn_id, "index": index, "tool_call": tool_call})
                    if "result" in tool_call:
                        yield _event("tool_result", {"turn_id": turn_id, "index": index, "result": tool_call["result"]})

            if turn.response_text and "response" not in emitted:
                emitted.add("response")
                yield _event("response", {"turn_id": turn_id, "text": turn.response_text})

            if turn.output_audio_id and "audio_ready" not in emitted:
                emitted.add("audio_ready")
                yield _event(
                    "audio_ready",
                    {
                        "turn_id": turn_id,
                        "audio_id": turn.output_audio_id,
                        "audio_url": f"/api/v1/voice/audio/{turn.output_audio_id}",
                    },
                )

            if turn.status in {"completed", "failed"}:
                yield _event(
                    "done",
                    {
                        "turn_id": turn_id,
                        "status": turn.status,
                        "error": turn.error_message,
                    },
                )
                break

            await asyncio.sleep(0.5)

    return EventSourceResponse(_gen())


def _is_approval_tool_result(tool_call: dict) -> bool:
    result = tool_call.get("result")
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            return False
    return isinstance(result, dict) and result.get("approval_required") is True
