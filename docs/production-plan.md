# Resonantia — Production Readiness Plan

## Current State Summary

The product has a complete UI, backend API structure, Temporal workflows, tool registry, guardrails, Langfuse tracing, RAGAS evals, Clerk auth, and Contentful blog. However, the frontend and backend are not fully connected — the frontend uses local Zustand state with hardcoded demo data instead of calling backend APIs.

**Deployment targets:**
- Frontend: Vercel
- Backend: AWS (ECS/EKS)
- Database: AWS RDS (PostgreSQL)
- Cache: AWS ElastiCache (Redis)
- Workflow engine: Temporal Cloud or self-hosted on EKS
- File storage: AWS S3

---

## Inventory of All Simulations / Demo Data / Dummy Functionality

### FRONTEND — 8 items

| # | File | What's Simulated | What It Should Do |
|---|------|------------------|-------------------|
| F1 | `src/components/lab/chat-interface.tsx:300-306` | `setTimeout` returns hardcoded "This is a demo response" | Call `POST /api/v1/chat/message`, stream response, show typing indicator |
| F2 | `src/stores/sample-store.ts:35` | Initializes with `DEMO_SAMPLES` (22 hardcoded samples), all CRUD is local-only | Fetch from `GET /api/v1/samples` on mount, persist via API |
| F3 | `src/stores/plate-store.ts:102-210` | Hardcoded source plates + 3 demo plate maps, local-only state | Fetch from `GET /api/v1/plates`, persist via API |
| F4 | `src/stores/lab-store.ts:43-62` | 3 hardcoded default tasks | Fetch from backend or start empty |
| F5 | `src/app/lab/processing/page.tsx:421-444` | `setTimeout` fakes 2-second analysis, generates random results | Call `POST /api/v1/processing/{type}` with real data, display real results |
| F6 | `src/lib/microscopy-demo.ts` | Entire module generates synthetic canvas microscopy images | Display real uploaded images from `GET /api/v1/microscopy/images/{id}` |
| F7 | `src/components/lab/worklist-generator.tsx` | Client-side worklist generation only | Call `POST /api/v1/plates/{id}/worklist` and download the real file |
| F8 | `src/lib/demo-data.ts` | 22 samples + 6 plates used as fallback data | Keep as seed data for empty databases, but primary source should be API |

### BACKEND — 7 items

| # | File | What's Simulated | What It Should Do |
|---|------|------------------|-------------------|
| B1 | `src/resonantia/workflows/activities.py:458-487` | `run_processing()` returns hardcoded None/empty for dose-response, normalization, qPCR | Call `data_processor.fit_dose_response()`, `normalize_plate()` — implementations exist |
| B2 | `src/resonantia/workflows/activities.py:343-356` | Cherry-pick and serial-dilution modes fall through to direct copy | Call `plate_mapper.cherry_pick()`, `plate_mapper.serial_dilution()` — implementations exist |
| B3 | `src/resonantia/workflows/activities.py:421` | `save_plate_map()` generates fake UUID, doesn't persist | Save to PostgreSQL via SQLAlchemy models |
| B4 | `src/resonantia/workflows/activities.py:520` | `save_results()` generates fake UUID, doesn't persist | Save to PostgreSQL via SQLAlchemy models |
| B5 | `src/resonantia/workflows/activities.py:503` | `generate_figures()` returns fake figure key | Use matplotlib to generate real plots, save to S3/local |
| B6 | `src/resonantia/workflows/activities.py:434` | `load_experiment_data()` returns empty dict | Query PostgreSQL for real experiment data |
| B7 | `src/resonantia/workflows/activities.py:279` | `validate_source_plates()` always returns valid | Query database to verify plates exist |

---

## Implementation Plan

### Phase 1: Core Wiring (Chat + API Integration)

**Priority: Critical — the product is unusable without these**

#### 1.1 Wire chat to real Claude API
- **File:** `frontend/src/components/lab/chat-interface.tsx`
- **Change:** Replace `setTimeout` demo response with `fetch(POST /api/v1/chat/message)`
- **Add:** `isLoading` state, typing indicator (animated dots), error handling
- **Add:** Streaming support via SSE (`/api/v1/chat/message/stream`) for real-time token output
- **Dependency:** `ANTHROPIC_API_KEY` must be set in backend `.env`
- **Effort:** Small

