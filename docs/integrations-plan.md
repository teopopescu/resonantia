# External Integrations — Implementation Plan

## Context

Resonantia Lab needs to connect with existing lab informatics software so the AI chat can query data from external systems alongside internal data. Scientists don't want to abandon their existing LIMS/ELN — they want Resonantia to sit on top and unify access.

**Problem:** Benchling and Dotmatics require enterprise licenses for API access. We need a working demo with an open-source alternative first, then build the integration framework so adding Benchling/Dotmatics later is just a new connector.

---

## Target Integrations

| Software | Type | API Access | Priority |
|---|---|---|---|
| **eLabFTW** | ELN | REST API, open-source, self-hosted | **Demo — build first** |
| **Benchling** | ELN + Registry | REST API, requires enterprise license | Phase 2 |
| **Dotmatics** | ELN + LIMS + Registration | REST API, enterprise only | Phase 2 |
| **STARLIMS** | LIMS | REST/SOAP API | Phase 3 |
| **LabWare** | LIMS | REST API | Phase 3 |
| **Sapio Sciences** | ELN + LIMS | REST API | Phase 3 |
| **OpenBIS** | Data management | REST + JSON-RPC, open-source (ETH Zurich) | Optional — academic |
| **SciNote** | ELN | REST API, free tier available | Optional — SMB |

---

## Architecture: Integration Framework

### Design Principle
Every external system implements the same abstract interface. The chat agent doesn't know which system it's querying — it calls a generic tool, and the integration layer routes to the right connector.

```
User: "What experiments did we run on EGFR last month?"
   │
   ▼
Chat Agent → calls `query_external_data` tool
   │
   ▼
Integration Router → checks which integrations are active
   │
   ├── eLabFTW connector → REST API → returns experiments
   ├── Benchling connector → REST API → returns entries
   └── Dotmatics connector → REST API → returns records
   │
   ▼
Merged results → returned to LLM → formatted response
```

### Abstract Interface

```python
# backend/src/resonantia/services/integrations/base.py

class LabIntegration(ABC):
    """Base class for all external lab software integrations."""
    
    name: str                    # "elabftw", "benchling", "dotmatics"
    display_name: str            # "eLabFTW", "Benchling", "Dotmatics"
    
    @abstractmethod
    async def test_connection(self) -> ConnectionResult
    
    @abstractmethod
    async def search_experiments(self, query: str, limit: int = 20) -> list[ExternalExperiment]
    
    @abstractmethod
    async def get_experiment(self, external_id: str) -> ExternalExperiment | None
    
    @abstractmethod
    async def search_samples(self, query: str, limit: int = 20) -> list[ExternalSample]
    
    @abstractmethod
    async def get_sample(self, external_id: str) -> ExternalSample | None
    
    @abstractmethod
    async def search_protocols(self, query: str, limit: int = 20) -> list[ExternalProtocol]
    
    @abstractmethod
    async def list_recent(self, days: int = 30, limit: int = 50) -> list[ExternalRecord]
```

### Normalized Data Models

All integrations return data in the same format, regardless of source:

```python
@dataclass
class ExternalExperiment:
    source: str              # "elabftw", "benchling", etc.
    external_id: str         # ID in the external system
    title: str
    body: str                # content/description
    status: str              # normalized: draft, active, completed, archived
    author: str | None
    created_at: datetime | None
    updated_at: datetime | None
    tags: list[str]
    url: str | None          # link back to the external system
    raw_data: dict           # original unprocessed response

@dataclass
class ExternalSample:
    source: str
    external_id: str
    name: str
    sample_type: str         # normalized type
    barcode: str | None
    location: str | None
    quantity: float | None
    unit: str | None
    metadata: dict
    url: str | None
    raw_data: dict

@dataclass
class ExternalProtocol:
    source: str
    external_id: str
    name: str
    description: str
    steps: list[dict]        # [{title, description, ...}]
    author: str | None
    url: str | None
    raw_data: dict

@dataclass
class ExternalRecord:
    source: str
    record_type: str         # "experiment", "sample", "protocol"
    external_id: str
    title: str
    summary: str
    updated_at: datetime | None
    url: str | None
```

---

## Demo Integration: eLabFTW

### Why eLabFTW
- Open-source (AGPL-3.0), self-hosted, runs in Docker
- REST API with comprehensive documentation
- Can run alongside Resonantia in docker-compose
- Has experiments, items (samples/reagents), tags, templates
- Widely used in academic labs

### eLabFTW API Mapping

