"""Plate mapping, worklist generation, and liquid-handling utilities."""

from __future__ import annotations

import csv
import io
import itertools
import string
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ROWS_96 = list(string.ascii_uppercase[:8])   # A-H
COLS_96 = list(range(1, 13))                 # 1-12
ROWS_384 = list(string.ascii_uppercase[:16]) # A-P
COLS_384 = list(range(1, 25))                # 1-24


def _wells_for_plate(plate_type: str) -> list[str]:
    rows, cols = (ROWS_384, COLS_384) if plate_type == "384" else (ROWS_96, COLS_96)
    return [f"{r}{c}" for r, c in itertools.product(rows, cols)]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_plate_map(
    sources: list[dict[str, Any]],
    destination_type: str = "96",
    mapping_rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a well-mapping from one or more source plates to a destination plate.

    ``sources`` is a list of dicts, each with at least ``plate_name`` and ``wells``
    (a dict mapping well-id to content metadata).

    Returns a dict with ``destination_type``, ``well_mappings``, and
    ``destination_plate`` keys.
    """
    dest_wells = _wells_for_plate(destination_type)
    well_iter = iter(dest_wells)
    mappings: list[dict[str, Any]] = []

    for src in sources:
        plate_name = src.get("plate_name", "SRC")
        wells: dict[str, Any] = src.get("wells", {})
        for src_well, content in wells.items():
            try:
                dest_well = next(well_iter)
            except StopIteration:
                break
            mappings.append(
                {
                    "source_plate": plate_name,
                    "source_well": src_well,
                    "destination_well": dest_well,
                    "content": content,
                }
            )

    return {
        "destination_type": destination_type,
        "well_mappings": mappings,
        "destination_plate": {
            "type": destination_type,
            "total_wells": len(dest_wells),
            "filled_wells": len(mappings),
        },
    }


def cherry_pick(
    source_plates: list[dict[str, Any]],
    hit_list: list[str],
    destination_type: str = "96",
) -> dict[str, Any]:
    """Cherry-pick specific wells from source plates into a compact destination."""
    dest_wells = _wells_for_plate(destination_type)
    well_iter = iter(dest_wells)
    hit_set = set(hit_list)
    mappings: list[dict[str, Any]] = []

    for src in source_plates:
        plate_name = src.get("plate_name", "SRC")
        wells: dict[str, Any] = src.get("wells", {})
        for src_well, content in wells.items():
            if src_well in hit_set:
                try:
                    dest_well = next(well_iter)
                except StopIteration:
                    break
                mappings.append(
                    {
                        "source_plate": plate_name,
                        "source_well": src_well,
                        "destination_well": dest_well,
                        "content": content,
                    }
                )

    return {
        "destination_type": destination_type,
        "well_mappings": mappings,
        "destination_plate": {
            "type": destination_type,
            "total_wells": len(dest_wells),
            "filled_wells": len(mappings),
        },
    }


def serial_dilution(
    compound: str,
    start_concentration: float,
    dilution_factor: float = 3.0,
    num_points: int = 8,
    replicates: int = 1,
    plate_type: str = "96",
) -> dict[str, Any]:
    """Generate a serial dilution plate layout."""
    rows = ROWS_384[:replicates] if plate_type == "384" else ROWS_96[:replicates]
    concentrations = [
        start_concentration / (dilution_factor ** i) for i in range(num_points)
    ]
    mappings: list[dict[str, Any]] = []

    for row in rows:
        for idx, conc in enumerate(concentrations):
            col = idx + 1
            mappings.append(
                {
                    "well": f"{row}{col}",
                    "compound": compound,
                    "concentration": round(conc, 6),
                    "replicate_row": row,
                }
            )

    return {
        "compound": compound,
        "start_concentration": start_concentration,
        "dilution_factor": dilution_factor,
        "num_points": num_points,
        "replicates": replicates,
        "concentrations": [round(c, 6) for c in concentrations],
        "layout": mappings,
    }


# ---------------------------------------------------------------------------
# Worklist generation
# ---------------------------------------------------------------------------

def generate_worklist(
    well_mappings: list[dict[str, Any]],
    fmt: str = "echo",
) -> str:
    """Produce a worklist string for the given liquid-handler format."""
    if fmt == "echo":
        return _worklist_echo(well_mappings)
    elif fmt == "hamilton":
        return _worklist_hamilton(well_mappings)
    elif fmt == "opentrons":
        return _worklist_opentrons(well_mappings)
    raise ValueError(f"Unknown worklist format: {fmt}")


def _worklist_echo(mappings: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "Source Plate Name",
        "Source Well",
        "Destination Plate Name",
        "Destination Well",
        "Transfer Volume",
    ])
    for m in mappings:
        writer.writerow([
            m.get("source_plate", ""),
            m.get("source_well", ""),
            "DEST",
            m.get("destination_well", ""),
            m.get("volume", 100),
        ])
    return buf.getvalue()


def _worklist_hamilton(mappings: list[dict[str, Any]]) -> str:
    lines = []
    for m in mappings:
        lines.append(
            f"A;{m.get('source_plate', '')};{m.get('source_well', '')};;;"
            f"{m.get('volume', 100)};;;;"
        )
        lines.append(
            f"D;DEST;{m.get('destination_well', '')};;;"
            f"{m.get('volume', 100)};;;;"
        )
        lines.append("W;")
    return "\n".join(lines)


def _worklist_opentrons(mappings: list[dict[str, Any]]) -> str:
    """Produce a simplified Opentrons protocol snippet (Python)."""
    lines = [
        "from opentrons import protocol_api",
        "",
        "metadata = {'apiLevel': '2.16'}",
        "",
        "def run(protocol: protocol_api.ProtocolContext):",
        "    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')",
        "    source = protocol.load_labware('corning_96_wellplate_360ul_flat', '2')",
        "    dest = protocol.load_labware('corning_96_wellplate_360ul_flat', '3')",
        "    pipette = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tiprack])",
        "",
    ]
    for m in mappings:
        vol = m.get("volume", 100)
        lines.append(
            f"    pipette.transfer({vol}, "
            f"source['{m.get('source_well', 'A1')}'], "
            f"dest['{m.get('destination_well', 'A1')}'])"
        )
    return "\n".join(lines)


def validate_mapping(well_mappings: list[dict[str, Any]]) -> list[str]:
    """Return a list of validation error strings (empty means valid)."""
    errors: list[str] = []
    dest_wells_used: set[str] = set()
    for idx, m in enumerate(well_mappings):
        dw = m.get("destination_well")
        if not dw:
            errors.append(f"Mapping {idx}: missing destination_well")
            continue
        if dw in dest_wells_used:
            errors.append(f"Mapping {idx}: duplicate destination well {dw}")
        dest_wells_used.add(dw)
    return errors
