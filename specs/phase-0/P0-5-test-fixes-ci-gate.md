# SPEC: Test Fixes + CI Gate

**ID:** P0.5
**Phase:** 0 — Stabilize
**Branch:** `fix/tests-ci-gate`
**Priority:** P0 (first — establish baseline)
**Effort:** 2 days
**Dependencies:** None

---

## Problem Statement

The Codex engineering audit found 1 backend test failing and 5 frontend tests failing. Without a green test suite, subsequent refactoring has no safety net. CI currently does not block merges on test failure, allowing regressions to accumulate.

### Current Failures
- **Backend:** `tests/test_tool_registry.py::TestDefaultTools::test_default_tools_count` — expected 32 tools, actual count is 33 (a tool was added without updating the test)
- **Frontend:** `src/lib/__tests__/plate-utils.test.ts` — 5 failures, all color expectation mismatches for `wellColor` function (palette was updated without updating test expectations)

---

## Scope

### In Scope
- Fix the 6 failing tests
- Configure CI to block merges on test failure
- Add strict markers to prevent test warnings from being ignored

### Out of Scope
- Writing new tests (that's per-PR going forward)
- Increasing coverage thresholds (defer to later)
- Refactoring test infrastructure

---

## Architecture

No architectural changes. Test fixes + CI configuration only.

### Backend Test Fix
```python
# tests/test_tool_registry.py
# Change: assert count against actual tool list, not a hardcoded number
def test_default_tools_registered(self):
    tools = registry.get_all_tools()
    expected_tools = set(TOOL_HANDLERS.keys())
    assert set(t.name for t in tools) == expected_tools
```

### Frontend Test Fix
```typescript
// src/lib/__tests__/plate-utils.test.ts
// Update wellColor expected values to match current palette
// Read actual palette from the source (plate-utils.ts) to keep in sync
```

### CI Configuration
```yaml
# .github/workflows/backend-tests.yml
- run: uv run pytest tests/ -v --strict-markers -W error

# .github/workflows/frontend-tests.yml  
- run: npm test -- --reporter=verbose
```

---

## Implementation

1. Run `uv run pytest tests/ -v` — identify exact failure assertion
2. Fix backend test: assert against `TOOL_HANDLERS` keys instead of magic number 32
3. Run `npm test` — identify exact color values expected vs actual
4. Fix frontend tests: update `wellColor` expected return values to match current palette in `plate-utils.ts`
5. Update `.github/workflows/backend-tests.yml`: add `--strict-markers`, `-W error`
6. Update `.github/workflows/frontend-tests.yml`: ensure non-zero exit on failure
7. Verify both suites pass locally: `uv run pytest tests/ -v && cd frontend && npm test`

---

## Expected Behavior

| Command | Before | After |
|---------|--------|-------|
| `uv run pytest tests/ -v` | 61 passed, 1 failed | 62+ passed, 0 failed |
| `npm test` | 43 passed, 5 failed | 48+ passed, 0 failed |
| PR to main with failing test | Merge allowed | Merge blocked |

---

## Acceptance Criteria

- [ ] `uv run pytest tests/ -v` exits 0 — all tests pass
- [ ] `cd frontend && npm test` exits 0 — all tests pass
- [ ] CI workflow runs on every PR targeting `main`
- [ ] CI blocks merge when any test fails (branch protection rule or required status check)
- [ ] Backend test for tool count is resilient to tool additions (asserts against registry, not number)
- [ ] Frontend color tests match the actual palette defined in source code

---

## Risks

- The tool count test may need to account for conditional tool registration (e.g., tools only available with certain config). If so, assert a minimum count + verify expected core tools exist.
- Frontend color palette may have changed for design reasons — verify with the new palette before "fixing" to old values.
