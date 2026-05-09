"""Tests for CSV upload-and-parse endpoint and column type detection."""

from __future__ import annotations

import io

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Column type detection unit tests
# ---------------------------------------------------------------------------

class TestColumnTypeDetection:
    def test_detect_integer(self):
        from resonantia.api.files import _detect_column_type
        assert _detect_column_type(["1", "2", "3", "42"]) == "integer"

    def test_detect_numeric(self):
        from resonantia.api.files import _detect_column_type
        assert _detect_column_type(["1.5", "2.7", "3.14"]) == "numeric"

    def test_detect_string(self):
        from resonantia.api.files import _detect_column_type
        assert _detect_column_type(["alpha", "beta", "gamma"]) == "string"

    def test_detect_date_iso(self):
        from resonantia.api.files import _detect_column_type
        assert _detect_column_type(["2024-01-15", "2024-02-20", "2024-03-25"]) == "date"

    def test_detect_date_us(self):
        from resonantia.api.files import _detect_column_type
        assert _detect_column_type(["01/15/2024", "02/20/2024"]) == "date"

    def test_empty_values_return_string(self):
        from resonantia.api.files import _detect_column_type
        assert _detect_column_type(["", "", ""]) == "string"

    def test_mixed_types_return_string(self):
        from resonantia.api.files import _detect_column_type
        assert _detect_column_type(["123", "abc", "456"]) == "string"


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------

class TestFormatDetection:
    def test_dose_response_detected(self):
        from resonantia.api.files import _detect_format
        assert _detect_format(["Compound", "Concentration_nM", "Response_%", "Well"]) == "dose_response"

    def test_plate_reader_detected(self):
        from resonantia.api.files import _detect_format
        assert _detect_format(["Well", "Value", "Plate"]) == "plate_reader"

    def test_qpcr_detected(self):
        from resonantia.api.files import _detect_format
        assert _detect_format(["Sample", "Ct", "Gene"]) == "qpcr"

    def test_generic_tabular(self):
        from resonantia.api.files import _detect_format
        assert _detect_format(["Name", "Score", "Date"]) == "tabular"


# ---------------------------------------------------------------------------
# CSV parsing
# ---------------------------------------------------------------------------

class TestCSVParsing:
    def test_parse_csv_basic(self):
        from resonantia.api.files import _parse_csv
        csv_bytes = b"Name,Value\nAlpha,1\nBeta,2\nGamma,3\n"
        result = _parse_csv(csv_bytes, "test.csv")
        assert result["columns"] == ["Name", "Value"]
        assert result["row_count"] == 3
        assert result["column_types"]["Name"] == "string"
        assert result["column_types"]["Value"] == "integer"
        assert len(result["preview_rows"]) == 3

    def test_parse_csv_dose_response(self):
        from resonantia.api.files import _parse_csv
        csv_bytes = b"Compound,Concentration_nM,Response_%\nDrug,0.1,95\nDrug,1.0,50\nDrug,10.0,10\n"
        result = _parse_csv(csv_bytes, "dose.csv")
        assert result["detected_format"] == "dose_response"
        assert result["row_count"] == 3

    def test_parse_csv_preview_limited_to_5(self):
        from resonantia.api.files import _parse_csv
        rows = "A,B\n" + "\n".join(f"{i},{i*10}" for i in range(20))
        result = _parse_csv(rows.encode(), "big.csv")
        assert len(result["preview_rows"]) == 5
        assert result["row_count"] == 20

    def test_parse_empty_csv(self):
        from resonantia.api.files import _parse_csv
        result = _parse_csv(b"", "empty.csv")
        assert result["row_count"] == 0
        assert result["columns"] == []


# ---------------------------------------------------------------------------
# Integration: POST /upload-and-parse
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_upload_and_parse_csv(client: AsyncClient):
    csv_content = b"Compound,Concentration_nM,Response_%\nDrug,0.1,95.0\nDrug,1.0,50.0\nDrug,10.0,10.0\n"
    files = {"file": ("dose_response.csv", io.BytesIO(csv_content), "text/csv")}
    r = await client.post(
        "/api/v1/files/upload-and-parse",
        files=files,
        headers={"X-Org-Id": "org_test"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["filename"] == "dose_response.csv"
    assert data["columns"] == ["Compound", "Concentration_nM", "Response_%"]
    assert data["row_count"] == 3
    assert data["column_types"]["Concentration_nM"] == "numeric"
    assert data["column_types"]["Response_%"] == "numeric"
    assert data["column_types"]["Compound"] == "string"
    assert data["detected_format"] == "dose_response"
    assert len(data["preview_rows"]) == 3
    assert "file_id" in data


@pytest.mark.asyncio
async def test_upload_and_parse_rejects_non_csv(client: AsyncClient):
    files = {"file": ("image.png", io.BytesIO(b"\x89PNG"), "image/png")}
    r = await client.post(
        "/api/v1/files/upload-and-parse",
        files=files,
        headers={"X-Org-Id": "org_test"},
    )
    assert r.status_code == 400
    assert "CSV" in r.json()["detail"]


@pytest.mark.asyncio
async def test_upload_and_parse_registers_in_file_registry(client: AsyncClient):
    csv_content = b"A,B\n1,2\n3,4\n"
    files = {"file": ("data.csv", io.BytesIO(csv_content), "text/csv")}
    r = await client.post(
        "/api/v1/files/upload-and-parse",
        files=files,
        headers={"X-Org-Id": "org_reg"},
    )
    assert r.status_code == 201
    file_id = r.json()["file_id"]

    # Should appear in the file list for same org
    r2 = await client.get("/api/v1/files/", headers={"X-Org-Id": "org_reg"})
    assert r2.status_code == 200
    assert any(f["id"] == file_id for f in r2.json())


# ---------------------------------------------------------------------------
# Integration: GET /serve/{path}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_serve_file_after_upload(client: AsyncClient):
    csv_content = b"X,Y\n1,10\n2,20\n"
    files = {"file": ("serve_test.csv", io.BytesIO(csv_content), "text/csv")}
    r = await client.post(
        "/api/v1/files/upload-and-parse",
        files=files,
        headers={"X-Org-Id": "org_serve"},
    )
    assert r.status_code == 201
    file_id = r.json()["file_id"]

    # Serve via the storage path
    serve_path = f"csv/{file_id}.csv"
    r2 = await client.get(f"/api/v1/files/serve/{serve_path}")
    assert r2.status_code == 200
    assert b"X,Y" in r2.content


@pytest.mark.asyncio
async def test_serve_nonexistent_returns_404(client: AsyncClient):
    r = await client.get("/api/v1/files/serve/nonexistent/file.csv")
    assert r.status_code == 404
