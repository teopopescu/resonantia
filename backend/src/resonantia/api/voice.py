"""Voice chat endpoint — chained pipeline: Whisper STT -> agent -> TTS."""

import os
import uuid
import tempfile
import logging
import time

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Request
from fastapi.responses import FileResponse

from resonantia.config import get_settings
from resonantia.dependencies import get_request_context
from resonantia.middleware import log_stage_latency
from resonantia.models.request_context import RequestContext
from resonantia.services.agent import chat as agent_chat
from resonantia.services.stt import OpenAISTTProvider
from resonantia.services.tts import OpenAITTSProvider

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory registry of generated audio files
_audio_registry: dict[str, str] = {}


@router.post("/chat")
async def voice_chat(
    request: Request,
    audio: UploadFile = File(...),
    conversation_id: str = Form(default="default"),
    ctx: RequestContext = Depends(get_request_context),
):
    """Single endpoint: receive audio -> transcribe -> agent chat -> TTS -> return all."""
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
        voice_dir = os.path.join(settings.upload_dir, "voice")
        os.makedirs(voice_dir, exist_ok=True)
        audio_id = uuid.uuid4().hex
        audio_path = os.path.join(voice_dir, f"{audio_id}.mp3")
        # Write audio bytes to file (stream_to_file may not work in async context)
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)
        logger.info("TTS audio saved: %s (%d bytes)", audio_path, len(audio_bytes))

        _audio_registry[audio_id] = audio_path

        return {
            "transcription": transcribed_text,
            "response": response_text,
            "audio_url": f"/api/v1/voice/audio/{audio_id}",
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
    path = _audio_registry.get(audio_id)
    if not path or not os.path.exists(path):
        # Try finding it in the voice directory
        settings = get_settings()
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
