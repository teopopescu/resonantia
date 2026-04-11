"""Tests for Resonantia Lab guardrails."""

from resonantia.services.guardrails import check_guardrails


def test_lab_query_allowed():
    allowed, reason = check_guardrails("Design a plate map for my screen")
    assert allowed is True


def test_blocked_poem():
    allowed, reason = check_guardrails("Write me a poem about flowers")
    assert allowed is False
    assert "write me a poem" in reason.lower()


def test_blocked_homework():
    allowed, reason = check_guardrails("Help me with my homework on algebra")
    assert allowed is False
    assert "homework" in reason.lower()


def test_greeting_allowed():
    allowed, reason = check_guardrails("Hello, how can you help?")
    assert allowed is True


def test_dose_response_allowed():
    allowed, reason = check_guardrails("Fit IC50 curves for compound X")
    assert allowed is True


def test_weather_allowed_ambiguous():
    """Short ambiguous messages are allowed through; the system prompt handles edge cases."""
    allowed, reason = check_guardrails("What is the weather?")
    assert allowed is True


def test_empty_message_allowed():
    allowed, reason = check_guardrails("")
    assert allowed is True
    assert reason == ""
