"""Resonantia MCP Server — exposes lab informatics tools via the Model Context Protocol.

Run standalone:
    python -m resonantia.mcp_server
    # or
    fastmcp run resonantia.mcp_server:mcp

Connects to the same backend database and services used by the Resonantia web app.
"""

from __future__ import annotations

import os
from typing import Optional

from fastmcp import FastMCP

mcp = FastMCP("Resonantia")

ORG_ID = os.environ.get("RESONANTIA_ORG_ID", "org_default")


async def _call_tool(tool_name: str, params: dict) -> str:
    """Delegate to the existing Resonantia tool executor."""
    from resonantia.services.tool_executor import execute_tool
    return await execute_tool(tool_name, params, ORG_ID)


# =========================================================================
# Plate Mapping Tools
# =========================================================================

@mcp.tool()
async def create_plate_map(
    name: str,
    plate_type: str = "96",
    source_plates: list[str] | None = None,
    mapping_mode: str = "cherry-pick",
    destination_format: str = "96",
) -> str:
    """Create a source-destination plate map for liquid handling transfers.

    Generates well-to-well mappings between source and destination plates.
    Supports cherry-pick, serial-dilution, and replicate mapping strategies.

    Args:
        name: Name for the plate map.
        plate_type: Destination plate type — "96" or "384".
        source_plates: List of source plate identifiers.
        mapping_mode: Transfer strategy — "cherry-pick", "serial-dilution", or "replicate".
        destination_format: Destination plate format (defaults to "96").
    """
    return await _call_tool("create_plate_map", {
        "name": name,
        "plate_type": plate_type,
        "source_plates": source_plates or [],
        "mapping_mode": mapping_mode,
        "destination_format": destination_format,
    })


@mcp.tool()
async def cherry_pick(
    source_plate_ids: list[str],
    hit_list: list[str],
    destination_plate_type: str = "96",
) -> str:
    """Cherry pick specific wells from source plates into a compact destination plate.

    Selects individual wells (hits) from one or more source plates and maps them
    sequentially into a new destination plate.

    Args:
        source_plate_ids: Source plate identifiers to pick from.
        hit_list: Well positions to cherry pick, e.g. ["A1", "B3", "H12"].
        destination_plate_type: Destination plate format — "96" or "384".
    """
    return await _call_tool("cherry_pick", {
        "source_plate_ids": source_plate_ids,
        "hit_list": hit_list,
        "destination_plate_type": destination_plate_type,
    })


@mcp.tool()
async def serial_dilution(
    compound_name: str,
    start_concentration: float,
    dilution_factor: float = 3.0,
    num_points: int = 8,
    direction: str = "horizontal",
) -> str:
    """Generate a serial dilution plate layout for dose-response experiments.

    Creates a concentration series by repeatedly diluting a compound, useful for
    IC50/EC50 determination.

    Args:
        compound_name: Name of the compound to dilute.
        start_concentration: Starting (highest) concentration in uM.
        dilution_factor: Fold dilution between each point (e.g. 3 for 1:3).
        num_points: Number of concentration points.
        direction: Dilution direction on plate — "horizontal" or "vertical".
    """
    return await _call_tool("serial_dilution", {
        "compound_name": compound_name,
        "start_concentration": start_concentration,
        "dilution_factor": dilution_factor,
        "num_points": num_points,
        "direction": direction,
    })


@mcp.tool()
async def generate_worklist(
    plate_map_id: str,
    format: str = "echo-csv",
    transfer_volume: float = 100.0,
    volume_unit: str = "nL",
) -> str:
    """Generate a liquid handler worklist file from an existing plate map.

    Produces worklist output compatible with Echo, Hamilton, or Opentrons instruments.

    Args:
        plate_map_id: ID of the plate map to generate from.
        format: Output format — "echo-csv", "hamilton-gwl", or "opentrons-py".
        transfer_volume: Volume to transfer per well.
        volume_unit: Unit for transfer volume — "nL", "uL", or "mL".
    """
    return await _call_tool("generate_worklist", {
        "plate_map_id": plate_map_id,
        "format": format,
        "transfer_volume": transfer_volume,
        "volume_unit": volume_unit,
    })


@mcp.tool()
async def get_plate_map_details(plate_map_name: str) -> str:
    """Get full details of a plate map including well-to-well mappings.

    Returns source/destination plates, individual well mappings, and worklist status.

    Args:
        plate_map_name: Name of the plate map to look up.
    """
    return await _call_tool("get_plate_map_details", {
        "plate_map_name": plate_map_name,
    })


# =========================================================================
# Data Processing Tools
# =========================================================================

