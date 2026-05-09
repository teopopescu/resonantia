"""Tests for the multi-agent orchestrator and specialist subagents.

These exercise the routing logic, tool-scoping, and structured-message
contracts without hitting the LLM. The OpenAI client is replaced with
an ``AsyncMock`` whose ``chat.completions.create`` returns canned
responses shaped like the real SDK.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from resonantia.services.multi_agent import (
    SPECIALISTS,
    TaskAssignment,
    TaskResult,
)
from resonantia.services.multi_agent import critic as critic_module
from resonantia.services.multi_agent import orchestrator
from resonantia.services.multi_agent import subagents as subagents_module
from resonantia.services.multi_agent.messages import OrchestrationPlan


def _fake_completion(content: str, *, with_tool_calls: list[dict] | None = None):
    """Build an object shaped like an OpenAI ChatCompletion response."""
    if with_tool_calls:
        message = SimpleNamespace(
            content=content,
            tool_calls=[
                SimpleNamespace(
                    id=tc["id"],
                    function=SimpleNamespace(
                        name=tc["name"],
                        arguments=json.dumps(tc.get("arguments", {})),
                    ),
                )
                for tc in with_tool_calls
            ],
        )
        finish = "tool_calls"
    else:
        message = SimpleNamespace(content=content, tool_calls=None)
        finish = "stop"
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message, finish_reason=finish)],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=20),
    )


def _mock_client(*responses):
    """Create an AsyncOpenAI-like mock that returns ``responses`` in order."""
    client = MagicMock()
    client.chat.completions.create = AsyncMock(side_effect=list(responses))
    return client


# ---------------------------------------------------------------------------
# Specialist registry
# ---------------------------------------------------------------------------

def test_specialist_registry_covers_documented_agents():
    """The 6 specialists named in subagents-acp-plan.md must be present.

    `experiment_design` from the doc is intentionally subsumed into the
    other specialists for Phase 1 and is not expected here.
    """
    expected = {
        "plate_designer",
        "data_analyst",
        "eln_scribe",
        "protocol_agent",
        "sample_agent",
        "general",
    }
    assert set(SPECIALISTS.keys()) == expected


def test_specialist_tool_categories_are_disjoint():
    """No two specialists should claim the same primary category.

    `general` legitimately overlaps (empty tuple = all tools), so it's
    excluded from the disjointness check.
    """
    seen: set[str] = set()
    for name, cfg in SPECIALISTS.items():
        if name == "general":
            continue
        for cat in cfg.tool_categories:
            assert cat not in seen, f"{name} reuses category {cat}"
            seen.add(cat)


# ---------------------------------------------------------------------------
# run_specialist
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_specialist_returns_completed_when_llm_answers_directly():
    task = TaskAssignment(
        task_id="t1",
        assigned_agent="sample_agent",
        objective="Look up the lot of anti-GFP",
    )
    client = _mock_client(_fake_completion("Lot AB123, expires 2026-12-01."))

    with patch.object(subagents_module, "_scoped_tools", new=AsyncMock(return_value=[])):
        with patch.object(
            subagents_module, "get_settings",
            return_value=SimpleNamespace(openai_api_key="x", llm_model="gpt-4o"),
        ):
            result = await subagents_module.run_specialist(
                task, org_id="org_test", client=client
            )

    assert result.status == "completed"
    assert "Lot AB123" in result.output
    assert result.assigned_agent == "sample_agent"
    assert result.task_id == "t1"


@pytest.mark.asyncio
async def test_run_specialist_executes_tools_then_returns_answer():
    task = TaskAssignment(
        task_id="t2",
        assigned_agent="data_analyst",
        objective="Fit dose-response for staurosporine",
    )
    # Round 1: LLM asks for a tool. Round 2: LLM produces final text.
    client = _mock_client(
        _fake_completion(
            "calling tool",
            with_tool_calls=[
                {"id": "call_1", "name": "fit_dose_response",
                 "arguments": {"concentrations": [], "responses": []}}
            ],
        ),
        _fake_completion("IC50 = 12 nM, Z' = 0.78"),
    )

    with patch.object(subagents_module, "_scoped_tools", new=AsyncMock(return_value=[])):
        with patch.object(
            subagents_module, "execute_tool",
            new=AsyncMock(return_value='{"ic50": 12, "z_prime": 0.78}'),
        ):
            with patch.object(
                subagents_module, "get_settings",
                return_value=SimpleNamespace(openai_api_key="x", llm_model="gpt-4o"),
            ):
                result = await subagents_module.run_specialist(
                    task, org_id="org_test", client=client
                )

    assert result.status == "completed"
    assert "IC50" in result.output
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0]["name"] == "fit_dose_response"


# ---------------------------------------------------------------------------
# Orchestrator decomposition
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_decompose_drops_unknown_specialists():
    raw = json.dumps(
        {
            "rationale": "split into two",
            "assignments": [
                {"task_id": "a1", "assigned_agent": "sample_agent",
                 "objective": "lookup", "inputs": {}, "constraints": []},
                {"task_id": "a2", "assigned_agent": "ghost_agent",
                 "objective": "irrelevant", "inputs": {}, "constraints": []},
            ],
            "can_run_parallel": True,
        }
    )
    client = _mock_client(_fake_completion(raw))
    with patch.object(
        orchestrator, "get_settings",
        return_value=SimpleNamespace(openai_api_key="x", llm_model="gpt-4o"),
    ):
        plan = await orchestrator._decompose("anything", client)
    assert len(plan.assignments) == 1
    assert plan.assignments[0].assigned_agent == "sample_agent"
    assert plan.can_run_parallel is True


@pytest.mark.asyncio
async def test_decompose_handles_invalid_json():
    client = _mock_client(_fake_completion("not json at all"))
    with patch.object(
        orchestrator, "get_settings",
        return_value=SimpleNamespace(openai_api_key="x", llm_model="gpt-4o"),
    ):
        plan = await orchestrator._decompose("hi", client)
    assert plan.assignments == []
    assert "invalid_decomposition" in plan.rationale


@pytest.mark.asyncio
async def test_decompose_empty_assignments_means_direct_reply():
    raw = json.dumps({"rationale": "small talk", "assignments": []})
    client = _mock_client(_fake_completion(raw))
    with patch.object(
        orchestrator, "get_settings",
        return_value=SimpleNamespace(openai_api_key="x", llm_model="gpt-4o"),
    ):
        plan = await orchestrator._decompose("hello", client)
    assert plan.assignments == []


# ---------------------------------------------------------------------------
# Critic
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_critic_passes_when_llm_returns_pass():
    result = TaskResult(
        task_id="t1", assigned_agent="data_analyst",
        status="completed", output="IC50 = 12 nM, Z' = 0.78",
    )
    client = _mock_client(
        _fake_completion(json.dumps({"decision": "pass", "reason": "QC reported"}))
    )
    with patch.object(
        critic_module, "get_settings",
        return_value=SimpleNamespace(openai_api_key="x", llm_model="gpt-4o"),
    ):
        verdict = await critic_module.review("fit the curve", result, client=client)
    assert verdict.decision == "pass"
    assert verdict.task_id == "t1"


@pytest.mark.asyncio
async def test_critic_degrades_to_soft_warn_on_unparseable_output():
    result = TaskResult(
        task_id="t1", assigned_agent="data_analyst",
        status="completed", output="…",
    )
    client = _mock_client(_fake_completion("not json"))
    with patch.object(
        critic_module, "get_settings",
        return_value=SimpleNamespace(openai_api_key="x", llm_model="gpt-4o"),
    ):
        verdict = await critic_module.review("anything", result, client=client)
    assert verdict.decision == "soft_warn"


@pytest.mark.asyncio
async def test_critic_degrades_when_no_api_key():
    result = TaskResult(
        task_id="t1", assigned_agent="data_analyst",
        status="completed", output="…",
    )
    with patch.object(
        critic_module, "get_settings",
        return_value=SimpleNamespace(openai_api_key="", llm_model="gpt-4o"),
    ):
        verdict = await critic_module.review("anything", result)
    assert verdict.decision == "soft_warn"
    assert "no_api_key" in verdict.reason


@pytest.mark.asyncio
async def test_critic_fails_closed_for_high_stakes_tool():
    """When the specialist used fit_dose_response and the critic is
    unavailable, the verdict is REJECT, not soft_warn."""
    result = TaskResult(
        task_id="t-hs",
        assigned_agent="data_analyst",
        status="completed",
        output="IC50 = 12 nM",
        tool_calls=[{"id": "1", "name": "fit_dose_response", "input": {}}],
    )
    with patch.object(
        critic_module, "get_settings",
        return_value=SimpleNamespace(openai_api_key="", llm_model="gpt-4o"),
    ):
        verdict = await critic_module.review("fit", result)
    assert verdict.decision == "reject"


@pytest.mark.asyncio
async def test_critic_soft_warns_for_low_stakes_tool():
    """When no high-stakes tool is involved and the critic is
    unavailable, degrade to soft_warn (don't block lookups)."""
    result = TaskResult(
        task_id="t-ls",
        assigned_agent="sample_agent",
        status="completed",
        output="Lot AB123",
        tool_calls=[{"id": "1", "name": "lookup_sample", "input": {}}],
    )
    with patch.object(
        critic_module, "get_settings",
        return_value=SimpleNamespace(openai_api_key="", llm_model="gpt-4o"),
    ):
        verdict = await critic_module.review("look up", result)
    assert verdict.decision == "soft_warn"


# ---------------------------------------------------------------------------
# Synthesizer
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_synthesize_returns_specialist_output_only_with_explicit_pass():
    """One specialist + explicit critic pass = verbatim output. An
    empty verdict list does NOT take the short-circuit, even with one
    specialist — the critic was skipped, not satisfied."""
    results = [
        TaskResult(task_id="t1", assigned_agent="sample_agent",
                   status="completed", output="Lot AB123")
    ]
    pass_verdict = critic_module.CriticVerdict(
        task_id="t1", decision="pass", reason=""
    )
    client = _mock_client()
    out = await orchestrator._synthesize_answer(
        "look up", results, [pass_verdict], client
    )
    assert out == "Lot AB123"


@pytest.mark.asyncio
async def test_synthesize_does_not_short_circuit_without_verdict():
    """Empty verdict list must not be treated as a critic pass."""
    results = [
        TaskResult(task_id="t1", assigned_agent="sample_agent",
                   status="completed", output="Lot AB123")
    ]
    client = _mock_client()
    out = await orchestrator._synthesize_answer("look up", results, [], client)
    # falls into the per-section render; no short-circuit
    assert "sample_agent" in out


@pytest.mark.asyncio
async def test_synthesize_combines_multiple_specialists_with_warnings():
    results = [
        TaskResult(task_id="t1", assigned_agent="data_analyst",
                   status="completed", output="IC50 = 12"),
        TaskResult(task_id="t2", assigned_agent="eln_scribe",
                   status="completed", output="Drafted entry."),
    ]
    verdicts = [
        critic_module.CriticVerdict(task_id="t1", decision="soft_warn",
                                    reason="Z' missing"),
        critic_module.CriticVerdict(task_id="t2", decision="pass", reason=""),
    ]
    client = _mock_client()
    out = await orchestrator._synthesize_answer(
        "analyse and write up", results, verdicts, client
    )
    assert "data_analyst" in out
    assert "eln_scribe" in out
    assert "[critic note]" in out
    assert "Z' missing" in out


# ---------------------------------------------------------------------------
# Sequential dependency threading
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_assignments_threads_upstream_into_sequential_inputs():
    """When ``can_run_parallel`` is false, downstream assignments must
    receive earlier results in their ``inputs.upstream`` field."""
    plan = OrchestrationPlan(
        rationale="design then write up",
        can_run_parallel=False,
        assignments=[
            TaskAssignment(
                task_id="a1", assigned_agent="plate_designer",
                objective="design a 96-well dose-response",
            ),
            TaskAssignment(
                task_id="a2", assigned_agent="eln_scribe",
                objective="draft an ELN entry",
            ),
        ],
    )

    captured: list[TaskAssignment] = []

    async def fake_run(assignment, org_id, *, client=None):
        captured.append(assignment)
        return TaskResult(
            task_id=assignment.task_id,
            assigned_agent=assignment.assigned_agent,
            status="completed",
            output=f"output for {assignment.task_id}",
        )

    with patch.object(orchestrator, "run_specialist", new=fake_run):
        await orchestrator._execute_assignments(plan, "org_test", client=_mock_client())

    assert len(captured) == 2
    # First assignment runs without upstream context.
    assert "upstream" not in captured[0].inputs
    # Second assignment receives the first specialist's output.
    upstream = captured[1].inputs.get("upstream")
    assert upstream is not None and len(upstream) == 1
    assert upstream[0]["task_id"] == "a1"
    assert "output for a1" in upstream[0]["output"]


@pytest.mark.asyncio
async def test_execute_assignments_runs_in_parallel_when_safe():
    plan = OrchestrationPlan(
        rationale="independent lookups",
        can_run_parallel=True,
        assignments=[
            TaskAssignment(task_id="a1", assigned_agent="sample_agent", objective="x"),
            TaskAssignment(task_id="a2", assigned_agent="sample_agent", objective="y"),
        ],
    )

    captured: list[TaskAssignment] = []

    async def fake_run(assignment, org_id, *, client=None):
        captured.append(assignment)
        return TaskResult(
            task_id=assignment.task_id,
            assigned_agent=assignment.assigned_agent,
            status="completed",
            output="ok",
        )

    with patch.object(orchestrator, "run_specialist", new=fake_run):
        await orchestrator._execute_assignments(plan, "org_test", client=_mock_client())

    # Neither assignment should have been mutated with upstream context.
    for a in captured:
        assert "upstream" not in a.inputs
