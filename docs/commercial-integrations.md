# Commercial Integrations — Partnerships & Requirements

## Overview

This document covers what Resonantia needs to do to commercially integrate with each major lab informatics platform, including partnership programs, API access requirements, and go-to-market strategy.

---

## Benchling

### Partner Program Structure

Benchling has a formal **Partner Program** with two ecosystems:

1. **Services Ecosystem** — for consulting/implementation firms
2. **Technology Ecosystem** — for software companies that integrate with Benchling (this is us)

### Services Partner Categories (from their Solution Brief)

| Category | What They Do | Relevance to Resonantia |
|---|---|---|
| **Advisory Partners** | Change management, strategic consulting | Not relevant — we're a technology partner |
| **Specialist Partners** | Certified for specific services during/post implementation (e.g. PQ testing) | Could be relevant if we offer Benchling integration consulting |
| **Implementation Partners** | Certified for full implementation services | Not our play |

### Certification Requirements (for Services Partners)

To join the program and deliver services to Benchling customers:

1. **Benchling Learning Labs** — complete on-demand courses on Benchling's official learning platform
2. **Written and practical exams** — pass both to earn certification
3. **Embed with Benchling Professional Services** — gain on-the-ground implementation experience as a prerequisite (ramp-to-prime process)
4. **Delivery Assurance** — Benchling oversees implementation checkpoints to ensure quality. This is mandatory for every customer implementation

### What Resonantia Needs to Do for Technology Partnership

The PDF focuses on Services Partners. For **Technology Partners** (which is what Resonantia is), the path is different:

**Step 1: Contact Benchling partnerships team**
- Email: partners@benchling.com
- Pitch: "Resonantia is an agentic lab informatics platform that integrates with Benchling to give scientists natural-language access to their Benchling data — experiments, registry entities, notebook entries — from a single chat interface"
- Key value prop: Resonantia doesn't replace Benchling, it makes Benchling more accessible

**Step 2: Demonstrate a working integration**
- Build the Benchling connector using our `LabIntegration` framework
- You need API access to do this — either from a mutual customer or a sandbox from Benchling
- The connector should show: search experiments, query registry entities, pull notebook entries

**Step 3: Get listed on Benchling Marketplace**
- Benchling has a marketplace/integrations page where partners list their connectors
- Listing requires: documentation, demo, and Benchling's review

**Step 4: Joint go-to-market**
- Co-marketing with Benchling (webinars, case studies)
- Benchling sales team refers customers who need agentic/AI capabilities
- You refer customers who need a full ELN to Benchling

### API Access
- Benchling API is REST-based at `https://{tenant}.benchling.com/api/v2/`
- API keys are per-tenant — each customer generates their own
- No standalone developer sandbox available without a customer relationship
- **Practical path:** find a design partner customer who uses Benchling and will share API access

### Benchling API Endpoints We'd Use

| Resonantia Feature | Benchling API |
|---|---|
| Search experiments | `GET /api/v2/entries?name__contains={query}` |
| Get experiment detail | `GET /api/v2/entries/{id}` |
| Search registry entities | `GET /api/v2/custom-entities?name__contains={query}` |
| Search containers/inventory | `GET /api/v2/containers?name__contains={query}` |
| List plates | `GET /api/v2/plates` |
| Get plate wells | `GET /api/v2/plates/{id}/wells` |
| Search protocols | `GET /api/v2/entries?schema_id={protocol_schema}` |
| Test connection | `GET /api/v2/organizations` |

---

## Dotmatics

### Partnership Path

Dotmatics (acquired by Insightful Science, now part of the Dotmatics portfolio) has a partner ecosystem that includes technology integrations.

**Step 1: Contact Dotmatics partnerships**
- Via dotmatics.com/partners or their business development team
- Dotmatics is actively recruiting integration partners post-acquisition (they bought Genedata, GraphPad Prism, etc.) — they value ecosystem connectors

**Step 2: Get partner API access**
- Dotmatics provides sandbox environments for approved partners
- Their REST API is documented for partners at their developer portal

**Step 3: Build connector**
- Implement `LabIntegration` interface against Dotmatics API
- Key entities: Studies, Experiments, Compounds, Plates, Assay Results

**Step 4: Joint GTM**
- Dotmatics partner ecosystem page listing
- Joint webinars/case studies with mutual customers

### API Endpoints We'd Use

| Resonantia Feature | Dotmatics API |
|---|---|
| Search experiments | `GET /api/rest/v1/experiments?search={query}` |
| Search compounds | `GET /api/rest/v1/compounds?search={query}` |
| Get assay results | `GET /api/rest/v1/studies/{id}/results` |
| Search plates | `GET /api/rest/v1/plates?search={query}` |
| Test connection | `GET /api/rest/v1/system/info` |

### Requirements
- Enterprise API license (customer provides)
- OAuth 2.0 authentication
- Per-customer field mapping configuration (Dotmatics is highly customizable)

---

## LabWare LIMS

### Partnership Path

**Step 1: Join LabWare Integration Partner program**
- Contact via labware.com or their regional sales team
- LabWare has a formal partner program for technology integrations

