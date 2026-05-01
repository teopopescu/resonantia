# Resonantia — Subagents & Agent Context Protocol (ACP) Plan

## Current Architecture: Single Agent

```
User → Claude (single agent, 32 tools) → results
```

One agent handles everything: plate mapping, data analysis, literature search, ELN writing, protocol design, experiment design. This works now but will hit limits as tool count grows beyond ~50 and context windows fill with tool definitions + conversation history + results.

---

## Why Subagents

| Problem | Impact | Subagent Solution |
|---|---|---|
| **Context window bloat** | 32 tool definitions + history + results compress useful context | Each subagent only loads its own tools (~5-8) |
| **No specialization** | One system prompt must cover all domains | Data analysis agent reasons differently than protocol design agent |
| **No parallelism** | "Analyze plate A and plate B" runs sequentially | Subagents can run in parallel |
| **Cross-platform actions** | Can't coordinate with external agents (Automata LINQ) | ACP enables agent-to-agent delegation |

---

## Target Architecture: Orchestrator + Subagents

```
User → Orchestrator Agent
         ├── Plate Design Agent
         │     Tools: create_plate_map, cherry_pick, serial_dilution,
         │            generate_worklist, get_plate_map_details
         │
         ├── Data Analysis Agent
         │     Tools: fit_dose_response, normalize_plate, calculate_z_prime,
         │            qpcr_analysis, get_processing_results
         │
         ├── Literature Agent
         │     Tools: search_literature (PubMed/bioRxiv), RAG over papers
         │
         ├── ELN Agent
         │     Tools: create_eln_entry, query_eln_entries, get_eln_entry,
         │            submit_eln_entry
         │
         ├── Protocol Agent
         │     Tools: create_protocol, query_protocols, check_protocol_inventory,
         │            calculate_dilution
         │
         ├── Sample Agent
         │     Tools: lookup_sample, check_inventory, add_sample,
         │            get_expiring_samples, get_sample_stats
         │
         └── Experiment Design Agent (already built)
               Tools: design_next_experiment (chains analysis → recommendation → plate)
```

### How Delegation Works

```
User: "Analyze the dose-response data from experiment 42,
       write up the results in an ELN entry, and design
       the followup experiment"

Orchestrator:
  1. → Data Analysis Agent: "Fit dose-response for experiment 42"
     ← Returns: IC50 values, Z-prime, curve parameters

  2. → ELN Agent: "Create entry with these results"
     ← Returns: ELN entry ID, formatted content
     (receives context from step 1)

  3. → Experiment Design Agent: "Design followup based on these results"
     ← Returns: recommendation + plate map + worklist
     (receives context from step 1)

  4. Orchestrator synthesizes final response to user
```

### Orchestrator Responsibilities

- Parse user intent and determine which subagents to invoke
- Route context between subagents (output of one becomes input of next)
- Handle parallel vs sequential execution
- Synthesize final response from subagent results
- Maintain conversation history at the top level
- Enforce org_id scoping across all subagent calls

---

## Agent Context Protocol (ACP) for Resonantia

ACP provides structured communication between agents — both internal subagents and external agents (Automata LINQ, Benchling, etc.).

### Use Case 1: Agent Discovery

External systems discover Resonantia's agent capabilities via a structured manifest:

```json
{
  "agent": "resonantia",
  "version": "1.0",
  "capabilities": [
    {
      "name": "plate_design",
      "description": "Design plate maps with cherry-pick, serial dilution, replicates",
      "accepts": ["compound_list", "concentration_range", "plate_format"],
      "returns": ["plate_map", "worklist"]
    },
    {
      "name": "data_analysis",
      "description": "Fit dose-response curves, calculate Z-prime, normalize plates",
      "accepts": ["assay_data", "control_wells"],
      "returns": ["ic50_values", "z_prime", "normalized_data"]
    },
    {
      "name": "experiment_design",
      "description": "Analyze results and recommend followup experiments",
      "accepts": ["experiment_id", "experiment_query"],
      "returns": ["recommendation", "plate_map", "worklist"]
    }
  ]
}
```

