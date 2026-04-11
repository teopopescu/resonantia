# Resonantia — Agentic Tool Registry

Resonantia's agent has access to 15 tools across 6 categories. Tools are stored in Redis
(`resonantia:tools` hash) and loaded at runtime by the LLM agent service. Each tool is
converted to Anthropic's tool-use format before being passed to Claude.

## API

| Method   | Endpoint                    | Description                          |
|----------|-----------------------------|--------------------------------------|
| `GET`    | `/api/v1/tools`             | List all tools (optional `?category=`) |
| `GET`    | `/api/v1/tools/{name}`      | Get a single tool schema             |
| `GET`    | `/api/v1/tools/search?q=…`  | Keyword search across name + description |
| `POST`   | `/api/v1/tools`             | Register a new tool                  |
| `DELETE` | `/api/v1/tools/{name}`      | Remove a tool                        |

---

## Plate Mapping (4 tools)

### `create_plate_map`
Create a source-destination plate map for liquid handling transfers.

| Parameter          | Type     | Required | Description                                |
|--------------------|----------|----------|--------------------------------------------|
| `name`             | string   | yes      | Name for the plate map                     |
| `plate_type`       | string   | yes      | Destination plate type (`96` \| `384`)     |
| `source_plates`    | array    | yes      | Array of source plate identifiers          |
| `mapping_mode`     | string   | yes      | Transfer strategy (`cherry-pick` \| `serial-dilution` \| `replicate`) |
| `destination_format` | string | no       | Destination plate format (default: `96`)   |

### `generate_worklist`
Generate a liquid handler worklist file from an existing plate map.

| Parameter         | Type   | Required | Description                                   |
|-------------------|--------|----------|-----------------------------------------------|
| `plate_map_id`    | string | yes      | ID of the plate map to generate from          |
| `format`          | string | yes      | Output format (`echo-csv` \| `hamilton-gwl` \| `opentrons-py`) |
| `transfer_volume` | number | yes      | Volume to transfer per well                   |
| `volume_unit`     | string | no       | Volume unit (`nL` \| `uL` \| `mL`, default: `uL`) |

### `cherry_pick`
Cherry pick specific compounds or samples from source plates into a destination plate.

| Parameter               | Type   | Required | Description                                |
|-------------------------|--------|----------|--------------------------------------------|
| `source_plate_ids`      | array  | yes      | Array of source plate identifiers          |
| `hit_list`              | array  | yes      | Well IDs to cherry pick (e.g. `["A1","B3","H12"]`) |
| `destination_plate_type`| string | no       | Destination format (`96` \| `384`, default: `96`) |

### `serial_dilution`
Generate a serial dilution plate layout for dose-response experiments.

| Parameter            | Type   | Required | Description                                   |
|----------------------|--------|----------|-----------------------------------------------|
| `compound_name`      | string | yes      | Name of the compound to dilute                |
| `start_concentration`| number | yes      | Starting (highest) concentration in uM        |
| `dilution_factor`    | number | yes      | Fold dilution between points (e.g. 3 for 1:3) |
| `num_points`         | number | yes      | Number of concentration points                |
| `direction`          | string | no       | Dilution direction (`horizontal` \| `vertical`, default: `horizontal`) |

---

## Data Processing (4 tools)

### `fit_dose_response`
Fit a 4-parameter logistic curve to dose-response data and compute IC50/EC50.

| Parameter       | Type   | Required | Description                              |
|-----------------|--------|----------|------------------------------------------|
| `concentrations`| array  | yes      | Array of concentration values            |
| `responses`     | array  | yes      | Array of response/signal values          |
| `model`         | string | no       | Curve model (`4pl` \| `3pl`, default: `4pl`) |

### `normalize_plate`
Normalize plate reader data using control wells.

| Parameter               | Type   | Required | Description                                   |
|-------------------------|--------|----------|-----------------------------------------------|
| `raw_data`              | array  | yes      | Array of raw plate reader values (row-major)  |
| `method`                | string | yes      | Method (`z-score` \| `percent-of-control` \| `robust-z`) |
| `positive_control_wells`| array  | no       | Well IDs of positive controls                 |
| `negative_control_wells`| array  | no       | Well IDs of negative controls                 |

### `calculate_z_prime`
Calculate Z-prime factor to assess high-throughput screening assay quality.

| Parameter         | Type  | Required | Description                          |
|-------------------|-------|----------|--------------------------------------|
| `positive_values` | array | yes      | Signal values from positive controls |
| `negative_values` | array | yes      | Signal values from negative controls |

### `qpcr_analysis`
Perform delta-delta Ct analysis for relative gene expression quantification.

