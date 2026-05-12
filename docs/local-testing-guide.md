# Resonantia — Local Testing Guide

Every workflow is accessible three ways: **Direct UI** (click through the module page), **Chat** (type a prompt), and **Voice** (hold Space and speak). This guide tests all three for every feature and tells you which test file to use.

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

## Test Files

All in `demo-data/`. Upload via the paperclip icon in the chat composer.

| File | What It Contains | Used In |
|------|-----------------|---------|
| `dose_response_staurosporine_HEK293T.csv` | 8 compounds, 10 concentrations, 3 replicates (240 rows). Staurosporine IC50 ~42 nM. | Killer workflow, dose-response fitting, ELN drafting |
| `dose-response.csv` | Minimal 8-row single-compound dose-response | Quick dose-response test |
| `compound-hit-list.csv` | 8 compounds with IC50, Hill slope, potency class, recommended action | Cherry-pick testing |
| `plate-reader-96well-controls.csv` | 96-well raw luminescence with labeled positive/negative controls, 4 compounds | Plate normalization, Z-prime |
| `qpcr-ct-values.csv` | 3 conditions, 2 genes, 2 replicates | Quick qPCR test |
| `qpcr-multiplex-experiment.csv` | 4 staurosporine concentrations, 6 genes (4 target + 2 reference), 3 replicates | Full qPCR analysis |
| `sample-inventory-import.csv` | 20 lab items: reagents, compounds, cell lines. 3 expiring within days. | Inventory import, expiry triage |
| `protocol-western-blot.csv` | 11-step Western Blot protocol with reagent names and volumes | Protocol creation, inventory pre-flight |
| `eln-experiment-results.csv` | 8 results across 3 studies (screen → confirmation → cell line panel) | ELN auto-generation |
| `microscopy-sample-DAPI-GFP.png` | Synthetic cell image with DAPI (blue nuclei) and GFP (green cytoplasm) | Multimodal image attachment |

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

**Expected:** Matching samples with barcode, location, quantity, expiry.

### Bulk Import

| Path | Action |
|------|--------|
| **Chat** | Attach `sample-inventory-import.csv` → "Import these samples into inventory" |

**Expected:** Agent reads the CSV, identifies 20 items (reagents, compounds, cell lines), and creates sample records. Three items flagged as expiring soon: CellTiter-Glo (May 25), Anti-p53 (Jun 10), Puromycin (May 20).

### Expiry Triage

| Path | Action |
|------|--------|
| **UI** | `/lab/samples` → look for orange/red expiry indicators |
| **Chat** | "What reagents are expiring in the next 30 days?" or attach `sample-inventory-import.csv` → "Which of these are expiring soon?" |
| **Voice** | Hold Space: "What's expiring soon?" |

**Expected:** CellTiter-Glo, Anti-p53 antibody, and Puromycin flagged with days until expiry.

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
| **Voice** | Hold Space: "Add a new reagent RPMI" → **redirected to chat** → Confirm |

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

### Cherry-Pick from Hit List (voice-blocked)

| Path | Action |
|------|--------|
| **UI** | `/lab/plates` → select Cherry Pick mode → select source wells → apply |
| **Chat** | Attach `compound-hit-list.csv` → "Cherry-pick all compounds with Potency_Class potent into a 384-well confirmation plate" |
| **Voice** | Hold Space: "Cherry-pick the top 3 hits" → **redirected to chat** → approval card → Confirm |

**Expected:** Agent reads hit list, identifies Staurosporine (A2), Dasatinib (B2), Compound_G (C2) as potent, creates plate map. Approval card shows plate grid with 3 compounds + controls.

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

**Expected:** CSV (Echo), GWL (Hamilton), or Python (OT-2) file downloads.

---

## 3. Data Processing

### Dose-Response Curve Fitting

| Path | Action |
|------|--------|
| **UI** | `/lab/processing` → paste concentration/response data → click Fit |
| **Chat (quick)** | Attach `dose-response.csv` → "Fit a dose-response curve for this data" |
| **Chat (full)** | Attach `dose_response_staurosporine_HEK293T.csv` → "Fit dose-response curves for all 8 compounds" |
| **Voice** | Hold Space: "Fit a dose-response curve for staurosporine" (needs data already uploaded) |

**Expected:** Quick: single IC50 value. Full: 8 compounds — Staurosporine IC50 ~42 nM, Compound_G ~8 nM (most potent), Compound_F inactive. Inline plot with sigmoidal curve.

### Plate Normalization

| Path | Action |
|------|--------|
| **UI** | `/lab/processing` → enter raw data → select Z-score method |
| **Chat** | Attach `plate-reader-96well-controls.csv` → "Normalize this plate data. Use wells A1-B2 as positive controls and A12-D12 as negative controls." |
| **Voice** | Hold Space: "Normalize my plate data using Z-score" (needs data in context) |

**Expected:** Normalized values per well. Positive controls near +1, negative controls near -1 (Z-score) or 100%/0% (PoC).

