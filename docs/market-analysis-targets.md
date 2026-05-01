# Resonantia — Market Analysis: Target Customers & Partners

## Market Overview

- **Lab informatics market:** ~$4.5B (2025), 8-10% CAGR
- **Key incumbents:** Benchling ($6.1B, $210M ARR), Dotmatics (acquired by Insightful Science), LabWare, STARLIMS
- **Emerging:** Scispot (AI-native ELN), Automata (lab automation OS), Recursion (internal platform)

---

## Target 1: Automata — Strategic Partner

### Company Profile
- **What:** Lab automation company building LINQ, an AI-ready orchestration platform (robotic benches + workflow software)
- **Founded:** London, UK
- **Funding:** $45M Series C (January 2026), led by Dimension + Danaher Ventures
- **Customers:** 5 top pharma companies, Francis Crick Institute, Royal Marsden NHS, Bit.bio, Lonza
- **Team:** ~100-150 people
- **Key metric:** 3x throughput increase, 95% reduction in manual interactions

### LINQ Platform
LINQ has three components:
1. **LINQ Canvas** — Node-based workflow designer (no-code)
2. **Python SDK** — Programmatic control for scientists
3. **LINQ Bench** — Configurable robotic hardware (800K+ configurations)

Features: concurrent execution, real-time monitoring, GitHub version control, MCP (Model Context Protocol) AI connectivity, REST API, simulation/digital twin

### The Gap Resonantia Fills

LINQ is explicitly an **execution layer** that connects to external LIMS, ELN, and databases — it does not provide them.

| LINQ Does | LINQ Does NOT Do | Resonantia Fills |
|-----------|-----------------|-----------------|
| Robotic workcell orchestration | Plate map design & logic | Intelligent plate mapping |
| Workflow scheduling & execution | Data analysis & curve fitting | 4PL IC50/EC50, Z-prime |
| Instrument control | Sample/reagent inventory | Barcode tracking, expiry alerts |
| Real-time run monitoring | Lab notebook / documentation | Immutable ELN |
| Python SDK for automation | Natural language lab queries | AI agent with 32 tools |
| Hardware modularity | Microscopy image analysis | Multi-channel FOV browser |

### Partnership Models

**1. Integration Partner (Near-term)**
Resonantia handles upstream (plate design, worklist generation) and downstream (data analysis, ELN documentation). LINQ handles physical execution. Worklist formats (Echo, Hamilton, Opentrons) extend to LINQ format.

**2. AI Layer for LINQ (Strategic)**
LINQ has MCP connectivity and REST API. Resonantia becomes the conversational AI front-end: scientist says "run the dose-response on batch 47" → Resonantia designs plate → generates worklist → triggers LINQ → monitors run → analyzes results. End-to-end voice-activated.

**3. Co-sell / Bundle (Commercial)**
Automata sells hardware + orchestration. Resonantia fills the informatics gap their sales team hears about: "LINQ is great, but what about my plate maps, my data analysis, my ELN?"

### Why Automata First
| Factor | Recursion | Automata |
|--------|-----------|----------|
| Internal eng capacity | Massive | Focused on hardware |
| Build vs. buy | Build | Buy/partner |
| Informatics gap | Partial (Recursion OS) | **Explicitly missing** |
| Deal complexity | Enterprise, long cycle | Partnership, faster |
| Strategic role | Customer | **Distribution partner** |
| Recent funding | Public company | $45M fresh capital |

### Outreach Plan
- **Contact:** BD/partnerships team, or through Danaher Ventures network
- **Pitch:** "We're the AI-native informatics layer your LINQ customers are asking for"
- **Demo:** Show Resonantia designing a plate → exporting worklist → (mock) LINQ execution → results analysis
- **Ask:** API sandbox access for integration development

---

## Target 2: Recursion Pharmaceuticals — Enterprise Customer

### Company Profile
- **What:** TechBio company using AI + cellular imaging for drug discovery
- **Founded:** 2013, Salt Lake City, Utah
- **Public:** RXRX (NASDAQ)
- **Valuation:** ~$2B+
- **Funding:** $500M+ in milestone payments to date
- **Employees:** ~500+
- **Key metric:** 2.2 million samples/week, 50+ petabytes of data

### Recursion OS Platform
- **Data:** 50+ PB across phenomics, transcriptomics, proteomics, ADME, de-identified patient data
- **Labs:** Automated wet labs processing 2.2M samples/week using 1536-well plates
- **Compute:** BioHive-2 supercomputer (504 NVIDIA H100 GPUs, 2 exaflops)
- **AI workflows:** Target nomination, molecular design, clinical development
- **Recent:** Acquired Exscientia (Nov 2024) — data architecture integration challenge

### Where Resonantia Fits

Recursion OS excels at computational drug discovery (target ID, molecular design, clinical strategy). The **last mile** — where scientists physically interact with plates, samples, microscopes, and data — still relies on fragmented tools.