| Resonantia Method | eLabFTW API Endpoint | Notes |
|---|---|---|
| `search_experiments` | `GET /api/v2/experiments?q={query}` | Full-text search |
| `get_experiment` | `GET /api/v2/experiments/{id}` | Returns body as HTML |
| `search_samples` | `GET /api/v2/items?q={query}` | Items = samples/reagents |
| `get_sample` | `GET /api/v2/items/{id}` | |
| `search_protocols` | `GET /api/v2/experiments?cat=protocol` | Filter by category |
| `list_recent` | `GET /api/v2/experiments?order=lastchange` | Sort by last modified |
| `test_connection` | `GET /api/v2/users/me` | Verify API key works |

### Docker Setup

Add eLabFTW to docker-compose.yml for the demo:

```yaml
elabftw:
  image: elabftw/elabimg:latest
  ports:
    - "3148:443"
  environment:
    DB_HOST: elabftw-mysql
    DB_NAME: elabftw
    DB_USER: elabftw
    DB_PASSWORD: elabftw_dev
    SECRET_KEY: <generated>
    SERVER_NAME: localhost
    SITE_URL: https://localhost:3148
  depends_on:
    - elabftw-mysql

elabftw-mysql:
  image: mysql:8.0
  environment:
    MYSQL_ROOT_PASSWORD: root
    MYSQL_DATABASE: elabftw
    MYSQL_USER: elabftw
    MYSQL_PASSWORD: elabftw_dev
  volumes:
    - elabftw_mysql_data:/var/lib/mysql
```

### Seed eLabFTW with Demo Data

On first run, use the eLabFTW API to create:
- 5 experiments (matching our internal experiments for cross-referencing)
- 10 items (reagents/samples)
- 2 protocol templates

This makes the demo immediately useful — the chat can query both internal and eLabFTW data.

---

## Agentic Tools for External Data

### New Tools (4)

```
query_external_experiments
  - description: "Search experiments across connected external lab software (eLabFTW, Benchling, etc.)"
  - params: query (string), source (optional — filter to specific system)
  - handler: iterates all active integrations, merges results

query_external_samples  
  - description: "Search samples/reagents across connected external lab software"
  - params: query (string), source (optional)

get_external_record
  - description: "Get full details of a specific record from an external system"
  - params: source (string), external_id (string), record_type (string)

list_external_recent
  - description: "List recently modified records across all connected external systems"
  - params: days (number, default 30), source (optional)
```

### How the Agent Uses Them

```
User: "What experiments did we run on EGFR last month?"

Agent decides to call TWO tools:
  1. query_experiments(query="EGFR")           → internal Resonantia data
  2. query_external_experiments(query="EGFR")  → eLabFTW / Benchling data

Agent merges results:
  "I found 2 experiments:
   - [Resonantia] EGFR IC50 — HEK293T (completed, EC50=0.042 µM)
   - [eLabFTW] EGFR Western Blot validation (active, last modified 3 days ago)
     View in eLabFTW: https://localhost:3148/experiments.php?id=42"
```

The agent can distinguish sources and provide links back to the original system.

---

## Integration Management UI

### Settings Page (`/lab/settings`)

Expand the existing settings page:

```
Integrations
├── eLabFTW          [Connected ●]  [Configure] [Disconnect]
├── Benchling         [Not configured]  [Connect]
├── Dotmatics         [Not configured]  [Connect]
└── + Add Integration
```

Each integration card shows:
- Connection status (green dot / gray)
- Last sync time
- Record count (X experiments, Y samples synced)
- Configure button → URL, API key, sync settings
- Test Connection button
- Enable/Disable toggle

### Configuration Storage

```
integration_configs table:
- id (UUID PK)
- org_id (String, indexed) — per-org config
- integration_type (String: "elabftw", "benchling", "dotmatics")
- display_name (String: user-friendly name, e.g. "Our eLabFTW")
- base_url (String)
- api_key_encrypted (String) — encrypted at rest
- enabled (Boolean)
- last_sync_at (DateTime, nullable)
- sync_status (String: "ok", "error", "never")
- config_extra (JSON) — integration-specific settings
- created_at, updated_at
```

### API Endpoints

```
GET    /api/v1/integrations/              — list all configured integrations
POST   /api/v1/integrations/              — add a new integration
PATCH  /api/v1/integrations/{id}          — update config
DELETE /api/v1/integrations/{id}          — remove integration
POST   /api/v1/integrations/{id}/test     — test connection
POST   /api/v1/integrations/{id}/sync     — trigger manual sync (optional)
GET    /api/v1/integrations/search        — search across all active integrations
```

