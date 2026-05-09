"""Structured messages exchanged between the orchestrator and specialist subagents.

Free-form text between agents is where multi-agent systems break.
Schema-validated messages is where they hold together. Per
docs/agentic-architecture.md §2 and docs/subagents-acp-plan.md.
"""

from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

AgentName = Literal[
    "plate_designer",
    "data_analyst",
    "eln_scribe",
    "protocol_agent",
    "sample_agent",
    "general",
]


class TaskAssignment(BaseModel):
    """Orchestrator → specialist task hand-off."""

    task_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    assigned_agent: AgentName
    objective: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    parent_task_id: str | None = None


class TaskResult(BaseModel):
    """Specialist → orchestrator response."""

    task_id: str
    assigned_agent: AgentName
    status: Literal["completed", "failed", "needs_clarification"]
    output: str
    rationale: str = ""
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0


class CriticVerdict(BaseModel):
    """Critic agent's review of a TaskResult before it reaches the user."""

    task_id: str
    decision: Literal["pass", "soft_warn", "reject"]
    reason: str = ""


class OrchestrationPlan(BaseModel):
    """Decomposition of a user message into specialist task assignments.

    The orchestrator emits this as structured output. An empty
    ``assignments`` list is the signal that the orchestrator has chosen
    to answer directly without delegation.
    """

    rationale: str
    assignments: list[TaskAssignment] = Field(default_factory=list)
    can_run_parallel: bool = False


class OrchestratorReply(BaseModel):
    """Final response returned to the chat layer."""

    message: str
    conversation_id: str
    routed_to: list[AgentName] = Field(default_factory=list)
    sub_results: list[TaskResult] = Field(default_factory=list)
    critic_verdicts: list[CriticVerdict] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
