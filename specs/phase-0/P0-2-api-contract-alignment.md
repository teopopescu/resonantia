# SPEC: Frontend/Backend API Contract Alignment

**ID:** P0.2
**Phase:** 0 — Stabilize
**Branch:** `fix/api-contracts`
**Priority:** P0
**Effort:** 4-5 days
**Dependencies:** P0.5 (test baseline)

---

## Problem Statement

Frontend stores make API calls that don't match backend routes. Writes silently fail and the frontend falls back to local Zustand state, giving users the false impression data is persisted.

### Known Mismatches (from Codex audit)
1. **ELN:** Frontend calls `/api/v1/eln/entries`, backend exposes `/api/v1/eln/`
2. **Protocol inventory check:** Frontend sends `GET`, backend expects `POST /api/v1/protocols/{id}/inventory-check`
3. **Dilution calculator:** Frontend sends `stock_concentration`/`target_concentration`/`target_volume`, backend expects `c1`/`c2`/`v1`/`v2`
4. **Response fields:** Backend returns snake_case, frontend expects camelCase — manual mapping hacks scattered through stores

---

## Scope

### In Scope
- Audit ALL frontend store API calls against backend routes
- Fix route mismatches (URLs, HTTP methods)
- Fix payload field name mismatches
- Add response transformer for snake_case→camelCase
- Add contract tests verifying frontend/backend compatibility

### Out of Scope
- OpenAPI code generation (nice-to-have, not required for P0)
- Backend schema changes beyond alias configuration
- New API endpoints

---

## Architecture

### Response Transformer

```typescript
// frontend/src/lib/api.ts

function snakeToCamel(obj: any): any {
  if (Array.isArray(obj)) return obj.map(snakeToCamel);
  if (obj !== null && typeof obj === 'object') {
    return Object.keys(obj).reduce((acc, key) => {
      const camelKey = key.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
      acc[camelKey] = snakeToCamel(obj[key]);
      return acc;
    }, {} as any);
  }
  return obj;
}

// Wrap the existing api() helper to transform responses
export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, options);
  const data = await response.json();
  return snakeToCamel(data) as T;
}
```

### Route Fix Mapping

| Store | Current Call | Correct Call |
|-------|------------|--------------|
| eln-store.ts | `GET /api/v1/eln/entries` | `GET /api/v1/eln/` |
| eln-store.ts | `POST /api/v1/eln/entries` | `POST /api/v1/eln/` |
| protocol-store.ts | `GET /api/v1/protocols/{id}/inventory-check` | `POST /api/v1/protocols/{id}/inventory-check` |
| protocol-store.ts | `POST .../dilution { stock_concentration, ... }` | `POST .../dilution { c1, c2, v1, v2 }` |
| sample-store.ts | Expects camelCase fields | Add transformer |
| plate-store.ts | Expects camelCase fields | Add transformer |

---

## Implementation

### Step 1: Full audit (day 1)
- Read each of the 7 stores, extract every `api()` call
- Match against backend router definitions in `backend/src/resonantia/api/`
- Document all mismatches in a table (route, method, payload, response)

### Step 2: Add response transformer (day 1)
- Implement `snakeToCamel` in `frontend/src/lib/api.ts`
- Apply to all API responses globally
- Remove all manual `x.created_at || x.createdAt` patterns from stores

### Step 3: Fix routes and methods (day 2-3)
- `eln-store.ts`: change `/eln/entries` → `/eln/`
- `protocol-store.ts`: change inventory check from GET to POST
- `protocol-store.ts`: change dilution payload to `{ c1, c2, v1, v2 }`
- Fix any other mismatches found in audit

### Step 4: Backend schema compatibility (day 3)
- Add `model_config = ConfigDict(populate_by_name=True)` to schemas that need to accept both snake and camel on input
- Verify `alias_generator` doesn't break existing backend tests

### Step 5: Contract tests (day 4)
- Write `backend/tests/test_api_contracts.py` that verifies:
  - Each route the frontend calls exists in the OpenAPI spec
  - Response schemas match what frontend TypeScript types expect
  - Request payloads are accepted without validation errors

---

## Expected Behavior

| Action | Before | After |
|--------|--------|-------|
| Create ELN entry | Fails silently (wrong route), falls back to local state | Creates in DB, returns persisted entry |
| Check protocol inventory | Fails (wrong HTTP method), shows nothing | Returns inventory status |
| Calculate dilution | Fails (wrong field names), shows nothing | Returns calculated volumes |
| Load sample list | Works but manual field mapping | Works with automatic snake→camel transform |

---

## Acceptance Criteria

- [ ] Every frontend store API call hits an existing backend route with correct HTTP method
- [ ] Payload field names match between frontend request and backend Pydantic schema
- [ ] Response transformer converts all snake_case fields to camelCase automatically
- [ ] No manual field mapping (`x.created_at || x.createdAt`) remains in any store
- [ ] `backend/tests/test_api_contracts.py` exists and passes
- [ ] Contract test covers: ELN CRUD, protocol inventory check, dilution calculator, sample CRUD, plate CRUD
- [ ] Frontend can create, read, update entities with data persisting to the database (not local state)
- [ ] All existing frontend and backend tests pass

---

## Risks

- **Global response transformer may break edge cases** where the backend intentionally returns camelCase or where field names contain underscores that aren't word separators (e.g., `ic_50` → `ic50` not `ic50`). Test thoroughly.
- **Some stores may have additional undocumented mismatches** beyond the Codex findings. The audit step is critical.
- **Changing request payloads is a coordinated change** — frontend and backend must deploy together (or backend must accept both old and new formats temporarily).
