# SPEC: End-to-End Killer Workflow Demo

**ID:** P1.6
**Phase:** 1 — Killer Workflow
**Branch:** `feat/killer-workflow-demo`
**Priority:** P1
**Effort:** 2 days
**Dependencies:** P1.0–P1.5, P1.4b

---

## Problem Statement

The killer workflow must be demonstrable end-to-end with reproducible results. Without a scripted demo with seed data, design partner demos are unreliable — dependent on live LLM responses that may vary.

---

## Scope

### In Scope
- Seed CSV file with realistic dose-response data
- Demo script document (exact prompts + expected responses)
- Backend integration test exercising the full workflow via API
- Verification that all 6 killer workflow steps complete successfully

### Out of Scope
- Playwright E2E test (nice-to-have, not blocking)
- Custom demo data per partner (generic seed data)
- Live LLM response pinning (LLM responses will vary; test structure, not exact text)

---

## Architecture

### Seed Data

```
demo-data/dose_response_staurosporine_HEK293T.csv

Columns: Compound, Concentration_nM, Response_Pct, Well, Replicate
Rows: 8 compounds x 10 concentrations x 3 replicates = 240 rows

Staurosporine: IC50 ~42 nM (sigmoid, Hill ~-1.2, R² ~0.99)
Compound_B: IC50 ~180 nM (moderate potency)
Compound_C: IC50 ~2500 nM (weak)
Compound_D: IC50 ~15 nM (potent)
Compound_E: no activity (flat curve)
Compound_F: IC50 ~90 nM
Compound_G: IC50 ~500 nM
Compound_H: IC50 ~8 nM (most potent)
```

### Demo Script

```
Step 1: Upload
> Prompt: "Analyze this plate reader export"
> Attach: dose_response_staurosporine_HEK293T.csv
> Expected: Agent parses CSV, shows preview, confirms structure

Step 2: Fit
> Prompt: "Fit dose-response curves for all compounds"
> Expected: IC50 values, Hill slopes, R², Z', inline plot for each compound

Step 3: ELN Draft
> Prompt: "Create an ELN entry summarizing these results"
> Expected: Approval card with structured ELN content
> Action: Click Confirm

Step 4: Follow-Up Proposal
> Prompt: "What experiments should we run next?"
> Expected: 2-3 options (hit confirmation for top 3 potent compounds, selectivity panel, etc.)
> Action: Select Option 1 (hit confirmation)

Step 5: Worklist
> Prompt: "Generate an Echo worklist for the confirmation plate"
> Expected: Approval card with amber warning, worklist preview
> Action: Click Confirm, download CSV

Step 6: Verify
> Check: ELN entry exists in /lab/eln with correct content
> Check: Plate map visible in /lab/plates
> Check: Downloaded worklist has valid Echo CSV format
> Check: All actions visible in Langfuse traces
```

### Integration Test

```python
# backend/tests/test_killer_workflow_e2e.py

async def test_killer_workflow():
    # 1. Upload CSV
    upload_resp = await client.post("/api/v1/files/upload-and-parse", files={"file": seed_csv})
    assert upload_resp.status_code == 200
    file_id = upload_resp.json()["file_id"]
    
    # 2. Chat: "Fit dose-response for file {file_id}"
    chat_resp = await client.post("/api/v1/chat", json={"message": f"Fit dose-response for uploaded file"})
    assert "IC50" in chat_resp.json()["message"]
    
    # 3. Chat: "Create ELN entry" → approve
    chat_resp = await client.post("/api/v1/chat", json={"message": "Create an ELN entry"})
    token = extract_approval_token(chat_resp)
    approve_resp = await client.post(f"/api/v1/chat/approve/{token}")
    assert approve_resp.status_code == 200
    
    # 4. Verify ELN exists
    eln_resp = await client.get("/api/v1/eln/")
    assert len(eln_resp.json()) > 0
    
    # 5. Chat: "Generate Echo worklist" → approve
    # ... similar pattern
```

---

## Acceptance Criteria

- [ ] Seed CSV exists at `demo-data/dose_response_staurosporine_HEK293T.csv`
- [ ] Seed data produces reproducible IC50 ~42 nM for staurosporine
- [ ] Demo script covers all 6 killer workflow steps with exact prompts
- [ ] Integration test exercises the full workflow via API calls
- [ ] Integration test passes in CI
- [ ] Single conversation can go from CSV upload to worklist download
- [ ] All artifacts (ELN entry, plate map, worklist) are persisted in database
- [ ] Full audit trail visible in Langfuse traces
- [ ] Demo completes in < 5 minutes with a cooperative LLM
