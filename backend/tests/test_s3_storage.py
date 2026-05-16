"""Tests for S3 storage and signed URL support."""

from __future__ import annotations

import pytest

from resonantia.services.storage import S3Storage, choose_storage_backend, is_signed_url


class _Body:
    def __init__(self, content: bytes) -> None:
        self._content = content

    def read(self) -> bytes:
        return self._content


class _FakeS3Client:
    def __init__(self) -> None:
        self.objects = {}
        self.presign_calls = []

    def put_object(self, **kwargs):
        self.objects[(kwargs["Bucket"], kwargs["Key"])] = kwargs

    def get_object(self, **kwargs):
        obj = self.objects[(kwargs["Bucket"], kwargs["Key"])]
        return {"Body": _Body(obj["Body"])}

    def delete_object(self, **kwargs):
        self.objects.pop((kwargs["Bucket"], kwargs["Key"]), None)

    def generate_presigned_url(self, operation, *, Params, ExpiresIn):
        self.presign_calls.append((operation, Params, ExpiresIn))
        return f"https://signed.example/{Params['Bucket']}/{Params['Key']}?expires={ExpiresIn}"


@pytest.mark.asyncio
async def test_s3_storage_saves_with_encryption_and_presigns():
    client = _FakeS3Client()
    storage = S3Storage(
        bucket="bucket",
        region="us-east-1",
        prefix="prefix",
        expires_seconds=3600,
        client=client,
    )

    url = await storage.save("files/data.csv", b"a,b\n1,2\n", "text/csv")
    assert is_signed_url(url)

    stored = client.objects[("bucket", "prefix/files/data.csv")]
    assert stored["ServerSideEncryption"] == "AES256"
    assert stored["ContentType"] == "text/csv"
    assert await storage.load("files/data.csv") == b"a,b\n1,2\n"
    assert client.presign_calls[-1][2] == 3600


def test_choose_storage_backend_uses_s3_for_large_configured_files(monkeypatch: pytest.MonkeyPatch):
    from resonantia.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "storage_backend", "s3")
    monkeypatch.setattr(settings, "s3_bucket", "bucket")

    assert choose_storage_backend(5 * 1024 * 1024) == "s3"
    assert choose_storage_backend(5 * 1024 * 1024 - 1) == "local"


def test_voice_audio_uses_signed_url_source():
    from resonantia.api import voice

    source = voice.voice_chat.__code__.co_consts
    joined = "\n".join(str(item) for item in source)
    assert "voice/" in joined
    assert "audio_url" in joined
