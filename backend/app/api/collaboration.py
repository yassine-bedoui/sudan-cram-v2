# app/api/collaboration.py

from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from app.agents.workflow import run_analysis
from app.models.collaboration import (
    FeedbackCreate,
    FeedbackRecord,
    LocalActorInputCreate,
    LocalActorInputRecord,
    ScenarioPreviewRequest,
    ScenarioPreviewResponse,
)
from app.services.collaboration_store import (
    append_feedback,
    append_local_input,
    get_feedback_for_region,
    get_feedback_for_run,
    get_local_input_for_region,
)

router = APIRouter(
    prefix="/api",
    tags=["collaboration"],
)


# ---- 1) Red-team / analyst feedback endpoints ----

@router.post(
    "/analysis/{run_id}/feedback",
    response_model=FeedbackRecord,
    summary="Submit analyst feedback / red-team correction for an analysis run.",
)
def submit_feedback(run_id: str, payload: FeedbackCreate) -> FeedbackRecord:
    if payload.run_id != run_id:
        raise HTTPException(
            status_code=400,
            detail="run_id in path and body do not match.",
        )

    record = FeedbackRecord(
        id=f"fb_{int(datetime.utcnow().timestamp() * 1000)}",
        created_at=datetime.utcnow().isoformat(),
        **payload.dict(),
    )

    append_feedback(record)
    return record


@router.get(
    "/analysis/{run_id}/feedback",
    response_model=List[FeedbackRecord],
    summary="List all feedback items attached to a specific run_id.",
)
def list_feedback_for_run(run_id: str) -> List[FeedbackRecord]:
    return get_feedback_for_run(run_id)


@router.get(
    "/regions/{region}/feedback",
    response_model=List[FeedbackRecord],
    summary="List feedback items for a region (across all runs).",
)
def list_feedback_for_region(region: str, limit: int = 100) -> List[FeedbackRecord]:
    return get_feedback_for_region(region=region, limit=limit)


# ---- 2) Local actor input & contestation ----

@router.post(
    "/regions/{region}/local-input",
    response_model=LocalActorInputRecord,
    summary="Submit local actor input / contestation for a region.",
)
def submit_local_actor_input(
    region: str,
    payload: LocalActorInputCreate,
) -> LocalActorInputRecord:
    # Ensure URL & body region are aligned (body wins if inconsistent)
    region_body = payload.region or region
    if region_body.lower() != region.lower():
        raise HTTPException(
            status_code=400,
            detail="Region in path and body do not match.",
        )

    record = LocalActorInputRecord(
        id=f"li_{int(datetime.utcnow().timestamp() * 1000)}",
        created_at=datetime.utcnow().isoformat(),
        **payload.dict(),
    )

    append_local_input(record)
    return record


@router.get(
    "/regions/{region}/local-input",
    response_model=List[LocalActorInputRecord],
    summary="List local actor inputs for a region.",
)
def list_local_actor_input(region: str, limit: int = 100) -> List[LocalActorInputRecord]:
    return get_local_input_for_region(region=region, limit=limit)


# ---- 3) Scenario exploration / sandbox ----

@router.post(
    "/scenarios/preview",
    response_model=ScenarioPreviewResponse,
    summary="Run a scenario preview with specific interventions (scenario dashboard / sandbox).",
)
def preview_scenarios(req: ScenarioPreviewRequest) -> ScenarioPreviewResponse:
    """
    This reuses the full multi-agent pipeline, but is intended for interactive
    'what if we try these interventions in this region?' exploration.

    Frontend can call this with different intervention sets and visualize
    the resulting scenarios + trend + decision prompts.
    """
    if not req.interventions:
        raise HTTPException(
            status_code=400,
            detail="At least one intervention is required for scenario preview.",
        )

    result = run_analysis(
        region=req.region,
        raw_data=req.raw_data,
        interventions=req.interventions,
    )

    explainability = result.get("explainability") or {}
    reasoning = explainability.get("reasoning") or {}
    decision_prompts = reasoning.get("decision_prompts") or []

    resp = ScenarioPreviewResponse(
        run_id=result.get("run_id"),
        region=result.get("region"),
        scenarios=result.get("scenarios"),
        trend_analysis=result.get("trend_analysis"),
        approval_status=result.get("approval_status"),
        confidence_score=float(result.get("confidence_score", 0.0)),
        decision_prompts=decision_prompts,
    )
    return resp
