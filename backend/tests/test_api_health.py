"""Integration tests for health and CORS."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "resonantia"


# ---------------------------------------------------------------------------
# CORS headers
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cors_allows_localhost_3000(client: AsyncClient):
    resp = await client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    # FastAPI CORS middleware should respond to preflight
    assert resp.status_code in (200, 204)
    assert "http://localhost:3000" in resp.headers.get(
        "access-control-allow-origin", ""
    )
