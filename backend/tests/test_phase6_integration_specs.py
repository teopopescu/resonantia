"""Smoke tests for Phase 6 staging integration regression specs."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_integration_specs_exist_and_are_env_gated():
    audit = ROOT / "tests" / "integration" / "test_audit_completeness.py"
    latency = ROOT / "tests" / "integration" / "test_latency_regression.py"

    for path in (audit, latency):
        source = path.read_text()
        assert "RESONANTIA_BASE_URL" in source
        assert "pytest.mark.skipif" in source


def test_audit_and_latency_specs_cover_required_paths():
    combined = "\n".join(
        path.read_text()
        for path in (ROOT / "tests" / "integration").glob("test_*.py")
    )

    for expected in (
        "/api/v1/files/upload",
        "/api/v1/processing/dose-response/from-file",
        "/api/v1/eln/draft-from-result",
        "audit_log",
        "p95",
        "budget",
    ):
        assert expected in combined
