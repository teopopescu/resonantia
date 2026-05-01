# Resonantia — AWS Production-Readiness Audit

**Date:** 2026-05-01
**Scope:** `infrastructure/terraform/` + CI/CD assumptions in `docs/merge-order-and-deployment.md`
**Method:** Read-only review of every `.tf` file plus deployment docs. Findings grouped by severity.

> Use this doc as the punch list for `feat/terraform-prod-hardening`. Items prefixed `B` are blockers (must fix before any external traffic), `M` are major (within 2 weeks of go-live), `m` are minor.

---

## Executive summary

The current Terraform is a sound skeleton — VPC across two AZs, RDS in private subnets, S3 with public access blocked, ECR with image scanning, ECS with separate exec/task roles, deletion protection on RDS. **It is not production-grade as-is.** The blockers are the same ones every "lift it up enough to demo" stack ends with: secrets baked into task envs, no HTTPS, RDS single-AZ, no customer-managed KMS, no Terraform state lock.

Total: **6 blockers, ~28 majors, ~5 minors.**

---

## What's already right (don't undo)

- Two-AZ VPC with public/private subnet pairs (`vpc.tf`).
- RDS and ElastiCache in private subnets, reachable only from ECS SGs.
- Security groups using SG references rather than CIDRs for service-to-service traffic.
- RDS: deletion protection on, automated backups configured, `publicly_accessible = false`, final snapshot on destroy.
- S3: server-side encryption on, versioning on, public access fully blocked.
- ECR: scan-on-push, lifecycle policy retaining last 10 images.
- ECS: Container Insights enabled, separate execution role and task role, health-check on task.
- ALB: cross-AZ across both public subnets.
- Default tags (`project`, `environment`, `ManagedBy`) applied to all resources.

---

## Blockers (B1–B6) — fix before external traffic

### B1 · Secrets in task definition envs
`ecs.tf` lines ~92–103 and ~147–158 inject `DB_PASSWORD`, `OPENAI_API_KEY`, `CLERK_SECRET_KEY`, `LANGFUSE_*` as plain `environment` values. They will surface in CloudWatch task events, the ECS console, and `aws ecs describe-task-definition` for anyone with read.

**Fix:** move every secret to AWS Secrets Manager, reference via `secrets` (`valueFrom`) not `environment`. Grant `secretsmanager:GetSecretValue` and `kms:Decrypt` on the specific ARNs only — not `*`.

### B2 · No HTTPS on the ALB
`alb.tf` ships only the HTTP:80 listener; the ACM cert and HTTPS:443 listener are commented out, no HTTP→HTTPS redirect.

**Fix:** add `aws_acm_certificate` (DNS-validated), HTTPS listener with `ELBSecurityPolicy-TLS13-1-2-2021-06`, redirect HTTP→HTTPS, then tighten the ALB SG to only allow 443 from the world. Cookies/Clerk session tokens are presently transmitted in cleartext.

### B3 · RDS is single-AZ
`rds.tf` `multi_az = false`. AZ failure = ~1–2h RTO with a manual restore. Unacceptable for a paid tier.

**Fix:** `multi_az = true`. Cost delta ≈ +50% on the instance line.

### B4 · No customer-managed KMS
RDS uses default RDS key, S3 uses AES256 (S3-managed), ElastiCache has neither at-rest nor in-transit encryption set.

**Fix:** create a CMK in `kms.tf`, point RDS, S3 (SSE-KMS), and ElastiCache (`at_rest_encryption_enabled = true`, `transit_encryption_enabled = true`, AUTH token from a `random_password`) at it. Add key rotation. This is the prerequisite for any "we control the keys" customer conversation.

### B5 · ECS execution role too broad for secrets
`iam.tf` attaches only the AWS-managed `AmazonECSTaskExecutionRolePolicy`. Once B1 lands, the role must also be allowed to read the specific secret ARNs and decrypt with the CMK from B4 — and *only* those.

**Fix:** add an inline policy with `Resource` set to the secret ARNs, not `*`.

### B6 · No Terraform state locking / remote backend
`main.tf` has the S3 backend block commented out. State lives on a developer laptop. Concurrent applies and lost state are a matter of time.

**Fix:** create `resonantia-terraform-state` (versioning + SSE-KMS + public-access-block) and `resonantia-terraform-locks` (DynamoDB, `LockID` PK), wire the backend block, migrate state.

---

## Majors (M1–M28)

### Networking & edge
- **M1 — VPC endpoints.** Add Gateway endpoints for S3 and DynamoDB; Interface endpoints for `ecr.api`, `ecr.dkr`, `secretsmanager`, `logs`, `kms`. Cuts NAT egress materially and removes the AWS API path from the public internet.
- **M2 — RDS SG egress is `0.0.0.0/0`.** `rds.tf:26–31` should be VPC-scoped (`10.0.0.0/16`) or removed (RDS does not initiate egress).
- **M3 — Redis SG egress is `0.0.0.0/0`.** Same fix as M2.
- **M4 — No WAF.** Attach `aws_wafv2_web_acl` with the AWS Managed Common Rule Set + SQLi rule set + a rate-based rule (e.g., 2,000 req/5min/IP).
- **M5 — No rate limiting / abuse controls.** Either via WAF rate-based rule (cheapest) or a CloudFront distribution in front of ALB.
- **M6 — ALB → ECS in cleartext on `:8000`.** Acceptable inside a VPC but not for compliance-conscious customers. Plan: terminate TLS at ALB; for pharma deployments, run mTLS to the task. Track as "enterprise tier requirement."