### Z-Prime Calculation

| Path | Action |
|------|--------|
| **UI** | `/lab/processing` → enter control values → calculate |
| **Chat** | Attach `plate-reader-96well-controls.csv` → "Calculate Z-prime using the positive and negative controls" |
| **Voice** | Hold Space: "What's the Z-prime for my plate?" |

**Expected:** Z' value. With the demo data: ~0.85 (excellent assay, good separation between controls).

### qPCR Delta-Delta Ct

| Path | Action |
|------|--------|
| **UI** | `/lab/processing` → enter Ct values → calculate |
| **Chat (quick)** | Attach `qpcr-ct-values.csv` → "Run delta-delta Ct analysis using GAPDH as reference and Untreated as control" |
| **Chat (full)** | Attach `qpcr-multiplex-experiment.csv` → "Analyze this qPCR experiment. Which genes are most upregulated by staurosporine at 1 µM?" |
| **Voice** | Hold Space: "Analyze my qPCR data" (needs file already uploaded) |

**Expected:** Quick: fold-change for GFP at each treatment. Full: CASP3 and BAX most upregulated at 1 µM (apoptosis markers), TP53 upregulated, BCL2 slightly changed. Agent should note the apoptosis signature.

---

## 4. ELN Notebook

### Search Entries

| Path | Action |
|------|--------|
| **UI** | `/lab/eln` → browse list |
| **Chat** | "Search ELN entries about staurosporine" |
| **Voice** | Hold Space: "Find my staurosporine ELN entries" |

**Expected:** Matching entries with title, entry number, status, date.

### Create Entry (voice-blocked)

| Path | Action |
|------|--------|
| **UI** | `/lab/eln` → click + → type title/content → save |
| **Chat** | "Create an ELN entry titled 'Staurosporine IC50 Determination'" |
| **Voice** | Hold Space: "Create a notebook entry for staurosporine" → **redirected to chat** → Confirm |

**Expected:** New entry with auto-generated number (ELN-2026-XXXX), status: draft.

### Auto-Generate from Experiment Results (voice-blocked)

| Path | Action |
|------|--------|
| **UI** | `/lab/eln` → click Auto-Generate → select experiment |
| **Chat** | Attach `eln-experiment-results.csv` → "Create an ELN entry summarizing experiment EXP-2026-001 (Kinase Inhibitor Screen Round 1)" |
| **Voice** | Hold Space: "Draft a notebook entry from my kinase screen" → **redirected to chat** |

**Expected:** Structured entry with: Objective (kinase inhibitor screen), Methods (96-well CellTiter-Glo, 3 replicates), Results (IC50 table: Staurosporine 42.3 nM, Dasatinib 18.7 nM, etc.), Conclusions (3 potent hits identified, recommend confirmation). References to experiment IDs.

### Submit Entry (voice-blocked, hard approval)

| Path | Action |
|------|--------|
| **UI** | `/lab/eln` → click Submit on draft |
| **Chat** | "Submit ELN entry ELN-2026-001" |
| **Voice** | Hold Space: "Submit my ELN entry" → **redirected to chat** → warning + Confirm |

**Expected:** Status changes to "submitted" (immutable).

---

## 5. Protocol Builder

### Create Protocol from CSV (voice-blocked)

| Path | Action |
|------|--------|
| **UI** | `/lab/protocols` → click + → add steps manually |
| **Chat** | Attach `protocol-western-blot.csv` → "Create a protocol from this CSV" |
| **Voice** | Hold Space: "Create a Western Blot protocol" → **redirected to chat** → Confirm |

**Expected:** 11-step protocol with step titles, instructions, durations, temperatures, equipment, and reagent volumes matching the CSV.

### Inventory Pre-Flight Check

| Path | Action |
|------|--------|
| **UI** | `/lab/protocols` → click Check Inventory on a protocol |
| **Chat** | After creating the Western Blot protocol: "Check if we have all reagents for it" or attach both `protocol-western-blot.csv` and `sample-inventory-import.csv` → "Do we have everything needed for this protocol?" |
| **Voice** | Hold Space: "Do we have everything for the Western Blot?" |

**Expected:** Cross-references protocol reagents against inventory. RIPA Buffer (have 100 mL, need 200 µL — OK), Protease Inhibitor (have 2 mL, need 2 µL — OK), Anti-p53 (have 100 µL, need 5 µL — OK but expiring June 10).

### Dilution Calculator

| Path | Action |
|------|--------|
| **UI** | `/lab/protocols` → enter stock/target/volume → calculate |
| **Chat** | "Calculate dilution: stock 10 mM, target 100 µM, volume 500 µL" |
| **Voice** | Hold Space: "Calculate dilution from 10 millimolar to 100 micromolar in 500 microliters" |

**Expected:** Stock volume: 5 µL, diluent volume: 495 µL. Formula: C1V1 = C2V2.

---

## 6. Killer Workflow — End-to-End

The core demo. Tests all modules working together in one conversation.

