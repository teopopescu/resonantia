"""Retention jobs for voice audio artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.config import get_settings
from resonantia.models.voice_turn import VoiceTurn
from resonantia.services.storage import get_storage


@dataclass
class RetentionResult:
    input_deleted: int = 0
    output_deleted: int = 0
    missing: int = 0


async def cleanup_expired_voice_audio(
    session: AsyncSession,
    *,
    now: datetime | None = None,
    input_retention_days: int | None = None,
    output_retention_days: int | None = None,
) -> RetentionResult:
    """Delete expired voice input/output audio and clear DB references."""
    settings = get_settings()
    current = now or datetime.now(timezone.utc)
    input_days = input_retention_days if input_retention_days is not None else settings.voice_input_retention_days
    output_days = output_retention_days if output_retention_days is not None else settings.voice_output_retention_days
    input_cutoff = current - timedelta(days=input_days)
    output_cutoff = current - timedelta(days=output_days)
    result = RetentionResult()

    rows = await session.execute(
        select(VoiceTurn).where(
            (VoiceTurn.input_audio_path.is_not(None)) | (VoiceTurn.output_audio_id.is_not(None))
        )
    )
    turns = rows.scalars().all()
    for turn in turns:
        created_at = _as_aware(turn.created_at)
        if turn.input_audio_path and created_at < input_cutoff:
            if _delete_local_path(turn.input_audio_path):
                result.input_deleted += 1
            else:
                result.missing += 1
            turn.input_audio_path = None

        if turn.output_audio_id and created_at < output_cutoff:
            deleted = await _delete_output_audio(turn.output_audio_id)
            if deleted:
                result.output_deleted += 1
            else:
                result.missing += 1
            turn.output_audio_id = None

    await session.flush()
    return result


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _delete_local_path(path: str) -> bool:
    try:
        target = Path(path)
        if target.exists():
            target.unlink()
            return True
    except OSError:
        return False
    return False


async def _delete_output_audio(audio_id: str) -> bool:
    settings = get_settings()
    storage_backend = "s3" if settings.storage_backend.lower() == "s3" and settings.s3_bucket else "local"
    for storage_path in (f"voice/output/{audio_id}.mp3", f"voice/{audio_id}.mp3"):
        try:
            await get_storage(storage_backend).delete(storage_path)
            return True
        except FileNotFoundError:
            continue
        except OSError:
            continue
    return False
