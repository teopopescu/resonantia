"""Tests for request ID propagation and aggregate latency fields."""

from __future__ import annotations

import json
import logging

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from resonantia.middleware import RequestContextMiddleware, log_stage_latency


@pytest.mark.asyncio
async def test_request_completion_log_contains_all_latency_fields(caplog):
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)

    @app.get("/latency-test")
    async def latency_test():
        log_stage_latency("stt", 1.2)
        log_stage_latency("llm", 2.3)
        log_stage_latency("tool", 3.4)
        log_stage_latency("tts", 4.5)
        log_stage_latency("db", 5.6)
        return {"ok": True}

    caplog.set_level(logging.INFO, logger="resonantia.request")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/latency-test", headers={"X-Request-Id": "req-test"})

    assert response.status_code == 200
    assert response.headers["X-Request-Id"] == "req-test"

    completed = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "resonantia.request" and '"event": "request_complete"' in record.message
    ]
    assert len(completed) == 1
    payload = completed[0]
    assert payload["request_id"] == "req-test"
    for field in ("stt_ms", "llm_ms", "tool_ms", "agent_ms", "tts_ms", "db_ms", "total_ms"):
        assert field in payload
    assert payload["agent_ms"] == pytest.approx(5.7)
