# SPEC: Demo Mode Discipline

**ID:** P0.4
**Phase:** 0 — Stabilize
**Branch:** `fix/demo-mode-explicit`
**Priority:** P0
**Effort:** 3 days
**Dependencies:** P0.2 (API contracts — shares store files)

---

## Problem Statement

All 7 frontend Zustand stores silently fall back to local state when API calls fail. A design partner using the product will think their data is saved when it's not. There is no visible indication that the system is operating in a degraded mode.

From Codex audit: "user actions may silently fall back to demo state, giving a false impression of persistence."

---

## Scope

### In Scope
- Explicit demo mode flag (`NEXT_PUBLIC_DEMO_MODE`)
- Health check probe on app mount
- Visible banner when in demo mode
- Error toasts when writes fail in non-demo mode
- Remove all silent catch-and-persist-locally patterns

### Out of Scope
- Seed data generation (keep existing `demo-data.ts` behind the flag)
- Backend-side demo mode handling
- Per-feature demo flags (one global flag)

---

## Architecture

### Demo Mode Detection

```typescript
// frontend/src/lib/demo-mode.ts

let _isDemoMode: boolean | null = null;

export function isDemoMode(): boolean {
  if (_isDemoMode !== null) return _isDemoMode;
  
  // Explicit env var takes precedence
  if (process.env.NEXT_PUBLIC_DEMO_MODE === 'true') {
    _isDemoMode = true;
    return true;
  }
  
  // Default: not demo mode (backend must be available)
  _isDemoMode = false;
  return false;
}

// Called on app mount — probes backend health
export async function initDemoMode(): Promise<void> {
  if (process.env.NEXT_PUBLIC_DEMO_MODE === 'true') {
    _isDemoMode = true;
    return;
  }
  
  try {
    const res = await fetch(`${API_URL}/health`, { signal: AbortSignal.timeout(3000) });
    _isDemoMode = !res.ok;
  } catch {
    _isDemoMode = true; // Backend unreachable — enter demo mode
  }
}

export function showErrorToast(action: string, error: unknown): void {
  // Display toast notification: "Failed to {action}. Changes not saved."
  toast.error(`Failed to ${action}. Changes not saved.`);
}
```

### Store Pattern (Before → After)

```typescript
// BEFORE (silent fallback)
createSample: async (sample) => {
  try {
    const created = await api('/api/v1/samples', { method: 'POST', body: ... });
    set(state => ({ samples: [...state.samples, created] }));
  } catch {
    // Silent local persist — user thinks it's saved
    set(state => ({ samples: [...state.samples, { ...sample, id: uuid() }] }));
  }
}

// AFTER (explicit error handling)
createSample: async (sample) => {
  if (isDemoMode()) {
    // Demo mode: persist locally, user knows via banner
    set(state => ({ samples: [...state.samples, { ...sample, id: uuid() }] }));
    return;
  }
  
  try {
    const created = await api('/api/v1/samples', { method: 'POST', body: ... });
    set(state => ({ samples: [...state.samples, created] }));
  } catch (error) {
    showErrorToast('create sample', error);
    // Do NOT persist locally — write failed, user must know
    throw error;
  }
}
```

### Banner Component

```tsx
// In frontend/src/app/lab/layout.tsx
{isDemoMode() && (
  <div className="bg-amber-100 border-b border-amber-300 px-4 py-2 text-sm text-amber-800">
    Demo mode — changes are not persisted to the server
  </div>
)}
```

---

## Implementation

### Step 1: Create demo-mode.ts (day 1)
- Implement `isDemoMode()`, `initDemoMode()`, `showErrorToast()`
- Call `initDemoMode()` in the root layout on mount

### Step 2: Update all 7 stores (day 1-2)
- `sample-store.ts` — add demo mode check + error toast to all mutations
- `plate-store.ts` — same
- `eln-store.ts` — same
- `protocol-store.ts` — same
- `lab-store.ts` — same
- `microscopy-store.ts` — same
- `onboarding-store.ts` — same

### Step 3: Add banner (day 2)
- Add persistent amber banner to `/lab` layout
- Only shows when `isDemoMode()` returns true
- Banner text: "Demo mode — changes are not persisted to the server"

### Step 4: Handle edge cases (day 3)
- Empty org with backend up: no demo banner (empty data is valid)
- Backend becomes unavailable mid-session: next failed write triggers toast + sets demo mode
- `microscopy-demo.ts` synthetic image generation: gate behind `isDemoMode()`

### Step 5: Verify (day 3)
- Manual test: stop backend, try all CRUD operations → all show toasts
- Manual test: start backend with empty org → no banner, no fallback data
- grep verification: `grep -r "catch" frontend/src/stores/` → no silent empty catches

---

## Expected Behavior

| Scenario | Before | After |
|----------|--------|-------|
| `DEMO_MODE=false`, backend up | Works (data persists) | Same — no change |
| `DEMO_MODE=false`, backend down | Works (appears to) — data lost on refresh | Toast on every write: "Failed to X. Not saved." |
| `DEMO_MODE=true` | Same as backend-down (indistinguishable) | Amber banner visible; local writes acknowledged as temporary |
| Empty org, backend up | May show demo data | Shows empty state (valid) — no banner |
| Backend goes down mid-session | No indication | Next failed write shows toast + banner appears |

---

## Acceptance Criteria

- [ ] `NEXT_PUBLIC_DEMO_MODE=false` + backend stopped → every create/update shows error toast
- [ ] No data is silently persisted locally when backend is unavailable (in non-demo mode)
- [ ] `NEXT_PUBLIC_DEMO_MODE=true` → amber banner visible on every `/lab` page
- [ ] Demo mode seeds local data from `demo-data.ts` (existing behavior, now explicit)
- [ ] Empty org with backend running → no banner, no fallback data, empty state UI
- [ ] `grep -rn "catch" frontend/src/stores/ | grep -v "showErrorToast\|isDemoMode"` → no silent catches
- [ ] `microscopy-demo.ts` synthetic data only loads when `isDemoMode() === true`
- [ ] All frontend tests pass
- [ ] Manual smoke test: 5 different CRUD operations with backend down → all show toasts

---

## Risks

- **UX impact in development.** Developers running frontend without backend will see error toasts constantly. Solution: use `NEXT_PUBLIC_DEMO_MODE=true` in local `.env.local`.
- **Store refactoring conflicts with P0.2.** Both modify the same store files. P0.4 depends on P0.2 to avoid merge conflicts — do P0.2 first (fixes routes), then P0.4 (adds error handling).
- **Toast library needed.** If no toast system exists, add a lightweight one (sonner, react-hot-toast).
