# SPEC: Agent-Driven Follow-Up Proposal (The Differentiator)

**ID:** P1.4b
**Phase:** 1 — Killer Workflow
**Branch:** `feat/agent-followup-proposal`
**Priority:** P1
**Effort:** 4 days
**Dependencies:** P1.4a (plate layout), P1.2 (dose-response)

---

## Problem Statement

After getting IC50 results, scientists mentally design the next experiment, then manually build the plate map. This is the highest-value reasoning step: turning assay results into the next actionable experiment. It's what separates Resonantia from a plate mapping tool.

Per codex-findings/02: Level 4 "Closed Loop" = `assay result → fit curve → identify ambiguous hits → propose concentration range → generate plate map → user approves`. This is the strongest 6-month product narrative.

---

## Scope

### In Scope
- New tool: `propose_follow_up_experiment`
- Agent analyzes IC50 results and proposes 2-3 follow-up options
- Each option: plate format, concentration range, replicate count, control layout, scientific rationale
- Multi-option approval card (user picks one)
- Selected option generates plate map (via P1.4a)

### Out of Scope
- ML-based experiment design (use LLM reasoning for now)
- Multi-day experiment orchestration (Temporal workflows — defer)
- Automated execution on instruments (Level 5 — defer)

---

## Architecture

### Follow-Up Reasoning Logic

The agent (via LLM reasoning + structured tool) considers:

```
Given:
  - IC50: 42.3 nM (CI: 38.1–47.0)
  - Hill slope: -1.18 (steep)
  - R²: 0.994 (excellent)
  - Z': 0.71 (good)
  - Original range: 0.5 nM → 10 μM (10-point, 3-fold)
  
Proposals:
  
  1. Hit Confirmation (most common next step)
     Rationale: Confirm IC50 with tighter range and more replicates
     Range: 5 nM → 500 nM (10-point, 2-fold, centered on IC50)
     Replicates: 4 (up from 3)
     Format: 384-well
     
  2. Selectivity Panel (if multiple kinases relevant)
     Rationale: Test selectivity across related targets
     Compounds: staurosporine vs 3 additional kinases
     Range: 5 concentrations bracketing IC50 (5, 20, 50, 100, 500 nM)
     Format: 384-well
     
  3. Cell Line Comparison (if indication-dependent)
     Rationale: Verify potency isn't cell-line-specific
     Cell lines: HEK293T (reference), A549, MCF-7
     Range: same as original (0.5 nM → 10 μM)
     Format: 96-well per cell line
```

### Tool Schema

```python
# New tool: propose_follow_up_experiment
{
    "name": "propose_follow_up_experiment",
    "description": "Analyze experiment results and propose 2-3 follow-up experiments with scientific rationale",
    "input_schema": {
        "experiment_id": "string (required)",
        "context": "string (optional — user's research goal or constraints)"
    },
    "gate_kind": "soft_review"  # User picks an option
}
```

### Response Schema

```python
class FollowUpOption(BaseModel):
    option_number: int
    title: str  # "Hit Confirmation"
    rationale: str  # Scientific reasoning
    plate_type: int  # 96 or 384
    concentration_range: dict  # { start_nM, end_nM, points, fold }
    replicates: int
    controls: dict  # { positive: str, negative: str, positions: str }
    estimated_wells: int
    compounds: list[str]
    
class FollowUpProposal(BaseModel):
    experiment_id: str
    summary: str  # "Based on IC50 42.3 nM..."
    options: list[FollowUpOption]  # 2-3 options
    recommended: int  # Which option the agent recommends
```

### Multi-Option Approval Card

