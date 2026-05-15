"""Tests for short voice response composition."""

from __future__ import annotations

import pytest

from resonantia.services.voice_composer import compose_voice_response, template_spoken_summary


def test_ic50_result_generates_template_response():
    summary = template_spoken_summary({"compound": "A", "ic50": 42.35})
    assert summary == "IC50 is 42.4 nanomolar."


def test_z_prime_result_generates_template_response():
    summary = template_spoken_summary({"assay": {"z_prime": 0.71}})
    assert summary == "Z-prime is 0.71."


def test_sample_location_generates_template_response():
    summary = template_spoken_summary({"sample_name": "Tube A", "location": "Freezer 2, rack B"})
    assert summary == "Tube A is in location Freezer 2, rack B."


def test_inventory_expiry_generates_template_response():
    summary = template_spoken_summary({"expiring_this_week": 6})
    assert summary == "6 samples expire this week."


@pytest.mark.asyncio
async def test_compose_returns_full_result_and_template_summary():
    result = {"ic50": 12.0, "plot_url": "/plot.png"}
    composed = await compose_voice_response(result)
    assert composed.full_result == result
    assert composed.spoken_summary == "IC50 is 12.0 nanomolar."


@pytest.mark.asyncio
async def test_multi_tool_result_uses_llm_summary_under_150_words():
    long_text = " ".join(f"word{i}" for i in range(180))

    async def fake_summary(result):
        assert result["tools"] == ["lookup_sample", "check_inventory"]
        return long_text

    composed = await compose_voice_response(
        {"tools": ["lookup_sample", "check_inventory"], "results": [{"ok": True}]},
        summary_fn=fake_summary,
    )

    assert len(composed.spoken_summary.split()) <= 150
    assert composed.spoken_summary.endswith(".")