**File:** `demo-data/dose_response_staurosporine_HEK293T.csv`
**Full script:** `docs/killer-workflow-demo.md`

| Step | Action | File | Expected | Approval? |
|------|--------|------|----------|-----------|
| 1. Upload | "Analyze this plate reader export" + attach CSV | `dose_response_staurosporine_HEK293T.csv` | Column preview: Compound, Concentration_nM, Response_Pct, Well, Replicate. 240 rows. | No |
| 2. Fit | "Fit dose-response curves for all compounds" | (already uploaded) | IC50 ~42 nM for staurosporine, Hill -1.18, R² 0.99. Inline plot. | No |
| 3. ELN draft | "Create an ELN entry summarizing these results" | (uses fit results) | Structured markdown: Objective, Methods, Results (IC50 table + plot), Conclusions | Yes (L2) |
| 4. Cherry-pick | "Cherry-pick the top 3 hits into a confirmation plate" | (uses fit results) | Plate grid: Compound_G, Dasatinib, Staurosporine mapped to 384-well | Yes (L2) |
| 5. Follow-up | "What experiments should we run next?" | (uses fit results) | Options: hit confirmation (tighter range), selectivity panel, cell line comparison | Yes (L2) |
| 6. Worklist | "Generate an Echo worklist for the confirmation plate" | (uses plate from step 4) | Echo CSV preview + amber warning: "This will be sent to instrument" | Yes (L3) |

---

## 7. Multimodal Image Test

| Path | Action |
|------|--------|
| **Chat** | Attach `microscopy-sample-DAPI-GFP.png` → "What cells do you see in this image?" |

**Expected:** Agent describes cells visible in the image (blue DAPI nuclei, green GFP cytoplasm). Tests the multimodal vision pipeline — image is sent to the LLM as a base64-encoded content block.

---

## 8. Voice-Specific Tests

| Test | Action | Expected |
|------|--------|----------|
| Push-to-talk | Hold Space → speak → release | Recording indicator, transcription in chat, agent responds, TTS plays |
| VAD mode | Click mic icon → speak → pause 2s | Auto-stops on silence |
| Safe tool via voice | Hold Space: "Look up sample DMEM" | Tool executes, spoken response |
| Blocked tool via voice | Hold Space: "Submit the ELN entry" | "This requires text confirmation" |
| Voice dictation to ELN | Hold Space: "Record observation: cells at 80% confluence, passage 12, morphology normal" | Draft ELN entry (must confirm in chat) |

---

## Use Cases from /use-cases Page

### Ready — test via all 3 paths

| Code | Use Case | File to Upload | Chat Prompt | Voice Prompt |
|------|----------|---------------|-------------|-------------|
| DAT/01 | Dose-response → IC50 → ELN | `dose_response_staurosporine_HEK293T.csv` | "Fit curves" → "Draft ELN" | "Fit dose-response" (read-only via voice) |
| PLT/01 | Cherry-pick hits | `compound-hit-list.csv` | "Cherry-pick potent compounds into 384-well" | "Cherry-pick the top hits" (→ chat) |
| PLT/02 | Serial dilution | — | "Serial dilution, A1, 8 points, 3-fold" | "Set up a serial dilution" (→ chat) |
| INV/01 | Reagent expiry | `sample-inventory-import.csv` | "Which are expiring soon?" | "What's expiring?" |
| PRO/01 | Protocol pre-flight | `protocol-western-blot.csv` + `sample-inventory-import.csv` | "Do we have all reagents?" | "Do we have everything for Western Blot?" |
| DAT/02 | Plate normalization | `plate-reader-96well-controls.csv` | "Normalize with Z-score" | "Normalize my plate" |
| DAT/03 | qPCR ΔΔCt | `qpcr-multiplex-experiment.csv` | "Analyze qPCR, which genes changed at 1 µM?" | "Analyze my qPCR" |
| SAM/01 | Sample lookup | — | "Look up sample DMEM" | "Look up sample DMEM" |
| WL/01 | Worklist export | — (after plate map exists) | "Generate Echo worklist" | "Generate worklist" (→ chat) |
| ELN/01 | ELN from artifacts | `eln-experiment-results.csv` | "Create ELN for EXP-2026-001" | "Draft notebook entry" (→ chat) |
| VOC/01 | Voice → ELN capture | — | N/A | "Record: HEK293T viability, staurosporine 10-point" |

### Preview — not fully functional

| Code | Use Case | Status |
|------|----------|--------|
| MIC/01 | Microscopy run triage | Gated. `/lab/microscopy` shows synthetic demo data. Tools disabled. |
| BNL/01 | Benchling write-back | Stub. Settings shows "Coming Soon". |
| PLN/01 | Closed-loop campaign | Partial. Agent proposes follow-ups but full Plan Mode not built. |

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
| Approval card not showing | Ensure approval service is running (check backend logs) |
| CSV not parsed | Check file has headers; use UTF-8 encoding |
