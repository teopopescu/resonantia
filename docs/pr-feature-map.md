# Resonantia — PR & Feature Map

_Last updated: 2026-04-15_

## All Pull Requests

| PR | Branch | Base | State | Description |
|---|---|---|---|---|
| [#1](https://github.com/teopopescu/resonantia/pull/1) | `feat/aws-terraform-ci` | `main` | OPEN | AWS Terraform infrastructure and GitHub Actions CI/CD |
| [#2](https://github.com/teopopescu/resonantia/pull/2) | `feat/voice-feature` | `main` | MERGED | Voice mode — speech-to-speech chained pipeline |
| [#3](https://github.com/teopopescu/resonantia/pull/3) | `feat/multi-tenancy` | `main` | OPEN | Multi-tenancy and conversation history |
| [#4](https://github.com/teopopescu/resonantia/pull/4) | `feat/ui-polish-integrations` | `main` | OPEN | Integration cards, @ mentions, feature requests, anonymised testimonials |
| [#5](https://github.com/teopopescu/resonantia/pull/5) | `feat/mcp-experiment-agent-skills` | `feat/ui-polish-integrations` | OPEN | MCP server, experiment design agent, thinking trace, Claude Code skills |

---

## Feature Breakdown by PR

### PR #1 — AWS Terraform Infrastructure (`feat/aws-terraform-ci`)

- Terraform modules: VPC, RDS (PostgreSQL), ElastiCache (Redis), ECS (Fargate), ALB, S3
- GitHub Actions CI/CD pipeline
- Environment configuration for staging and production
- Estimated AWS cost: ~$130-350/month

### PR #2 — Voice Mode (`feat/voice-feature`) — MERGED

- Full voice-to-voice pipeline: Whisper STT → Claude agent → OpenAI TTS
- Voice Activity Detection (VAD) with energy-based silence detection (1.5s threshold)
- Waveform visualization in the UI
- Hands-free lab access with all 32 agentic tools available via voice
- Audio recording in WebM/MP3, served via `/api/v1/voice/audio/{audio_id}`
- Voice mode component with states: Listening → Silence → Transcribing → Thinking → Speaking

### PR #3 — Multi-Tenancy & Conversation History (`feat/multi-tenancy`)

- Row-level data isolation via `org_id` column on all database tables
- `get_org_context` FastAPI dependency extracting org from request headers
- Conversation persistence: `Conversation` + `ConversationMessage` models in PostgreSQL
- Conversation sidebar: list, search, rename, delete conversations
- Clerk Organizations integration with org switcher
- "No access" page for users without an organization
- Fallback to `org_default` for single-tenant/demo mode

### PR #4 — UI Polish & Integrations (`feat/ui-polish-integrations`)

- Integration logos and "coming soon" cards (eLabFTW, Benchling, Dotmatics)
- @ mentions system in chat (target integrations and resources)
- Feature request page with AWS SES email notifications
- Anonymised testimonials on marketing site
- File analysis tools: upload CSV, XLSX, TSV, FCS, TIFF, PNG for agent analysis
- Data processing handlers wired to real backend services
- Demo data seeding on startup
- PR merge order and AWS deployment plan documentation

### PR #5 — MCP Server, Experiment Design Agent, Thinking Trace (`feat/mcp-experiment-agent-skills`)

**Resonantia MCP Server (FastMCP)**
- 15 MCP tools exposing Resonantia capabilities via Model Context Protocol
  - Plate Mapping: create_plate_map, cherry_pick, serial_dilution, generate_worklist, get_plate_map_details
  - Data Processing: fit_dose_response, normalize_plate, calculate_z_prime, qpcr_analysis
  - Sample Management: lookup_sample, check_inventory, get_expiring_samples
  - Experiments: query_experiments, get_ic50_values
  - ELN: create_eln_entry, query_eln_entries
  - Protocols: create_protocol, calculate_dilution
- 8 MCP resources for read-only data access (experiments, samples, plate maps, ELN, protocols)
- Configurable org_id via `RESONANTIA_ORG_ID` environment variable
- Runnable via `python -m resonantia.mcp_server` or `fastmcp run resonantia.mcp_server:mcp`

**Experiment Design Agent (Closed-Loop Lab OS)**
- `ExperimentDesigner` class with three methods:
  - `analyze_results()` — Z-prime QC, hit identification (IC50 < 10 µM), poor fit flagging (R² < 0.9, |Hill slope| > 2), out-of-range detection
  - `recommend_followup()` — tighter dilution series for hits, retests for poor fits, control recommendations, plate format selection (384-well if >20 compounds)
  - `generate_followup_plate()` — creates actual plate map + worklist from recommendation
- Registered as `design_next_experiment` agentic tool
- Closes the loop: results → analysis → recommendation → plate design → execution

**Thinking Trace UI**
- Collapsible "Used N tools" indicator above assistant messages
- Numbered tool steps with friendly labels (e.g. "Fitting dose-response curve")
- Expandable parameters view for each tool call
- Works for both live queries and loaded conversation history
- Loading state: spinning icon with "Thinking..." instead of bouncing dots

**Bug Fixes**
- Conversation fetching: frontend called `/conversations/{id}/messages` (404) → fixed to `/conversations/{id}`
- Pydantic schema: `tool_calls: dict | None` → `list | dict | None` (500 error on conversations with tool calls)

**Claude Code Skills & Hooks**
- 6 developer skills: `/add-tool`, `/check-lab`, `/test-tool`, `/seed-data`, `/deploy`, `/start-mcp`
- PostToolUse hook: auto-lint Python files with ruff on edit
- MCP server config in `.claude/settings.json`

**Business Strategy Documents**
- `docs/critical-path-seed.md` — 24-month timeline to $1M ARR, seed round targets ($2.5-3.5M)
- `docs/pricing-restructure.md` — Per-lab tiers replacing per-seat pricing
- `docs/product-gaps-must-have.md` — Enterprise blockers and PMF features
- `docs/market-analysis-targets.md` — Recursion (customer) and Automata (partner) analysis
- `docs/strategy-closed-loop-lab-os.md` — Closed-loop positioning aligned with BVP thesis

---

## Merge Order

```
1. PR #3 (multi-tenancy)           → main     [foundational — org_id scoping]
2. PR #4 (UI polish/integrations)  → main     [features on multi-tenant foundation]
3. PR #5 (MCP/agent/skills)        → PR #4    [then flows to main with PR #4]
4. PR #1 (AWS Terraform)           → main     [infrastructure — independent of app code]
```

PR #2 (voice mode) is already merged into main.

---

## Cumulative Feature Count

| Category | Features |
|---|---|
| **Core AI** | Agentic chat (32 tools), voice mode, experiment design agent, thinking trace |
| **Lab Tools** | Plate mapper, worklist export (Echo/Hamilton/Opentrons), data processing (IC50, Z-prime, qPCR), microscopy browser, sample inventory, ELN, protocol builder |
| **Platform** | Multi-tenancy, conversation history, file upload/analysis, @ mentions, feature requests |
| **Integrations** | eLabFTW (implemented), Benchling/Dotmatics (framework), MCP server (15 tools) |
| **Infrastructure** | AWS Terraform, Docker Compose, CI/CD, Temporal workflows |
| **Developer Tools** | 6 Claude Code skills, ruff auto-lint hook, MCP config |
| **Business** | Pricing model, critical path, market analysis, product gaps, strategy docs |
