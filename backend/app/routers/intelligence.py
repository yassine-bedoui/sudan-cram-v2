# app/routers/intelligence.py
from typing import List, Optional, Any, Dict
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from database import get_db
from app.agents.workflow import run_analysis
from app.models.analysis import AnalysisRun

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


# ---------- Pydantic models ----------

class IntelligenceRequest(BaseModel):
    region: str
    raw_data: Optional[str] = None
    interventions: List[str] = Field(default_factory=list)


class FeedbackPayload(BaseModel):
    approved: bool
    comment: Optional[str] = None


# ---------- Health ----------

@router.get("/health")
async def health():
    return {"status": "healthy", "service": "intelligence"}


# ---------- Small helpers for logging ----------

def _extract_recommendation_summary(scenarios: Optional[Dict[str, Any]]) -> Optional[str]:
    if not scenarios:
        return None
    items = scenarios.get("scenarios") or []
    if not items:
        return None
    recommendations = {s.get("recommendation") for s in items if s.get("recommendation")}
    if not recommendations:
        return None
    if len(recommendations) == 1:
        return next(iter(recommendations))
    return ", ".join(sorted(recommendations))


def _extract_max_success_prob(scenarios: Optional[Dict[str, Any]]) -> Optional[int]:
    if not scenarios:
        return None
    vals: List[int] = []
    for s in scenarios.get("scenarios") or []:
        opt = s.get("optimistic") or {}
        p = opt.get("success_probability")
        if isinstance(p, (int, float)):
            vals.append(int(p))
    return max(vals) if vals else None


def _extract_max_risk_prob(scenarios: Optional[Dict[str, Any]]) -> Optional[int]:
    if not scenarios:
        return None
    vals: List[int] = []
    for s in scenarios.get("scenarios") or []:
        pess = s.get("pessimistic") or {}
        p = pess.get("risk_probability")
        if isinstance(p, (int, float)):
            vals.append(int(p))
    return max(vals) if vals else None


# ---------- Main analysis endpoint ----------

@router.post("/analyze")
def analyze_intelligence(payload: IntelligenceRequest, db: Session = Depends(get_db)):
    # 1) Run the LangGraph / intelligence workflow
    result = run_analysis(
        region=payload.region,
        raw_data=payload.raw_data,
        interventions=payload.interventions,
    )

    trend = result.get("trend_analysis") or {}
    forecast = trend.get("forecast_7_days") or {}
    scenarios = result.get("scenarios")
    validation = result.get("validation") or {}
    explainability = result.get("explainability")

    # 2) Best-effort persistence: if DB is down, we still return 200
    run_id: Optional[int] = None

    try:
        analysis_run = AnalysisRun(
            region=result.get("region"),
            has_raw_data=result.get("raw_data") is not None,
            interventions=json.dumps(result.get("interventions") or []),
            trend_classification=trend.get("trend_classification"),
            trend_confidence_label=trend.get("confidence"),
            forecast_armed_clash=forecast.get("armed_clash_likelihood"),
            forecast_civilian_targeting=forecast.get("civilian_targeting_likelihood"),
            recommendation_summary=_extract_recommendation_summary(scenarios),
            max_success_probability=_extract_max_success_prob(scenarios),
            max_risk_probability=_extract_max_risk_prob(scenarios),
            validation_status=validation.get("validation_status"),
            issue_count=len(validation.get("issues") or []),
            overall_confidence=float(
                validation.get("overall_confidence")
                or result.get("confidence_score")
                or 0.0
            ),
            # Column is JSON in the DB model, so we can pass the dict directly
            explainability=explainability,
        )
        db.add(analysis_run)
        db.commit()
        db.refresh(analysis_run)
        run_id = analysis_run.id
    except OperationalError as e:
        # Remote DB unreachable (DNS / network / etc.)
        db.rollback()
        print(f"⚠️ Could not persist analysis run (DB unavailable): {e}")
        result.setdefault("messages", []).append(
            "⚠️ Failed to persist analysis run (database unavailable)."
        )
    except SQLAlchemyError as e:
        # Any other SQLAlchemy error – do not crash the endpoint
        db.rollback()
        print(f"⚠️ SQLAlchemy error while logging analysis run: {e}")
        result.setdefault("messages", []).append(
            "⚠️ Failed to persist analysis run due to database error."
        )

    # 3) Shape API response for the frontend
    response = {
        "run_id": run_id,
        "region": result.get("region"),
        "timestamp": result.get("timestamp"),
        "events": result.get("extracted_events"),
        "trends": result.get("trend_analysis"),
        "scenarios": result.get("scenarios"),
        "validation": result.get("validation"),
        "approval_status": result.get("approval_status"),
        "confidence": result.get("confidence_score"),
        "messages": result.get("messages", []),
        "explainability": result.get("explainability"),
    }
    return response


# ---------- History / runs list ----------

@router.get("/runs")
def list_runs(limit: int = 20, db: Session = Depends(get_db)):
    try:
        runs = (
            db.query(AnalysisRun)
            .order_by(AnalysisRun.created_at.desc())
            .limit(limit)
            .all()
        )
    except OperationalError as e:
        print(f"⚠️ DB unavailable when listing runs: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable.")

    return [
        {
            "id": r.id,
            "region": r.region,
            "created_at": r.created_at,
            "trend_classification": r.trend_classification,
            "overall_confidence": r.overall_confidence,
            "validation_status": r.validation_status,
            "recommendation_summary": r.recommendation_summary,
        }
        for r in runs
    ]


@router.get("/runs/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db)):
    try:
        run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    except OperationalError as e:
        print(f"⚠️ DB unavailable when getting run {run_id}: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable.")

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return {
        "id": run.id,
        "region": run.region,
        "created_at": run.created_at,
        "trend_classification": run.trend_classification,
        "trend_confidence_label": run.trend_confidence_label,
        "forecast_armed_clash": run.forecast_armed_clash,
        "forecast_civilian_targeting": run.forecast_civilian_targeting,
        "recommendation_summary": run.recommendation_summary,
        "max_success_probability": run.max_success_probability,
        "max_risk_probability": run.max_risk_probability,
        "validation_status": run.validation_status,
        "issue_count": run.issue_count,
        "overall_confidence": run.overall_confidence,
        "explainability": run.explainability,
    }


# ---------- Feedback / approval (Task 3) ----------

@router.post("/runs/{run_id}/feedback")
def submit_feedback(
    run_id: int,
    payload: FeedbackPayload,
    db: Session = Depends(get_db),
):
    try:
        run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    except OperationalError as e:
        print(f"⚠️ DB unavailable when updating feedback for run {run_id}: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable.")

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    status = "approved" if payload.approved else "rejected"
    # For now we just log the feedback; we can add columns later if needed.
    print(f"📝 Feedback for run {run_id}: {status} (comment={payload.comment!r})")

    return {"run_id": run_id, "status": status}
