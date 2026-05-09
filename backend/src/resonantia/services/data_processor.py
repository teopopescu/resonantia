"""Data-processing pipelines for screening and assay data."""

from __future__ import annotations

import io
import logging
import math
import uuid
from typing import Any

import matplotlib
matplotlib.use("Agg")  # non-interactive backend — must precede pyplot import
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import zscore

logger = logging.getLogger(__name__)


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
# Enhanced dose-response: CI, outliers, plot
# ---------------------------------------------------------------------------

def _compute_ic50_ci(
    x: np.ndarray,
    y: np.ndarray,
    popt: np.ndarray,
    pcov: np.ndarray,
) -> tuple[float, float]:
    """Compute 95 %% asymptotic confidence interval on EC50 (index 2).

    Uses the diagonal of the covariance matrix and assumes normality.
    """
    ec50 = float(popt[2])
    se_ec50 = float(np.sqrt(pcov[2, 2]))
    ci_lower = ec50 - 1.96 * se_ec50
    ci_upper = ec50 + 1.96 * se_ec50
    return max(ci_lower, 0.0), ci_upper


def _detect_outliers(
    x: np.ndarray,
    y: np.ndarray,
    popt: np.ndarray,
    threshold_sd: float = 3.0,
) -> list[dict[str, Any]]:
    """Flag points whose residuals exceed *threshold_sd* standard deviations."""
    fitted = _four_pl(x, *popt)
    residuals = y - fitted
    sd = float(np.std(residuals)) if len(residuals) > 1 else 1.0
    if sd < 1e-12:
        return []

    outliers: list[dict[str, Any]] = []
    for i in range(len(x)):
        if abs(residuals[i]) > threshold_sd * sd:
            outliers.append({
                "index": i,
                "concentration": float(x[i]),
                "response": float(y[i]),
                "residual": float(residuals[i]),
            })
    return outliers


def _generate_dose_response_plot(
    x: np.ndarray,
    y: np.ndarray,
    popt: np.ndarray,
    ic50: float,
    ic50_ci_lower: float,
    ic50_ci_upper: float,
    r_squared: float,
    hill_slope: float,
    outliers: list[dict[str, Any]],
) -> bytes:
    """Generate a publication-quality dose-response plot and return PNG bytes."""
    fig, ax = plt.subplots(figsize=(6, 4), dpi=150)

    bottom, top_val, ec50, hill = popt

    # Smooth curve
    x_positive = x[x > 0]
    if len(x_positive) == 0:
        x_positive = np.array([1e-3, 1e3])
    x_smooth = np.logspace(
        np.log10(x_positive.min() / 5),
        np.log10(x_positive.max() * 5),
        200,
    )
    y_smooth = _four_pl(x_smooth, *popt)

    # CI band around the curve (propagate EC50 uncertainty)
    y_ci_lower = _four_pl(x_smooth, bottom, top_val, ic50_ci_lower, hill)
    y_ci_upper = _four_pl(x_smooth, bottom, top_val, ic50_ci_upper, hill)
    # Make sure lower <= upper
    y_band_lo = np.minimum(y_ci_lower, y_ci_upper)
    y_band_hi = np.maximum(y_ci_lower, y_ci_upper)

    ax.fill_between(x_smooth, y_band_lo, y_band_hi, alpha=0.15, color="steelblue", label="95% CI")

    # Fitted curve
    ax.plot(x_smooth, y_smooth, color="crimson", linewidth=2, label="4PL fit")

    # Data points
    outlier_indices = {o["index"] for o in outliers}
    normal_mask = np.array([i not in outlier_indices for i in range(len(x))])
    outlier_mask = ~normal_mask

    ax.scatter(x[normal_mask], y[normal_mask], color="steelblue", s=40, zorder=5, label="Data")
    if np.any(outlier_mask):
        ax.scatter(x[outlier_mask], y[outlier_mask], color="red", s=50, marker="x", zorder=6, label="Outlier")

    # IC50 line
    ic50_response = _four_pl(np.array([ic50]), *popt)[0]
    ax.axvline(ic50, color="gray", linestyle="--", linewidth=1, alpha=0.7)
    ax.axhline(ic50_response, color="gray", linestyle=":", linewidth=0.8, alpha=0.5)
    ax.plot(ic50, ic50_response, "D", color="orange", markersize=8, zorder=7)

    # Annotation
    # Determine good units
    if ic50 < 1:
        ic50_str = f"{ic50 * 1000:.1f} pM"
    elif ic50 < 1000:
        ic50_str = f"{ic50:.1f} nM"
    else:
        ic50_str = f"{ic50 / 1000:.2f} µM"

    annotation = f"IC50 = {ic50_str}\nHill = {hill_slope:.2f}\nR² = {r_squared:.3f}"
    ax.annotate(
        annotation,
        xy=(0.97, 0.97),
        xycoords="axes fraction",
        ha="right", va="top",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="gray", alpha=0.85),
    )

    ax.set_xscale("log")
    ax.set_xlabel("Concentration (nM)", fontsize=11)
    ax.set_ylabel("Response (%)", fontsize=11)
    ax.set_title("Dose-Response Curve", fontsize=13, fontweight="bold")
    ax.legend(fontsize=8, loc="lower left")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


