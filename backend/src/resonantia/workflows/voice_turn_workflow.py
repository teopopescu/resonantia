"""Voice turn workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from resonantia.workflows.voice_activities import (
        complete_voice_turn_activity,
        create_voice_turn_activity,
        fail_voice_turn_activity,
        run_voice_agent_activity,
        synthesize_voice_turn_activity,
        transcribe_voice_turn_activity,
    )


@dataclass
class VoiceTurnInput:
    org_id: str
    user_id: str
    idempotency_key: str
    input_audio_path: str
    conversation_id: str | None = None
    request_context: dict[str, Any] | None = None
    workflow_id: str | None = None


@dataclass
class VoiceTurnOutput:
    turn_id: str
    status: str
    transcript: str
    response_text: str
    conversation_id: str | None
    audio_id: str | None
    tool_calls: list[dict[str, Any]]
    stt_latency_ms: int
    agent_latency_ms: int
    tts_latency_ms: int
    total_latency_ms: int


RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_attempts=3,
    maximum_interval=timedelta(seconds=30),
)


@workflow.defn
class VoiceTurnWorkflow:
    """Durable STT -> agent -> TTS workflow for one voice turn."""

    @workflow.run
    async def run(self, inp: VoiceTurnInput) -> VoiceTurnOutput:
        create_result: dict[str, Any] = await workflow.execute_activity(
            create_voice_turn_activity,
            args=[
                inp.org_id,
                inp.user_id,
                inp.idempotency_key,
                inp.conversation_id,
                inp.input_audio_path,
                inp.workflow_id,
            ],
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RETRY_POLICY,
        )
        turn_id = create_result["turn_id"]

        try:
            stt_result: dict[str, Any] = await workflow.execute_activity(
                transcribe_voice_turn_activity,
                args=[turn_id, inp.input_audio_path],
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RETRY_POLICY,
            )
            transcript = stt_result.get("transcript", "")

            agent_result: dict[str, Any] = await workflow.execute_activity(
                run_voice_agent_activity,
                args=[turn_id, transcript, inp.conversation_id, inp.request_context],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RETRY_POLICY,
            )
            response_text = agent_result.get("response_text", "")

            tts_result: dict[str, Any] = await workflow.execute_activity(
                synthesize_voice_turn_activity,
                args=[turn_id, response_text],
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RETRY_POLICY,
            )

            complete_result: dict[str, Any] = await workflow.execute_activity(
                complete_voice_turn_activity,
                args=[
                    turn_id,
                    transcript,
                    response_text,
                    tts_result.get("audio_id"),
                    agent_result.get("conversation_id"),
                    agent_result.get("tool_calls", []),
                    agent_result.get("intent_class"),
                    stt_result.get("stt_latency_ms", 0),
                    agent_result.get("agent_latency_ms", 0),
                    tts_result.get("tts_latency_ms", 0),
                ],
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RETRY_POLICY,
            )
        except Exception as exc:
            await workflow.execute_activity(
                fail_voice_turn_activity,
                args=[turn_id, str(exc)],
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RETRY_POLICY,
            )
            raise

        return VoiceTurnOutput(
            turn_id=turn_id,
            status=complete_result.get("status", "completed"),
            transcript=transcript,
            response_text=response_text,
            conversation_id=agent_result.get("conversation_id"),
            audio_id=tts_result.get("audio_id"),
            tool_calls=agent_result.get("tool_calls", []),
            stt_latency_ms=stt_result.get("stt_latency_ms", 0),
            agent_latency_ms=agent_result.get("agent_latency_ms", 0),
            tts_latency_ms=tts_result.get("tts_latency_ms", 0),
            total_latency_ms=complete_result.get("total_latency_ms", 0),
        )
