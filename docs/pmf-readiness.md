# Resonantia — PMF readiness

**Date:** 2026-05-02
**Question this answers:** can Resonantia find product-market fit with the current features?
**Sources:** `codex-findings/01–06` (Codex audit), this session's PRs (#8–#15), the live walkthrough (`docs/walkthroughs/beatriz-walkthrough.md`).
**Audience:** founders + first design-partner conversations.

---

## TL;DR

**No — not with the current product as-shipped today. Yes — with the same product after ~2 months of focused stabilization, then ~4 months of one deep workflow + one deep integration.**

The wedge that lands PMF is **narrower** than the marketing site claims and the **execution gap** is smaller than the marketing site suggests. Codex's audit and this session's PRs describe the same product from opposite sides; together they bound the work.

---

## The wedge that finds PMF (per `codex-findings/03` + `06`)

Not "AI-powered lab informatics". Not a 6-module platform. **One closed loop:**

> Design experiment → generate plate / worklist → analyze assay result → document → propose next experiment

And the first-release positioning is even tighter (`06`):

> Resonantia is the **voice-first agent layer** that captures lab work as it happens and writes **structured, auditable records back to your existing ELN/LIMS**.

That is the framing: **Capture → Sync → Analyze**, with Resonantia sitting **above** eLabFTW / Benchling rather than competing with them. The difference matters: replacing Benchling is a 3-year sales cycle you usually lose; augmenting Benchling is a 6-month cycle that lands.

---

## Why today's product doesn't yet hit PMF

Codex's `01-engineering-audit.md` names four structural blockers that will sink a design-partner conversation:

1. **Frontend↔backend contract drift.** ELN routes don't match (`/eln/entries` vs `/eln/`). Protocol inventory check uses the wrong HTTP verb. Dilution payload uses wrong field names. **A partner clicks "save", thinks it persisted, comes back tomorrow, the data is gone.** That kills trust on day one.
2. **Silent demo-mode fallback.** Frontend stores fall back to local Zustand on API failure with no banner. Same trust-killer.
3. **Generated-code Temporal workflow.** The agent path that runs LLM-generated Python in a sandbox is too risky to be the production path. Replace with typed plan steps + known tools (`02-agent-and-voice-strategy.md` autonomy levels).
4. **Inconsistent LLM provider config.** Some code uses OpenAI, some Anthropic, some references settings fields that don't exist.

The Beatriz walkthrough (`docs/walkthroughs/beatriz-walkthrough.md`) added: empty `/about` section, `/pricing` page contradicts the internal economics, Clerk dev-mode banner visible on the sign-in card.

**None of these are thesis problems.** All of them are "make the existing thing work reliably enough for someone other than you" problems.

---

## What exists today vs. what the wedge needs

| Wedge requirement | Status today | Source |
|---|---|---|
| Voice capture (hands-free) | ✅ VAD voice-mode + PR #11 push-to-talk | `frontend/src/components/lab/voice-{mode,ptt}.tsx` |
| Structured experiment record extraction from speech | ⚠️ Possible via single-agent today; not productized. PR #9 (multi-agent + critic) makes it durable. | `services/multi_agent/` |
| Persisted plates / samples / ELN / protocols | ⚠️ Backend persists; frontend silently drops on API mismatch | Codex `01` finding 1 |
| Dose-response / IC50 / Z′ / qPCR | ✅ Real implementations, real tests | `services/data_processor.py` |
| Multimodal chat (image attachments) | ✅ PR #10, with cross-tenant isolation | `services/multimodal.py` |
| eLabFTW write-back | ❌ HTTP client exists; settings don't persist; not productized | `services/integrations/elabftw.py` |
| Benchling integration | ❌ Not built; "coming soon" copy | n/a |
| Audit log per ELN entry | ❌ Tracked as Sprint 2 | `docs/production-readiness-summary.md` |

Score against the wedge: **4 ✅ · 3 ⚠️ · 3 ❌.** The ⚠️s are tractable in P0 work; two of the ❌s (eLabFTW productized, audit log) gate PMF directly.

---

## Sequenced path to PMF (folds Codex `04` into this session's PRs)