```
┌─────────────────────────────────────────────────────┐
│ Follow-Up Proposal for EXP-2026-0142                │
│                                                      │
│ Based on IC50 42.3 nM (staurosporine, HEK293T):    │
│                                                      │
│ ○ Option 1: Hit Confirmation (recommended)           │
│   Tighter 10-point range around IC50, 4 replicates  │
│   384-well, 88 wells used                           │
│                                                      │
│ ○ Option 2: Selectivity Panel                        │
│   Test against PKC, CDK2, Aurora A at 5 conc.       │
│   384-well, 120 wells used                          │
│                                                      │
│ ○ Option 3: Cell Line Comparison                     │
│   Repeat in A549 + MCF-7                            │
│   3x 96-well plates                                 │
│                                                      │
│ [Select & Generate Plate Map]  [Modify]  [Cancel]   │
└─────────────────────────────────────────────────────┘
```

---

## Implementation

### Step 1: Follow-up reasoning in experiment_designer.py (day 1-2)
- `propose_follow_up(experiment: Experiment) -> FollowUpProposal`
- Load experiment results (IC50, Hill, R², Z')
- Apply heuristic rules + LLM reasoning to generate 2-3 options
- Each option includes concrete plate parameters (not vague suggestions)

### Step 2: Tool handler (day 2)
- Register `propose_follow_up_experiment` tool
- Gate: soft_review
- Returns FollowUpProposal as pending approval preview

### Step 3: Multi-option approval card (day 3)
- Frontend component: radio-select between options
- Shows rationale, plate format, well count per option
- "Recommended" badge on agent's preferred option
- Select + confirm → generates plate map via create_plate_map

### Step 4: Wire to plate generation (day 3-4)
- On approval: selected option parameters feed into plate_mapper
- Plate map generated + second approval gate (P1.4a flow)
- Or: combine into single approval (select option = approve plate)

### Step 5: Tests (day 4)
- Test: propose for high-quality IC50 → returns hit confirmation as recommended
- Test: propose for poor R² → includes "re-test with outlier removal" option
- Test: options have valid plate parameters (wells fit in format, concentrations are reasonable)
- Test: select option → plate map generated with correct parameters

---

## Expected Behavior

| IC50 Quality | Agent Proposal |
|-------------|----------------|
| IC50 42 nM, R² 0.99, Z' 0.71 | Hit confirmation (tighter range), selectivity panel, cell line comparison |
| IC50 42 nM, R² 0.85, Z' 0.71 | Re-test with outlier removal, hit confirmation with more replicates |
| IC50 42 nM, R² 0.99, Z' 0.35 | Assay optimization (poor Z' → optimize controls), re-test with optimized assay |
| Multiple compounds with IC50 < 100 nM | Cherry-pick all hits into confirmation plate, SAR follow-up |

---

## Acceptance Criteria

- [ ] `propose_follow_up_experiment` tool registered with gate_kind: soft_review
- [ ] Given an experiment_id with dose-response results, returns 2-3 follow-up options
- [ ] Each option includes: title, rationale, plate_type, concentration range, replicates, controls, estimated wells
- [ ] Agent recommends one option with scientific reasoning
- [ ] Frontend renders multi-option approval card with radio selection
- [ ] Selected option generates a plate map via create_plate_map
- [ ] Proposals are scientifically reasonable:
  - Tighter range is centered on IC50 (not random)
  - Replicate count >= original
  - Controls are always included
  - Concentrations span a pharmacologically relevant range
- [ ] Poor R² experiments get "re-test" as an option
- [ ] Poor Z' experiments get "optimize assay" as an option
- [ ] Cancel results in no plate map created

---

## Risks

- **LLM reasoning quality.** The follow-up proposals depend on the LLM understanding dose-response pharmacology. Mitigate with a strong system prompt that encodes standard follow-up patterns (hit confirmation, selectivity, dose-range expansion). The tool handler should validate that proposed concentrations are physically possible.
- **Scope creep.** Keep this to single-compound follow-up. Multi-compound SAR campaigns are a post-pilot feature.
- **Two approval gates in sequence.** Select option → generate plate map → approve plate map could feel heavy. Consider combining: selecting an option immediately shows the plate grid preview.
