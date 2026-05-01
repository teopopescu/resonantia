Start and connect the Resonantia MCP server.

## Start standalone

```bash
cd /Users/teopopescu/Desktop/resonantia/backend
RESONANTIA_ORG_ID=org_default uv run python -m resonantia.mcp_server
```

Or with fastmcp CLI:
```bash
cd /Users/teopopescu/Desktop/resonantia/backend
uv run fastmcp run resonantia.mcp_server:mcp
```

## Add to Claude Code

```bash
claude mcp add resonantia -- uv run --directory /Users/teopopescu/Desktop/resonantia/backend python -m resonantia.mcp_server
```

## Available tools

- **Plate Mapping:** create_plate_map, cherry_pick, serial_dilution, generate_worklist, get_plate_map_details
- **Data Processing:** fit_dose_response, normalize_plate, calculate_z_prime, qpcr_analysis
- **Sample Management:** lookup_sample, check_inventory, get_expiring_samples
- **Experiments:** query_experiments, get_ic50_values
- **ELN:** create_eln_entry, query_eln_entries
- **Protocols:** create_protocol, calculate_dilution

## Available resources

- `resonantia://experiments` — List all experiments
- `resonantia://samples` — List all samples
- `resonantia://plate-maps` — List all plate maps
- `resonantia://eln` — List ELN entries
- `resonantia://protocols` — List protocols
