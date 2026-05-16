"""Validation helpers for ELN drafts generated from processing results."""

from __future__ import annotations

import math
import re
from typing import Any


FLOAT_RE = r"([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"
CLAIM_PATTERNS = {
    "ic50": re.compile(rf"\b(?:ic50|ec50)\b\s*(?:=|:)?\s*{FLOAT_RE}", re.IGNORECASE),
    "r_squared": re.compile(rf"\b(?:r\s*(?:\^2|2|squared)|r_squared)\b\s*(?:=|:)?\s*{FLOAT_RE}", re.IGNORECASE),
    "z_prime": re.compile(rf"\b(?:z\s*['-]?\s*prime|z_prime)\b\s*(?:=|:)?\s*{FLOAT_RE}", re.IGNORECASE),
}
UNSUPPORTED_CLAIM_PATTERN = re.compile(
    rf"\b(ld50|auc|p\s*-?\s*value|ki|kd)\b\s*(?:=|:)?\s*{FLOAT_RE}",
    re.IGNORECASE,
)


def expected_claims_from_result(result: dict[str, Any]) -> dict[str, float]:
    """Extract supported numeric claims from a processing result payload."""
    claims: dict[str, float] = {}
    parameters = result.get("parameters") if isinstance(result.get("parameters"), dict) else {}

    ic50 = parameters.get("ec50", parameters.get("ic50"))
    if ic50 is not None:
        claims["ic50"] = float(ic50)

    r_squared = result.get("r_squared")
    if r_squared is not None:
        claims["r_squared"] = float(r_squared)

    z_prime = result.get("z_prime", result.get("z-prime"))
    if z_prime is not None:
        claims["z_prime"] = float(z_prime)

    return claims


def extract_numeric_claims(markdown: str) -> dict[str, list[float]]:
    """Find supported numeric claims in Markdown prose."""
    found: dict[str, list[float]] = {}
    for claim, pattern in CLAIM_PATTERNS.items():
        values = [float(match.group(1)) for match in pattern.finditer(markdown)]
        if values:
            found[claim] = values
    return found


def validate_numeric_claims(
    markdown: str,
    processing_result: dict[str, Any],
    *,
    rel_tol: float = 1e-6,
    abs_tol: float = 1e-6,
) -> dict[str, Any]:
    """Validate supported numeric claims and flag review-only claims."""
    expected = expected_claims_from_result(processing_result)
    found = extract_numeric_claims(markdown)
    issues: list[dict[str, Any]] = []

    for claim, values in found.items():
        expected_value = expected.get(claim)
        if expected_value is None:
            issues.append({
                "claim": claim,
                "severity": "review",
                "reason": "claim_not_present_in_processing_result",
            })
            continue
        for value in values:
            if not math.isclose(value, expected_value, rel_tol=rel_tol, abs_tol=abs_tol):
                issues.append({
                    "claim": claim,
                    "severity": "error",
                    "reason": "numeric_mismatch",
                    "expected": expected_value,
                    "actual": value,
                })

    for match in UNSUPPORTED_CLAIM_PATTERN.finditer(markdown):
        issues.append({
            "claim": re.sub(r"\s+", "_", match.group(1).lower()),
            "severity": "review",
            "reason": "unsupported_claim_requires_review",
            "actual": float(match.group(2)),
        })

    return {
        "status": "passed" if not issues else "review_required",
        "expected_claims": expected,
        "found_claims": found,
        "issues": issues,
    }


def render_draft_from_processing_result(
    *,
    title: str,
    processing_result: dict[str, Any],
    validation: dict[str, Any] | None = None,
) -> str:
    """Render a conservative draft that mirrors persisted processing output."""
    lines = [
        f"# {title}",
        "",
        "## Source Result",
        "",
    ]
    claims = expected_claims_from_result(processing_result)
    if "ic50" in claims:
        lines.append(f"- IC50: {claims['ic50']}")
    if "r_squared" in claims:
        lines.append(f"- R-squared: {claims['r_squared']}")
    if "z_prime" in claims:
        lines.append(f"- Z-prime: {claims['z_prime']}")
    if not claims:
        lines.append("- No supported numeric claims were found in the processing result.")

    lines.extend(["", "## Validation", ""])
    status = (validation or {}).get("status", "not_run")
    lines.append(f"- Status: {status}")
    lines.extend(["", "## Conclusions", "", "To be completed by the investigator."])
    return "\n".join(lines)