#### 1.2 Wire sample store to backend API
- **File:** `frontend/src/stores/sample-store.ts`
- **Change:** Add `fetchSamples()`, `createSample()`, `updateSample()`, `deleteSample()` that call `/api/v1/samples`
- **Keep:** `DEMO_SAMPLES` as seed data when database is empty (backend should seed on first run)
- **Add:** `loading`, `synced`, `error` state
- **Effort:** Small

#### 1.3 Wire plate store to backend API
- **File:** `frontend/src/stores/plate-store.ts`
- **Change:** Add `fetchPlateMaps()`, `createPlateMap()`, `savePlateMap()` calling `/api/v1/plates`
- **Keep:** Demo source plates as initial data
- **Effort:** Small

#### 1.4 Wire processing page to backend API
- **File:** `frontend/src/app/lab/processing/page.tsx`
- **Change:** `handleRunAnalysis()` calls `POST /api/v1/processing/dose-response` (or normalization/qpcr) with the form data
- **Change:** Upload file first via `/api/v1/files/upload`, then pass file reference to processing
- **Change:** Display real results (IC50, Z-prime, fold changes) instead of random names
- **Effort:** Medium

#### 1.5 Wire worklist export to backend API
- **File:** `frontend/src/components/lab/worklist-generator.tsx`
- **Change:** "Echo CSV" / "Hamilton GWL" / "Opentrons Python" buttons call `POST /api/v1/plates/{id}/worklist`
- **Change:** Download the response as a file (blob download)
- **Keep:** Client-side generation as fallback
- **Effort:** Small

### Phase 2: Backend Activity Wiring

**Priority: High — makes Temporal workflows functional**

#### 2.1 Wire processing activities to real services
- **File:** `backend/src/resonantia/workflows/activities.py`
- **Change:** `run_processing()` calls `data_processor.fit_dose_response()` for dose_response type
- **Change:** Calls `data_processor.normalize_plate()` for plate_normalization type
- **Change:** Implements real delta-delta Ct for qpcr type
- **Effort:** Small — implementations already exist in `services/data_processor.py`

#### 2.2 Wire plate mapping activities
- **File:** `backend/src/resonantia/workflows/activities.py`
- **Change:** Cherry-pick mode calls `plate_mapper.cherry_pick()`
- **Change:** Serial-dilution mode calls `plate_mapper.serial_dilution()`
- **Change:** `generate_worklist()` calls `plate_mapper.generate_worklist()`
- **Effort:** Small — implementations exist in `services/plate_mapper.py`

#### 2.3 Wire persistence activities
- **File:** `backend/src/resonantia/workflows/activities.py`
- **Change:** `save_plate_map()` creates a PlateMap row via SQLAlchemy
- **Change:** `save_results()` updates Experiment.results via SQLAlchemy
- **Change:** `load_experiment_data()` queries Experiment by ID
- **Change:** `validate_source_plates()` queries PlateMap table
- **Effort:** Medium — needs async DB session in activity context

#### 2.4 Add figure generation
- **File:** `backend/src/resonantia/workflows/activities.py`
- **Dependency:** `uv add matplotlib`
- **Change:** `generate_figures()` uses matplotlib to plot dose-response curves, normalization distributions
- **Change:** Save PNG to uploads directory, return file path
- **Effort:** Medium

### Phase 3: Microscopy

**Priority: Medium — works visually but uses synthetic data**

#### 3.1 Real microscopy image display
- **File:** `frontend/src/lib/microscopy-demo.ts` → keep for empty-state demo
- **File:** `frontend/src/components/lab/microscopy-viewer.tsx`
- **Change:** When real images exist (uploaded via `/api/v1/microscopy/upload`), display them instead of synthetic ones
- **Change:** Fetch image list from `GET /api/v1/microscopy/images?plate_id=X&well=Y&channel=Z`
- **Keep:** Synthetic fallback when no real images uploaded
- **Effort:** Medium

### Phase 4: Database Seeding

**Priority: Medium — good first-run experience**

#### 4.1 Backend seed command
- **File:** Create `backend/src/resonantia/seed.py`
- **Purpose:** Seed the database with the demo samples, plates, and experiments on first run
- **Change:** Move `DEMO_SAMPLES` data to a backend seed script that creates real DB rows
- **When:** Run automatically when database is empty (check in lifespan)
- **Effort:** Small

### Phase 5: Deployment Preparation

