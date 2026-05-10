# Resonantia AI — Production Readiness Gaps

> Last updated: 2026-05-10
>
> This document identifies what is **missing** for a true production deployment of Resonantia AI. Each gap includes a description, why it matters, estimated effort, and priority level.

---

## Priority Key

| Priority | Definition |
|----------|-----------|
| **P1** | Must-have before first production deployment |
| **P2** | Should-have within 30 days of launch |
| **P3** | Nice-to-have, plan for within 90 days |

---

## 1. Observability (MISSING)

### 1.1 OpenTelemetry Distributed Tracing

| Attribute | Detail |
|-----------|--------|
| **What** | No OpenTelemetry SDK instrumentation or collector deployment. Cannot trace a request across backend, Temporal worker, and MCP server. |
| **Why it matters** | Without distributed tracing, debugging latency issues or failures in multi-service flows (e.g., user chat -> backend -> Temporal workflow -> MCP tool call -> LLM) requires correlating logs manually across services. In production, this is nearly impossible at scale. |
| **Effort** | 3-5 days (instrument Python services with `opentelemetry-sdk`, deploy OTel collector sidecar on ECS, configure exporters) |
| **Priority** | **P1** |

### 1.2 APM (Application Performance Monitoring)

| Attribute | Detail |
|-----------|--------|
| **What** | No DataDog, New Relic, or equivalent APM. Only Langfuse exists, which is LLM-specific (token usage, prompt latency) — not general application performance. |
| **Why it matters** | Cannot monitor response times (p50/p95/p99), throughput, error rates, or resource utilization at the application level. No way to detect performance regressions before users complain. |
| **Effort** | 2-3 days (DataDog agent setup on ECS, dashboard configuration, baseline alerting) |
| **Priority** | **P1** |

### 1.3 Error Tracking (Sentry)

| Attribute | Detail |
|-----------|--------|
| **What** | No Sentry or equivalent error tracking. Errors are only visible in CloudWatch logs (if configured). |
| **Why it matters** | Unhandled exceptions, stack traces, and error frequency/impact are invisible. Cannot prioritize bug fixes by user impact or detect new errors introduced by deployments. |
| **Effort** | 1 day (install `sentry-sdk`, configure DSN, add FastAPI integration, add Next.js Sentry plugin) |
| **Priority** | **P1** |

### 1.4 Uptime Monitoring / Synthetic Checks

| Attribute | Detail |
|-----------|--------|
| **What** | No synthetic monitoring (e.g., DataDog Synthetics, Checkly, Pingdom). No external health check pinging the application. |
| **Why it matters** | If the site goes down, the team learns about it from users rather than automated alerts. No SLA tracking or uptime metrics for investor/customer conversations. |
| **Effort** | 0.5 days (configure health check endpoints, set up external monitoring service) |
| **Priority** | **P1** |

### 1.5 Alerting (PagerDuty/OpsGenie)

| Attribute | Detail |
|-----------|--------|
| **What** | No incident alerting pipeline. No on-call rotation. No escalation policies. |
| **Why it matters** | Even with monitoring, alerts that go to email or Slack are easily missed. Production incidents need guaranteed human response within defined SLAs. |
| **Effort** | 1-2 days (PagerDuty setup, integration with APM/monitors, escalation policy, on-call schedule) |
| **Priority** | **P2** |

---

## 2. Testing (MISSING)

### 2.1 Allure Test Reporting

| Attribute | Detail |
|-----------|--------|
| **What** | Test results are raw pytest/vitest console output. No structured test reporting with history, trends, or categorization. |
| **Why it matters** | Cannot track test flakiness over time, cannot share test results with non-engineers (product, investors), cannot identify which test suites are degrading. |
| **Effort** | 1 day (install allure-pytest, configure GitHub Actions to generate/publish reports) |
| **Priority** | **P3** |

### 2.2 Load Testing

| Attribute | Detail |
|-----------|--------|
| **What** | No load testing framework (k6, Locust, or equivalent). No performance baselines established. |
| **Why it matters** | Unknown capacity limits. Cannot answer "how many concurrent users can we support?" or "will LLM latency cause timeouts under load?" Critical for seed-round customer demos and early adoption. |
| **Effort** | 3-4 days (write k6 scripts for critical paths, establish baselines, integrate into CI as gate) |
| **Priority** | **P2** |

### 2.3 E2E Browser Tests (Playwright CI)

| Attribute | Detail |
|-----------|--------|
| **What** | No end-to-end browser tests running in CI. Frontend changes can break user flows without detection. |
| **Why it matters** | Regressions in critical flows (login, chat, plate mapping, worklist generation) are only caught manually. As the team scales, manual testing will not keep pace with deployment frequency. |
| **Effort** | 3-5 days (write Playwright tests for 5-10 critical flows, configure CI runner with browser, add to PR checks) |
| **Priority** | **P2** |

