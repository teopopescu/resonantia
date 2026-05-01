# Architecture diagrams

## Files

- **`prod.drawio`** — production AWS architecture (post-PR #12 hardening) and the backend agent topology (PR #9). Two pages in one file:
  1. _Production AWS infrastructure_ — VPC + 2 AZs, ECS Fargate, RDS Multi-AZ, ElastiCache replication group, KMS-protected Secrets Manager + S3 + CloudWatch, the Terraform state bootstrap stack, and the external SaaS band (Vercel, Clerk, Anthropic, OpenAI, Temporal Cloud, Grafana Cloud Free, Sentry Free, Langfuse).
  2. _Backend agent topology_ — orchestrator + 5 specialists + critic, scoped tools via `tool_executor`, fail-closed critic on high-stakes operations.

## Opening / editing

The file is plain `.drawio` (mxGraph XML). Open in any of:

- [draw.io desktop](https://www.diagrams.net/) — recommended for editing.
- [diagrams.net web](https://app.diagrams.net/) — File → Open from device.
- VS Code with the [Draw.io Integration](https://marketplace.visualstudio.com/items?itemName=hediet.vscode-drawio) extension.

## Exporting to PNG / SVG

drawio CLI (one-time install: `npm i -g @drawio/drawio-desktop-cli`):

```bash
drawio --export --format png --output prod.png docs/architecture/prod.drawio
drawio --export --format svg --output prod.svg docs/architecture/prod.drawio
```

Or use the GUI: File → Export As → PNG / SVG / PDF.

PNG/SVG exports are gitignored project-wide (`*.png`); commit only the `.drawio` source.

## What's deliberately NOT in the diagram

- **WAF, GuardDuty, CloudTrail, AWS Config** — Wave 3 of the audit, separate PRs.
- **VPC endpoints, ECS auto-scaling, RDS read replica** — Wave 2 of the audit, separate PRs.
- **GitHub Actions OIDC** — audit M8, separate PR.
- **Plan Mode workflow** — not yet built; lives in `docs/agentic-architecture.md` §1.

These are tracked in `docs/aws-prod-readiness-audit.md` so the diagram and the audit doc agree on scope.

## Per-PR provenance

The diagram is the visual companion to:

- **PR #12** — every AWS resource and security boundary on Page 1.
- **PR #9** — the agent topology on Page 2.
- **PR #10** — the multimodal flow into the file registry (Page 2 right side).
- **PR #11** — voice surface lives in the Vercel frontend (Page 1 external band).
- **PR #8** — observability picks (Grafana / Sentry / Langfuse / OnCall) on Page 1's external band.
