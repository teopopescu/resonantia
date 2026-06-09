"""Unit tests for resonantia.services.plate_mapper."""

from __future__ import annotations

import csv
import io

import pytest

from resonantia.services.plate_mapper import (
    INSTRUMENT_PROFILES,
    WorklistValidationError,
    _wells_for_plate,
    cherry_pick,
    generate_plate_map,
    generate_worklist,
    serial_dilution,
    validate_mapping,
    validate_worklist,
)


# ---------------------------------------------------------------------------
# Well label generation
# ---------------------------------------------------------------------------

class TestGenerateWellLabels:
    def test_96_well_count(self):
        wells = _wells_for_plate("96")
        assert len(wells) == 96

    def test_96_well_first_last(self):
        wells = _wells_for_plate("96")
        assert wells[0] == "A1"
        assert wells[-1] == "H12"

    def test_384_well_count(self):
        wells = _wells_for_plate("384")
        assert len(wells) == 384

    def test_384_well_first_last(self):
        wells = _wells_for_plate("384")
        assert wells[0] == "A1"
        assert wells[-1] == "P24"


# ---------------------------------------------------------------------------
# Cherry pick
# ---------------------------------------------------------------------------

class TestCherryPick:
    def test_cherry_pick_creates_correct_mappings(self):
        sources = [
            {
                "plate_name": "SRC-1",
                "wells": {
                    "A1": {"compound": "aspirin"},
                    "A2": {"compound": "ibuprofen"},
                    "B1": {"compound": "caffeine"},
                },
            }
        ]
        result = cherry_pick(sources, hit_list=["A1", "B1"])
        mappings = result["well_mappings"]
        assert len(mappings) == 2
        picked_src_wells = [m["source_well"] for m in mappings]
        assert "A1" in picked_src_wells
        assert "B1" in picked_src_wells
        assert "A2" not in picked_src_wells

    def test_cherry_pick_destination_wells_are_compact(self):
        sources = [
            {
                "plate_name": "SRC-1",
                "wells": {"A1": {}, "C5": {}, "H12": {}},
            }
        ]
        result = cherry_pick(sources, hit_list=["A1", "C5", "H12"])
        dest_wells = [m["destination_well"] for m in result["well_mappings"]]
        # Should fill destination sequentially starting at A1
        assert dest_wells == ["A1", "A2", "A3"]

    def test_cherry_pick_empty_hit_list(self):
        sources = [{"plate_name": "SRC", "wells": {"A1": {}}}]
        result = cherry_pick(sources, hit_list=[])
        assert result["well_mappings"] == []
        assert result["destination_plate"]["filled_wells"] == 0


# ---------------------------------------------------------------------------
# Serial dilution
# ---------------------------------------------------------------------------

class TestSerialDilution:
    def test_default_8_point_dilution(self):
        result = serial_dilution(
            compound="TestCmpd",
            start_concentration=10.0,
            dilution_factor=3.0,
            num_points=8,
        )
        assert result["compound"] == "TestCmpd"
        assert len(result["concentrations"]) == 8
        assert result["concentrations"][0] == 10.0

    def test_dilution_factor_applied_correctly(self):
        result = serial_dilution(
            compound="X", start_concentration=100.0, dilution_factor=2.0, num_points=4
        )
        expected = [100.0, 50.0, 25.0, 12.5]
        assert result["concentrations"] == expected

    def test_layout_well_assignments(self):
        result = serial_dilution(
            compound="Y", start_concentration=10.0, num_points=3, replicates=1
        )
        wells = [m["well"] for m in result["layout"]]
        assert wells == ["A1", "A2", "A3"]

    def test_replicates_create_multiple_rows(self):
        result = serial_dilution(
            compound="Z", start_concentration=10.0, num_points=2, replicates=3
        )
        assert len(result["layout"]) == 6  # 2 points x 3 replicates


# ---------------------------------------------------------------------------
# Worklist generation — Echo CSV
# ---------------------------------------------------------------------------

