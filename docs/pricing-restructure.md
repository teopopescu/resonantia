# Resonantia — Pricing Restructure

## Why Change: The Current Pricing is Broken

### Current Pricing (from Canva deck)
| Tier | Price | Includes |
|------|-------|----------|
| FREE | $0 | 1 user, 5 plate maps/month, basic processing, 100 samples |
| PRO | $99/user/month | Unlimited plate maps, advanced processing, microscopy, priority support |
| ENTERPRISE | Custom | All PRO + integrations, audit logging, dedicated support |

### The Problem

**$99/user/month is stuck in no-man's land:**

1. **Too expensive for self-serve adoption** — Individual scientists won't pay $99/mo out of pocket. Benchling gives academics free access.
2. **Too cheap to build enterprise ARR** — At $99/user, a 20-person lab pays $24K/year. You need 42 such labs to reach $1M ARR. That's impossible for a 2-person team.
3. **Doesn't match how labs buy** — Lab managers have software budgets ($20-50K/year). They don't think in per-seat terms; they think in per-lab or per-team costs.
4. **Underpriced vs. the market by 5-30x** — Benchling charges $15-20K/year for startups, $50-100K for mid-size, $500K-1M+ for enterprise. Their ACV is $175K. Yours would be ~$6K.

### Market Pricing Reality (Benchling)
| Segment | Benchling Price | Your Current Price | Gap |
|---------|----------------|-------------------|-----|
| Startup (5 users) | $15-20K/year | $6K/year | 3x under |
| Mid-size (20 users) | $50-100K/year | $24K/year | 3-4x under |
| Enterprise (100+ users) | $500K-1M+/year | Undefined | Massive |
| Average ACV | $175K | ~$6K | **29x under** |

Benchling customers are **actively complaining** about $5-7K/user/year pricing and still paying. You have AI capabilities Benchling doesn't — yet you charge less than their startup tier.

---

## New Pricing Model

### Shift: Per-Seat → Per-Lab Tiers

Labs don't buy per-seat. They buy a tool for the team. Flat tiers with user caps align with how budgets work.

---

### Starter (Free)
**Purpose:** Get scientists hooked, generate word-of-mouth

| Feature | Limit |
|---------|-------|
| Users | 2 |
| Plate maps | 3/month |
| AI agent queries | 5/day |
| Data processing | Basic (Z-prime, simple normalization) |
| Sample tracking | 50 items |
| ELN | 5 entries |
| Voice mode | No |
| Integrations | No |

**Why free matters:** Benchling's free academic tier is their #1 growth engine. Scientists who learn on it during grad school bring it to industry jobs.

---

### Team — $500/month ($6,000/year)
**Purpose:** Self-serve for small labs (startups, academic groups)

| Feature | Included |
|---------|----------|
| Users | Up to 10 |
| Plate maps | Unlimited |
| AI agent queries | 100/day |
| Data processing | Full (4PL, normalization, qPCR, Z-prime) |
| Microscopy | Full |
| Sample tracking | Unlimited |
| ELN | Unlimited, PDF export |
| Protocol builder | Full |
| Voice mode | Yes |
| Integrations | eLabFTW |
| Support | Email, 48hr response |

**Target customer:** 3-10 person biotech startup, academic research lab
**ACV:** $6,000

---

### Lab — $2,000/month ($24,000/year)
**Purpose:** Mid-size labs, core revenue tier

| Feature | Included |
|---------|----------|
| Users | Up to 25 |
| Plate maps | Unlimited |
| AI agent queries | Unlimited |
| Data processing | Full + batch processing |
| Microscopy | Full + montage generation |
| Sample tracking | Unlimited + barcode scanning |
| ELN | Unlimited + review workflows |
| Protocol builder | Full + templates |
| Voice mode | Yes |
| Integrations | eLabFTW, Benchling import |
| Dashboards | PI/lab manager views |
| Notifications | In-app + email alerts |
| Support | Email, 24hr response |

**Target customer:** 10-25 person lab at mid-size biotech or pharma R&D site
**ACV:** $24,000

---

### Enterprise — $5,000+/month ($60,000+/year)
**Purpose:** Large pharma, regulated environments

