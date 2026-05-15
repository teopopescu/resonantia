"""Opt-in external provider tests for Phase 1 integrations.

These tests are skipped by default so the normal CI suite stays hermetic.
Run them with RUN_EXTERNAL_PROVIDER_TESTS=1 and the required provider keys.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from resonantia.dependencies import get_request_context
from resonantia.models.request_context import RequestContext


@pytest.mark.asyncio
async def test_clerk_auth_rejects_missing_token():
    app = FastAPI()

    @app.get("/protected")
    async def protected(ctx: RequestContext = Depends(get_request_context)):
        return {"user_id": ctx.user_id}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/protected")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_clerk_auth_rejects_invalid_token():
    app = FastAPI()

    @app.get("/protected")
    async def protected(ctx: RequestContext = Depends(get_request_context)):
        return {"user_id": ctx.user_id}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/protected",
            headers={"Authorization": "Bearer invalid.jwt.token"},
        )

    assert response.status_code == 401


def _external_enabled() -> bool:
    return os.environ.get("RUN_EXTERNAL_PROVIDER_TESTS") == "1"


@pytest.mark.external
@pytest.mark.skipif(not _external_enabled(), reason="Set RUN_EXTERNAL_PROVIDER_TESTS=1 to call external providers")
@pytest.mark.asyncio
async def test_openai_stt_transcribes_audio_clip():
    audio_path = os.environ.get("OPENAI_STT_TEST_AUDIO")
    if not audio_path or not Path(audio_path).exists():
        pytest.skip("Set OPENAI_STT_TEST_AUDIO to a local audio clip")

    from resonantia.services.stt import OpenAISTTProvider

    provider = OpenAISTTProvider()
    with open(audio_path, "rb") as audio:
        text = await provider.transcribe(audio)

    assert isinstance(text, str)
    assert text.strip()


@pytest.mark.external
@pytest.mark.skipif(not _external_enabled(), reason="Set RUN_EXTERNAL_PROVIDER_TESTS=1 to call external providers")
@pytest.mark.asyncio
async def test_openai_tts_generates_audio_and_streams_chunks():
    from resonantia.services.tts import OpenAITTSProvider

    provider = OpenAITTSProvider()
    audio = await provider.synthesize("External provider smoke test.")
    assert len(audio) > 1000

    chunks = [chunk async for chunk in provider.synthesize_stream("Streaming smoke test.")]
    assert chunks
    assert all(isinstance(chunk, bytes) and chunk for chunk in chunks)


@pytest.mark.external
@pytest.mark.skipif(not _external_enabled(), reason="Set RUN_EXTERNAL_PROVIDER_TESTS=1 to call external providers")
@pytest.mark.asyncio
async def test_anthropic_prompt_caching_reports_cache_read_tokens():
    from resonantia.services.llm.anthropic_adapter import AnthropicAdapter

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY is required")

    adapter = AnthropicAdapter(api_key=api_key)
    cached_prompt = "You are testing prompt caching. " * 700
    tools = [
        {
            "name": "lookup_sample",
            "description": "Look up a sample by barcode.",
            "input_schema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        }
    ]
    messages = [
        {"role": "system", "content": cached_prompt},
        {"role": "user", "content": "Reply with exactly: cache smoke ok"},
    ]

    await adapter.completion(messages=messages, tools=tools, max_tokens=32)
    second = await adapter.completion(messages=messages, tools=tools, max_tokens=32)

    assert second.cache_read_input_tokens > 0