| Weeks | Focus | Codex section | Session PRs that help |
|---|---|---|---|
| **0–4** | P0 stabilization: API contract fixes, demo-mode banner, single LLM provider, fail noisy not silent | `05` P0 + `01` findings 1, 2, 4 | None yet — this is the missing prerequisite |
| **4–8** | Killer workflow E2E: CSV upload → IC50 → ELN draft → next-plate proposal → user approves → worklist exports | `04` Month 1–2 | PR #9 (multi-agent + critic), PR #10 (image upload) |
| **8–12** | Voice scoped to lookup / dictation / draft (not destructive); approval cards for everything consequential | `02` autonomy levels 2–3 | PR #11 (PTT) |
| **12–16** | One real eLabFTW write-back integration (deep, not shallow) | `04` Month 3–4 + `06` positioning | None — new build |
| **16–20** | Partner-specific deepening on HTS or HCI, not both | `04` Month 4–5 | — |
| **20–24** | Convert to paid pilots with explicit success metrics (50% time reduction, etc.) | `04` Month 5–6 | PR #12 makes it safe to deploy |

---

## Hard takeaways

1. **The features you have are roughly the right features.** The product thesis is not broken; the execution is incomplete.
2. **The biggest single PMF blocker is the silent-failure bug class.** Fix the 6–8 P0 contract mismatches in `codex-findings/05-refactor-backlog.md` before any partner call. 1–2 weeks of refactor, not a month.
3. **The biggest single PMF accelerator is reframing the product as a Capture-and-Sync layer above eLabFTW**, not a replacement for ELN/LIMS. Copy + integration change, not a product change.
4. **Microscopy GA, 1536-well, "32 tools" should come off the marketing surface.** Per `docs/decommission-list.md` and `codex-findings/06`, those are aspirations not first-release claims.
5. **Skip SOC 2, SAML, vLLM, custom ASR, Electron, GraphRAG.** All explicitly deferred in `codex-findings/04`. None of them block the first 3 design partners.

---

## Best-fit design partners (per `codex-findings/03`)

**Best first design partners:**

- 30–200 person biotech.
- Screening, cellular assay, or platform biology team.
- Already uses plates, imaging, GraphPad/Excel, and some ELN/LIMS.
- No large internal informatics team.
- Has urgency around reproducibility, throughput, or automation handoffs.

**Avoid first:**

- Large pharma enterprise (AstraZeneca, Novo Nordisk).
- Highly regulated GxP teams.
- Labs that primarily need full LIMS replacement.
- Teams without plate / assay / data handoff pain.

**Named-org fit (from `03`):**

- **Dewpoint** — best strategic fit. Condensate biology + HCI + AI-native culture. Wedge: "from HCI/assay output to prioritized follow-up experiment."
- **Max Planck** — plausible academic design partner. Wedge: research data management, reproducibility, ELN/protocol automation. Risk: slow procurement, fragmented budgets.
- **AstraZeneca** — long-term proof point, not near-term. Use a smaller biotech pilot to create proof, then approach via a specific assay/data workflow.
- **Novo Nordisk** — later enterprise. Build VPC / self-hosted only after smaller pilots validate the workflow.

---

## What this doc commits to

- The wedge per `codex-findings/03` + `06` (Capture → Sync → Analyze, voice-first, ELN/LIMS write-back).
- Stabilization-before-features (`codex-findings/01` findings, fixed first).
- Repositioning the marketing surface to match the wedge (`/about`, `/pricing`, hero copy).
- Three named-org fit conclusions (Dewpoint first, Max Planck second, AstraZeneca / Novo Nordisk later).

## What this doc does NOT commit to

- A specific revenue target — `docs/agentic-architecture.md` §9 has the unit economics; reconcile after a month of design-partner usage data.
- A specific deployment path for VPC / on-prem (deferred per `04`).
- Any product feature beyond what is already in the open PRs (#8–#15) plus the killer-workflow build in weeks 4–8.

---

## Bottom line

PMF is **6 months of focused execution away**, not 18. The product is closer than the marketing suggests, and farther than the running demo suggests. Codex is more honest about what's not yet working; this session's PRs do the engineering on what's already designed. The two views are consistent and additive.

**Suggested next move:** turn `codex-findings/05-refactor-backlog.md` P0 items into one PR per item. That's the unblocking work for getting design partners on the product without lying to them about persistence.
