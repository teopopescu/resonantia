# Resonantia Infrastructure

Terraform configuration for deploying the Resonantia backend on AWS.

The frontend deploys separately on Vercel and is not managed by this Terraform configuration.

## Architecture

- **VPC** with public/private subnets across 2 AZs
- **ECS Fargate** running backend API and Temporal worker containers (≥2 tasks each)
- **ALB** with HTTPS-only listener (HTTP→HTTPS redirect), TLS-1.3 policy
- **RDS PostgreSQL 16**, Multi-AZ, KMS-encrypted, 30-day backups, Performance Insights on
- **ElastiCache Redis 7** as a replication group with auto-failover, at-rest + transit encryption, AUTH token
- **ECR** for Docker image storage
- **S3** for file uploads (microscopy images, plate data, etc.), SSE-KMS, public access blocked
- **AWS Secrets Manager** for every credential (DB password, LLM API keys, Clerk, Langfuse, Redis AUTH) under a customer-managed KMS key
- **CloudWatch Logs** with 90-day retention, encrypted with the same CMK

See `docs/aws-prod-readiness-audit.md` for the full hardening status (Wave 1 blockers landed; Wave 2/3 tracked separately).

## Prerequisites

1. [Terraform](https://developer.hashicorp.com/terraform/install) ~> 1.5
2. AWS CLI configured with credentials (`aws configure`)
3. Docker for building container images

## First-time deploy

This stack uses an **S3 remote backend with DynamoDB locking** — required for safe collaboration. The bucket and lock table that hold the state are themselves created by a small bootstrap stack.

### Step 1 — Bootstrap the state backend (one-time, per AWS account)

```bash
cd infrastructure/terraform/bootstrap
terraform init
terraform apply -var "project_name=resonantia"
# Note the output: state_bucket and state_lock_table.
```

This creates `resonantia-terraform-state` (versioned, KMS-encrypted, public-access blocked) and `resonantia-terraform-locks` (PAY_PER_REQUEST DynamoDB table with PITR).

The bootstrap stack uses a **local backend** on purpose (chicken-and-egg). The resulting `bootstrap/terraform.tfstate`:

- **Do NOT commit it** to git. `.gitignore` already excludes `*.tfstate`, but the directive is named here so nobody overrides that rule.
- Back it up to an out-of-band encrypted store (1Password vault, an S3 bucket in a different account, an encrypted USB held by an officer).
- You only re-run the bootstrap stack to update the KMS key or the lock table — not on regular deploys.

### Step 2 — Initialize the main stack against the remote backend

```bash
cd infrastructure/terraform
terraform init \
  -backend-config="bucket=resonantia-terraform-state" \
  -backend-config="dynamodb_table=resonantia-terraform-locks" \
  -backend-config="region=us-east-1" \
  -backend-config="encrypt=true"
```

### Step 3 — Configure variables

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your actual values:
#   db_password         — bootstrap value, will be overwritten by Secrets Manager rotation
#   openai_api_key
#   clerk_secret_key
#   langfuse_public_key, langfuse_secret_key
#   acm_certificate_arn — optional; leave blank to provision an ACM cert for var.domain_name
#   domain_name         — e.g. api.resonantia.io
```

### Step 4 — Plan and apply

```bash
terraform plan
terraform apply
```

After apply, every credential lives in Secrets Manager. Rotate via the AWS console or `aws secretsmanager rotate-secret` — Terraform's lifecycle blocks ignore `secret_string` changes so it doesn't fight rotation.

## Pushing Docker images to ECR

```bash
# Authenticate Docker with ECR (region-aware)
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin \
    $(terraform output -raw ecr_backend_url | cut -d'/' -f1)

# Build and push backend
cd ../../backend
docker build -t resonantia-backend .
docker tag resonantia-backend:latest $(terraform output -raw ecr_backend_url):latest
docker push $(terraform output -raw ecr_backend_url):latest

# Build and push temporal worker
docker build -f Dockerfile.worker -t resonantia-temporal-worker .
docker tag resonantia-temporal-worker:latest $(terraform output -raw ecr_worker_url):latest
docker push $(terraform output -raw ecr_worker_url):latest

# Force a new deployment so ECS pulls the new image
aws ecs update-service \
  --cluster resonantia-production \
  --service resonantia-production-backend \
  --force-new-deployment
```

## HTTPS

ALB serves HTTPS-only; HTTP returns a 301 redirect to HTTPS. The certificate comes from one of two places:

- **You already have a cert** — set `acm_certificate_arn` in `terraform.tfvars`. The stack uses it directly.
- **Provision via ACM** — leave `acm_certificate_arn` empty. Terraform creates an ACM certificate for `var.domain_name` with DNS validation. Add the validation `CNAME` shown in `terraform plan` to your DNS provider, then re-apply once the cert validates.

## Costs

With the hardened defaults (Multi-AZ RDS, replicated ElastiCache, 2 Fargate tasks, NAT GW, Secrets Manager, KMS, 90-day logs):

- ECS Fargate (2 backend + 2 worker, t3.micro-equivalent): ~$50/month
- RDS Multi-AZ db.t3.micro + 30-day backups + Perf Insights: ~$50/month
- ElastiCache primary+replica cache.t3.micro: ~$25/month
- ALB: ~$22/month
- NAT GW: ~$32/month + data transfer
- KMS + Secrets Manager + S3 + CloudWatch logs: ~$15/month

Rough total **~$200/month** for production. Wave-2 fixes (VPC endpoints, log lifecycle to Glacier) are designed to cut NAT egress and CloudWatch storage further.

## Migration runbooks

### From the pre-hardening stack

If you applied an older version of this Terraform (single-AZ RDS, plaintext task-env secrets, AES256 S3, single-node ElastiCache cluster), the next `terraform apply` is **not** a no-op. The two changes that need a manual migration step:

#### 1. ElastiCache: cluster → replication group

The hardening replaces `aws_elasticache_cluster.main` with `aws_elasticache_replication_group.main`. Terraform on the new code does not see the old resource address in state — it will plan to create the new replication group but will leave the old single-node cluster running, billing forever.

```bash
# 1. Identify the old resource in state.
terraform state list | grep elasticache_cluster

# 2. Delete it from state and from AWS (Terraform won't manage it any more).
terraform state rm aws_elasticache_cluster.main
aws elasticache delete-cache-cluster \
  --cache-cluster-id resonantia-production-redis \
  --region us-east-1

# 3. Apply the new code.
terraform apply
```

Plan a brief Redis outage during the cutover.

#### 2. ECS task definitions: env-var secrets → Secrets Manager

The hardening removes secret values from the `environment` block of each task definition and references Secrets Manager via `secrets`. The first apply on an existing cluster:

- Creates new task-definition revisions.
- ECS rolls services to the new revisions one task at a time (no downtime if `desired_count >= 2`, which the hardening also enforces).

The application code must read each secret as the env var the task injects (`DB_PASSWORD`, `OPENAI_API_KEY`, `CLERK_SECRET_KEY`, `LANGFUSE_*`, `REDIS_AUTH_TOKEN`). The backend already does — no code change.

## Where the audit log of these decisions lives

`docs/aws-prod-readiness-audit.md` — the source of truth for what's done, what's deferred, and why. The Wave 1 entries (B1–B6) are implemented in this directory. Wave 2/3 entries are tracked there.
