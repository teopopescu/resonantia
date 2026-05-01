# Beatriz walkthrough — findings

**Persona:** Beatriz Ferreira Gomes, Product Manager (drug discovery background) at a Series-A/B biotech (e.g., Dewpoint Therapeutics).
**Date of run:** 2026-05-01
**Method:** Playwright MCP against the live local stack (Docker compose, all services healthy) for public pages; lab-side findings are grounded in the 53 screenshots captured in prior real sessions plus a code review of the corresponding components. The lab is auth-gated by Clerk and a fresh Playwright browser cannot inherit a session, so the live drive could not enter the lab.

What Beatriz cares about, ranked: provenance / audit (every IC50 must be traceable), tool consolidation (her current pain is Excel→vendor SW→Prism→PowerPoint), data-residency and SOC 2 (regulated environment), hands-free at the bench, real data over canned demo.

Verdict: the marketing surface is polished and the agent thesis is clear. The lab itself is more capable than it looks from the public site, but it ships several things that would make a senior lab informatics user pause: a pricing page that contradicts the internal economic model, an empty About page, and a few feature gaps that a regulated-lab buyer flags on the first call.

---

## What was driven live

### 1. Marketing home (`/`)

- Polished hero: "Agentic OS for Lab Informatics", "Now in early access" pill, dual CTA (Try Resonantia Lab / Read our vision).
- Typography and spacing land. Beatriz's first impression is favourable.
- **Finding (NIT):** the body copy says "design worklists, browse microscopy data, and manage reagent inventory" — the **decommission list** (PR #8) shrinks the microscopy viewer; this copy will need to follow the cut so we don't pitch a feature we're sunsetting.

_Local capture: `docs/walkthroughs/beatriz-01-marketing-home.png` (not committed; PNGs are gitignored)._

### 2. Sign-in (`/lab` → Clerk)

- Clerk gate fires correctly; "Continue with Google" + email path; "Development mode" banner shows.
- **Finding (MAJOR for an enterprise prospect):** the Clerk dev-mode banner is visible at `accounts.dev`. Production deploys must be on the `*.resonantia.io` Clerk domain or the banner becomes a credibility problem on a sales call.
- **Finding (MINOR):** sign-in copy is generic; missing reassurance that the lab is org-scoped (Beatriz's team will care: "if I sign up with my work email, do my colleagues see my data?"). One sentence under the heading would handle it.

_Local capture: `docs/walkthroughs/beatriz-02-clerk-signin.png`._

### 3. Pricing (`/pricing`)

The page ships **Free $0 / Pro $99 / Enterprise Custom**. This is the most concrete cut between current public surface and internal strategy.

- The internal model in `docs/agentic-architecture.md` §9 prices **Pro at $149/seat with 500 turns/month** and **Team at $349/seat** — and warns explicitly that "unlimited" pricing in any tier below Enterprise is one of the things that kills the economics.
- The current Pro tier promises "Unlimited plate maps", "All data processing pipelines", "Microscopy image browser", "Unlimited sample tracking", "File upload & download", "Priority support" — the unlimited language plus $99 leaves a single power user well underwater on API cost alone (per the audit: ~$150/mo at 100 turns/day).
- Enterprise card mentions "Audit logging & compliance reports", "SSO / SAML", "Custom instrument integrations", "Dedicated support & SLA", but **no SOC 2, no data-residency, no 21 CFR Part 11 hooks**. Those are the words a Dewpoint-class buyer scans for first.
- **Finding (MAJOR — both editorial and economic):** reconcile the public pricing page with the internal pricing model. Either lift the Pro tier to $149 with explicit allowance language ("500 agent turns / month, overage $0.25/turn"), or keep $99 but cap turns and call it the Free-with-BYOK path the audit recommends. Add SOC 2 in-progress + EU/US data residency to the Enterprise column.
- **Finding (MAJOR):** missing FAQ. "Where is my data hosted?", "Can I bring my own LLM key?", "What happens to my data when I cancel?" — three questions every regulated buyer asks, none answered.

_Local capture: `docs/walkthroughs/beatriz-03-pricing.png`._

### 4. About (`/about`)

- Hero copy is good ("Built by scientists, for scientists" — the framing matches Beatriz's pain).
- **Finding (BLOCKER for marketing — visible bug):** the page renders an "Our mission" heading with a completely **empty** section underneath. Multiple subsequent sections appear to have empty container areas too. This is a public-page bug that will be one of the first things Beatriz sees if she clicks About from the nav.

_Local capture: `docs/walkthroughs/beatriz-04-about.png`._

---

## Lab-side findings (grounded in the 53 prior screenshots + code review)

The walkthrough cannot enter `/lab` live (Clerk gate), but every flow Beatriz would care about has been captured in prior real sessions saved to the project root: `J0–J5*.png`, `b1–b4*.png`, `s1–s5*.png`. Reading them next to the corresponding components gives a faithful picture of what she'd see.

### Lab home + chat (`b2-lab-home.png`, `b2-lab-chat.png`, `J5-chat-with-skills.png`)

- The chat composer is the central surface — Beatriz's mental model lines up with this. She wants "type / talk / drag a CSV" and the layout supports all three.
- "Skills" pill row exposes typed prompts (Plate mapping, Dose-response, Sample lookup, Image analysis, Protocol design). Useful as a discovery affordance for a first-time user.
- @-mentions for resources (plate maps, samples, microscopy images, ELN, protocols, processing results) — lab-informatics-fluent UX. Beatriz would recognise this as "structured data on tap".
- **Finding (MAJOR, code-level):** chat is single-agent today. PR #9 introduces the multi-agent topology (planner + 5 specialists + critic). Beatriz at a senior lab would feel the difference quickly — single-agent answers tend to be confident-but-shallow on multi-step requests like "design the plate AND draft the ELN entry AND analyse the results". Fast-track PR #9 behind a `multi_agent_enabled=true` flag for design-partner accounts.
- **Finding (MINOR):** the demo script (`docs/demo-script-beatriz.md`) opens with a guardrail-test prompt ("write me a poem about kinases" → declined). Cute, but the polished version surfaces a constitutional banner once at the top of the chat ("This assistant only helps with lab work; full audit log enabled") instead of relying on the user fishing for a refusal.

### Plates (`s1-plates-actual.png`, `J1-plate-mapper-loaded.png`, `s1-s3-plate-detail-with-worklist.png`)

- Plate mapper renders 96-well and 384-well grids, supports cherry-pick + serial dilution + replicate, generates Echo-CSV / Hamilton-GWL / Opentrons-PY worklists. This is the substrate the audit told us to keep — and it shows.
- **Finding (POSITIVE):** the explicit volume range in the worklist (e.g., 2.5 nL ≤ V ≤ 1 µL for Echo) matches the constitutional rules in PR #9's `plate_designer` system prompt. When PR #9 lands, these rules become enforced by the critic agent — exactly Beatriz's expectation.
- **Finding (MINOR):** prior screenshots show a worklist export that downloads as a generic CSV without an explicit `Source Plate, Source Well, Dest Plate, Dest Well, Volume` header verifiable against an Echo-552 manual. Add an export-format unit test in `services/plate_mapper.py` that snapshots the first 5 rows of the worklist and compares against a fixture.

### Samples & inventory (`b2-samples.png`, `J2-add-sample-dialog.png`, `J2-samples-search-anti.png`)

- Real CRUD, real search. The "Add sample" dialog accepts barcode, lot, location, expiry, and a free-text storage temperature. Good.
- **Finding (MAJOR):** there is no dedicated **expiring-soon** banner on the samples page — even though `get_expiring_samples` is a registered tool. Beatriz's team gets paged when reagents expire mid-experiment; a banner ("3 reagents expire in the next 14 days · review") at the top of `/lab/samples` is a one-day add and worth more than a chat search.
- **Finding (MINOR):** `add_sample` does not appear to validate barcode uniqueness in the UI before submit; the backend should and the UI should pre-check. Otherwise a busy lab gets duplicate-barcode errors after the user has typed everything.

### Microscopy (`b2-microscopy.png`, `J3-microscopy-view.png`, `J3-microscopy-fov3.png`)

- The current viewer is a thumbnail strip + single-image inspector backed by **synthetic canvas-generated** images per `frontend/src/lib/microscopy-demo.ts`. Beatriz will probe this immediately — "what HCS systems integrate?" — and the answer "we generate fake images for the demo" will land badly.
- **Finding (MAJOR):** the decommission list (PR #8) explicitly calls for shrinking this surface — keep the data model and metadata API as substrate for the **Scope-Scout** agent in PR #9, drop the synthetic-canvas demo + the FOV-browser UI. Replace the page with a metadata table + per-image inspector + an agent affordance ("ask the agent to triage").
- **Finding (MAJOR):** no "redo" workflow surface. A senior lab informatics user expects: agent flags out-of-focus / debris / well-collapse, surfaces a **redo recommendation** (which wells, what channels), and threads it back into the plate mapper. PR #9's Scope Scout has the prompt for this; the missing piece is the UI surface in `/lab/microscopy`.

### ELN (`b3-resource-menu.png`, `b4-microscopy-detail.png`, `J5-chat-with-skills.png`)

- ELN entry creation works via tool call (`create_eln_entry`) and `submit_eln_entry` makes it immutable. The agent-drafted-entry flow (Notebook Scribe per PR #9) maps onto this perfectly.
- **Finding (MINOR):** UI does not yet show an audit-log diff per submitted entry. For 21 CFR Part 11 conversations, a "show what changed and when" inline view at `/lab/eln/<id>` is the difference between "demo" and "regulated-pharma usable".

### Voice (`docs/voice-testing-guide.md` + `voice-mode.tsx` review)

- Existing voice mode is VAD-based (auto-stop on silence). PR #4 just shipped push-to-talk. Both surfaces coexist now via a discriminated `voicePanel: null|"vad"|"ptt"` in chat-interface.tsx.
- **Finding (POSITIVE):** the demo script's "create an ELN entry for the staurosporine experiment" voice prompt is exactly the constitutional shape the audit recommended (lookup + dictation, never autonomous command). PR #9's critic enforces "no destructive action without explicit approval" so even a voice-initiated ELN submission will surface an approval card.
- **Finding (MINOR):** voice mode session ID is hardcoded (`"voice-session"` and `"voice-ptt-session"`). Pre-existing in voice-mode.tsx; flagged in PR #4. With multi-tenancy on (multi-tenancy already merged via PR #3 of the original branch series), concurrent voice users on the same backend collide. Switch to a per-user/conversation ID.

### Settings & integrations (`b4-invite.png`, `b3-skill-menu.png`)

- eLabFTW connector is partially wired (HTTP client + endpoints); per the decommission list, **defer** rather than build out — but don't remove yet, the integration shell is reusable for Benchling.
- **Finding (MINOR — pricing alignment):** Settings advertises eLabFTW; the pricing page does not. If Beatriz expects integration parity between marketing copy and product, surface eLabFTW (or its successor Benchling write-back) on the public Features page.

---

## Cross-cutting observations

### Auth-walled live walkthroughs are blind to UAT

A Playwright session in a fresh profile cannot inherit a Clerk login. Two options for next time:

1. **Test-mode auth bypass behind an env flag.** `if (process.env.NEXT_PUBLIC_E2E_AUTH === "bypass") return mockSession;` — Cypress / Playwright can drive the lab end-to-end without dragging real users through Clerk. Keeps the dev-mode banner irrelevant to test environments.
2. **Service-account Clerk key.** Generate a single fixed user via Clerk admin API, log in via JWT in `localStorage` before navigating. More work, but what Cypress-against-prod needs anyway.

Either is a half-day's work and unblocks every future `chore/walkthrough-*` PR.

### The dev-mode Clerk banner is visible to the full Playwright run

This will also be visible to anyone we screen-share with during a sales call if we're on `localhost`. Worth a separate Vercel-staging env with the production Clerk app so Playwright + screen-shares both look like the real product.

### The "decommission list" must lead the next sprint

The strongest signal across the walkthrough: the gap between **what the marketing site claims** and **what the lab actually delivers convincingly today** is widest on microscopy and ELN richness — exactly what the decommission list (PR #8) flags for shrinking. If we ship the shrink + Plan-Mode + multi-agent (PRs #8 / #9) before another sales conversation, Beatriz's experience tightens dramatically.

---

## Punch list (priority order)

| # | Severity | Where | What |
|---|----------|-------|------|
| 1 | BLOCKER (public bug) | `/about` | "Our mission" section is empty; rest of page also looks unfilled. Either populate or hide. |
| 2 | MAJOR | `/pricing` | Reconcile public tiers with `agentic-architecture.md` §9; add SOC 2 / data residency / FAQ. |
| 3 | MAJOR | Sign-in | Move off Clerk dev-mode account before any external sales call. |
| 4 | MAJOR | `/lab` (microscopy) | Drop synthetic-canvas demo per decommission list; replace with metadata + agent triage surface. |
| 5 | MAJOR | `/lab/samples` | Add expiring-soon banner using `get_expiring_samples`. |
| 6 | MAJOR | Chat | Land PR #9 (multi-agent + critic) behind a flag for design-partner accounts. |
| 7 | MINOR | `/lab/eln` | Add per-entry audit-log diff for 21 CFR Part 11 conversations. |
| 8 | MINOR | Voice | Per-user voice conversation IDs, not the hardcoded session strings. |
| 9 | MINOR | Worklist export | Add a fixture-based test that asserts the Echo / Hamilton CSV format byte-for-byte. |
| 10 | MINOR | Marketing copy | Update the home-page subtitle once microscopy viewer is shrunk. |
| 11 | MINOR | UAT tooling | Add an E2E auth-bypass flag + a service-account Clerk login path. |

---

## What this doc is not

- It is not a product spec. It is one persona's read of the surface. Treat it as a checklist of "Beatriz-shaped" things to fix; weight against the broader engineering roadmap.
- It is not the final word on pricing. The numbers in `agentic-architecture.md` §9 are themselves design-doc numbers; once design partners are live with usage data, re-derive.
- It is not a replacement for putting Beatriz herself in front of the product. The most expensive thing about this doc is the things she'd notice that I didn't.
