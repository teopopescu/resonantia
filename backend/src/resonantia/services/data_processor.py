"""Data-processing pipelines for screening and assay data."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import zscore


# ---------------------------------------------------------------------------
# Dose-response (4-parameter logistic)
# ---------------------------------------------------------------------------

def _four_pl(x: np.ndarray, bottom: float, top: float, ec50: float, hill: float) -> np.ndarray:
    return bottom + (top - bottom) / (1.0 + (x / ec50) ** hill)


def fit_dose_response(
    concentrations: list[float],
    responses: list[float],
) -> dict[str, Any]:
    """Fit a 4-parameter logistic curve and return parameters + fitted values."""
    x = np.asarray(concentrations, dtype=float)
    y = np.asarray(responses, dtype=float)

    # Initial guesses
    bottom_guess = float(np.min(y))
    top_guess = float(np.max(y))
    ec50_guess = float(np.median(x[x > 0])) if np.any(x > 0) else 1.0
    hill_guess = -1.0

    try:
        popt, pcov = curve_fit(
            _four_pl,
            x,
            y,
            p0=[bottom_guess, top_guess, ec50_guess, hill_guess],
            maxfev=10_000,
        )
        bottom, top, ec50, hill = popt
        perr = np.sqrt(np.diag(pcov))
        fitted = _four_pl(x, *popt).tolist()
        r_squared = float(1.0 - np.sum((y - _four_pl(x, *popt)) ** 2) / np.sum((y - np.mean(y)) ** 2))
    except RuntimeError:
        return {
            "success": False,
            "error": "Curve fitting did not converge",
        }

    return {
        "success": True,
        "parameters": {
            "bottom": float(bottom),
            "top": float(top),
            "ec50": float(ec50),
            "hill_slope": float(hill),
        },
        "standard_errors": {
            "bottom": float(perr[0]),
            "top": float(perr[1]),
            "ec50": float(perr[2]),
            "hill_slope": float(perr[3]),
        },
        "r_squared": r_squared,
        "fitted_values": fitted,
    }


# ---------------------------------------------------------------------------
# Plate normalization
# ---------------------------------------------------------------------------

def normalize_plate(
    raw_data: list[list[float]],
    method: str = "z-score",
    positive_control_wells: list[tuple[int, int]] | None = None,
    negative_control_wells: list[tuple[int, int]] | None = None,
) -> dict[str, Any]:
    """Normalize a plate's raw readings.

    Supported methods: ``z-score``, ``percent-of-control``, ``robust-z``.
    """
    arr = np.asarray(raw_data, dtype=float)

    if method == "z-score":
        normed = zscore(arr, axis=None, nan_policy="omit")
        return {"method": method, "normalized": normed.tolist()}

    if method == "percent-of-control":
        if not positive_control_wells or not negative_control_wells:
            return {"error": "Control well positions required for percent-of-control"}
        pos_vals = [arr[r][c] for r, c in positive_control_wells]
        neg_vals = [arr[r][c] for r, c in negative_control_wells]
        pos_mean = float(np.mean(pos_vals))
        neg_mean = float(np.mean(neg_vals))
        denom = pos_mean - neg_mean
        if abs(denom) < 1e-12:
            return {"error": "Positive and negative controls are identical"}
        normed = ((arr - neg_mean) / denom * 100).tolist()
        return {"method": method, "normalized": normed}

    if method == "robust-z":
        median = float(np.nanmedian(arr))
        mad = float(np.nanmedian(np.abs(arr - median)))
        if mad < 1e-12:
            return {"error": "MAD is zero, cannot compute robust Z"}
        normed = ((arr - median) / (1.4826 * mad)).tolist()
        return {"method": method, "normalized": normed}

    return {"error": f"Unknown normalization method: {method}"}


# ---------------------------------------------------------------------------
# Z-prime
# ---------------------------------------------------------------------------

def calculate_z_prime(
    positive_controls: list[float],
    negative_controls: list[float],
) -> dict[str, Any]:
    """Compute Z' factor for assay quality."""
    pos = np.asarray(positive_controls, dtype=float)
    neg = np.asarray(negative_controls, dtype=float)
    z_prime = 1.0 - (3.0 * (np.std(pos) + np.std(neg)) / abs(np.mean(pos) - np.mean(neg)))
    return {
        "z_prime": float(z_prime),
        "positive_mean": float(np.mean(pos)),
        "positive_std": float(np.std(pos)),
        "negative_mean": float(np.mean(neg)),
        "negative_std": float(np.std(neg)),
        "quality": (
            "excellent" if z_prime >= 0.5
            else "acceptable" if z_prime >= 0.0
            else "poor"
        ),
    }
