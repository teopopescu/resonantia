# SPEC: Strip Non-Core Surface

**ID:** P0-CUT
**Phase:** 0 — Stabilize
**Branch:** `chore/strip-non-core`
**Priority:** P0 (parallel, day 1)
**Effort:** 1 day
**Dependencies:** None

---

## Problem Statement

The product currently exposes marketing pages (`/blog`, `/blog/[slug]`, `/about`) with no real content and a feature request page that adds maintenance burden. The `/api/v1/evals` endpoint exposes internal evaluation tooling as a public API. These dilute credibility for design partners and expand attack surface unnecessarily.

Per Opus 4.7 analysis: "Aspirational content with no real blog posts dilutes credibility. Keep only landing + pricing."

## Scope

### In Scope
- Remove empty marketing pages
- Replace feature-request page with external link
- Hide evals endpoint from public API
- Update navigation

### Out of Scope
- Landing page content changes
- `/use-cases` page (keep — has real workflow content)
- Pricing page restructure

---

## Architecture

No architectural changes. This is a surface-area reduction.

### Frontend Changes
```
DELETE: frontend/src/app/blog/page.tsx
DELETE: frontend/src/app/blog/[slug]/page.tsx
DELETE: frontend/src/app/about/page.tsx
DELETE: frontend/src/app/feature-request/page.tsx (or equivalent)
MODIFY: frontend/src/components/navbar.tsx — remove links, add external feedback link
```

### Backend Changes
```
MODIFY: backend/src/resonantia/api/router.py — remove /api/v1/evals from public router
OPTIONAL: Move evals to /api/v1/internal/evals with admin-only auth check
```

---

## Implementation

1. Delete frontend page directories for `/blog`, `/blog/[slug]`, `/about`
2. Delete or replace `/feature-request` page with a redirect to an external form (Typeform/Notion)
3. Update `navbar.tsx`: navigation items become Home, Use Cases, Pricing, Lab (authenticated)
4. Remove `evals.py` router inclusion from main API router (or gate behind admin check)
5. Clean up any unused imports (blog-data.ts, contentful.ts if only used by blog)

---

## Expected Behavior

| Action | Before | After |
|--------|--------|-------|
| Visit `/blog` | Empty blog listing | 404 or redirect to `/` |
| Visit `/about` | Placeholder about page | 404 or redirect to `/` |
| Visit `/feature-request` | In-app form page | Redirect to external form URL |
| `GET /api/v1/evals` | Returns eval data (public) | 401 Unauthorized (or 404) |
| Navbar links | Home, Use Cases, About, Blog, Pricing, Lab | Home, Use Cases, Pricing, Lab |

---

## Acceptance Criteria

- [ ] `/blog` returns 404 or 301 redirect to `/`
- [ ] `/blog/any-slug` returns 404
- [ ] `/about` returns 404 or 301 redirect to `/`
- [ ] `/feature-request` either redirects to external URL or is removed
- [ ] `GET /api/v1/evals` without admin auth returns 401 or 404
- [ ] Navbar displays only: Home, Use Cases, Pricing, Lab
- [ ] No broken links on the landing page or `/use-cases`
- [ ] `npm run build` succeeds without errors (no dead imports)
- [ ] Existing frontend tests pass

---

## Risks

- Low risk. Pure removal. No behavioral dependencies.
- If blog-data.ts or contentful.ts have other consumers, verify before deleting.
