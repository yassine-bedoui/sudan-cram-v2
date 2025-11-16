# app/routers/intelligence.py

from datetime import datetime
import json
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from app.agents.workflow import run_analysis
from app.models.analysis import AnalysisRun

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _dedupe_messages(messages: List[str]) -> List[str]:
    """
    Remove duplicate log lines while preserving order.
    If the same message appears many times, we keep only the first.
    """
    seen = set()
    cleaned: List[str] = []
    for m in messages:
        if m not in seen:
            cleaned.append(m)
            seen.add(m)
    return cleaned


def _derive_approval_status_from_confidence(conf: float) -> str:
    """
    Lightweight heuristic to mirror the LangGraph human_approval_node logic
    for history records that don't store approval status explicitly.
    """
    if conf < 0.7:
        return "pending"
    return "auto-approved"


# ---------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------


class IntelligenceRequest(BaseModel):
    region: str
    raw_data: Optional[str] = None
    interventions: Optional[List[str]] = None


class FeedbackPayload(BaseModel):
    approved: Optional[bool] = None
    feedback: Optional[str] = None


class AnalysisRunSummary(BaseModel):
    id: int
    region: str
    has_raw_data: bool
    interventions: List[str]
    trend_classification: Optional[str] = None
    trend_confidence_label: Optional[str] = None
    forecast_armed_clash: Optional[int] = None
    forecast_civilian_targeting: Optional[int] = None
    recommendation_summary: Optional[str] = None
    max_success_probability: Optional[int] = None
    max_risk_probability: Optional[int] = None
    validation_status: Optional[str] = None
    issue_count: int
    overall_confidence: float
    approval_status: Optional[str] = None
    human_feedback: Optional[str] = None
    explainability: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        orm_mode = True


# ---------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------


@router.get("/health")
def health() -> Dict[str, str]:
    return {"status": "healthy", "service": "intelligence"}


