"""Closed-loop Experiment Design Agent.

Analyzes previous experiment results and recommends the next experiment,
closing the design-execute-analyze loop described in the strategy doc.

Heuristics
----------
- Follow up hits (IC50 < 10 uM) with tighter 3-fold dilution series centred on IC50.
- Re-test compounds with R^2 < 0.9 or Hill slope > 2 (suspicious fit).
- Always include 2 positive and 2 negative control wells per plate.
- Flag compounds with IC50 near the highest or lowest tested concentration.
- Recommend 384-well format when > 20 compounds, otherwise 96-well.
"""

from __future__ import annotations

import json
import logging
import math
import uuid as _uuid
from dataclasses import dataclass, field, asdict
from typing import Any

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.db.session import async_session_factory
from resonantia.models.experiment import Experiment

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Thresholds (easily tuneable)
# ---------------------------------------------------------------------------

IC50_HIT_THRESHOLD_UM = 10.0
R_SQUARED_MIN = 0.9
HILL_SLOPE_MAX = 2.0
CONCENTRATION_EDGE_FACTOR = 3.0  # IC50 within 3x of min/max conc = out-of-range
CONTROLS_PER_TYPE = 2  # pos/neg control wells per plate
COMPOUND_THRESHOLD_384 = 20  # switch to 384-well above this count
DEFAULT_DILUTION_FOLD = 3.0
DEFAULT_DILUTION_POINTS = 8


# ---------------------------------------------------------------------------
# Data classes for structured recommendations
# ---------------------------------------------------------------------------

@dataclass
class CompoundRecommendation:
    compound_name: str
    reason: str
    suggested_top_concentration_um: float | None = None
    suggested_dilution_fold: float = DEFAULT_DILUTION_FOLD
    suggested_points: int = DEFAULT_DILUTION_POINTS


@dataclass
class ConcentrationAdjustment:
    compound_name: str
    original_ic50_um: float
    new_top_um: float
    new_bottom_um: float
    dilution_fold: float = DEFAULT_DILUTION_FOLD
    points: int = DEFAULT_DILUTION_POINTS


@dataclass
class ControlRecommendation:
    control_type: str  # "positive" or "negative"
    compound_name: str
    concentration_um: float | None = None
    wells_per_plate: int = CONTROLS_PER_TYPE


@dataclass
class ExperimentRecommendation:
    compounds_to_retest: list[CompoundRecommendation] = field(default_factory=list)
    concentration_adjustments: list[ConcentrationAdjustment] = field(default_factory=list)
    new_compounds: list[str] = field(default_factory=list)
    controls: list[ControlRecommendation] = field(default_factory=list)
    plate_format: int = 96  # 96 or 384
    reasoning: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisResult:
    experiment_name: str
    experiment_id: str
    overall_quality: str  # "good", "acceptable", "poor"
    z_prime: float | None = None
    z_prime_quality: str = "unknown"
    compounds_analyzed: int = 0
    hits: list[dict[str, Any]] = field(default_factory=list)
    poor_fits: list[dict[str, Any]] = field(default_factory=list)
    out_of_range: list[dict[str, Any]] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# ExperimentDesigner — the main service class
# ---------------------------------------------------------------------------