| Recursion Need | Resonantia Capability |
|----------------|----------------------|
| 2.2M samples/week plate ops | Plate mapping + worklist export (Echo, Hamilton) |
| Millions of microscopy images/week | Multi-channel FOV browser |
| IC50/EC50 dose-response analysis | 4PL curve fitting + Z-prime QC |
| 50PB multi-modal data queries | AI agent with 32 tools querying real DB |
| Post-Exscientia tool fragmentation | Integration-first architecture |
| Hands-free lab access | Voice mode (Whisper → Claude → TTS) |
| Audit/compliance needs | Immutable ELN with versioning + PDF export |

### Sales Approach
- **Tier:** Enterprise ($60-120K+ ACV)
- **Champion:** Lab operations manager or head of automation
- **Blocker:** Recursion has significant internal engineering — they may prefer to build
- **Counter:** "Your engineers should focus on drug discovery AI, not reinventing lab informatics. Resonantia is purpose-built for the bench."
- **Deployment:** Must support VPC/on-prem — Recursion won't send 50PB through a SaaS endpoint
- **Timeline:** Long enterprise sale (6-12 months), start with a pilot team

### Risk
Recursion could build competing capabilities internally. Mitigate by:
- Moving fast on features they'd need to rebuild from scratch (agentic chat, voice, NLP plate design)
- Offering deep integration with their existing systems
- Starting with a small team pilot to prove value before broader rollout

---

## Target 3: Mid-Size Biotech (Ideal Customer Profile)

### Profile
- 50-200 employees
- 2-5 lab teams (biology, chemistry, screening, DMPK)
- Currently using Benchling (unhappy with pricing) or spreadsheets + ad-hoc tools
- $20-50K annual software budget per team
- No dedicated informatics staff

### Why They're Ideal
1. **Decision-making speed:** Can sign a $24K contract in weeks, not months
2. **Pain is acute:** Scientists juggling 5+ tools, losing data in handoffs
3. **Budget exists:** $20-50K is within team lead approval authority
4. **Low competition:** Too small for LabWare/STARLIMS, too frustrated with Benchling pricing
5. **Growth potential:** As they grow, upgrade from Lab → Enterprise tier

### Examples to Target
- Series A-C biotech companies in Bay Area, Boston, San Diego, Cambridge UK
- Contract research organizations (CROs) running HTS for clients
- Academic spinouts transitioning to industry

### Sales Motion
- **Channel:** LinkedIn outreach to Heads of Biology / Lab Operations
- **Hook:** "Your scientists spend 40% of their time on data management. What if they could just ask?"
- **Demo:** Live plate design via natural language, voice mode in the lab
- **Close:** Team tier ($500/mo) self-serve, upgrade to Lab ($2K/mo) after 30-day trial

---

## Target 4: Contract Research Organizations (CROs)

### Why CROs
- Run plates for dozens of clients simultaneously
- Desperate for workflow efficiency (margin business)
- Need multi-tenant data isolation (already built in Resonantia)
- Worklist generation is their daily bread — Resonantia's plate mapper is directly valuable
- Less regulatory burden than pharma (research-use-only)

### Examples
- Charles River, Eurofins, WuXi AppTec (large)
- Reaction Biology, Pharmaron, Evotec (mid-size, more accessible)

---

## Competitive Landscape

### Direct Competitors
| Company | Strength | Weakness vs. Resonantia |
|---------|----------|------------------------|
| **Benchling** | Market leader, $6.1B, 1,200 customers | Pre-LLM architecture, no AI agents, pricing complaints |
| **Scispot** | AI-native, transparent pricing | Narrower feature set, no plate mapping |
| **Dotmatics** | Chemistry-focused, Insightful Science backing | Complex, expensive, not AI-native |
| **LabWare** | Enterprise LIMS gold standard | Legacy, on-prem focused, no AI |
| **STARLIMS** | Abbott backing, regulated industries | Heavy, slow to implement, no AI |

### Indirect Competitors
| Company | Overlap | Differentiation |
|---------|---------|----------------|
| **Automata** | Lab workflow orchestration | Hardware-focused; partner not competitor |
| **Geneious** | Molecular biology + notebooks | Sequence-focused, not general lab informatics |
| **eLabFTW** | Open-source ELN | No AI, no plate mapping, no data processing |

### Resonantia's Moat
1. **AI-native from day one** — 32 agentic tools, not AI bolted onto legacy software
2. **Voice-first** — Only lab informatics platform with full voice pipeline
3. **Integration-first** — Connective tissue between existing tools, not a replacement
4. **Runtime tool registry** — Customer-extensible via API, creating deep lock-in
5. **Temporal workflows** — Long-running experiment orchestration no LIMS/ELN offers

---

## Go-to-Market Priority

```
Priority 1 (Month 1-6):     Automata partnership + 3-5 mid-size biotech design partners
Priority 2 (Month 7-12):    Convert partners to paid, land 2 Enterprise deals
Priority 3 (Month 13-18):   CRO segment entry, Automata co-sell live
Priority 4 (Month 19-24):   Recursion pilot, expand Enterprise pipeline
```