| Parameter       | Type   | Required | Description                                    |
|-----------------|--------|----------|------------------------------------------------|
| `ct_values`     | object | yes      | Object mapping sample names to Ct value arrays |
| `reference_gene`| string | yes      | Name of the housekeeping/reference gene        |
| `control_sample`| string | yes      | Name of the control/calibrator sample          |

---

## Sample Management (3 tools)

### `lookup_sample`
Look up a sample or reagent by barcode, name, or lot number.

| Parameter  | Type   | Required | Description                                     |
|------------|--------|----------|-------------------------------------------------|
| `query`    | string | yes      | Search term (barcode, name, or lot number)      |
| `search_by`| string | no       | Field to search (`barcode` \| `name` \| `lot`, default: `barcode`) |

### `check_inventory`
Check current stock levels and expiry status of a reagent.

| Parameter      | Type    | Required | Description                           |
|----------------|---------|----------|---------------------------------------|
| `reagent_name` | string  | yes      | Name of the reagent to check          |
| `check_expiry` | boolean | no       | Include expiry date check (default: `true`) |

### `add_sample`
Register a new sample or reagent in the inventory system.

| Parameter     | Type   | Required | Description                                    |
|---------------|--------|----------|------------------------------------------------|
| `name`        | string | yes      | Sample name                                    |
| `type`        | string | yes      | Sample type (compound, antibody, cell-line, plasmid) |
| `barcode`     | string | yes      | Unique barcode identifier                      |
| `location`    | string | yes      | Storage location (e.g. Freezer-2/Shelf-3/Box-A)|
| `storage_temp`| string | no       | Storage temperature (e.g. -20C, 4C, RT)        |
| `lot_number`  | string | no       | Manufacturer lot number                        |
| `quantity`    | number | yes      | Amount in stock                                |
| `unit`        | string | yes      | Unit of quantity (uL, mg, vials)               |

---

## Microscopy (2 tools)

### `browse_microscopy`
Browse microscopy images for a given plate, well, channel, and field of view.

| Parameter  | Type   | Required | Description                                |
|------------|--------|----------|--------------------------------------------|
| `plate_id` | string | yes      | Plate identifier                           |
| `well`     | string | no       | Well position (e.g. A1, B12)               |
| `channel`  | string | no       | Fluorescence channel (DAPI, GFP, mCherry)  |
| `fov`      | number | no       | Field of view index                        |

### `generate_montage`
Create an image montage compositing multiple fields of view or channels.

| Parameter  | Type   | Required | Description                                |
|------------|--------|----------|--------------------------------------------|
| `plate_id` | string | yes      | Plate identifier                           |
| `wells`    | array  | yes      | Array of well positions to include         |
| `channels` | array  | yes      | Array of channels to overlay               |
| `layout`   | string | no       | Montage layout (e.g. `2x3`, `auto`, default: `auto`) |

---

## Protocol (1 tool)

### `design_protocol`
Design an experimental protocol with steps, reagents, and timing.

| Parameter        | Type   | Required | Description                                    |
|------------------|--------|----------|------------------------------------------------|
| `experiment_type`| string | yes      | Experiment type (cytotoxicity, transfection, western-blot) |
| `cell_line`      | string | no       | Cell line to use                               |
| `target`         | string | no       | Target gene/protein                            |
| `assay_format`   | string | no       | Plate format (`96` \| `384` \| `6` \| `24`, default: `96`) |

---

## General (1 tool)

### `search_literature`
Search scientific literature databases (PubMed, bioRxiv) for relevant papers.

| Parameter    | Type   | Required | Description                                    |
|--------------|--------|----------|------------------------------------------------|
| `query`      | string | yes      | Search query (keywords, gene names, compounds) |
| `max_results`| number | no       | Maximum papers to return (default: `10`)       |
| `date_range` | string | no       | Date filter (e.g. `last-year`, `2020-2024`)    |

---

## Adding Custom Tools

Tools can be registered at runtime via the API:

```bash
curl -X POST http://localhost:8000/api/v1/tools \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_custom_tool",
    "description": "Description of what this tool does",
    "category": "general",
    "parameters": [
      {
        "name": "input",
        "type": "string",
        "description": "Input value",
        "required": true
      }
    ]
  }'
```

Tools are automatically picked up by the agent on the next conversation turn.

## Architecture

```
User message
    |
    v
Agent Service (agent.py)
    |-- loads tools from Redis via get_tools_as_anthropic()
    |-- converts ToolSchema -> Anthropic tool format
    |-- sends to Claude API with tool definitions
    |
    v
Claude decides which tool to call
    |
    v
Tool execution (plate_mapper.py, data_processor.py, etc.)
    |
    v
Result returned to Claude for response generation
```
