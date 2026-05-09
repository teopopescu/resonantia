# Resonantia — production-readiness summary

**Date:** 2026-05-01
**Author:** session summary across PRs #8 → #13.
**Audience:** founders, prospective investors, design-partner conversations.

This is the consolidated read of where Resonantia stands on the path to production: what is required before paying customers, what has shipped in this session, and what is still to do. It supersedes nothing — every claim here points at a primary source (audit doc, PR, code path).

---

## Verdict

Resonantia today is **a working agentic prototype with the right substrate** (plate maps, samples, microscopy data, ELN, processing) and **the wrong cap-table assumptions baked into the public surface** (pricing, observability, SOC 2 hooks). The session's six PRs close the most expensive of those gaps without introducing new dependencies.

It is **not yet** production-ready in the strict sense (paying customers + 99.9% SLA + SOC 2). It **is** ready to put in front of three design partners on the path to that, with a 4–6 week runway of focused work between this session and that conversation.

---

## What shipped in this session

Six PRs, all with adversarial review applied via the local code-reviewer / security-auditor agents.

### #8 · `feat/decommission-and-prod-audit` — scoping docs

- `docs/aws-prod-readiness-audit.md` — read-only audit of the existing Terraform: 6 blockers, ~28 majors, 5 minors. Flags secrets in task envs, no HTTPS, single-AZ RDS, AWS-managed keys only, no Terraform state lock, no observability stack.
- `docs/decommission-list.md` — feature triage against the agent thesis: shrinks microscopy viewer, protocol builder, ELN editor; reframes voice as lookup + dictation only; defers eLabFTW. Surfaces what's *missing* — Plan Mode, multi-agent topology, lab memory.
- **Observability section:** Grafana Cloud Free + Sentry Free + Langfuse + Grafana OnCall as the recommended free stack (compared against New Relic Free, Datadog Free, Honeycomb Free, OpenObserve self-hosted, PagerDuty Free, Squadcast Free). $0/month through design-partner stage.

### #9 · `feat/multi-agent-topology` — orchestrator + 5 specialists + critic

Phase 1 of `docs/subagents-acp-plan.md` and §2 of `docs/agentic-architecture.md`. Behind the `multi_agent_enabled` flag (default off) so the legacy single-agent loop is unchanged.

