# SPEC: Observability Stack — OpenTelemetry + Sentry + PagerDuty

**ID:** P5-OTel
**Phase:** 5 — Production Readiness
**Branch:** `feat/otel-observability`
**Priority:** P1
**Effort:** 5-6 days
**Dependencies:** None (can start anytime)

---

## Problem Statement

Resonantia has Langfuse for LLM-specific tracing but no infrastructure-level observability. When a tool handler crashes, a DB connection times out, or latency spikes during a demo, there's no alert and no way to trace the issue across services. Design partners need reliability guarantees we can't currently provide.

## What We Have

- **Langfuse:** LLM call traces (model, tokens, latency, cost). Specialist-level spans from P4.2.
- **CloudWatch:** ECS container stdout/stderr logs (unstructured, no trace correlation).
- **Nothing else:** No error tracking, no distributed tracing, no alerting.

## What We Need

Three layers working together:

| Layer | Tool | Job |
|-------|------|-----|
| Instrumentation | OpenTelemetry SDK + Collector | Collect traces, metrics, logs from all services |
| Error tracking | Sentry | Catch errors, group them, show stack traces with context |
| Alerting | PagerDuty | Page on-call when error rate or latency exceeds thresholds |

---

## Architecture

### Data Flow

```
ECS Fargate Task
┌───────────────────────────────────────────────┐
│                                               │
│  Backend (FastAPI)   Temporal Worker    MCP    │
│       │                   │             │     │
│       └────────┬──────────┘             │     │
│                │                        │     │
│   OTel SDK (auto-instrumented)          │     │
│                │                        │     │
│                ▼                        │     │
│   OTel Collector (sidecar container)    │     │
│                │                        │     │
└────────────────┼────────────────────────┘
                 │
        ┌────────┼────────┬──────────┐
        │        │        │          │
        ▼        ▼        ▼          ▼
     Sentry  CloudWatch  Langfuse  (future:
   (errors)  (logs +     (LLM)    DataDog)
        │    metrics)
        ▼
    PagerDuty
   (alerting)
```

### Why a Sidecar Collector (not direct export)

The OTel Collector runs as a sidecar container in the same ECS task. The app sends OTLP to `localhost:4317`. The collector then fans out to multiple backends. Benefits:
- App doesn't need Sentry/CloudWatch/DataDog SDKs — just OTLP
- Switching backends is a config change, not a code change
- Collector handles batching, sampling, retry — app doesn't block on export
- Multiple services (backend, worker, MCP) share one collector config

---

## Scope

### In Scope
- OTel SDK instrumentation for FastAPI, SQLAlchemy, httpx (LLM calls)
- OTel Collector sidecar in ECS task definition (Terraform)
- Sentry integration (error tracking + performance)
- PagerDuty integration via Sentry alerts
- Structured JSON logging with trace_id correlation
- Collector config exporting to: Sentry (traces), CloudWatch (logs + metrics)

### Out of Scope
- DataDog / New Relic (future — just change collector config)
- Custom dashboards (use Sentry Performance + CloudWatch)
- Frontend error tracking (defer — Sentry React SDK is a separate PR)

---

## Implementation

### Step 1: OTel SDK in Backend (day 1-2)

```python
# backend/src/resonantia/observability.py

from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

def init_telemetry(app, engine):
    resource = Resource.create({
        "service.name": "resonantia-backend",
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
    })
    
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317"))
        )
    )
    trace.set_tracer_provider(provider)
    
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine)
    HTTPXClientInstrumentor().instrument()
```

Dependencies: `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`, `opentelemetry-instrumentation-sqlalchemy`, `opentelemetry-instrumentation-httpx`, `opentelemetry-exporter-otlp`

### Step 2: Structured Logging (day 2)

Replace print/logger calls with structured JSON that includes trace_id:

```python
import logging
import json
from opentelemetry import trace

class OTelJsonFormatter(logging.Formatter):
    def format(self, record):
        span = trace.get_current_span()
        ctx = span.get_span_context() if span else None
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "trace_id": format(ctx.trace_id, '032x') if ctx and ctx.trace_id else None,
            "span_id": format(ctx.span_id, '016x') if ctx and ctx.span_id else None,
        })
```

