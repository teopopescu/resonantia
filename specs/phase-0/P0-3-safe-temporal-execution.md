# SPEC: Eliminate Unsafe Temporal + Fix Chat Path

**ID:** P0.3
**Phase:** 0 — Stabilize
**Branch:** `fix/temporal-safe-execution`
**Priority:** P0
**Effort:** 5-6 days
**Dependencies:** P0.1 (provider abstraction), P0.7 (output guardrails)

---

## Problem Statement

The Temporal agent workflow (`agent_workflow.py`) generates arbitrary Python code and executes it via `python -c` in a subprocess. This is:
1. **Unsafe:** Generated code can access the filesystem, network, or database without controls
2. **Unauditable:** No structured trace of what code ran or what it modified
3. **Broken:** The workflow references nonexistent config fields and a missing `TOOLS_FALLBACK` import

Additionally, `chat.py` has three related bugs:
- `await handle.result()` has no timeout — a wedged workflow hangs the HTTP request indefinitely
- `except Exception` catches everything and falls back to direct mode — hides real bugs
- No `org_id` in the workflow input — Temporal tools execute without tenant context

---

## Scope

### In Scope
- Delete `generate_code` and `execute_in_sandbox` activities
- Replace `AgentRunWorkflow` with a safe `AgentToolCallWorkflow` using registered tool handlers
- Add timeout to workflow result await
- Narrow exception handling to Temporal-specific errors
- Add org_id to workflow input
- Ensure Temporal path persists conversation history (same as direct path)

### Out of Scope
- Multi-agent orchestration in Temporal (Phase 4)
- Plan-as-first-class artifact (defer — current scope is single-turn tool execution)
- Approval gates in Temporal (Phase 1)

---

## Architecture

### Current Flow (Broken + Unsafe)

```
chat.py → start AgentRunWorkflow(prompt)
    → activities.llm_plan(prompt) → returns Plan dict
    → activities.generate_code(plan) → LLM writes Python code string
    → activities.execute_in_sandbox(code) → subprocess.run("python", "-c", code)
    → activities.compile_results(output)
    → activities.review_for_hallucinations(results)
    
Fallback: except Exception → agent.chat() direct mode (hides ALL errors)
```

### Target Flow (Safe)

```
chat.py → start AgentToolCallWorkflow(messages, tools, org_id)
    → activity: call_llm(messages, tools) via provider → returns LLMResponse
    → if tool_calls: activity: execute_tool(name, args, org_id) via tool_executor → returns ToolResult
    → feed tool results back → loop until text response or max_iterations
    → activity: persist_conversation(conversation_id, messages)
    → return final response

Fallback: except (TemporalConnectionError, WorkflowServiceError) ONLY → direct mode
All other exceptions → surface to user as error
```

### Key Design Decisions
- Temporal workflow is a **durable version of the same agentic loop** in agent.py — not a separate execution model
- Max 10 tool call iterations per workflow run (prevent infinite loops)
- Each tool execution is its own Temporal activity (individually retriable, timed)
- Conversation persistence happens inside the workflow (not in chat.py after)

### File Changes

```
DELETE (activities): generate_code, execute_in_sandbox, review_for_hallucinations
REWRITE: backend/src/resonantia/workflows/agent_workflow.py
MODIFY: backend/src/resonantia/workflows/activities.py (keep: call_llm, execute_tool, persist)
MODIFY: backend/src/resonantia/api/chat.py
MODIFY: backend/src/resonantia/workflows/worker.py
NEW:  backend/tests/test_temporal_safe_workflow.py
```

---

## Implementation

### Step 1: Define new workflow schema (day 1)

```python
# backend/src/resonantia/workflows/agent_workflow.py

@dataclass
class AgentToolCallInput:
    messages: list[dict]
    tools: list[dict]
    org_id: str
    conversation_id: str | None
    max_iterations: int = 10

@dataclass  
class AgentToolCallOutput:
    response: str
    tool_calls_made: list[dict]
    conversation_id: str

@workflow.defn
class AgentToolCallWorkflow:
    @workflow.run
    async def run(self, input: AgentToolCallInput) -> AgentToolCallOutput:
        messages = input.messages
        iterations = 0
        tool_calls_log = []
        
        while iterations < input.max_iterations:
            # Call LLM
            llm_result = await workflow.execute_activity(
                call_llm_activity,
                args=[messages, input.tools],
                start_to_close_timeout=timedelta(seconds=30),
            )
            
            if not llm_result.tool_calls:
                # Final text response
                break
            
            # Execute each tool call
            for tc in llm_result.tool_calls:
                tool_result = await workflow.execute_activity(
                    execute_tool_activity,
                    args=[tc.name, tc.arguments, input.org_id],
                    start_to_close_timeout=timedelta(seconds=30),
                )
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": tool_result})
                tool_calls_log.append({"name": tc.name, "args": tc.arguments, "result": tool_result})
            
            iterations += 1
        
        # Persist conversation
        await workflow.execute_activity(
            persist_conversation_activity,
            args=[input.conversation_id, input.org_id, messages],
            start_to_close_timeout=timedelta(seconds=10),
        )
        
        return AgentToolCallOutput(
            response=llm_result.content,
            tool_calls_made=tool_calls_log,
            conversation_id=input.conversation_id,
        )
```

