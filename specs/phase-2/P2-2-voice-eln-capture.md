# SPEC: Voice-to-ELN Capture Flow

**ID:** P2.2
**Phase:** 2 — Voice Safety
**Branch:** `feat/voice-eln-capture`
**Priority:** P2
**Effort:** 3-4 days
**Dependencies:** P2.1 (voice safety), P1.0 (approval gates)

---

## Problem Statement

Scientists at the bench (gloves on, hands busy) need to capture observations without touching a keyboard. "Record observation: Cell confluence at 80%, passage 12, morphology normal" should become a structured ELN draft that they review later.

This is the hero workflow from the landing page and codex-findings/06: "Voice capture → Agent parsing → ELN draft → Confirmation → Sync."

---

## Scope

### In Scope
- Voice dictation → structured ELN draft
- Agent extracts structured fields from free-form speech
- Draft presented via approval gate (not auto-created)
- Voice response confirms: "Draft saved. Review in your notebook when ready."

### Out of Scope
- Real-time transcription display (use existing Whisper pipeline)
- ELN sync to eLabFTW (Phase 3)
- Multi-turn voice editing of the draft

---

## Architecture

### Flow

```
Scientist (holding Space):
  "Record observation for experiment alpha-7: Cell confluence at 80 percent,
   passage 12, morphology looks normal, some debris in wells B3 and C5,
   pH 7.35, started drug treatment at 10 micromolar"

→ Whisper STT → transcript text
→ Agent parses → extracts:
    experiment_ref: "alpha-7"
    observations:
      - confluence: 80%
      - passage: 12
      - morphology: normal
      - debris: wells B3, C5
      - pH: 7.35
      - treatment: drug, 10 μM
→ Agent calls create_eln_entry (gate: soft_review)
→ Returns draft with structured content
→ TTS: "Draft observation recorded for experiment alpha-7. Review in your notebook."
→ Approval card appears in chat (user reviews later at desk)
```

---

## Acceptance Criteria

- [ ] Voice dictation creates structured ELN draft with parsed fields
- [ ] Draft appears as approval card in chat (not auto-created)
- [ ] Voice response confirms draft creation via TTS
- [ ] Structured fields extracted: experiment reference, numeric values, well positions, units
- [ ] User can review and confirm/edit/cancel the draft in the chat UI
- [ ] Works with the existing push-to-talk UI (Space bar)
