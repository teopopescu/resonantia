"""Agent execution workflow — orchestrates the LLM agent loop via Temporal."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from resonantia.workflows.activities import (
        compile_results,
        evaluate_result,
        execute_in_sandbox,
        generate_code,
        llm_plan,
        retrieve_relevant_tools,
        review_for_hallucinations,
    )


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class AgentRunInput:
    user_message: str
    conversation_id: str
    user_id: str
    context: dict[str, Any] | None = None


@dataclass
class PlanStep:
    description: str
    tool_hint: str | None = None
    order: int = 0


@dataclass
class Plan:
    steps: list[PlanStep] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class EvalResult:
    success: bool
    output: str
    revised_step: PlanStep | None = None


@dataclass
class StepOutput:
    step: PlanStep
    code: str
    execution_output: str
    eval: EvalResult


@dataclass
class AgentRunOutput:
    response: str
    conversation_id: str
    step_outputs: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------

RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_attempts=3,
    maximum_interval=timedelta(seconds=30),
)


@workflow.defn
class AgentRunWorkflow:
    """Orchestrates a full agent run: plan, generate, execute, evaluate."""

    @workflow.run
    async def run(self, inp: AgentRunInput) -> AgentRunOutput:
        # 1. Retrieve relevant tools
        tools = await workflow.execute_activity(
            retrieve_relevant_tools,
            args=[inp.user_message],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RETRY_POLICY,
        )

        # 2. Create a step-by-step plan
        plan: Plan = await workflow.execute_activity(
            llm_plan,
            args=[inp.user_message, tools],
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RETRY_POLICY,
        )

        # 3. Loop over plan steps
        all_outputs: list[StepOutput] = []
        context: dict[str, Any] = {"conversation_id": inp.conversation_id}

        for step in plan.steps:
            # Check for cancellation between steps
            workflow.check_condition(lambda: False, timeout=timedelta(seconds=0))

            # 3a. Generate code
            code: str = await workflow.execute_activity(
                generate_code,
                args=[step, context],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RETRY_POLICY,
            )

            # 3b. Execute in sandbox (long-running — uses heartbeat)
            execution_output: str = await workflow.execute_activity(
                execute_in_sandbox,
                args=[code, 300],
                start_to_close_timeout=timedelta(seconds=360),
                heartbeat_timeout=timedelta(seconds=60),
                retry_policy=RETRY_POLICY,
            )

            # 3c. Evaluate result
            eval_result: EvalResult = await workflow.execute_activity(
                evaluate_result,
                args=[step, execution_output],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RETRY_POLICY,
            )

            step_out = StepOutput(
                step=step,
                code=code,
                execution_output=execution_output,
                eval=eval_result,
            )
            all_outputs.append(step_out)

            # Update context with latest output for next step
            context[f"step_{step.order}_output"] = execution_output

        # 4. Compile results
        serialised_outputs = [o.execution_output for o in all_outputs]
        compiled: str = await workflow.execute_activity(
            compile_results,
            args=[serialised_outputs],
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RETRY_POLICY,
        )

        # 5. Review for hallucinations
        sources = [o.execution_output for o in all_outputs]
        reviewed: str = await workflow.execute_activity(
            review_for_hallucinations,
            args=[compiled, sources],
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RETRY_POLICY,
        )

        return AgentRunOutput(
            response=reviewed,
            conversation_id=inp.conversation_id,
            step_outputs=[
                {
                    "step": o.step.description,
                    "success": o.eval.success,
                    "output_preview": o.execution_output[:500],
                }
                for o in all_outputs
            ],
        )
