# Resonantia Architecture

## System Overview

```
                        ┌─────────────────────────────────────────────────────────┐
                        │                   Docker Compose                        │
                        │                                                         │
  ┌──────────┐          │  ┌──────────────┐       ┌──────────────────────────┐    │
  │  Browser  │◄────────┼──┤   Frontend   │       │       Backend            │    │
  │           │─────────┼──►  (Next.js)   │──────►│     (FastAPI)            │    │
  └──────────┘  :3000   │  │  Port 3000   │ :8000 │     Port 8000           │    │
                        │  │              │       │                          │    │
                        │  │  - Zustand   │       │  ┌────────────────────┐  │    │
                        │  │  - React     │       │  │  Service Modules   │  │    │
                        │  │    Query     │       │  │                    │  │    │
                        │  │  - Clerk     │       │  │  ┌──────────────┐  │  │    │
                        │  │    Auth      │       │  │  │ Microscopy   │  │  │    │
                        │  └──────────────┘       │  │  │ Image Viewer │  │  │    │
                        │                         │  │  ├──────────────┤  │  │    │
                        │                         │  │  │ Plate        │  │  │    │
                        │                         │  │  │ Mapping      │  │  │    │
                        │                         │  │  ├──────────────┤  │  │    │
                        │                         │  │  │ Experiment   │  │  │    │
                        │                         │  │  │ Tracker      │  │  │    │
                        │                         │  │  ├──────────────┤  │  │    │
                        │                         │  │  │ AI Lab       │  │  │    │
                        │                         │  │  │ Assistant    │  │  │    │
                        │                         │  │  ├──────────────┤  │  │    │
                        │                         │  │  │ Protocol     │  │  │    │
                        │                         │  │  │ Builder      │  │  │    │
                        │                         │  │  └──────────────┘  │  │    │
                        │                         │  └────────────────────┘  │    │
                        │                         │            │             │    │
                        │                         └────────────┼─────────────┘    │
                        │                                      │                  │
                        │                    ┌─────────────────┼────────────┐     │
                        │                    │                 │            │     │
                        │               ┌────▼─────┐    ┌─────▼────┐  ┌───▼───┐ │
                        │               │PostgreSQL │    │  Redis   │  │Anthro-│ │
                        │               │   16      │    │    7     │  │pic API│ │
                        │               │ Port 5432 │    │Port 6379 │  │       │ │
                        │               └──────────┘    └──────────┘  └───────┘ │
                        │                                                         │
                        │           ┌─────────────────────────────┐               │
                        │           │   Temporal (Future)          │               │
                        │           │   Workflow Orchestration     │               │
                        │           │   - Long-running experiments │               │
                        │           │   - Pipeline execution       │               │
                        │           │   - Scheduled tasks          │               │
                        │           └─────────────────────────────┘               │
                        └─────────────────────────────────────────────────────────┘
```

## Data Flow

```
  User Request
       │
       ▼
  ┌─────────┐    REST/WS     ┌─────────┐
  │ Next.js │ ──────────────► │ FastAPI │
  │ + Clerk │ ◄────────────── │  + Auth │
  └─────────┘                 └────┬────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
               ┌────▼────┐  ┌────▼────┐  ┌─────▼──────┐
               │Postgres │  │  Redis  │  │ Anthropic  │
               │         │  │         │  │ Claude API │
               │- Users  │  │- Cache  │  │            │
               │- Plates │  │- Session│  │- Chat      │
               │- Images │  │- Queues │  │- Analysis  │
               │- Expts  │  │         │  │- Protocols │
               └─────────┘  └─────────┘  └────────────┘
```

## Feature Modules (Initial 5)

| Module | Description |
|--------|-------------|
| **Microscopy Image Viewer** | Upload, view, annotate, and AI-analyze microscopy images |
| **Plate Mapping** | Source-destination plate mapping with drag-and-drop well selection |
| **Experiment Tracker** | Create, manage, and track lab experiments with metadata |
| **AI Lab Assistant** | Claude-powered conversational assistant for lab workflows |
| **Protocol Builder** | Step-by-step protocol creation with version control |

## Production Deployment (Future)

```
  ┌────────────┐     ┌──────────────────────────────────────┐
  │   Vercel   │     │              AWS                      │
  │  (Next.js) │────►│                                      │
  └────────────┘     │  ┌───────────┐    ┌──────────────┐   │
                     │  │ ECS / EKS │    │     RDS      │   │
                     │  │ (FastAPI) │───►│ (PostgreSQL) │   │
                     │  └─────┬─────┘    └──────────────┘   │
                     │        │                              │
                     │        │          ┌──────────────┐   │
                     │        └─────────►│ ElastiCache  │   │
                     │                   │   (Redis)    │   │
                     │                   └──────────────┘   │
                     │                                      │
                     │  ┌──────────────────────────────┐    │
                     │  │  Temporal Cloud / EKS         │    │
                     │  │  (Workflow Orchestration)     │    │
                     │  └──────────────────────────────┘    │
                     │                                      │
                     │  ┌──────────────┐                    │
                     │  │     S3       │                    │
                     │  │ (Image Store)│                    │
                     │  └──────────────┘                    │
                     └──────────────────────────────────────┘
```
