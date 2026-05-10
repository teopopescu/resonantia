# Killer Workflow E2E Demo Script

**Duration:** ~5 minutes
**Prerequisites:** Resonantia backend running, seed data loaded
**Data file:** `demo-data/dose_response_staurosporine_HEK293T.csv`

---

## Step 1 -- Upload

### User Prompt
> "Analyze this plate reader export"

Attach: `dose_response_staurosporine_HEK293T.csv`

### Expected Agent Response
- Agent calls the file upload endpoint (POST /api/v1/files/upload-and-parse)
- Agent identifies the CSV structure:
  - 5 columns: Compound, Concentration_nM, Response_Pct, Well, Replicate
  - 240 data rows
  - Detected format: `dose_response`
- Agent shows a preview of the first few rows
- Agent summarizes: "8 compounds, 10 concentrations each, 3 replicates per condition"

### What the User Sees
- File upload confirmation with parsed metadata
- Column types detected (Compound=string, Concentration_nM=numeric, Response_Pct=numeric, Well=string, Replicate=integer)
- Preview table showing first 5 rows

### Verification
- File persisted in storage (check /api/v1/files/)
- file_id returned in response
- `detected_format` = "dose_response"
- `row_count` = 240

---

## Step 2 -- Fit Dose-Response Curves

### User Prompt
> "Fit dose-response curves for all compounds"

### Expected Agent Response
- Agent calls `fit_dose_response` tool for each of the 8 compounds
- For each compound, returns:
  - IC50 value with 95% confidence interval
  - Hill slope
  - R-squared
  - Plot URL (PNG)

Key expected results:

| Compound       | IC50 (nM) | Hill Slope | R-squared | Classification |
|----------------|-----------|------------|-----------|----------------|
| Staurosporine | ~40-44    | ~-1.2      | >0.99     | Potent         |
| Rapamycin      | ~170-190  | ~-1.0      | >0.98     | Moderate       |
| Imatinib       | ~2400-2600| ~-0.8      | >0.95     | Weak           |
| Dasatinib      | ~13-17    | ~-1.4      | >0.99     | Very potent    |
| Sorafenib      | ~85-95    | ~-1.1      | >0.99     | Moderate       |
| Erlotinib      | ~480-520  | ~-0.9      | >0.98     | Moderate-weak  |
| Compound_F     | >50000    | ~-0.3      | N/A       | Inactive       |
| Compound_G     | ~6-10     | ~-1.5      | >0.99     | Most potent    |

### What the User Sees
- Table of IC50 values for all compounds
- Inline dose-response plot for each compound (or a combined multi-panel plot)
- Classification of hits (potent/moderate/weak/inactive)
- Outlier flags if any

### Verification
- Staurosporine IC50 is between 35-50 nM
- R-squared for Staurosporine is > 0.98
- Compound_F correctly identified as inactive (IC50 far above tested range)
- Compound_G identified as most potent (IC50 < 10 nM)
- Experiment records created in database for each compound

---

## Step 3 -- ELN Draft

### User Prompt
> "Create an ELN entry summarizing these results"

### Expected Agent Response
- Agent calls `create_eln_entry` tool with experiment context
- Returns an approval card containing:
  - Entry number (e.g., ELN-2026-0001)
  - Title: "ELN -- Dose-Response: Staurosporine" (or multi-compound summary)
  - Structured markdown content with sections:
    - Objective
    - Methods (plate format, compounds, replicates, readout)
    - Results (IC50, Hill slope, R-squared, plot)
    - Conclusions
    - References

### What the User Sees
- Approval card with rendered ELN preview
- "Confirm" and "Edit" buttons
- Structured ELN content with proper formatting

### User Action
Click **Confirm** to persist the ELN entry.

### Verification
- ELN entry created in database with status "draft"
- Entry accessible via GET /api/v1/eln/
- Content includes IC50 values and experiment references
- Entry linked to the experiment record

---

## Step 4a -- Plate Layout (Cherry-Pick)

### User Prompt
> "Cherry-pick the top 3 hits into a confirmation plate"

### Expected Agent Response
- Agent identifies top 3 hits by IC50 potency:
  1. Compound_G (IC50 ~8 nM)
  2. Dasatinib (IC50 ~15 nM)
  3. Staurosporine (IC50 ~42 nM)
- Agent calls `cherry_pick` tool with hit list
- Returns approval card with:
  - Visual plate map preview (96-well format)
  - Color-coded wells (sample=blue, positive control=green, negative control=red)
  - Transfer summary

### What the User Sees
- Approval card with plate layout visualization
- Summary: "3 compounds cherry-picked into confirmation plate"
- Well assignments for each compound