---

## Benchling Integration (Phase 2 — when license available)

### API Mapping

| Resonantia Method | Benchling API Endpoint |
|---|---|
| `search_experiments` | `GET /api/v2/entries?name.contains={query}` |
| `get_experiment` | `GET /api/v2/entries/{id}` |
| `search_samples` | `GET /api/v2/custom-entities?name.contains={query}` or `GET /api/v2/containers?name.contains={query}` |
| `search_protocols` | `GET /api/v2/entries?schema=protocol&name.contains={query}` |
| `test_connection` | `GET /api/v2/organizations` |

### Benchling-Specific Features
- Registry entities (plasmids, strains, antibodies) → map to ExternalSample
- Notebook entries → map to ExternalExperiment
- Structured tables in entries → parse and make queryable
- Benchling uses tenant URLs: `{tenant}.benchling.com/api/v2/`

---

## Dotmatics Integration (Phase 2)

### API Mapping

| Resonantia Method | Dotmatics API |
|---|---|
| `search_experiments` | `GET /api/rest/v1/experiments?search={query}` |
| `search_samples` | `GET /api/rest/v1/samples?search={query}` |
| `get_experiment` | `GET /api/rest/v1/experiments/{id}` |
| `test_connection` | `GET /api/rest/v1/system/info` |

### Dotmatics-Specific Features
- Studies and Study Plans → map to ExternalExperiment
- Compound registration → map to ExternalSample with structure data
- Plate data → could map to our PlateMap model
- Dotmatics Browser (biological data) → queryable via Resonantia chat

---

## Implementation Phases

```
Phase 1 — Integration Framework + eLabFTW Demo (3-4 days)
├── Abstract LabIntegration interface + normalized models
├── Integration config model + API endpoints
├── eLabFTW connector (full implementation)
├── Add eLabFTW to docker-compose.yml
├── Seed eLabFTW with demo data
├── 4 agentic tools for external queries
├── Settings UI for managing integrations
└── Test: chat queries both Resonantia DB + eLabFTW

Phase 2 — Benchling + Dotmatics Connectors (2-3 days each, when licenses available)
├── Benchling connector implementing LabIntegration
├── Dotmatics connector implementing LabIntegration
├── Connector-specific field mappings
└── Test with real API keys

Phase 3 — Advanced Features (future)
├── Background sync: periodic pull from external systems → cache in Resonantia
├── Bidirectional sync: push Resonantia data to external systems
├── Conflict resolution for two-way sync
├── Webhook receivers: external system notifies Resonantia of changes
└── Data deduplication across sources
```

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Demo system | eLabFTW | Open-source, Docker-ready, good API, widely used in academia |
| Architecture | Abstract interface + connectors | Adding Benchling/Dotmatics = just a new class |
| Data caching | Query on demand, no local cache (Phase 1) | Simple, always fresh data. Add caching in Phase 3 |
| API key storage | Encrypted in PostgreSQL per org | Secure, multi-tenant ready |
| Agent access | Separate `query_external_*` tools | Agent explicitly decides when to search external vs internal |
| Result merging | Agent handles it (not code) | LLM is better at contextual merging than hardcoded rules |

---

## Demo Scenario

After implementation, this conversation works:

```
User: "What do we know about Staurosporine across all our systems?"

Agent calls 3 tools in parallel:
  1. lookup_sample(query="Staurosporine")           → Resonantia: 1mg, -20°C, lot CP-2024-8810
  2. get_ic50_values(compound="Staurosporine")       → Resonantia: EC50=0.042 µM in HEK293T  
  3. query_external_experiments(query="Staurosporine") → eLabFTW: 2 experiments found

Agent response:
  "Here's everything we have on Staurosporine:

  **Inventory (Resonantia)**
  - 1 mg in stock, Freezer-B / Shelf-2 / Box-4, lot CP-2024-8810, expires 2027

  **Dose-Response (Resonantia)**  
  - IC50 = 0.042 µM in HEK293T (R² = 0.994, Hill slope = 1.23)

  **External Experiments (eLabFTW)**
  - 'Staurosporine selectivity panel' — completed, last modified April 8
    → View in eLabFTW: https://localhost:3148/experiments.php?id=15
  - 'Staurosporine time-course imaging' — active, last modified April 10
    → View in eLabFTW: https://localhost:3148/experiments.php?id=23"
```
