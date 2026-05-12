# Resonantia AI — Critical Path to Seed Round

## Founders
- Teodor Popescu — Co-Founder & CTO
- Beatriz — Co-Founder

## Timeline Overview (18-24 months to $1M ARR)

```
Month 0          Month 6          Month 12         Month 18         Month 24
  |                |                 |                 |                |
  ▼                ▼                 ▼                 ▼                ▼
  Bootstrap        First Revenue     Seed Close        Scale            $1M ARR
  & Design         $30K ARR          $200K+ ARR        $720K ARR        $1.06M ARR
  Partners         2-3 paying        $2.5-3.5M         10 Lab +         12 Lab +
  (3-5 labs)       customers         raised            5 Enterprise     8 Enterprise
```

---

## Phase 1: Pre-Seed / Bootstrap (Months 1-6)

### Goals
- Secure 3-5 design partners (mid-size biotech, 50-200 people)
- Convert 2-3 to paying customers
- Reach ~$30K ARR
- Begin Automata/LINQ partnership conversation

### Key Activities
| Month | Activity | Deliverable |
|-------|----------|-------------|
| 1-2 | Billing (Stripe) + SSO/SAML + outreach to target labs | Payment infrastructure, 3 signed design partners |
| 2-3 | RBAC + Audit trail + Data export | Enterprise-ready auth and compliance |
| 3-4 | **Experiment Design Agent** (closed-loop reasoning) | Agent analyzes results → proposes next experiment → generates plate map |
| 4-5 | Resonantia MCP server + Benchling import | Ecosystem integration standard, migration path |
| 5-6 | Convert design partners to paid Team/Lab tiers | 2-3 paying customers |

### Metrics to Track
- Design partner engagement (weekly active users)
- Feature requests from partners (signal for PMF)
- NPS / willingness to pay

---

## Phase 2: Seed Preparation (Months 7-12)

### Goals
- Reach $200-300K ARR (seed-ready)
- Close 5 Lab + 2 Enterprise customers
- Refine pitch deck and financial model
- Begin investor conversations

### Key Activities
| Month | Activity | Deliverable |
|-------|----------|-------------|
| 7-8 | Automata LINQ integration (bidirectional closed loop) | Design → execute → analyze → redesign demo |
| 8-9 | Temporal multi-day experiment workflows | DoseResponseScreen, HitConfirmation, SARFollowUp workflows |
| 9-10 | Ontology mapping + GenAI CI/CD evals | ChEBI/BAO/GO mapped data, automated eval pipeline |
| 10-11 | Land 2 Enterprise deals + pitch deck finalized | Signed contracts, data room ready, SOC 2 in progress |
| 11-12 | Close seed round $2.5-3.5M | Term sheet signed |

### Target Investors
- **Tier 1:** Lux Capital, a16z Bio, NFX
- **Tier 2:** Dimension (backed Automata), Octopus Ventures
- **Accelerators:** Y Combinator Bio (W27 or S27 batch)
- **Strategic:** Danaher Ventures (Automata investor, lab equipment giant)

---

## Phase 3: Post-Seed Scale (Months 13-24)

### Goals
- Scale to $1M+ ARR
- Hire 3 people (2 eng + 1 sales/BD)
- Establish Automata partnership as distribution channel

### Key Activities
| Month | Activity | Deliverable |
|-------|----------|-------------|
| 13-15 | Hire backend engineer + full-stack engineer | Team of 4 |
| 14-16 | Hire sales/BD lead + Lab ASR fine-tuning | Enterprise pipeline, lab jargon voice accuracy |
| 15-18 | SDK + Dashboards + Notifications + Collaboration | Developer platform + PI-facing views |
| 18-20 | Experiment Design ML model + Automata co-sell live | Proprietary model training on customer data, joint pipeline |
| 20-24 | Self-hosted vLLM + scale to 12 Lab + 8 Enterprise | VPC deployment for pharma, $1M+ ARR |