| Feature | Included |
|---------|----------|
| Users | Unlimited (per org) |
| Everything in Lab | Yes |
| SSO / SAML | Yes (Okta, Azure AD) |
| RBAC | Full role hierarchy |
| Audit trail | Complete activity logging |
| Compliance | SOC 2 Type II, 21 CFR Part 11 readiness |
| Integrations | Full (Benchling, Dotmatics, Automata LINQ, custom) |
| Temporal workflows | Long-running experiment orchestration |
| Deployment | Cloud or VPC/on-prem |
| Data residency | Configurable region |
| Support | Dedicated success manager, Slack channel, 4hr response |
| Custom tools | API for adding org-specific agent tools |
| SLA | 99.9% uptime guarantee |

**Target customer:** Pharma R&D division, large biotech (Recursion, Genentech, etc.)
**ACV:** $60,000 - $120,000+ (scales with users and deployment complexity)

---

## Usage-Based AI Pricing (Add-On)

On top of flat tier pricing, add a usage-based component for AI agent queries:

| Tier | Included Queries/Month | Overage |
|------|----------------------|---------|
| Starter | 150 (5/day) | Upgrade to Team |
| Team | 3,000 (100/day) | $0.10/query |
| Lab | Unlimited | — |
| Enterprise | Unlimited | — |

**Why this works:**
- Captures upside from power users on Team tier
- Aligns cost with value (more queries = more productive scientist)
- Standard in AI SaaS (GitHub Copilot, Cursor, Replit)
- Active 10-person Team lab (~5,000 queries/month) → $200 overage → $700/month effective

---

## $1M ARR Math — New vs. Old

### Old Pricing ($99/user/month)
| Target | Seats Needed | Labs (~10 users) | Feasible for 2 founders? |
|--------|-------------|-------------------|--------------------------|
| $1M ARR | 842 | ~84 | No |

### New Pricing (Blended Tiers)
| Tier | ACV | Customers for $1M | Feasible for 2 founders? |
|------|-----|-------------------|--------------------------|
| Team only | $6K | 167 | No |
| Lab only | $24K | 42 | Borderline |
| Enterprise only | $96K | 11 | Yes, but slow sales cycle |
| **Blended** | **$40K** | **25** | **Yes** |

### Realistic Customer Mix at $1M ARR
| Tier | Customers | ARR Contribution |
|------|-----------|-----------------|
| Team | 10 | $60K |
| Lab | 8 | $192K |
| Enterprise | 7 | $750K |
| **Total** | **25** | **$1.002M** |

---

## Pricing Migration Plan

### For Existing Design Partners
- Grandfather current users at Team tier pricing for 12 months
- Use as case studies and references for investor materials

### For New Customers
- Launch new pricing immediately on website
- Remove per-seat pricing from all materials
- Update Canva presentation deck

### Pricing Page Design
- Show Team and Lab pricing publicly (transparent)
- Enterprise shows "Contact us" (standard for this segment)
- Add comparison table vs. Benchling highlighting AI features and lower total cost of ownership

---

## Competitive Pricing Positioning

```
                    PRICE (ACV)
                        │
         $500K+         │                    ● Benchling Enterprise
                        │
         $100K          │         ● Resonantia Enterprise
                        │
          $50K          │    ● Benchling Pro
                        │
          $24K          │  ● Resonantia Lab
                        │
          $15K          │ ● Benchling Startup
                        │
           $6K          │● Resonantia Team
                        │
           Free    ─────●────────────────────────────────
                        │
                     Basic              AI-Native
                    CAPABILITIES ──────────────────►
```

**Key message:** Resonantia offers more capability (AI agents, voice, natural language) at a lower price point than Benchling, while being purpose-built for the AI era.

---

## Revenue Projections (24 months)

| Month | Team | Lab | Enterprise | MRR | ARR |
|-------|------|-----|-----------|-----|-----|
| 3 | 2 | 0 | 0 | $1K | $12K |
| 6 | 3 | 1 | 0 | $3.5K | $42K |
| 9 | 5 | 3 | 1 | $11.5K | $138K |
| 12 | 7 | 4 | 2 | $21.5K | $258K |
| 15 | 8 | 6 | 3 | $31K | $372K |
| 18 | 9 | 7 | 5 | $43.5K | $522K |
| 21 | 10 | 8 | 6 | $53K | $636K |
| 24 | 10 | 8 | 7 | $83.5K | $1.002M |

**Assumptions:**
- Team tier churn: 5%/month (high, self-serve)
- Lab tier churn: 2%/month (moderate, relationship-driven)
- Enterprise tier churn: <1%/month (contract-based)
- Enterprise ACV grows over time as features mature ($60K → $120K)