async def fit_dose_response_full(
    concentrations: list[float],
    responses: list[float],
    positive_controls: list[float] | None = None,
    negative_controls: list[float] | None = None,
    compound_name: str = "Compound",
) -> dict[str, Any]:
    """Enhanced 4PL fit with CI, outliers, plot, and Z-prime.

    Returns everything the tool handler needs to build a rich
    ``DoseResponseResult``.
    """
    x = np.asarray(concentrations, dtype=float)
    y = np.asarray(responses, dtype=float)

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
    except RuntimeError:
        return {"success": False, "error": "Curve fitting did not converge"}

    bottom, top_val, ec50, hill = popt
    fitted = _four_pl(x, *popt)
    ss_res = float(np.sum((y - fitted) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    ic50 = float(ec50)
    ic50_ci_lower, ic50_ci_upper = _compute_ic50_ci(x, y, popt, pcov)
    outliers = _detect_outliers(x, y, popt)

    # Z-prime (optional)
    z_prime = None
    if positive_controls and negative_controls:
        zp = calculate_z_prime(positive_controls, negative_controls)
        z_prime = zp.get("z_prime")

    # Count unique concentrations to estimate n_replicates
    unique_concs = len(set(concentrations))
    n_replicates = max(1, len(concentrations) // unique_concs) if unique_concs > 0 else 1

    # Generate plot
    plot_bytes = _generate_dose_response_plot(
        x, y, popt,
        ic50, ic50_ci_lower, ic50_ci_upper,
        r_squared, float(hill), outliers,
    )

    # Save plot via storage abstraction
    from resonantia.services.storage import get_storage

    storage = get_storage()
    plot_path = f"plots/dose_response_{uuid.uuid4().hex[:12]}.png"
    plot_url = await storage.save(plot_path, plot_bytes, "image/png")

    return {
        "success": True,
        "ic50": ic50,
        "ic50_ci_lower": ic50_ci_lower,
        "ic50_ci_upper": ic50_ci_upper,
        "hill_slope": float(hill),
        "top": float(top_val),
        "bottom": float(bottom),
        "r_squared": r_squared,
        "z_prime": z_prime,
        "n_points": len(x),
        "n_replicates": n_replicates,
        "outliers": outliers,
        "plot_url": plot_url,
        "fitted_values": fitted.tolist(),
        "parameters": {
            "bottom": float(bottom),
            "top": float(top_val),
            "ec50": ic50,
            "hill_slope": float(hill),
        },
        "standard_errors": {
            "bottom": float(np.sqrt(pcov[0, 0])),
            "top": float(np.sqrt(pcov[1, 1])),
            "ec50": float(np.sqrt(pcov[2, 2])),
            "hill_slope": float(np.sqrt(pcov[3, 3])),
        },
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
