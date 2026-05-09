"""Tests for enhanced dose-response fitting: CI, outliers, plot generation."""

from __future__ import annotations

import os
import tempfile

import numpy as np
import pytest

from resonantia.services.data_processor import (
    _compute_ic50_ci,
    _detect_outliers,
    _four_pl,
    _generate_dose_response_plot,
    fit_dose_response,
    fit_dose_response_full,
)


# ---------------------------------------------------------------------------
# Original fit_dose_response (backward compat)
# ---------------------------------------------------------------------------

class TestFitDoseResponseBackwardCompat:
    def test_successful_fit_returns_ic50(self):
        concentrations = [0.001, 0.01, 0.1, 1.0, 10.0, 100.0]
        responses = [95.0, 90.0, 70.0, 50.0, 15.0, 5.0]
        result = fit_dose_response(concentrations, responses)
        assert result["success"] is True
        assert "ec50" in result["parameters"]
        assert result["parameters"]["ec50"] > 0

    def test_fit_returns_standard_errors(self):
        concentrations = [0.01, 0.1, 1.0, 10.0, 100.0]
        responses = [100.0, 85.0, 50.0, 15.0, 5.0]
        result = fit_dose_response(concentrations, responses)
        assert result["success"] is True
        assert len(result["standard_errors"]) == 4


# ---------------------------------------------------------------------------
# Confidence intervals
# ---------------------------------------------------------------------------

class TestIC50CI:
    def test_ci_returns_two_bounds(self):
        x = np.array([0.01, 0.1, 1.0, 10.0, 100.0])
        y = np.array([100.0, 85.0, 50.0, 15.0, 5.0])
        from scipy.optimize import curve_fit
        popt, pcov = curve_fit(
            _four_pl, x, y, p0=[5.0, 100.0, 1.0, -1.0], maxfev=10_000
        )
        ci_lower, ci_upper = _compute_ic50_ci(x, y, popt, pcov)
        assert ci_lower < ci_upper
        assert ci_lower >= 0  # clamped at 0

    def test_ci_contains_point_estimate(self):
        x = np.array([0.01, 0.1, 1.0, 10.0, 100.0])
        y = np.array([100.0, 85.0, 50.0, 15.0, 5.0])
        from scipy.optimize import curve_fit
        popt, pcov = curve_fit(
            _four_pl, x, y, p0=[5.0, 100.0, 1.0, -1.0], maxfev=10_000
        )
        ci_lower, ci_upper = _compute_ic50_ci(x, y, popt, pcov)
        ec50 = float(popt[2])
        assert ci_lower <= ec50 <= ci_upper


# ---------------------------------------------------------------------------
# Outlier detection
# ---------------------------------------------------------------------------

class TestOutlierDetection:
    def test_no_outliers_on_clean_data(self):
        x = np.array([0.01, 0.1, 1.0, 10.0, 100.0])
        y = np.array([100.0, 85.0, 50.0, 15.0, 5.0])
        from scipy.optimize import curve_fit
        popt, _ = curve_fit(
            _four_pl, x, y, p0=[5.0, 100.0, 1.0, -1.0], maxfev=10_000
        )
        outliers = _detect_outliers(x, y, popt, threshold_sd=3.0)
        assert len(outliers) == 0

    def test_detects_obvious_outlier(self):
        x = np.array([0.01, 0.1, 1.0, 10.0, 100.0])
        y = np.array([100.0, 85.0, 50.0, 15.0, 5.0])
        from scipy.optimize import curve_fit
        popt, _ = curve_fit(
            _four_pl, x, y, p0=[5.0, 100.0, 1.0, -1.0], maxfev=10_000
        )
        # Inject a wildly wrong value
        y_with_outlier = y.copy()
        y_with_outlier[2] = 200.0  # should be ~50, make it 200
        outliers = _detect_outliers(x, y_with_outlier, popt, threshold_sd=2.0)
        assert len(outliers) >= 1
        assert any(o["index"] == 2 for o in outliers)


# ---------------------------------------------------------------------------
# Plot generation
# ---------------------------------------------------------------------------

