# Resonantia — Feature Decommission & Shrink List

**Date:** 2026-05-01
**Author:** scoped from `agentic-architecture.md`, `subagents-acp-plan.md`, `production-plan.md`, the live codebase, and the project `CLAUDE.md`.
**Audience:** founders + roadmap.

> The thesis is **agentic co-scientist** — Plan Mode, multi-agent topology, lab memory. Anything that does not feed that thesis (or the substrate it acts on) is a candidate to shrink, defer, or remove.
> Calibration constraint: `CLAUDE.md` requires microscopy and source-destination plate mapping as substrate. Those stay; what ships *around* them is what's up for review.

---

## Scoring

Each feature is scored 1–5 on three axes:

- **Differentiation** — how much it expresses the agent thesis (5 = unique to Resonantia, 1 = generic SaaS).
- **Implementation health** — how real it is today (5 = persisted, tested, in production-shape; 1 = mocked or local-only).
- **Competitive density** — how owned the space already is (5 = big incumbents, 1 = unowned).

Verdicts:

- **KEEP** — the agent thesis (or substrate) needs it.
- **SHRINK** — exists but scope is too wide; cut to the part the agent uses.
- **DEFER** — punt until a design partner asks; don't invest now.
- **DECOMMISSION** — remove from the codebase.

---

## Inventory & verdicts

| Feature | Diff | Health | Density | Verdict | Note |
|---|---|---|---|---|---|
| Agentic chat | 5 | 4 | 3 | **KEEP** | Core surface. The multi-agent rewrite (PR2) replaces the single-agent loop. |
| Plan Mode (planner + critic + approval gates) | 5 | 0 | 1 | **BUILD** | Not yet implemented. Highest-leverage feature per `agentic-architecture.md` §1. |
| Lab memory (semantic + episodic + working) | 5 | 0 | 2 | **BUILD** | Not yet implemented. Highest-leverage moat per §4. |
| Plate mapper (source→destination, cherry-pick, dilution) | 4 | 4 | 5 | **KEEP** | Substrate, explicit `CLAUDE.md` ask, real implementation + tests. |
| Worklist generator (Echo / Hamilton CSV) | 4 | 4 | 4 | **KEEP** | Substrate; ties the agent to instruments. |
| Data processing (4PL, Z′, qPCR, normalization) | 3 | 4 | 5 | **KEEP** | Substrate for the analyst agent. Don't try to be a stats product; be a stats *caller*. |
| Sample / inventory CRUD | 3 | 4 | 5 | **KEEP** | Substrate (lab-memory seed). |
| Microscopy data + viewer | 3 | 1 | 5 | **SHRINK** | Substrate per `CLAUDE.md` — keep the data model, image storage, and metadata API. **Cut** the synthetic canvas demo and the feature-complete viewer. The Scope-Scout agent reasons over metadata; we don't ship a Slidebook competitor. |
| ELN editor | 2 | 3 | 5 | **SHRINK** | Crowded (Benchling, eLabFTW, Dotmatics own it). Keep the **agent-drafted ELN entry** flow (Notebook Scribe writes, user reviews); **cut** rich-text authoring features that ape Benchling. Long-term path: write-back into the customer's existing ELN, not compete. |
| Protocol builder (visual step UI) | 2 | 2 | 5 | **SHRINK** | Visual step-by-step authoring is low-ROI versus Opentrons/Hamilton/Benchling protocols. Keep dilution calculator + inventory checker (agent uses them). Cut the editor UI; let protocols be code (or imported). |
| Voice mode | 3 | 4 | 4 | **SHRINK + REFRAME** | `agentic-architecture.md` §6 is explicit: voice = lookup + dictation, **not** universal command. The pipeline works; the surface needs to be reframed (push-to-talk, hands-free wake word for narrow phrases, no autonomous voice-driven actions). Hard rule: voice **never** triggers a non-reversible action without a visible approval card. |
| eLabFTW integration | 2 | 1 | 4 | **DEFER** | Half-wired (env-only settings, no persistence). Don't kill the code yet — it's the integration shell we'll reuse. **Defer** building the rest until a design partner asks. Benchling has 10× the install base; if we have to integrate, integrate there first. |
| Onboarding flow (separate page) | 2 | 3 | 4 | **SHRINK** | Mostly fine; trim copy, fold into a single first-run step inside the lab shell rather than a separate route. |
| Feature-request page | 1 | 2 | 1 | **DEFER** | Not part of the thesis. Cheap to keep but cheaper to defer until you actually have users to feature-request. |
| Marketing site (about, blog, pricing) | 2 | 4 | 1 | **KEEP** | Required for design-partner conversations; already built. Maintenance only. |