### Step 3: Sentry Integration (day 3)

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("ENVIRONMENT", "development"),
    traces_sample_rate=0.1,
    integrations=[FastApiIntegration()],
)
```

Sentry receives OTel traces via its OTLP endpoint in the collector config, plus catches unhandled exceptions directly.

### Step 4: OTel Collector Config (day 3-4)

```yaml
# infrastructure/otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc: { endpoint: 0.0.0.0:4317 }
      http: { endpoint: 0.0.0.0:4318 }

processors:
  batch: { timeout: 5s }
  resource:
    attributes:
      - { key: service.name, action: upsert, value: resonantia }

exporters:
  sentry:
    dsn: ${SENTRY_DSN}
  awscloudwatchlogs:
    log_group_name: /resonantia/otel
    region: ${AWS_REGION}
  awsemf:
    namespace: Resonantia
    region: ${AWS_REGION}

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [sentry]
    metrics:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [awsemf]
    logs:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [awscloudwatchlogs]
```

### Step 5: ECS Task Definition Update (day 4)

Add collector sidecar to Terraform:

```hcl
container_definitions = [
  {
    name      = "backend"
    image     = "${var.ecr_backend_url}:latest"
    essential = true
    environment = [
      { name = "OTEL_EXPORTER_OTLP_ENDPOINT", value = "http://localhost:4317" },
      { name = "SENTRY_DSN", value = var.sentry_dsn },
    ]
  },
  {
    name      = "otel-collector"
    image     = "otel/opentelemetry-collector-contrib:latest"
    essential = false
    command   = ["--config=/etc/otel/config.yaml"]
  },
]
```

### Step 6: PagerDuty + Sentry Alerts (day 5)

In Sentry dashboard:
- Alert rule: "Error rate > 5% for 5 minutes on resonantia-backend" → PagerDuty P1
- Alert rule: "New unhandled exception type" → PagerDuty P2
- Alert rule: "Transaction p95 > 30s for 10 minutes" → PagerDuty P2

PagerDuty integration: Sentry → PagerDuty integration (built-in, just needs API key).

### Step 7: Coexistence with Langfuse (day 5-6)

Langfuse stays for LLM-specific observability. Share trace_id between OTel and Langfuse:

```python
# In llm/provider.py, when making LLM calls:
span = trace.get_current_span()
otel_trace_id = format(span.get_span_context().trace_id, '032x')

# Pass to Langfuse trace
trace_llm_call(..., metadata={"otel_trace_id": otel_trace_id})
```

This lets you cross-reference: "Langfuse shows this conversation cost $0.12" → "OTel shows the same request had a 2s DB query in the tool executor."

---

## Acceptance Criteria

- [ ] Every HTTP request to FastAPI produces an OTel trace
- [ ] Every SQLAlchemy query appears as a span within the request trace
- [ ] Every LLM API call (httpx) appears as a span
- [ ] Logs include `trace_id` and `span_id` for correlation
- [ ] OTel Collector runs as sidecar in ECS task definition
- [ ] Sentry captures unhandled exceptions with stack traces + request context
- [ ] Sentry receives OTel performance traces
- [ ] PagerDuty alert fires on >5% error rate (tested with intentional error)
- [ ] Langfuse traces include `otel_trace_id` for cross-referencing
- [ ] CloudWatch receives structured JSON logs from collector
- [ ] `terraform plan` includes collector sidecar in task definitions

---

## Cost Estimate

| Service | Plan | Monthly Cost |
|---------|------|-------------|
| OTel Collector | Open source (sidecar) | $0 (included in ECS task) |
| Sentry | Team (50K events) | $26/mo |
| PagerDuty | Professional (1 user) | $21/mo |
| CloudWatch Logs | ~1 GB/mo ingestion | $0.50/mo |
| CloudWatch Metrics | Custom metrics | ~$3/mo |
| **Total** | | **~$50/mo** |
