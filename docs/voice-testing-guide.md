# Voice Mode — Testing Guide

## How It Works

1. Open http://localhost:3000/lab
2. Click the **microphone icon** in the chat toolbar (between paperclip and Resource)
3. Allow microphone access when prompted
4. **Speak your command** — the waveform bars respond to your voice
5. **Stop speaking** — after 1.5 seconds of silence, the system auto-sends (or tap the mic to send manually)
6. Watch the status: Listening → Transcribing → Thinking → Speaking
7. The assistant speaks the response and automatically starts listening again
8. Press **Escape** or click **X** to exit voice mode

All voice interactions appear as text in the chat thread for a permanent record.

---

## Test Scenarios

These 5 scenarios exercise every major feature through the full speech-to-speech pipeline: microphone → Whisper STT → GPT-4o with agentic tools → database queries → TTS → speaker.

---

### 1. Sample Inventory Query

**Tests:** Sample Tracker, `get_expiring_samples` tool, PostgreSQL query

**Say:**
> "What antibodies are expiring in the next 30 days?"

**Expected flow:**
- Whisper transcribes the audio
- Agent calls `get_expiring_samples(days=30)`
- Tool queries the `samples` table for items with `expiry_date` within 30 days and `sample_type = antibody`
- Finds: Anti-HER2 Rabbit (15 days), Anti-GFP Rabbit pAb (20 days)
- TTS speaks the results

**Expected response (spoken):**
> "You have 2 antibodies expiring soon: Anti-HER2 Rabbit with 15 days remaining, stored in Freezer-A Shelf-1 Box-3, and Anti-GFP Rabbit pAb with 20 days remaining in Freezer-A Shelf-2 Box-1."

**What it validates:**
- Full voice pipeline (STT → tools → TTS)
- Database query with date filtering
- Structured response formatting from raw DB data

---

### 2. Dose-Response Results

**Tests:** Data Processing, Experiments, `get_ic50_values` tool

**Say:**
> "What was the IC50 for Staurosporine in the HEK293T experiment?"

**Expected flow:**
- Agent calls `get_ic50_values(compound="Staurosporine")`
- Tool queries experiments where name/description matches "Staurosporine"
- Finds the completed experiment with results: EC50=0.042, Hill slope=1.23, R²=0.994
- TTS speaks the results

**Expected response (spoken):**
> "The IC50 for Staurosporine in HEK293T was 0.042 micromolar, with a Hill slope of 1.23 and an R-squared of 0.994. The experiment status is completed."

**What it validates:**
- Scientific terminology in STT (Staurosporine, IC50, HEK293T)
- JSON results extraction from experiments table
- Numeric precision in TTS output

---

### 3. Plate Map Details

**Tests:** Plate Mapping, `get_plate_map_details` tool, well mapping data

**Say:**
> "Show me the well mappings for the HTS Screen plate map"

**Expected flow:**
- Agent calls `get_plate_map_details(plate_map_name="HTS Screen")`
- Tool queries `plate_maps` table, returns well mappings JSON
- Finds 5 mappings: Staurosporine at 10/3.33/1.11 µM, Rapamycin at 10/3.33 µM
- TTS speaks the plate layout

**Expected response (spoken):**
> "The HTS Screen Round 1 is a 96-well plate for the primary cytotoxicity screen of the kinase inhibitor panel. It has 5 well transfers: Staurosporine mapped at 10, 3.33, and 1.11 micromolar in wells A1 through A3, and Rapamycin at 10 and 3.33 micromolar in wells B1 and B2."

**What it validates:**
- Complex JSON data (well mappings) summarised for voice
- Plate terminology (96-well, wells A1-B2) in both STT and TTS
- Source-destination mapping comprehension

---

### 4. ELN Entry Creation

**Tests:** ELN Notebook, `create_eln_entry` tool, auto-generation from experiment data

**Say:**
> "Create an ELN entry for the Staurosporine IC50 experiment"

**Expected flow:**
- Agent calls `create_eln_entry(title="...", experiment_id="...")`
- Tool fetches the experiment from DB, generates markdown with objectives, protocol, results
- Creates a new row in `eln_entries` table with entry number ELN-2026-XXXX
- TTS confirms the creation

**Expected response (spoken):**
> "I've created ELN entry ELN-2026-0002 for the Staurosporine IC50 HEK293T experiment. It includes the protocol, plate layout, and dose-response results with an EC50 of 0.042 micromolar. You can view and edit it in the Notebook tab."

**What it validates:**
- Write operation via voice (creates a database record)
- Auto-generation from experiment context
- Cross-referencing experiments → plate maps → results
- Entry number generation

---

### 5. Protocol Inventory Check

**Tests:** Protocol Builder, Sample Tracker, `query_protocols` + `check_protocol_inventory` tools, multi-tool orchestration

**Say:**
> "Do we have all the reagents for the CellTiter-Glo cytotoxicity protocol?"

**Expected flow:**
- Agent calls `query_protocols(query="CellTiter-Glo")` to find the protocol
- Agent calls `check_protocol_inventory(protocol_id="...")` to cross-reference reagents against inventory
- Tool joins protocol step reagents against the `samples` table
- Reports which reagents are available and which are missing
- TTS speaks the availability report

**Expected response (spoken):**
> "I checked the CellTiter-Glo cytotoxicity protocol. You have DMEM media and PBS buffer in stock. However, the CellTiter-Glo reagent itself is not in your inventory. I'd recommend ordering it before starting the protocol."

**What it validates:**
- Multi-tool orchestration (two sequential tool calls in one turn)
- Cross-table join (protocols → steps → reagents → samples)
- Practical actionable advice in the response
- Complex protocol name recognition in STT

---

## Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| No mic icon visible | Browser doesn't support MediaRecorder | Use Chrome or Edge |
| "Microphone permission denied" | Browser blocked mic access | Click the lock icon in the address bar → Allow microphone |
| "I didn't catch that" | Too quiet or too short | Speak louder or closer to the mic, ensure > 500ms of speech |
| Long silence before sending | Threshold too low for your environment | Background noise keeps the VAD active — tap mic to send manually |
| No audio playback | Browser autoplay policy | Interact with the page first (click anything), then try voice mode |
| "Voice processing failed" | Backend not running or OpenAI key missing | Check `docker compose ps` and verify OPENAI_API_KEY is set |
| Response is text-only, no speech | TTS failed | Check backend logs: `docker compose logs backend` |

## Keyboard Shortcuts

| Key | Action |
|---|---|
| **Escape** | Exit voice mode |
| **Click mic circle** | Manual stop and send (push-to-talk) |
