# Resonantia

**Agentic OS for Lab Informatics**

AI-powered plate mapping, dose-response analysis, and sample tracking for lab scientists. Design worklists, browse microscopy data, and manage reagent inventory — from one intelligent interface.

[![Backend Tests](https://img.shields.io/badge/backend_tests-62_passed-brightgreen)](backend/tests/)
[![Frontend Tests](https://img.shields.io/badge/frontend_tests-46_passed-brightgreen)](frontend/src/)
[![Python](https://img.shields.io/badge/python-3.12-blue)](backend/pyproject.toml)
[![Next.js](https://img.shields.io/badge/next.js-16-black)](frontend/package.json)
[![License](https://img.shields.io/badge/license-proprietary-lightgrey)]()

---

## Features

| Feature | Description |
|---|---|
| **Agentic Chat** | 33 tools querying real PostgreSQL — ask "What plates do we have?" and get answers from your data |
| **Plate Map Designer** | Source-destination mapping with cherry-pick, serial dilution, replicate modes. Worklist export for Echo, Hamilton, Opentrons |
| **Microscopy Browser** | FOV image viewer with DAPI/GFP/mCherry channel overlay, plate-well-FOV navigation |
| **Sample Tracker** | Reagent inventory with barcode lookup, expiry alerts, storage location tracking |
| **Data Processing** | 4PL dose-response curve fitting, plate normalization (Z-score, PoC), qPCR delta-delta Ct |
| **ELN Notebook** | Markdown editor with auto-generate from experiments, PDF export, submit for immutability |
| **Protocol Builder** | Step-by-step protocols with reagent linking, inventory checker, C1V1=C2V2 dilution calculator |

## Architecture

```
Frontend (Next.js 16)     Backend (FastAPI)         Infrastructure
┌─────────────────┐      ┌──────────────────┐      ┌──────────────┐
│ Marketing site  │      │ REST API (v1)    │      │ PostgreSQL   │
│ Lab platform    │─────>│ Agent service    │─────>│ Redis        │
│ Clerk auth      │      │ Tool executor    │      │ Temporal     │
│ Zustand stores  │      │ Temporal workers │      │ Langfuse     │
└─────────────────┘      └──────────────────┘      └──────────────┘
```

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- An OpenAI API key (optional — the product works without it, chat will show a setup message)

### Run with Docker Compose

```bash
# Clone the repository
git clone git@github.com:teopopescu/resonantia.git
cd resonantia

# Create .env with your API keys (optional)
cp .env.example .env
# Edit .env to add OPENAI_API_KEY if you have one

# Start all 8 services
docker compose up -d

# Wait ~30 seconds for all services to initialize
docker compose ps
```

### Services

| Service | URL | Description |
|---|---|---|
| Frontend | http://localhost:3000 | Next.js application |
| Backend API | http://localhost:8000 | FastAPI + 32 agentic tools |
| Temporal UI | http://localhost:8080 | Workflow monitoring |
| PostgreSQL | localhost:5432 | Primary database |
| Redis | localhost:6379 | Tool registry + caching |
| Temporal | localhost:7233 | Workflow orchestration |

### Local Development (without Docker)

```bash
# Backend
cd backend
uv sync
uv run uvicorn resonantia.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Temporal (optional)
temporal server start-dev
```

## Tests

### Backend — 62 tests

```bash
cd backend && uv run pytest tests/ -v
```

| Suite | Tests | Coverage |
|---|---|---|
| Plate Mapper | 17 | Well generation, cherry-pick, serial dilution, worklist formats, validation |
| Data Processor | 11 | 4PL curve fitting, Z-score normalization, Z-prime calculation |
| Tool Registry | 8 | Schema conversion, serialization, default tools |
| API Health | 2 | Health endpoint, CORS headers |
| API Plates | 10 | CRUD, worklist generation, cherry-pick, serial dilution |
| API Samples | 6 | CRUD, barcode scan |
| Guardrails | 7 | Lab-only topic filtering, blocked patterns |

### Frontend — 46 tests

```bash
cd frontend && npx vitest run
```

| Suite | Tests | Coverage |
|---|---|---|
| Plate Utils | 16 | Well labels, coordinates, cherry-pick, serial dilution, well colors |
| Demo Data | 5 | Sample fields, unique barcodes, expiry, stock levels, types |
| Microscopy Demo | 8 | Cell generation, channel rendering, deterministic seeding |
| Lab Store | 6 | Tasks, messages, sidebar, pending prompts |
| Sample Store | 5 | CRUD, filters, initial state |

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS, Zustand, Framer Motion |
| Backend | Python 3.12, FastAPI, Pydantic, SQLAlchemy (async) |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Workflows | Temporal |
| LLM | OpenAI GPT-4o (32 agentic tools) |
| Auth | Clerk (invite-only, Google OAuth) |
| CMS | Contentful (blog) |
| Tracing | Langfuse |
| Evals | RAGAS |
| Containerization | Docker Compose (8 services) |

## Agentic Tools (32)

The chat agent has access to 33 tools across 7 categories, all querying the real database:

| Category | Tools |
|---|---|
| **Plate Mapping** (5) | create_plate_map, generate_worklist, cherry_pick, serial_dilution, get_plate_map_details |
| **Data Processing** (5) | fit_dose_response, normalize_plate, calculate_z_prime, qpcr_analysis, get_processing_results |
| **Sample Management** (3) | lookup_sample, check_inventory, add_sample |
| **ELN** (4) | create_eln_entry, query_eln_entries, get_eln_entry, submit_eln_entry |
| **Protocol** (4) | create_protocol, query_protocols, check_protocol_inventory, calculate_dilution |
| **Microscopy** (2) | browse_microscopy, generate_montage |
| **General** (9) | query_experiments, get_ic50_values, get_expiring_samples, get_sample_stats, list_files, get_file_info, query_plate_maps, search_literature, design_protocol |

## Project Structure

```
resonantia/
├── frontend/                  # Next.js 16 application
│   ├── src/
│   │   ├── app/              # Pages (marketing + lab platform)
│   │   ├── components/       # React components
│   │   ├── stores/           # Zustand state management
│   │   └── lib/              # Utilities, API client, demo data
│   └── Dockerfile
├── backend/                   # FastAPI application
│   ├── src/resonantia/
│   │   ├── api/              # REST endpoints
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic + integrations
│   │   └── workflows/        # Temporal workflow definitions
│   ├── tests/                # pytest test suite
│   └── Dockerfile
├── docs/                      # Architecture, plans, testing scenarios
├── docker-compose.yml         # All 8 services
└── .env.example              # Environment variable template
```

## Documentation

| Document | Description |
|---|---|
| [Architecture](docs/architecture.md) | System design and data flow |
| [Tools Reference](docs/tools.md) | All 32 agentic tools with parameters |
| [Testing Scenarios](docs/testing-scenarios.md) | Persona-based QA test plans |
| [Production Plan](docs/production-plan.md) | Deployment roadmap (Vercel + AWS) |
| [Multi-Tenancy Plan](docs/multi-tenancy-plan.md) | Org-based data isolation design |
| [Integrations Plan](docs/integrations-plan.md) | External lab software integration framework |
| [Commercial Integrations](docs/commercial-integrations.md) | Benchling, Dotmatics, LabWare partnership requirements |
| [ELN + Protocol Plan](docs/eln-protocol-plan.md) | ELN and Protocol Builder feature design |

## Environment Variables

```env
# Required for AI chat (optional — product works without it)
OPENAI_API_KEY=sk-...

# Langfuse tracing (optional)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# Clerk authentication
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...

# Contentful blog
NEXT_PUBLIC_CONTENTFUL_SPACE_ID=...
NEXT_PUBLIC_CONTENTFUL_ACCESS_TOKEN=...
```

See `.env.example` for the full list.

## Author

**Teodor Popescu** — [GitHub](https://github.com/teopopescu)

---

*Resonantia — Agentic OS for Lab Informatics*
