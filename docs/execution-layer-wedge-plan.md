# Resonantia Execution Layer Wedge

## Strategic Decision

Resonantia should sell a narrow, operational workflow before it sells the
broader platform story.

The external wedge is:

> Resonantia is the execution layer between experiment intent and lab automation
> hardware.

The internal architecture can still remain agentic and extensible, but the
startup-grade product promise should be:

> Describe an assay. Get a validated, auditable worklist for your liquid
> handler.

This avoids competing head-on with ELN/LIMS platforms such as Benchling and
instead positions Resonantia as the instrument-aware layer they do not deeply
own: converting experimental intent into executable, validated lab actions.

## Initial Workflow

The first workflow should be liquid-handler and acoustic-dispenser execution,
starting with Echo-compatible worklist generation.

1. Scientist describes the assay or uploads source/destination plate files.
2. Resonantia generates a destination plate map and transfer worklist.
3. Resonantia validates constraints:
   - instrument volume range
   - dead volume
   - source availability
   - concentration series
   - controls
   - replicates
   - duplicate destination wells
   - edge-effect rules
4. Scientist reviews warnings and manually approves the executable artifact.
5. Resonantia exports the worklist as instrument-native CSV/GWL/Python.
6. Scientist runs the instrument.
7. Resonantia ingests run results and plate-reader outputs.
8. Resonantia writes structured results back to the customer's ELN/LIMS.
9. Every action, input, validation, approval, and export is audit logged.

## Product Framing

Do not lead with:

- AI lab operating system
- general lab chat
- broad ELN/LIMS replacement
- generic agent platform
- voice assistant
- microscopy browser

Lead with:

- validated plate maps
- instrument-native worklists
- liquid-handler constraints
- manual approval
- immutable run logs
- result ingestion
- ELN/LIMS write-back

Recommended headline:

> Turn experiment intent into validated liquid-handler worklists.

Recommended one-liner:

> Resonantia generates, validates, approves, and records automation-ready plate
> maps and worklists for screening labs.

## Product Surface Mapping

The existing modules stay, but their job changes:

| Surface | New Role |
| --- | --- |
| Console | Natural-language run setup and review |
| Plates | Core run builder: plate maps, constraints, worklists |
| Inventory | Source availability, dead-volume and stock checks |
| Protocols | Reusable run templates and method constraints |
| Processing | Result ingestion and assay analysis |
| Notebook | Audit summary and ELN/LIMS write-back |

The product should feel like a run execution console, not a set of unrelated
lab-informatics tabs.

## Design-Partner Validation

Ask each design partner for:

- 5 real source plate files
- 5 real destination plate layouts
- 5 recent worklists
- target instrument model and export format
- common spreadsheet edits they make manually
- common failure modes
- plate-reader result files
- ELN/LIMS handoff format

Run shadow-mode comparisons:

| Question | Measurement |
| --- | --- |
| Can Resonantia reproduce the human worklist? | row-level diff vs accepted worklist |
| Does it reduce time? | minutes from intent to validated export |
| Does it catch real errors? | validation warnings accepted as useful |
| Does it avoid guessing? | ambiguous requests trigger clarification |
| Is the artifact trusted? | scientist willingness to run it |
| Is the record useful? | ELN/LIMS write-back accepted with minimal edits |

Success criterion for the wedge:

> A design partner uses Resonantia to generate a worklist they would otherwise
> have built in spreadsheets, and they are willing to run it after review.

### Outreach Timing

Do not wait until Phase D to start design-partner outreach. The outreach should
start in stages:

| Stage | Timing | Purpose | Product Readiness |
| --- | --- | --- | --- |
| Discovery recruiting | Phase A | Find labs, understand workflows, collect real artifacts | Positioning and demo sufficient |
| Artifact collection | Phase A-B | Gather source plates, worklists, instrument formats, failure cases | No live product dependency |
| Shadow-mode validation | Phase B-C | Compare Resonantia-generated worklists against accepted human worklists | Validators and Run Builder needed |
| Workflow pilot | After Phase D | Run the full loop from worklist to result record/write-back | Result ingestion and audit trail needed |
| Live instrument execution | After repeated shadow-mode success | Let a partner run an approved Resonantia worklist | Instrument-specific validation and approvals required |

Recommendation:

> Start outreach now, but do not position it as a full production pilot until
> Phase D is complete.

The ask before Phase D should be: "show us how you build worklists today and let
us reproduce them in shadow mode." The ask after Phase D can become: "use
Resonantia for one real run with manual approval and compare it to your current
process."

## Reliability Evals

The first eval suite should focus on deterministic worklist correctness.

Required evals:

- valid plate dimensions for 96/384 formats
- valid well labels
- no duplicate destination wells unless explicitly allowed
- transfer volume within instrument range
- dead-volume check passes or blocks export
- concentration series is mathematically correct
- controls are present and placed according to policy
- replicate count matches request
- edge wells avoided when requested
- randomized layouts preserve constraints
- worklist CSV/GWL schema matches instrument target
- ambiguous user input asks a clarification question
- high-impact actions require manual approval before export
- approved worklist is reproducible from saved inputs

Priority fixtures:

- Echo cherry-pick
- Echo serial dilution
- Hamilton GWL cherry-pick
- 96-to-384 transfer
- multi-source plate transfer
- failed dead-volume case
- ambiguous controls case
- invalid concentration series case

## Manual Approval Model