class ExperimentDesigner:
    """Analyze experiment results and design follow-up experiments."""

    # ------------------------------------------------------------------
    # analyze_results
    # ------------------------------------------------------------------

    async def analyze_results(
        self,
        org_id: str,
        experiment_id_or_query: str,
    ) -> AnalysisResult:
        """Fetch experiment results, assess quality, and identify gaps.

        Parameters
        ----------
        org_id : str
            Organisation scope for multi-tenant isolation.
        experiment_id_or_query : str
            UUID of an experiment, or a free-text query matched against
            experiment name / description / protocol.

        Returns
        -------
        AnalysisResult
            Structured analysis including quality metrics and gap list.
        """
        experiment = await self._fetch_experiment(org_id, experiment_id_or_query)
        if experiment is None:
            return AnalysisResult(
                experiment_name="(not found)",
                experiment_id=experiment_id_or_query,
                overall_quality="unknown",
                summary=f"No experiment found matching '{experiment_id_or_query}'.",
            )

        results: dict[str, Any] = experiment.results or {}
        analysis = AnalysisResult(
            experiment_name=experiment.name,
            experiment_id=str(experiment.id),
        )

        # --- Z-prime assessment ---
        z_prime = results.get("z_prime")
        if z_prime is not None:
            analysis.z_prime = float(z_prime)
            if z_prime >= 0.5:
                analysis.z_prime_quality = "excellent"
            elif z_prime >= 0.0:
                analysis.z_prime_quality = "acceptable"
            else:
                analysis.z_prime_quality = "poor"
                analysis.gaps.append(
                    f"Z-prime is {z_prime:.3f} (< 0), indicating the assay window is too narrow or controls are noisy."
                )

        # --- Per-compound analysis ---
        compounds = results.get("compounds", [])
        if not compounds and "ec50" in results:
            # Single-compound shorthand stored at top-level
            compounds = [
                {
                    "name": results.get("compound", experiment.name),
                    "ic50": results.get("ec50"),
                    "hill_slope": results.get("hill_slope"),
                    "r_squared": results.get("r_squared"),
                    "top_concentration": results.get("top_concentration"),
                    "bottom_concentration": results.get("bottom_concentration"),
                }
            ]

        analysis.compounds_analyzed = len(compounds)

        for cpd in compounds:
            name = cpd.get("name", "unknown")
            ic50 = cpd.get("ic50")
            r2 = cpd.get("r_squared")
            hill = cpd.get("hill_slope")
            top_conc = cpd.get("top_concentration")
            bottom_conc = cpd.get("bottom_concentration")

            # Hits
            if ic50 is not None and float(ic50) < IC50_HIT_THRESHOLD_UM:
                analysis.hits.append({"compound": name, "ic50_um": float(ic50)})

            # Poor fits
            if r2 is not None and float(r2) < R_SQUARED_MIN:
                analysis.poor_fits.append({
                    "compound": name,
                    "r_squared": float(r2),
                    "reason": f"R^2 = {float(r2):.3f} (< {R_SQUARED_MIN})",
                })
            if hill is not None and abs(float(hill)) > HILL_SLOPE_MAX:
                analysis.poor_fits.append({
                    "compound": name,
                    "hill_slope": float(hill),
                    "reason": f"|Hill slope| = {abs(float(hill)):.2f} (> {HILL_SLOPE_MAX})",
                })

            # Out of range
            if ic50 is not None and top_conc is not None:
                if float(ic50) > float(top_conc) / CONCENTRATION_EDGE_FACTOR:
                    analysis.out_of_range.append({
                        "compound": name,
                        "ic50_um": float(ic50),
                        "top_conc_um": float(top_conc),
                        "reason": "IC50 near top concentration — may be underestimated",
                    })
            if ic50 is not None and bottom_conc is not None:
                if float(ic50) < float(bottom_conc) * CONCENTRATION_EDGE_FACTOR:
                    analysis.out_of_range.append({
                        "compound": name,
                        "ic50_um": float(ic50),
                        "bottom_conc_um": float(bottom_conc),
                        "reason": "IC50 near bottom concentration — may be overestimated",
                    })

        # --- Gaps ---
        if not compounds:
            analysis.gaps.append("No per-compound dose-response data found in results.")
        if z_prime is None:
            analysis.gaps.append("No Z-prime value — assay quality cannot be assessed.")
        if analysis.poor_fits:
            analysis.gaps.append(
                f"{len(analysis.poor_fits)} compound(s) have suspicious curve fits and should be retested."
            )
        if analysis.out_of_range:
            analysis.gaps.append(
                f"{len(analysis.out_of_range)} compound(s) have IC50 near the edge of the tested range."
            )

        # --- Overall quality ---
        if analysis.z_prime_quality == "poor" or len(analysis.poor_fits) > len(compounds) * 0.5:
            analysis.overall_quality = "poor"
        elif analysis.z_prime_quality in ("excellent",) and not analysis.poor_fits:
            analysis.overall_quality = "good"
        else:
            analysis.overall_quality = "acceptable"

        # --- Summary ---
        parts = [
            f"Experiment '{experiment.name}': {analysis.compounds_analyzed} compound(s) analyzed.",
            f"Assay quality: {analysis.overall_quality} (Z' = {analysis.z_prime or 'N/A'}).",
            f"Hits (IC50 < {IC50_HIT_THRESHOLD_UM} uM): {len(analysis.hits)}.",
            f"Poor fits: {len(analysis.poor_fits)}.",
            f"Out-of-range: {len(analysis.out_of_range)}.",
        ]
        if analysis.gaps:
            parts.append("Gaps: " + "; ".join(analysis.gaps))
        analysis.summary = " ".join(parts)

        return analysis

    # ------------------------------------------------------------------
    # recommend_followup
    # ------------------------------------------------------------------

    async def recommend_followup(
        self,
        org_id: str,
        experiment_id_or_query: str,
    ) -> ExperimentRecommendation:
        """Recommend the next experiment based on prior results.

        Runs ``analyze_results`` internally, then applies heuristics to produce
        a structured recommendation including compounds, concentrations, controls
        and plate format.
        """
        analysis = await self.analyze_results(org_id, experiment_id_or_query)

        rec = ExperimentRecommendation()
        reasoning_parts: list[str] = []

        # --- Compounds to retest (poor fit / suspicious slope) ---
        retest_names: set[str] = set()
        for pf in analysis.poor_fits:
            name = pf["compound"]
            if name not in retest_names:
                retest_names.add(name)
                rec.compounds_to_retest.append(
                    CompoundRecommendation(
                        compound_name=name,
                        reason=pf["reason"],
                    )
                )
        if rec.compounds_to_retest:
            reasoning_parts.append(
                f"{len(rec.compounds_to_retest)} compound(s) need retesting due to poor curve fits."
            )

        # --- Out-of-range compounds also need retesting with adjusted range ---
        for oor in analysis.out_of_range:
            name = oor["compound"]
            if name not in retest_names:
                retest_names.add(name)
                rec.compounds_to_retest.append(
                    CompoundRecommendation(
                        compound_name=name,
                        reason=oor["reason"],
                        suggested_top_concentration_um=oor.get("ic50_um", 10.0) * 10,
                    )
                )

        # --- Concentration adjustments for hits ---
        for hit in analysis.hits:
            ic50 = hit["ic50_um"]
            # Centre a 3-fold dilution series around the IC50
            half_range_log = (DEFAULT_DILUTION_POINTS / 2) * math.log10(DEFAULT_DILUTION_FOLD)
            new_top = ic50 * (10 ** half_range_log)
            new_bottom = ic50 / (10 ** half_range_log)
            rec.concentration_adjustments.append(
                ConcentrationAdjustment(
                    compound_name=hit["compound"],
                    original_ic50_um=ic50,
                    new_top_um=round(new_top, 4),
                    new_bottom_um=round(new_bottom, 6),
                    dilution_fold=DEFAULT_DILUTION_FOLD,
                    points=DEFAULT_DILUTION_POINTS,
                )
            )
        if rec.concentration_adjustments:
            reasoning_parts.append(
                f"{len(rec.concentration_adjustments)} hit(s) get tighter {DEFAULT_DILUTION_FOLD}-fold dilution series centred on IC50."
            )

        # --- Controls ---
        rec.controls = [
            ControlRecommendation(
                control_type="positive",
                compound_name="Staurosporine (positive control)",
                concentration_um=1.0,
                wells_per_plate=CONTROLS_PER_TYPE,
            ),
            ControlRecommendation(
                control_type="positive",
                compound_name="Doxorubicin (positive control)",
                concentration_um=0.5,
                wells_per_plate=CONTROLS_PER_TYPE,
            ),
            ControlRecommendation(
                control_type="negative",
                compound_name="DMSO (vehicle control)",
                concentration_um=0.0,
                wells_per_plate=CONTROLS_PER_TYPE,
            ),
            ControlRecommendation(
                control_type="negative",
                compound_name="Untreated (negative control)",
                concentration_um=0.0,
                wells_per_plate=CONTROLS_PER_TYPE,
            ),
        ]

        # --- Plate format ---
        total_compounds = (
            len(rec.compounds_to_retest)
            + len(rec.concentration_adjustments)
            + len(rec.new_compounds)
        )
        rec.plate_format = 384 if total_compounds > COMPOUND_THRESHOLD_384 else 96
        reasoning_parts.append(
            f"Plate format: {rec.plate_format}-well ({total_compounds} compound(s) to test)."
        )

        # --- Overall quality note ---
        if analysis.overall_quality == "poor":
            reasoning_parts.insert(
                0,
                "WARNING: Previous experiment had poor assay quality. "
                "Consider optimising assay conditions before running follow-up.",
            )

        rec.reasoning = " ".join(reasoning_parts) if reasoning_parts else "No follow-up needed — all results look clean."

        return rec

    # ------------------------------------------------------------------
    # generate_followup_plate
    # ------------------------------------------------------------------

    async def generate_followup_plate(
        self,
        org_id: str,
        recommendation: ExperimentRecommendation | dict[str, Any],
    ) -> dict[str, Any]:
        """Turn a recommendation into a concrete plate map and worklist.

        Uses the existing ``create_plate_map`` and ``serial_dilution`` tool
        handlers from the tool executor so we stay consistent with the rest of
        the platform.

        Returns
        -------
        dict
            Contains ``plate_map``, ``worklist``, and ``dilution_series``.
        """
        from resonantia.services.tool_executor import execute_tool

        if isinstance(recommendation, dict):
            rec = recommendation
        else:
            rec = recommendation.to_dict()

        plate_format = rec.get("plate_format", 96)

        # Build compound list with concentrations
        compounds: list[dict[str, Any]] = []

        for adj in rec.get("concentration_adjustments", []):
            compounds.append({
                "name": adj["compound_name"] if isinstance(adj, dict) else adj.compound_name,
                "top_concentration": adj["new_top_um"] if isinstance(adj, dict) else adj.new_top_um,
                "dilution_fold": adj["dilution_fold"] if isinstance(adj, dict) else adj.dilution_fold,
                "points": adj["points"] if isinstance(adj, dict) else adj.points,
            })

        for retest in rec.get("compounds_to_retest", []):
            name = retest["compound_name"] if isinstance(retest, dict) else retest.compound_name
            # Skip if already in concentration_adjustments
            if any(c["name"] == name for c in compounds):
                continue
            top_conc = (retest.get("suggested_top_concentration_um") if isinstance(retest, dict)
                        else retest.suggested_top_concentration_um) or 100.0
            compounds.append({
                "name": name,
                "top_concentration": top_conc,
                "dilution_fold": DEFAULT_DILUTION_FOLD,
                "points": DEFAULT_DILUTION_POINTS,
            })

        # Generate serial dilution series for each compound
        dilution_results = []
        for cpd in compounds:
            dilution_raw = await execute_tool(
                "serial_dilution",
                {
                    "top_concentration": cpd["top_concentration"],
                    "dilution_factor": cpd["dilution_fold"],
                    "num_dilutions": cpd["points"],
                    "compound_name": cpd["name"],
                },
                org_id,
            )
            dilution_results.append({
                "compound": cpd["name"],
                "dilution": json.loads(dilution_raw) if isinstance(dilution_raw, str) else dilution_raw,
            })

        # Build well mappings
        well_mappings = self._layout_wells(compounds, rec.get("controls", []), plate_format)

        # Create the plate map via the existing tool
        plate_map_raw = await execute_tool(
            "create_plate_map",
            {
                "name": f"Follow-up — {len(compounds)} compounds ({plate_format}-well)",
                "plate_type": str(plate_format),
                "description": rec.get("reasoning", "Auto-generated follow-up plate"),
                "well_mappings": well_mappings,
            },
            org_id,
        )
        plate_map = json.loads(plate_map_raw) if isinstance(plate_map_raw, str) else plate_map_raw

        # Build worklist (transfer instructions)
        worklist = self._build_worklist(well_mappings, compounds)

        return {
            "plate_map": plate_map,
            "worklist": worklist,
            "dilution_series": dilution_results,
            "compounds_count": len(compounds),
            "plate_format": plate_format,
            "controls_count": sum(
                (c["wells_per_plate"] if isinstance(c, dict) else c.wells_per_plate)
                for c in rec.get("controls", [])
            ),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _fetch_experiment(self, org_id: str, id_or_query: str) -> Experiment | None:
        """Look up an experiment by UUID or free-text search."""
        async with async_session_factory() as session:
            # Try UUID first
            try:
                exp_uuid = _uuid.UUID(id_or_query)
                exp = await session.get(Experiment, exp_uuid)
                if exp and exp.org_id == org_id:
                    return exp
            except (ValueError, AttributeError):
                pass

            # Fall back to text search
            stmt = (
                select(Experiment)
                .where(
                    Experiment.org_id == org_id,
                    or_(
                        Experiment.name.ilike(f"%{id_or_query}%"),
                        Experiment.description.ilike(f"%{id_or_query}%"),
                    ),
                )
                .order_by(Experiment.created_at.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    def _layout_wells(
        compounds: list[dict[str, Any]],
        controls: list[dict | ControlRecommendation],
        plate_format: int,
    ) -> list[dict[str, Any]]:
        """Assign compounds and controls to wells in row-major order.

        Returns a list of well mapping dicts suitable for ``create_plate_map``.
        """
        rows = "ABCDEFGHIJKLMNOP" if plate_format == 384 else "ABCDEFGH"
        cols = range(1, 25) if plate_format == 384 else range(1, 13)
        all_wells = [f"{r}{c}" for r in rows for c in cols]
        idx = 0
        mappings: list[dict[str, Any]] = []

        # Controls first (edges of plate)
        for ctrl in controls:
            ctrl_d = ctrl if isinstance(ctrl, dict) else asdict(ctrl)
            n_wells = ctrl_d.get("wells_per_plate", CONTROLS_PER_TYPE)
            for _ in range(n_wells):
                if idx >= len(all_wells):
                    break
                mappings.append({
                    "well": all_wells[idx],
                    "compound": ctrl_d.get("compound_name", "control"),
                    "concentration_um": ctrl_d.get("concentration_um", 0.0),
                    "type": ctrl_d.get("control_type", "control"),
                })
                idx += 1

        # Compounds — one row per dilution series
        for cpd in compounds:
            points = cpd.get("points", DEFAULT_DILUTION_POINTS)
            top = cpd.get("top_concentration", 100.0)
            fold = cpd.get("dilution_fold", DEFAULT_DILUTION_FOLD)
            for pt in range(points):
                if idx >= len(all_wells):
                    break
                conc = top / (fold ** pt)
                mappings.append({
                    "well": all_wells[idx],
                    "compound": cpd["name"],
                    "concentration_um": round(conc, 6),
                    "type": "sample",
                })
                idx += 1

        return mappings

    @staticmethod
    def _build_worklist(
        well_mappings: list[dict[str, Any]],
        compounds: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Generate a liquid-handler worklist from well mappings."""
        worklist: list[dict[str, Any]] = []
        for wm in well_mappings:
            volume_ul = 0.1 if wm.get("type") == "sample" else 10.0  # nanolitre dispensing for compounds
            worklist.append({
                "source_plate": "compound_stock",
                "source_well": "A1",  # placeholder — real mapping depends on stock layout
                "destination_well": wm["well"],
                "compound": wm.get("compound", ""),
                "concentration_um": wm.get("concentration_um", 0.0),
                "volume_ul": volume_ul,
                "type": wm.get("type", "sample"),
            })
        return worklist


# ---------------------------------------------------------------------------
# Tool handler for registration in TOOL_HANDLERS
# ---------------------------------------------------------------------------

_designer = ExperimentDesigner()


async def _design_next_experiment(params: dict, org_id: str = "org_default") -> dict:
    """Agentic tool: analyze a prior experiment and design the follow-up.

    Parameters (in ``params``):
        experiment_id : str — UUID or name/query of the source experiment.
        generate_plate : bool — if True, also create the plate map (default False).

    Returns a dict with ``analysis``, ``recommendation``, and optionally ``plate``.
    """
    experiment_id = params.get("experiment_id", "") or params.get("query", "")
    generate_plate = params.get("generate_plate", False)

    if not experiment_id:
        return {"error": "Provide 'experiment_id' (UUID or experiment name) to design from."}

    analysis = await _designer.analyze_results(org_id, experiment_id)
    recommendation = await _designer.recommend_followup(org_id, experiment_id)

    result: dict[str, Any] = {
        "analysis": analysis.to_dict(),
        "recommendation": recommendation.to_dict(),
    }

    if generate_plate:
        plate = await _designer.generate_followup_plate(org_id, recommendation)
        result["plate"] = plate

    return result


def get_design_tool_handler():
    """Return the handler suitable for TOOL_HANDLERS registration."""
    return _design_next_experiment
