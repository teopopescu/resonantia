"""Tests for P0.3: Eliminate unsafe Temporal execution.

Verifies that:
- No subprocess references exist in the backend source
- AgentRunWorkflow is fully removed
- The new AgentToolCallWorkflow input includes org_id
- Unsafe activities (generate_code, execute_in_sandbox, review_for_hallucinations)
  are deleted
- chat.py has timeout on workflow result
- chat.py uses specific exception handling (not bare except Exception)
"""

from __future__ import annotations

import ast
import importlib
import os
import textwrap
from pathlib import Path

import pytest

# Root of the backend source tree
BACKEND_SRC = Path(__file__).resolve().parent.parent / "src"


# ---------------------------------------------------------------------------
# 1. No subprocess references in backend source
# ---------------------------------------------------------------------------


class TestNoSubprocess:
    """Verify that subprocess/create_subprocess_exec/python -c are purged."""

    def _collect_python_files(self) -> list[Path]:
        """Collect all .py files under backend/src/."""
        return list(BACKEND_SRC.rglob("*.py"))

    def test_no_subprocess_import(self):
        """No file in backend/src should import subprocess."""
        violations = []
        for path in self._collect_python_files():
            content = path.read_text()
            if "import subprocess" in content or "from subprocess" in content:
                violations.append(str(path.relative_to(BACKEND_SRC)))
        assert violations == [], f"Files still importing subprocess: {violations}"

    def test_no_subprocess_references(self):
        """No file should reference subprocess.run, subprocess.Popen, etc."""
        violations = []
        for path in self._collect_python_files():
            content = path.read_text()
            for pattern in [
                "subprocess.run",
                "subprocess.Popen",
                "subprocess.call",
                "subprocess.check_output",
                "create_subprocess_exec",
                "create_subprocess_shell",
            ]:
                if pattern in content:
                    violations.append(f"{path.relative_to(BACKEND_SRC)}: {pattern}")
        assert violations == [], f"Subprocess references found: {violations}"

    def test_no_python_c_execution(self):
        """No file should run 'python -c' to execute generated code."""
        violations = []
        for path in self._collect_python_files():
            content = path.read_text()
            if '"python", "-c"' in content or "'python', '-c'" in content:
                violations.append(str(path.relative_to(BACKEND_SRC)))
        assert violations == [], f"Files with python -c execution: {violations}"


# ---------------------------------------------------------------------------
# 2. AgentRunWorkflow is removed
# ---------------------------------------------------------------------------


class TestAgentRunWorkflowRemoved:
    """Verify the old unsafe workflow class is fully gone."""

    def test_no_agent_run_workflow_class(self):
        """AgentRunWorkflow should not exist in agent_workflow.py."""
        from resonantia.workflows import agent_workflow

        assert not hasattr(agent_workflow, "AgentRunWorkflow"), (
            "AgentRunWorkflow still exists — it should be replaced by AgentToolCallWorkflow"
        )

    def test_no_agent_run_input_class(self):
        """AgentRunInput should not exist in agent_workflow.py."""
        from resonantia.workflows import agent_workflow

        assert not hasattr(agent_workflow, "AgentRunInput"), (
            "AgentRunInput still exists — should be replaced by AgentToolCallInput"
        )

    def test_no_agent_run_output_class(self):
        """AgentRunOutput should not exist in agent_workflow.py."""
        from resonantia.workflows import agent_workflow

        assert not hasattr(agent_workflow, "AgentRunOutput"), (
            "AgentRunOutput still exists — should be replaced by AgentToolCallOutput"
        )


# ---------------------------------------------------------------------------
# 3. New workflow has correct input schema
# ---------------------------------------------------------------------------


