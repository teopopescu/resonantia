# Resonantia Architecture

## System Overview (post-Phase 0 stabilization)

```
  Browser ──► Next.js 16 (Clerk Auth) ──► FastAPI (Python 3.12)
                :3000                        :8000
                                               │
              ┌────────────────────────────────┼──────────────────────┐
              │                                │                      │
         ┌────▼─────┐    ┌────────────┐  ┌────▼──────┐   ┌─────────┐
         │PostgreSQL │    │   Redis    │  │  LLM      │   │Temporal │
         │   16      │    │    7       │  │ Provider  │   │         │
         │           │    │            │  │           │   │ Durable │
         │- Convos   │    │- Tool      │  │ OpenAI    │   │ tool    │
         │- Samples  │    │  schemas   │  │ Anthropic │   │ calls   │
         │- Plates   │    │- Cache     │  │           │   │         │
         │- ELN      │    │            │  │ Langfuse  │   │ 30s     │
         │- Protocols│    │            │  │ traced    │   │ timeout │
         │- Expts    │    │            │  │           │   │         │
         └──────────┘    └────────────┘  └───────────┘   └─────────┘
```

## Key Architectural Decisions (Phase 0)

### LLM Provider Abstraction (`services/llm/`)
All LLM calls route through a thin provider interface. OpenAI and Anthropic adapters normalize tool schemas, message formats, and responses. Per-agent model assignment via config. Direct SDK usage only in `api/voice.py` for STT/TTS.

### Temporal Architecture
Two components, often confused:
- **Temporal Server** (managed): Stores workflow state, manages task queues, handles retries. Use Temporal Cloud in production — no self-hosting required. The docker-compose includes a self-hosted server for local dev only.
- **Temporal Worker** (your code, ECS): Runs `AgentToolCallWorkflow` and activity implementations (`call_llm_activity`, `execute_tool_activity`, `persist_conversation_activity`). Always runs in your infrastructure because it needs access to your DB, LLM keys, and tool executor. Polls Temporal Cloud for tasks.

The workflow is a durable version of the same tool-calling loop as direct mode. No generated code, no subprocess execution. Each tool call is an individually retriable activity with 30s timeout. Temporal unavailability falls back to direct mode.

### Tenant Isolation
- `org_id` derived from `X-Org-Id` header (Clerk session), never from request body
- Every DB query filters by `org_id`
- Conversation loading checks `conv.org_id == caller's org_id`
- File registry scoped by `org_id`
- Cross-org access returns 403

### Output Guardrails (`services/output_validator.py`)
3-step validation before tool execution: (1) schema validation against registered JSON schema, (2) cross-tenant entity reference check, (3) execute with system-error masking. Typed `ToolResult`/`ToolError` envelopes replace raw JSON strings.

### Demo Mode (`lib/demo-mode.ts`)
Explicit flag (`NEXT_PUBLIC_DEMO_MODE`) or backend health probe. Amber banner when active. Failed writes show error toasts instead of silently persisting locally.

## Data Flow

```
  User message (text/voice/image)
       │
       ▼
  Frontend (Zustand stores + React Query)
       │ POST /api/v1/chat/message
       ▼
  Chat endpoint (org_id from Depends)
       │
       ├── Try Temporal (AgentToolCallWorkflow)
       │     └── Activity: call_llm → tool_calls? → execute_tool → loop
       │
       └── Fallback: direct mode (agent_router.chat)
             └── LLM provider → tool calls → tool_executor → loop
       │
       ▼
  Tool executor (validate → check tenant → execute → audit)
       │
       ▼
  PostgreSQL (persist) + Langfuse (trace) + Redis (cache)
```

## Feature Modules

| Module | Status | Tools |
|--------|--------|-------|
| Plate Mapping | GA | create_plate_map, cherry_pick, serial_dilution, generate_worklist, get_plate_map_details |
| Data Processing | GA | fit_dose_response, normalize_plate, calculate_z_prime, qpcr_analysis |
| Sample Tracker | GA | lookup_sample, check_inventory, get_expiring_samples, get_ic50_values |
| ELN | GA | create_eln_entry, query_eln_entries, submit_eln_entry |
| Protocol Builder | GA | create_protocol, query_protocols, check_protocol_inventory, calculate_dilution |
| Agent Console | BETA | 33 tools across 7 categories, voice mode, multi-agent topology |
| Microscopy | PREVIEW | browse_microscopy, generate_montage (partner-triggered only) |

## Test Coverage

- Backend: 140+ tests (pytest)
- Frontend: 53 tests (vitest)
- CI: GitHub Actions, strict markers, merge-blocking