Automata LINQ queries this manifest to understand what it can delegate to Resonantia. Resonantia queries LINQ's manifest to understand what execution capabilities are available.

### Use Case 2: Cross-Platform Agent Communication (Automata Partnership)

This is the closed-loop play:

```
┌─────────────────┐         ACP          ┌─────────────────┐
│   RESONANTIA    │◄────────────────────►│  AUTOMATA LINQ  │
│                 │                       │                 │
│  "Design plate, │  ──── delegate ────► │  "Execute this   │
│   analyze data" │                       │   worklist on    │
│                 │  ◄── report back ──── │   robotic bench" │
│                 │                       │                 │
│  Agent actions: │                       │  Agent actions: │
│  - Design plate │                       │  - Queue run     │
│  - Generate     │                       │  - Monitor       │
│    worklist     │                       │    execution     │
│  - Analyze      │                       │  - Report errors │
│    results      │                       │  - Return data   │
│  - Recommend    │                       │                 │
│    followup     │                       │                 │
└─────────────────┘                       └─────────────────┘
```

**Flow:**

1. Scientist tells Resonantia: "Run a dose-response screen for these 20 compounds"
2. Resonantia's Plate Design Agent creates plate map + worklist
3. Resonantia sends ACP message to LINQ: `{action: "execute_worklist", worklist: {...}, callback: "resonantia://results"}`
4. LINQ executes on robotic bench, monitors run
5. LINQ sends ACP callback to Resonantia: `{status: "complete", results: {...}, errors: [...]}`
6. Resonantia's Data Analysis Agent processes results
7. Resonantia's Experiment Design Agent recommends followup
8. Cycle repeats (closed loop)

### Use Case 3: Multi-Org Agent Federation

For CROs or large pharma with multiple teams:

```
Admin Agent (CRO-level)
  ├── Client A Agent (org_id: org_client_a)
  │     └── Full Resonantia subagent stack, isolated data
  ├── Client B Agent (org_id: org_client_b)
  │     └── Full Resonantia subagent stack, isolated data
  └── Shared Resource Agent
        └── Cross-client inventory, shared protocols
```

ACP handles:
- **Context boundaries** — Client A's agent cannot see Client B's data
- **Delegation rules** — Admin agent can delegate to any client agent
- **Shared resources** — Shared protocol library accessible to all client agents with read-only access

### Use Case 4: Benchling/Dotmatics Integration via ACP

Instead of REST API connectors, Resonantia communicates with Benchling's agent:

```
Resonantia Agent: "Import experiment EXP-2024-001 from Benchling"
  → ACP → Benchling Agent: {action: "export_experiment", id: "EXP-2024-001"}
  ← ACP ← Benchling Agent: {experiment: {...}, notebook_entries: [...], entities: [...]}
Resonantia Agent: maps to local schema, creates experiment + ELN entry
```

This is more robust than REST because:
- The Benchling agent handles data format negotiation
- Schema mapping happens at the agent level, not the API level
- Retries and error handling are agent-to-agent, not HTTP-level

---

## ACP Message Format (Draft)

```json
{
  "protocol": "acp/1.0",
  "from": "resonantia",
  "to": "automata-linq",
  "action": "execute_worklist",
  "context": {
    "experiment_id": "exp-42",
    "org_id": "org_client_a",
    "priority": "normal"
  },
  "payload": {
    "worklist": {
      "format": "echo-csv",
      "transfers": [...]
    },
    "plate_map": {
      "plate_type": "96",
      "well_mappings": [...]
    }
  },
  "callback": {
    "uri": "resonantia://results/exp-42",
    "expects": ["run_status", "well_data", "errors"]
  }
}
```

---

## Implementation Roadmap

