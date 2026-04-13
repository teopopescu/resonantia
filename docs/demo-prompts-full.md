# Resonantia Lab -- Complete Prompt Guide

Every prompt below works in both text chat and voice mode. Where voice phrasing differs from typed text (e.g. "microlitres" vs "uL"), both forms are shown.

---

## 1. Lab Informatics Features

### 1.1 Plates

| Action | Prompt |
|--------|--------|
| Create a plate map (cherry-pick) | "Create a plate map called Kinase Selectivity Panel with cherry-pick mode for a 96-well plate" |
| Create a plate map (serial dilution) | "Create a 384-well plate map called HTS Primary Screen using serial dilution mode with 8-point 3-fold dilutions" |
| List all plate maps | "Show me all our plate maps" |
| Inspect a plate map | "What are the well mappings for the HTS Screen plate map?" |
| Export a worklist | "Export the Kinase Selectivity Panel plate map as an Echo-compatible CSV worklist" |
| Toggle plate format | "Switch the plate view to 384-well format" |
| Assign compounds to wells | "Assign Staurosporine to wells A1 through A8 at concentrations 10, 3, 1, 0.3, 0.1, 0.03, 0.01, and 0.003 micromolar" |

### 1.2 Samples

| Action | Prompt |
|--------|--------|
| Full inventory overview | "What samples do we have in total, broken down by type?" |
| Look up expired compounds | "Look up all compounds in our inventory and tell me which ones are expired" |
| List antibodies | "What antibodies do we have in stock?" |
| Find a specific sample | "Check if we have Anti-EGFR antibody and where it's stored" |
| Check stock levels | "Which of our reagents are running low?" |
| Add a new sample | "Add a new compound called Dasatinib, 10 millimolar in DMSO, stored in Freezer B Shelf 3, expires December 2026" |
| Update a sample | "Update the Anti-EGFR antibody location to Fridge A Shelf 2" |

### 1.3 Microscopy

| Action | Prompt |
|--------|--------|
| List images | "What microscopy images do we have? List them by well and channel" |
| View a specific well | "Show me the microscopy image for well B3" |
| Compare channels | "Show DAPI and GFP channels side by side for well A1" |
| Overlay channels | "Overlay the DAPI and phalloidin channels for well C5" |

> Note: microscopy features require uploaded images. Use the upload button or drag and drop TIFF/PNG files to populate the image store before running these prompts.

### 1.4 ELN Notebook

| Action | Prompt |
|--------|--------|
| Create an entry | "Create an ELN entry for the Staurosporine IC50 experiment and include all the results" |
| List entries | "Show me all my notebook entries" |
| Search entries | "What did I write about the kinase panel?" |
| Edit an entry | "Add a conclusion section to my latest ELN entry saying the IC50 was 42 nanomolar" |
| Sync to eLabFTW | "Sync my latest notebook entry to eLabFTW" |
| Tag an entry | "Tag the Staurosporine IC50 entry with kinase-inhibitor and dose-response" |

### 1.5 Protocols

| Action | Prompt |
|--------|--------|
| List protocols | "Show me all protocols we have" |
| Reagent check | "Check if we have all the reagents needed for the CellTiter-Glo cytotoxicity protocol" |
| Dilution calculator | "Calculate the dilution I need to make 200 microlitres of 0.5 micromolar Staurosporine from a 10 millimolar stock" |
| Voice-friendly dilution | "Calculate the dilution I need to make two hundred microlitres of zero point five micromolar Staurosporine from a ten millimolar stock" |
| Create a protocol | "Create a new protocol called Western Blot for EGFR with steps for lysis, gel loading, transfer, blocking, primary antibody, secondary antibody, and imaging" |
| Step details | "What are the steps in the CellTiter-Glo protocol?" |

### 1.6 Processing

| Action | Prompt |
|--------|--------|
| Get IC50 | "What was the IC50 for Staurosporine in the HEK293T experiment?" |
| List results | "Show me all completed processing results" |
| Z-prime score | "What was the Z-prime for our latest screen?" |
| Plate normalization | "Normalize plate data using Z-score with columns 1 and 2 as positive controls" |
| Dose-response fit | "Fit a 4-parameter logistic curve to the Staurosporine dose-response data" |

