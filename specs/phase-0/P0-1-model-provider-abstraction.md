# SPEC: Model Provider Abstraction

**ID:** P0.1
**Phase:** 0 — Stabilize
**Branch:** `fix/model-provider-abstraction`
**Priority:** P0
**Effort:** 5-6 days
**Dependencies:** P0.5 (test baseline)

---

## Problem Statement

The codebase has a "split-brain" LLM provider configuration:
- `services/agent.py:56-58` instantiates `AsyncOpenAI` directly and uses OpenAI chat-completions tool calling format
- `workflows/activities.py:58-128` instantiates `AsyncAnthropic` directly and uses Anthropic messages format
- `config.py:28-29` only declares `openai_api_key` and `llm_model: gpt-4o`; Anthropic settings referenced in activities don't exist
- Multi-agent specialists (now merged) inherit whichever provider their parent file uses

This means: the Temporal path crashes on startup (references nonexistent config), switching providers requires code changes (not config), and Langfuse tracing is inconsistent.

---

## Scope

### In Scope
- Create a thin provider interface wrapping both OpenAI and Anthropic SDKs
- Migrate agent.py, activities.py, and multi-agent specialists to use the interface
- Add provider config (which model for which agent role)
- Maintain Langfuse tracing through the abstraction
- Handle tool-call format differences (OpenAI function calling vs Anthropic tool_use)

### Out of Scope
- LiteLLM (unnecessary complexity for 2 providers)
- Voice STT/TTS (keep direct OpenAI — not an LLM routing concern)
- Self-hosted vLLM (deferred post-pilot)
- Automatic failover between providers (nice-to-have, not P0)

---

## Architecture

### Provider Interface Design

```python
# backend/src/resonantia/services/llm/provider.py

from typing import AsyncIterator
from pydantic import BaseModel

class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict

class LLMResponse(BaseModel):
    content: str | None
    tool_calls: list[ToolCall]
    model: str
    input_tokens: int
    output_tokens: int

class LLMProvider:
    """Thin wrapper that normalizes OpenAI and Anthropic into one interface."""
    
    async def completion(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse: ...
    
    async def completion_stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str | ToolCall]: ...
```

### Message Format Normalization

The interface accepts messages in a normalized format (OpenAI-style `role/content` dicts). Internally:
- For OpenAI: pass through as-is
- For Anthropic: convert to Anthropic message format (system prompt separate, tool_use blocks)

### Tool Schema Normalization

Tools are stored in Redis as provider-agnostic JSON Schema. The provider converts:
- For OpenAI: wrap in `{"type": "function", "function": {"name": ..., "parameters": ...}}`
- For Anthropic: use `{"name": ..., "input_schema": ...}` format

### Configuration

```python
# backend/src/resonantia/config.py (additions)

class Settings(BaseSettings):
    # Existing
    openai_api_key: str = ""
    llm_model: str = "gpt-4o"
    
    # New
    anthropic_api_key: str = ""
    default_provider: str = "anthropic"  # "openai" | "anthropic"
    
    # Per-role model assignment
    planner_model: str = "claude-sonnet-4-20250514"
    specialist_model: str = "claude-sonnet-4-20250514"
    critic_model: str = "claude-haiku-4-5-20251001"
```

### File Changes

```
NEW:  backend/src/resonantia/services/llm/__init__.py
NEW:  backend/src/resonantia/services/llm/provider.py
NEW:  backend/src/resonantia/services/llm/openai_adapter.py
NEW:  backend/src/resonantia/services/llm/anthropic_adapter.py
MODIFY: backend/src/resonantia/services/agent.py
MODIFY: backend/src/resonantia/workflows/activities.py
MODIFY: backend/src/resonantia/services/multi_agent/orchestrator.py
MODIFY: backend/src/resonantia/services/multi_agent/specialists/*.py
MODIFY: backend/src/resonantia/services/multi_agent/critic.py
MODIFY: backend/src/resonantia/config.py
MODIFY: backend/src/resonantia/services/tracing.py
NEW:  backend/tests/test_llm_provider.py
```