| Phase | When | What |
|---|---|---|
| **Phase 1: Internal subagents** | Month 12-15 (post-seed) | Split single agent into orchestrator + 4 subagents (data, plates, ELN, design). Same LLM, same DB, just scoped tool sets and system prompts. |
| **Phase 2: MCP as foundation** | Month 9-12 | Resonantia MCP server (already built) is the precursor to ACP — external tools can already call Resonantia capabilities. |
| **Phase 3: Automata ACP** | Month 12-18 | Bidirectional agent communication with LINQ. Resonantia delegates execution, LINQ reports results. Requires LINQ API access + callback mechanism. |
| **Phase 4: Federation** | Month 18+ | Multi-org agent isolation. Admin agents delegating to per-client agents. Shared resource agents for protocol libraries. |

### Phase 1 Technical Approach

No new infrastructure needed — subagents are just separate LLM calls with scoped tools:

```python
class SubAgent:
    def __init__(self, name: str, tools: list[str], system_prompt: str):
        self.name = name
        self.tools = tools  # subset of TOOL_HANDLERS
        self.system_prompt = system_prompt

    async def run(self, message: str, context: dict, org_id: str) -> str:
        # Same as agent.chat() but with scoped tools and custom prompt
        ...

class Orchestrator:
    subagents = {
        "data_analysis": SubAgent("data_analysis", [...], "You are a data analysis specialist..."),
        "plate_design": SubAgent("plate_design", [...], "You are a plate design specialist..."),
        "eln": SubAgent("eln", [...], "You are an ELN specialist..."),
        "experiment_design": SubAgent("experiment_design", [...], "You design experiments..."),
    }

    async def route(self, message: str, org_id: str) -> str:
        # Determine which subagent(s) to invoke
        # Execute sequentially or in parallel
        # Synthesize results
        ...
```

### Phase 3 Technical Approach

ACP over Temporal workflows:

```python
@workflow.defn
class CrossPlatformExperimentWorkflow:
    @workflow.run
    async def run(self, experiment_id: str):
        # Step 1: Design plate (Resonantia subagent)
        plate = await workflow.execute_activity(design_plate, ...)

        # Step 2: Execute on LINQ (ACP message to Automata)
        run_id = await workflow.execute_activity(send_acp_to_linq, plate.worklist)

        # Step 3: Wait for LINQ callback (Temporal signal)
        results = await workflow.wait_condition(lambda: self.linq_results is not None)

        # Step 4: Analyze results (Resonantia subagent)
        analysis = await workflow.execute_activity(analyze_results, results)

        # Step 5: Design followup (Resonantia subagent)
        followup = await workflow.execute_activity(design_followup, analysis)

        return followup
```

---

## Relationship to Existing Infrastructure

| Component | Current Role | ACP Role |
|---|---|---|
| **MCP Server** | Exposes 15 tools to external clients | Foundation — tool-level integration |
| **Temporal** | Workflow orchestration (planned) | Durable execution of cross-agent workflows |
| **Tool Registry** | Redis-backed tool schemas | Subagent capability manifest |
| **Agent chat loop** | Single agent, 32 tools | Orchestrator routing to subagents |
| **Experiment Designer** | Single-call analysis + recommendation | Subagent for experiment design |

---

## Key Decisions

1. **MCP first, ACP later** — MCP (tool-level) is simpler and already built. ACP (agent-level) adds delegation, context passing, and multi-agent coordination. Ship MCP integration with Automata first, upgrade to ACP when the closed loop is proven.

2. **Subagents share the database** — No need for separate databases per subagent. They all query the same PostgreSQL via `async_session_factory`, scoped by `org_id`. The isolation is at the tool/prompt level, not the data level.

3. **Orchestrator is an LLM call** — The orchestrator itself is a Claude call with a routing system prompt. It doesn't need a custom router — the LLM decides which subagent to invoke based on the user's intent.

4. **ACP is transport-agnostic** — Could be HTTP callbacks, WebSockets, Temporal signals, or message queues. Start with Temporal signals (already have the infra) and standardize later.
