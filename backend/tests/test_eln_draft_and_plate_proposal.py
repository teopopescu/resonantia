"""Tests for P1.3 (ELN draft from results) and P1.4a (plate layout proposal).

These tests exercise the pure-logic helpers directly (no DB required)
and mock the async session for the tool handler integration tests.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from resonantia.services.tool_executor import (
    _build_plate_preview,
    _generate_eln_content,
    _plate_dimensions,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_experiment(
    name: str = "EXP-001",
    description: str = "Determine IC50 of Staurosporine in HeLa cytotoxicity assay",
    protocol: str = "CellTiter-Glo 48h viability",
    status: str = "completed",
    results: dict[str, Any] | None = None,
) -> SimpleNamespace:
    """Return a lightweight experiment-like object for unit testing."""
    return SimpleNamespace(
        id=uuid.uuid4(),
        name=name,
        description=description,
        protocol=protocol,
        status=status,
        results=results or {},
        org_id="org_default",
        created_at=datetime(2025, 6, 1, 12, 0, 0),
    )


# ---------------------------------------------------------------------------
# P1.3: _generate_eln_content
# ---------------------------------------------------------------------------

class TestGenerateELNContent:
    """Unit tests for the ELN markdown template engine."""

    def test_full_results_generates_all_sections(self):
        exp = _make_experiment(results={
            "ec50": 42.5,
            "hill_slope": -1.2,
            "r_squared": 0.98,
            "z_prime": 0.72,
            "compound": "Staurosporine",
            "plate_type": 384,
            "n_points": 10,
            "dilution_factor": 3,
            "n_replicates": 3,
            "readout_method": "Luminescence",
            "pos_control": "DMSO 0.1%",
            "vehicle_control": "DMSO",
            "plot_url": "/plots/exp001.png",
            "file_upload_id": "file-abc123",
            "plate_map_id": "pm-xyz789",
        })
        md = _generate_eln_content(exp)

        # All required sections present
        assert "## Objective" in md
        assert "## Methods" in md
        assert "## Results" in md
        assert "## Conclusions" in md
        assert "## References" in md

        # Key values
        assert "42.5" in md
        assert "-1.2" in md
        assert "0.98" in md
        assert "0.72" in md
        assert "Staurosporine" in md
        assert "384-well" in md
        assert "10-point" in md
        assert "Luminescence" in md
        assert "DMSO 0.1%" in md

        # Plot reference
        assert "![Dose-Response Curve](/plots/exp001.png)" in md

        # References
        assert "file-abc123" in md
        assert "pm-xyz789" in md
        assert date.today().isoformat() in md

    def test_missing_results_handled_gracefully(self):
        exp = _make_experiment(results={})
        md = _generate_eln_content(exp)

        # Should still have all sections -- Conclusions falls back
        assert "## Objective" in md
        assert "## Conclusions" in md
        assert "Review results" in md

    def test_no_results_dict(self):
        exp = _make_experiment(results=None)
        md = _generate_eln_content(exp)
        assert "## Objective" in md
        assert "## Conclusions" in md

    def test_conclusion_excellent_r_squared(self):
        exp = _make_experiment(results={"r_squared": 0.97, "ec50": 10})
        md = _generate_eln_content(exp)
        assert "excellent" in md.lower()

    def test_conclusion_good_r_squared(self):
        exp = _make_experiment(results={"r_squared": 0.92, "ec50": 10})
        md = _generate_eln_content(exp)
        assert "good" in md.lower()

    def test_conclusion_moderate_r_squared(self):
        exp = _make_experiment(results={"r_squared": 0.75, "ec50": 10})
        md = _generate_eln_content(exp)
        assert "moderate" in md.lower()

    def test_conclusion_z_prime_excellent(self):
        exp = _make_experiment(results={"z_prime": 0.65})
        md = _generate_eln_content(exp)
        assert "excellent" in md.lower()

    def test_conclusion_z_prime_poor(self):
        exp = _make_experiment(results={"z_prime": -0.3})
        md = _generate_eln_content(exp)
        assert "poor" in md.lower()

    def test_protocol_fallback_when_no_method_fields(self):
        exp = _make_experiment(
            protocol="Add 50 uL of reagent, incubate 2h at 37C",
            results={},
        )
        md = _generate_eln_content(exp)
        assert "50 uL" in md or "Add 50" in md

    def test_experiment_name_in_title(self):
        exp = _make_experiment(name="SCREEN-2025-042")
        md = _generate_eln_content(exp)
        assert "# SCREEN-2025-042" in md

    def test_extra_result_keys_included(self):
        exp = _make_experiment(results={"custom_metric": 123.4})
        md = _generate_eln_content(exp)
        assert "custom_metric" in md
        assert "123.4" in md

    def test_ci_bounds_rendered(self):
        exp = _make_experiment(results={
            "ec50": 50, "ci_lower": 30, "ci_upper": 80,
        })
        md = _generate_eln_content(exp)
        assert "30" in md
        assert "80" in md
        assert "95% CI" in md


# ---------------------------------------------------------------------------
# P1.4a: _plate_dimensions
# ---------------------------------------------------------------------------

class TestPlateDimensions:
    def test_96_well(self):
        assert _plate_dimensions("96") == (8, 12)

    def test_384_well(self):
        assert _plate_dimensions("384") == (16, 24)

    def test_default_is_96(self):
        assert _plate_dimensions("48") == (8, 12)


# ---------------------------------------------------------------------------
# P1.4a: _build_plate_preview
# ---------------------------------------------------------------------------

class TestBuildPlatePreview:
    def test_empty_96_plate(self):
        preview = _build_plate_preview("96", [], include_controls=False)
        assert preview["plate_type"] == 96
        assert preview["rows"] == 8
        assert preview["cols"] == 12
        assert preview["summary"]["total_wells"] == 96
        assert preview["summary"]["used_wells"] == 0
        assert len(preview["wells"]) == 96

    def test_with_controls_96(self):
        preview = _build_plate_preview("96", [], include_controls=True)
        pos_count = sum(1 for w in preview["wells"] if w["type"] == "control_positive")
        neg_count = sum(1 for w in preview["wells"] if w["type"] == "control_negative")
        # Column 1 = positive (8 rows), column 12 = negative (8 rows)
        assert pos_count == 8
        assert neg_count == 8
        assert preview["summary"]["controls"]["positive"] == 8
        assert preview["summary"]["controls"]["negative"] == 8

    def test_with_controls_384(self):
        preview = _build_plate_preview("384", [], include_controls=True)
        pos_count = sum(1 for w in preview["wells"] if w["type"] == "control_positive")
        neg_count = sum(1 for w in preview["wells"] if w["type"] == "control_negative")
        assert pos_count == 16
        assert neg_count == 16
        assert preview["summary"]["total_wells"] == 384

    def test_sample_wells_override_controls(self):
        """If a sample is assigned to a control column position, sample wins."""
        well_dicts = [{"well": "A1", "compound": "TestDrug"}]
        preview = _build_plate_preview("96", well_dicts, include_controls=True)
        a1 = next(w for w in preview["wells"] if w["position"] == "A1")
        assert a1["type"] == "sample"
        assert a1["compound"] == "TestDrug"

    def test_compound_count_in_summary(self):
        wells = [
            {"well": "A2", "compound": "DrugA"},
            {"well": "A3", "compound": "DrugA"},
            {"well": "A4", "compound": "DrugB"},
        ]
        preview = _build_plate_preview("96", wells, include_controls=False)
        assert preview["summary"]["compounds"] == 2

    def test_concentration_preserved(self):
        wells = [{"well": "B3", "compound": "X", "concentration": 500.0}]
        preview = _build_plate_preview("96", wells, include_controls=False)
        b3 = next(w for w in preview["wells"] if w["position"] == "B3")
        assert b3["concentration_nM"] == 500.0

    def test_color_coding(self):
        wells = [{"well": "A5", "compound": "Y"}]
        preview = _build_plate_preview("96", wells, include_controls=True)
        a1 = next(w for w in preview["wells"] if w["position"] == "A1")
        a5 = next(w for w in preview["wells"] if w["position"] == "A5")
        a12 = next(w for w in preview["wells"] if w["position"] == "A12")
        empty = next(w for w in preview["wells"] if w["position"] == "A6")

        assert a1["color"] == "#22c55e"   # positive control
        assert a5["color"] == "#3b82f6"   # sample
        assert a12["color"] == "#ef4444"  # negative control
        assert empty["color"] == "#d1d5db" # empty


# ---------------------------------------------------------------------------
# Integration: serial_dilution preview shape
# ---------------------------------------------------------------------------

class TestSerialDilutionPreview:
    def test_serial_dilution_layout_produces_preview(self):
        from resonantia.services.plate_mapper import serial_dilution

        layout = serial_dilution(
            compound="Staurosporine",
            start_concentration=10000.0,
            dilution_factor=3.0,
            num_points=8,
            replicates=2,
            plate_type="96",
        )
        well_dicts = layout["layout"]
        preview = _build_plate_preview(
            "96", well_dicts, compounds=["Staurosporine"], replicates=2,
        )
        assert preview["summary"]["compounds"] == 1
        assert preview["summary"]["replicates"] == 2
        assert preview["summary"]["used_wells"] > 0
        # 8 points x 2 replicates = 16 sample wells + controls
        sample_wells = [w for w in preview["wells"] if w["type"] == "sample"]
        assert len(sample_wells) == 16

    def test_serial_dilution_concentrations_descending(self):
        from resonantia.services.plate_mapper import serial_dilution

        layout = serial_dilution(
            compound="X", start_concentration=1000, dilution_factor=2, num_points=5,
        )
        concs = layout["concentrations"]
        assert concs == sorted(concs, reverse=True)


# ---------------------------------------------------------------------------
# Integration: cherry_pick preview shape
# ---------------------------------------------------------------------------

class TestCherryPickPreview:
    def test_cherry_pick_creates_preview(self):
        from resonantia.services.plate_mapper import cherry_pick

        sources = [{
            "plate_name": "SRC-1",
            "wells": {
                "A1": {"compound": "aspirin"},
                "A2": {"compound": "ibuprofen"},
                "B1": {"compound": "caffeine"},
            },
        }]
        layout = cherry_pick(sources, hit_list=["A1", "B1"])
        mappings = layout["well_mappings"]

        well_dicts = []
        for m in mappings:
            content = m.get("content", {})
            well_dicts.append({
                "well": m["destination_well"],
                "compound": content.get("compound", ""),
            })

        preview = _build_plate_preview("96", well_dicts, include_controls=True)
        assert preview["summary"]["compounds"] == 2
        sample_wells = [w for w in preview["wells"] if w["type"] == "sample"]
        assert len(sample_wells) == 2
