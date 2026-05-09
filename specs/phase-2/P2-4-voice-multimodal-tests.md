# SPEC: Voice + Multimodal Tests

**ID:** P2.4
**Phase:** 2 — Voice Safety
**Branch:** `test/voice-multimodal`
**Priority:** P2
**Effort:** 2-3 days
**Dependencies:** P2.1, P2.2, P2.3

---

## Problem Statement

Voice and multimodal features have been merged without dedicated test suites. Need automated verification of safety filters, provider routing, and transcription pipeline.

---

## Scope

### In Scope
- Voice safety filter unit tests
- Voice endpoint integration tests (mocked Whisper/TTS)
- Multimodal provider routing tests (both providers)
- CI coverage for voice and multimodal paths

### Out of Scope
- Live audio testing (use mocked transcription)
- Browser-based voice UI tests (Playwright)

---

## Acceptance Criteria

- [ ] Voice safety filter tests: verify each tool classification (safe/unsafe)
- [ ] Voice endpoint test: safe tool → executes, unsafe tool → redirect message
- [ ] Voice endpoint test: transcript + intent logged
- [ ] Multimodal test: image + text → correct response via OpenAI adapter
- [ ] Multimodal test: image + text → correct response via Anthropic adapter
- [ ] All tests pass in CI
- [ ] Coverage for voice and multimodal paths > 70%
