# Resonantia — Strategic Positioning: Closed-Loop Lab OS

_Reference: [BVP Atlas — Building Biology-Native Data Infrastructure for the AI Era](https://www.bvp.com/atlas/building-biology-native-data-infrastructure-for-the-ai-era)_

---

## Executive Summary

Resonantia must evolve from a "lab informatics tool" (competing with Benchling on features) to a **closed-loop lab operating system** (competing on autonomous research cycles). The companies attracting top-tier VC investment in 2026 are not building better ELNs — they're building systems that autonomously design experiments, orchestrate execution, analyze results, and propose the next iteration.

Resonantia already has the building blocks (plate mapping, data processing, worklist generation, Temporal, voice). The missing piece is the **reasoning layer that closes the loop** between results and the next experiment.

This is not a pivot. It's an extension.

---

## BVP's Three Principles & Where Resonantia Fits

BVP identifies three interconnected layers defining next-generation biotech infrastructure:

### Principle 1: Biology-Native Data at Scale

**BVP thesis:** Competitive advantage demands multi-modal biological datasets. Public data (PDB, UniProt, ChEMBL) covers only early-stage discovery. Critical gaps exist in cellular phenotypes, patient-level omics, and ADME data.

**Resonantia's role:** Data **producer and organizer**, not data generator.

| What we produce | How it maps |
|----------------|-------------|
| Structured plate assay results (IC50, EC50, Z-prime) | Screening data with full metadata |
| Microscopy images with well/channel/FOV annotations | Phenomic imaging data |
| ELN entries linked to experiments + protocols | Contextualized experimental records |
| Sample inventory with barcode, lot, storage metadata | Material provenance data |

**Key move:** Ontology-map all data from day one (ChEBI, BAO, Gene Ontology, NCIT, UO). This makes Resonantia data interoperable with the biology-native data companies (Inductive Bio, NOETIK, Converge Bio) and positions us as a high-quality data source for the ecosystem.

### Principle 2: Agentic AI Across R&D Workflows

**BVP thesis:** Modular infrastructure that autonomously orchestrates best-in-class tools. AI operating systems spanning entire drug development processes. Autonomous AI scientists that design experiments, generate reports, and iterate.

**Resonantia's role:** This is our core layer. We have 32 agentic tools, multi-turn reasoning, voice interface, and tool chaining. But we're missing the **autonomous experiment design** capability.

| BVP example | What they do | Resonantia equivalent |
|-------------|-------------|----------------------|
| K-Dense | Autonomous AI scientist — plans, executes, iterates | Closest to our vision, but we're human-in-the-loop |
| Edison Scientific | Long-horizon research workflows | Our Temporal workflows (planned) |
| Phylo | Unified datasets + analytical pipelines + AI collaboration | Our direct inspiration / competitor |
| Potato | OS that autonomously designs and runs experiments | What we need to become |

**Key move:** Build the Experiment Design Agent that closes the loop (see below).

### Principle 3: Closed-Loop Lab Automation

**BVP thesis:** Connecting computational predictions to physical execution. Natural language interfaces for non-engineers. Vision-native systems interpreting microscopy autonomously.

**Resonantia's role:** We handle the **software orchestration** side; hardware partners (Automata, Hamilton) handle physical execution.

| BVP example | What they do | Resonantia relationship |
|-------------|-------------|------------------------|
| Automata | LINQ — instrument-agnostic robotic platform | Integration partner (planned) |
| Medra | Instrument-agnostic robotics | Potential second hardware partner |
| Lila Sciences | Vertically integrated automated lab | Competitor if they build software layer |
| Dash Bio | Automated CRO | Potential customer (our software, their robots) |

**Key move:** Automata LINQ integration with bidirectional data flow — not just worklist push, but result pull + feedback into next experiment design.

---

## The Closed Loop: What We're Building

### Current State (Open Loop)
```
Scientist asks → Agent helps → Scientist decides → Scientist acts
                                    ↓
                              Manual handoff
                              to next experiment
```

### Target State (Closed Loop)
```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│   │  DESIGN  │───▶│ EXECUTE  │───▶│ ANALYZE  │         │
│   │          │    │          │    │          │         │
│   │ Experiment│    │ Plate Map│    │ IC50     │         │
│   │ Design   │    │ Worklist │    │ Z-prime  │         │
│   │ Agent    │    │ → LINQ / │    │ Normalize│         │
│   │          │    │ Hamilton │    │ qPCR     │         │
│   └────▲─────┘    └──────────┘    └────┬─────┘         │
│        │                               │               │
│        │         FEEDBACK LOOP         │               │
│        │                               │               │
│   ┌────┴─────┐                    ┌────▼─────┐         │
│   │ RECOMMEND│◀───────────────────│ EVALUATE │         │
│   │          │                    │          │         │
│   │ Next     │                    │ Hit rate │         │
│   │ compounds│                    │ SAR gaps │         │
│   │ Conc.    │                    │ QC flags │         │
│   │ Controls │                    │ Outliers │         │
│   └──────────┘                    └──────────┘         │
│                                                          │
│   Human-in-the-loop: scientist approves/modifies at     │
│   any step. Full autonomy is opt-in, not default.       │
└──────────────────────────────────────────────────────────┘
```

### Human-in-the-Loop vs. Full Autonomy

BVP highlights fully autonomous systems (K-Dense, Potato). We should take a **graduated autonomy** approach:

| Level | Description | When |
|-------|-------------|------|
| **Level 1: Assist** | Agent answers questions, runs tools on request | Current state |
| **Level 2: Suggest** | Agent analyzes results and proposes next experiment | Experiment Design Agent (next build) |
| **Level 3: Draft** | Agent designs full plate map + worklist, scientist approves | Post-seed |
| **Level 4: Autopilot** | Agent runs full design-execute-analyze cycles, scientist monitors | Enterprise tier, opt-in |

This is safer for regulated environments and more palatable to scientists who don't trust full autonomy yet. It also builds the training data we need for Level 4.

---

## New Features Required (Prioritized)

### 1. Experiment Design Agent — The Loop Closer

**What it does:**
1. Ingests previous experiment results (IC50 curves, Z-prime, hit rates, SAR data)
2. Identifies gaps: untested concentration ranges, missing controls, compounds with ambiguous activity
3. Proposes next experiment: which compounds, what concentrations, which plate layout, what controls
4. Generates the plate map and worklist automatically
5. Scientist reviews and approves (or modifies) before execution

**Technical approach:**
- New agentic tool: `design_next_experiment`
- Chains existing tools: `query_experiments` → `fit_dose_response` → `create_plate_map` → `generate_worklist`
- System prompt with experiment design heuristics:
  - Follow-up hits with tighter concentration ranges
  - Always include positive/negative controls
  - Expand SAR around active scaffolds
  - Flag compounds with steep Hill slopes for re-testing
- Eventually: ML model trained on historical experiment outcomes (proprietary model opportunity)

**Effort:** 4-6 weeks (agentic tool + reasoning chain + UI for review/approve)

**Impact:** Transforms Resonantia from "tool" to "autonomous research partner." This is the single feature that changes the investor narrative.

### 2. Temporal Multi-Day Experiment Workflows

**What it does:**
- Orchestrates multi-step experiments spanning days/weeks:
  - Day 1: Seed cells → wait 24h
  - Day 2: Add compounds (worklist from Design Agent) → wait 48h
  - Day 4: Read plates (trigger instrument or manual step)
  - Day 4: Analyze results (automatic)
  - Day 4: Design follow-up (automatic, pending approval)
- Handles delays, retries, human checkpoints
- Full execution history and audit trail

**Technical approach:**
- Temporal workflow definitions for common experiment types:
  - `DoseResponseScreenWorkflow`
  - `HitConfirmationWorkflow`
  - `SARFollowUpWorkflow`
  - `CounterScreenWorkflow`
- Each step is a Temporal activity that calls existing services
- Human-in-the-loop via Temporal signals (approve/reject/modify)
- Dashboard showing active workflows, pending approvals, timeline

**Effort:** 3-4 weeks (Temporal infra exists, need workflow definitions + approval UI)

**Impact:** No other lab informatics tool has durable, multi-day workflow orchestration. This is a genuine technical moat.

### 3. Ontology-Mapped Data Model

**What it does:**
- All entities tagged with standard ontology identifiers:
  - Compounds → ChEBI IDs
  - Assays → BAO (BioAssay Ontology) terms
  - Genes/targets → Gene Ontology + UniProt IDs
  - Cell lines → Cellosaurus IDs
  - Units → UO (Units Ontology)
  - Diseases → NCIT (NCI Thesaurus) or MONDO
- Enables cross-lab data interoperability
- Powers smarter experiment design ("find all IC50 data for EGFR inhibitors across our org")

**Technical approach:**
- Add `ontology_id` and `ontology_source` columns to relevant models
- Build ontology lookup service (cache ChEBI, BAO locally or via API)
- Agent tool: `map_to_ontology` — auto-suggests ontology terms for new entities
- Validate on data entry: "This compound maps to ChEBI:28748 (aspirin). Confirm?"

**Effort:** 3-4 weeks for initial mapping + lookup service

**Impact:** BVP explicitly flags "contextualization deficit" as a critical gap. Ontology-mapped data from day one makes Resonantia a high-quality data source for the entire ecosystem.

### 4. Resonantia MCP Server

**What it does:**
- Exposes Resonantia's 32 tools as an MCP server
- Any MCP-compatible client (Claude, Automata LINQ, other AI systems) can query Resonantia data and trigger actions
- Enables ecosystem integration without point-to-point connectors

**Why now:**
- Benchling has "first-class MCP integrations"
- Automata LINQ has MCP connectivity
- Anthropic is building Claude connectors for Benchling, PubMed, ChEMBL
- MCP is the integration standard for 2026 — not having it is like not having a REST API in 2015

**Technical approach:**
- Implement MCP server spec over existing FastAPI endpoints
- Expose tool registry as MCP tool definitions
- Authentication via API keys (per-org)

**Effort:** 2-3 weeks

**Impact:** Makes Resonantia a first-class citizen in the AI tooling ecosystem. Required for Automata partnership.

### 5. Proprietary Models Strategy

**Not building foundation models.** Resonantia is an orchestration company, not a model company. But we will build domain-specific models where they create defensible advantage:

| Model | Type | When | Why |
|-------|------|------|-----|
| **Lab ASR** | Fine-tuned Whisper | Month 6-9 | Accurate transcription of "IC50", "DMSO", "A7", "qPCR". Collect training data from design partners. |
| **Experiment Design ML** | Active learning / recommendation | Month 12-18 | Learns from historical experiment outcomes across customers. "Labs that tested X with Y parameters got better results." Proprietary dataset compounds with every customer. |
| **Plate QC Vision** | Fine-tuned vision model | Month 18+ | Detect plate edge effects, contamination, precipitation from plate images. Only if customer demand validates. |

The **Experiment Design ML model** is the long-term proprietary moat. It gets better with every experiment run through Resonantia, creating a data flywheel competitors can't replicate.

---

## Competitive Repositioning

### Old Positioning
> "Resonantia is an AI-powered lab informatics platform — a modern alternative to Benchling with natural language, voice, and agentic tools."

**Problem:** Competes on features with a $6.1B incumbent. Tool story, not platform story.

### New Positioning
> "Resonantia is the agentic operating system that closes the loop between computational experiment design and wet lab execution. We autonomously analyze results, design follow-up experiments, generate worklists, orchestrate automation, and feed insights back into the next cycle — compressing research timelines from months to days."

**Why this works:**
1. Aligns with BVP's three principles (data + agents + automation)
2. Differentiates from Benchling (they're a system of record; we're a system of action)
3. Positions the Automata partnership as core, not add-on
4. Justifies premium pricing (we're not selling ELN access; we're selling faster drug discovery)
5. Creates a proprietary data flywheel (experiment design model)

### Positioning by Audience

| Audience | Message |
|----------|---------|
| **Scientists** | "Tell Resonantia what you want to test. It designs the experiment, generates the worklist, and analyzes the results — so you can focus on the science." |
| **Lab managers** | "One platform connecting your instruments, data, and team. Automated QC, real-time dashboards, audit-ready documentation." |
| **VPs of R&D** | "Compress your design-make-test-analyze cycle from weeks to days. Resonantia orchestrates the full loop, from hypothesis to plate to insight." |
| **Investors (BVP-style)** | "We're building the agentic infrastructure layer for closed-loop lab automation. Ontology-mapped data, autonomous experiment design, Temporal workflows, and hardware integrations create a compounding data moat." |

---

## Updated Market Map Position

```
BVP's Three Layers:

┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: Biology-Native Data                                │
│                                                             │
│ Peptone  Inductive Bio  NOETIK  Converge Bio  Prima Mente  │
│                          ▲                                  │
│                          │ Ontology-mapped data feeds up    │
├──────────────────────────┼──────────────────────────────────┤
│ LAYER 2: Agentic AI Workflows                               │
│                          │                                  │
│ K-Dense  Edison  Phylo   │  ★ RESONANTIA ★   Convoke       │
│                          │                                  │
│                          │ Worklists + results flow down    │
├──────────────────────────┼──────────────────────────────────┤
│ LAYER 3: Closed-Loop Lab Automation                         │
│                          ▼                                  │
│ Automata (LINQ)    Medra    Lila Sciences    Dash Bio       │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Resonantia is the BRIDGE between Layer 2 and Layer 3,
with data flowing up to Layer 1.
```

---

## What This Means for the Roadmap

### Reprioritized Feature Order

```
MONTH 1-3:   Billing → SSO/RBAC → Audit trail → Data export
MONTH 3-6:   Experiment Design Agent → Resonantia MCP → Benchling import
MONTH 6-9:   Automata LINQ integration (bidirectional) → Temporal workflows
             → Ontology mapping → GenAI CI/CD + evals
MONTH 9-12:  Lab ASR fine-tuning → SDK → Dashboards + Notifications
MONTH 12-18: Experiment Design ML model → Self-hosted vLLM → Collaboration
MONTH 18+:   Plate QC Vision model → Electron offline (only if validated)
```

### Key Change from Previous Roadmap
The **Experiment Design Agent** moves from "not on the roadmap" to **Month 3-6 priority**. This is the single feature that transforms the investor narrative and aligns with where the market is going.

**Dashboards and Notifications** move later (Month 9-12). They're important for PIs but don't change the strategic positioning. The closed loop matters more.

---

## Success Metrics

| Metric | Target | Why it matters |
|--------|--------|---------------|
| Experiments with agent-designed follow-ups | 30% of all experiments by Month 12 | Proves the loop is closing |
| Time from results → next experiment design | <1 hour (vs. days manually) | Core value prop quantified |
| Ontology coverage | 80% of entities mapped by Month 9 | Data quality for ecosystem play |
| LINQ integration experiments | 10+ closed-loop runs by Month 9 | Partnership validated |
| Proprietary experiment data | 10,000+ experiment records by Month 18 | Training data for ML model |

---

## Appendix: BVP Company Comparisons

### Companies BVP Highlights That Overlap With Resonantia

**Phylo (Most Direct Competitor)**
- Integrated Biology Environment
- AI agent collaboration over unified datasets
- BVP portfolio company
- Resonantia was explicitly modeled after Phylo
- Differentiation: Resonantia adds plate mapping, worklist generation, voice mode, closed-loop automation integration

**K-Dense (Aspirational Target)**
- Fully autonomous AI scientist
- Plans, executes, iterates end-to-end
- More autonomous than Resonantia (today)
- Our Level 4 autonomy is where K-Dense starts

**Anthropic (Enabler, Not Competitor)**
- Building Claude connectors for Benchling, PubMed, ChEMBL
- Our LLM provider
- MCP ecosystem alignment — Resonantia as MCP server fits their vision

**Automata (Partner)**
- Explicitly named in BVP's Layer 3
- LINQ platform = our physical execution partner
- Joint closed-loop demo is the most fundable story we can tell
