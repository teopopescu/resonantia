"""Tests for voice audio retention."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.models.voice_turn import VoiceTurn
from resonantia.services.retention import cleanup_expired_voice_audio


@pytest.mark.asyncio
async def test_cleanup_expired_voice_audio_deletes_old_files(
    db_session: AsyncSession,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
):
    from resonantia.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    monkeypatch.setattr(settings, "storage_backend", "local")

    input_path = tmp_path / "voice" / "input" / "old.webm"
    input_path.parent.mkdir(parents=True)
    input_path.write_bytes(b"input")
    output_path = tmp_path / "voice" / "output" / "audio-old.mp3"
    output_path.parent.mkdir(parents=True)
    output_path.write_bytes(b"output")

    old_turn = VoiceTurn(
        id=uuid.uuid4(),
        org_id="org_retention",
        created_by="user-1",
        idempotency_key="old",
        status="completed",
        input_audio_path=str(input_path),
        output_audio_id="audio-old",
        created_at=datetime.now(timezone.utc) - timedelta(days=45),
    )
    recent_turn = VoiceTurn(
        id=uuid.uuid4(),
        org_id="org_retention",
        created_by="user-1",
        idempotency_key="recent",
        status="completed",
        input_audio_path=str(tmp_path / "recent.webm"),
        output_audio_id="audio-recent",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add_all([old_turn, recent_turn])
    await db_session.commit()

    result = await cleanup_expired_voice_audio(
        db_session,
        now=datetime.now(timezone.utc),
        input_retention_days=30,
        output_retention_days=7,
    )
    await db_session.commit()

    assert result.input_deleted == 1
    assert result.output_deleted == 1
    assert not input_path.exists()
    assert not output_path.exists()
    await db_session.refresh(old_turn)
    await db_session.refresh(recent_turn)
    assert old_turn.input_audio_path is None
    assert old_turn.output_audio_id is None
    assert recent_turn.output_audio_id == "audio-recent"


def test_terraform_enables_rds_encryption_and_s3_lifecycle():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    rds_tf = (root / "infrastructure" / "terraform" / "rds.tf").read_text()
    s3_tf = (root / "infrastructure" / "terraform" / "s3.tf").read_text()

    assert "storage_encrypted     = true" in rds_tf
    assert "kms_key_id = aws_kms_key.main.arn" in rds_tf
    assert "aws_s3_bucket_lifecycle_configuration" in s3_tf
    assert "voice_input_retention_days" in s3_tf
    assert "voice_output_retention_days" in s3_tf
