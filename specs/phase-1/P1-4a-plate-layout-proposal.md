# SPEC: Plate Layout Proposal (Cherry-Pick / Serial Dilution)

**ID:** P1.4a
**Phase:** 1 — Killer Workflow
**Branch:** `feat/plate-layout-proposal`
**Priority:** P1
**Effort:** 3 days
**Dependencies:** P1.0 (approval gates), P1.2 (dose-response)

---

## Problem Statement

Scientists manually design plate maps in Excel, then re-enter well assignments into liquid handler software. The agent should create plate maps from natural language instructions and present them visually for approval before persisting.

The plate mapper service exists (`plate_mapper.py`) with cherry-pick, serial dilution, and replicate logic. This spec wires it into the approval gate system with visual preview.

---

## Scope

### In Scope
- Wire existing plate mapper to approval gates
- Visual plate grid preview in approval card
- Cherry-pick mode: user specifies compounds + destination format
- Serial dilution mode: user specifies starting concentration, fold, points
- 96-well and 384-well format support

### Out of Scope
- Agent-driven follow-up reasoning (P1.4b)
- 1536-well format (defer)
- Drag-and-drop plate editing (existing plate page handles this)

---

## Architecture

### Approval Flow

```
User: "Cherry-pick the top 3 hits into a 384-well confirmation plate"
    → Agent calls create_plate_map(mode="cherry_pick", compounds=[...], plate_type=384, ...)
    → Tool detects gate_kind: soft_review
    → plate_mapper.generate_plate_map() creates well assignments
    → Returns { pending_approval: true, preview: { plate_grid, well_assignments, summary } }
    → Frontend renders plate grid (color-coded wells, compound labels, control positions)
    → User confirms → plate map persisted to DB
```

### Visual Preview Data

```json
{
  "plate_type": 384,
  "rows": 16,
  "cols": 24,
  "wells": [
    { "position": "A1", "type": "control_positive", "compound": "DMSO", "color": "#22c55e" },
    { "position": "A2", "type": "sample", "compound": "Staurosporine", "concentration_nM": 500, "color": "#3b82f6" },
    ...
  ],
  "summary": {
    "total_wells": 384,
    "used_wells": 88,
    "compounds": 3,
    "replicates": 3,
    "controls": { "positive": 16, "negative": 16 }
  }
}
```

---

## Implementation

### Step 1: Wire plate mapper to approval (day 1)
- `create_plate_map` handler generates layout via `plate_mapper.py`
- Returns pending_approval with visual preview data

### Step 2: Plate grid preview component (day 2)
- Render 96 or 384-well grid in ApprovalCard
- Color-code by: sample (blue), positive control (green), negative control (red), empty (gray)
- Hover tooltip: compound name, concentration, replicate number
- Summary stats below grid

### Step 3: Persist on approval (day 2-3)
- Approved plate map saved to `plate_maps` table
- Linked to experiment if context available
- Well assignments stored in `well_mappings` JSON field

### Step 4: Tests (day 3)
- Test: cherry-pick 3 compounds → returns valid layout with controls
- Test: serial dilution 10-point → returns correct concentration series
- Test: approve → plate map in DB; reject → no record

---

## Acceptance Criteria

- [ ] `create_plate_map` with cherry-pick mode returns visual plate grid preview
- [ ] `create_plate_map` with serial dilution returns concentration series layout
- [ ] Approval card renders 96 or 384-well grid with color-coded wells
- [ ] Well tooltip shows: compound, concentration, replicate number
- [ ] Summary shows: total/used wells, compound count, replicate count, control count
- [ ] Confirm → plate map persisted to database with well_mappings
- [ ] Cancel → no database record created
- [ ] Supports 96-well and 384-well plate types
- [ ] Controls placed in standard positions (column 1 and 24 for 384-well)
