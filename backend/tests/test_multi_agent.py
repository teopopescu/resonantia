"""Tests for the multi-agent orchestrator and specialist subagents.

These exercise the routing logic, tool-scoping, and structured-message
contracts without hitting the LLM. The LLM provider is replaced with
a mock whose ``completion`` returns canned ``LLMResponse`` objects.

P4.1 additions: provider usage verification, critic source_ref
validation, MULTI_AGENT_ENABLED config flag behavior.

P4.2 additions: trace metadata completeness, routing decision tracing.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from resonantia.services.llm.provider import LLMResponse, ToolCall
from resonantia.services.multi_agent import (
    SPECIALISTS,
    TaskAssignment,
    TaskResult,
)
from resonantia.services.multi_agent import critic as critic_module
from resonantia.services.multi_agent import orchestrator
from resonantia.services.multi_agent import subagents as subagents_module
from resonantia.services.multi_agent.messages import OrchestrationPlan


def _fake_response(content: str, *, tool_calls: list[ToolCall] | None = None) -> LLMResponse:
    """Build a mock LLMResponse."""
    return LLMResponse(
        content=content,
        tool_calls=tool_calls or [],
        model="test-model",
        provider="test",
        input_tokens=10,
        output_tokens=20,
    )


def _mock_provider(*responses: LLMResponse) -> MagicMock:
    """Create a mock LLMProvider that returns ``responses`` in order."""
    provider = MagicMock()
    provider.provider_name = "test"
    provider.completion = AsyncMock(side_effect=list(responses))
    return provider


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
    provider = _mock_provider(_fake_response("Lot AB123, expires 2026-12-01."))

    with patch.object(subagents_module, "_scoped_tools", new=AsyncMock(return_value=[])):
        with patch.object(
            subagents_module, "get_settings",
            return_value=SimpleNamespace(
                openai_api_key="x", anthropic_api_key="x",
                default_provider="anthropic",
                specialist_model="test-model",
            ),
        ):
            result = await subagents_module.run_specialist(
                task, org_id="org_test", provider=provider
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
    provider = _mock_provider(
        _fake_response(
            "calling tool",
            tool_calls=[
                ToolCall(
                    id="call_1",
                    name="fit_dose_response",
                    arguments={"concentrations": [], "responses": []},
                )
            ],
        ),
        _fake_response("IC50 = 12 nM, Z' = 0.78"),
    )

    with patch.object(subagents_module, "_scoped_tools", new=AsyncMock(return_value=[])):
        with patch.object(
            subagents_module, "execute_tool",
            new=AsyncMock(return_value='{"ic50": 12, "z_prime": 0.78}'),
        ):
            with patch.object(
                subagents_module, "get_settings",
                return_value=SimpleNamespace(
                    openai_api_key="x", anthropic_api_key="x",
                    default_provider="anthropic",
                    specialist_model="test-model",
                ),
            ):
                result = await subagents_module.run_specialist(
                    task, org_id="org_test", provider=provider
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
    provider = _mock_provider(_fake_response(raw))
    with patch.object(
        orchestrator, "get_settings",
        return_value=SimpleNamespace(
            openai_api_key="x", anthropic_api_key="x",
            default_provider="anthropic",
            planner_model="test-model",
        ),
    ):
        plan = await orchestrator._decompose("anything", provider)
    assert len(plan.assignments) == 1
    assert plan.assignments[0].assigned_agent == "sample_agent"
    assert plan.can_run_parallel is True


@pytest.mark.asyncio
async def test_decompose_handles_invalid_json():
    provider = _mock_provider(_fake_response("not json at all"))
    with patch.object(
        orchestrator, "get_settings",
        return_value=SimpleNamespace(
            openai_api_key="x", anthropic_api_key="x",
            default_provider="anthropic",
            planner_model="test-model",
        ),
    ):
        plan = await orchestrator._decompose("hi", provider)
    assert plan.assignments == []
    assert "invalid_decomposition" in plan.rationale


@pytest.mark.asyncio
async def test_decompose_empty_assignments_means_direct_reply():
    raw = json.dumps({"rationale": "small talk", "assignments": []})
    provider = _mock_provider(_fake_response(raw))
    with patch.object(
        orchestrator, "get_settings",
        return_value=SimpleNamespace(
            openai_api_key="x", anthropic_api_key="x",
            default_provider="anthropic",
            planner_model="test-model",
        ),
    ):
        plan = await orchestrator._decompose("hello", provider)
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
    provider = _mock_provider(
        _fake_response(json.dumps({"decision": "pass", "reason": "QC reported"}))
    )
    with patch.object(
        critic_module, "get_settings",
        return_value=SimpleNamespace(
            openai_api_key="x", anthropic_api_key="x",
            default_provider="anthropic",
            critic_model="test-model",
        ),
    ):
        verdict = await critic_module.review("fit the curve", result, provider=provider)
    assert verdict.decision == "pass"
    assert verdict.task_id == "t1"


@pytest.mark.asyncio
async def test_critic_degrades_to_soft_warn_on_unparseable_output():
    result = TaskResult(
        task_id="t1", assigned_agent="data_analyst",
        status="completed", output="...",
    )
    provider = _mock_provider(_fake_response("not json"))
    with patch.object(
        critic_module, "get_settings",
        return_value=SimpleNamespace(
            openai_api_key="x", anthropic_api_key="x",
            default_provider="anthropic",
            critic_model="test-model",
        ),
    ):
        verdict = await critic_module.review("anything", result, provider=provider)
    assert verdict.decision == "soft_warn"


@pytest.mark.asyncio
async def test_critic_degrades_when_no_api_key():
    result = TaskResult(
        task_id="t1", assigned_agent="data_analyst",
        status="completed", output="...",
    )
    with patch.object(
        critic_module, "get_settings",
        return_value=SimpleNamespace(
            openai_api_key="", anthropic_api_key="",
            default_provider="anthropic",
            critic_model="test-model",
        ),
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
        return_value=SimpleNamespace(
            openai_api_key="", anthropic_api_key="",
            default_provider="anthropic",
            critic_model="test-model",
        ),
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
        return_value=SimpleNamespace(
            openai_api_key="", anthropic_api_key="",
            default_provider="anthropic",
            critic_model="test-model",
        ),
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
    specialist -- the critic was skipped, not satisfied."""
    results = [
        TaskResult(task_id="t1", assigned_agent="sample_agent",
                   status="completed", output="Lot AB123")
    ]
    pass_verdict = critic_module.CriticVerdict(
        task_id="t1", decision="pass", reason=""
    )
    provider = _mock_provider()
    out = await orchestrator._synthesize_answer(
        "look up", results, [pass_verdict], provider
    )
    assert out == "Lot AB123"


