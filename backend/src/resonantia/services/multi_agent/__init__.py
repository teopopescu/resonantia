"""Multi-agent topology — orchestrator, specialist subagents, and critic.

Implements Phase 1 of docs/subagents-acp-plan.md and §2 of
docs/agentic-architecture.md. Behind the ``multi_agent_enabled``
settings flag — the legacy single-agent path in ``services/agent.py``
is unchanged when the flag is off.
"""

from resonantia.services.multi_agent.messages import (
    AgentName,
    CriticVerdict,
    OrchestrationPlan,
    OrchestratorReply,
    TaskAssignment,
    TaskResult,
)
from resonantia.services.multi_agent.orchestrator import chat
from resonantia.services.multi_agent.subagents import SPECIALISTS, run_specialist

__all__ = [
    "AgentName",
    "CriticVerdict",
    "OrchestrationPlan",
    "OrchestratorReply",
    "SPECIALISTS",
    "TaskAssignment",
    "TaskResult",
    "chat",
    "run_specialist",
]
