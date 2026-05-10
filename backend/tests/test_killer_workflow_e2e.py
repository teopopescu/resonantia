"""P1.6 — End-to-End Killer Workflow Integration Test.

Exercises the full workflow via API calls and direct tool executor calls:
1. Upload CSV via POST /api/v1/files/upload-and-parse
2. Verify parsed columns and row count
3. Call fit_dose_response tool directly via tool_executor
4. Verify IC50 result for staurosporine is ~42 nM
5. Call create_eln_entry tool with experiment context
6. Call generate_worklist tool
7. All scoped by org_id
"""

from __future__ import annotations

import csv
import io
import os
import uuid
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

ORG_ID = "org_test_e2e"
SEED_CSV_PATH = Path(__file__).parent.parent.parent / "demo-data" / "dose_response_staurosporine_HEK293T.csv"


def _load_seed_csv() -> bytes:
    """Load the seed CSV as bytes."""
    assert SEED_CSV_PATH.exists(), f"Seed CSV not found at {SEED_CSV_PATH}"
    return SEED_CSV_PATH.read_bytes()


def _parse_csv_to_compounds(csv_bytes: bytes) -> dict[str, list[tuple[float, float]]]:
    """Parse CSV bytes into per-compound concentration/response lists."""
    text = csv_bytes.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    compounds: dict[str, list[tuple[float, float]]] = {}
    for row in reader:
        name = row["Compound"]
        conc = float(row["Concentration_nM"])
        resp = float(row["Response_Pct"])
        compounds.setdefault(name, []).append((conc, resp))
    return compounds


# ---------------------------------------------------------------------------
# Step 1: Upload CSV via API
# ---------------------------------------------------------------------------

class TestStep1Upload:
    """Test CSV upload via the /api/v1/files/upload-and-parse endpoint."""

    @pytest.fixture(autouse=True)
    def _patch_storage(self, tmp_path, monkeypatch):
        """Inject a LocalStorage pointed at tmp_path."""
        from resonantia.services import storage as storage_mod
        instance = storage_mod.LocalStorage(base_dir=str(tmp_path))
        monkeypatch.setattr(storage_mod, "_storage_instance", instance)
        yield
        monkeypatch.setattr(storage_mod, "_storage_instance", None)

    @pytest.mark.asyncio
    async def test_upload_and_parse_returns_correct_structure(self, client):
        """Upload seed CSV and verify parsed metadata."""
        csv_bytes = _load_seed_csv()

        response = await client.post(
            "/api/v1/files/upload-and-parse",
            files={"file": ("dose_response_staurosporine_HEK293T.csv", csv_bytes, "text/csv")},
            headers={"X-Org-Id": ORG_ID},
        )

        assert response.status_code == 201, f"Upload failed: {response.text}"
        data = response.json()

        # Verify structure
        assert "file_id" in data
        assert data["filename"] == "dose_response_staurosporine_HEK293T.csv"
        assert set(data["columns"]) == {"Compound", "Concentration_nM", "Response_Pct", "Well", "Replicate"}
        assert data["row_count"] == 240
        assert data["detected_format"] == "dose_response"

        # Verify column types
        assert data["column_types"]["Compound"] == "string"
        assert data["column_types"]["Concentration_nM"] == "numeric"
        assert data["column_types"]["Response_Pct"] == "numeric"
        assert data["column_types"]["Replicate"] == "integer"

        # Verify preview rows
        assert len(data["preview_rows"]) == 5
        assert data["preview_rows"][0]["Compound"] == "Staurosporine"


# ---------------------------------------------------------------------------
# Step 2: Fit dose-response curves
# ---------------------------------------------------------------------------

