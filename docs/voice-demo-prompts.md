# Voice Demo Prompts — Testing All Features

6 voice prompts that exercise every major feature through the speech-to-speech pipeline. Each prompt creates, modifies, or queries real data in PostgreSQL via the agentic tool loop.

Use these in voice mode (click the mic icon) or type them in the chat.

---

## 1. Plates — Create a Plate Map

**Prompt:**
> "Create a plate map called Kinase Selectivity Panel with cherry-pick mode for a 96-well plate"

**Tools called:** `create_plate_map`

**What happens:**
- Agent calls the plate mapping tool with name="Kinase Selectivity Panel", plate_type="96", mapping_mode="cherry-pick"
- A new row is created in the `plate_maps` table in PostgreSQL
- The plate map appears in the Plates tab sidebar

**Verifies:** Write operations via voice, plate mapping tool, database persistence

---

## 2. Samples — Query Expired Inventory

**Prompt:**
> "Look up all compounds in our inventory and tell me which ones are expired"

**Tools called:** `get_expiring_samples`, `lookup_sample`

**What happens:**
- Agent queries the `samples` table filtering by expiry date
- Finds Rapamycin (expired ~10 days ago, lot CP-2024-8811, Freezer-B)
- Reports the expired item with location, quantity, and how many days overdue

**Verifies:** Read queries with date filtering, scientific terminology in STT/TTS (Rapamycin, lot numbers)

---

## 3. Microscopy — Browse Imaging Data

**Prompt:**
> "What microscopy images do we have? List them by well and channel"

**Tools called:** `browse_microscopy`

**What happens:**
- Agent queries the `microscopy_images` table
- If images have been uploaded, lists them by well position and fluorescence channel (DAPI, GFP, mCherry)
- If no images exist, responds with: "No microscopy images found. Upload images via the Microscopy tab."

**Verifies:** Microscopy tool, graceful handling of empty datasets, channel terminology

---

## 4. ELN Notebook — Auto-Generate Entry

**Prompt:**
> "Create an ELN entry for the Staurosporine IC50 experiment and include all the results"

**Tools called:** `create_eln_entry` (with experiment_id)

**What happens:**
- Agent finds the "Staurosporine IC50 — HEK293T" experiment in the database
- Auto-generates a markdown ELN entry with:
  - Objective (from experiment description)
  - Protocol (from experiment protocol field)
  - Results: EC50=0.042 µM, Hill slope=1.23, R²=0.994, Top=100.2%, Bottom=3.1%
- Saves to the `eln_entries` table with auto-generated entry number (ELN-2026-XXXX)
- The entry appears in the Notebook tab

**Verifies:** Write operation, cross-table query (experiments → results), auto-generation, ELN tool

---

## 5. Protocols — Inventory Check

**Prompt:**
> "Check if we have all the reagents needed for the CellTiter-Glo cytotoxicity protocol"

**Tools called:** `query_protocols`, `check_protocol_inventory`

**What happens:**
- Agent first searches for the protocol by name ("CellTiter-Glo")
- Then cross-references each reagent listed in the protocol steps against the `samples` table
- Reports availability:
  - Available: DMEM media (500 mL in Fridge-1), PBS buffer (1000 mL on Shelf-A)
  - Missing: CellTiter-Glo reagent (not in inventory)
- Suggests ordering the missing reagent before running the protocol

**Verifies:** Multi-tool orchestration (two sequential tool calls), cross-table join (protocols → steps → reagents → samples), actionable recommendations

---

## 6. Processing — Dilution Calculator

**Prompt:**
> "Calculate the dilution I need to make 200 microlitres of 0.5 micromolar Staurosporine from a 10 millimolar stock"

**Tools called:** `calculate_dilution`

**What happens:**
- Agent calls C1V1=C2V2 calculator: c1=10000 µM, c2=0.5 µM, v2=200 µL
- Computes: v1 = (0.5 × 200) / 10000 = 0.01 µL
- Responds: "Add 0.01 µL of your 10 mM stock to 199.99 µL of diluent to get 200 µL at 0.5 µM"
- Shows the formula: V1 = (C2 × V2) / C1

**Verifies:** Mathematical computation, unit handling in STT (microlitres, micromolar, millimolar), formula display in TTS

---

## How to Test

### Voice Mode
1. Open http://localhost:3000/lab
2. Click the **microphone icon** in the chat toolbar
3. Allow microphone access
4. Speak one of the prompts above
5. Wait for: Listening → Transcribing → Thinking → Speaking
6. Verify the response mentions the correct data
7. Check the corresponding tab (Plates, Samples, Notebook, etc.) to confirm data was created/queried

### Text Mode
1. Type the prompt in the chat input
2. Press Enter
3. Verify the response and check the relevant tab

### What to Look For
- **Transcription accuracy:** Did Whisper correctly transcribe scientific terms? (Staurosporine, micromolar, CellTiter-Glo)
- **Tool selection:** Did the agent pick the right tool for the task?
- **Data accuracy:** Do the returned values match what's in the database?
- **TTS clarity:** Did the spoken response correctly pronounce numbers, units, and chemical names?
- **State change:** After prompts 1 and 4 (which create data), does the new item appear in the relevant tab?
