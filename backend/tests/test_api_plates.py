"""Integration tests for the plates API (/api/v1/plates)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_plate(client: AsyncClient, **overrides) -> dict:
    payload = {
        "name": "Test Plate",
        "plate_type": "96",
        "description": "unit test plate",
        "well_mappings": [
            {
                "source_plate": "SRC-1",
                "source_well": "A1",
                "destination_well": "A1",
                "volume": 100.0,
            },
            {
                "source_plate": "SRC-1",
                "source_well": "A2",
                "destination_well": "A2",
                "volume": 100.0,
            },
        ],
    }
    payload.update(overrides)
    resp = await client.post("/api/v1/plates/", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_plate_map(client: AsyncClient):
    data = await _create_plate(client)
    assert data["name"] == "Test Plate"
    assert data["plate_type"] == "96"
    assert "id" in data
    assert len(data["well_mappings"]) == 2


@pytest.mark.asyncio
async def test_list_plate_maps(client: AsyncClient):
    await _create_plate(client, name="Plate A")
    await _create_plate(client, name="Plate B")
    resp = await client.get("/api/v1/plates/")
    assert resp.status_code == 200
    plates = resp.json()
    assert len(plates) >= 2


@pytest.mark.asyncio
async def test_get_plate_map(client: AsyncClient):
    created = await _create_plate(client)
    plate_id = created["id"]
    resp = await client.get(f"/api/v1/plates/{plate_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == plate_id


@pytest.mark.asyncio
async def test_get_plate_map_not_found(client: AsyncClient):
    import uuid

    resp = await client.get(f"/api/v1/plates/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Worklist generation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_worklist_echo(client: AsyncClient):
    created = await _create_plate(client)
    plate_id = created["id"]
    resp = await client.post(
        f"/api/v1/plates/{plate_id}/worklist",
        json={"format": "echo"},
    )
    assert resp.status_code == 200
    assert "Source Plate Name" in resp.text


@pytest.mark.asyncio
async def test_generate_worklist_hamilton(client: AsyncClient):
    created = await _create_plate(client)
    plate_id = created["id"]
    resp = await client.post(
        f"/api/v1/plates/{plate_id}/worklist",
        json={"format": "hamilton"},
    )
    assert resp.status_code == 200
    assert resp.text.startswith("A;")


@pytest.mark.asyncio
async def test_generate_worklist_rejects_duplicate_destination(client: AsyncClient):
    created = await _create_plate(
        client,
        well_mappings=[
            {
                "source_plate": "SRC-1",
                "source_well": "A1",
                "destination_well": "A1",
                "volume": 100.0,
            },
            {
                "source_plate": "SRC-1",
                "source_well": "A2",
                "destination_well": "A1",
                "volume": 100.0,
            },
        ],
    )
    resp = await client.post(
        f"/api/v1/plates/{created['id']}/worklist",
        json={"format": "echo"},
    )
    assert resp.status_code == 400
    detail = resp.json()["detail"]
    assert detail["message"] == "Worklist validation failed"
    assert any("duplicate destination well A1" in error for error in detail["errors"])


# ---------------------------------------------------------------------------
# Stateless mapping endpoints
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cherry_pick_endpoint(client: AsyncClient):
    resp = await client.post(
        "/api/v1/plates/cherry-pick",
        json={
            "source_plates": [
                {"plate_name": "SRC", "wells": {"A1": {"cmpd": "X"}, "B2": {"cmpd": "Y"}}}
            ],
            "hit_list": ["A1"],
            "destination_type": "96",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["well_mappings"]) == 1


@pytest.mark.asyncio
async def test_serial_dilution_endpoint(client: AsyncClient):
    resp = await client.post(
        "/api/v1/plates/serial-dilution",
        json={
            "compound": "TestCmpd",
            "start_concentration": 10.0,
            "dilution_factor": 3.0,
            "num_points": 8,
            "replicates": 1,
            "plate_type": "96",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["compound"] == "TestCmpd"
    assert len(data["concentrations"]) == 8