### 2.4 Contract Testing (OpenAPI Generated Client)

| Attribute | Detail |
|-----------|--------|
| **What** | No contract testing between frontend and backend. The Next.js frontend uses hand-written API calls; no generated TypeScript client from OpenAPI spec. |
| **Why it matters** | Backend API changes can silently break the frontend. Type mismatches between frontend expectations and backend responses are only caught at runtime. |
| **Effort** | 2-3 days (export OpenAPI spec from FastAPI, generate TypeScript client with `openapi-typescript-codegen`, integrate into frontend build) |
| **Priority** | **P2** |

---

## 3. Security (MISSING)

### 3.1 WAF Rules on ALB

| Attribute | Detail |
|-----------|--------|
| **What** | No AWS WAF rules configured. The ALB accepts all traffic without filtering. |
| **Why it matters** | Vulnerable to common web attacks: SQL injection attempts, XSS payloads, request flooding, bot traffic. For a lab informatics platform handling sensitive research data, this is unacceptable. |
| **Effort** | 1-2 days (enable AWS WAF, configure managed rule groups: AWSManagedRulesCommonRuleSet, rate limiting, geo-blocking if needed) |
| **Priority** | **P1** |

### 3.2 Secrets Rotation

| Attribute | Detail |
|-----------|--------|
| **What** | Secrets (API keys, database credentials) are static environment variables. No automated rotation. |
| **Why it matters** | If a secret is compromised, there is no mechanism to rotate it without a deployment. Long-lived secrets increase blast radius of any credential leak. |
| **Effort** | 2-3 days (migrate to AWS Secrets Manager with rotation lambdas, update ECS task definitions to pull from Secrets Manager) |
| **Priority** | **P2** |

### 3.3 Penetration Testing

| Attribute | Detail |
|-----------|--------|
| **What** | No penetration testing has been conducted (internal or third-party). |
| **Why it matters** | Unknown attack surface. Lab informatics platforms handle proprietary research data — a breach could be catastrophic for customer trust and company reputation. Required for SOC 2. |
| **Effort** | 1-2 weeks (engage third-party pen test firm, remediate findings) |
| **Priority** | **P2** |

### 3.4 Dependency Vulnerability Scanning

| Attribute | Detail |
|-----------|--------|
| **What** | No Dependabot, Snyk, or equivalent scanning for known vulnerabilities in Python/Node dependencies. |
| **Why it matters** | Supply chain attacks and known CVEs in dependencies are a top attack vector. Without automated scanning, vulnerable packages persist indefinitely. |
| **Effort** | 0.5 days (enable GitHub Dependabot, or add Snyk to CI pipeline) |
| **Priority** | **P1** |

### 3.5 CSP Headers (Content Security Policy)

| Attribute | Detail |
|-----------|--------|
| **What** | No Content-Security-Policy, Strict-Transport-Security, or other security headers configured on the frontend or API. |
| **Why it matters** | Without CSP, the application is vulnerable to XSS attacks via injected scripts. Missing HSTS means browsers may connect over HTTP. |
| **Effort** | 0.5-1 day (configure Next.js security headers in `next.config.js`, add middleware for API security headers) |
| **Priority** | **P1** |

---

## 4. Infrastructure (PARTIAL)

### 4.1 Terraform Not Applied

| Attribute | Detail |
|-----------|--------|
| **What** | Terraform IaC exists in the repository but has never been applied to create actual AWS infrastructure. Running locally with Docker only. |
| **Why it matters** | Infrastructure is not reproducible. Cannot spin up staging environments, cannot recover from disasters, cannot onboard new engineers to a consistent environment. |
| **Effort** | 2-3 days (review and apply Terraform, set up remote state in S3 + DynamoDB lock, configure CI for `terraform plan` on PRs) |
| **Priority** | **P1** |

### 4.2 No Blue-Green / Canary Deployments

| Attribute | Detail |
|-----------|--------|
| **What** | ECS deployments are rolling updates only. No blue-green or canary deployment strategy. |
| **Why it matters** | A bad deployment affects all users simultaneously. Cannot gradually shift traffic to validate new versions. Rollback requires a full redeployment. |
| **Effort** | 2-3 days (configure ECS blue-green with CodeDeploy, or implement canary via ALB weighted target groups) |
| **Priority** | **P2** |

### 4.3 No Auto-Scaling Policies

| Attribute | Detail |
|-----------|--------|
| **What** | ECS services have fixed task counts (2 for backend, 1 for workers). No auto-scaling based on CPU/memory/request count. |
| **Why it matters** | Cannot handle traffic spikes (e.g., demo day, customer onboarding). Over-provisioning wastes money; under-provisioning causes outages. |
| **Effort** | 1-2 days (configure ECS Service Auto Scaling with target tracking policies on CPU and request count) |
| **Priority** | **P2** |

### 4.4 No Database Migration Automation in CI