@router.post("/analyze")
def analyze(payload: IntelligenceRequest, db: Session = Depends(get_db)):
    """
    Run the LangGraph pipeline, log a compact summary to analysis_runs,
    and return the full structured result to the caller.
    """
    # 1) Run workflow
    result = run_analysis(
        region=payload.region,
        raw_data=payload.raw_data,
        interventions=payload.interventions,
    )

    # 2) Clean up repeated log messages
    raw_messages = result.get("messages") or []
    messages = _dedupe_messages(raw_messages)
    result["messages"] = messages  # keep in sync

    # 3) Extract parts we care about
    trends: Dict[str, Any] = result.get("trend_analysis") or {}
    scenarios: Dict[str, Any] = result.get("scenarios") or {}
    validation: Dict[str, Any] = result.get("validation") or {}
    explainability: Dict[str, Any] = result.get("explainability") or {}
    confidence = float(result.get("confidence_score", 0.0))

    forecast = trends.get("forecast_7_days") or {}
    validation_status = validation.get("validation_status")
    issues = validation.get("issues") or []
    issue_count = len(issues)

    # Scenario roll-up
    recommendation_summary = None
    max_success_probability = None
    max_risk_probability = None
    scenario_list = scenarios.get("scenarios") or []
    if scenario_list:
        recommendation_summary = scenario_list[0].get("recommendation")
        max_success_probability = max(
            (s.get("optimistic", {}).get("success_probability") or 0)
            for s in scenario_list
        )
        max_risk_probability = max(
            (s.get("pessimistic", {}).get("risk_probability") or 0)
            for s in scenario_list
        )

    # 4) Persist a lightweight log row
    run = AnalysisRun(
        region=result["region"],
        has_raw_data=bool(result.get("raw_data")),
        interventions=json.dumps(result.get("interventions") or []),
        trend_classification=trends.get("trend_classification"),
        trend_confidence_label=trends.get("confidence"),
        forecast_armed_clash=forecast.get("armed_clash_likelihood"),
        forecast_civilian_targeting=forecast.get("civilian_targeting_likelihood"),
        recommendation_summary=recommendation_summary,
        max_success_probability=max_success_probability,
        max_risk_probability=max_risk_probability,
        validation_status=validation_status,
        issue_count=issue_count,
        overall_confidence=float(validation.get("overall_confidence", confidence)),
        explainability=explainability,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # 5) Return full analysis payload (plus run_id) to caller
    return {
        "run_id": run.id,
        "region": result["region"],
        "timestamp": result["timestamp"],
        "events": result.get("extracted_events"),
        "trends": trends,
        "scenarios": scenarios,
        "validation": validation,
        "approval_status": result.get("approval_status"),
        "confidence": confidence,
        "messages": messages,
        "explainability": explainability,
    }


@router.get("/runs", response_model=List[AnalysisRunSummary])
def list_runs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Lightweight history endpoint so the frontend can show recent analyses.
    """
    runs = (
        db.query(AnalysisRun)
        .order_by(AnalysisRun.created_at.desc())
        .limit(limit)
        .all()
    )

    summaries: List[AnalysisRunSummary] = []
    for r in runs:
        try:
            interventions = json.loads(r.interventions) if r.interventions else []
        except Exception:
            interventions = []

        # Derive approval-ish label from confidence if nothing else is stored
        approval_status = _derive_approval_status_from_confidence(
            float(r.overall_confidence or 0.0)
        )

        # Optional human feedback/note stored inside explainability.meta (if any)
        expl = r.explainability or {}
        meta = expl.get("meta") or {}
        human_feedback = meta.get("human_feedback")

        summaries.append(
            AnalysisRunSummary(
                id=r.id,
                region=r.region,
                has_raw_data=r.has_raw_data,
                interventions=interventions,
                trend_classification=r.trend_classification,
                trend_confidence_label=r.trend_confidence_label,
                forecast_armed_clash=r.forecast_armed_clash,
                forecast_civilian_targeting=r.forecast_civilian_targeting,
                recommendation_summary=r.recommendation_summary,
                max_success_probability=r.max_success_probability,
                max_risk_probability=r.max_risk_probability,
                validation_status=r.validation_status,
                issue_count=r.issue_count,
                overall_confidence=r.overall_confidence,
                approval_status=approval_status,
                human_feedback=human_feedback,
                explainability=expl,
                created_at=r.created_at,
            )
        )

    return summaries


@router.get("/runs/{run_id}", response_model=AnalysisRunSummary)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(AnalysisRun).get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    try:
        interventions = json.loads(run.interventions) if run.interventions else []
    except Exception:
        interventions = []

    expl = run.explainability or {}
    meta = expl.get("meta") or {}
    human_feedback = meta.get("human_feedback")

    approval_status = _derive_approval_status_from_confidence(
        float(run.overall_confidence or 0.0)
    )

    return AnalysisRunSummary(
        id=run.id,
        region=run.region,
        has_raw_data=run.has_raw_data,
        interventions=interventions,
        trend_classification=run.trend_classification,
        trend_confidence_label=run.trend_confidence_label,
        forecast_armed_clash=run.forecast_armed_clash,
        forecast_civilian_targeting=run.forecast_civilian_targeting,
        recommendation_summary=run.recommendation_summary,
        max_success_probability=run.max_success_probability,
        max_risk_probability=run.max_risk_probability,
        validation_status=run.validation_status,
        issue_count=run.issue_count,
        overall_confidence=run.overall_confidence,
        approval_status=approval_status,
        human_feedback=human_feedback,
        explainability=expl,
        created_at=run.created_at,
    )


@router.post("/runs/{run_id}/feedback")
def submit_feedback(
    run_id: int,
    payload: FeedbackPayload,
    db: Session = Depends(get_db),
):
    """
    Simple feedback / approval endpoint.

    To avoid changing the DB schema, we tuck human feedback and approval
    into the explainability.meta section of the analysis_runs row.
    """
    run = db.query(AnalysisRun).get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    expl = run.explainability or {}
    meta = expl.get("meta") or {}

    if payload.approved is not None:
        meta["human_approved"] = bool(payload.approved)

    if payload.feedback:
        meta["human_feedback"] = payload.feedback

    expl["meta"] = meta
    run.explainability = expl

    db.add(run)
    db.commit()
    db.refresh(run)

    # Mirror the label we might show in the UI
    approval_status = None
    if payload.approved is True:
        approval_status = "approved"
    elif payload.approved is False:
        approval_status = "rejected"

    return {
        "run_id": run.id,
        "region": run.region,
        "approval_status": approval_status,
        "feedback": payload.feedback,
        "explainability_meta": meta,
    }