**Priority: Required for Vercel + AWS deploy**

#### 5.1 Vercel frontend deployment
- **File:** `frontend/next.config.ts`
- **Change:** Add output config, environment variable handling for production API URL
- **Change:** Ensure all API calls use `NEXT_PUBLIC_API_URL` (already done)
- **Add:** Vercel-specific build config if needed
- **Effort:** Small

#### 5.2 AWS backend deployment
- **Files:** Create `infrastructure/` directory with Terraform
- **Create:** ECS task definition for backend (or EKS deployment)
- **Create:** RDS PostgreSQL instance
- **Create:** ElastiCache Redis cluster
- **Create:** S3 bucket for file uploads and microscopy images
- **Create:** ALB for backend API
- **Create:** ECR repository for backend Docker image
- **Change:** Backend Dockerfile already exists, may need production optimizations
- **Effort:** Large

#### 5.3 Temporal deployment
- **Options:**
  - A) Temporal Cloud (managed, recommended for production)
  - B) Self-hosted Temporal on EKS
  - C) For demo: Temporal dev server (current setup)
- **Change:** Backend config already supports `TEMPORAL_HOST` env var
- **Effort:** Medium (Temporal Cloud) to Large (self-hosted)

#### 5.4 Environment variables for production
```env
# Backend
DATABASE_URL=postgresql+asyncpg://user:pass@rds-host:5432/resonantia
REDIS_URL=redis://elasticache-host:6379
ANTHROPIC_API_KEY=sk-ant-...
CLERK_SECRET_KEY=sk_live_...
TEMPORAL_HOST=temporal-cloud-host:7233
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
CORS_ORIGINS=["https://resonantia.vercel.app"]

# Frontend (Vercel)
NEXT_PUBLIC_API_URL=https://api.resonantia.io
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
NEXT_PUBLIC_CONTENTFUL_SPACE_ID=gismnhbb3kki
NEXT_PUBLIC_CONTENTFUL_ACCESS_TOKEN=e7if3JoufyZzs33-...
NEXT_PUBLIC_APP_URL=https://resonantia.vercel.app
CLERK_SECRET_KEY=sk_live_...
```

#### 5.5 S3 integration for file storage
- **File:** `backend/src/resonantia/services/storage.py` (new)
- **Change:** Abstract file storage behind an interface: local filesystem for dev, S3 for production
- **Change:** Update `/api/v1/files/upload` to use the storage abstraction
- **Change:** Microscopy images go to S3
- **Effort:** Medium

---

## Implementation Order (Recommended)

```
Phase 1 (Week 1): Core Wiring
├── 1.1 Chat → real Claude API
├── 1.2 Samples → backend API  
├── 1.3 Plates → backend API
├── 1.4 Processing → backend API
└── 1.5 Worklist → backend download

Phase 2 (Week 1-2): Backend Activities
├── 2.1 Processing activities → real services
├── 2.2 Plate mapping activities → real services
├── 2.3 Persistence activities → PostgreSQL
└── 2.4 Figure generation → matplotlib

Phase 3 (Week 2): Microscopy
└── 3.1 Real image display with synthetic fallback

Phase 4 (Week 2): Seeding
└── 4.1 Database seed script

Phase 5 (Week 3-4): Deployment
├── 5.1 Vercel config
├── 5.2 AWS Terraform (ECS, RDS, ElastiCache, S3, ALB)
├── 5.3 Temporal Cloud setup
├── 5.4 Production env vars
└── 5.5 S3 storage abstraction
```

---

## What's Already Production-Ready

- ✅ Clerk authentication (invite-only, Google OAuth)
- ✅ Contentful blog (5 articles published)
- ✅ Marketing site (About, Pricing, Blog pages)
- ✅ File upload/download API
- ✅ Guardrails (topic filtering + system prompt)
- ✅ Langfuse tracing (connected, traces flowing)
- ✅ RAGAS evaluation framework
- ✅ Tool registry in Redis (15 tools, 6 categories)
- ✅ Backend data processing algorithms (4PL, Z-score, Z-prime)
- ✅ Backend plate mapping logic (cherry pick, serial dilution, worklist generation)
- ✅ Temporal workflows defined (agent, plate, processing)
- ✅ Docker Compose for local infrastructure
- ✅ 62 backend tests + 46 frontend tests passing
- ✅ Styled UI with consistent design system