class TestAgentToolCallWorkflow:
    """Verify AgentToolCallWorkflow and its input/output types."""

    def test_workflow_exists(self):
        from resonantia.workflows.agent_workflow import AgentToolCallWorkflow

        assert AgentToolCallWorkflow is not None

    def test_input_has_org_id(self):
        from resonantia.workflows.agent_workflow import AgentToolCallInput

        inp = AgentToolCallInput(
            messages=[{"role": "user", "content": "hello"}],
            tools=[],
            org_id="org_test",
        )
        assert inp.org_id == "org_test"

    def test_input_has_messages(self):
        from resonantia.workflows.agent_workflow import AgentToolCallInput

        msgs = [{"role": "user", "content": "test"}]
        inp = AgentToolCallInput(messages=msgs, tools=[], org_id="org_1")
        assert inp.messages == msgs

    def test_input_has_tools(self):
        from resonantia.workflows.agent_workflow import AgentToolCallInput

        tools = [{"name": "lookup_sample", "description": "look up", "input_schema": {}}]
        inp = AgentToolCallInput(messages=[], tools=tools, org_id="org_1")
        assert inp.tools == tools

    def test_input_has_max_iterations(self):
        from resonantia.workflows.agent_workflow import AgentToolCallInput

        inp = AgentToolCallInput(messages=[], tools=[], org_id="org_1")
        assert inp.max_iterations == 10  # default

        inp2 = AgentToolCallInput(messages=[], tools=[], org_id="org_1", max_iterations=5)
        assert inp2.max_iterations == 5

    def test_input_has_conversation_id(self):
        from resonantia.workflows.agent_workflow import AgentToolCallInput

        inp = AgentToolCallInput(
            messages=[], tools=[], org_id="org_1", conversation_id="conv-123"
        )
        assert inp.conversation_id == "conv-123"

    def test_output_has_required_fields(self):
        from resonantia.workflows.agent_workflow import AgentToolCallOutput

        out = AgentToolCallOutput(
            response="hello",
            tool_calls_made=[{"name": "lookup_sample", "args": {}, "result": "{}"}],
            conversation_id="conv-123",
        )
        assert out.response == "hello"
        assert len(out.tool_calls_made) == 1
        assert out.conversation_id == "conv-123"


# ---------------------------------------------------------------------------
# 4. Unsafe activities are deleted
# ---------------------------------------------------------------------------


class TestUnsafeActivitiesRemoved:
    """Verify generate_code, execute_in_sandbox, review_for_hallucinations are gone."""

    def test_no_generate_code(self):
        from resonantia.workflows import activities

        assert not hasattr(activities, "generate_code"), (
            "generate_code activity still exists — must be deleted"
        )

    def test_no_execute_in_sandbox(self):
        from resonantia.workflows import activities

        assert not hasattr(activities, "execute_in_sandbox"), (
            "execute_in_sandbox activity still exists — must be deleted"
        )

    def test_no_review_for_hallucinations(self):
        from resonantia.workflows import activities

        assert not hasattr(activities, "review_for_hallucinations"), (
            "review_for_hallucinations activity still exists — must be deleted"
        )

    def test_no_retrieve_relevant_tools(self):
        """retrieve_relevant_tools used TOOLS_FALLBACK which doesn't exist."""
        from resonantia.workflows import activities

        assert not hasattr(activities, "retrieve_relevant_tools"), (
            "retrieve_relevant_tools activity still exists — references nonexistent TOOLS_FALLBACK"
        )


# ---------------------------------------------------------------------------
# 5. New safe activities exist
# ---------------------------------------------------------------------------


class TestSafeActivitiesExist:
    """Verify the new activities are registered."""

    def test_call_llm_activity_exists(self):
        from resonantia.workflows.activities import call_llm_activity

        assert callable(call_llm_activity)

    def test_execute_tool_activity_exists(self):
        from resonantia.workflows.activities import execute_tool_activity

        assert callable(execute_tool_activity)

    def test_persist_conversation_activity_exists(self):
        from resonantia.workflows.activities import persist_conversation_activity

        assert callable(persist_conversation_activity)

    def test_evaluate_result_still_exists(self):
        from resonantia.workflows.activities import evaluate_result

        assert callable(evaluate_result)

    def test_compile_results_still_exists(self):
        from resonantia.workflows.activities import compile_results

        assert callable(compile_results)


# ---------------------------------------------------------------------------
# 6. Worker registers correct workflow + activities
# ---------------------------------------------------------------------------


