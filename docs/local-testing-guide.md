# Resonantia — Local Testing Guide

Every workflow is accessible three ways: **Direct UI** (click through the module page), **Chat** (type a prompt), and **Voice** (hold Space and speak). This guide tests all three for every feature.

---

## Setup

```bash
# 1. Start infrastructure
docker compose up -d postgres redis temporal temporal-postgres temporal-ui

# 2. Start backend
cd backend
cp ../.env .env  # needs OPENAI_API_KEY at minimum
uv sync
uv run uvicorn resonantia.main:app --reload --port 8000

# 3. Start frontend (use 3001 if Docker is on 3000)
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev -- --port 3001

# 4. Verify
curl http://localhost:8000/health  # {"status": "ok"}
open http://localhost:3001
```

**Required:** `OPENAI_API_KEY`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`
**Optional:** `ANTHROPIC_API_KEY` (set `DEFAULT_PROVIDER=anthropic`), `LANGFUSE_*` keys

---

## Interaction Modes

Every test below can be run three ways. Voice-blocked actions (creates, submits, exports) redirect to chat for text confirmation — the agent drafts the action but the user must click Confirm.

| Mode | How | When to use |
|------|-----|-------------|
| **Direct UI** | Navigate to module page, click buttons | Browsing, bulk editing, visual layout work |
| **Chat** | Type prompt in `/lab` console | Precise instructions, multi-step workflows |
| **Voice** | Hold Space → speak → release | Hands-free at the bench, lookups, dictation |

---

## 1. Sample & Reagent Inventory

### Lookup

| Path | Action |
|------|--------|
| **UI** | `/lab/samples` → type "DMEM" in search box |
| **Chat** | "Look up sample DMEM" |
| **Voice** | Hold Space: "Look up sample DMEM" |

**Expected:** Table/response shows matching samples with barcode, location, quantity, expiry.

### Expiry Triage

| Path | Action |
|------|--------|
| **UI** | `/lab/samples` → look for orange/red expiry indicators |
| **Chat** | "What reagents are expiring in the next 30 days?" |
| **Voice** | Hold Space: "What's expiring soon?" |

**Expected:** List of samples with days until expiry, status (ok / expiring_soon / expired).

### Check Stock

| Path | Action |
|------|--------|
| **UI** | `/lab/samples` → filter by type, check quantity column |
| **Chat** | "Check inventory for Protease Inhibitor Cocktail" |
| **Voice** | Hold Space: "Do we have protease inhibitor in stock?" |

**Expected:** Quantity, unit, location, lot number, expiry status.

### Add Sample (voice-blocked)

| Path | Action |
|------|--------|
| **UI** | `/lab/samples` → click + → fill form → save |
| **Chat** | "Add a new sample: RPMI-1640, reagent, 500 mL, Freezer B shelf 3" |
| **Voice** | Hold Space: "Add a new reagent RPMI" → **redirected to chat for confirmation** |

**Expected:** UI/Chat: sample created. Voice: agent drafts, says "confirm in chat."

---

## 2. Plate Mapping

### View & Select Wells

| Path | Action |
|------|--------|
| **UI** | `/lab/plates` → click wells on grid to select |
| **Chat** | "Show me plate map HTS Screen Round 1" |
| **Voice** | Hold Space: "What plate maps do we have?" |

**Expected:** Color-coded well grid (blue=sample, green=positive control, red=negative control).

### Cherry-Pick (voice-blocked)

| Path | Action |
|------|--------|
| **UI** | `/lab/plates` → select Cherry Pick mode → select source wells → apply |
| **Chat** | "Cherry-pick wells A2, A3, B2 from source plate into a 384-well confirmation plate" |
| **Voice** | Hold Space: "Cherry-pick the top 3 hits" → **redirected to chat** → approval card with plate preview → Confirm |

**Expected:** New plate map with selected wells mapped to destination. Approval card shows visual preview.

### Serial Dilution (voice-blocked)

| Path | Action |
|------|--------|
| **UI** | `/lab/plates` → select Serial Dilution mode → set fold=3, steps=8 → apply |
| **Chat** | "Design a serial dilution starting at A1, 8 points, 3-fold, horizontal" |
| **Voice** | Hold Space: "Set up an 8-point 3-fold dilution" → **redirected to chat** → Confirm |

**Expected:** Wells filled with decreasing concentrations (1, 0.33, 0.11, 0.037, ...).

### Worklist Export (voice-blocked, hard approval)

| Path | Action |
|------|--------|
| **UI** | `/lab/plates` → click Export Worklist → select Echo/Hamilton/OT-2 → download |
| **Chat** | "Generate an Echo worklist for plate map HTS Screen Round 1" |
| **Voice** | Hold Space: "Generate a worklist for the Echo" → **redirected to chat** → amber warning + approval card → Confirm → download |

**Expected:** CSV (Echo), GWL (Hamilton), or Python (OT-2) file with transfer volumes and well mappings.

---

## 3. Data Processing

### Dose-Response Curve Fitting

| Path | Action |
|------|--------|
| **UI** | `/lab/processing` → paste concentration/response data → click Fit |
| **Chat** | "Fit a dose-response curve for concentrations [0.1, 1, 10, 100, 1000] and responses [95, 88, 62, 25, 8]" |
| **Voice** | Hold Space: "Fit a dose-response curve for staurosporine" (needs data context) |

**Expected:** IC50, Hill slope, R², Z' (if controls provided). Inline plot with sigmoidal curve.

### Plate Normalization

| Path | Action |
|------|--------|
| **UI** | `/lab/processing` → enter raw data → select Z-score method → normalize |
| **Chat** | "Normalize this plate data using Z-score: [45, 52, 48, 95, 92, 88, 5, 3, 7]" |
| **Voice** | Hold Space: "Normalize my plate data using Z-score" (needs data in context) |

**Expected:** Normalized values with method used and data count.

### Z-Prime Calculation

| Path | Action |
|------|--------|
| **UI** | `/lab/processing` → enter positive/negative control values → calculate |
| **Chat** | "Calculate Z-prime with positive controls [100, 98, 102] and negative controls [5, 3, 7]" |
| **Voice** | Hold Space: "What's the Z-prime for my latest plate?" |

**Expected:** Z' value with quality assessment (>0.5 = good assay, <0.5 = poor).

### qPCR Delta-Delta Ct

| Path | Action |
|------|--------|
| **UI** | `/lab/processing` → enter Ct values → calculate |
| **Chat** | "Run qPCR analysis: target Ct [25.3, 25.1], reference Ct [18.2, 18.5], control target Ct [28.1, 27.9], control reference Ct [18.3, 18.1]" |
| **Voice** | Hold Space: "Analyze my qPCR data" (needs Ct values in context) |

**Expected:** Delta-delta Ct and fold-change values.

---

## 4. ELN Notebook

### Search Entries

| Path | Action |
|------|--------|
| **UI** | `/lab/eln` → browse list of entries |
| **Chat** | "Search ELN entries about staurosporine" |
| **Voice** | Hold Space: "Find my staurosporine ELN entries" |

**Expected:** List of matching entries with title, entry number, status, date.

### Create Entry (voice-blocked)

| Path | Action |
|------|--------|
| **UI** | `/lab/eln` → click + → type title and markdown content → save |
| **Chat** | "Create an ELN entry titled 'Staurosporine IC50 Determination'" |
| **Voice** | Hold Space: "Create a notebook entry for staurosporine" → **redirected to chat** → approval card with markdown preview → Confirm |

**Expected:** New entry with auto-generated entry number (ELN-2026-XXXX), status: draft.

### Auto-Generate from Experiment (voice-blocked)

| Path | Action |
|------|--------|
| **UI** | `/lab/eln` → click Auto-Generate → select experiment |
| **Chat** | "Create an ELN entry for experiment EXP-001" |
| **Voice** | Hold Space: "Draft a notebook entry from my latest experiment" → **redirected to chat** |

**Expected:** Structured entry with Objective, Methods, Results (IC50, Hill, R², Z'), Conclusions, References.

### Submit Entry (voice-blocked, hard approval)

| Path | Action |
|------|--------|
| **UI** | `/lab/eln` → click Submit on a draft entry |
| **Chat** | "Submit ELN entry ELN-2026-001" |
| **Voice** | Hold Space: "Submit my ELN entry" → **redirected to chat** → approval card with warning → Confirm |

**Expected:** Status changes to "submitted" (immutable — cannot be edited after submission).

### Export

| Path | Action |
|------|--------|
| **UI** | `/lab/eln` → click PDF or Markdown export button |
| **Chat** | "Export ELN entry ELN-2026-001 as PDF" |

**Expected:** PDF or Markdown file downloads.

---

## 5. Protocol Builder

### Search Protocols

| Path | Action |
|------|--------|
| **UI** | `/lab/protocols` → browse list |
| **Chat** | "Search protocols about Western Blot" |
| **Voice** | Hold Space: "What protocols do we have for Western Blot?" |

**Expected:** List of matching protocols with name, version, status.

### Create Protocol (voice-blocked)

| Path | Action |
|------|--------|
| **UI** | `/lab/protocols` → click + → add steps with reagents |
| **Chat** | "Create a protocol for CellTiter-Glo viability assay" |
| **Voice** | Hold Space: "Create a cell viability protocol" → **redirected to chat** → Confirm |

**Expected:** Protocol with numbered steps, reagent requirements, durations.

### Inventory Pre-Flight Check

| Path | Action |
|------|--------|
| **UI** | `/lab/protocols` → click Check Inventory on a protocol |
| **Chat** | "Check if we have all reagents for the Western Blot protocol" |
| **Voice** | Hold Space: "Do we have everything for the Western Blot?" |

**Expected:** List of required reagents with availability status (available/missing/low stock).

### Dilution Calculator

| Path | Action |
|------|--------|
| **UI** | `/lab/protocols` → enter stock/target/volume → calculate |
| **Chat** | "Calculate dilution: stock 10 mM, target 100 µM, volume 500 µL" |
| **Voice** | Hold Space: "Calculate dilution from 10 millimolar to 100 micromolar in 500 microliters" |

**Expected:** Stock volume (5 µL) and diluent volume (495 µL) with C1V1=C2V2 formula.

---

## 6. Killer Workflow — End-to-End

The core demo flow. Tests all modules working together via chat. Use `demo-data/dose_response_staurosporine_HEK293T.csv`.

See `docs/killer-workflow-demo.md` for the full script. Summary:

| Step | Prompt | Expected | Approval? |
|------|--------|----------|-----------|
| 1. Upload | "Analyze this plate reader export" + attach CSV | Column preview, 240 rows detected | No |
| 2. Fit | "Fit dose-response curves for all compounds" | IC50 ~42 nM for staurosporine, inline plot | No |
| 3. ELN draft | "Create an ELN entry summarizing these results" | Structured markdown draft | Yes (L2) |
| 4. Plate | "Cherry-pick the top 3 hits into a confirmation plate" | Visual plate grid preview | Yes (L2) |
| 5. Follow-up | "What experiments should we run next?" | 2-3 options with scientific rationale | Yes (L2) |
| 6. Worklist | "Generate an Echo worklist for the confirmation plate" | Preview + amber warning | Yes (L3) |

---

## 7. Voice-Specific Tests

These test the voice pipeline itself, separate from the workflows above.

| Test | Action | Expected |
|------|--------|----------|
| Push-to-talk | Hold Space → speak → release | Recording indicator, transcription in chat, agent responds, TTS plays |
| VAD mode | Click mic icon → speak → pause 2s | Auto-stops recording on silence |
| Safe tool via voice | Hold Space: "Look up sample DMEM" | Tool executes, spoken response |
| Blocked tool via voice | Hold Space: "Submit the ELN entry" | "This requires text confirmation" |
| Voice dictation to ELN | Hold Space: "Record observation: cells at 80% confluence, passage 12, morphology normal" | Draft ELN entry created (must confirm in chat) |

---

## Use Cases from /use-cases Page

### Ready — test via all 3 paths

| Code | Use Case | Chat Prompt | Voice Prompt | UI Path |
|------|----------|-------------|-------------|---------|
| DAT/01 | Dose-response → IC50 → ELN | Upload CSV → "Fit curves" → "Draft ELN" | "Fit dose-response for staurosporine" (lookup only via voice) | `/lab/processing` |
| PLT/01 | Cherry-pick hits to 384-well | "Cherry-pick wells A2, A3, B2 into 384-well" | "Cherry-pick the top hits" (→ confirm in chat) | `/lab/plates` → Cherry Pick mode |
| PLT/02 | Serial dilution layout | "Serial dilution, A1, 8 points, 3-fold" | "Set up a serial dilution" (→ confirm in chat) | `/lab/plates` → Serial Dilution mode |
| INV/01 | Reagent expiry triage | "What reagents expire within 30 days?" | "What's expiring soon?" | `/lab/samples` → check expiry column |
| PRO/01 | Protocol pre-flight + dilution | "Check reagents for Western Blot" then "Dilution 10mM → 100µM in 500µL" | "Do we have everything for the Western Blot?" | `/lab/protocols` → Check Inventory |
| DAT/02 | Plate normalization | "Normalize using Z-score: [45,52,48,95,92,88,5,3,7]" | "Normalize my plate data" | `/lab/processing` |
| DAT/03 | qPCR ΔΔCt | "Run qPCR: target Ct [25.3,25.1], ref [18.2,18.5], ctrl target [28.1,27.9], ctrl ref [18.3,18.1]" | "Analyze my qPCR data" | `/lab/processing` |
| SAM/01 | Hands-free sample lookup | "Look up sample DMEM" | "Look up sample DMEM" | `/lab/samples` → search |
| WL/01 | Worklist export | "Generate Echo worklist for PM-demo-1" | "Generate a worklist" (→ confirm in chat) | `/lab/plates` → Export |
| ELN/01 | ELN from artifacts | "Create ELN entry for experiment EXP-001" | "Draft a notebook entry" (→ confirm in chat) | `/lab/eln` → Auto-Generate |
| VOC/01 | Voice → ELN capture | N/A (voice-first workflow) | "Record: HEK293T viability, staurosporine 10-point, CellTiter-Glo" | N/A |

### Preview — not fully functional

| Code | Use Case | Status | What works |
|------|----------|--------|------------|
| MIC/01 | Microscopy run triage | Gated | Page at `/lab/microscopy` shows synthetic demo data. Tools disabled. |
| BNL/01 | Benchling write-back | Stub | Settings shows "Coming Soon". No functional API. |
| PLN/01 | Closed-loop campaign | Partial | Agent proposes follow-up experiments. Full multi-step Plan Mode not built. |

---

## Automated Tests

```bash
# All backend tests (~400)
cd backend && uv run pytest tests/ -v

