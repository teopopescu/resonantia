# SPEC: Voice Safety Scope

**ID:** P2.1
**Phase:** 2 — Voice Safety
**Branch:** `feat/voice-safety-scope`
**Priority:** P2
**Effort:** 3 days
**Dependencies:** Phase 0 complete

---

## Problem Statement

Voice push-to-talk is in main but has no safety filter. A scientist wearing gloves could accidentally trigger destructive actions (submit ELN, delete samples, send worklist to instrument) via voice without visual confirmation. Per codex-findings/02: "Voice and agents should be the primary interaction layer, but not the source of truth or safety boundary."

---

## Scope

### In Scope
- Classify all tools as voice-safe or voice-unsafe
- Filter tool calls through safety check in voice endpoint
- Redirect unsafe actions to text confirmation
- Log voice transcripts and interpreted intents

### Out of Scope
- Lab vocabulary correction / custom ASR (deferred)
- Wake word detection
- Multi-turn voice conversations

---

## Architecture

### Tool Voice Safety Classification

| Safe (execute via voice) | Unsafe (redirect to text) |
|-------------------------|--------------------------|
| `lookup_sample`, `check_inventory`, `get_expiring_samples` | `submit_eln_entry` |
| `query_experiments`, `query_eln_entries`, `query_protocols` | `generate_worklist` (instrument-bound) |
| `calculate_dilution`, `get_ic50_values` | Any delete operation |
| `browse_microscopy` | `create_eln_entry` (redirect to draft) |
| `read_file_contents` | `create_plate_map` (redirect to draft) |
| `fit_dose_response`, `normalize_plate`, `calculate_z_prime`, `qpcr_analysis` | Reorder reagents |

### Safety Filter

```python
VOICE_SAFE_TOOLS = {
    "lookup_sample", "check_inventory", "get_expiring_samples",
    "query_experiments", "query_eln_entries", "query_protocols",
    "calculate_dilution", "get_ic50_values", "browse_microscopy",
    "read_file_contents", "fit_dose_response", "normalize_plate",
    "calculate_z_prime", "qpcr_analysis", "get_plate_map_details",
}

def is_voice_safe(tool_name: str) -> bool:
    return tool_name in VOICE_SAFE_TOOLS

# In voice endpoint: when LLM selects an unsafe tool
# → Do NOT execute
# → Return: "This action requires text confirmation. I've drafted it for you — please confirm in the chat."
```

---

## Acceptance Criteria

- [ ] All tools classified as voice-safe or voice-unsafe
- [ ] Voice endpoint filters tool calls through `is_voice_safe()`
- [ ] Voice "look up sample ABC-001" → executes, returns result via TTS
- [ ] Voice "submit the ELN entry" → blocked, redirected to text with draft
- [ ] Voice "delete sample" → blocked, redirected to text
- [ ] Voice transcript + interpreted intent logged for every voice interaction
- [ ] No destructive action can be triggered without visual confirmation
