"""Evaluation API endpoints for Resonantia Lab."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from resonantia.services.evals import EVAL_DATASET, EvalResult, EvalSample, run_evaluations

router = APIRouter()


class EvalSampleSchema(BaseModel):
    question: str
    answer: str = ""
    contexts: list[str] = []
    ground_truth: str = ""


class RunEvalsRequest(BaseModel):
    samples: list[EvalSampleSchema] | None = None


class EvalResultSchema(BaseModel):
    relevance: float | None = None
    faithfulness: float | None = None
    recall_at_10: float | None = None
    precision_at_10: float | None = None
    metadata: dict[str, Any] = {}


@router.get("/dataset", response_model=list[EvalSampleSchema])
async def get_eval_dataset() -> list[EvalSampleSchema]:
    """Return the golden evaluation dataset."""
    return [
        EvalSampleSchema(
            question=s.question,
            answer=s.answer,
            contexts=s.contexts,
            ground_truth=s.ground_truth,
        )
        for s in EVAL_DATASET
    ]


@router.post("/run", response_model=EvalResultSchema)
async def run_evals(body: RunEvalsRequest) -> EvalResultSchema:
    """Run evaluations on provided samples or the golden dataset."""
    samples = None
    if body.samples:
        samples = [
            EvalSample(
                question=s.question,
                answer=s.answer,
                contexts=s.contexts,
                ground_truth=s.ground_truth,
            )
            for s in body.samples
        ]

    result: EvalResult = await run_evaluations(samples)
    return EvalResultSchema(
        relevance=result.relevance,
        faithfulness=result.faithfulness,
        recall_at_10=result.recall_at_10,
        precision_at_10=result.precision_at_10,
        metadata=result.metadata,
    )