class TestWorkerRegistration:
    """Verify worker.py registers the new workflow and activities."""

    def test_worker_has_new_workflow(self):
        from resonantia.workflows.worker import ALL_WORKFLOWS
        from resonantia.workflows.agent_workflow import AgentToolCallWorkflow

        assert AgentToolCallWorkflow in ALL_WORKFLOWS

    def test_worker_does_not_have_old_workflow(self):
        from resonantia.workflows.worker import ALL_WORKFLOWS

        workflow_names = [w.__name__ for w in ALL_WORKFLOWS]
        assert "AgentRunWorkflow" not in workflow_names

    def test_worker_has_new_activities(self):
        from resonantia.workflows.activities import (
            call_llm_activity,
            execute_tool_activity,
            persist_conversation_activity,
        )
        from resonantia.workflows.worker import ALL_ACTIVITIES

        assert call_llm_activity in ALL_ACTIVITIES
        assert execute_tool_activity in ALL_ACTIVITIES
        assert persist_conversation_activity in ALL_ACTIVITIES

    def test_worker_no_unsafe_activities(self):
        from resonantia.workflows.worker import ALL_ACTIVITIES

        activity_names = [a.__name__ for a in ALL_ACTIVITIES]
        assert "generate_code" not in activity_names
        assert "execute_in_sandbox" not in activity_names
        assert "review_for_hallucinations" not in activity_names
        assert "retrieve_relevant_tools" not in activity_names


# ---------------------------------------------------------------------------
# 7. chat.py has timeout and specific exception handling
# ---------------------------------------------------------------------------


class TestChatSafety:
    """Verify chat.py timeout and exception handling via AST inspection."""

    def _get_chat_source(self) -> str:
        chat_path = BACKEND_SRC / "resonantia" / "api" / "chat.py"
        return chat_path.read_text()

    def test_has_asyncio_wait_for(self):
        """chat.py must use asyncio.wait_for for timeout."""
        source = self._get_chat_source()
        assert "asyncio.wait_for" in source, (
            "chat.py must use asyncio.wait_for(handle.result(), timeout=...) "
            "instead of bare await handle.result()"
        )

    def test_has_timeout_value(self):
        """chat.py must specify a timeout value."""
        source = self._get_chat_source()
        assert "timeout=" in source, "chat.py must specify a timeout= parameter"

    def test_catches_timeout_error(self):
        """chat.py must catch asyncio.TimeoutError."""
        source = self._get_chat_source()
        assert "TimeoutError" in source, (
            "chat.py must catch asyncio.TimeoutError for workflow timeout"
        )

    def test_catches_rpc_error(self):
        """chat.py must catch RPCError for Temporal unavailability."""
        source = self._get_chat_source()
        assert "RPCError" in source, (
            "chat.py must catch RPCError for Temporal connection failures"
        )

    def test_catches_service_error(self):
        """chat.py must catch ServiceError for Temporal service errors."""
        source = self._get_chat_source()
        assert "ServiceError" in source, (
            "chat.py must catch ServiceError for Temporal service errors"
        )

    def test_no_bare_except_exception(self):
        """chat.py must NOT have 'except Exception' in the send_message function."""
        source = self._get_chat_source()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "send_message":
                for child in ast.walk(node):
                    if isinstance(child, ast.ExceptHandler):
                        if child.type is not None and isinstance(child.type, ast.Name):
                            assert child.type.id != "Exception", (
                                "send_message must not use bare 'except Exception' — "
                                "use specific Temporal error types instead"
                            )
                break

    def test_catches_value_error_for_cross_org(self):
        """chat.py must catch ValueError for cross-org access."""
        source = self._get_chat_source()
        assert "ValueError" in source, (
            "chat.py must catch ValueError for cross-org conversation access"
        )


# ---------------------------------------------------------------------------
# 8. temporal_client.py passes org_id
# ---------------------------------------------------------------------------


class TestTemporalClientOrgId:
    """Verify temporal_client.py passes org_id to the workflow."""

    def test_start_agent_workflow_accepts_org_id(self):
        """start_agent_workflow should accept an org_id parameter."""
        import inspect
        from resonantia.services.temporal_client import start_agent_workflow

        sig = inspect.signature(start_agent_workflow)
        assert "org_id" in sig.parameters, (
            "start_agent_workflow must accept org_id parameter"
        )

    def test_start_agent_workflow_source_uses_org_id(self):
        """The org_id should be passed to AgentToolCallInput."""
        import inspect
        from resonantia.services import temporal_client

        source = inspect.getsource(temporal_client.start_agent_workflow)
        assert "org_id" in source, (
            "start_agent_workflow must pass org_id to AgentToolCallInput"
        )
        assert "AgentToolCallInput" in source, (
            "start_agent_workflow must use AgentToolCallInput (not AgentRunInput)"
        )