- Pydantic-typed inter-agent messages (`TaskAssignment`, `TaskResult`, `OrchestrationPlan`, `CriticVerdict`).
- Constitutional system prompts per specialist (Echo volume range, Z'<0.5 gating IC50 reports, ELN structure rules).
- Critic fails closed (rejects) on high-stakes tools (`fit_dose_response`, `generate_worklist`, `create_plate_map`, `submit_eln_entry`, `qpcr_analysis`) when itself unavailable; soft-warns for low-stakes lookups.
- Sequential execution threads upstream specialist outputs into downstream `inputs.upstream` (the adversarial reviewer caught that without this, sequential mode is broken).
- 17 tests covering routing decomposition, single + multi specialist synthesis, critic pass/soft-warn/fail-closed, dependency threading.

### #10 · `feat/multimodal-chat` — image attachments to chat

Resonantia chat now accepts images (microscopy, gel photos, plate-reader screenshots) on a user message. Backend resolves them into vision-format content blocks at base64 data URLs.

Plus the **security hardening** the audit forced: file registry now records `org_id` on upload and every read path returns 404 to other tenants; upload extension whitelist closes a path-traversal vector; per-turn caps (5 images, 15 MB total, 5 MB per image); MIME allowlist tightened to `{png, jpeg, webp}` (drops `svg+xml`, `gif`, `tiff`, non-canonical `jpg`); image bytes never reach Langfuse traces.

26 tests — 20 multimodal, 6 file-API tenant isolation. Cross-tenant probing now returns 404, not 403.

### #11 · `feat/voice-push-to-talk` — bench-friendly hands-free

Hold Spacebar (or a foot pedal mapped to Space) to record, release to send. Coexists with the existing VAD voice mode via a discriminated `voicePanel: null|"vad"|"ptt"` state.

Critical adversarial fixes during review: stop-before-getUserMedia race that stranded the recorder (BLOCKER), Spacebar stealing focus from page-wide buttons, mouseLeave cancelling a Spacebar hold, "Transcribing..." chat placeholder orphaned on no-speech-detected, MediaRecorder mimeType negotiation for Safari.

5 vitest tests, including one that exercises the BLOCKER race directly. **Wake-word is intentionally deferred to a separate later PR using openWakeWord** (Apache-2.0; the same model Home Assistant uses) so we don't introduce a Picovoice license dependency.

### #12 · `feat/terraform-prod-hardening` — Wave 1 blockers

| Blocker | Fix |
|---|---|
| **B1** Secrets in task envs | New `secrets.tf`: 6 KMS-encrypted Secrets Manager entries (db, openai, clerk, langfuse×2, redis_auth). ECS task defs use `secrets[]` with `valueFrom`. |
| **B2** HTTP-only ALB | TLS-1.3 policy, HTTP→HTTPS 301, HTTPS listener gated on `aws_acm_certificate_validation` so PENDING_VALIDATION doesn't error first apply. |
| **B3** Single-AZ RDS | `multi_az = true`, KMS-encrypted, 30-day backups, Performance Insights on. |
| **B4** AWS-managed keys | New `kms.tf` CMK with annual rotation, deliberately narrow policy (root + scoped CloudWatch Logs entry; other services use grants). |
| **B5** Broad exec role | `secretsmanager:GetSecretValue` scoped to the 6 specific ARNs only; `kms:Decrypt` on the CMK only. |
| **B6** Local Terraform state | New `bootstrap/` submodule creates the state bucket (versioned, KMS-encrypted, public-access blocked) and DynamoDB lock (PAY_PER_REQUEST, PITR). README documents the bootstrap and forbids committing the bootstrap state. |

Plus selected Wave 2 wins: SG egress narrowed to VPC CIDR (M2/M3), task-role logs scoped (M7), ElastiCache cluster→replication group with auto-failover + AUTH + transit encryption (M12), 90-day log retention (M17), `desired_count = 2` on the API service (M23), pinned Terraform version (m3).

Both stacks pass `terraform validate`; `terraform fmt -recursive` clean.

### #13 · `chore/beatriz-walkthrough` — senior-PM read

Drove the live local stack (Playwright MCP) for public surfaces; synthesized lab-side findings from 53 prior captured sessions + code review (the lab is auth-gated and Playwright cannot inherit a Clerk session).

Headline findings:
- BLOCKER (public bug): `/about` ships an empty "Our mission" section visible on viewport one.
- MAJOR: `/pricing` ($99 Pro with "unlimited" copy) contradicts the internal economics in `agentic-architecture.md` §9 ($149/seat with a 500-turn cap).
- MAJOR: Clerk **dev-mode** banner is visible during sign-in — not okay for an external sales call.
- MAJOR: microscopy viewer is synthetic-canvas; matches the decommission list — drop the viewer, keep the data + Scope-Scout agent.
- MAJOR: no expiring-soon banner on `/lab/samples` even though `get_expiring_samples` exists.
- MAJOR: chat is single-agent today; #9 must land behind the flag for design-partner accounts.

---

## Production-readiness checklist

The state of each leg, rated **DONE / IN-PR / TODO**.

### Security & compliance

| Item | Status | Where |
|---|---|---|
| Secrets out of plaintext | **IN-PR #12** | `secrets.tf`, `iam.tf` |
| HTTPS-only with TLS 1.3 | **IN-PR #12** | `alb.tf` |
| Customer-managed KMS for RDS / S3 / ElastiCache / SM / Logs | **IN-PR #12** | `kms.tf` |
| Multi-tenant file isolation | **IN-PR #10** | `services/multimodal.py`, `api/files.py` |
| GitHub PAT in `.git/config` | **TODO (flagged)** | rotate token; switch remote to SSH |
| SOC 2 Type II | **TODO** | enterprise-tier requirement; not started |
| 21 CFR Part 11 audit-log diff per ELN entry | **TODO** | `/lab/eln/<id>` UI surface (#13 finding) |
| WAF on ALB | **TODO (Wave 3)** | `aws_wafv2_web_acl` |
| GuardDuty / CloudTrail / Config | **TODO (Wave 3)** | per audit M26/M27 |

### Reliability & HA

| Item | Status | Where |
|---|---|---|
| RDS Multi-AZ | **IN-PR #12** | `rds.tf` |
| ElastiCache replication + auto-failover | **IN-PR #12** | `elasticache.tf` |
| ECS desired_count ≥ 2 | **IN-PR #12** | `ecs.tf` |
| Auto-scaling on CPU/mem | **TODO** | `aws_appautoscaling_target` |
| Cross-region or cross-account backup | **TODO (Wave 2)** | per audit M14 |
| Read replica | **TODO** | per audit M11 |

### Observability

| Item | Status | Where |
|---|---|---|
| Langfuse for LLM traces | **DONE** (in stack) | `services/tracing.py` |
| Plan: Grafana Cloud Free + Sentry Free + Grafana OnCall | **IN-PR #8** | `docs/aws-prod-readiness-audit.md` |
| ADOT collector sidecar | **TODO** | follow-up PR |
| Sentry SDK (FastAPI + Vercel) | **TODO** | follow-up PR |
| CloudWatch alarms (5xx, ECS CPU/mem, RDS CPU/free-storage) | **TODO (Wave 2)** | per audit M18 |
| 1-page incident runbook | **TODO** | `docs/runbook.md` (referenced but not written) |

### Agent quality

| Item | Status | Where |
|---|---|---|
| Multi-agent topology + critic | **IN-PR #9** | `services/multi_agent/` |
| Multimodal chat (images) | **IN-PR #10** | `services/multimodal.py` |
| Voice PTT | **IN-PR #11** | `voice-ptt.tsx` |
| Wake-word (openWakeWord) | **TODO** | follow-up PR |
| Plan Mode (planner / approval gates / Temporal Signals) | **TODO** | core thesis from `agentic-architecture.md` §1 |
| Lab memory (semantic + episodic + working) | **TODO** | `agentic-architecture.md` §4 |
| Eval surface `/admin/eval` | **TODO** | per audit §7 |

### Infrastructure & deploy

| Item | Status | Where |
|---|---|---|
| AWS Terraform Wave 1 | **IN-PR #12** | `infrastructure/terraform/` |
| Terraform remote state + lock | **IN-PR #12** | `bootstrap/` + `main.tf` |
| GitHub Actions OIDC for AWS | **TODO** | per audit M8 |
| `terraform plan` PR comment + manual `apply` gate | **TODO** | per audit |
| AWS Budgets alert | **TODO** | per audit m1 |

### Marketing surface

| Item | Status | Where |
|---|---|---|
| Empty `/about` section | **TODO (BLOCKER)** | per #13 walkthrough |
| Pricing page reconciled with internal model | **TODO** | per #13 walkthrough |
| Clerk production app + custom domain | **TODO** | per #13 walkthrough |
| FAQ (data residency, BYOK, cancellation) | **TODO** | per #13 walkthrough |

---

## What's left to be production-ready (in priority order)

A reasonable two-sprint cadence for a 3-person team:

### Sprint 1 (next 2 weeks)

1. **Public-page bugs** — fix `/about`, reconcile `/pricing`, move Clerk to production.
2. **Merge PRs #8–#13** in order. PR #8 is doc-only; PRs #9–#13 are flag-gated or strictly additive — none should block each other.
3. **Wire observability** — Grafana Cloud Free OTLP endpoint into ADOT sidecar; Sentry SDK in FastAPI + Next.js. One alert per the audit's M18 list, routed to Grafana OnCall → Slack. Write `docs/runbook.md`.
4. **Apply Terraform PR #12 against a sandbox AWS account** end-to-end, including the ACM two-pass DNS validation flow. Document anything unexpected.
5. **GitHub Actions OIDC for `terraform apply`** (audit M8) — replace any long-lived AWS keys with role assumption, add a manual-approval gate before apply.

### Sprint 2 (next 2 weeks)

6. **Plan Mode v1** — Plan / Step Pydantic objects, planner agent, Temporal workflow + approval-gate Signals, plan-card UI. This is the killer feature per `agentic-architecture.md` §1.
7. **Lab memory v1** — `lab_facts` table, memory-extractor agent (nightly Temporal workflow), settings UI to view/edit facts.
8. **Wake-word** — openWakeWord ONNX model in the browser, wired to the existing voice pipeline.
9. **Microscopy decommission** per the list — keep data + Scope-Scout agent, drop the synthetic-canvas viewer.
10. **First design partner** — academic lab, low integration overhead. Use the runbook for self-serve onboarding.

After Sprint 2 the product is design-partner-ready. After ~3 months of design-partner data, the LoRA path opens (per `agentic-architecture.md` §3 layer 4) and the SOC 2 + 21 CFR Part 11 conversations become tractable.

---

## What this session did NOT solve (called out so they don't disappear)

- **GitHub PAT in `.git/config`** — flagged in PR #8's audit; needs out-of-band rotation. Rotate the token, switch the remote to SSH (`git remote set-url origin git@github.com:teopopescu/resonantia.git`), and use a credential helper.
- **Multi-agent path doesn't yet call `build_user_content`** — multimodal images flow only through the legacy single-agent path. A small follow-up wires it after PR #9 merges.
- **`conversation_id` is hardcoded for voice** (`"voice-session"`, `"voice-ptt-session"`). Pre-existing in voice-mode.tsx; multi-tenancy will collide concurrent voice users on the same backend. Per-user IDs is one line of code change.
- **Plan Mode + lab memory** are the two largest pieces of the original `agentic-architecture.md` thesis still unbuilt. They are the real differentiator. The session's six PRs are scaffolding for them.
- **No SOC 2 evidence collection has started.** Picking the picks in PR #8's observability section (Grafana, Sentry, Langfuse) doesn't make SOC 2 easier — it just doesn't make it harder. The audit work itself is a separate budget line.

---

## "Codex adversarial review" — note

The original ask referenced OpenAI Codex / `adversarial-review`. Codex isn't directly callable from this session, so the substitute was the local `agent-skills:code-reviewer` and `agent-skills:security-auditor` agents, run on every code-bearing PR (#9, #10, #11, #12). Each found real BLOCKERs and MAJORs that were addressed in the same commit; the PR descriptions list the findings explicitly and link back to where each was fixed.

If you want a true Codex pass, run it yourself against the open branches before merging:

```
gh pr checkout 9   # or 10 / 11 / 12
codex review --against main
```

The branches are stable on top of `main`; merging them in this order avoids the test-count drive-by collision: **#8 → #9 → #10 → #11 → #12 → #13**.

---

## Bottom line

Six PRs. ~3,800 lines of code + docs. 88 backend tests + 5 frontend tests, all green. Two real BLOCKERs and ten MAJORs caught in adversarial review and fixed in the same session. Two genuine product-thesis features still to build (Plan Mode, lab memory).

The product is closer to design-partner-ready than the public marketing surface suggests, and farther from paying-customer-ready than the public marketing surface suggests. The session's PRs close that gap from both sides.
