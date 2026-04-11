"""Integration tests for the samples API (/api/v1/samples)."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_sample(client: AsyncClient, **overrides) -> dict:
    payload = {
        "name": "Test Reagent",
        "barcode": f"BC-{uuid.uuid4().hex[:8]}",
        "sample_type": "reagent",
        "location": "Freezer-1/Shelf-2",
        "quantity": 50.0,
        "unit": "uL",
    }
    payload.update(overrides)
    resp = await client.post("/api/v1/samples/", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_sample(client: AsyncClient):
    data = await _create_sample(client)
    assert data["name"] == "Test Reagent"
    assert data["sample_type"] == "reagent"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_samples(client: AsyncClient):
    await _create_sample(client, name="Sample A")
    await _create_sample(client, name="Sample B")
    resp = await client.get("/api/v1/samples/")
    assert resp.status_code == 200
    samples = resp.json()
    assert len(samples) >= 2


@pytest.mark.asyncio
async def test_get_sample(client: AsyncClient):
    created = await _create_sample(client)
    sample_id = created["id"]
    resp = await client.get(f"/api/v1/samples/{sample_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == sample_id


@pytest.mark.asyncio
async def test_get_sample_not_found(client: AsyncClient):
    resp = await client.get(f"/api/v1/samples/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Barcode scan
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scan_barcode_found(client: AsyncClient):
    barcode = f"SCAN-{uuid.uuid4().hex[:8]}"
    await _create_sample(client, barcode=barcode)
    resp = await client.post(
        "/api/v1/samples/scan",
        json={"barcode": barcode},
    )
    assert resp.status_code == 200
    assert resp.json()["barcode"] == barcode


@pytest.mark.asyncio
async def test_scan_barcode_not_found(client: AsyncClient):
    resp = await client.post(
        "/api/v1/samples/scan",
        json={"barcode": "DOES-NOT-EXIST"},
    )
    assert resp.status_code == 404
