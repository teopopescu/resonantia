"""OpenTelemetry setup and span helpers.

The helpers in this module intentionally degrade to no-ops when
OpenTelemetry is not installed or is disabled. That keeps local tests and
developer environments independent of a running collector while production
can export traces by setting standard OTEL environment variables.
"""

from __future__ import annotations

from contextlib import contextmanager, nullcontext
import logging
from typing import Any, Iterator

logger = logging.getLogger(__name__)

try:  # pragma: no cover - exercised when optional dependency is installed
    from opentelemetry import propagate, trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.trace import Span, SpanKind, Status, StatusCode
except Exception:  # pragma: no cover - no-op fallback
    propagate = None  # type: ignore[assignment]
    trace = None  # type: ignore[assignment]
    OTLPSpanExporter = None  # type: ignore[assignment]
    Resource = None  # type: ignore[assignment]
    TracerProvider = None  # type: ignore[assignment]
    BatchSpanProcessor = None  # type: ignore[assignment]
    Span = Any  # type: ignore[misc, assignment]
    SpanKind = None  # type: ignore[assignment]
    Status = None  # type: ignore[assignment]
    StatusCode = None  # type: ignore[assignment]


_initialized = False


def initialize_telemetry() -> bool:
    """Initialize OpenTelemetry tracing with an OTLP exporter."""
    global _initialized
    if _initialized:
        return trace is not None
    if trace is None:
        logger.info("OpenTelemetry packages unavailable; tracing disabled")
        _initialized = True
        return False

    from resonantia.config import get_settings

    settings = get_settings()
    resource = Resource.create({
        "service.name": settings.otel_service_name,
        "deployment.environment": settings.otel_environment,
    })
    provider = TracerProvider(resource=resource)
    exporter_kwargs: dict[str, Any] = {}
    if settings.otel_exporter_otlp_endpoint:
        exporter_kwargs["endpoint"] = settings.otel_exporter_otlp_endpoint
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(**exporter_kwargs)))
    trace.set_tracer_provider(provider)
    _initialized = True
    return True


def get_tracer():
    if trace is None:
        return None
    return trace.get_tracer("resonantia")


@contextmanager
def start_span(
    name: str,
    attributes: dict[str, Any] | None = None,
    *,
    kind: Any | None = None,
) -> Iterator[Span | None]:
    """Start a span, or yield ``None`` when tracing is unavailable."""
    tracer = get_tracer()
    if tracer is None:
        with nullcontext(None) as span:
            yield span
        return

    span_kind = kind
    if span_kind is None and SpanKind is not None:
        span_kind = SpanKind.INTERNAL
    with tracer.start_as_current_span(name, kind=span_kind) as span:
        set_span_attributes(span, attributes or {})
        yield span


def set_span_attributes(span: Span | None, attributes: dict[str, Any]) -> None:
    if span is None:
        return
    for key, value in attributes.items():
        if value is None:
            continue
        if isinstance(value, (str, bool, int, float)):
            span.set_attribute(key, value)
        else:
            span.set_attribute(key, str(value))


def record_span_exception(span: Span | None, exc: BaseException) -> None:
    if span is None:
        return
    span.record_exception(exc)
    if Status is not None and StatusCode is not None:
        span.set_status(Status(StatusCode.ERROR, str(exc)))


def current_trace_context() -> dict[str, str]:
    """Return W3C trace context headers for Temporal payload propagation."""
    if propagate is None:
        return {}
    carrier: dict[str, str] = {}
    propagate.inject(carrier)
    return carrier