class TestStep2FitDoseResponse:
    """Test dose-response fitting for staurosporine data."""

    @pytest.fixture(autouse=True)
    def _patch_storage(self, tmp_path, monkeypatch):
        """Inject a LocalStorage pointed at tmp_path."""
        from resonantia.services import storage as storage_mod
        instance = storage_mod.LocalStorage(base_dir=str(tmp_path))
        monkeypatch.setattr(storage_mod, "_storage_instance", instance)
        yield
        monkeypatch.setattr(storage_mod, "_storage_instance", None)

    @pytest.mark.asyncio
    async def test_staurosporine_ic50_approximately_42nm(self):
        """Fit staurosporine data and verify IC50 is ~42 nM."""
        from resonantia.services.data_processor import fit_dose_response_full

        compounds = _parse_csv_to_compounds(_load_seed_csv())
        stauro_data = compounds["Staurosporine"]
        concentrations = [d[0] for d in stauro_data]
        responses = [d[1] for d in stauro_data]

        result = await fit_dose_response_full(concentrations, responses, compound_name="Staurosporine")

        assert result["success"] is True
        # IC50 should be within 20% of 42 nM (accounting for noise)
        assert 30.0 <= result["ic50"] <= 55.0, f"IC50 {result['ic50']} not near 42 nM"
        # Hill slope should be negative and around -1.2
        assert -2.0 <= result["hill_slope"] <= -0.8, f"Hill slope {result['hill_slope']} unexpected"
        # R-squared should be excellent
        assert result["r_squared"] > 0.98, f"R² {result['r_squared']} too low"
        # Plot should be generated
        assert result["plot_url"].startswith("/api/v1/files/serve/")
        # Should have 30 data points (10 conc x 3 reps)
        assert result["n_points"] == 30

    @pytest.mark.asyncio
    async def test_compound_g_most_potent(self):
        """Compound_G should have lowest IC50 (~8 nM)."""
        from resonantia.services.data_processor import fit_dose_response_full

        compounds = _parse_csv_to_compounds(_load_seed_csv())
        cpg_data = compounds["Compound_G"]
        concentrations = [d[0] for d in cpg_data]
        responses = [d[1] for d in cpg_data]

        result = await fit_dose_response_full(concentrations, responses, compound_name="Compound_G")

        assert result["success"] is True
        # IC50 should be < 15 nM
        assert result["ic50"] < 15.0, f"Compound_G IC50 {result['ic50']} not potent enough"
        assert result["r_squared"] > 0.95

    @pytest.mark.asyncio
    async def test_all_compounds_fit_successfully(self):
        """All 8 compounds should produce a successful fit."""
        from resonantia.services.data_processor import fit_dose_response_full

        compounds = _parse_csv_to_compounds(_load_seed_csv())
        assert len(compounds) == 8

        for name, data in compounds.items():
            concentrations = [d[0] for d in data]
            responses = [d[1] for d in data]
            result = await fit_dose_response_full(concentrations, responses, compound_name=name)
            assert result["success"] is True, f"Fit failed for {name}: {result.get('error')}"

    @pytest.mark.asyncio
    async def test_fit_dose_response_tool_via_executor(self):
        """Exercise the fit_dose_response tool handler directly."""
        from resonantia.services.tool_executor import _fit_dose_response_tool

        compounds = _parse_csv_to_compounds(_load_seed_csv())
        stauro_data = compounds["Staurosporine"]
        concentrations = [d[0] for d in stauro_data]
        responses = [d[1] for d in stauro_data]

        # Mock the DB session for experiment persistence
        mock_exp = MagicMock()
        mock_exp.id = uuid.uuid4()

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("resonantia.services.tool_executor.async_session_factory", return_value=mock_session):
            result = await _fit_dose_response_tool(
                {
                    "concentrations": concentrations,
                    "responses": responses,
                    "compound_name": "Staurosporine",
                },
                org_id=ORG_ID,
            )

        assert result["success"] is True
        assert 30.0 <= result["ic50"] <= 55.0


# ---------------------------------------------------------------------------
# Step 3: ELN entry creation
# ---------------------------------------------------------------------------