# Specific suites
uv run pytest tests/test_killer_workflow_e2e.py -v    # Killer workflow (15 tests)
uv run pytest tests/test_tenant_isolation.py -v        # Tenant security (9 tests)
uv run pytest tests/test_approval.py -v                # Approval gates (16 tests)
uv run pytest tests/test_voice_safety.py -v            # Voice safety (12 tests)
uv run pytest tests/test_llm_provider.py -v            # Provider abstraction (22 tests)
uv run pytest tests/test_output_validator.py -v        # Output guardrails (32 tests)
uv run pytest tests/test_a2a.py -v                     # A2A protocol (26 tests)
uv run pytest tests/test_multi_agent.py -v             # Multi-agent (36 tests)

# All frontend tests (53)
cd frontend && npx vitest run
```

---

## Demo Mode vs Live Mode

| Mode | Activate | Behavior |
|------|----------|----------|
| **Demo** | `NEXT_PUBLIC_DEMO_MODE=true` | Amber banner, seeded data, local persistence only |
| **Live** | Backend running, no demo flag | Data persists to PostgreSQL, errors shown as toasts |
| **Degraded** | Backend down, no demo flag | Error toasts on every write, no silent fallback |

---

## Common Issues

| Issue | Fix |
|-------|-----|
| "OpenAI API key not configured" | Add `OPENAI_API_KEY` to `.env` |
| Chat returns empty | Start backend on :8000 |
| Port 3000 in use | Use `--port 3001` for frontend dev |
| Voice not working | Allow microphone permission in browser |
| No demo data | Set `NEXT_PUBLIC_DEMO_MODE=true` or seed DB |
| Approval card not showing | Ensure P1.0 approval service is in the backend code |