@mcp.tool()
async def fit_dose_response(
    concentrations: list[float],
    responses: list[float],
    model: str = "4pl",
) -> str:
    """Fit a 4-parameter logistic curve to dose-response data and compute IC50/EC50.

    Returns fitted parameters (bottom, top, EC50, Hill slope), R-squared,
    standard errors, and the fitted curve values.

    Args:
        concentrations: Array of concentration values (e.g. in uM).
        responses: Array of corresponding response/signal values.
        model: Curve model — "4pl" (default) or "3pl".
    """
    return await _call_tool("fit_dose_response", {
        "concentrations": concentrations,
        "responses": responses,
        "model": model,
    })


@mcp.tool()
async def normalize_plate(
    raw_data: list,
    method: str = "z-score",
    positive_control_wells: list[str] | None = None,
    negative_control_wells: list[str] | None = None,
) -> str:
    """Normalize plate reader data using control wells.

    Supports z-score, percent-of-control, and robust-z normalization methods.
    Control well positions are required for percent-of-control.

    Args:
        raw_data: Array of raw plate reader values (row-major order).
        method: Normalization method — "z-score", "percent-of-control", or "robust-z".
        positive_control_wells: Well IDs of positive controls, e.g. ["A1", "A2"].
        negative_control_wells: Well IDs of negative controls.
    """
    return await _call_tool("normalize_plate", {
        "raw_data": raw_data,
        "method": method,
        "positive_control_wells": positive_control_wells,
        "negative_control_wells": negative_control_wells,
    })


@mcp.tool()
async def calculate_z_prime(
    positive_values: list[float],
    negative_values: list[float],
) -> str:
    """Calculate Z-prime factor to assess high-throughput screening assay quality.

    Returns Z' value, control means/stds, and a quality rating
    (excellent >= 0.5, acceptable >= 0, poor < 0).

    Args:
        positive_values: Signal values from positive control wells.
        negative_values: Signal values from negative control wells.
    """
    return await _call_tool("calculate_z_prime", {
        "positive_values": positive_values,
        "negative_values": negative_values,
    })


@mcp.tool()
async def qpcr_analysis(
    ct_values: dict,
    reference_gene: str = "GAPDH",
    control_sample: str = "Control",
) -> str:
    """Perform delta-delta Ct analysis for relative gene expression quantification.

    Computes fold changes relative to a control sample and housekeeping gene.

    Args:
        ct_values: Object mapping sample/gene names to arrays of Ct values.
        reference_gene: Name of the housekeeping/reference gene.
        control_sample: Name of the control/calibrator sample.
    """
    return await _call_tool("qpcr_analysis", {
        "ct_values": ct_values,
        "reference_gene": reference_gene,
        "control_sample": control_sample,
    })


# =========================================================================
# Sample Management Tools
# =========================================================================

@mcp.tool()
async def lookup_sample(
    query: str,
    search_by: str = "barcode",
) -> str:
    """Look up a sample or reagent by barcode, name, or lot number.

    Args:
        query: Search term (barcode, name, or lot number).
        search_by: Field to search — "barcode", "name", or "lot".
    """
    return await _call_tool("lookup_sample", {
        "query": query,
        "search_by": search_by,
    })


@mcp.tool()
async def check_inventory(
    reagent_name: str,
    check_expiry: bool = True,
) -> str:
    """Check current stock levels and expiry status of a reagent.

    Args:
        reagent_name: Name of the reagent to check.
        check_expiry: Whether to include expiry date check.
    """
    return await _call_tool("check_inventory", {
        "reagent_name": reagent_name,
        "check_expiry": check_expiry,
    })


@mcp.tool()
async def get_expiring_samples(days: int = 30) -> str:
    """Find all samples and reagents expiring within a given number of days.

    Args:
        days: Number of days to look ahead for expiring items (default 30).
    """
    return await _call_tool("get_expiring_samples", {"days": days})


# =========================================================================
# Experiment Tools
# =========================================================================

@mcp.tool()
async def query_experiments(query: str) -> str:
    """Search experiments by name, description, or protocol.

    Returns experiment details including status, protocol, and results
    (IC50, Z-prime, etc.) when available.

    Args:
        query: Search term to match against experiment name, description, or protocol.
    """
    return await _call_tool("query_experiments", {"query": query})


@mcp.tool()
async def get_ic50_values(compound: str) -> str:
    """Retrieve IC50/EC50 dose-response results for a specific compound across all experiments.

    Args:
        compound: Compound name to search for (e.g. "Staurosporine", "Rapamycin").
    """
    return await _call_tool("get_ic50_values", {"compound": compound})


