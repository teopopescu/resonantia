"""Evaluation framework using RAGAS metrics for Resonantia Lab."""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EvalSample:
    """A single evaluation sample."""
    question: str
    answer: str
    contexts: list[str] = field(default_factory=list)
    ground_truth: str = ""


@dataclass
class EvalResult:
    """Results from running evaluations."""
    relevance: float | None = None
    faithfulness: float | None = None
    recall_at_10: float | None = None
    precision_at_10: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# ---- Golden evaluation dataset for lab informatics ----

EVAL_DATASET: list[EvalSample] = [
    EvalSample(
        question="Design a cherry-pick plate map from a 96-well source plate",
        answer="",
        contexts=["Plate mapping supports cherry-pick, serial dilution, replicate, and randomize modes for 96 and 384-well plates."],
        ground_truth="Create a cherry-pick plate map by selecting source wells and mapping them to destination wells. Supports 96-well and 384-well formats with worklist export for Echo, Hamilton, and Opentrons.",
    ),
    EvalSample(
        question="What is the IC50 for compound X based on this dose-response data?",
        answer="",
        contexts=["4-parameter logistic regression is used to fit dose-response curves. IC50 is the concentration at 50% response. The model estimates top, bottom, Hill slope, and EC50 parameters."],
        ground_truth="Fit a 4-parameter logistic (4PL) curve to the concentration-response data. The IC50 is the inflection point where 50% inhibition occurs. Report IC50, Hill slope, R-squared, and confidence intervals.",
    ),
    EvalSample(
        question="Normalize my plate reader data using Z-score method",
        answer="",
        contexts=["Plate normalization supports Z-score, percent-of-control, and robust-Z methods. Z-score uses mean and standard deviation of sample wells."],
        ground_truth="Z-score normalization: for each well, z = (value - mean) / std. Uses the mean and standard deviation of all sample wells (excluding controls). Positive controls and negative controls are used for quality metrics like Z-prime.",
    ),
    EvalSample(
        question="Show me microscopy images for well B3, DAPI channel, plate HCS-001",
        answer="",
        contexts=["Microscopy browser supports plate, well, channel (DAPI, GFP, mCherry, Brightfield, Phase), and FOV selection. Images can be viewed as individual channels or composite overlays."],
        ground_truth="Navigate to the microscopy browser, select plate HCS-001, click well B3 in the grid, and enable the DAPI channel checkbox. The viewer shows all FOVs for that well/channel combination with thumbnails.",
    ),
    EvalSample(
        question="Check if my Anti-EGFR antibody lot AB-2847 has expired",
        answer="",
        contexts=["Sample tracker stores reagent metadata including lot number, expiry date, storage temperature, and location. Expiry alerts flag items within 30 days of expiration."],
        ground_truth="Look up sample by lot number AB-2847 in the sample tracker. Check the expiry date field. If within 30 days, it will show an 'Expiring' status badge. If past the date, it shows 'Expired'.",
    ),
    EvalSample(
        question="Generate an Echo CSV worklist for my cherry-pick plate map",
        answer="",
        contexts=["Worklist generation supports Echo CSV, Hamilton GWL, and Opentrons Python formats. Echo CSV includes source plate barcode, source well, destination plate barcode, destination well, and transfer volume in nanoliters."],
        ground_truth="Generate an Echo CSV worklist with columns: Source Plate Barcode, Source Well, Destination Plate Barcode, Destination Well, Transfer Volume (nL). Default volume is 25 nL unless specified.",
    ),
    EvalSample(
        question="Calculate Z-prime factor for my assay",
        answer="",
        contexts=["Z-prime = 1 - (3 * (std_positive + std_negative) / abs(mean_positive - mean_negative)). Z' > 0.5 indicates an excellent assay."],
        ground_truth="Z-prime factor measures assay quality. Z' = 1 - 3(sigma+ + sigma-) / |mu+ - mu-|. Z' > 0.5 is excellent, 0 < Z' < 0.5 is marginal, Z' < 0 means overlap between controls.",
    ),
    EvalSample(
        question="Perform delta-delta Ct analysis for GFP expression",
        answer="",
        contexts=["qPCR analysis uses the delta-delta Ct method with a reference gene and calibrator sample. dCt = Ct_target - Ct_reference. ddCt = dCt_sample - dCt_calibrator. Fold change = 2^(-ddCt)."],
        ground_truth="Delta-delta Ct: 1) Calculate dCt for each sample (Ct_GFP - Ct_reference_gene). 2) Calculate ddCt (dCt_sample - dCt_control). 3) Fold change = 2^(-ddCt). Report fold changes with error bars from technical replicates.",
    ),
    EvalSample(
        question="What is the weather today?",
        answer="",
        contexts=[],
        ground_truth="BLOCKED: This question is outside Resonantia Lab's scope. Suggest lab-related tasks instead.",
    ),
    EvalSample(
        question="Write me a poem about science",
        answer="",
        contexts=[],
        ground_truth="BLOCKED: Creative writing is outside Resonantia Lab's scope. Suggest lab-related tasks instead.",
    ),
]


async def run_evaluations(samples: list[EvalSample] | None = None) -> EvalResult:
    """Run RAGAS evaluations on the provided samples.

    If no samples provided, uses the golden dataset.
    Falls back to manual scoring if RAGAS is unavailable.
    """
    eval_samples = samples or EVAL_DATASET

    try:
        from ragas.metrics import faithfulness, answer_relevancy
        from ragas import evaluate
        from datasets import Dataset

        # Build RAGAS dataset
        data = {
            "question": [s.question for s in eval_samples if s.answer],
            "answer": [s.answer for s in eval_samples if s.answer],
            "contexts": [s.contexts for s in eval_samples if s.answer],
            "ground_truth": [s.ground_truth for s in eval_samples if s.answer],
        }

        if not data["question"]:
            logger.info("No answered samples to evaluate")
            return EvalResult(metadata={"status": "no_samples"})

        dataset = Dataset.from_dict(data)

        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy],
        )

        return EvalResult(
            relevance=result.get("answer_relevancy"),
            faithfulness=result.get("faithfulness"),
            metadata={"ragas_result": dict(result)},
        )
    except ImportError:
        logger.warning("RAGAS not fully available, using manual scoring")
        return _manual_eval(eval_samples)
    except Exception as e:
        logger.warning("RAGAS evaluation failed: %s", e)
        return _manual_eval(eval_samples)


def _manual_eval(samples: list[EvalSample]) -> EvalResult:
    """Fallback manual evaluation when RAGAS is unavailable."""
    answered = [s for s in samples if s.answer]
    if not answered:
        return EvalResult(metadata={"status": "no_answers"})

    # Simple keyword overlap scoring
    relevance_scores = []
    faithfulness_scores = []

    for sample in answered:
        # Relevance: does the answer address the question's key terms?
        q_words = set(sample.question.lower().split())
        a_words = set(sample.answer.lower().split())
        overlap = len(q_words & a_words) / max(len(q_words), 1)
        relevance_scores.append(min(overlap * 3, 1.0))  # scale up

        # Faithfulness: does the answer use context terms?
        if sample.contexts:
            ctx_words = set(" ".join(sample.contexts).lower().split())
            ctx_overlap = len(ctx_words & a_words) / max(len(ctx_words), 1)
            faithfulness_scores.append(min(ctx_overlap * 3, 1.0))
        else:
            faithfulness_scores.append(0.0)

    return EvalResult(
        relevance=sum(relevance_scores) / len(relevance_scores) if relevance_scores else None,
        faithfulness=sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else None,
        metadata={"method": "manual_keyword_overlap", "sample_count": len(answered)},
    )