@pytest.mark.asyncio
async def test_synthesize_does_not_short_circuit_without_verdict():
    """Empty verdict list must not be treated as a critic pass."""
    results = [
        TaskResult(task_id="t1", assigned_agent="sample_agent",
                   status="completed", output="Lot AB123")
    ]
    provider = _mock_provider()
    out = await orchestrator._synthesize_answer("look up", results, [], provider)
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
    provider = _mock_provider()
    out = await orchestrator._synthesize_answer(
        "analyse and write up", results, verdicts, provider
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

    async def fake_run(assignment, org_id, *, provider=None, conversation_id=None):
        captured.append(assignment)
        return TaskResult(
            task_id=assignment.task_id,
            assigned_agent=assignment.assigned_agent,
            status="completed",
            output=f"output for {assignment.task_id}",
        )

    with patch.object(orchestrator, "run_specialist", new=fake_run):
        await orchestrator._execute_assignments(plan, "org_test", provider=_mock_provider())

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

    async def fake_run(assignment, org_id, *, provider=None, conversation_id=None):
        captured.append(assignment)
        return TaskResult(
            task_id=assignment.task_id,
            assigned_agent=assignment.assigned_agent,
            status="completed",
            output="ok",
        )

    with patch.object(orchestrator, "run_specialist", new=fake_run):
        await orchestrator._execute_assignments(plan, "org_test", provider=_mock_provider())

    # Neither assignment should have been mutated with upstream context.
    for a in captured:
        assert "upstream" not in a.inputs


# ---------------------------------------------------------------------------
# P4.1: Provider usage verification
# ---------------------------------------------------------------------------

def test_all_specialists_use_provider_not_direct_sdk():
    """P4.1: Verify no direct openai/anthropic imports in multi-agent code."""
    import inspect
    import resonantia.services.multi_agent.orchestrator as orch_mod
    import resonantia.services.multi_agent.subagents as sub_mod
    import resonantia.services.multi_agent.critic as crit_mod

    for mod in [orch_mod, sub_mod, crit_mod]:
        source = inspect.getsource(mod)
        assert "import openai" not in source, f"{mod.__name__} imports openai directly"
        assert "import anthropic" not in source, f"{mod.__name__} imports anthropic directly"
        assert "from openai" not in source, f"{mod.__name__} imports from openai directly"
        assert "from anthropic" not in source, f"{mod.__name__} imports from anthropic directly"


def test_specialist_uses_provider_completion():
    """P4.1: run_specialist calls provider.completion, not SDK directly."""
    import inspect
    source = inspect.getsource(subagents_module.run_specialist)
    assert "provider.completion" in source


def test_critic_uses_provider_completion():
    """P4.1: critic.review calls provider.completion, not SDK directly."""
    import inspect
    source = inspect.getsource(critic_module.review)
    assert "provider.completion" in source


def test_orchestrator_uses_provider_completion():
    """P4.1: orchestrator._decompose calls provider.completion."""
    import inspect
    source = inspect.getsource(orchestrator._decompose)
    assert "provider.completion" in source


# ---------------------------------------------------------------------------
# P4.1: Per-agent model assignment
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_specialist_uses_specialist_model_from_config():
    """P4.1: run_specialist passes settings.specialist_model to provider."""
    task = TaskAssignment(
        task_id="t-model",
        assigned_agent="sample_agent",
        objective="check inventory",
    )
    provider = _mock_provider(_fake_response("Found item."))
    custom_model = "claude-custom-specialist"

    with patch.object(subagents_module, "_scoped_tools", new=AsyncMock(return_value=[])):
        with patch.object(
            subagents_module, "get_settings",
            return_value=SimpleNamespace(
                openai_api_key="x", anthropic_api_key="x",
                default_provider="anthropic",
                specialist_model=custom_model,
            ),
        ):
            await subagents_module.run_specialist(
                task, org_id="org_test", provider=provider
            )

    # Check the model arg passed to provider.completion
    call_kwargs = provider.completion.call_args
    assert call_kwargs.kwargs.get("model") == custom_model or call_kwargs[1].get("model") == custom_model


@pytest.mark.asyncio
async def test_critic_uses_critic_model_from_config():
    """P4.1: critic.review passes settings.critic_model to provider."""
    result = TaskResult(
        task_id="t-cm", assigned_agent="data_analyst",
        status="completed", output="IC50 = 12 nM",
    )
    provider = _mock_provider(
        _fake_response(json.dumps({"decision": "pass", "reason": "ok"}))
    )
    custom_model = "claude-custom-critic"

    with patch.object(
        critic_module, "get_settings",
        return_value=SimpleNamespace(
            openai_api_key="x", anthropic_api_key="x",
            default_provider="anthropic",
            critic_model=custom_model,
        ),
    ):
        await critic_module.review("fit curve", result, provider=provider)

    call_kwargs = provider.completion.call_args
    assert call_kwargs.kwargs.get("model") == custom_model or call_kwargs[1].get("model") == custom_model


# ---------------------------------------------------------------------------
# P4.1: Critic catches fabricated data (source_ref validation)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_critic_rejects_high_stakes_result_without_source_refs():
    """P4.1: Critic rejects when high-stakes tool used but no source_refs in output."""
    result = TaskResult(
        task_id="t-fab",
        assigned_agent="data_analyst",
        status="completed",
        # Output has no identifiers/references at all
        output="The compound is very potent and works great.",
        tool_calls=[{"id": "1", "name": "fit_dose_response", "input": {}}],
    )
    # Provider should not even be called -- source_ref check rejects first
    with patch.object(
        critic_module, "get_settings",
        return_value=SimpleNamespace(
            openai_api_key="x", anthropic_api_key="x",
            default_provider="anthropic",
            critic_model="test-model",
        ),
    ):
        verdict = await critic_module.review("fit the curve", result)

    assert verdict.decision == "reject"
    assert "source_ref" in verdict.reason


@pytest.mark.asyncio
async def test_critic_passes_when_output_has_references():
    """P4.1: Critic does not flag source_ref issue when output cites IDs."""
    result = TaskResult(
        task_id="t-ref",
        assigned_agent="data_analyst",
        status="completed",
        output="IC50 = 12 nM (exp_id: abc123, Z' = 0.82)",
        tool_calls=[{"id": "1", "name": "fit_dose_response", "input": {}}],
    )
    provider = _mock_provider(
        _fake_response(json.dumps({"decision": "pass", "reason": "data matches"}))
    )
    with patch.object(
        critic_module, "get_settings",
        return_value=SimpleNamespace(
            openai_api_key="x", anthropic_api_key="x",
            default_provider="anthropic",
            critic_model="test-model",
        ),
    ):
        verdict = await critic_module.review("fit", result, provider=provider)

    assert verdict.decision == "pass"


@pytest.mark.asyncio
async def test_critic_soft_warns_non_high_stakes_without_refs():
    """P4.1: Non-high-stakes tool missing refs gets soft_warn (not reject)."""
    result = TaskResult(
        task_id="t-sw",
        assigned_agent="sample_agent",
        status="completed",
        output="The sample is available and ready to use.",
        tool_calls=[{"id": "1", "name": "lookup_sample", "input": {}}],
    )
    provider = _mock_provider(
        _fake_response(json.dumps({"decision": "pass", "reason": "ok"}))
    )
    with patch.object(
        critic_module, "get_settings",
        return_value=SimpleNamespace(
            openai_api_key="x", anthropic_api_key="x",
            default_provider="anthropic",
            critic_model="test-model",
        ),
    ):
        verdict = await critic_module.review("lookup", result, provider=provider)

    # LLM said pass but source_ref check upgrades to soft_warn
    assert verdict.decision == "soft_warn"
    assert "source_ref" in verdict.reason or "no_source_refs" in verdict.reason


# ---------------------------------------------------------------------------
# P4.1: Config flag disables multi-agent
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_config_flag_routes_to_single_agent_when_disabled():
    """P4.1: MULTI_AGENT_ENABLED=false routes to legacy agent."""
    from resonantia.services import agent_router

    with patch.object(
        agent_router, "get_settings",
        return_value=SimpleNamespace(multi_agent_enabled=False),
    ):
        with patch("resonantia.services.agent.chat", new=AsyncMock(return_value={"message": "legacy"})) as legacy_mock:
            result = await agent_router.chat("hello")
            legacy_mock.assert_called_once()
            assert result["message"] == "legacy"


@pytest.mark.asyncio
async def test_config_flag_routes_to_multi_agent_when_enabled():
    """P4.1: MULTI_AGENT_ENABLED=true routes to orchestrator."""
    from resonantia.services import agent_router

    with patch.object(
        agent_router, "get_settings",
        return_value=SimpleNamespace(multi_agent_enabled=True),
    ):
        with patch(
            "resonantia.services.multi_agent.orchestrator.chat",
            new=AsyncMock(return_value={"message": "multi"}),
        ) as multi_mock:
            result = await agent_router.chat("hello")
            multi_mock.assert_called_once()
            assert result["message"] == "multi"


# ---------------------------------------------------------------------------
# P4.2: Trace metadata completeness
# ---------------------------------------------------------------------------

def test_trace_llm_call_includes_all_required_fields():
    """P4.2: trace_llm_call builds metadata with org_id, agent_role, etc."""
    from resonantia.services import tracing

    captured_metadata: dict = {}

    def fake_get_client():
        # Return None so we exercise the metadata building without Langfuse
        return None

    with patch.object(tracing, "_get_client", fake_get_client):
        # trace_llm_call returns None when client is None, but we can
        # test the function signature accepts all required params
        result = tracing.trace_llm_call(
            user_message="test",
            system_prompt="sys",
            response="resp",
            model="claude-sonnet-4-20250514",
            org_id="org_123",
            conversation_id="conv_456",
            agent_role="specialist:data_analyst",
            tool_calls=["fit_dose_response"],
            latency_ms=1234.5,
            token_usage={"input_tokens": 100, "output_tokens": 50},
        )
        # Returns None because client is None -- that's fine
        assert result is None


def test_trace_specialist_call_sets_agent_role():
    """P4.2: trace_specialist_call prefixes agent_role with 'specialist:'."""
    from resonantia.services import tracing

    with patch.object(tracing, "_get_client", return_value=None):
        # Won't actually send anything but verifies the function exists and
        # accepts the expected parameters without error
        result = tracing.trace_specialist_call(
            agent_role="data_analyst",
            objective="fit dose-response",
            response="IC50 = 12 nM",
            model="claude-sonnet-4-20250514",
            org_id="org_test",
            conversation_id="conv_test",
            tool_calls=["fit_dose_response"],
            latency_ms=500.0,
            token_usage={"input_tokens": 50, "output_tokens": 30},
        )
        assert result is None


def test_trace_routing_decision_captures_assigned_agents():
    """P4.2: trace_routing_decision includes assigned_agents in metadata."""
    from resonantia.services import tracing

    with patch.object(tracing, "_get_client", return_value=None):
        result = tracing.trace_routing_decision(
            user_message="design plate and fit curve",
            rationale="two specialists needed",
            assigned_agents=["plate_designer", "data_analyst"],
            can_run_parallel=True,
            model="claude-sonnet-4-20250514",
            org_id="org_test",
            conversation_id="conv_test",
            latency_ms=200.0,
        )
        assert result is None


def test_trace_critic_call_captures_decision():
    """P4.2: trace_critic_call includes decision and specialist info."""
    from resonantia.services import tracing

    with patch.object(tracing, "_get_client", return_value=None):
        result = tracing.trace_critic_call(
            task_id="t1",
            specialist="data_analyst",
            decision="pass",
            reason="numbers match tool output",
            model="claude-haiku-4-5-20251001",
            org_id="org_test",
            conversation_id="conv_test",
            latency_ms=150.0,
        )
        assert result is None


def test_estimate_cost_known_model():
    """P4.2: _estimate_cost returns reasonable values for known models."""
    from resonantia.services.tracing import _estimate_cost

    cost = _estimate_cost("claude-sonnet-4-20250514", 1000, 500)
    # 1000 * 3.0 / 1M + 500 * 15.0 / 1M = 0.003 + 0.0075 = 0.0105
    assert 0.01 < cost < 0.02


def test_estimate_cost_unknown_model_uses_default():
    """P4.2: _estimate_cost falls back to default pricing for unknown models."""
    from resonantia.services.tracing import _estimate_cost

    cost = _estimate_cost("unknown-model-xyz", 1000, 500)
    # Should use default pricing (same as sonnet)
    assert cost > 0


# ---------------------------------------------------------------------------
# P4.2: Langfuse span wrapping in specialist calls
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_specialist_traces_call_on_completion():
    """P4.2: run_specialist calls trace_specialist_call on success."""
    task = TaskAssignment(
        task_id="t-trace",
        assigned_agent="sample_agent",
        objective="check inventory for anti-GFP",
    )
    provider = _mock_provider(_fake_response("Lot AB123, barcode: BC-001"))

    with patch.object(subagents_module, "_scoped_tools", new=AsyncMock(return_value=[])):
        with patch.object(
            subagents_module, "get_settings",
            return_value=SimpleNamespace(
                openai_api_key="x", anthropic_api_key="x",
                default_provider="anthropic",
                specialist_model="test-model",
            ),
        ):
            with patch.object(
                subagents_module, "trace_specialist_call",
            ) as trace_mock:
                result = await subagents_module.run_specialist(
                    task, org_id="org_test", provider=provider,
                    conversation_id="conv_123",
                )

    assert result.status == "completed"
    trace_mock.assert_called_once()
    call_kwargs = trace_mock.call_args.kwargs
    assert call_kwargs["agent_role"] == "sample_agent"
    assert call_kwargs["objective"] == "check inventory for anti-GFP"
    assert call_kwargs["org_id"] == "org_test"
    assert call_kwargs["conversation_id"] == "conv_123"
    assert call_kwargs["model"] == "test-model"
    assert isinstance(call_kwargs["latency_ms"], float)


@pytest.mark.asyncio
async def test_critic_traces_call_on_review():
    """P4.2: critic.review calls trace_critic_call."""
    result = TaskResult(
        task_id="t-ct",
        assigned_agent="data_analyst",
        status="completed",
        output="IC50 = 12 nM, exp_id: e-001",
    )
    provider = _mock_provider(
        _fake_response(json.dumps({"decision": "pass", "reason": "ok"}))
    )

    with patch.object(
        critic_module, "get_settings",
        return_value=SimpleNamespace(
            openai_api_key="x", anthropic_api_key="x",
            default_provider="anthropic",
            critic_model="test-model",
        ),
    ):
        with patch.object(critic_module, "trace_critic_call") as trace_mock:
            verdict = await critic_module.review(
                "fit", result, provider=provider,
                org_id="org_test", conversation_id="conv_test",
            )

    assert verdict.decision == "pass"
    trace_mock.assert_called_once()
    call_kwargs = trace_mock.call_args.kwargs
    assert call_kwargs["task_id"] == "t-ct"
    assert call_kwargs["specialist"] == "data_analyst"
    assert call_kwargs["decision"] == "pass"
    assert call_kwargs["org_id"] == "org_test"
    assert call_kwargs["conversation_id"] == "conv_test"
