"""Redis-backed agentic tool schema registry.

Tools are agent capabilities -- things the LLM can invoke during conversations.
Schemas are stored in a Redis hash under ``resonantia:tools`` and converted to
Anthropic's tool-use format when passed to the model.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from typing import Any

import redis.asyncio as aioredis

from resonantia.config import get_settings

logger = logging.getLogger(__name__)

REDIS_KEY = "resonantia:tools"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ToolParameter:
    name: str
    type: str  # string, number, boolean, array, object
    description: str
    required: bool = True
    enum: list[str] | None = None
    default: Any = None


@dataclass
class ToolSchema:
    name: str
    description: str
    category: str  # plate_mapping, data_processing, sample_management, microscopy, protocol, general
    parameters: list[ToolParameter]
    version: str = "1.0"
    enabled: bool = True


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _serialize(tool: ToolSchema) -> str:
    return json.dumps(asdict(tool))


def _deserialize(raw: str | bytes) -> ToolSchema:
    data = json.loads(raw)
    data["parameters"] = [ToolParameter(**p) for p in data["parameters"]]
    return ToolSchema(**data)


def tool_schema_to_anthropic(tool: ToolSchema) -> dict[str, Any]:
    """Convert a ``ToolSchema`` into Anthropic's tool-use format."""
    properties: dict[str, Any] = {}
    required: list[str] = []
    for p in tool.parameters:
        prop: dict[str, Any] = {"type": p.type, "description": p.description}
        if p.type == "array":
            prop["items"] = {"type": "string"}  # default array item type
        if p.enum is not None:
            prop["enum"] = p.enum
        if p.default is not None:
            prop["default"] = p.default
        properties[p.name] = prop
        if p.required:
            required.append(p.name)

    return {
        "name": tool.name,
        "description": tool.description,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


# ---------------------------------------------------------------------------
# Redis connection helper
# ---------------------------------------------------------------------------

_pool: aioredis.Redis | None = None


async def _get_redis() -> aioredis.Redis:
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _pool


async def close_redis() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


# ---------------------------------------------------------------------------
# Registry CRUD
# ---------------------------------------------------------------------------

async def register_tool(tool: ToolSchema) -> None:
    """Store a tool schema in Redis."""
    r = await _get_redis()
    await r.hset(REDIS_KEY, tool.name, _serialize(tool))
    logger.info("Registered tool %s (category=%s)", tool.name, tool.category)


async def get_tool(name: str) -> ToolSchema | None:
    """Retrieve a single tool schema by name."""
    r = await _get_redis()
    raw = await r.hget(REDIS_KEY, name)
    if raw is None:
        return None
    return _deserialize(raw)


async def list_tools(category: str | None = None) -> list[ToolSchema]:
    """List all registered tools, optionally filtered by category."""
    r = await _get_redis()
    all_raw = await r.hvals(REDIS_KEY)
    tools = [_deserialize(v) for v in all_raw]
    if category:
        tools = [t for t in tools if t.category == category]
    return sorted(tools, key=lambda t: (t.category, t.name))


async def remove_tool(name: str) -> bool:
    """Remove a tool from the registry. Returns True if it existed."""
    r = await _get_redis()
    removed = await r.hdel(REDIS_KEY, name)
    return removed > 0


async def search_tools(query: str) -> list[ToolSchema]:
    """Simple keyword search on tool name + description."""
    query_lower = query.lower()
    all_tools = await list_tools()
    results = []
    for t in all_tools:
        if query_lower in t.name.lower() or query_lower in t.description.lower():
            results.append(t)
    return results


async def get_tools_as_anthropic(category: str | None = None) -> list[dict[str, Any]]:
    """Return all enabled tools in Anthropic API format."""
    tools = await list_tools(category)
    return [tool_schema_to_anthropic(t) for t in tools if t.enabled]


# ---------------------------------------------------------------------------
# Default tools
# ---------------------------------------------------------------------------

def _default_tools() -> list[ToolSchema]:
    return [
        # -- plate_mapping --
        ToolSchema(
            name="create_plate_map",
            description="Create a source-destination plate map for liquid handling transfers.",
            category="plate_mapping",
            parameters=[
                ToolParameter(name="name", type="string", description="Name for the plate map"),
                ToolParameter(name="plate_type", type="string", description="Destination plate type", enum=["96", "384"]),
                ToolParameter(name="source_plates", type="array", description="Array of source plate identifiers"),
                ToolParameter(name="mapping_mode", type="string", description="Transfer mapping strategy", enum=["cherry-pick", "serial-dilution", "replicate"]),
                ToolParameter(name="destination_format", type="string", description="Destination plate format", required=False, default="96"),
            ],
        ),
        ToolSchema(
            name="generate_worklist",
            description="Generate a liquid handler worklist file from an existing plate map.",
            category="plate_mapping",
            parameters=[
                ToolParameter(name="plate_map_id", type="string", description="ID of the plate map to generate from"),
                ToolParameter(name="format", type="string", description="Output worklist format", enum=["echo-csv", "hamilton-gwl", "opentrons-py"]),
                ToolParameter(name="transfer_volume", type="number", description="Volume to transfer per well"),
                ToolParameter(name="volume_unit", type="string", description="Unit for transfer volume", enum=["nL", "uL", "mL"], required=False, default="uL"),
            ],
        ),
        ToolSchema(
            name="cherry_pick",
            description="Cherry pick specific compounds or samples from source plates into a destination plate.",
            category="plate_mapping",
            parameters=[
                ToolParameter(name="source_plate_ids", type="array", description="Array of source plate identifiers"),
                ToolParameter(name="hit_list", type="array", description="Array of well IDs to cherry pick (e.g. ['A1','B3','H12'])"),
                ToolParameter(name="destination_plate_type", type="string", description="Destination plate format", enum=["96", "384"], required=False, default="96"),
            ],
        ),
        ToolSchema(
            name="serial_dilution",
            description="Generate a serial dilution plate layout for dose-response experiments.",
            category="plate_mapping",
            parameters=[
                ToolParameter(name="compound_name", type="string", description="Name of the compound to dilute"),
                ToolParameter(name="start_concentration", type="number", description="Starting (highest) concentration in uM"),
                ToolParameter(name="dilution_factor", type="number", description="Fold dilution between each point (e.g. 3 for 1:3)"),
                ToolParameter(name="num_points", type="number", description="Number of concentration points"),
                ToolParameter(name="direction", type="string", description="Dilution direction on plate", enum=["horizontal", "vertical"], required=False, default="horizontal"),
            ],
        ),

        # -- data_processing --
        ToolSchema(
            name="fit_dose_response",
            description="Fit a 4-parameter logistic curve to dose-response data and compute IC50/EC50.",
            category="data_processing",
            parameters=[
                ToolParameter(name="concentrations", type="array", description="Array of concentration values"),
                ToolParameter(name="responses", type="array", description="Array of response/signal values"),
                ToolParameter(name="model", type="string", description="Curve model to fit", enum=["4pl", "3pl"], required=False, default="4pl"),
            ],
        ),
        ToolSchema(
            name="normalize_plate",
            description="Normalize plate reader data using control wells.",
            category="data_processing",
            parameters=[
                ToolParameter(name="raw_data", type="array", description="Array of raw plate reader values (row-major)"),
                ToolParameter(name="method", type="string", description="Normalization method", enum=["z-score", "percent-of-control", "robust-z"]),
                ToolParameter(name="positive_control_wells", type="array", description="Well IDs of positive controls (e.g. ['A1','A2'])", required=False),
                ToolParameter(name="negative_control_wells", type="array", description="Well IDs of negative controls", required=False),
            ],
        ),
        ToolSchema(
            name="calculate_z_prime",
            description="Calculate Z-prime factor to assess high-throughput screening assay quality.",
            category="data_processing",
            parameters=[
                ToolParameter(name="positive_values", type="array", description="Signal values from positive control wells"),
                ToolParameter(name="negative_values", type="array", description="Signal values from negative control wells"),
            ],
        ),
        ToolSchema(
            name="qpcr_analysis",
            description="Perform delta-delta Ct analysis for relative gene expression quantification.",
            category="data_processing",
            parameters=[
                ToolParameter(name="ct_values", type="object", description="Object mapping sample names to Ct value arrays"),
                ToolParameter(name="reference_gene", type="string", description="Name of the housekeeping/reference gene"),
                ToolParameter(name="control_sample", type="string", description="Name of the control/calibrator sample"),
            ],
        ),

        # -- sample_management --
        ToolSchema(
            name="lookup_sample",
            description="Look up a sample or reagent by barcode, name, or lot number.",
            category="sample_management",
            parameters=[
                ToolParameter(name="query", type="string", description="Search term (barcode, name, or lot number)"),
                ToolParameter(name="search_by", type="string", description="Field to search", enum=["barcode", "name", "lot"], required=False, default="barcode"),
            ],
        ),
        ToolSchema(
            name="check_inventory",
            description="Check current stock levels and expiry status of a reagent.",
            category="sample_management",
            parameters=[
                ToolParameter(name="reagent_name", type="string", description="Name of the reagent to check"),
                ToolParameter(name="check_expiry", type="boolean", description="Whether to include expiry date check", required=False, default=True),
            ],
        ),
        ToolSchema(
            name="add_sample",
            description="Register a new sample or reagent in the inventory system.",
            category="sample_management",
            parameters=[
                ToolParameter(name="name", type="string", description="Sample name"),
                ToolParameter(name="type", type="string", description="Sample type (e.g. compound, antibody, cell-line, plasmid)"),
                ToolParameter(name="barcode", type="string", description="Unique barcode identifier"),
                ToolParameter(name="location", type="string", description="Storage location (e.g. Freezer-2/Shelf-3/Box-A)"),
                ToolParameter(name="storage_temp", type="string", description="Storage temperature (e.g. -20C, 4C, RT)", required=False),
                ToolParameter(name="lot_number", type="string", description="Manufacturer lot number", required=False),
                ToolParameter(name="quantity", type="number", description="Amount in stock"),
                ToolParameter(name="unit", type="string", description="Unit of quantity (e.g. uL, mg, vials)"),
            ],
        ),

        # -- microscopy --
        ToolSchema(
            name="browse_microscopy",
            description="Browse microscopy images for a given plate, well, channel, and field of view.",
            category="microscopy",
            parameters=[
                ToolParameter(name="plate_id", type="string", description="Plate identifier"),
                ToolParameter(name="well", type="string", description="Well position (e.g. A1, B12)", required=False),
                ToolParameter(name="channel", type="string", description="Fluorescence channel (e.g. DAPI, GFP, mCherry)", required=False),
                ToolParameter(name="fov", type="number", description="Field of view index", required=False),
            ],
        ),
        ToolSchema(
            name="generate_montage",
            description="Create an image montage compositing multiple fields of view or channels.",
            category="microscopy",
            parameters=[
                ToolParameter(name="plate_id", type="string", description="Plate identifier"),
                ToolParameter(name="wells", type="array", description="Array of well positions to include"),
                ToolParameter(name="channels", type="array", description="Array of channels to overlay"),
                ToolParameter(name="layout", type="string", description="Montage layout (e.g. '2x3', '4x4', 'auto')", required=False, default="auto"),
            ],
        ),

        # -- protocol --
        ToolSchema(
            name="design_protocol",
            description="Design an experimental protocol with steps, reagents, and timing.",
            category="protocol",
            parameters=[
                ToolParameter(name="experiment_type", type="string", description="Type of experiment (e.g. cytotoxicity, transfection, western-blot)"),
                ToolParameter(name="cell_line", type="string", description="Cell line to use", required=False),
                ToolParameter(name="target", type="string", description="Target gene/protein", required=False),
                ToolParameter(name="assay_format", type="string", description="Assay plate format", enum=["96", "384", "6", "24"], required=False, default="96"),
            ],
        ),

        # -- general --
        ToolSchema(
            name="search_literature",
            description="Search scientific literature databases (PubMed, bioRxiv) for relevant papers.",
            category="general",
            parameters=[
                ToolParameter(name="query", type="string", description="Search query (keywords, gene names, compound names)"),
                ToolParameter(name="max_results", type="number", description="Maximum papers to return", required=False, default=10),
                ToolParameter(name="date_range", type="string", description="Date filter (e.g. 'last-year', 'last-5-years', '2020-2024')", required=False),
            ],
        ),

        # -- structured queries (agentic database access) --
        ToolSchema(
            name="query_experiments",
            description="Search experiments by name, description, or protocol. Returns experiment details including results (IC50, Z-prime, etc).",
            category="general",
            parameters=[
                ToolParameter(name="query", type="string", description="Search term to match against experiment name, description, or protocol"),
            ],
        ),
        ToolSchema(
            name="query_plate_maps",
            description="Search plate maps by name or description. Returns plate map details including well mapping counts.",
            category="general",
            parameters=[
                ToolParameter(name="query", type="string", description="Search term to match against plate map name or description"),
            ],
        ),
        ToolSchema(
            name="get_ic50_values",
            description="Retrieve IC50/EC50 dose-response results for a specific compound across all experiments.",
            category="general",
            parameters=[
                ToolParameter(name="compound", type="string", description="Compound name to search for (e.g. Staurosporine, Rapamycin)"),
            ],
        ),
        ToolSchema(
            name="get_expiring_samples",
            description="Find all samples and reagents expiring within a given number of days.",
            category="general",
            parameters=[
                ToolParameter(name="days", type="number", description="Number of days to look ahead for expiring items", required=False, default=30),
            ],
        ),
        ToolSchema(
            name="get_sample_stats",
            description="Get summary statistics about the sample inventory: total count, count by type, expiring items, expired items.",
            category="general",
            parameters=[],
        ),

        # -- file access --
        ToolSchema(
            name="list_files",
            description="List all files uploaded by the user in this session.",
            category="general",
            parameters=[],
        ),
        ToolSchema(
            name="get_file_info",
            description="Get details about a specific uploaded file by ID or filename.",
            category="general",
            parameters=[
                ToolParameter(name="file_id", type="string", description="File ID to look up", required=False),
                ToolParameter(name="filename", type="string", description="Filename to search for", required=False),
            ],
        ),

        # -- eln --
        ToolSchema(
            name="create_eln_entry",
            description="Create an ELN (Electronic Lab Notebook) entry, optionally auto-generating content from an experiment.",
            category="eln",
            parameters=[
                ToolParameter(name="title", type="string", description="Title for the ELN entry"),
                ToolParameter(name="experiment_id", type="string", description="Optional experiment UUID to auto-generate content from", required=False),
                ToolParameter(name="content_markdown", type="string", description="Markdown content for the entry (used if no experiment_id)", required=False),
                ToolParameter(name="tags", type="array", description="Tags for the entry", required=False),
            ],
        ),
        ToolSchema(
            name="query_eln_entries",
            description="Search ELN entries by title, content, or tags.",
            category="eln",
            parameters=[
                ToolParameter(name="query", type="string", description="Search term to match against title or content"),
                ToolParameter(name="status", type="string", description="Filter by status", enum=["draft", "submitted", "archived"], required=False),
            ],
        ),
        ToolSchema(
            name="get_eln_entry",
            description="Get full ELN entry content including appendices by ID or entry number.",
            category="eln",
            parameters=[
                ToolParameter(name="entry_id", type="string", description="ELN entry UUID or entry number (e.g. ELN-2026-0001)"),
            ],
        ),
        ToolSchema(
            name="submit_eln_entry",
            description="Submit an ELN entry for audit compliance, making it immutable.",
            category="eln",
            parameters=[
                ToolParameter(name="entry_id", type="string", description="ELN entry UUID to submit"),
            ],
        ),

        # -- protocol tools --
        ToolSchema(
            name="create_protocol",
            description="Create an experimental protocol with AI-generated steps based on experiment type.",
            category="protocol",
            parameters=[
                ToolParameter(name="name", type="string", description="Protocol name"),
                ToolParameter(name="experiment_type", type="string", description="Type of experiment (e.g. cytotoxicity, transfection, western-blot)", required=False),
                ToolParameter(name="description", type="string", description="Protocol description", required=False),
                ToolParameter(name="cell_line", type="string", description="Cell line to use", required=False),
            ],
        ),
        ToolSchema(
            name="query_protocols",
            description="Search protocols by name or description.",
            category="protocol",
            parameters=[
                ToolParameter(name="query", type="string", description="Search term to match against protocol name or description"),
                ToolParameter(name="status", type="string", description="Filter by status", enum=["draft", "published", "archived"], required=False),
            ],
        ),
        ToolSchema(
            name="check_protocol_inventory",
            description="Check if all reagents needed for a protocol are available in the sample inventory.",
            category="protocol",
            parameters=[
                ToolParameter(name="protocol_id", type="string", description="Protocol UUID to check inventory for"),
            ],
        ),
        ToolSchema(
            name="calculate_dilution",
            description="C1V1=C2V2 dilution calculator. Provide three of four values to solve for the missing one.",
            category="protocol",
            parameters=[
                ToolParameter(name="c1", type="number", description="Initial concentration"),
                ToolParameter(name="v1", type="number", description="Initial volume (omit to solve)", required=False),
                ToolParameter(name="c2", type="number", description="Final concentration"),
                ToolParameter(name="v2", type="number", description="Final volume (omit to solve)", required=False),
                ToolParameter(name="unit_concentration", type="string", description="Concentration unit", required=False, default="uM"),
                ToolParameter(name="unit_volume", type="string", description="Volume unit", required=False, default="uL"),
            ],
        ),

        # -- detailed plate access --
        ToolSchema(
            name="get_plate_map_details",
            description="Get full details of a plate map including well-to-well mappings, source/destination plates, and worklist status.",
            category="plate_mapping",
            parameters=[
                ToolParameter(name="plate_map_name", type="string", description="Name of the plate map to look up"),
            ],
        ),

        # -- processing results --
        ToolSchema(
            name="get_processing_results",
            description="Get results from completed data processing runs (dose-response, normalization, qPCR). Returns IC50, Z-prime, fold changes etc.",
            category="data_processing",
            parameters=[
                ToolParameter(name="type", type="string", description="Filter by processing type (e.g. 'dose-response', 'normalization', 'qpcr')", required=False),
            ],
        ),
    ]


async def seed_default_tools() -> None:
    """Register all default tools into Redis. Idempotent."""
    defaults = _default_tools()
    for tool in defaults:
        await register_tool(tool)
    logger.info("Seeded %d default tools into Redis", len(defaults))
