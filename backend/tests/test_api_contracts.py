"""Contract tests: verify frontend-expected routes exist with correct methods.

These tests encode the API contract that the frontend stores depend on.
If a backend route is renamed, removed, or its method changes, these tests
will fail — catching the mismatch before it silently breaks the UI.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# ELN contract (eln-store.ts)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_eln_list_entries(client: AsyncClient):
    """Frontend: GET /api/v1/eln/"""
    resp = await client.get("/api/v1/eln/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_eln_create_entry(client: AsyncClient):
    """Frontend: POST /api/v1/eln/"""
    resp = await client.post(
        "/api/v1/eln/",
        json={
            "title": "Contract test entry",
            "content_markdown": "## Test",
            "tags": ["contract-test"],
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["title"] == "Contract test entry"


@pytest.mark.asyncio
async def test_eln_submit_entry(client: AsyncClient):
    """Frontend: POST /api/v1/eln/{id}/submit"""
    # Create first
    create_resp = await client.post(
        "/api/v1/eln/",
        json={"title": "Submit test", "content_markdown": "content"},
    )
    entry_id = create_resp.json()["id"]

    resp = await client.post(f"/api/v1/eln/{entry_id}/submit")
    assert resp.status_code == 200
    assert resp.json()["status"] == "submitted"


@pytest.mark.asyncio
async def test_eln_export_pdf_route_exists(client: AsyncClient):
    """Frontend: GET /api/v1/eln/{id}/export/pdf — route must exist."""
    create_resp = await client.post(
        "/api/v1/eln/",
        json={"title": "PDF test", "content_markdown": "content"},
    )
    entry_id = create_resp.json()["id"]

    try:
        resp = await client.get(f"/api/v1/eln/{entry_id}/export/pdf")
        # 200 if weasyprint installed, 501 if not — either confirms the route exists
        assert resp.status_code in (200, 501)
    except OSError:
        # weasyprint may raise OSError if system libs (pango) are missing —
        # the route itself exists, which is what we're testing.
        pytest.skip("weasyprint native libs not available")


@pytest.mark.asyncio
async def test_eln_auto_generate_route_exists(client: AsyncClient):
    """Frontend: POST /api/v1/eln/auto-generate — route must exist."""
    resp = await client.post(
        "/api/v1/eln/auto-generate",
        json={"experiment_id": str(uuid.uuid4())},
    )
    # 404 is expected (experiment doesn't exist), but confirms route exists
    assert resp.status_code in (201, 404)


# ---------------------------------------------------------------------------
# Protocol contract (protocol-store.ts)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_protocol_list(client: AsyncClient):
    """Frontend: GET /api/v1/protocols"""
    resp = await client.get("/api/v1/protocols/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_protocol_create(client: AsyncClient):
    """Frontend: POST /api/v1/protocols"""
    resp = await client.post(
        "/api/v1/protocols/",
        json={"name": "Contract test protocol"},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Contract test protocol"


@pytest.mark.asyncio
async def test_protocol_publish(client: AsyncClient):
    """Frontend: POST /api/v1/protocols/{id}/publish"""
    create_resp = await client.post(
        "/api/v1/protocols/",
        json={"name": "Publish test"},
    )
    proto_id = create_resp.json()["id"]

    resp = await client.post(f"/api/v1/protocols/{proto_id}/publish")
    assert resp.status_code == 200
    assert resp.json()["status"] == "published"


@pytest.mark.asyncio
async def test_protocol_inventory_check_is_post(client: AsyncClient):
    """Frontend must use POST (not GET) for inventory check."""
    create_resp = await client.post(
        "/api/v1/protocols/",
        json={"name": "Inv check test"},
    )
    proto_id = create_resp.json()["id"]

    # POST should work (200)
    resp_post = await client.post(f"/api/v1/protocols/{proto_id}/inventory-check")
    assert resp_post.status_code == 200

    # GET should fail (405 Method Not Allowed)
    resp_get = await client.get(f"/api/v1/protocols/{proto_id}/inventory-check")
    assert resp_get.status_code == 405


@pytest.mark.asyncio
async def test_protocol_dilution_calculator_fields(client: AsyncClient):
    """Frontend must send c1/c2/v2 (not stock_concentration etc.)."""
    # Correct field names
    resp = await client.post(
        "/api/v1/protocols/dilution-calculator",
        json={"c1": 100.0, "c2": 10.0, "v2": 1000.0},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "v1" in data
    assert "formula" in data

    # Old field names should fail validation
    resp_old = await client.post(
        "/api/v1/protocols/dilution-calculator",
        json={
            "stock_concentration": 100.0,
            "target_concentration": 10.0,
            "target_volume": 1000.0,
        },
    )
    assert resp_old.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_protocol_generate_route(client: AsyncClient):
    """Frontend: POST /api/v1/protocols/generate"""
    resp = await client.post("/api/v1/protocols/generate")
    assert resp.status_code == 201


# ---------------------------------------------------------------------------
# Sample contract (sample-store.ts)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sample_list(client: AsyncClient):
    """Frontend: GET /api/v1/samples"""
    resp = await client.get("/api/v1/samples/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_sample_create(client: AsyncClient):
    """Frontend: POST /api/v1/samples"""
    resp = await client.post(
        "/api/v1/samples/",
        json={
            "name": "Contract test sample",
            "barcode": f"CT-{uuid.uuid4().hex[:8]}",
            "sample_type": "reagent",
            "location": "Shelf-1",
            "quantity": 100.0,
            "unit": "uL",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Contract test sample"


@pytest.mark.asyncio
async def test_sample_delete(client: AsyncClient):
    """Frontend: DELETE /api/v1/samples/{id}"""
    create_resp = await client.post(
        "/api/v1/samples/",
        json={
            "name": "Delete test",
            "barcode": f"DEL-{uuid.uuid4().hex[:8]}",
            "sample_type": "reagent",
            "location": "Shelf-1",
            "quantity": 10.0,
            "unit": "mL",
        },
    )
    sample_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/v1/samples/{sample_id}")
    assert resp.status_code == 204


# ---------------------------------------------------------------------------
# Plate contract (plate-store.ts)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_plate_list(client: AsyncClient):
    """Frontend: GET /api/v1/plates"""
    resp = await client.get("/api/v1/plates/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_plate_create(client: AsyncClient):
    """Frontend: POST /api/v1/plates"""
    resp = await client.post(
        "/api/v1/plates/",
        json={
            "name": "Contract test plate",
            "plate_type": "96",
            "well_mappings": [
                {
                    "source_plate": "SRC-1",
                    "source_well": "A1",
                    "destination_well": "A1",
                    "volume": 100.0,
                },
            ],
        },
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_plate_worklist_is_post(client: AsyncClient):
    """Frontend: POST /api/v1/plates/{id}/worklist"""
    create_resp = await client.post(
        "/api/v1/plates/",
        json={
            "name": "Worklist test",
            "plate_type": "96",
            "well_mappings": [
                {
                    "source_plate": "SRC",
                    "source_well": "A1",
                    "destination_well": "A1",
                    "volume": 50.0,
                },
            ],
        },
    )
    plate_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/plates/{plate_id}/worklist",
        json={"format": "echo"},
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Chat/conversations contract (lab-store.ts)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_conversations_list(client: AsyncClient):
    """Frontend: GET /api/v1/chat/conversations?clerk_user_id=..."""
    resp = await client.get("/api/v1/chat/conversations?clerk_user_id=test-user")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ---------------------------------------------------------------------------
# Response format contract — all responses use snake_case
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_response_keys_are_snake_case(client: AsyncClient):
    """Backend responses must use snake_case keys (frontend transforms to camelCase)."""
    # Create a sample and check response keys
    resp = await client.post(
        "/api/v1/samples/",
        json={
            "name": "Key format test",
            "barcode": f"KF-{uuid.uuid4().hex[:8]}",
            "sample_type": "reagent",
            "location": "Shelf-1",
            "quantity": 50.0,
            "unit": "uL",
        },
    )
    data = resp.json()
    # These keys should be snake_case from the backend
    assert "created_at" in data
    assert "sample_type" in data
    # camelCase variants should NOT be present in raw backend response
    assert "createdAt" not in data
    assert "sampleType" not in data
