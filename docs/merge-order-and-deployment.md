# PR Merge Order & AWS Deployment Plan

---

## PR Merge Order

Merge in this exact sequence. Each PR builds on the previous state of `main`.

### 1. PR #3 — Multi-tenancy and conversation history
**Branch:** `feat/multi-tenancy`
**Why first:** This is the foundational change — adds `org_id` to every table, conversation persistence, and org-based data isolation. Everything else depends on org scoping.

**What it contains:**
- `org_id` column on all data tables (samples, plates, experiments, ELN, protocols, microscopy, conversations)
- `Conversation` + `ConversationMessage` models in PostgreSQL
- Agent persists messages to DB, auto-generates conversation titles
- `get_org_context` FastAPI dependency (X-Org-Id header)
- All API endpoints + all tool handlers filter by org_id
- Frontend sends X-Org-Id on every API call
- Conversation sidebar (replaces task panel)
- Onboarding without workspace step (orgs are admin-created)
- "No access" page for users without an organization

**After merging:** Verify `docker compose up --build`, test that conversations persist across refreshes, test that different org_ids return different data.

---

### 2. PR #4 — UI polish, integrations, file analysis, demo data
**Branch:** `feat/ui-polish-integrations`
**Why second:** Adds features on top of the multi-tenant foundation — tools, UI improvements, demo assets.

**What it contains:**
- `read_file_contents` tool — agent reads uploaded CSV/TXT files
- `fit_dose_response`, `normalize_plate`, `calculate_z_prime`, `qpcr_analysis` tool handlers
- Full pipeline: upload CSV → agent reads → fits IC50 curve
- Integration SVG logos (eLabFTW, Benchling, Dotmatics)
- Benchling + Dotmatics "Coming Soon" cards on Settings
- @ mention dropdown in chat
- Feature request page (/feature-request)
- Anonymised testimonials
- Fixed conversation date display
- Demo CSV files + demo prompts guide + Beatriz demo script

**After merging:** Verify file upload → IC50 analysis works end-to-end, check Settings page shows 3 integration cards, test @ mentions in chat.

**Note:** This PR may have merge conflicts with #3 since both modify `chat-interface.tsx`, `lab-store.ts`, and `tool_executor.py`. Resolve by keeping both sets of changes.

---

### 3. PR #1 — AWS Terraform infrastructure and GitHub Actions CI/CD
**Branch:** `feat/aws-terraform-ci`
**Why last:** Infrastructure doesn't affect application code. Merging after the app is stable ensures CI workflows test the final codebase.

**What it contains:**
- Terraform: VPC, RDS PostgreSQL, ElastiCache Redis, ECS Fargate, ALB, ECR, S3, IAM
- GitHub Actions: backend tests, frontend tests, Docker build, deploy to ECS
- Infrastructure README with deployment instructions

**After merging:** Verify GitHub Actions workflows pass. Don't `terraform apply` until AWS deployment is ready.

---

## AWS Deployment Plan

### Prerequisites

Before deploying:
1. AWS account with admin access
2. AWS CLI configured (`aws configure`)
3. Terraform installed (v1.5+)
4. Domain name ready (e.g. `api.resonantia.io` for backend, `resonantia.io` for frontend)
5. All 3 PRs merged to main
6. GitHub Actions secrets configured

### Phase 1: Foundation (Day 1)

#### 1.1 Terraform Init
```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with real values:
#   db_password, openai_api_key, clerk_secret_key, langfuse keys

terraform init
terraform plan    # review ~25 resources
terraform apply   # creates VPC, subnets, NAT, IGW
```

#### 1.2 Database + Cache
Terraform creates:
- RDS PostgreSQL 16 (db.t3.micro, encrypted, 7-day backups)
- ElastiCache Redis 7 (cache.t3.micro)
- Both in private subnets, only accessible from ECS

Note the outputs:
```
rds_endpoint = "resonantia-db.xxxx.us-east-1.rds.amazonaws.com"
redis_endpoint = "resonantia-cache.xxxx.cache.amazonaws.com:6379"
```