# =========================================================================
# ELN (Electronic Lab Notebook) Tools
# =========================================================================

@mcp.tool()
async def create_eln_entry(
    title: str,
    experiment_id: Optional[str] = None,
    content_markdown: Optional[str] = None,
    tags: list[str] | None = None,
) -> str:
    """Create an ELN (Electronic Lab Notebook) entry.

    Can auto-generate content from an existing experiment, or accept
    free-form markdown. Generates a sequential entry number (ELN-YYYY-NNNN).

    Args:
        title: Title for the ELN entry.
        experiment_id: Optional experiment UUID to auto-generate content from.
        content_markdown: Markdown content (used if no experiment_id).
        tags: Tags for the entry.
    """
    return await _call_tool("create_eln_entry", {
        "title": title,
        "experiment_id": experiment_id,
        "content_markdown": content_markdown,
        "tags": tags or [],
    })


@mcp.tool()
async def query_eln_entries(
    query: str,
    status: Optional[str] = None,
) -> str:
    """Search ELN entries by title, content, or tags.

    Args:
        query: Search term to match against title or content.
        status: Filter by status — "draft", "submitted", or "archived".
    """
    params: dict = {"query": query}
    if status:
        params["status"] = status
    return await _call_tool("query_eln_entries", params)


# =========================================================================
# Protocol Tools
# =========================================================================

@mcp.tool()
async def create_protocol(
    name: str,
    experiment_type: Optional[str] = None,
    description: Optional[str] = None,
    cell_line: Optional[str] = None,
) -> str:
    """Create an experimental protocol with AI-generated steps.

    Generates step-by-step instructions based on experiment type
    (cytotoxicity, transfection, western-blot, etc.).

    Args:
        name: Protocol name.
        experiment_type: Type of experiment for auto-generated steps.
        description: Protocol description.
        cell_line: Cell line to use.
    """
    return await _call_tool("create_protocol", {
        "name": name,
        "experiment_type": experiment_type,
        "description": description,
        "cell_line": cell_line,
    })


@mcp.tool()
async def calculate_dilution(
    c1: float,
    c2: float,
    v1: Optional[float] = None,
    v2: Optional[float] = None,
    unit_concentration: str = "uM",
    unit_volume: str = "uL",
) -> str:
    """C1V1 = C2V2 dilution calculator. Provide three of four values to solve for the missing one.

    Args:
        c1: Initial concentration.
        c2: Final (desired) concentration.
        v1: Initial volume (omit to solve for it).
        v2: Final volume (omit to solve for it).
        unit_concentration: Concentration unit (default "uM").
        unit_volume: Volume unit (default "uL").
    """
    params: dict = {
        "c1": c1,
        "c2": c2,
        "unit_concentration": unit_concentration,
        "unit_volume": unit_volume,
    }
    if v1 is not None:
        params["v1"] = v1
    if v2 is not None:
        params["v2"] = v2
    return await _call_tool("calculate_dilution", params)


# =========================================================================
# MCP Resources — read-only listing endpoints
# =========================================================================

@mcp.resource("resonantia://experiments")
async def list_experiments() -> str:
    """List all experiments in the Resonantia database."""
    result = await _call_tool("query_experiments", {"query": ""})
    return result


@mcp.resource("resonantia://experiments/{query}")
async def search_experiments(query: str) -> str:
    """Search experiments by keyword."""
    return await _call_tool("query_experiments", {"query": query})


@mcp.resource("resonantia://samples")
async def list_samples() -> str:
    """List sample inventory statistics."""
    return await _call_tool("get_sample_stats", {})


@mcp.resource("resonantia://samples/expiring")
async def list_expiring_samples() -> str:
    """List samples expiring within 30 days."""
    return await _call_tool("get_expiring_samples", {"days": 30})


@mcp.resource("resonantia://plate-maps")
async def list_plate_maps() -> str:
    """List all plate maps."""
    return await _call_tool("query_plate_maps", {"query": ""})


@mcp.resource("resonantia://plate-maps/{name}")
async def get_plate_map(name: str) -> str:
    """Get details of a specific plate map by name."""
    return await _call_tool("get_plate_map_details", {"plate_map_name": name})


@mcp.resource("resonantia://eln")
async def list_eln_entries() -> str:
    """List all ELN entries."""
    return await _call_tool("query_eln_entries", {"query": ""})


@mcp.resource("resonantia://protocols")
async def list_protocols() -> str:
    """List all protocols."""
    return await _call_tool("query_protocols", {"query": ""})


# =========================================================================
# Entry point
# =========================================================================

if __name__ == "__main__":
    mcp.run()
