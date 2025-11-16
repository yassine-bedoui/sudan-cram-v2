# app/routers/intelligence.py
from datetime import datetime
import json
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.workflow import run_analysis
from database import get_db
from app.models.analysis import AnalysisRun

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


# ---------- Pydantic models ----------

class AnalysisRequest(BaseModel):
    region: str
    raw_data: Optional[str] = None
    interventions: Optional[List[str]] = None


class AnalysisRunSummary(BaseModel):
    id: int
    region: str
    created_at: datetime
    trend_classification: Optional[str] = None
    validation_status: Optional[str] = None
    overall_confidence: Optional[float] = None
    recommendation_summary: Optional[str] = None

    class Config:
        orm_mode = True


# ---------- Helper: log to analysis_runs ----------

def log_analysis_run(db: Session, result: dict) -> AnalysisRun:
    """
    Persist a lightweight log of this analysis run into analysis_runs table,
    using the explainability payload as the main source of truth.
    """
    explain = result.get("explainability") or {}

    input_block = explain.get("input", {}) or {}
    trend = explain.get("trend", {}) or {}
    scenarios = explain.get("scenarios", {}) or {}
    validation = explain.get("validation", {}) or {}

    # Input context
    region = result.get("region") or input_block.get("region")
    has_raw_data = bool(input_block.get("has_raw_data", False))
    interventions = input_block.get("interventions", [])

    # Trend
    forecast = trend.get("forecast_7_days", {}) or {}
    trend_classification = trend.get("trend_classification")
    trend_confidence_label = trend.get("confidence_label")

    # Scenarios
    recs = scenarios.get("recommendations", []) or []
    max_success = scenarios.get("max_success_probability")
    max_risk = scenarios.get("max_risk_probability")

    # Validation
    validation_status = validation.get("status")
    issue_count = validation.get("issue_count")
    overall_confidence = validation.get("overall_confidence")

    run = AnalysisRun(
        region=region or "UNKNOWN",
        has_raw_data=has_raw_data,
        interventions=json.dumps(interventions, ensure_ascii=False),
        trend_classification=trend_classification,
        trend_confidence_label=trend_confidence_label,
        forecast_armed_clash=forecast.get("armed_clash_likelihood"),
        forecast_civilian_targeting=forecast.get("civilian_targeting_likelihood"),
        recommendation_summary=",".join(recs)[:100] if recs else None,
        max_success_probability=max_success,
        max_risk_probability=max_risk,
        validation_status=validation_status,
        issue_count=issue_count,
        overall_confidence=overall_confidence,
        explainability=explain or None,
    )

    db.add(run)
    db.commit()
    db.refresh(run)
    return run


# ---------- Routes ----------

@router.post("/analyze")
async def analyze(request: AnalysisRequest, db: Session = Depends(get_db)):
    """Run multi-agent analysis and log it to analysis_runs."""
    try:
        result = run_analysis(
            region=request.region,
            raw_data=request.raw_data,
            interventions=request.interventions,
        )

        # Persist to DB (Task 2)
        run = log_analysis_run(db, result)

        return {
            "run_id": run.id,
            "region": result["region"],
            "timestamp": result["timestamp"],
            "events": result.get("extracted_events"),
            "trends": result.get("trend_analysis"),
            "scenarios": result.get("scenarios"),
            "validation": result.get("validation"),
            "approval_status": result.get("approval_status"),
            "confidence": result.get("confidence_score"),
            "messages": result.get("messages", []),
            # expose explainability so frontend can render "Why this?"
            "explainability": result.get("explainability"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs", response_model=List[AnalysisRunSummary])
async def list_runs(limit: int = 20, db: Session = Depends(get_db)):
    """
    Return the most recent analysis runs (for internal dashboard / debugging).
    """
    runs = (
        db.query(AnalysisRun)
        .order_by(AnalysisRun.created_at.desc())
        .limit(limit)
        .all()
    )
    return runs


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "intelligence"}