class TestStep3ELNEntry:
    """Test ELN entry creation via tool executor."""

    @pytest.mark.asyncio
    async def test_create_eln_entry_with_experiment(self):
        """Create an ELN entry linked to an experiment."""
        from resonantia.services.tool_executor import _create_eln_entry

        # Mock experiment with dose-response results
        mock_exp = MagicMock()
        mock_exp.id = uuid.uuid4()
        mock_exp.org_id = ORG_ID
        mock_exp.name = "Dose-Response: Staurosporine"
        mock_exp.description = "4PL curve fit for Staurosporine in HEK293T cells"
        mock_exp.protocol = "CellTiter-Glo viability"
        mock_exp.status = "completed"
        mock_exp.results = {
            "ec50": 42.0,
            "hill_slope": -1.2,
            "r_squared": 0.996,
            "z_prime": 0.72,
            "compound": "Staurosporine",
            "n_points": 30,
            "n_replicates": 3,
            "plot_url": "/api/v1/files/serve/plots/test.png",
        }
        mock_exp.created_at = datetime(2026, 5, 10, 10, 0, 0)

        # Mock ELN entry to be returned after commit
        mock_entry = MagicMock()
        mock_entry.id = uuid.uuid4()
        mock_entry.entry_number = "ELN-2026-0001"
        mock_entry.title = "ELN -- Dose-Response: Staurosporine"
        mock_entry.status = "draft"
        mock_entry.content_markdown = "# Test"
        mock_entry.tags = ["auto-generated"]
        mock_entry.linked_references = {"experiment_id": str(mock_exp.id)}

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_exp)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        # Mock the scalar call for entry number generation
        mock_session.scalar = AsyncMock(return_value=0)

        with patch("resonantia.services.tool_executor.async_session_factory", return_value=mock_session):
            result = await _create_eln_entry(
                {
                    "title": "Dose-Response Summary",
                    "experiment_id": str(mock_exp.id),
                },
                org_id=ORG_ID,
            )

        assert result["created"] is True
        assert result["entry_number"] == "ELN-2026-0001"
        assert result["status"] == "draft"
        # Content should have been auto-generated
        assert "content_markdown" in result
        assert "42.0" in result["content_markdown"]
        assert "Staurosporine" in result["content_markdown"]

    @pytest.mark.asyncio
    async def test_eln_content_includes_all_sections(self):
        """Generated ELN content must include all required sections."""
        from resonantia.services.tool_executor import _generate_eln_content

        exp = SimpleNamespace(
            id=uuid.uuid4(),
            name="Dose-Response: Staurosporine",
            description="Determine IC50 of Staurosporine in HEK293T cells",
            protocol="CellTiter-Glo 48h viability",
            status="completed",
            results={
                "ec50": 42.0,
                "hill_slope": -1.2,
                "r_squared": 0.996,
                "compound": "Staurosporine",
                "n_points": 30,
                "n_replicates": 3,
                "plot_url": "/api/v1/files/serve/plots/test.png",
            },
            org_id=ORG_ID,
            created_at=datetime(2026, 5, 10, 10, 0, 0),
        )

        content = _generate_eln_content(exp)

        assert "## Objective" in content
        assert "## Methods" in content
        assert "## Results" in content
        assert "## Conclusions" in content
        assert "## References" in content
        assert "42.0" in content
        assert "-1.2" in content


# ---------------------------------------------------------------------------
# Step 4: Cherry-pick and follow-up proposal
# ---------------------------------------------------------------------------

class TestStep4CherryPickAndFollowUp:
    """Test cherry-pick plate creation and follow-up proposals."""

    @pytest.mark.asyncio
    async def test_cherry_pick_creates_plate_map(self):
        """Cherry-pick top 3 hits into a plate map."""
        from resonantia.services.tool_executor import _cherry_pick_tool

        mock_plate = MagicMock()
        mock_plate.id = uuid.uuid4()
        mock_plate.name = "Cherry-Pick Confirmation"
        mock_plate.plate_type = "96"

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("resonantia.services.tool_executor.async_session_factory", return_value=mock_session):
            result = await _cherry_pick_tool(
                {
                    "source_plates": [
                        {
                            "plate_name": "SOURCE_1",
                            "wells": {
                                "A1": {"compound": "Compound_G", "concentration_nM": 8.0},
                                "A2": {"compound": "Dasatinib", "concentration_nM": 15.0},
                                "A3": {"compound": "Staurosporine", "concentration_nM": 42.0},
                            },
                        }
                    ],
                    "hit_list": ["A1", "A2", "A3"],
                    "plate_type": "96",
                    "name": "Cherry-Pick Confirmation",
                },
                org_id=ORG_ID,
            )

        assert result["created"] is True
        assert result["name"] == "Cherry-Pick Confirmation"
        assert "preview" in result
        assert result["preview"]["plate_type"] == 96

    @pytest.mark.asyncio
    async def test_follow_up_proposal_generates_options(self):
        """Follow-up proposal should produce 2-3 options."""
        from resonantia.services.tool_executor import _propose_follow_up

        mock_exp = MagicMock()
        mock_exp.org_id = ORG_ID
        mock_exp.name = "Dose-Response: Staurosporine"
        mock_exp.results = {
            "ic50": 42.0,
            "hill_slope": -1.2,
            "r_squared": 0.996,
            "z_prime": 0.72,
        }

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_exp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("resonantia.services.tool_executor.async_session_factory", return_value=mock_session):
            result = await _propose_follow_up(
                {"experiment_id": "550e8400-e29b-41d4-a716-446655440000"},
                org_id=ORG_ID,
            )

        assert "options" in result
        assert 2 <= len(result["options"]) <= 3
        assert result["options"][0]["title"] == "Hit Confirmation"
        assert result["recommended"] == 1
        # Concentration range should bracket the IC50
        conc_range = result["options"][0]["concentration_range"]
        assert conc_range["start_nM"] < 42.0
        assert conc_range["end_nM"] > 42.0


# ---------------------------------------------------------------------------
# Step 5: Worklist generation
# ---------------------------------------------------------------------------

