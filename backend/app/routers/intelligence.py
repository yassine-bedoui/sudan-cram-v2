from datetime import datetime
from typing import Any, Dict, List, Optional

import json
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.workflow import run_analysis
from app.models.analysis import AnalysisRun
from database import get_db  # NOTE: keep this (not app.database) for local/Render compatibility


router = APIRouter(
    prefix="/api/intelligence",
    tags=["intelligence"],
)


# --------- Pydantic models ---------


class IntelligenceRequest(BaseModel):
    region: str
    raw_data: Optional[str] = None
    interventions: List[str] = Field(default_factory=list)


class IntelligenceResponse(BaseModel):
    run_id: Optional[int]
    region: str
    timestamp: datetime
    events: List[Dict[str, Any]] = Field(default_factory=list)
    trends: Optional[Dict[str, Any]] = None
    scenarios: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None
    approval_status: Optional[str] = None
    confidence: float
    messages: List[str]
    explainability: Optional[Dict[str, Any]] = None


class AnalysisRunSummary(BaseModel):
    id: int
    region: str
    created_at: datetime
    trend_classification: Optional[str]
    overall_confidence: Optional[float]
    recommendation_summary: Optional[str]


# --------- Endpoints ---------


@router.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "healthy", "service": "intelligence"}


@router.post("/analyze", response_model=IntelligenceResponse)
def analyze(
    payload: IntelligenceRequest,
    db: Session = Depends(get_db),
) -> IntelligenceResponse:
    """
    Run the LangGraph pipeline and log a summary row into analysis_runs.
    """

    result = run_analysis(
        region=payload.region,
        raw_data=payload.raw_data,
        interventions=payload.interventions,
    )

    # --- Unpack pieces from the pipeline result ---
    events = result.get("events") or []  # 👈 IMPORTANT FIX: expose the timeline
    trends = result.get("trend_analysis") or {}
    scenarios = result.get("scenarios") or {}
    validation = result.get("validation") or {}
    explainability = result.get("explainability") or {}

    has_raw_data = bool(result.get("raw_data"))
    interventions_json = json.dumps(result.get("interventions") or [])

    trend_classification = trends.get("trend_classification")
    trend_confidence_label = trends.get("confidence")

    forecast = trends.get("forecast_7_days") or {}
    forecast_armed_clash = forecast.get("armed_clash_likelihood")
    forecast_civilian_targeting = forecast.get("civilian_targeting_likelihood")

    scenarios_list = scenarios.get("scenarios") or []
    recommendation_summary: Optional[str] = None
    max_success_probability: Optional[int] = None
    max_risk_probability: Optional[int] = None

    if scenarios_list:
        # Take the first recommendation as the summary for now
        recommendation_summary = scenarios_list[0].get("recommendation")
        for s in scenarios_list:
            optim = (s or {}).get("optimistic") or {}
            pess = (s or {}).get("pessimistic") or {}
            sp = optim.get("success_probability")
            rp = pess.get("risk_probability")
            if sp is not None:
                max_success_probability = (
                    sp
                    if max_success_probability is None
                    else max(max_success_probability, sp)
                )
            if rp is not None:
                max_risk_probability = (
                    rp
                    if max_risk_probability is None
                    else max(max_risk_probability, rp)
                )

    validation_status = validation.get("validation_status")
    issues = validation.get("issues") or []
    issue_count = len(issues)

    overall_confidence = validation.get(
        "overall_confidence", result.get("confidence_score", 0.0)
    )
    overall_confidence = float(overall_confidence or 0.0)

    explainability_json = json.dumps(explainability, ensure_ascii=False)

    # --- Persist to analysis_runs ---
    db_run = AnalysisRun(
        region=result["region"],
        has_raw_data=has_raw_data,
        interventions=interventions_json,
        trend_classification=trend_classification,
        trend_confidence_label=trend_confidence_label,
        forecast_armed_clash=forecast_armed_clash,
        forecast_civilian_targeting=forecast_civilian_targeting,
        recommendation_summary=recommendation_summary,
        max_success_probability=max_success_probability,
        max_risk_probability=max_risk_probability,
        validation_status=validation_status,
        issue_count=issue_count,
        overall_confidence=overall_confidence,
        explainability=explainability_json,
    )
    db.add(db_run)
    db.commit()
    db.refresh(db_run)

    # --- Build API response ---
    ts_str = result.get("timestamp")
    try:
        ts = datetime.fromisoformat(ts_str) if ts_str else db_run.created_at
    except Exception:
        ts = db_run.created_at

    return IntelligenceResponse(
        run_id=db_run.id,
        region=result["region"],
        timestamp=ts,
        events=events,  # 👈 now the frontend gets the actual timeline
        trends=trends,
        scenarios=scenarios,
        validation=validation,
        approval_status=result.get("approval_status"),
        confidence=result.get("confidence_score", overall_confidence),
        messages=result.get("messages") or [],
        explainability=explainability,
    )


@router.get("/runs", response_model=List[AnalysisRunSummary])
def list_runs(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> List[AnalysisRunSummary]:
    """
    Lightweight history endpoint for the last N analysis runs.
    """

    rows = (
        db.query(AnalysisRun)
        .order_by(AnalysisRun.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        AnalysisRunSummary(
            id=row.id,
            region=row.region,
            created_at=row.created_at,
            trend_classification=row.trend_classification,
            overall_confidence=row.overall_confidence,
            recommendation_summary=row.recommendation_summary,
        )
        for row in rows
    ]
