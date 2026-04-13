# Demo Script -- Beatriz (Dewpoint Therapeutics)

**Duration:** 15 minutes
**Presenter:** Teo
**Audience:** Beatriz -- Product Manager, Drug Discovery background (Dewpoint Therapeutics)
**Setup:** localhost:3000 open in Chrome, backend running (`cd backend && uvicorn main:app`), demo data seeded (`python -m scripts.seed_demo_data`)

---

## Opening (1 min)

> "Resonantia is an agentic OS for lab informatics. One interface for everything a scientist does between designing an experiment and writing it up."

- Point to the chat interface on screen.
- Emphasize: text, voice, file upload -- all in the same window.

---

## Act 1: The Problem (2 min)

Walk through the current workflow most discovery labs endure:

1. **Excel** -- design a plate map, manually type well assignments.
2. **Vendor software** -- program the liquid handler, re-enter the same layout.
3. **Plate reader export** -- get a raw CSV, open in another tool.
4. **GraphPad Prism** -- copy-paste data, fit curves, export images.
5. **PowerPoint** -- assemble figures for the team meeting.
6. **Email** -- send the deck, lose the context.

> "That is six disconnected tools for one experiment. Each handoff is manual, error-prone, and unlogged. Nobody can reproduce it six months later."

Pause. Let the pain land.

---

## Act 2: Chat-First Interface (3 min)

### Show the inventory query

Type into the chat box:

```
What samples do we have in total, broken down by type?
```

- The assistant calls `lookup_sample` and returns a structured breakdown: compounds, antibodies, cell lines, reagents.
- Point out: "No SQL. No dashboard navigation. Just a question."

### Show experiment results

Type:

```
What was the IC50 for Staurosporine?
```

- The assistant calls `get_ic50_values` and returns the fitted IC50 with confidence interval.
- Point out: "It pulled from a real processing result. This is live data, not a canned response."

### Show guardrails (optional, if time)

Type:

```
Write me a poem about kinases
```

- The assistant declines: "I can only help with lab informatics tasks."
- Point out: "Guardrails keep it focused. No hallucinated science, no off-topic drift."

---

## Act 3: Voice Mode (2 min)

Click the microphone icon in the chat bar.

Say clearly:

> "Create an ELN entry for the Staurosporine IC50 experiment"

Walk through the voice loop visually as it happens:

1. **Listening** -- waveform animation appears.
2. **Transcribing** -- text appears in the input bar.
3. **Thinking** -- the assistant indicator pulses.
4. **Speaking** -- the assistant reads back the confirmation.

Navigate to the **Notebook** tab in the sidebar. Show the new ELN entry that was just created, with:
- Title auto-generated from the voice prompt.
- Experiment metadata pulled from processing results.
- Timestamp and author logged.

> "Hands-free. Useful at the bench when your gloves are on."

---

## Act 4: Plate Mapping (2 min)

Navigate to the **Plates** tab.

### Show the plate grid

- Point out the 96-well visual grid with colour-coded wells.
- Toggle to **384-well** format. The grid re-renders instantly.
- Toggle back to 96-well.

### Show cherry-pick mode

- Click "Cherry-pick" in the toolbar.
- Click individual wells to assign compounds. Show the selection highlight.
- Point out the source-destination mapping panel on the right.

### Show serial dilution mode

- Click "Serial Dilution."
- Select a starting well and direction. Show the gradient fill.

### Export

- Click "Export Worklist."
- Show the downloaded CSV. Open it briefly -- it is Echo-compatible format (Source Plate, Source Well, Dest Plate, Dest Well, Volume).

> "From plate design to liquid handler instructions in 30 seconds. No re-entry."

---

## Act 5: Everything Connects (3 min)

### Cross-reference protocols and inventory

Click the mic or type:

```
Check if we have all reagents for the CellTiter-Glo cytotoxicity protocol
```

Walk through what happens:
1. The system looks up the CellTiter-Glo protocol and its steps.
2. It extracts every reagent mentioned.
3. It cross-references the sample inventory.
4. It returns a table: reagent name, required, in stock (yes/no), location, expiry.

> "One question replaced 10 minutes of cross-checking spreadsheets."

### Dilution calculator

Type or say:

```
Calculate the dilution I need to make 200 microlitres of 0.5 micromolar Staurosporine from a 10 millimolar stock
```

The assistant returns:
- C1V1 = C2V2 calculation shown.
- Volume of stock to add: 0.01 microlitres.
- Volume of solvent to add: 199.99 microlitres.
- A note if the stock volume is below pipetting accuracy and suggests an intermediate dilution.

> "It does not just compute -- it warns you when the answer is impractical."

---

## Act 6: Integrations and Compliance (2 min)

Navigate to the **Settings** tab.

### Show integrations panel

- **eLabFTW**: connected (green indicator). ELN entries sync bidirectionally.
- **Benchling**: coming soon (greyed out).
- **Dotmatics**: coming soon (greyed out).

> "We start with eLabFTW because it is open-source and widely used in academic and biotech labs. Benchling and Dotmatics are on the roadmap."

### Show conversation history

- Open the sidebar. Show previous conversations listed with timestamps.
- Click one. Show the full thread is preserved.
- Point out: "Every conversation is persistent and scoped to the organisation. If Beatriz asks a question today and her colleague opens the app tomorrow, the context is there."

### Mention observability

> "Every tool call is traced through Langfuse. Every LLM interaction is logged. If a regulator asks why a decision was made, we have the audit trail."

### Mention multi-tenancy

> "Each organisation is fully isolated. Data, conversations, samples, protocols -- nothing leaks between tenants. Clerk handles authentication; our backend enforces organisation-level access on every query."

---

## Closing (1 min)

> "Every action is logged. Every conversation is persistent. Every organisation is isolated. And it works hands-free."

Pause.

> "We are starting with five core modules: plates, samples, protocols, ELN, and processing. The next five -- inventory alerts, batch tracking, instrument integration, reporting, and approval workflows -- are scoped for Q3."

> "What questions do you have?"

---

## Backup Prompts (if questions lead here)

| Topic | Prompt to type live |
|-------|---------------------|
| Data analysis | Upload `dose-response.csv` and say "Analyze this dose-response data and fit an IC50 curve" |
| qPCR | Upload `qpcr-ct-values.csv` and say "Run delta-delta Ct analysis using GAPDH as reference" |
| Plate normalization | Upload `plate-reader.csv` and say "Normalize this plate data using Z-score" |
| Microscopy | "What microscopy images do we have?" (if images are seeded) |
| Compound summary | "Give me a complete summary of everything we know about Staurosporine" |

---

## Technical Details (only if asked)

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js, Zustand, React Query, Clerk auth |
| Backend | Python (FastAPI), Pydantic models |
| LLM | Anthropic Claude (tool-use with structured outputs) |
| Database | PostgreSQL |
| Cache | Redis |
| Orchestration | Temporal (local KIND cluster for demo) |
| Observability | Langfuse |
| ELN Integration | eLabFTW API |
| Voice | Web Speech API (browser-native) |
| Deployment | Local for demo; AWS for production |