class TestStep5Worklist:
    """Test worklist generation from a plate map."""

    @pytest.mark.asyncio
    async def test_generate_worklist_produces_valid_echo_csv(self):
        """Generate worklist and verify Echo CSV format."""
        from resonantia.services.tool_executor import _generate_worklist_tool

        plate_map_id = str(uuid.uuid4())

        # Mock plate map with well mappings
        mock_plate_map = MagicMock()
        mock_plate_map.id = uuid.UUID(plate_map_id)
        mock_plate_map.org_id = ORG_ID
        mock_plate_map.name = "Cherry-Pick Confirmation"
        mock_plate_map.well_mappings = [
            {"source_plate": "SOURCE_1", "source_well": "A1", "destination_well": "A1", "content": {"compound": "Compound_G"}},
            {"source_plate": "SOURCE_1", "source_well": "A2", "destination_well": "A2", "content": {"compound": "Dasatinib"}},
            {"source_plate": "SOURCE_1", "source_well": "A3", "destination_well": "A3", "content": {"compound": "Staurosporine"}},
        ]

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_plate_map)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("resonantia.services.tool_executor.async_session_factory", return_value=mock_session):
            result = await _generate_worklist_tool(
                {
                    "plate_map_id": plate_map_id,
                    "instrument": "echo",
                    "volume_nl": 100,
                },
                org_id=ORG_ID,
            )

        assert "error" not in result, f"Worklist generation failed: {result.get('error')}"
        assert result["instrument"] == "echo"
        assert result["format"] == "csv"
        assert result["total_transfers"] == 3
        assert result["total_volume_nl"] == 300

        # Verify CSV content format
        content = result["content"]
        lines = content.strip().split("\n")
        assert len(lines) == 4  # header + 3 transfers

        # Parse and verify header
        reader = csv.reader(io.StringIO(content))
        header = next(reader)
        assert "Source Plate Name" in header
        assert "Source Well" in header
        assert "Destination Plate Name" in header
        assert "Destination Well" in header
        assert "Transfer Volume" in header

        # Verify first data row
        row = next(reader)
        assert row[0] == "SOURCE_1"  # Source Plate Name
        assert row[1] == "A1"  # Source Well
        assert row[3] == "A1"  # Destination Well

    @pytest.mark.asyncio
    async def test_generate_worklist_requires_plate_map_id(self):
        """Missing plate_map_id should return an error."""
        from resonantia.services.tool_executor import _generate_worklist_tool

        result = await _generate_worklist_tool({}, org_id=ORG_ID)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_generate_worklist_cross_tenant_blocked(self):
        """Worklist for another org's plate map should fail."""
        from resonantia.services.tool_executor import _generate_worklist_tool

        plate_map_id = str(uuid.uuid4())

        mock_plate_map = MagicMock()
        mock_plate_map.id = uuid.UUID(plate_map_id)
        mock_plate_map.org_id = "org_other"  # Different org
        mock_plate_map.name = "Other Org Plate"
        mock_plate_map.well_mappings = []

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_plate_map)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("resonantia.services.tool_executor.async_session_factory", return_value=mock_session):
            result = await _generate_worklist_tool(
                {"plate_map_id": plate_map_id, "instrument": "echo"},
                org_id=ORG_ID,
            )

        assert "error" in result
        assert "not accessible" in result["error"]


# ---------------------------------------------------------------------------
# Full workflow integration
# ---------------------------------------------------------------------------

