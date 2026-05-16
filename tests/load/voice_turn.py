"""Locust tasks for durable voice turn throughput."""

from __future__ import annotations

from io import BytesIO

try:
    from locust import HttpUser, between, task
except ImportError:  # pragma: no cover - allows smoke imports without locust installed
    class HttpUser:  # type: ignore[no-redef]
        pass

    def between(*args, **kwargs):  # type: ignore[no-redef]
        return None

    def task(weight=1):  # type: ignore[no-redef]
        def _decorator(fn):
            return fn
        return _decorator


class VoiceTurnUser(HttpUser):
    """Target: 10 concurrent voice users completing durable turn starts."""

    wait_time = between(1, 3)
    abstract = False

    @task(2)
    def start_voice_turn(self):
        audio = BytesIO(_minimal_wav_bytes())
        files = {
            "audio": ("load-test.wav", audio, "audio/wav"),
        }
        with self.client.post(
            "/api/v1/voice/turn",
            files=files,
            data={"conversation_id": "load-test-voice"},
            headers={"X-Org-Id": "org_load"},
            catch_response=True,
            name="voice.turn.start",
        ) as response:
            if response.status_code != 202:
                response.failure(f"unexpected status {response.status_code}: {response.text[:200]}")
                return
            payload = response.json()
            if not payload.get("stream_url"):
                response.failure("missing stream_url")


def _minimal_wav_bytes() -> bytes:
    # 44-byte WAV header plus a tiny silence payload. Providers may reject
    # this in real staging if STT is enabled; the load target here is the
    # durable turn ingestion path.
    return (
        b"RIFF$\x00\x00\x00WAVEfmt "
        b"\x10\x00\x00\x00\x01\x00\x01\x00@\x1f\x00\x00@\x1f\x00\x00\x01\x00\x08\x00"
        b"data\x00\x00\x00\x00"
    )