### Hiring Plan ($3M Seed Budget — 24 months)
| Allocation | Amount | Detail |
|------------|--------|--------|
| Engineering (2 hires) | $600K | Backend + full-stack |
| Sales/BD (1 hire) | $250K | Enterprise pipeline + partnerships |
| Founder salaries (2x) | $480K | $10K/month each |
| Infrastructure | $200K | AWS, Temporal Cloud, monitoring |
| Compliance/Legal | $150K | SOC 2 Type II, IP protection |
| Marketing/Events | $120K | SLAS, content, demo videos |
| Buffer | $200K | Contingency |
| **Total spend** | **$2M** | **$1M runway buffer** |

---

## Seed Round Targets

| Metric | Conservative | Target | Stretch |
|--------|-------------|--------|---------|
| Raise | $2M | $3M | $4.5M |
| Pre-money valuation | $10M | $15-18M | $22M |
| Dilution | 20% | 17-20% | 15-18% |
| Runway | 18 months | 24 months | 30 months |

Healthcare/biotech SaaS median seed in 2026: $4-5M (skewed by clinical-stage biotechs). For software-only lab informatics with 2 founders: **$2.5-3.5M at $15-18M pre-money** is realistic.

---

## ARR Benchmarks

| Milestone | ARR | Customers (blended $40K ACV) | Timeline |
|-----------|-----|------|----------|
| First revenue | $30K | 3 Team | Month 4-6 |
| Seed-ready | $200K | 5 Lab + 2 Enterprise | Month 9-12 |
| Post-seed growth | $720K | 10 Lab + 5 Enterprise | Month 18 |
| Series A ready | $1M+ | 12 Lab + 8 Enterprise | Month 20-24 |

---

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Benchling cuts pricing / adds AI | Competitive pressure | Move fast on closed-loop differentiation; Benchling is system of record, we're system of action |
| Enterprise sales cycle too long | Slower ARR growth | Start with Team tier self-serve; use design partners for warm enterprise intros |
| 2-person team capacity | Can't ship fast enough | Prioritize loop-closing features (Experiment Design Agent, MCP) over polish features |
| Automata partnership doesn't materialize | Lose distribution channel | Parallel outreach to Medra, Hamilton, Opentrons |
| K-Dense / Potato build lab informatics | Direct competition on closed loop | Our wet-lab specificity (plate mapping, worklists, liquid handlers) is hard to replicate |
| Closed loop too ambitious for 2 founders | Overextend, ship nothing | Graduated autonomy: ship Level 2 (suggest) first, Level 4 (autopilot) post-seed |

---

## The Narrative for Investors

> **Positioning (updated — aligned with BVP thesis on closed-loop lab infrastructure):**
>
> "Resonantia is the agentic operating system that closes the loop between computational experiment design and wet lab execution. We sit at the center of BVP's three principles for biology-native infrastructure:
>
> **Data:** Ontology-mapped, multi-modal lab data (plates, images, assay results, protocols) feeding both internal ML and ecosystem data companies.
>
> **Agentic AI:** 32 tools orchestrated by Claude, with autonomous experiment design — the agent analyzes results and proposes the next experiment, not just the next plate map.
>
> **Closed-loop automation:** Native integration with Automata LINQ for robotic execution, with Temporal workflows managing multi-day experiment cycles.
>
> We're not replacing Benchling. Benchling is a system of record. We're building a system of action — the layer that turns disconnected lab tools into an autonomous research loop. Every experiment run through Resonantia trains our proprietary experiment design model, creating a data flywheel competitors can't replicate."
>
> _See: docs/strategy-closed-loop-lab-os.md for full strategic positioning._

---

## Industry Context

- **Lab informatics market:** ~$4.5B (2025), 8-10% CAGR
- **Benchling:** $210M ARR, $6.1B valuation, $175K ACV, 1,200 customers
- **Only 13.4%** of SaaS startups reach $1M ARR within 3 years
- **Median time** to $1M ARR: 2-5 years from first monetization
- AI-native products in vertical SaaS are compressing these timelines significantly
