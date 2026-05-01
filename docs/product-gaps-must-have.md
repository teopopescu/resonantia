# Resonantia — Must-Have Product Gaps

## Current State Summary

Resonantia has a strong foundation with 9 major features implemented:
- Agentic Chat (32 tools), Plate Map Designer, Worklist Export, Data Processing Pipeline,
  Microscopy Browser, Sample Inventory, ELN, Protocol Builder, Voice Mode

This document identifies what's **missing** to close enterprise deals and reach product-market fit.

---

## Priority 1: Enterprise Blockers (Must ship before first enterprise sale)

### 1.1 SSO / SAML Authentication
- **Current:** Clerk handles auth (Google OAuth, email/password)
- **Gap:** No SAML/SSO support — enterprises with Okta/Azure AD cannot enforce their identity policies
- **Impact:** No SSO = automatic rejection by any company >50 people
- **Effort:** ~2 weeks (Clerk supports SAML on Enterprise plan)
- **Action:** Upgrade Clerk plan, enable SAML, test with Okta/Azure AD

### 1.2 Role-Based Access Control (RBAC)
- **Current:** Basic org membership via Clerk (member or not)
- **Gap:** No granular roles — labs need:
  - `admin` — manage org, billing, integrations
  - `pi` (principal investigator) — approve ELN entries, manage team
  - `scientist` — full lab access, create experiments
  - `reviewer` — read-only + approve/reject ELN entries
  - `read-only` — view dashboards, no modifications
- **Impact:** Compliance teams require role separation for audit purposes
- **Effort:** ~2-3 weeks (Clerk Organizations + custom role middleware)
- **Action:** Define role schema, add role checks to all API endpoints, build admin UI

### 1.3 Audit Trail & Activity Logging
- **Current:** ELN has immutable submission (draft → submitted), but no system-wide activity log
- **Gap:** Need to log: who accessed what data, when, from which IP, what actions were taken
- **Impact:** Required for GxP environments, 21 CFR Part 11 adjacent compliance
- **Effort:** ~3-4 weeks (event sourcing middleware + audit log table + viewer UI)
- **Action:** Add audit middleware to FastAPI, create `audit_log` table, build log viewer in admin panel
- **Schema:**
  ```
  audit_log:
    id, timestamp, user_id, org_id, action, resource_type,
    resource_id, details_json, ip_address, user_agent
  ```

### 1.4 SOC 2 Type II Readiness
- **Current:** No formal security posture documented
- **Gap:** Enterprise procurement requires SOC 2 or equivalent security documentation
- **Impact:** Deals stall at procurement/legal review without it
- **Effort:** 3-6 months (process, not just code)
- **Action:** Engage a SOC 2 automation platform (Vanta, Drata), implement required controls, begin audit

### 1.5 Data Export & Portability
- **Current:** PDF export for ELN, CSV worklist export
- **Gap:** No bulk data export for experiments, plate maps, samples, conversation history
- **Impact:** Enterprises won't adopt without an exit strategy — procurement requires it
- **Effort:** ~1-2 weeks
- **Action:** Add `/api/v1/export` endpoints for all major entities (JSON, CSV, XLSX)

---

## Priority 2: Product-Market Fit (Must ship before seed raise)

### 2.1 Real Integrations (Beyond Framework)
- **Current:** eLabFTW client implemented; Benchling and Dotmatics are framework-only stubs
- **Gap:** Need at least one more working integration to prove the "integration-first" positioning
- **Recommended first target:** Benchling data import (scientists migrating from Benchling)
- **Effort:** ~3-4 weeks
- **Action:** Implement Benchling API client for notebook import, sample sync, and entity mapping

### 2.2 Reporting & Dashboards
- **Current:** All insights go through chat — no visual summary for lab managers/PIs
- **Gap:** PIs and lab managers need at-a-glance views:
  - Experiments this week/month (status breakdown)
  - Assay success rates and Z-prime trends
  - Inventory alerts (expiring samples, low stock)
  - Team activity (who ran what)
- **Impact:** Without dashboards, PIs can't justify the tool to their management
- **Effort:** ~3-4 weeks
- **Action:** Build `/lab/dashboard` page with summary cards, charts (recharts), and alert panels