### IAM
- **M7 — `logs:*` on `Resource = "*"` in the task role policy.** Scope to the two log group ARNs.
- **M8 — No GitHub Actions OIDC.** Deploy doc assumes long-lived `AWS_ACCESS_KEY_ID` secrets. Add `aws_iam_openid_connect_provider` for `token.actions.githubusercontent.com`, an IAM role with a trust policy keyed to `repo:teopopescu/resonantia:ref:refs/heads/main` (and a separate role for the `pr-plan` workflow).
- **M9 — Backend service and Temporal worker share a task role.** Split: the worker doesn't need the same S3 / Secrets surface as the API. Two roles, two minimal policies.

### Data durability & DR
- **M10 — 7-day backup retention.** Increase to 30. For pharma later, longer.
- **M11 — No read replica or RDS Performance Insights.** Add Performance Insights now (cheap, gives query-level diagnostics). Read replica only when read load justifies it.
- **M12 — ElastiCache is single-node.** Move to `aws_elasticache_replication_group` with `automatic_failover_enabled = true` and a replica in the second AZ.
- **M13 — No S3 lifecycle policies.** Add: `STANDARD_IA` after 30d, `GLACIER` after 180d, expire noncurrent versions after 365d. Critical when microscopy starts landing real images.
- **M14 — No cross-account / cross-region backup.** Phase-2 work, but document RPO and decide.

### Encryption & TLS
- **M15 — ElastiCache plaintext.** Covered by B4; tracked here so ops checklists hit both.
- **M16 — No EBS encryption defaults.** Enforce account-level `aws_ebs_encryption_by_default` with the CMK.

### Observability
- **M17 — Log retention 30d.** Bump to 90d for app logs, 365d for audit/CloudTrail. Cheap.
- **M18 — Zero CloudWatch alarms.** Minimum set: ECS service CPU>80% / mem>85%, ALB 5xx rate>1%, RDS CPU>75%, RDS free storage<20%. Wire to SNS → Slack/PagerDuty.
- **M19 — Container Insights without dashboards.** Build one CloudWatch dashboard so the metric stream is actually used.
- **M20 — RDS Performance Insights off.** See M11.
- **M21 — No VPC Flow Logs.** Send to CloudWatch (or S3 for cost). Required for incident forensics.
- **M22 — No distributed tracing.** Langfuse covers LLM calls, not the rest of the request path. Add OTEL → ADOT collector → CloudWatch X-Ray (or an OTLP endpoint).

### Scaling / HA
- **M23 — `desired_count = 1` on the API service.** Two minimum, with `aws_appautoscaling_target` + a step-scaling policy on CPU. Zero-downtime deploys are impossible at count=1.
- **M24 — No explicit AZ-spread placement.** With Fargate the scheduler tries, but document and enforce.

### Compliance / audit
- **M25 — No S3 access logging.** Add a logging bucket; turn on `aws_s3_bucket_logging` for the artifact bucket.
- **M26 — No CloudTrail.** Org-trail or single-account trail to S3 + CloudWatch Logs. Required for any SOC 2 path.
- **M27 — No GuardDuty / Security Hub / Config.** Enable GuardDuty (cheap), Config recorder + a small starter rule set, Security Hub aggregating. This is the pharma-conversation table-stakes set.
- **M28 — No PII inventory / data classification.** Document which tables contain PII, plus a quarterly review hook.

### Cost guardrails
- **m1 — No `aws_budgets_budget`.** Add a $500/mo budget with 80% / 100% alerts to the founders' email.
- **m2 — `t3.micro` for RDS and Redis.** Fine for design partners, undersized at 5+ active orgs. Reserve right-sizing for after one month of real traffic.
- **m3 — `required_version = ">= 1.5.0"`.** Pin to `~> 1.5`.

### CI/CD
- **m4 — No `terraform plan` gate in PRs.** Add a `terraform plan` step posting the diff as a PR comment, plus a manual approval gate before `apply`.
- **m5 — No drift detection.** Nightly `terraform plan` with Slack alert on non-empty diff.

---

## Repo-level: secret in `.git/config`

Out of Terraform scope but found while auditing: `origin` remote URL embeds a GitHub Personal Access Token (`ghp_…`) in plaintext. Rotate the token, then re-set the remote either with HTTPS-no-token (and use a credential helper) or SSH.

```
git remote set-url origin git@github.com:teopopescu/resonantia.git
```

Add `.git/config` patterns to any future doc-screenshot or repo-share runbooks.

---

## What this doc is not

- It is not a runbook for incident response.
- It is not a SOC 2 / 21 CFR Part 11 control matrix — flagged hooks (CloudTrail, Config, audit logging) are prerequisites, not the work itself.
- It is not a Vercel review. The frontend lives there; do that audit separately.

---

## Roadmap (paired with `feat/terraform-prod-hardening`)

| Wave | Items | Effort |
|---|---|---|
| **Wave 1 — pre-traffic** | B1, B2, B3, B4, B5, B6 | 2–3 days |
| **Wave 2 — first month live** | M1, M2, M3, M7, M8, M10, M12, M17, M18, M23, M25 | ~1 week |
| **Wave 3 — pharma readiness** | M4, M5, M9, M13, M14, M21, M22, M26, M27, M28 | sprint |
| **Wave 4 — polish** | M11, M16, M19, M20, M24, m1–m5 | continuous |

Wave 1 is the contents of `feat/terraform-prod-hardening`. Waves 2–4 land as separate PRs in priority order.
