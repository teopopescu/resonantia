# ELN Entry Generator & Protocol Builder — Implementation Plan

## Context

Resonantia Lab has 5 features built (plate mapping, microscopy, samples, processing, agentic chat). Two key features from the original top-10 are missing: **ELN Entry Generator** (auto-creates structured notebook entries from experiment data) and **Protocol Builder** (step-by-step experimental protocols with inventory checks). These close the experiment lifecycle loop — from protocol design through execution to documentation.

---

## Data Models

### ELN Entry (`eln_entries` table)
- `id` (UUID PK), `created_at`, `updated_at`
- `title` (String 500)
- `entry_number` (String 64, unique, e.g. "ELN-2026-0042")
- `content_markdown` (Text — the full notebook body)
- `summary` (Text, auto-generated)
- `status` (String 32: draft | submitted | archived)
- `version` (Integer, default 1)
- `experiment_id` (FK → experiments, nullable)
- `author_id` (String — Clerk user ID)
- `embedded_figures` (JSON array: [{figure_id, caption, path}])
- `linked_references` (JSON: {samples: [uuid], plates: [uuid], experiments: [uuid]})
- `tags` (JSON array)

### ELN Appendix (`eln_appendices` table)
- `id` (UUID PK), `created_at`
- `eln_entry_id` (FK → eln_entries)
- `content_markdown` (Text)
- `author_id` (String)
- `appendix_number` (Integer, sequential)

Immutability rule: once `status = "submitted"`, the API rejects edits to `content_markdown` and only allows POST to appendices.

### Protocol (`protocols` table)
- `id` (UUID PK), `created_at`, `updated_at`
- `name` (String 255)
- `description` (Text)
- `version` (Integer, default 1)
- `status` (String 32: draft | published | archived)
- `is_template` (Boolean)
- `parent_protocol_id` (FK self → protocols, for version history)
- `author_id` (String)
- `experiment_id` (FK → experiments, nullable)
- `tags` (JSON array)

### Protocol Step (`protocol_steps` table)
- `id` (UUID PK), `created_at`, `updated_at`
- `protocol_id` (FK → protocols)
- `step_order` (Integer)
- `title` (String 255)
- `description` (Text, markdown)
- `duration_minutes` (Float)
- `temperature_celsius` (Float)
- `equipment` (String 255)
- `reagents` (JSON array: [{sample_id, name, volume, unit, concentration}])
- `parameters` (JSON dict)
- `notes` (Text)

---

## API Endpoints

### ELN (`/api/v1/eln`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/` | Create draft entry |
| GET | `/` | List entries (filter: status, experiment_id, tags) |
| GET | `/{id}` | Get entry with appendices |
| PATCH | `/{id}` | Update draft only |
| POST | `/{id}/submit` | Submit (becomes immutable) |
| POST | `/{id}/appendix` | Add appendix to submitted entry |
| POST | `/auto-generate` | Auto-generate from experiment_id |
| GET | `/{id}/export/pdf` | Export PDF |
| GET | `/{id}/export/markdown` | Export Markdown |
| DELETE | `/{id}` | Delete draft only |

### Protocols (`/api/v1/protocols`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/` | Create protocol |
| GET | `/` | List (filter: status, is_template, tags) |
| GET | `/{id}` | Get with steps |
| PATCH | `/{id}` | Update |
| POST | `/{id}/publish` | Publish (freeze version) |
| POST | `/{id}/new-version` | Clone into new version |
| GET | `/{id}/versions` | Version history |
| POST | `/{id}/steps` | Add step |
| PATCH | `/{id}/steps/{step_id}` | Update step |
| DELETE | `/{id}/steps/{step_id}` | Remove step |
| POST | `/{id}/inventory-check` | Check reagent availability |
| POST | `/dilution-calculator` | C1V1=C2V2 calculator |
| POST | `/{id}/execute` | Start execution via Temporal |
| POST | `/generate` | AI-generate protocol |

---

## Agentic Tools (8 new)

**ELN tools:**
1. `create_eln_entry` — create entry, optionally auto-generate from experiment
2. `query_eln_entries` — search by title/content/tags
3. `get_eln_entry` — get full content with appendices
4. `submit_eln_entry` — submit for audit compliance

**Protocol tools:**
5. `create_protocol` — create with AI-generated steps
6. `query_protocols` — search by name/description
7. `check_protocol_inventory` — verify reagent availability
8. `calculate_dilution` — C1V1=C2V2 calculation

---

## Frontend

### New sidebar items (after Samples, before Processing):
- Notebook (BookOpen icon) → `/lab/eln`
- Protocols (ClipboardList icon) → `/lab/protocols`

### ELN page (`/lab/eln`)
- Dashboard cards: Total Entries, Drafts, Submitted This Week
- Entry list table: Entry #, Title, Experiment, Status, Created
- Entry editor: markdown textarea with preview, figure embedding, reference linking
- Export buttons: PDF, Markdown
- Auto-generate button (select experiment → generates entry)