### 2.3 Webhooks & Notifications
- **Current:** No notification system
- **Gap:** Scientists need proactive alerts:
  - "Z-prime dropped below 0.5 on plate X"
  - "3 samples expiring in 7 days"
  - "ELN entry #42 requires your review"
  - "Worklist generation complete"
- **Effort:** ~2 weeks
- **Action:** Build notification service (in-app + email via AWS SES), webhook registry for external consumers

### 2.4 Collaboration Features
- **Current:** @mentions in chat; ELN is single-author
- **Gap:** Multi-user needs:
  - Shared plate map editing (or at minimum, shared visibility)
  - ELN co-authoring or review workflows
  - @mentions in ELN entries and protocols
  - Team-visible experiment assignments
- **Effort:** ~3-4 weeks
- **Action:** Add assignee fields, review workflow to ELN, shared plate map visibility

### 2.5 Automata LINQ Integration
- **Current:** Not implemented
- **Gap:** This is the key partnership differentiator — need a working demo
- **What it means:** Resonantia designs plate map → generates worklist → pushes to LINQ API → LINQ executes on robotic bench → results flow back to Resonantia for analysis
- **Effort:** ~4-6 weeks (depends on LINQ API access)
- **Action:** Reach out to Automata BD team, get API sandbox access, build bidirectional integration

---

## Priority 3: Post-Seed Enhancements (Nice-to-have, ship after funding)

### 3.1 Instrument Connectivity
- Plate reader data import (BMG, BioTek, Molecular Devices formats)
- Flow cytometry FCS file deeper analysis
- Direct instrument API connections

### 3.2 Batch/Lot Genealogy
- Full chain-of-custody for samples
- Parent-child relationships (aliquots, dilutions)
- Lot tracking with certificate of analysis linking

### 3.3 Protocol Template Marketplace
- Community-shared protocol templates
- Validated protocols with version history
- One-click protocol adoption with reagent inventory check

### 3.4 Mobile App
- Walk-around inventory scanning (barcode/QR)
- Quick sample lookup
- Push notifications for alerts
- Voice mode on mobile

### 3.5 Advanced Compliance
- Full 21 CFR Part 11 compliance (electronic signatures, validated systems)
- EU Annex 11 alignment
- HIPAA considerations for clinical samples

---

## Implementation Priority Matrix

```
                    HIGH IMPACT
                        │
   ┌────────────────────┼────────────────────┐
   │                    │                    │
   │  P1: SSO/SAML     │  P2: Dashboards    │
   │  P1: RBAC         │  P2: LINQ Integ.   │
   │  P1: Audit Trail  │  P2: Benchling     │
   │                    │     Import         │
   │  DO FIRST          │  DO SECOND         │
LOW ├────────────────────┼────────────────────┤ HIGH
EFFORT │                 │                    │ EFFORT
   │  P2: Notifications │  P3: Mobile App    │
   │  P2: Collaboration │  P3: 21 CFR Part11 │
   │  P1: Data Export   │  P3: Instrument    │
   │                    │     Connectivity   │
   │  QUICK WINS        │  DEFER             │
   │                    │                    │
   └────────────────────┼────────────────────┘
                        │
                    LOW IMPACT
```

---

## Estimated Engineering Timeline (2 founders)

| Sprint | Weeks | Deliverable |
|--------|-------|-------------|
| Sprint 1 | Week 1-2 | SSO/SAML + Data Export |
| Sprint 2 | Week 3-5 | RBAC (roles, middleware, admin UI) |
| Sprint 3 | Week 6-9 | Audit trail (middleware, table, viewer) |
| Sprint 4 | Week 10-13 | Dashboards + Notifications |
| Sprint 5 | Week 14-17 | Benchling import integration |
| Sprint 6 | Week 18-21 | Collaboration features |
| Sprint 7 | Week 22-27 | Automata LINQ integration |

**Total: ~27 weeks (6-7 months) for Priority 1 + 2, working in parallel as 2 founders.**

This aligns with the critical path: ship enterprise blockers by Month 3, PMF features by Month 6, partnership integration by Month 7-9.