#### 1.3 ECR Repositories
Terraform creates two ECR repos. Push the initial images:
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account_id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push backend
docker build -t resonantia-backend ./backend
docker tag resonantia-backend:latest <account_id>.dkr.ecr.us-east-1.amazonaws.com/resonantia-backend:latest
docker push <account_id>.dkr.ecr.us-east-1.amazonaws.com/resonantia-backend:latest

# Build and push temporal-worker
docker build -t resonantia-worker ./backend
docker tag resonantia-worker:latest <account_id>.dkr.ecr.us-east-1.amazonaws.com/resonantia-temporal-worker:latest
docker push <account_id>.dkr.ecr.us-east-1.amazonaws.com/resonantia-temporal-worker:latest
```

### Phase 2: Application Services (Day 1-2)

#### 2.1 ECS Services
Terraform creates:
- ECS Cluster (Fargate)
- Backend task definition (port 8000, env vars for DB/Redis/OpenAI/Clerk/Langfuse)
- Temporal worker task definition (same env vars)
- Backend service (desired count: 1)
- Worker service (desired count: 1)
- CloudWatch log groups

#### 2.2 Load Balancer
Terraform creates:
- ALB in public subnets
- HTTP listener on port 80 → target group → ECS backend
- Health check on `/health`

Verify: `curl http://<alb_dns_name>/health` returns `{"status": "ok"}`

#### 2.3 S3 Bucket
Terraform creates:
- `resonantia-uploads-production` bucket
- Versioning enabled, encrypted, public access blocked
- ECS task role has read/write access

Update backend config to use S3 instead of local filesystem (future — for now, ECS task uses an EFS mount or ephemeral storage).

### Phase 3: Temporal (Day 2)

#### Option A: Temporal Cloud (recommended for production)
- Sign up at temporal.io/cloud
- Create a namespace
- Set `TEMPORAL_HOST` in ECS task definition to Temporal Cloud endpoint
- No self-hosted Temporal infrastructure needed

#### Option B: Self-hosted Temporal on ECS
- Additional ECS task definitions for Temporal server + Temporal UI
- Additional RDS instance (or schema) for Temporal's database
- More complex but no external dependency

### Phase 4: Frontend on Vercel (Day 2)

#### 4.1 Connect Vercel
1. Go to vercel.com → Import Git Repository → `teopopescu/resonantia`
2. Set root directory to `frontend`
3. Framework: Next.js (auto-detected)

#### 4.2 Environment Variables in Vercel
```
NEXT_PUBLIC_API_URL=https://api.resonantia.io
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
NEXT_PUBLIC_APP_URL=https://resonantia.io
NEXT_PUBLIC_CONTENTFUL_SPACE_ID=gismnhbb3kki
NEXT_PUBLIC_CONTENTFUL_ACCESS_TOKEN=e7if3JoufyZzs33-...
```

#### 4.3 Deploy
Vercel auto-deploys on push to main. First deploy takes ~2 minutes.

### Phase 5: DNS & SSL (Day 2-3)

#### 5.1 Backend Domain
1. Create ACM certificate for `api.resonantia.io` in us-east-1
2. Add CNAME validation record in DNS
3. Uncomment HTTPS listener in Terraform ALB config
4. `terraform apply` — ALB now serves HTTPS on 443

#### 5.2 Frontend Domain
1. In Vercel: Settings → Domains → Add `resonantia.io` and `www.resonantia.io`
2. Update DNS: CNAME `resonantia.io` → `cname.vercel-dns.com`
3. Vercel handles SSL automatically

#### 5.3 Update CORS
Backend must allow the production frontend domain:
```python
cors_origins: list[str] = [
    "https://resonantia.io",
    "https://www.resonantia.io",
    "http://localhost:3000",  # keep for local dev
]
```

### Phase 6: CI/CD (Day 3)

