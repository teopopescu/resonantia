"""Voice-safe response composition for short spoken summaries."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

MAX_SPOKEN_WORDS = 150

SummaryFn = Callable[[dict[str, Any]], Awaitable[str]]


@dataclass
class VoiceComposition:
    full_result: dict[str, Any]
    spoken_summary: str


def _word_limit(text: str, max_words: int = MAX_SPOKEN_WORDS) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(".,;:") + "."


def _number(value: Any, digits: int = 3) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if numeric == 0:
        return "0"
    if abs(numeric) >= 100:
        return f"{numeric:.0f}"
    if abs(numeric) >= 10:
        return f"{numeric:.1f}"
    return f"{numeric:.{digits}g}"


def _find_key(payload: Any, *keys: str) -> Any:
    if isinstance(payload, dict):
        for key in keys:
            if key in payload and payload[key] is not None:
                return payload[key]
        for value in payload.values():
            found = _find_key(value, *keys)
            if found is not None:
                return found
    if isinstance(payload, list):
        for item in payload:
            found = _find_key(item, *keys)
            if found is not None:
                return found
    return None


def template_spoken_summary(result: dict[str, Any]) -> str | None:
    ic50 = _find_key(result, "ic50", "ec50", "IC50", "EC50")
    if ic50 is not None:
        unit = _find_key(result, "unit", "units", "concentration_unit") or "nanomolar"
        return f"IC50 is {_number(ic50)} {unit}."

    z_prime = _find_key(result, "z_prime", "zPrime", "z-prime")
    if z_prime is not None:
        return f"Z-prime is {_number(z_prime)}."

    location = _find_key(result, "location", "storage_location")
    sample_name = _find_key(result, "sample_name", "sample", "name") or "That sample"
    if location is not None:
        return f"{sample_name} is in location {location}."

    expiring = _find_key(result, "expiring_within_7_days", "expiring_this_week", "expires_this_week")
    if expiring is not None:
        return f"{_number(expiring, digits=0)} samples expire this week."

    return None


async def _llm_summary(result: dict[str, Any]) -> str:
    from resonantia.services.llm import get_provider

    provider = get_provider()
    response = await provider.completion(
        messages=[
            {
                "role": "system",
                "content": (
                    "Summarize this lab tool result for spoken voice output. "
                    "Use fewer than 150 words, no markdown, and mention only actionable facts."
                ),
            },
            {"role": "user", "content": json.dumps(result, default=str)},
        ],
        max_tokens=220,
    )
    return response.content or "The result is ready in the interface."


async def compose_voice_response(
    full_result: dict[str, Any],
    *,
    summary_fn: SummaryFn | None = None,
) -> VoiceComposition:
    """Return full UI result plus a short TTS-safe spoken summary."""
    template = template_spoken_summary(full_result)
    if template is not None:
        return VoiceComposition(full_result=full_result, spoken_summary=_word_limit(template))

    summarizer = summary_fn or _llm_summary
    summary = await summarizer(full_result)
    summary = summary.strip() or "The result is ready in the interface."
    return VoiceComposition(full_result=full_result, spoken_summary=_word_limit(summary))