### User Action
Click **Confirm** to create the plate map.

### Verification
- PlateMap record created in database
- Well mappings include all 3 compounds
- Controls assigned to columns 1 and 12

---

## Step 4b -- Follow-Up Proposal

### User Prompt
> "What experiments should we run next?"

### Expected Agent Response
- Agent calls `propose_follow_up_experiment` tool
- Returns a multi-option proposal card with 2-3 options:

**Option 1: Hit Confirmation** (Recommended)
- Confirm IC50 of top hits with tighter concentration range and more replicates
- 384-well plate, 10-point 2-fold dilution, 4 replicates
- ~88 wells estimated

**Option 2: Selectivity Panel**
- Test compound selectivity across related targets
- 384-well plate, 5-point 10-fold dilution, 3 replicates
- ~120 wells estimated

**Option 3: Cell Line Comparison**
- Verify potency is not cell-line-specific
- 96-well plate, 10-point 3-fold dilution, 3 replicates
- ~36 wells estimated

### What the User Sees
- Multi-option proposal card
- Each option has title, rationale, plate layout details, and estimated well count
- Radio buttons or cards to select an option

### User Action
Select **Option 1** (Hit Confirmation).

### Verification
- Options include concentration ranges centered around the measured IC50
- Recommended option is #1 (Hit Confirmation)
- Each option has plate_type, concentration_range, replicates, and controls

---

## Step 5 -- Worklist Generation

### User Prompt
> "Generate an Echo worklist for the confirmation plate"

### Expected Agent Response
- Agent calls `generate_worklist` tool with the plate_map_id from Step 4a
- Returns approval card with:
  - Amber warning indicator (liquid handler commands are irreversible)
  - Worklist filename (e.g., `worklist_Cherry-Pick_Plate_echo.csv`)
  - Preview of first 10 rows (Echo CSV format)
  - Total transfers count
  - Total volume summary

### What the User Sees
- Approval card with amber/warning styling
- Warning text: "This will generate commands for the Echo liquid handler"
- CSV preview showing:
  ```
  Source Plate Name,Source Well,Destination Plate Name,Destination Well,Transfer Volume
  SRC,A1,DEST,A1,100
  SRC,B1,DEST,A2,100
  ...
  ```
- Download button for full CSV

### User Action
Click **Confirm** to generate the worklist file.

### Verification
- Worklist content is valid Echo CSV format
- Header row: Source Plate Name, Source Well, Destination Plate Name, Destination Well, Transfer Volume
- Number of transfer rows matches plate map well count
- Volume values are consistent (default 100 nL)
- File downloadable via storage API

---

## Step 6 -- Summary

### User Prompt
(Agent summarizes automatically after Step 5, or user asks "Summarize what we did")

### Expected Agent Response
Agent provides a structured summary of all actions taken:

> **Session Summary:**
>
> 1. Uploaded and parsed dose-response data (240 data points, 8 compounds)
> 2. Fitted 4PL curves for all compounds:
>    - Top hit: Compound_G (IC50 = 8 nM)
>    - 2nd: Dasatinib (IC50 = 15 nM)
>    - 3rd: Staurosporine (IC50 = 42 nM)
>    - Inactive: Compound_F
> 3. Created ELN entry ELN-2026-0001 (draft)
> 4. Cherry-picked top 3 hits into confirmation plate
> 5. Generated Echo worklist (N transfers, N nL total volume)
>
> **Artifacts created:**
> - ELN Entry: ELN-2026-0001
> - Plate Map: Cherry-Pick Plate
> - Worklist: worklist_Cherry-Pick_Plate_echo.csv
>
> **Next steps:** Hit confirmation experiment ready to run

### Verification
- [ ] ELN entry exists in /lab/eln with correct content
- [ ] Plate map visible in /lab/plates
- [ ] Downloaded worklist has valid Echo CSV format
- [ ] All actions visible in Langfuse traces (if enabled)

---

## Troubleshooting

### IC50 values differ from expected
The seed data uses a fixed random seed (42) for noise generation. Fitted IC50 values should be within 10% of nominal values. If they differ significantly, regenerate the CSV:
```bash
cd backend && uv run python ../demo-data/generate_seed_csv.py
```

### Compound_F shows as active
Compound_F has an IC50 of 50,000 nM, well above the tested range (max 10,000 nM). The curve should appear flat. If fitting succeeds with a low IC50, the fit is unreliable -- check that the fitter correctly identifies this as a poor fit (low R-squared or IC50 outside tested range).

### Worklist generation fails
Ensure a plate map exists before calling generate_worklist. The tool requires a valid `plate_map_id` from a previously created plate map (Step 4a).
