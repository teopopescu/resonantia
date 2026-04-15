Test a Resonantia agentic tool by sending a chat message that should trigger it.

Usage: /test-tool <tool_name>

Based on the tool name provided, construct an appropriate test message and send it to the backend:

Tool test prompts:
- `lookup_sample` → "Look up sample with barcode BC-001"
- `check_inventory` → "What's in our inventory? Show me stock levels"
- `query_experiments` → "List all experiments"
- `get_ic50_values` → "What are the IC50 values from our dose-response experiments?"
- `fit_dose_response` → "Fit a dose-response curve to concentrations [0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30] and responses [2, 5, 12, 28, 55, 78, 93, 99]"
- `create_plate_map` → "Create a plate map for a 96-well plate mapping wells A1-A8 from source to destination"
- `serial_dilution` → "Set up an 8-point serial dilution starting at 10 uM with 3-fold dilution"
- `calculate_z_prime` → "Calculate Z-prime with positive controls [95, 98, 92, 97] and negative controls [3, 5, 2, 4]"
- `create_eln_entry` → "Create a new ELN entry titled 'Test Experiment' with content 'Testing the ELN tool'"
- `query_eln_entries` → "Search ELN entries for 'experiment'"
- `create_protocol` → "Create a protocol for cell viability assay with 3 steps"
- `design_next_experiment` → "Analyze our recent experiments and recommend what to test next"

Run the test:
```bash
curl -s -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -H "X-Org-Id: org_default" \
  -d "{\"message\": \"<test_prompt>\", \"clerk_user_id\": \"test-user\"}" | python3 -m json.tool
```

Check the response for: tool_calls (did the right tool get called?), message (is the response useful?), errors.
