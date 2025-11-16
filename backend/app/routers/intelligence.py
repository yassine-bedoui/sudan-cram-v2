from datetime import datetime
import json
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.agents.workflow import run_analysis
from app.models.analysis_run import AnalysisRun, AnalysisFeedback
from database import get_db

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


# ---------- Pydantic models ----------


class AnalysisRequest(BaseModel):
    region: str
    raw_data: Optional[str] = None
    interventions: Optional[List[str]] = None


class FeedbackRequest(BaseModel):
    status: Literal["approved", "rejected"]
    comment: Optional[str] = None
    user: Optional[str] = None


# ---------- Helper: build narrative summary from explainability ----------


def build_narrative_from_explainability(expl: dict | None) -> Optional[str]:
    if not expl:
        return None

    try:
        input_block = expl.get("input", {}) or {}
        retrieval = expl.get("retrieval", {}) or {}
        trend = expl.get("trend", {}) or {}
        scenarios = expl.get("scenarios", {}) or {}
        validation = expl.get("validation", {}) or {}

        region = input_block.get("region")
        total_events = retrieval.get("total_events_considered")
        time_span_days = retrieval.get("time_span_days")
        sources_dict = retrieval.get("sources") or {}

        # e.g. "GDELT (20)"
        sources_list = []
        for name, count in sources_dict.items():
            if isinstance(count, (int, float)):
                sources_list.append(f"{name} ({int(count)})")
            else:
                sources_list.append(str(name))
        sources_str = ", ".join(sources_list)

        trend_cls = trend.get("trend_classification")
        conf_label = trend.get("confidence_label")
        forecast = trend.get("forecast_7_days") or {}
        armed = forecast.get("armed_clash_likelihood")
        civilian = forecast.get("civilian_targeting_likelihood")

        scen_recs = scenarios.get("recommendations") or []
        rec = scen_recs[0] if scen_recs else None
        max_success = scenarios.get("max_success_probability")
        max_risk = scenarios.get("max_risk_probability")

        val_status = validation.get("status")
        overall_conf = validation.get("overall_confidence")
        issue_count = validation.get("issue_count") or len(validation.get("issues") or [])

        parts: list[str] = []

        # 1) Region + data window
        if region:
            parts.append(f"Region {region}:")

        if total_events is not None and time_span_days is not None:
            segment = f" over the last {time_span_days} days the model considered {total_events} recent events"
            if sources_str:
                segment += f" from {sources_str}"
            segment += "."
            parts.append(segment)
        elif total_events is not None:
            parts.append(f" The model considered {total_events} recent events.")

        # 2) Trend classification
        if trend_cls:
            segment = f" Current trend is classified as {trend_cls}"
            if conf_label:
                segment += f" (confidence {conf_label})"
            segment += "."
            parts.append(segment)

        # 3) 7-day risk outlook
        if armed is not None or civilian is not None:
            sub = []
            if armed is not None:
                sub.append(f"~{armed}% chance of armed clashes")
            if civilian is not None:
                sub.append(f"~{civilian}% risk of civilian targeting")
            risk_segment = " 7-day outlook: " + " and ".join(sub) + "."
            parts.append(risk_segment)

        # 4) Intervention recommendation
        if rec or max_success is not None or max_risk is not None:
            seg = " Intervention signal: "
            if rec:
                seg += f"{rec} is recommended"
            if max_success is not None:
                seg += f" with success probability around {max_success}%"
            if max_risk is not None:
                seg += f" and downside risk around {max_risk}%"
            seg += "."
            parts.append(seg)

        # 5) Validation + confidence
        if val_status:
            seg = f" Validation status: {val_status}"
            if isinstance(overall_conf, (int, float, float)):
                seg += f" (overall confidence {overall_conf:.2f})"
            if issue_count:
                seg += f", with {issue_count} flagged issue(s)."
            else:
                seg += "."
            parts.append(seg)

        narrative = " ".join(p.strip() for p in parts if p)
        return narrative or None

    except Exception:
        # Fail soft: never break the API because of narrative generation
        return None


# ---------- Health ----------


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "intelligence"}


# ---------- Main analysis endpoint ----------


