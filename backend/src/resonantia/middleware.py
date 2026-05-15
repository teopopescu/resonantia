"""Request-scoped middleware for IDs, demo responses, and latency logs."""

from __future__ import annotations

import contextvars
import json
import logging
import time
import uuid
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from resonantia.config import get_settings

logger = logging.getLogger("resonantia.request")

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id",
    default=None,
)
latency_fields_var: contextvars.ContextVar[dict[str, float] | None] = contextvars.ContextVar(
    "latency_fields",
    default=None,
)


def get_request_id() -> str | None:
    """Return the request ID for the current async context."""
    return request_id_var.get()


def log_stage_latency(stage: str, elapsed_ms: float, **extra: Any) -> None:
    """Emit a structured JSON latency log for a pipeline stage."""
    rounded_ms = round(elapsed_ms, 2)
    fields = latency_fields_var.get()
    if fields is not None:
        fields[f"{stage}_ms"] = fields.get(f"{stage}_ms", 0.0) + rounded_ms

    payload: dict[str, Any] = {
        "event": "latency",
        "stage": stage,
        "request_id": get_request_id(),
        f"{stage}_ms": rounded_ms,
    }
    payload.update(extra)
    logger.info(json.dumps(payload, default=str, sort_keys=True))


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach an X-Request-Id and log total request latency."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.latency_fields = {
            "stt_ms": 0.0,
            "llm_ms": 0.0,
            "tool_ms": 0.0,
            "agent_ms": 0.0,
            "tts_ms": 0.0,
            "db_ms": 0.0,
        }
        token = request_id_var.set(request_id)
        latency_token = latency_fields_var.set(request.state.latency_fields)
        start = time.monotonic()

        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
            latency_fields_var.reset(latency_token)

        total_ms = (time.monotonic() - start) * 1000
        response.headers["X-Request-Id"] = request_id

        settings = get_settings()
        if settings.demo_mode:
            response.headers["X-Demo-Mode"] = "true"
            response = await _add_demo_mode_to_json_object(response, request_id)

        latency_fields = dict(request.state.latency_fields)
        latency_fields["total_ms"] = round(total_ms, 2)
        latency_fields["agent_ms"] = round(
            latency_fields.get("agent_ms", 0.0)
            or latency_fields.get("llm_ms", 0.0) + latency_fields.get("tool_ms", 0.0),
            2,
        )

        logger.info(
            json.dumps(
                {
                    "event": "request_complete",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    **latency_fields,
                },
                sort_keys=True,
            )
        )
        return response


async def _add_demo_mode_to_json_object(response: Response, request_id: str) -> Response:
    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        return response

    body = b""
    async for chunk in response.body_iterator:
        body += chunk

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        payload = None

    if isinstance(payload, dict):
        payload.setdefault("mode", "demo")
        body = json.dumps(payload, default=str).encode("utf-8")

    headers = dict(response.headers)
    headers["X-Request-Id"] = request_id
    headers["X-Demo-Mode"] = "true"
    headers["content-length"] = str(len(body))
    return Response(
        content=body,
        status_code=response.status_code,
        headers=headers,
        media_type="application/json",
        background=response.background,
    )