---

## 2. AI and Intelligence Features

### 2.1 Guardrails -- Off-Topic Rejection

These prompts should be blocked or redirected by the guardrails system.

| Prompt | Expected behaviour |
|--------|--------------------|
| "Write me a poem about science" | Blocked. Response: "I can only help with lab informatics tasks." |
| "Help me with my homework" | Blocked. Response redirects to lab tasks. |
| "What is the weather today?" | Redirected. "I focus on lab informatics. Is there a lab task I can help with?" |
| "Tell me a joke" | Blocked. |
| "What is the meaning of life?" | Blocked. |

### 2.2 Cross-Feature Queries

These prompts exercise multi-tool orchestration. The system calls several backend tools in parallel and merges the results.

| Prompt | Tools triggered |
|--------|-----------------|
| "Give me a complete summary of everything we know about Staurosporine" | lookup_sample, get_ic50_values, query_experiments, query_eln_entries |
| "What experiments have we completed and what were the results?" | query_experiments, get_processing_results |
| "Which of our reagents are running low or expiring soon?" | lookup_sample (filter: expiry / quantity) |
| "Prepare a slide deck summary for the Staurosporine project" | query_eln_entries, get_ic50_values, query_experiments |
| "Are there any protocols we cannot run right now due to missing reagents?" | list_protocols, check_reagents, lookup_sample |

---

## 3. Integration Features

### 3.1 File Upload

Upload the file first (drag-and-drop or click the upload button), then type or speak the prompt.

| File | Prompt |
|------|--------|
| `dose-response.csv` | "Analyze this dose-response data and fit an IC50 curve" |
| `plate-reader.csv` | "Normalize this plate data using Z-score with columns 1 and 2 as positive controls" |
| `qpcr-ct-values.csv` | "Run delta-delta Ct analysis on this qPCR data using GAPDH as reference and Untreated as control" |

Expected outputs:
- **dose-response.csv**: fitted curve parameters, IC50 value with 95% CI, Hill coefficient, R-squared, and a plotted curve.
- **plate-reader.csv**: Z-score normalised heatmap, Z-prime calculation, hit identification with configurable threshold.
- **qpcr-ct-values.csv**: delta-Ct, delta-delta-Ct, fold-change table per sample/gene pair, bar chart of fold-change.

### 3.2 @ Mentions

@ mentions let you target a specific feature module directly. Type `@` to see the autocomplete list.

| Prompt | Target module |
|--------|---------------|
| `@Plate Maps show me the HTS Screen` | Plates module |
| `@Sample Inventory what antibodies are expiring?` | Samples module |
| `@eLabFTW sync my latest notebook entry` | eLabFTW integration |
| `@Protocols list all cytotoxicity protocols` | Protocols module |
| `@Processing what was the last IC50 we calculated?` | Processing module |
| `@Microscopy show images for well A1` | Microscopy module |

---

## 4. Voice-Mode Specific Tips

- Speak naturally. Numbers like "zero point three micromolar" are parsed correctly.
- Say "stop" or "cancel" to interrupt the assistant mid-response.
- The voice loop is: listening --> transcribing --> thinking --> speaking.
- You can interject while the assistant is speaking; it will pause and listen.
- For precise well references, spell them out: "well A one" or "well H twelve."

---

## 5. Quick-Start Checklist

1. Open `http://localhost:3000` in Chrome.
2. Sign in with Clerk (dev mode accepts any email).
3. Verify the sidebar shows: Chat, Plates, Samples, Microscopy, Notebook, Protocols, Processing, Settings.
4. Seed demo data: `cd backend && python -m scripts.seed_demo_data`.
5. Try the first prompt: "What samples do we have in total, broken down by type?"
6. Upload `demo-data/dose-response.csv` and ask: "Analyze this dose-response data and fit an IC50 curve."
7. Click the mic icon and say: "Show me all my notebook entries."