### Step 2: Delete unsafe activities (day 1)
- Remove `generate_code`, `execute_in_sandbox` from activities.py
- Remove `review_for_hallucinations` (replaced by output_validator in P0.7)
- Keep `compile_results` if it does useful post-processing; otherwise remove

### Step 3: Implement new activities (day 2)

```python
@activity.defn
async def call_llm_activity(messages: list[dict], tools: list[dict]) -> LLMResponse:
    provider = get_provider(settings.default_provider)
    return await provider.completion(messages=messages, tools=tools)

@activity.defn
async def execute_tool_activity(tool_name: str, tool_args: dict, org_id: str) -> str:
    result = await execute_tool(tool_name, tool_args, org_id)
    if isinstance(result, ToolError):
        return json.dumps({"error": result.message, "type": result.error_type})
    return json.dumps(result.data)

@activity.defn
async def persist_conversation_activity(conv_id: str, org_id: str, messages: list[dict]):
    async with get_db_session() as db:
        # Save messages to conversation in DB
        ...
```

### Step 4: Fix chat.py (day 3)

```python
@router.post("/")
async def chat(request: ChatRequest, org_context = Depends(get_org_context), db = Depends(get_db)):
    org_id = org_context.org_id
    
    try:
        client = await get_temporal_client()
        handle = await client.start_workflow(
            AgentToolCallWorkflow.run,
            AgentToolCallInput(
                messages=[{"role": "user", "content": request.message}],
                tools=get_tool_schemas(),
                org_id=org_id,
                conversation_id=request.conversation_id,
            ),
            id=f"chat-{uuid4()}",
            task_queue="agent-queue",
        )
        # TIMEOUT: 30 seconds max wait
        result = await asyncio.wait_for(handle.result(), timeout=30.0)
        return ChatResponse(message=result.response, conversation_id=result.conversation_id)
        
    except (asyncio.TimeoutError,):
        # Workflow is still running — tell user to wait
        return ChatResponse(message="Processing is taking longer than expected. Check back shortly.", ...)
        
    except (RPCError, ServiceError) as e:
        # Temporal is actually unavailable — fall back to direct mode
        logger.warning(f"Temporal unavailable, using direct mode: {e}")
        response = await agent.chat(request.message, org_id=org_id, db=db)
        return ChatResponse(message=response, ...)
    
    # All other exceptions propagate as 500 — do NOT catch and hide
```

### Step 5: Register workflow + tests (day 4-5)
- Update `worker.py` to register `AgentToolCallWorkflow` + new activities
- Write integration test: send chat message → workflow executes → tool called → response returned
- Write test: Temporal down → falls back to direct mode
- Write test: workflow timeout → user gets informative message
- Verify no subprocess references remain: `grep -r "subprocess\|create_subprocess" backend/src/`

---

## Expected Behavior

| Scenario | Before | After |
|----------|--------|-------|
| Chat with Temporal up | Workflow generates Python, runs subprocess | Workflow calls tools via registered handlers |
| Chat with Temporal down | Silent fallback, hides all errors | Falls back to direct mode with logged warning |
| Workflow takes > 30s | HTTP request hangs indefinitely | Returns "processing taking longer" after 30s |
| DB connection error during tool | Caught by `except Exception`, hidden | Propagates as 500 with proper error response |
| Temporal path conversation | Not persisted (different code path) | Persisted same as direct mode |

---

## Acceptance Criteria

- [ ] `grep -r "subprocess\|create_subprocess_exec\|python.*-c" backend/src/` returns zero results
- [ ] `AgentRunWorkflow` is deleted; `AgentToolCallWorkflow` is registered
- [ ] `generate_code` and `execute_in_sandbox` activities are deleted
- [ ] Workflow uses only registered tool handlers from `TOOL_HANDLERS` dict
- [ ] `await handle.result()` has 30-second timeout
- [ ] Only `RPCError`/`ServiceError` triggers direct-mode fallback
- [ ] Other exceptions propagate as HTTP 500 (not hidden)
- [ ] `org_id` is passed into workflow and used for tool execution
- [ ] Conversation history persisted in Temporal path (same DB records as direct path)
- [ ] Integration test passes: chat → tool execution → response via Temporal
- [ ] Direct-mode fallback test passes: Temporal connection refused → direct mode works
- [ ] Existing backend tests pass

---

## Risks

- **Activity serialization:** Temporal activities must use serializable inputs/outputs. `LLMResponse` and tool results must be JSON-serializable (no raw Python objects).
- **Workflow determinism:** Temporal workflows must be deterministic. LLM calls must happen inside activities (not workflow code directly).
- **Migration:** If any running workflows exist from the old `AgentRunWorkflow`, they'll fail after deploy. Since this is pre-production, acceptable — but document the breaking change.
- **Conversation persistence timing:** If workflow fails mid-execution, partially-executed tool calls should still be persisted for debugging.