| Attribute | Detail |
|-----------|--------|
| **What** | Alembic migration framework exists, but migrations are not run automatically as part of the deployment pipeline. |
| **Why it matters** | Manual migration execution is error-prone. Forgetting to run migrations after a deployment causes application errors. No validation that migrations are safe (e.g., no lock timeouts, no backward compatibility checks). |
| **Effort** | 1 day (add migration step to ECS deployment pipeline, run as pre-deployment task, add migration linting) |
| **Priority** | **P1** |

### 4.5 No Backup Verification

| Attribute | Detail |
|-----------|--------|
| **What** | RDS automated backups are presumably enabled but never tested. No backup restoration drills. |
| **Why it matters** | "Untested backups are not backups." If data loss occurs, there is no confidence that restoration will work or how long it will take. |
| **Effort** | 1 day (document and execute restore procedure, automate periodic restore-to-staging verification) |
| **Priority** | **P2** |

---

## 5. Compliance (MISSING)

### 5.1 SOC 2 Controls

| Attribute | Detail |
|-----------|--------|
| **What** | No SOC 2 Type I or Type II controls implemented. No access control policies, change management documentation, or security incident response plan. |
| **Why it matters** | Enterprise pharma/biotech customers will require SOC 2 certification before purchasing. Starting early avoids a 6+ month scramble later. Many controls (access logs, change management, encryption) are straightforward to implement now. |
| **Effort** | 4-8 weeks (initial gap assessment, implement controls, engage auditor for Type I) |
| **Priority** | **P2** |

### 5.2 Audit Log Export

| Attribute | Detail |
|-----------|--------|
| **What** | No structured audit log export to compliance/SIEM systems. Application events are in application logs but not in a compliance-ready format. |
| **Why it matters** | Compliance frameworks (SOC 2, GxP) require tamper-evident audit trails. Regulators and auditors need structured, queryable access to who-did-what-when. |
| **Effort** | 2-3 days (define audit event schema, implement audit log middleware, export to S3/CloudWatch in immutable format) |
| **Priority** | **P2** |

### 5.3 Data Retention Policies

| Attribute | Detail |
|-----------|--------|
| **What** | No defined data retention or deletion policies. Data grows indefinitely in PostgreSQL and S3. |
| **Why it matters** | Regulatory requirements (GDPR, GxP) mandate defined retention periods. Unbounded data growth increases storage costs and breach exposure. Customers will ask "how long do you keep my data?" |
| **Effort** | 2-3 days (define retention policy document, implement S3 lifecycle rules, create database archival jobs) |
| **Priority** | **P3** |

### 5.4 GDPR Data Deletion Workflow

| Attribute | Detail |
|-----------|--------|
| **What** | No mechanism for users to request data deletion (Right to Erasure). No process to identify and purge all user data across services. |
| **Why it matters** | GDPR Article 17 requires ability to delete all personal data upon request. EU customers and partners will require this. Non-compliance carries fines up to 4% of global revenue. |
| **Effort** | 3-5 days (map all PII storage locations, implement deletion API endpoint, handle cascading deletes across PostgreSQL/S3/Redis/Langfuse, create verification process) |
| **Priority** | **P2** |

---

## Summary Matrix

| Category | Items | P1 | P2 | P3 |
|----------|-------|----|----|-----|
| Observability | 5 | 4 | 1 | 0 |
| Testing | 4 | 0 | 3 | 1 |
| Security | 5 | 3 | 2 | 0 |
| Infrastructure | 5 | 2 | 3 | 0 |
| Compliance | 4 | 0 | 3 | 1 |
| **Total** | **23** | **9** | **12** | **2** |

---

## Recommended Implementation Order

### Sprint 1 (Week 1-2) — P1 Critical Path

1. Sentry error tracking (1 day)
2. Dependency vulnerability scanning (0.5 day)
3. CSP + security headers (0.5 day)
4. WAF rules on ALB (1 day)
5. OpenTelemetry instrumentation (3 days)
6. APM setup (2 days)
7. Uptime monitoring (0.5 day)
8. Apply Terraform to AWS (2 days)
9. Database migration automation in CI (1 day)

**Total: ~12 engineering days**

### Sprint 2 (Week 3-4) — P2 High Value

1. E2E Playwright tests (3 days)
2. Load testing baselines (3 days)
3. Secrets rotation (2 days)
4. Auto-scaling policies (1 day)
5. Blue-green deployments (2 days)
6. PagerDuty alerting (1 day)
7. Audit log export (2 days)

**Total: ~14 engineering days**

### Sprint 3 (Month 2-3) — P2/P3 Long-tail

1. SOC 2 gap assessment + controls (ongoing)
2. Contract testing / OpenAPI client (2 days)
3. GDPR deletion workflow (4 days)
4. Penetration testing (1-2 weeks, external)
5. Backup verification drill (1 day)
6. Data retention policies (2 days)
7. Allure test reporting (1 day)
