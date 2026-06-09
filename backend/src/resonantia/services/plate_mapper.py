"""Plate mapping, worklist generation, and liquid-handling utilities."""

from __future__ import annotations

import csv
import io
import itertools
import re
import string
from dataclasses import dataclass
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ROWS_96 = list(string.ascii_uppercase[:8])   # A-H
COLS_96 = list(range(1, 13))                 # 1-12
ROWS_384 = list(string.ascii_uppercase[:16]) # A-P
COLS_384 = list(range(1, 25))                # 1-24
WELL_RE = re.compile(r"^([A-P])([1-9]\d?)$")


@dataclass(frozen=True)
class InstrumentProfile:
    """Validation constraints for a worklist target."""

    name: str
    min_volume_nl: float
    max_volume_nl: float
    allowed_plate_types: tuple[str, ...] = ("96", "384")
    require_unique_destination_wells: bool = True


INSTRUMENT_PROFILES: dict[str, InstrumentProfile] = {
    "echo": InstrumentProfile(
        name="Echo acoustic dispenser",
        min_volume_nl=2.5,
        max_volume_nl=1000.0,
    ),
    "hamilton": InstrumentProfile(
        name="Hamilton liquid handler",
        min_volume_nl=1.0,
        max_volume_nl=300000.0,
    ),
    "opentrons": InstrumentProfile(
        name="Opentrons OT-2",
        min_volume_nl=1.0,
        max_volume_nl=300000.0,
    ),
}


class WorklistValidationError(ValueError):
    """Raised when a worklist would be unsafe or invalid to export."""

    def __init__(self, errors: list[str]):
        super().__init__("Invalid worklist: " + "; ".join(errors))
        self.errors = errors


def _wells_for_plate(plate_type: str) -> list[str]:
    rows, cols = (ROWS_384, COLS_384) if plate_type == "384" else (ROWS_96, COLS_96)
    return [f"{r}{c}" for r, c in itertools.product(rows, cols)]


def _normalise_format(fmt: str) -> str:
    aliases = {
        "echo-csv": "echo",
        "hamilton-gwl": "hamilton",
        "opentrons-python": "opentrons",
    }
    normalised = aliases.get(fmt.lower(), fmt.lower())
    if normalised not in INSTRUMENT_PROFILES:
        raise ValueError(f"Unknown worklist format: {fmt}")
    return normalised


def _is_valid_well_label(well: str, plate_type: str) -> bool:
    match = WELL_RE.match(well)
    if not match:
        return False
    row, raw_col = match.groups()
    col = int(raw_col)
    rows, cols = (ROWS_384, COLS_384) if plate_type == "384" else (ROWS_96, COLS_96)
    return row in rows and col in cols


def _infer_plate_type(well_mappings: list[dict[str, Any]]) -> str:
    """Infer the smallest plate type that can hold all referenced wells."""
    for mapping in well_mappings:
        for key in ("source_well", "destination_well"):
            raw_well = mapping.get(key)
            if not raw_well:
                continue
            match = WELL_RE.match(str(raw_well))
            if not match:
                continue
            row, raw_col = match.groups()
            if row not in ROWS_96 or int(raw_col) not in COLS_96:
                return "384"
    return "96"


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
    plate_type: str | None = None,
) -> str:
    """Produce a worklist string for the given liquid-handler format."""
    fmt = _normalise_format(fmt)
    validation = validate_worklist(well_mappings, fmt=fmt, plate_type=plate_type)
    if validation["errors"]:
        raise WorklistValidationError(validation["errors"])

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


def validate_worklist(
    well_mappings: list[dict[str, Any]],
    fmt: str = "echo",
    plate_type: str | None = None,
) -> dict[str, Any]:
    """Validate a worklist against target instrument and plate constraints."""
    fmt = _normalise_format(fmt)
    profile = INSTRUMENT_PROFILES[fmt]
    plate_type = plate_type or _infer_plate_type(well_mappings)
    errors: list[str] = []
    checks: list[str] = []

    if plate_type not in profile.allowed_plate_types:
        errors.append(f"{profile.name} does not support {plate_type}-well plates")

    if not well_mappings:
        errors.append("Worklist has no transfers")
        return {
            "ok": False,
            "instrument": profile.name,
            "format": fmt,
            "errors": errors,
            "checks": checks,
        }

    destination_wells_seen: set[str] = set()
    source_wells_seen: set[str] = set()
    total_volume_by_source: dict[str, float] = {}
    min_volume = float("inf")
    max_volume = 0.0

    for idx, mapping in enumerate(well_mappings):
        source_plate = str(mapping.get("source_plate") or "SRC")
        source_well = str(mapping.get("source_well") or "")
        dest_well = str(mapping.get("destination_well") or "")
        volume = float(mapping.get("volume") or 100)

        if not source_well:
            errors.append(f"Transfer {idx}: missing source_well")
        elif not _is_valid_well_label(source_well, plate_type):
            errors.append(f"Transfer {idx}: invalid source well {source_well} for {plate_type}-well plate")

        if not dest_well:
            errors.append(f"Transfer {idx}: missing destination_well")
        elif not _is_valid_well_label(dest_well, plate_type):
            errors.append(f"Transfer {idx}: invalid destination well {dest_well} for {plate_type}-well plate")

        if profile.require_unique_destination_wells and dest_well in destination_wells_seen:
            errors.append(f"Transfer {idx}: duplicate destination well {dest_well}")
        destination_wells_seen.add(dest_well)
        source_wells_seen.add(f"{source_plate}:{source_well}")

        if volume < profile.min_volume_nl or volume > profile.max_volume_nl:
            errors.append(
                f"Transfer {idx}: volume {volume:g} nL outside {profile.name} range "
                f"{profile.min_volume_nl:g}-{profile.max_volume_nl:g} nL"
            )
        min_volume = min(min_volume, volume)
        max_volume = max(max_volume, volume)
        total_volume_by_source[source_plate] = total_volume_by_source.get(source_plate, 0.0) + volume

    if not errors:
        checks = [
            f"{len(well_mappings)} transfers",
            f"{len(source_wells_seen)} source wells",
            f"{len(destination_wells_seen)} unique destination wells",
            f"volume range {min_volume:g}-{max_volume:g} nL",
            f"{profile.name} constraints passed",
        ]

    return {
        "ok": not errors,
        "instrument": profile.name,
        "format": fmt,
        "transfer_count": len(well_mappings),
        "min_volume_nl": None if min_volume == float("inf") else min_volume,
        "max_volume_nl": max_volume,
        "total_volume_by_source_plate_nl": total_volume_by_source,
        "errors": errors,
        "checks": checks,
    }
