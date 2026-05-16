"""Smoke tests for observability dashboard definitions."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_DIR = ROOT / "infra" / "dashboards"


def test_dashboard_json_files_are_valid():
    for name in ("latency.json", "voice.json", "cost.json"):
        path = DASHBOARD_DIR / name
        payload = json.loads(path.read_text())
        assert payload["title"]
        assert payload["panels"]
        assert payload["schemaVersion"] >= 30


def test_dashboards_cover_required_phase6_metrics():
    combined = "\n".join(path.read_text() for path in DASHBOARD_DIR.glob("*.json"))

    for expected in (
        "p50",
        "p95",
        "p99",
        "Error rate",
        "Active voice sessions",
        "Token usage",
        "Estimated LLM cost",
        "Prompt cache hit rate",
    ):
        assert expected in combined
