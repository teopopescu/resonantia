"""Voice chat endpoint — chained pipeline: Whisper STT -> agent -> TTS."""

import hashlib
import os
import uuid
import tempfile
import logging
import time
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.config import get_settings
from resonantia.db.session import get_db
from resonantia.dependencies import get_request_context
from resonantia.middleware import log_stage_latency
from resonantia.models.request_context import RequestContext
from resonantia.models.voice_turn import VoiceTurn
from resonantia.services.agent import chat as agent_chat
from resonantia.services.storage import get_storage, is_signed_url
from resonantia.services.stt import OpenAISTTProvider
from resonantia.services.tts import OpenAITTSProvider
from resonantia.api.voice_events import router as voice_events_router
from resonantia.workflows.voice_turn_workflow import VoiceTurnInput, VoiceTurnWorkflow

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory registry of generated audio files
_audio_registry: dict[str, str] = {}

_SAFE_EXTENSIONS = {".webm", ".wav", ".mp3", ".m4a", ".ogg"}


async def _start_voice_turn_workflow(inp: VoiceTurnInput) -> str:
    from resonantia.services.temporal_client import get_temporal_client

    client = await get_temporal_client()
    settings = get_settings()
    workflow_id = inp.workflow_id or f"voice-{inp.idempotency_key}"
    await client.start_workflow(
        VoiceTurnWorkflow.run,
        inp,
        id=workflow_id,
        task_queue=settings.temporal_task_queue,
    )
    return workflow_id


def _safe_audio_extension(filename: str | None) -> str:
    ext = Path(filename or "recording.webm").suffix.lower()
    return ext if ext in _SAFE_EXTENSIONS else ".webm"


router.include_router(voice_events_router)


@router.post("/turn", status_code=202)
async def start_voice_turn(
    request: Request,
    audio: UploadFile = File(...),
    conversation_id: str | None = Form(default=None),
    ctx: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    """Start a durable voice turn workflow and return immediately."""
    settings = get_settings()
    content = await audio.read()
    if not content:
        raise HTTPException(status_code=400, detail="Audio upload is empty")

    turn_id = str(uuid.uuid4())
    ext = _safe_audio_extension(audio.filename)
    input_dir = Path(settings.upload_dir) / "voice" / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    input_path = input_dir / f"{turn_id}{ext}"
    input_path.write_bytes(content)

    idempotency_key = hashlib.sha256(
        f"{ctx.org_id}:{ctx.user_id}:{turn_id}".encode("utf-8")
    ).hexdigest()
    workflow_id = f"voice-{turn_id}"
    turn = VoiceTurn(
        id=uuid.UUID(turn_id),
        org_id=ctx.org_id,
        created_by=ctx.user_id,
        idempotency_key=idempotency_key,
        status="processing",
        workflow_id=workflow_id,
        conversation_id=conversation_id,
        input_audio_path=os.fspath(input_path),
        tool_calls=[],
    )
    db.add(turn)
    await db.flush()
    await db.commit()

    try:
        await _start_voice_turn_workflow(
            VoiceTurnInput(
                org_id=ctx.org_id,
                user_id=ctx.user_id,
                idempotency_key=idempotency_key,
                input_audio_path=os.fspath(input_path),
                conversation_id=conversation_id,
                request_context=ctx.model_dump(),
                workflow_id=workflow_id,
            )
        )
    except Exception as exc:
        turn.status = "failed"
        turn.error_message = f"Could not start voice workflow: {exc.__class__.__name__}"
        await db.commit()
        raise HTTPException(status_code=503, detail="Could not start voice workflow") from exc

    return {
        "turn_id": turn_id,
        "stream_url": f"/api/v1/voice/turns/{turn_id}/events",
    }


@router.post("/chat")
async def voice_chat(
    request: Request,
    audio: UploadFile = File(...),
    conversation_id: str = Form(default="default"),
    ctx: RequestContext = Depends(get_request_context),
):
    """Single endpoint: receive audio -> transcribe -> agent chat -> TTS -> return all."""
    logger.warning("Deprecated endpoint /api/v1/voice/chat used; use /api/v1/voice/turn")
    settings = get_settings()

    if not settings.openai_api_key:
        raise HTTPException(
            status_code=400,
            detail="OpenAI API key not configured. Voice mode requires OPENAI_API_KEY.",
        )

    stt_provider = OpenAISTTProvider(api_key=settings.openai_api_key, default_model=settings.stt_model)
    tts_provider = OpenAITTSProvider(api_key=settings.openai_api_key, default_model=settings.tts_model)

    # 1. Save uploaded audio to temp file
    suffix = os.path.splitext(audio.filename or "recording.webm")[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 2. Whisper STT
        stt_start = time.monotonic()
        with open(tmp_path, "rb") as f:
            transcribed_text = await stt_provider.transcribe(f)
        log_stage_latency("stt", (time.monotonic() - stt_start) * 1000)

        if not transcribed_text:
            return {
                "error": "no_speech_detected",
                "transcription": "",
                "response": "",
                "audio_url": None,
                "conversation_id": conversation_id,
            }

        # 3. Agent chat (full agentic loop with tools)
        agent_start = time.monotonic()
        chat_result = await agent_chat(
            message=transcribed_text,
            conversation_id=conversation_id,
            request_context=ctx,
            source="voice",
            request_id=getattr(request.state, "request_id", None),
        )
        log_stage_latency("agent", (time.monotonic() - agent_start) * 1000)
        response_text = chat_result.get("message", "")

        # 4. TTS — generate spoken response
        tts_start = time.monotonic()
        audio_bytes = await tts_provider.synthesize(response_text[:4096], voice=settings.tts_voice)
        log_stage_latency("tts", (time.monotonic() - tts_start) * 1000)

        # Save TTS audio
        audio_id = uuid.uuid4().hex
        storage_path = f"voice/output/{audio_id}.mp3"
        storage = get_storage("s3" if settings.storage_backend.lower() == "s3" else "local")
        await storage.save(storage_path, audio_bytes, "audio/mpeg")
        logger.info("TTS audio saved: %s (%d bytes)", storage_path, len(audio_bytes))

        _audio_registry[audio_id] = storage_path
        audio_url = storage.url(storage_path)
        if not is_signed_url(audio_url):
            audio_url = f"/api/v1/voice/audio/{audio_id}"

        return {
            "transcription": transcribed_text,
            "response": response_text,
            "audio_url": audio_url,
            "conversation_id": chat_result.get("conversation_id", conversation_id),
            "tool_calls": chat_result.get("tool_calls"),
        }

    finally:
        # Clean up temp input file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@router.get("/audio/{audio_id}")
async def get_audio(audio_id: str):
    """Serve a generated TTS audio file."""
    storage_path = _audio_registry.get(audio_id)
    settings = get_settings()
    storage = get_storage("s3" if settings.storage_backend.lower() == "s3" else "local")
    if storage_path:
        signed_url = storage.url(storage_path)
        if is_signed_url(signed_url):
            return RedirectResponse(signed_url, status_code=307)
        path = os.path.join(settings.upload_dir, storage_path)
    else:
        # Try finding it in the voice directory
        path = os.path.join(settings.upload_dir, "voice", f"{audio_id}.mp3")
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Audio not found")

    return FileResponse(
        path,
        media_type="audio/mpeg",
        filename=f"{audio_id}.mp3",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600",
        },
    )