#### 6.1 GitHub Secrets
Add to the repository (Settings → Secrets):
```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION=us-east-1
ECR_BACKEND_URL=<account_id>.dkr.ecr.us-east-1.amazonaws.com/resonantia-backend
ECR_WORKER_URL=<account_id>.dkr.ecr.us-east-1.amazonaws.com/resonantia-temporal-worker
ECS_CLUSTER=resonantia-production
ECS_BACKEND_SERVICE=resonantia-backend
ECS_WORKER_SERVICE=resonantia-temporal-worker
```

#### 6.2 Deploy Flow
On push to `main`:
1. GitHub Actions runs tests (backend + frontend)
2. Builds Docker images
3. Pushes to ECR
4. Updates ECS services (force new deployment)
5. ECS pulls new images and does rolling update

### Phase 7: Monitoring & Observability (Day 3-4)

#### 7.1 Already Have
- Langfuse: LLM call tracing (latency, tokens, tools, guardrails)
- CloudWatch: ECS container logs

#### 7.2 Add
- CloudWatch Alarms: CPU > 80%, memory > 80%, 5xx error rate > 1%
- RDS monitoring: connection count, read/write IOPS
- ALB metrics: request count, latency p99, healthy host count
- Optional: Datadog or Grafana for dashboards

### Phase 8: Production Checklist (Day 4)

- [ ] Backend health check returns 200 on production URL
- [ ] Frontend loads on production domain
- [ ] Clerk auth works with production keys (switch from pk_test to pk_live)
- [ ] Chat connects to OpenAI and returns real responses
- [ ] Voice mode works (Whisper STT + TTS)
- [ ] File upload/download works
- [ ] Conversation history persists across sessions
- [ ] Multi-tenancy: two orgs see different data
- [ ] Temporal workflows execute (or graceful fallback)
- [ ] Langfuse traces appear in dashboard
- [ ] GitHub Actions deploy workflow succeeds
- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] CORS configured for production domain
- [ ] Rate limiting in place (ALB or application-level)
- [ ] Database backups verified (RDS automated)
- [ ] Monitoring alerts configured

---

## Cost Estimate (Production)

| Service | Spec | Monthly Cost |
|---|---|---|
| ECS Fargate (backend) | 0.5 vCPU, 1GB RAM | ~$15 |
| ECS Fargate (worker) | 0.5 vCPU, 1GB RAM | ~$15 |
| RDS PostgreSQL | db.t3.micro, 20GB | ~$15 |
| ElastiCache Redis | cache.t3.micro | ~$12 |
| ALB | Fixed + LCU | ~$16 + usage |
| NAT Gateway | Per-hour + data | ~$32 |
| ECR | Storage | ~$1 |
| S3 | Storage + requests | ~$1 |
| CloudWatch | Logs + metrics | ~$5 |
| **Total** | | **~$110-130/month** |
| Vercel (frontend) | Pro plan | $20/month |
| Temporal Cloud | Free tier or $0-200 | $0-200/month |
| **Grand Total** | | **~$130-350/month** |

### Cost Optimization Options
- Use Graviton (ARM) instances for ECS: ~20% cheaper
- Use RDS reserved instances for 1-year commit: ~30% cheaper
- Remove NAT Gateway by using VPC endpoints for ECR/S3: saves ~$32/month
- Use `gpt-4o-mini` as default model: ~10x cheaper per token than gpt-4o

---

## Timeline Summary

| Day | Phase | What Gets Done |
|---|---|---|
| 1 | Foundation | Terraform apply, VPC, RDS, Redis, ECR, push images |
| 1-2 | Application | ECS services running, ALB health check passing |
| 2 | Temporal + Frontend | Temporal Cloud or self-hosted, Vercel deploy |
| 2-3 | DNS & SSL | HTTPS on api.resonantia.io and resonantia.io |
| 3 | CI/CD | GitHub Actions auto-deploy working |
| 3-4 | Monitoring | CloudWatch alarms, production checklist |
| **Total** | | **3-4 days** |
