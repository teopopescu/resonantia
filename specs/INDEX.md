# Resonantia Spec Index

31 specs across 6 phases. Each spec is a self-contained PRD with: problem statement, architecture, implementation steps, expected behavior, and acceptance criteria.

## How to Use

1. **Before implementing:** Read the spec. Verify assumptions against current code.
2. **During implementation:** Check off acceptance criteria as you go.
3. **Before merging:** All acceptance criteria must pass.
4. **Dependencies:** Respect the sequencing — specs list their dependencies.

---

## Phase 0: Stabilize (Month 0-1)

| ID | Spec | Effort | Dependencies |
|----|------|--------|-------------|
| P0-CUT | [Strip Non-Core Surface](phase-0/P0-CUT-strip-non-core-surface.md) | 1d | None |
| P0.5 | [Test Fixes + CI Gate](phase-0/P0-5-test-fixes-ci-gate.md) | 2d | None |
| P0.0 | [Multi-Tenancy Security Fix](phase-0/P0-0-tenant-security.md) | 3d | None |
| P0.1 | [Model Provider Abstraction](phase-0/P0-1-model-provider-abstraction.md) | 5-6d | P0.5 |
| P0.7 | [Output Guardrails](phase-0/P0-7-output-guardrails.md) | 3d | P0.1 |
| P0.3 | [Safe Temporal Execution](phase-0/P0-3-safe-temporal-execution.md) | 5-6d | P0.1, P0.7 |
| P0.2 | [API Contract Alignment](phase-0/P0-2-api-contract-alignment.md) | 4-5d | P0.5 |
| P0.4 | [Demo Mode Discipline](phase-0/P0-4-demo-mode-discipline.md) | 3d | P0.2 |
| P0.6 | [Docs Sync + Langfuse](phase-0/P0-6-docs-sync-langfuse.md) | 2d | All P0 |

## Phase 1: Killer Workflow (Month 1-2)

| ID | Spec | Effort | Dependencies |
|----|------|--------|-------------|
| P1.0 | [Approval Gates](phase-1/P1-0-approval-gates.md) | 4-5d | Phase 0 |
| P1.1 | [Storage + CSV Upload](phase-1/P1-1-storage-csv-upload.md) | 4d | P1.0 |
| P1.2 | [Dose-Response Integration](phase-1/P1-2-dose-response-integration.md) | 3d | P1.1 |
| P1.3 | [ELN Draft from Results](phase-1/P1-3-eln-draft-from-results.md) | 3-4d | P1.0, P1.2 |
| P1.4a | [Plate Layout Proposal](phase-1/P1-4a-plate-layout-proposal.md) | 3d | P1.0, P1.2 |
| P1.4b | [Agent Follow-Up Proposal](phase-1/P1-4b-agent-followup-proposal.md) | 4d | P1.4a, P1.2 |
| P1.5 | [Worklist Generation](phase-1/P1-5-worklist-generation.md) | 2d | P1.4a |
| P1.6 | [Killer Workflow Demo](phase-1/P1-6-killer-workflow-demo.md) | 2d | All P1 |

## Phase 2: Voice Safety (Month 2-3)

| ID | Spec | Effort | Dependencies |
|----|------|--------|-------------|
| P2.1 | [Voice Safety Scope](phase-2/P2-1-voice-safety-scope.md) | 3d | Phase 0 |
| P2.2 | [Voice-to-ELN Capture](phase-2/P2-2-voice-eln-capture.md) | 3-4d | P2.1, P1.0 |
| P2.3 | [Multimodal Provider](phase-2/P2-3-multimodal-provider.md) | 2d | P0.1 |
| P2.4 | [Voice + Multimodal Tests](phase-2/P2-4-voice-multimodal-tests.md) | 2-3d | P2.1-P2.3 |

## Phase 3: Design Partner Hardening (Month 3-4)

| ID | Spec | Effort | Dependencies |
|----|------|--------|-------------|
| P3.1 | [Audit Log](phase-3/P3-1-audit-log.md) | 4d | Phase 0 |
| P3.2 | [Data Export](phase-3/P3-2-data-export.md) | 3d | P3.1 |
| P3.3 | [Org Admin + Roles](phase-3/P3-3-org-admin-roles.md) | 4d | Phase 0 |
| P3.4 | [eLabFTW Integration](phase-3/P3-4-elabftw-integration.md) | 4-5d | Phase 0 |
| P3.5 | [Production Infra](phase-3/P3-5-production-infra-basics.md) | 3d | Phase 0 |

## Phase 4: Multi-Agent + Observability (Month 4-5)

| ID | Spec | Effort | Dependencies |
|----|------|--------|-------------|
| P4.1 | [Multi-Agent Stabilize](phase-4/P4-1-multi-agent-stabilize.md) | 4d | P0.1 |
| P4.2 | [Langfuse Dashboard](phase-4/P4-2-langfuse-dashboard.md) | 3d | P4.1 |
| P4.3 | [Partner Workflows](phase-4/P4-3-partner-workflows.md) | 3d | P3.3 |

## Phase 5: Paid Pilot Preparation (Month 5-6)

| ID | Spec | Effort | Dependencies |
|----|------|--------|-------------|
| P5.1 | [Usage Metering + Billing](phase-5/P5-1-usage-metering-billing.md) | 5d | Phase 3 |
| P5.2 | [Deployment Finalization](phase-5/P5-2-deployment-finalization.md) | 4d | All phases |
| P5-OTel | [Observability Stack](phase-5/P5-OTel-observability-stack.md) | 5-6d | None |