Manual approval is part of the product, not a safety afterthought.

Approval cards for worklist export should show:

- instrument target
- source plate count
- destination plate format
- transfer count
- min/max transfer volume
- total volume by source plate
- dead-volume result
- control placement result
- replicate count result
- validation warnings
- export format
- user approving

Suggested approval title:

> Approve Echo worklist export

Suggested approval body:

> 384 transfers, 100 nL each. Echo volume range passed. Dead volume passed.
> Controls present. 3 replicates per compound. Edge wells avoided.

## Benchling / ELN Strategy

Benchling should be an ally, not the first competitor.

Resonantia should:

- pull entities, plates, compounds, and notebook context where available
- generate execution artifacts Benchling does not deeply own
- push run summaries, worklists, results, and approvals back to Benchling
- avoid rebuilding a full ELN experience for the initial wedge

Notebook remains useful as a local review/audit surface, but the design-partner
story is write-back to the customer's system of record.

## Implementation Plan

### Phase A: Positioning and Product Focus

Goal: make the app and docs describe Resonantia as a worklist execution layer.

- Update homepage and metadata from broad "agentic OS" language to execution
  layer language.
- Rename in-app "Plates" surface to "Run Builder" while keeping route
  compatibility.
- Reframe "Processing" as "Results Analysis".
- Reframe "Notebook" as "Run Records".
- Add a worklist-first demo script.
- Add design-partner intake checklist.

### Phase B: Worklist Reliability Core

Goal: make generated worklists measurably trustworthy.

- Add instrument profiles for Echo, Hamilton, and Opentrons.
- Add explicit worklist validators.
- Add deterministic fixtures for common transfer workflows.
- Snapshot export headers and rows.
- Add eval reports for valid/invalid plate maps.
- Fail closed on invalid or ambiguous worklist requests.

### Phase C: Run Builder UX

Goal: turn Plates into the primary execution workflow.

- Add "New Run" workflow:
  - choose instrument
  - choose transfer mode
  - upload source data
  - configure assay controls and replicates
  - validate
  - approve
  - export
- Add validation summary panel before export.
- Add run artifact history.
- Make manual approval cards instrument-specific.

### Phase D: Result Ingestion and Write-Back

Goal: close the operational loop.

- Ingest plate-reader output against a run/worklist.
- Link processing results back to the run artifact.
- Generate a structured run record.
- Export or push the record to an ELN/LIMS.
- Preserve immutable audit trail.

### Phase E: Instrument Partnership Path

Goal: become the software layer around real lab automation.

- Validate Echo CSV with design partners first.
- Add Hamilton GWL next if partner demand exists.
- Add Tecan/Automata integration only after CSV-based shadow mode works.
- Build partner demos around before/after spreadsheet time and error reduction.

## Near-Term Build Order

1. Update positioning and in-app labels.
2. Add worklist-focused demo and design-partner checklist.
3. Add Echo worklist validation fixtures.
4. Add instrument validation summary in the Run Builder.
5. Add approval-card details for worklist export.
6. Add run artifact persistence and audit view.
7. Add result ingestion linked to a run.
8. Add ELN/Benchling write-back target.

## Internal Product Principle

Every feature should answer at least one of these questions:

- Does it help create an executable worklist?
- Does it make that worklist safer or more correct?
- Does it reduce manual spreadsheet work?
- Does it make the run reproducible and auditable?
- Does it connect execution back to the customer's system of record?

If not, it is probably not part of the wedge.

## Feature Decision Checklist

Every new feature proposal should answer these questions before implementation.
If the answers are weak, defer the feature.

### Workflow Fit

- What exact liquid-handler or assay-execution workflow does this improve?
- Which user performs the step: scientist, automation engineer, lab manager, or
  data scientist?
- Is this before export, during approval, after execution, or during write-back?
- What existing manual spreadsheet, file conversion, or record-keeping step does
  it replace?

### Worklist Value

- Does it help create an executable worklist?
- Does it make that worklist safer, more correct, or easier to review?
- Does it validate an instrument-specific constraint?
- Does it reduce ambiguity before export?
- Does it prevent a real failure mode design partners have seen?

### Trust and Auditability

- What does the user need to approve?
- What artifact is saved for reproducibility?
- What parameters, source files, prompts, and tool calls must be logged?
- Can the run be regenerated from stored inputs?
- How would a scientist explain this decision six months later?

### System-of-Record Fit

- Does this belong in Resonantia, or should it be pushed to Benchling/ELN/LIMS?
- What object does it read from or write back to?
- What external identifier should be preserved?
- Is this a local review surface or a permanent source of truth?

### Eval Requirements

- What deterministic test fixture proves this works?
- What invalid input should fail closed?
- What ambiguity should trigger clarification?
- What acceptance threshold makes this design-partner-ready?
- Which regression test protects the exported artifact?

### Design-Partner Evidence

- Which partner asked for this?
- What file, screenshot, worklist, or failure case did they provide?
- How much time or risk does it remove?
- Would they use this in shadow mode within two weeks?
- Would they be disappointed if this feature did not exist?

### Feature Spec Template

Use this short template for implementation tickets:

```markdown
## Feature

## Workflow Step
Before export / approval / execution / result ingestion / write-back

## User

## Design-Partner Evidence

## Worklist or Run Artifact Impact

## Validation Rules

## Approval/Audit Requirements

## System-of-Record Touchpoint

## Evals and Fixtures

## Out of Scope
```