@router.post("/analyze")
async def analyze_intelligence(
    req: AnalysisRequest,
    db: Session = Depends(get_db),
):
    # 1) Run the multi-agent workflow
    result = run_analysis(
        region=req.region,
        raw_data=req.raw_data,
        interventions=req.interventions,
    )

    trends = result.get("trend_analysis") or {}
    scenarios = result.get("scenarios") or {}
    validation = result.get("validation") or {}
    explainability = result.get("explainability")

    # NEW: short narrative summary derived from explainability
    narrative_summary = build_narrative_from_explainability(explainability)

    # 2) Build a compact summary for the DB row
    forecast = trends.get("forecast_7_days") or {}

    scenarios_list = scenarios.get("scenarios") or []
    recommendation_summary = None
    max_success_probability = None
    max_risk_probability = None

    if scenarios_list:
        # First non-null recommendation as summary
        recs = [s.get("recommendation") for s in scenarios_list if s.get("recommendation")]
        recommendation_summary = recs[0] if recs else None

        success_probs = [
            s.get("optimistic", {}).get("success_probability")
            for s in scenarios_list
            if isinstance(s.get("optimistic", {}).get("success_probability"), (int, float))
        ]
        risk_probs = [
            s.get("pessimistic", {}).get("risk_probability")
            for s in scenarios_list
            if isinstance(s.get("pessimistic", {}).get("risk_probability"), (int, float))
        ]
        max_success_probability = max(success_probs) if success_probs else None
        max_risk_probability = max(risk_probs) if risk_probs else None

    issues = validation.get("issues") or []
    issue_count = len(issues)

    # Store interventions as JSON string for now (keeps schema simple)
    interventions_json_str = json.dumps(req.interventions) if req.interventions is not None else None

    run_row = AnalysisRun(
        region=result.get("region", req.region),
        has_raw_data=bool(req.raw_data),
        interventions=interventions_json_str,
        trend_classification=trends.get("trend_classification"),
        trend_confidence_label=trends.get("confidence"),
        forecast_armed_clash=forecast.get("armed_clash_likelihood"),
        forecast_civilian_targeting=forecast.get("civilian_targeting_likelihood"),
        recommendation_summary=recommendation_summary,
        max_success_probability=max_success_probability,
        max_risk_probability=max_risk_probability,
        validation_status=validation.get("validation_status"),
        issue_count=issue_count,
        overall_confidence=validation.get("overall_confidence", result.get("confidence_score")),
        explainability=explainability,
    )

    db.add(run_row)
    db.commit()
    db.refresh(run_row)

    # 3) Shape API response (same as run_analysis + run_id)
    response = {
        "run_id": run_row.id,
        "region": result.get("region", req.region),
        "timestamp": result.get("timestamp", datetime.utcnow().isoformat()),
        "events": result.get("extracted_events"),
        "trends": trends,
        "scenarios": scenarios,
        "validation": validation,
        "approval_status": result.get("approval_status"),
        "confidence": result.get("confidence_score"),
        "messages": result.get("messages", []),
    }

    if explainability is not None:
        response["explainability"] = explainability
    if narrative_summary:
        response["narrative_summary"] = narrative_summary

    return response


# ---------- Thin history endpoint ----------


@router.get("/runs")
async def list_runs(limit: int = 20, db: Session = Depends(get_db)):
    rows = (
        db.query(AnalysisRun)
        .order_by(AnalysisRun.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": r.id,
            "region": r.region,
            "has_raw_data": r.has_raw_data,
            "interventions": json.loads(r.interventions) if r.interventions else None,
            "trend_classification": r.trend_classification,
            "trend_confidence_label": r.trend_confidence_label,
            "forecast_armed_clash": r.forecast_armed_clash,
            "forecast_civilian_targeting": r.forecast_civilian_targeting,
            "recommendation_summary": r.recommendation_summary,
            "max_success_probability": r.max_success_probability,
            "max_risk_probability": r.max_risk_probability,
            "validation_status": r.validation_status,
            "issue_count": r.issue_count,
            "overall_confidence": r.overall_confidence,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


# ---------- Feedback / approval endpoint ----------


@router.post("/runs/{run_id}/feedback")
async def submit_feedback(
    run_id: int,
    payload: FeedbackRequest,
    db: Session = Depends(get_db),
):
    run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="analysis_run not found")

    feedback = AnalysisFeedback(
        run_id=run_id,
        status=payload.status,
        comment=payload.comment,
        user=payload.user,
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return {
        "id": feedback.id,
        "run_id": feedback.run_id,
        "status": feedback.status,
        "comment": feedback.comment,
        "user": feedback.user,
        "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
    }