**Step 2: API access**
- LabWare v7+ has a modern REST API
- Older versions (v6 and below) use SOAP/XML — many large pharma still run these
- Each customer's LabWare is heavily customized — field names, workflows, and data models vary significantly between installations

**Step 3: Build connector**
- Generic connector against REST API
- Per-customer configuration layer for field mapping
- This is where services revenue comes in ($5k-25k per customer setup)

### API Details
- **Authentication:** OAuth 2.0 or Windows Authentication (NTLM) depending on customer setup
- **REST API (v7+):** Standard CRUD for samples, tests, results, batches
- **SOAP API (legacy):** XML-based, requires WSDL parsing — avoid if possible, push customers to upgrade
- **No public documentation** — requires partner agreement to access docs

### Key Entities

| LabWare Entity | Resonantia Mapping |
|---|---|
| Sample | ExternalSample |
| Test / Analysis | ExternalExperiment |
| Result | Experiment results JSON |
| Batch | Could map to PlateMap |
| Specification | Could map to Protocol |

### The Hard Part
Every LabWare installation is different. A pharma company's LabWare might have 500+ custom fields. The integration needs a configuration layer where the customer maps their LabWare fields to Resonantia's normalized model. This is a professional services engagement, not a self-serve feature.

---

## STARLIMS (Abbott)

### Partnership Path

**Step 1: Contact Abbott's STARLIMS partner team**
- Via starlims.com or Abbott Informatics sales
- STARLIMS has a technology partner program

**Step 2: API access**
- STARLIMS v12+ has a modern REST API
- Older versions use the "HTML Bridge" — essentially a programmatic interface that wraps their web UI
- v11 and below: limited API, screen-scraping territory

**Step 3: Build connector**
- Target v12+ REST API only
- STARLIMS is dominant in regulated environments (pharma QC, clinical labs)
- Compliance features (audit trail, electronic signatures) are critical for these customers

### API Details
- **Authentication:** OAuth 2.0 / Windows Auth
- **REST API (v12+):** Modern, well-structured
- **HTML Bridge (legacy):** Avoid — brittle, undocumented
- **Documentation:** Available through Abbott's developer portal (partner access required)

### Key Entities

| STARLIMS Entity | Resonantia Mapping |
|---|---|
| Sample | ExternalSample |
| Test | ExternalExperiment |
| Result | Experiment results |
| Method | ExternalProtocol |
| Instrument | Equipment reference |

### Requirements
- Enterprise license (customer provides)
- Per-customer configuration (STARLIMS is highly customized per site)
- GxP/21 CFR Part 11 compliance considerations — any integration with STARLIMS in a regulated environment needs validation documentation

---

## Sapio Sciences

### Partnership Path

**Step 1: Apply to Sapio Partner Program**
- Sapio is the most startup-friendly of the group
- They actively recruit technology partners for their Jarvis platform
- Contact via sapiosciences.com/partners

**Step 2: Get sandbox access**
- Sapio provides sandbox environments for partners — easier to develop against than Benchling/Dotmatics
- Their developer docs are accessible to partners

**Step 3: Build connector**
- Sapio's data model is cleaner than LabWare/STARLIMS
- Less per-customer customization needed

### API Details
- **Authentication:** API key or OAuth 2.0
- **REST API:** Clean, well-documented
- **Developer portal:** Available to partners

### Key Entities

| Sapio Entity | Resonantia Mapping |
|---|---|
| Experiment | ExternalExperiment |
| Sample | ExternalSample |
| Protocol | ExternalProtocol |
| Data Record | Experiment results |
| Workflow | Could map to Protocol execution |

---

## Commercialization Strategy

### Phase 1: Prove the pattern (now)
- Build integration framework with eLabFTW demo
- Show that the chat can query external data alongside internal data
- This becomes the "integration-ready" story

### Phase 2: First commercial integration (months 1-3)
- Find one design partner customer who uses Benchling or Dotmatics
- They provide API access, you build the connector against their real data
- This becomes the case study and reference

### Phase 3: Partner program applications (months 3-6)
- Apply to Benchling Technology Partner Program with working integration + reference customer
- Apply to Dotmatics partner ecosystem
- Contact Sapio (most startup-friendly, likely fastest to onboard)

### Phase 4: Enterprise integrations (months 6-12)
- LabWare and STARLIMS integrations driven by customer demand
- These are per-customer professional services engagements
- Build the configuration layer, charge $10-25k per integration setup

### Revenue Model for Integrations

| Revenue Stream | Price | Description |
|---|---|---|
| Integration setup (self-serve) | Included in Pro tier | Customer enters API key, we connect |
| Integration setup (enterprise) | $5k-25k one-time | Custom field mapping, validation, testing |
| Integration maintenance | Included in Enterprise tier | Ongoing connector updates |
| Validated integration (GxP) | $15-50k one-time | IQ/OQ/PQ documentation for regulated environments |

### Key Contacts

| Company | Contact Method | Notes |
|---|---|---|
| Benchling | partners@benchling.com | Ask for Technology Partner Program |
| Dotmatics | dotmatics.com/partners | Partner ecosystem team |
| LabWare | labware.com contact form | Integration Partner program |
| STARLIMS | Abbott Informatics sales | STARLIMS partner team |
| Sapio | sapiosciences.com/partners | Most startup-friendly |