class TestPlotGeneration:
    def test_plot_returns_png_bytes(self):
        x = np.array([0.01, 0.1, 1.0, 10.0, 100.0])
        y = np.array([100.0, 85.0, 50.0, 15.0, 5.0])
        popt = np.array([5.0, 100.0, 1.0, -1.0])
        png = _generate_dose_response_plot(
            x, y, popt,
            ic50=1.0, ic50_ci_lower=0.5, ic50_ci_upper=1.5,
            r_squared=0.99, hill_slope=-1.0, outliers=[],
        )
        assert isinstance(png, bytes)
        # PNG magic bytes
        assert png[:4] == b"\x89PNG"
        assert len(png) > 1000  # non-trivial image

    def test_plot_with_outliers_renders(self):
        x = np.array([0.01, 0.1, 1.0, 10.0, 100.0])
        y = np.array([100.0, 85.0, 200.0, 15.0, 5.0])
        popt = np.array([5.0, 100.0, 1.0, -1.0])
        outliers = [{"index": 2, "concentration": 1.0, "response": 200.0, "residual": 150.0}]
        png = _generate_dose_response_plot(
            x, y, popt,
            ic50=1.0, ic50_ci_lower=0.5, ic50_ci_upper=1.5,
            r_squared=0.80, hill_slope=-1.0, outliers=outliers,
        )
        assert png[:4] == b"\x89PNG"


# ---------------------------------------------------------------------------
# Full enhanced fit (async)
# ---------------------------------------------------------------------------

class TestFitDoseResponseFull:
    @pytest.fixture(autouse=True)
    def _patch_storage(self, tmp_path, monkeypatch):
        """Inject a LocalStorage pointed at tmp_path for every test."""
        from resonantia.services import storage as storage_mod
        instance = storage_mod.LocalStorage(base_dir=str(tmp_path))
        monkeypatch.setattr(storage_mod, "_storage_instance", instance)
        yield
        monkeypatch.setattr(storage_mod, "_storage_instance", None)

    @pytest.mark.asyncio
    async def test_full_fit_returns_all_fields(self):
        concentrations = [0.001, 0.01, 0.1, 1.0, 10.0, 100.0]
        responses = [95.0, 90.0, 70.0, 50.0, 15.0, 5.0]
        result = await fit_dose_response_full(concentrations, responses)

        assert result["success"] is True
        assert "ic50" in result
        assert "ic50_ci_lower" in result
        assert "ic50_ci_upper" in result
        assert result["ic50_ci_lower"] <= result["ic50"] <= result["ic50_ci_upper"]
        assert "hill_slope" in result
        assert "r_squared" in result
        assert "top" in result
        assert "bottom" in result
        assert "outliers" in result
        assert "plot_url" in result
        assert result["plot_url"].startswith("/api/v1/files/serve/")
        assert "n_points" in result
        assert result["n_points"] == 6
        assert "n_replicates" in result

    @pytest.mark.asyncio
    async def test_full_fit_with_z_prime(self):
        concentrations = [0.01, 0.1, 1.0, 10.0, 100.0]
        responses = [100.0, 85.0, 50.0, 15.0, 5.0]
        pos = [95.0, 97.0, 96.0, 94.0]
        neg = [5.0, 6.0, 4.0, 5.5]

        result = await fit_dose_response_full(
            concentrations, responses,
            positive_controls=pos,
            negative_controls=neg,
        )
        assert result["success"] is True
        assert result["z_prime"] is not None
        assert result["z_prime"] > 0.5  # excellent assay

    @pytest.mark.asyncio
    async def test_full_fit_plot_file_exists(self, tmp_path):
        concentrations = [0.01, 0.1, 1.0, 10.0, 100.0]
        responses = [100.0, 85.0, 50.0, 15.0, 5.0]
        result = await fit_dose_response_full(concentrations, responses)

        # Verify the plot file was written
        plot_url = result["plot_url"]
        rel_path = plot_url.replace("/api/v1/files/serve/", "")
        full_path = tmp_path / rel_path
        assert full_path.exists()
        assert full_path.read_bytes()[:4] == b"\x89PNG"