### Protocol page (`/lab/protocols`)
- Protocol list with version/status/template badges
- Step-by-step builder: sortable cards with reagent autocomplete from Sample inventory
- Inventory check panel: green/red availability per reagent
- Dilution calculator panel
- Version history timeline

### New Zustand stores:
- `eln-store.ts` — CRUD + autoGenerate + exportPdf + submit
- `protocol-store.ts` — CRUD + addStep/updateStep/reorderSteps + checkInventory + calculateDilution

---

## Integration with External Lab Software

### Benchling
- `POST /api/v1/eln/{id}/export/benchling` — returns JSON matching Benchling's entry creation schema
- Optional: direct API push via `services/integrations/benchling.py` if user provides Benchling API key
- Maps: title → name, content_markdown (rendered) → entry content, linked_references → entity links, figures → attachments

### LabArchives
- HTML export (LabArchives imports HTML entries)
- ELN Archive (.eln) format — RO-Crate based open standard (ZIP with JSON-LD metadata)

### LIMS (STARLIMS, LabWare)
- Abstract `LIMSIntegration` interface in `services/integrations/base.py`
- Methods: push_sample, pull_sample, push_protocol, sync_inventory
- Webhook/polling model: push on create in Resonantia, pull updates on schedule

### SiLA2 (Instrument automation)
- Phase 3: map Protocol steps with `equipment` field to SiLA2 gRPC device commands
- During Temporal protocol execution, `execute_step` activity optionally calls SiLA2 services

### Export Formats Summary
| Format | Use Case | Implementation |
|--------|----------|----------------|
| PDF | Print, archive, sharing | weasyprint from HTML/CSS |
| Markdown | Version control, plain text | Direct content_markdown field |
| Benchling JSON | Benchling ELN sync | Custom JSON mapper |
| ELN Archive (.eln) | Open standard, LabArchives | RO-Crate ZIP with JSON-LD |
| HTML | LabArchives import, email | markdown → HTML rendering |
| CSV (protocols) | Simple protocol sharing | Step table as CSV |

---

## Temporal Workflow

### ProtocolExecutionWorkflow
1. `validate_protocol_inventory` activity — check all reagents available
2. For each step: `log_step_start` → wait duration → `log_step_complete`
3. `auto_generate_eln_entry` activity — create ELN from execution log
4. Return: steps_completed, total_steps, eln_entry_id

---

## PDF Generation
- Library: weasyprint (HTML/CSS → PDF)
- Flow: content_markdown → HTML (via `markdown` library with tables/fenced_code extensions) → inject Resonantia branding CSS (amber/charcoal) → embed figures as base64 → add header (entry_number, title, author, date) and footer (page numbers) → weasyprint → PDF
- Dependencies: `weasyprint`, `markdown`

---

## Implementation Phases

### Phase 1: Data Foundation (1-2 days)
- Create models: eln_entry.py, eln_appendix.py, protocol.py (with ProtocolStep)
- Create Pydantic schemas
- Register models, run migrations
- Add seed data

### Phase 2: API Layer (2-3 days)
- ELN CRUD + submit + appendix + auto-generate + PDF export
- Protocol CRUD + steps + inventory-check + dilution-calculator
- Register routers, write tests

### Phase 3: Agentic Tools (1-2 days)
- Add 8 tool schemas to tool_registry.py
- Implement 8 handler functions in tool_executor.py
- Test via chat

### Phase 4: Temporal Workflow (1-2 days)
- ProtocolExecutionWorkflow
- New activities for step logging and ELN auto-generation
- Wire execute endpoint

### Phase 5: Frontend — ELN (2-3 days)
- eln-store.ts, /lab/eln page, editor + list components
- Sidebar navigation, skill bar entry

### Phase 6: Frontend — Protocol Builder (2-3 days)
- protocol-store.ts, /lab/protocols page
- Step builder, inventory checker, dilution calculator
- Sidebar navigation

### Phase 7: Integration Layer (2-3 days)
- Benchling export/sync
- ELN Archive (.eln) export
- HTML export for LabArchives
- Integration config in Settings

---

## Key Files to Modify
- `backend/src/resonantia/models/__init__.py` — register new models
- `backend/src/resonantia/api/router.py` — register eln + protocols routers
- `backend/src/resonantia/services/tool_registry.py` — add 8 tools to `_default_tools()`
- `backend/src/resonantia/services/tool_executor.py` — add 8 handler functions
- `backend/src/resonantia/workflows/worker.py` — register ProtocolExecutionWorkflow
- `frontend/src/components/lab/sidebar.tsx` — add Notebook + Protocols nav items
- `frontend/src/components/lab/skill-bar.tsx` — add ELN skill

## Verification
1. `uv run pytest tests/ -v` — all existing + new tests pass
2. `npm run build` — frontend compiles
3. `docker compose up --build -d` — all containers healthy
4. Chat: "Create an ELN entry for the Staurosporine experiment" → auto-generates from real DB data
5. Chat: "Design a cytotoxicity protocol for HeLa cells" → creates protocol with steps
6. Chat: "Check if we have all reagents for protocol X" → inventory check against real samples