---

## Implementation

### Step 1: Create provider interface (day 1)
- Write `LLMProvider` class with `completion()` and `completion_stream()`
- Write `OpenAIAdapter` that wraps `AsyncOpenAI`
- Write `AnthropicAdapter` that wraps `AsyncAnthropic`
- Factory: `get_provider(provider_name: str) -> LLMProvider`

### Step 2: Handle format differences (day 2)
- Tool call response normalization (OpenAI `function_call` → `ToolCall`, Anthropic `tool_use` → `ToolCall`)
- Tool schema format conversion per provider
- Streaming: normalize SSE chunks from both providers into `str | ToolCall` iterator

### Step 3: Migrate agent.py (day 3)
- Replace `self.client = AsyncOpenAI()` with `self.provider = get_provider(settings.default_provider)`
- Replace `self.client.chat.completions.create(...)` with `self.provider.completion(...)`
- Update tool schema loading to use provider-agnostic format
- Wire Langfuse span around provider calls

### Step 4: Migrate activities.py + multi-agent (day 4)
- Delete direct `AsyncAnthropic` instantiation
- Delete references to nonexistent `settings.anthropic_api_key` / `settings.anthropic_model`
- All multi-agent specialists get provider via injection, not direct SDK import
- Per-specialist model assignment from config (`critic_model`, `specialist_model`)

### Step 5: Tests + config (day 5)
- Unit tests with mocked provider responses
- Test that switching `DEFAULT_PROVIDER` changes which SDK is called
- Test tool schema format conversion for both providers
- Update `.env.example` with new config fields

---

## Expected Behavior

| Scenario | Before | After |
|----------|--------|-------|
| `DEFAULT_PROVIDER=openai` | Works (agent.py uses OpenAI directly) | Works (routed through provider) |
| `DEFAULT_PROVIDER=anthropic` | Crashes (activities.py refs missing config) | Works (routed through provider) |
| Add a new model provider | Requires code changes in multiple files | Add one adapter file + config entry |
| Langfuse trace for chat | Shows OpenAI call only | Shows model, provider, tokens, latency regardless of provider |
| Multi-agent specialist call | Uses whatever SDK the file imported | Uses model from config (critic_model, specialist_model) |

---

## Acceptance Criteria

- [ ] No direct `AsyncOpenAI()` or `AsyncAnthropic()` instantiation outside `services/llm/` (exception: voice.py for STT/TTS)
- [ ] `grep -r "AsyncOpenAI\|AsyncAnthropic" backend/src/resonantia/services/ backend/src/resonantia/workflows/` returns only `services/llm/` matches + voice.py
- [ ] Setting `DEFAULT_PROVIDER=anthropic` in `.env` routes all chat/tool calls through Anthropic
- [ ] Setting `DEFAULT_PROVIDER=openai` routes through OpenAI
- [ ] Multi-agent specialists use model from config (`specialist_model`, `critic_model`)
- [ ] Langfuse traces show: model name, provider, input_tokens, output_tokens, latency for every LLM call
- [ ] `backend/tests/test_llm_provider.py` covers: completion, tool_call, streaming, format conversion
- [ ] All existing backend tests pass without modification (or with minimal fixture updates)
- [ ] Temporal path no longer crashes on startup with `DEFAULT_PROVIDER=anthropic`

---

## Risks

- **Tool call format differences are subtle.** OpenAI returns `arguments` as a JSON string; Anthropic returns `input` as a dict. The adapter must handle both consistently.
- **Streaming format differs significantly.** OpenAI uses `delta.tool_calls[0].function.arguments` chunks; Anthropic uses `content_block_delta` with `input_json_delta`. Normalizing streams is the hardest part.
- **Multi-agent code was merged without source review.** The `.pyc` files were committed; source may have import assumptions that break when provider changes.
- **Token counting differs.** OpenAI reports usage in response; Anthropic reports in message_stop event. Both must be captured for Langfuse.
