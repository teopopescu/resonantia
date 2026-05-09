# SPEC: ELN Draft Generation from Results

**ID:** P1.3
**Phase:** 1 — Killer Workflow
**Branch:** `feat/eln-from-results`
**Priority:** P1
**Effort:** 3-4 days
**Dependencies:** P1.0 (approval gates), P1.2 (dose-response)

---

## Problem Statement

Scientists currently assemble experiment documentation manually: copy IC50 values from GraphPad, paste figures into Word, write methods from memory, email to themselves. The agent should auto-draft a structured ELN entry from experiment artifacts — but must not create it without user review (approval gate L2).

---

## Scope

### In Scope
- Enhance `create_eln_entry` tool to accept experiment_id and auto-populate sections
- Structured ELN template: Objective, Methods, Results, Conclusions, References
- Embed plot references and link to source data
- Approval gate integration (L2: soft_review)

### Out of Scope
- ELN submission to external systems (Phase 3 — eLabFTW)
- Co-authoring / review workflows (Phase 3)
- PDF export (already exists, keep as-is)

---

## Architecture

### ELN Template Structure

When `create_eln_entry` receives an `experiment_id`, the agent generates:

```markdown
# {Experiment Name}

## Objective
Determine IC50 of {compound} in {cell_line} {assay_type} assay.

## Methods
- **Plate format:** {plate_type}-well
- **Compound:** {compound_name}, {n_points}-point {dilution_factor}-fold dilution ({concentration_range})
- **Replicates:** {n_replicates}
- **Readout:** {readout_method}
- **Controls:** Positive ({pos_control}), Vehicle ({vehicle_control})

## Results
- **IC50:** {ic50} nM (95% CI: {ci_lower}–{ci_upper} nM)
- **Hill slope:** {hill_slope}
- **R²:** {r_squared}
- **Z':** {z_prime}
- **Outliers:** {outlier_count} points flagged at {outlier_wells}

![Dose-Response Curve]({plot_url})

## Conclusions
{agent-generated summary based on results quality and values}

## References
- Experiment: {experiment_id}
- Source data: {file_upload_id}
- Plate map: {plate_map_id} (if linked)
- Analysis date: {timestamp}
```

### Approval Integration

```
Agent calls create_eln_entry(experiment_id=..., title=..., ...)
    → Tool detects gate_kind: soft_review
    → Generates draft content using template + experiment data
    → Returns { pending_approval: true, token: "...", preview: { markdown: "..." } }
    → Agent shows: "Here's the draft ELN entry: [preview]. Confirm to save?"
    → Frontend renders ApprovalCard with markdown preview
    → User can Edit (modify in-place), Confirm, or Cancel
```

---

## Implementation

### Step 1: Template engine (day 1)
- Function: `generate_eln_content(experiment: Experiment) -> str`
- Loads experiment results (IC50, Hill, R², Z', plot URL)
- Fills template sections
- Agent adds conclusions based on result quality

### Step 2: Enhanced create_eln_entry handler (day 2)
- Accept `experiment_id` parameter
- If provided: load experiment, call template engine, generate draft
- If not provided: use content from agent message (existing behavior)
- Return pending_approval with markdown preview

### Step 3: Approval card for ELN (day 2-3)
- Render markdown preview in ApprovalCard
- "Edit" button opens inline markdown editor (modify before confirming)
- Confirmed entry saved with `status: draft` and linked to experiment

### Step 4: Tests (day 3-4)
- Test: create_eln_entry with experiment_id → returns pending with correct content
- Test: approve → entry persisted with experiment link
- Test: reject → no entry created
- Test: edit before confirm → modified content persisted

---

## Expected Behavior

| Action | Result |
|--------|--------|
| Agent: "Create ELN entry for experiment EXP-001" | Generates structured draft from experiment data |
| Draft shown to user | Approval card with full markdown preview |
| User clicks Confirm | Entry saved to DB as draft, linked to experiment |
| User clicks Edit, modifies conclusion, then Confirm | Modified content saved |
| User clicks Cancel | No entry created |

---

## Acceptance Criteria

- [ ] `create_eln_entry` with `experiment_id` generates structured ELN content from experiment data
- [ ] Generated content includes all sections: Objective, Methods, Results, Conclusions, References
- [ ] Results section embeds plot URL as markdown image
- [ ] Approval gate (L2): user sees preview and must Confirm before entry is created
- [ ] Cancel results in no database write
- [ ] Edit before Confirm saves modified content
- [ ] ELN entry links to experiment_id, file_upload_id, and plate_map_id (if available)
- [ ] Entry created with `status: draft` (not submitted)
- [ ] Template handles missing fields gracefully (e.g., no Z' if no controls)
