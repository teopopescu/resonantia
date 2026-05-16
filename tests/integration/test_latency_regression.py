"""Staging latency regression checks.

Skipped unless RESONANTIA_BASE_URL is configured. Budgets are p95 ceilings
including 20 percent headroom above current production budgets.
"""

from __future__ import annotations

from statistics import quantiles
import os
import time

import pytest


pytest.importorskip("httpx")


BASE_URL = os.getenv("RESONANTIA_BASE_URL", "").rstrip("/")
AUTH_TOKEN = os.getenv("RESONANTIA_AUTH_TOKEN", "")
ORG_ID = os.getenv("RESONANTIA_ORG_ID", "org_default")

pytestmark = pytest.mark.skipif(not BASE_URL, reason="RESONANTIA_BASE_URL is not configured")


def test_latency_regression_p95_within_budget():
    import httpx

    headers = {"X-Org-Id": ORG_ID}
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"

    scenarios = [
        ("health", "GET", "/health", None, 250.0),
        ("files.list", "GET", "/api/v1/files/", None, 1200.0),
        ("chat.message", "POST", "/api/v1/chat/message", {"message": "hello"}, 12000.0),
    ]

    with httpx.Client(base_url=BASE_URL, headers=headers, timeout=30.0) as client:
        for name, method, path, payload, budget_ms in scenarios:
            samples = []
            for _ in range(10):
                start = time.perf_counter()
                response = client.request(method, path, json=payload)
                elapsed_ms = (time.perf_counter() - start) * 1000
                if response.status_code >= 500:
                    pytest.fail(f"{name} returned {response.status_code}: {response.text[:200]}")
                samples.append(elapsed_ms)

            p95 = quantiles(samples, n=20)[18]
            assert p95 <= budget_ms, f"{name} p95 {p95:.1f}ms exceeded budget {budget_ms:.1f}ms"
