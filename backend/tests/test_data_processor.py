"""Unit tests for resonantia.services.data_processor."""

from __future__ import annotations

import numpy as np
import pytest

from resonantia.services.data_processor import (
    calculate_z_prime,
    fit_dose_response,
    normalize_plate,
)


# ---------------------------------------------------------------------------
# Dose-response curve fitting (4PL)
# ---------------------------------------------------------------------------

class TestFitDoseResponse:
    def test_successful_fit_returns_ic50(self):
        # Sigmoidal data: high at low conc, low at high conc
        concentrations = [0.001, 0.01, 0.1, 1.0, 10.0, 100.0]
        responses = [95.0, 90.0, 70.0, 50.0, 15.0, 5.0]
        result = fit_dose_response(concentrations, responses)
        assert result["success"] is True
        assert "ec50" in result["parameters"]
        assert result["parameters"]["ec50"] > 0
        assert "r_squared" in result

    def test_fit_returns_all_four_parameters(self):
        concentrations = [0.01, 0.1, 1.0, 10.0, 100.0]
        responses = [100.0, 85.0, 50.0, 15.0, 5.0]
        result = fit_dose_response(concentrations, responses)
        assert result["success"] is True
        params = result["parameters"]
        assert "bottom" in params
        assert "top" in params
        assert "ec50" in params
        assert "hill_slope" in params

    def test_fit_returns_standard_errors(self):
        concentrations = [0.01, 0.1, 1.0, 10.0, 100.0]
        responses = [100.0, 85.0, 50.0, 15.0, 5.0]
        result = fit_dose_response(concentrations, responses)
        assert result["success"] is True
        assert "standard_errors" in result
        assert len(result["standard_errors"]) == 4

    def test_fit_returns_fitted_values(self):
        concentrations = [0.01, 0.1, 1.0, 10.0, 100.0]
        responses = [100.0, 85.0, 50.0, 15.0, 5.0]
        result = fit_dose_response(concentrations, responses)
        assert result["success"] is True
        assert len(result["fitted_values"]) == len(concentrations)


# ---------------------------------------------------------------------------
# Plate normalisation — z-score
# ---------------------------------------------------------------------------

class TestNormalizePlateZScore:
    def test_zscore_returns_normalised_data(self):
        raw = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        result = normalize_plate(raw, method="z-score")
        assert result["method"] == "z-score"
        normed = np.array(result["normalized"])
        # z-score should have mean ~ 0 and std ~ 1
        assert abs(np.nanmean(normed)) < 1e-6
        assert abs(np.nanstd(normed) - 1.0) < 0.1

    def test_zscore_shape_preserved(self):
        raw = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        result = normalize_plate(raw, method="z-score")
        normed = result["normalized"]
        assert len(normed) == 3
        assert len(normed[0]) == 2


# ---------------------------------------------------------------------------
# Plate normalisation — percent-of-control
# ---------------------------------------------------------------------------

class TestNormalizePlatePOC:
    def test_poc_returns_percentage(self):
        raw = [[10.0, 50.0], [90.0, 100.0]]
        result = normalize_plate(
            raw,
            method="percent-of-control",
            positive_control_wells=[(1, 1)],  # value 100
            negative_control_wells=[(0, 0)],  # value 10
        )
        assert result["method"] == "percent-of-control"
        normed = np.array(result["normalized"])
        # negative control should be ~0%, positive should be ~100%
        assert abs(normed[0][0] - 0.0) < 1e-6
        assert abs(normed[1][1] - 100.0) < 1e-6

    def test_poc_requires_controls(self):
        raw = [[1.0, 2.0]]
        result = normalize_plate(raw, method="percent-of-control")
        assert "error" in result


# ---------------------------------------------------------------------------
# Z-prime factor
# ---------------------------------------------------------------------------

class TestCalculateZPrime:
    def test_z_prime_good_assay(self):
        """Good separation between controls gives Z' > 0.5."""
        pos = [90.0, 92.0, 91.0, 89.0, 93.0, 90.0, 91.0, 92.0]
        neg = [10.0, 12.0, 11.0, 9.0, 13.0, 10.0, 11.0, 12.0]
        result = calculate_z_prime(pos, neg)
        assert result["z_prime"] > 0.5
        assert result["quality"] == "excellent"

    def test_z_prime_bad_assay(self):
        """Overlapping controls give Z' < 0."""
        pos = [50.0, 55.0, 45.0, 60.0, 40.0, 52.0, 48.0, 58.0]
        neg = [48.0, 53.0, 47.0, 58.0, 42.0, 50.0, 46.0, 56.0]
        result = calculate_z_prime(pos, neg)
        assert result["z_prime"] < 0
        assert result["quality"] == "poor"

    def test_z_prime_returns_statistics(self):
        pos = [100.0, 100.0]
        neg = [0.0, 0.0]
        result = calculate_z_prime(pos, neg)
        assert "positive_mean" in result
        assert "positive_std" in result
        assert "negative_mean" in result
        assert "negative_std" in result
        assert "quality" in result