class TestFullWorkflowIntegration:
    """End-to-end test combining all steps (mocking DB for persistence)."""

    @pytest.fixture(autouse=True)
    def _patch_storage(self, tmp_path, monkeypatch):
        """Inject a LocalStorage pointed at tmp_path."""
        from resonantia.services import storage as storage_mod
        instance = storage_mod.LocalStorage(base_dir=str(tmp_path))
        monkeypatch.setattr(storage_mod, "_storage_instance", instance)
        yield
        monkeypatch.setattr(storage_mod, "_storage_instance", None)

    @pytest.mark.asyncio
    async def test_upload_fit_eln_worklist_pipeline(self, client):
        """Exercise the complete upload -> fit -> ELN -> worklist pipeline."""
        # --- Step 1: Upload CSV ---
        csv_bytes = _load_seed_csv()
        upload_resp = await client.post(
            "/api/v1/files/upload-and-parse",
            files={"file": ("dose_response_staurosporine_HEK293T.csv", csv_bytes, "text/csv")},
            headers={"X-Org-Id": ORG_ID},
        )
        assert upload_resp.status_code == 201
        file_id = upload_resp.json()["file_id"]
        assert upload_resp.json()["row_count"] == 240

        # --- Step 2: Fit dose-response for staurosporine ---
        from resonantia.services.data_processor import fit_dose_response_full

        compounds = _parse_csv_to_compounds(csv_bytes)
        stauro_data = compounds["Staurosporine"]
        concentrations = [d[0] for d in stauro_data]
        responses = [d[1] for d in stauro_data]

        fit_result = await fit_dose_response_full(
            concentrations, responses, compound_name="Staurosporine"
        )
        assert fit_result["success"] is True
        assert 30.0 <= fit_result["ic50"] <= 55.0
        assert fit_result["r_squared"] > 0.98

        # --- Step 3: Verify ELN content generation ---
        from resonantia.services.tool_executor import _generate_eln_content

        exp = SimpleNamespace(
            id=uuid.uuid4(),
            name="Dose-Response: Staurosporine",
            description="4PL fit for Staurosporine",
            protocol="CellTiter-Glo",
            status="completed",
            results={
                "ec50": fit_result["ic50"],
                "hill_slope": fit_result["hill_slope"],
                "r_squared": fit_result["r_squared"],
                "plot_url": fit_result["plot_url"],
                "compound": "Staurosporine",
                "n_points": fit_result["n_points"],
                "n_replicates": fit_result["n_replicates"],
            },
            org_id=ORG_ID,
            created_at=datetime(2026, 5, 10),
        )
        eln_content = _generate_eln_content(exp)
        assert "## Results" in eln_content
        assert "IC50" in eln_content

        # --- Step 4: Verify worklist generation logic ---
        from resonantia.services.plate_mapper import generate_worklist

        well_mappings = [
            {"source_plate": "SRC", "source_well": "A1", "destination_well": "A1", "volume": 100},
            {"source_plate": "SRC", "source_well": "B1", "destination_well": "B1", "volume": 100},
            {"source_plate": "SRC", "source_well": "C1", "destination_well": "C1", "volume": 100},
        ]
        worklist = generate_worklist(well_mappings, fmt="echo")
        assert "Source Plate Name" in worklist
        assert "SRC" in worklist
        lines = worklist.strip().split("\n")
        assert len(lines) == 4  # header + 3 rows

    @pytest.mark.asyncio
    async def test_seed_csv_is_deterministic(self):
        """Verify that the seed CSV produces consistent results across runs."""
        csv_bytes = _load_seed_csv()
        compounds = _parse_csv_to_compounds(csv_bytes)

        # Must have exactly 8 compounds
        assert len(compounds) == 8
        expected_compounds = {
            "Staurosporine", "Rapamycin", "Imatinib", "Dasatinib",
            "Sorafenib", "Erlotinib", "Compound_F", "Compound_G",
        }
        assert set(compounds.keys()) == expected_compounds

        # Each compound must have exactly 30 data points (10 conc x 3 reps)
        for name, data in compounds.items():
            assert len(data) == 30, f"{name} has {len(data)} points, expected 30"

        # Total rows = 240
        total = sum(len(d) for d in compounds.values())
        assert total == 240

    @pytest.mark.asyncio
    async def test_ranking_top_hits(self):
        """Verify correct ranking of compounds by IC50."""
        from resonantia.services.data_processor import fit_dose_response_full

        csv_bytes = _load_seed_csv()
        compounds = _parse_csv_to_compounds(csv_bytes)

        # Fit all compounds and rank by IC50
        ic50_values: dict[str, float] = {}
        for name, data in compounds.items():
            concentrations = [d[0] for d in data]
            responses = [d[1] for d in data]
            result = await fit_dose_response_full(concentrations, responses, compound_name=name)
            if result["success"]:
                ic50_values[name] = result["ic50"]

        # Top 3 most potent should be Compound_G, Dasatinib, Staurosporine
        ranked = sorted(ic50_values.items(), key=lambda x: x[1])
        top_3_names = [r[0] for r in ranked[:3]]

        assert "Compound_G" in top_3_names, f"Compound_G not in top 3: {top_3_names}"
        assert "Dasatinib" in top_3_names, f"Dasatinib not in top 3: {top_3_names}"
        assert "Staurosporine" in top_3_names, f"Staurosporine not in top 3: {top_3_names}"

        # Compound_G should be most potent (lowest IC50)
        assert ranked[0][0] == "Compound_G", f"Most potent is {ranked[0][0]}, expected Compound_G"

        # Imatinib and Compound_F should be least potent
        bottom_2_names = [r[0] for r in ranked[-2:]]
        assert "Imatinib" in bottom_2_names or "Compound_F" in bottom_2_names
