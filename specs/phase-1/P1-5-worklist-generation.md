# SPEC: Worklist Generation from Plate Map

**ID:** P1.5
**Phase:** 1 — Killer Workflow
**Branch:** `feat/worklist-from-plate-map`
**Priority:** P1
**Effort:** 2 days
**Dependencies:** P1.4a (plate layout)

---

## Problem Statement

Scientists re-enter plate layouts into vendor liquid handler software (Echo, Hamilton STAR, Opentrons). The biggest manual re-entry pain point. The worklist generator exists (`plate_mapper.py`) but needs approval gates (L3: hard_approval — instrument-bound actions are consequential) and download UX.

---

## Scope

### In Scope
- Wire existing worklist generation to approval gates (L3: hard_approval)
- Worklist preview (first 10 rows) in approval card
- Download button for generated CSV/GWL/Python
- Support: Echo (CSV with nL volumes), Hamilton (GWL), Opentrons (Python script)

### Out of Scope
- Direct instrument API integration (defer — Automata LINQ is post-pilot)
- Worklist validation against instrument constraints
- Multi-plate worklist batching

---

## Architecture

### Approval Flow (L3: Hard Approval)

```
Agent: "Generate a worklist for the Echo 550?"
    → Agent calls generate_worklist(plate_map_id, instrument="echo")
    → Gate: hard_approval
    → Generates worklist CSV content
    → Returns { pending_approval: true, preview: { rows: [...], instrument, summary }, warning: "This worklist will be formatted for the Echo 550." }
    → Frontend: ApprovalCard with amber warning + worklist preview table + Confirm/Cancel
    → User confirms → file saved via storage, download URL returned
```

### Worklist Formats

| Instrument | Format | Key Columns |
|-----------|--------|-------------|
| Echo 550 | CSV | Source Plate, Source Well, Dest Plate, Dest Well, Transfer Volume (nL) |
| Hamilton STAR | GWL (Gemini Worklist) | Aspirate/Dispense commands, volumes (μL) |
| Opentrons OT-2 | Python | `protocol.transfer()` calls with labware definitions |

---

## Implementation

### Step 1: Wire to approval gate (day 1)
- `generate_worklist` handler: gate_kind = hard_approval
- Generate worklist content from plate_map well_mappings
- Return preview (first 10 rows + summary stats)

### Step 2: Download endpoint (day 1)
- Save generated worklist via storage abstraction
- Return download URL: `/api/v1/files/serve/{worklist_path}`
- Filename: `worklist_{plate_map_name}_{instrument}_{date}.{ext}`

### Step 3: Approval card with warning (day 2)
- Amber warning banner: "This worklist targets {instrument}. Verify before loading."
- Table preview of first 10 transfer rows
- Summary: total transfers, total volume, source plates, destination plates
- Download button (active only after approval)

### Step 4: Tests (day 2)
- Test: generate Echo CSV → valid format, nL volumes
- Test: generate Hamilton GWL → valid command syntax
- Test: approval required before download URL is active
- Test: reject → no file generated

---

## Acceptance Criteria

- [ ] `generate_worklist` requires L3 hard_approval (explicit confirm with warning)
- [ ] Worklist preview shows first 10 rows as table in approval card
- [ ] Amber warning banner shows target instrument name
- [ ] Confirm → worklist file saved, download URL returned to user
- [ ] Cancel → no file generated
- [ ] Echo CSV format: Source Plate, Source Well, Dest Plate, Dest Well, Transfer Volume (nL)
- [ ] Hamilton GWL format: valid Aspirate/Dispense commands
- [ ] Opentrons Python: valid protocol script with labware definitions
- [ ] Worklist file persisted via storage (survives restart)
- [ ] File linked to plate_map record in database
