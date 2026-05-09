# SPEC: Storage Abstraction + CSV Upload Pipeline

**ID:** P1.1
**Phase:** 1 — Killer Workflow
**Branch:** `feat/storage-and-csv-upload`
**Priority:** P1
**Effort:** 4 days
**Dependencies:** P1.0 (approval gates)

---

## Problem Statement

The killer workflow requires uploading CSV files, generating figures (PNG plots), and storing worklists. Currently:
- File uploads use an in-memory `_file_registry` dict (lost on restart)
- No structured CSV parsing endpoint (agent receives raw text)
- No storage abstraction (hardcoded local filesystem paths)
- Generated figures have no consistent URL scheme

---

## Scope

### In Scope
- Storage interface (local filesystem now, S3 later — same API)
- File upload model (persist metadata to PostgreSQL)
- CSV parsing endpoint with structure detection
- Frontend CSV preview before sending to agent

### Out of Scope
- S3 implementation (just the interface — local for now)
- Image upload for microscopy (existing flow, separate concern)
- Large file chunked upload (defer — lab CSVs are small)

---

## Architecture

### Storage Interface

```python
# backend/src/resonantia/services/storage.py

from abc import ABC, abstractmethod

class StorageBackend(ABC):
    @abstractmethod
    async def save(self, path: str, content: bytes, content_type: str) -> str:
        """Save file, return access URL."""
    
    @abstractmethod
    async def load(self, path: str) -> bytes:
        """Load file content."""
    
    @abstractmethod
    def url(self, path: str) -> str:
        """Get public/signed URL for file."""

class LocalStorage(StorageBackend):
    def __init__(self, base_dir: str = "./uploads"):
        self.base_dir = Path(base_dir)
    
    async def save(self, path: str, content: bytes, content_type: str) -> str:
        full_path = self.base_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return f"/api/v1/files/serve/{path}"
    
    async def load(self, path: str) -> bytes:
        return (self.base_dir / path).read_bytes()
    
    def url(self, path: str) -> str:
        return f"/api/v1/files/serve/{path}"

# Future: class S3Storage(StorageBackend): ...
```

### File Upload Model

```python
# backend/src/resonantia/models/file_upload.py

class FileUpload(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "file_uploads"
    
    org_id: Mapped[str]
    filename: Mapped[str]
    content_type: Mapped[str]
    size_bytes: Mapped[int]
    storage_path: Mapped[str]  # path within storage backend
    parsed_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # For CSVs: { columns: [...], row_count: N, detected_types: {...} }
```

### CSV Parsing Endpoint

```python
# POST /api/v1/files/upload-and-parse
# Accepts: multipart/form-data with file
# Returns:
{
    "file_id": "uuid",
    "filename": "dose_response.csv",
    "columns": ["Compound", "Concentration_nM", "Response_%", "Well", "Replicate"],
    "row_count": 240,
    "column_types": {
        "Compound": "string",
        "Concentration_nM": "numeric",
        "Response_%": "numeric",
        "Well": "string",
        "Replicate": "integer"
    },
    "preview_rows": [...first 5 rows as dicts...],
    "detected_format": "dose_response"  # heuristic: has concentration + response columns
}
```

---

## Implementation

### Step 1: Storage interface + local backend (day 1)
### Step 2: FileUpload model + migration (day 1)
### Step 3: Upload endpoint with CSV parsing (day 2)
### Step 4: Serve endpoint for accessing stored files (day 2)
### Step 5: Frontend CSV preview in chat composer (day 3)
### Step 6: Update `read_file_contents` tool to use DB-persisted files (day 3-4)
### Step 7: Tests (day 4)

---

## Expected Behavior

| Action | Before | After |
|--------|--------|-------|
| Upload CSV | Stored in memory dict, lost on restart | Stored on disk + metadata in DB, survives restart |
| Agent calls `read_file_contents` | Reads from in-memory dict | Reads from DB-tracked file via storage interface |
| View uploaded file later | Gone after restart | Accessible via URL indefinitely |
| Upload CSV in chat | Raw file sent to agent | Preview shown first (columns, 5 rows), then sent |

---

## Acceptance Criteria

- [ ] `POST /api/v1/files/upload-and-parse` accepts CSV and returns structured metadata
- [ ] File metadata persisted in `file_uploads` table with org_id
- [ ] File content stored via StorageBackend (local filesystem)
- [ ] `GET /api/v1/files/serve/{path}` returns file content with correct Content-Type
- [ ] `read_file_contents` tool reads from DB-tracked files (not in-memory dict)
- [ ] Files survive backend restart
- [ ] Frontend shows CSV preview (column names, types, first 5 rows) before sending
- [ ] CSV column type detection identifies: string, numeric, integer, date
- [ ] File uploads are org-scoped (org_A cannot access org_B's files)
- [ ] Storage interface has `save()`, `load()`, `url()` methods