---

## Build queue (added by this audit)

These are not in the codebase yet and are higher priority than anything below:

1. **Plan Mode** (`agentic-architecture.md` §1) — Plan/Step Pydantic objects, planner agent, critic, approval gates as Temporal Signals, plan card UI.
2. **Multi-agent topology** (`subagents-acp-plan.md` Phase 1) — orchestrator + 4 specialists (data analyst, plate designer, ELN scribe, experiment designer) + critic. Implemented in PR2.
3. **Lab memory** (`agentic-architecture.md` §4) — `lab_facts` table, memory extractor, settings UI to view/edit facts.
4. **Multimodal chat** — image + file inputs to the agent (Claude vision). Implemented in PR3.
5. **Voice hands-free narrow scope** — push-to-talk, wake-word, dictation-only. Implemented in PR4.

---

## Specific cuts (PR follow-ups)

### Microscopy SHRINK

**Cut:**
- `frontend/src/lib/microscopy-demo.ts` — synthetic canvas image generator. Real images come from upload + S3.
- Demo seed images bundled in `frontend/public/`.
- Any "browse all images in a fancy lightbox" affordance beyond what the agent (Scope Scout) needs to point at.

**Keep:**
- `backend/.../api/microscopy.py` (real API + storage).
- `frontend/.../microscopy-viewer.tsx` reduced to a thumbnail strip + single-image inspector. No FOV browser, no annotation toolbox.
- The `browse_microscopy` agent tool.

### Protocol builder SHRINK

**Cut:**
- `frontend/.../protocol-step-builder.tsx`.
- Backend create/update endpoints for protocols if they exist.

**Keep:**
- `frontend/.../dilution-calculator.tsx` — high-utility, agent-callable.
- `frontend/.../inventory-checker.tsx` — substrate.
- Read-only protocol list + agent-callable tools (`query_protocols`, `get_protocol`).

### ELN SHRINK

**Cut:**
- Any rich-text formatting features beyond what the agent emits (markdown is enough).
- "Compete with Benchling" energy in the UI copy.

**Keep:**
- Agent-drafted entry flow (Notebook Scribe → user approval gate → submit).
- Audit log and submission semantics — these are the parts a regulated lab cares about.

### Voice REFRAME

**Cut:**
- Any UI affordance suggesting voice can execute a write (e.g., "Send to Echo" button reachable from voice mode).

**Keep / change:**
- Push-to-talk and short-phrase wake-word for hands-free *lookup* and *dictation*.
- Voice transcription always lands as text in the chat thread (durable transcript).
- Any voice-initiated action passes through the same approval card any chat-initiated action would.

---

## Out of scope (deliberate non-cuts)

- **Temporal substrate.** Even if currently underused, it's the correct foundation for Plan Mode. Don't rip it out.
- **Tool registry / MCP server.** Substrate for ACP later (per `subagents-acp-plan.md`). Don't rip out.
- **Langfuse / RAGAS evals.** These are the eval surface §7 needs.

---

## What this saves

Rough scope of removed/shrunk code:

- Microscopy demo + viewer trim: ~700 LOC removed.
- Protocol-builder UI removal: ~400 LOC removed.
- ELN trim: ~150 LOC removed.
- Voice reframe: ~50 LOC edited (mostly copy + button hide).

Net engineering time recovered, conservatively: **2–3 weeks** that pays directly into Plan Mode + multi-agent + memory.

---

## Decision log this doc commits to

1. We do **not** compete with Benchling on rich-text ELN.
2. We do **not** compete with HCS-software incumbents on microscopy viewing.
3. We do **not** ship a visual protocol-builder.
4. Voice is **lookup + dictation**, never command.
5. Plan Mode + multi-agent + lab memory are the next three big things, in that order.