class TestWorklistEcho:
    def test_echo_csv_header(self):
        mappings = [
            {"source_plate": "SRC", "source_well": "A1", "destination_well": "A1"}
        ]
        output = generate_worklist(mappings, fmt="echo")
        reader = csv.reader(io.StringIO(output))
        header = next(reader)
        assert "Source Plate Name" in header
        assert "Transfer Volume" in header

    def test_echo_csv_row_count(self):
        mappings = [
            {"source_plate": "S", "source_well": f"A{i}", "destination_well": f"B{i}"}
            for i in range(1, 4)
        ]
        output = generate_worklist(mappings, fmt="echo")
        lines = [l for l in output.strip().splitlines() if l.strip()]
        # 1 header + 3 data rows
        assert len(lines) == 4

    def test_echo_csv_default_volume(self):
        mappings = [
            {"source_plate": "S", "source_well": "A1", "destination_well": "A1"}
        ]
        output = generate_worklist(mappings, fmt="echo")
        reader = csv.reader(io.StringIO(output))
        next(reader)  # skip header
        row = next(reader)
        assert row[-1] == "100"  # default volume

    def test_echo_volume_below_minimum_fails_closed(self):
        mappings = [
            {"source_plate": "S", "source_well": "A1", "destination_well": "A1", "volume": 1}
        ]
        with pytest.raises(WorklistValidationError) as exc:
            generate_worklist(mappings, fmt="echo")
        assert "outside Echo acoustic dispenser range" in str(exc.value)

    def test_echo_duplicate_destination_fails_closed(self):
        mappings = [
            {"source_plate": "S", "source_well": "A1", "destination_well": "B1", "volume": 100},
            {"source_plate": "S", "source_well": "A2", "destination_well": "B1", "volume": 100},
        ]
        with pytest.raises(WorklistValidationError) as exc:
            generate_worklist(mappings, fmt="echo")
        assert "duplicate destination well B1" in str(exc.value)


# ---------------------------------------------------------------------------
# Worklist generation — Hamilton GWL
# ---------------------------------------------------------------------------

class TestWorklistHamilton:
    def test_hamilton_gwl_structure(self):
        mappings = [
            {"source_plate": "SRC", "source_well": "A1", "destination_well": "B1"}
        ]
        output = generate_worklist(mappings, fmt="hamilton")
        lines = output.strip().splitlines()
        # Each mapping produces: A; ... , D; ... , W;
        assert lines[0].startswith("A;")
        assert lines[1].startswith("D;")
        assert lines[2] == "W;"

    def test_hamilton_multiple_transfers(self):
        mappings = [
            {"source_plate": "S", "source_well": "A1", "destination_well": "A1"},
            {"source_plate": "S", "source_well": "A2", "destination_well": "A2"},
        ]
        output = generate_worklist(mappings, fmt="hamilton")
        lines = output.strip().splitlines()
        assert len(lines) == 6  # 3 lines per mapping


# ---------------------------------------------------------------------------
# Validate mapping
# ---------------------------------------------------------------------------

class TestValidateMapping:
    def test_valid_mapping_no_errors(self):
        mappings = [
            {"destination_well": "A1"},
            {"destination_well": "A2"},
            {"destination_well": "B1"},
        ]
        errors = validate_mapping(mappings)
        assert errors == []

    def test_duplicate_destination_detected(self):
        mappings = [
            {"destination_well": "A1"},
            {"destination_well": "A1"},  # duplicate
        ]
        errors = validate_mapping(mappings)
        assert len(errors) == 1
        assert "duplicate" in errors[0].lower()

    def test_missing_destination_well(self):
        mappings = [{}]
        errors = validate_mapping(mappings)
        assert len(errors) == 1
        assert "missing" in errors[0].lower()


class TestValidateWorklist:
    def test_instrument_profiles_are_declared(self):
        assert INSTRUMENT_PROFILES["echo"].min_volume_nl == 2.5
        assert INSTRUMENT_PROFILES["echo"].max_volume_nl == 1000
        assert "hamilton" in INSTRUMENT_PROFILES
        assert "opentrons" in INSTRUMENT_PROFILES

    def test_valid_echo_worklist_returns_checks(self):
        mappings = [
            {"source_plate": "S", "source_well": "A1", "destination_well": "B1", "volume": 100},
            {"source_plate": "S", "source_well": "A2", "destination_well": "B2", "volume": 100},
        ]
        result = validate_worklist(mappings, fmt="echo")
        assert result["ok"] is True
        assert result["errors"] == []
        assert result["transfer_count"] == 2
        assert any("Echo acoustic dispenser" in check for check in result["checks"])

    def test_invalid_well_label_returns_error(self):
        mappings = [
            {"source_plate": "S", "source_well": "Z99", "destination_well": "B1", "volume": 100},
        ]
        result = validate_worklist(mappings, fmt="echo")
        assert result["ok"] is False
        assert "invalid source well Z99" in result["errors"][0]


# ---------------------------------------------------------------------------
# Unknown worklist format
# ---------------------------------------------------------------------------

class TestWorklistUnknownFormat:
    def test_unknown_format_raises(self):
        with pytest.raises(ValueError, match="Unknown worklist format"):
            generate_worklist([], fmt="nonexistent")
