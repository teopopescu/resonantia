# SPEC: Multimodal Provider Unification

**ID:** P2.3
**Phase:** 2 — Voice Safety
**Branch:** `fix/multimodal-provider`
**Priority:** P2
**Effort:** 2 days
**Dependencies:** P0.1 (provider abstraction)

---

## Problem Statement

Multimodal chat (PR #10, now merged) sends images to the LLM but is hardcoded to one SDK's format. After P0.1 (provider abstraction), image content blocks must route through the provider interface so multimodal works with both OpenAI and Anthropic.

---

## Scope

### In Scope
- Route image content blocks through provider abstraction
- Support both OpenAI vision format and Anthropic vision format
- Persist image references in conversation history

### Out of Scope
- Image generation (not a feature)
- Video or audio attachments
- OCR / document parsing from images

---

## Architecture

### Message Format Normalization

```python
# Normalized (provider-agnostic):
{"role": "user", "content": [
    {"type": "text", "text": "What cells are in this image?"},
    {"type": "image", "source": {"type": "base64", "data": "...", "media_type": "image/png"}}
]}

# OpenAI adapter converts to:
{"role": "user", "content": [
    {"type": "text", "text": "What cells are in this image?"},
    {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
]}

# Anthropic adapter converts to:
{"role": "user", "content": [
    {"type": "text", "text": "What cells are in this image?"},
    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "..."}}
]}
```

---

## Acceptance Criteria

- [ ] Image attachments work with `DEFAULT_PROVIDER=openai`
- [ ] Image attachments work with `DEFAULT_PROVIDER=anthropic`
- [ ] Images persisted in conversation history (base64 or URL reference)
- [ ] Non-image attachments (CSV, PDF) still use existing `read_file_contents` tool
- [ ] Provider adapter handles image format conversion transparently
