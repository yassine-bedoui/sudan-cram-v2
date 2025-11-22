# app/api/feedback.py

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services.feedback_store import FeedbackStore, get_feedback_store

router = APIRouter(prefix="/api", tags=["feedback"])


# ---------- Pydantic models ----------


class FeedbackCreate(BaseModel):
    """Payload used when an analyst/system submits feedback."""

    run_id: str = Field(..., description="ID of the analysis run this feedback refers to")
    region: str = Field(..., description="Region name, e.g. 'Khartoum'")
    source: Literal["analyst", "system", "local_actor", "other"] = Field(
        "analyst", description="Who provided the feedback"
    )
    feedback_type: Literal["CORRECTION", "APPROVAL", "ALERT", "OTHER"] = Field(
        ..., description="Type/category of feedback"
    )
    comment: str = Field(..., description="Free-text feedback from the user")
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        "LOW", description="How important/urgent this feedback is"
    )
    created_by: Optional[str] = Field(
        None, description="Optional user ID / name of the person creating the feedback"
    )


class FeedbackRecord(FeedbackCreate):
    """What we store + return from the API."""

    id: str = Field(..., description="Unique ID for this feedback record")
    created_at: datetime = Field(
        ..., description="When this feedback record was created (UTC ISO timestamp)"
    )


class FeedbackSummary(BaseModel):
    """Aggregated view of feedback for a single run."""

    run_id: str
    region: Optional[str] = Field(
        None,
        description="Dominant region for this run (if consistent across feedback rows)",
    )
    total_feedback: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    latest_created_at: Optional[datetime] = None


# ---------- Internal helper ----------


def _get_field(obj: Any, name: str, default: Any = None) -> Any:
    """
    Safely get a field from either a dict or an object with attributes.

    This makes the API resilient regardless of whether FeedbackStore returns
    plain dicts or Pydantic models / dataclasses.
    """
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


# ---------- Routes ----------


@router.post(
    "/feedback",
    response_model=FeedbackRecord,
    summary="Submit feedback for an analysis run",
)
def create_feedback(
    payload: FeedbackCreate,
    store: FeedbackStore = Depends(get_feedback_store),
) -> FeedbackRecord:
    """
    Create a new feedback record.

    This is the endpoint your `curl -X POST /api/feedback` is already hitting.
    """
    record = store.append(payload.dict())
    # `record` comes back as a dict that matches FeedbackRecord
    return FeedbackRecord(**record)


@router.get(
    "/feedback/run/{run_id}",
    response_model=List[FeedbackRecord],
    summary="List feedback for a specific run",
)
def get_feedback_for_run(
    run_id: str,
    store: FeedbackStore = Depends(get_feedback_store),
) -> List[FeedbackRecord]:
    """
    Return all feedback records associated with a single analysis run.
    """
    rows = store.list_by_run(run_id)
    return [FeedbackRecord(**r) for r in rows]


@router.get(
    "/feedback/region/{region}",
    response_model=List[FeedbackRecord],
    summary="List feedback for a specific region",
)
def get_feedback_for_region(
    region: str,
    store: FeedbackStore = Depends(get_feedback_store),
) -> List[FeedbackRecord]:
    """
    Return all feedback records associated with a given region.
    """
    rows = store.list_by_region(region)
    return [FeedbackRecord(**r) for r in rows]


@router.get(
    "/feedback",
    response_model=List[FeedbackRecord],
    summary="List all feedback (optional filters by run_id or region)",
)
def list_all_feedback(
    run_id: Optional[str] = None,
    region: Optional[str] = None,
    store: FeedbackStore = Depends(get_feedback_store),
) -> List[FeedbackRecord]:
    """
    List all feedback, with optional query filters.

    Examples:
      - GET /api/feedback                       -> all feedback
      - GET /api/feedback?run_id=123            -> only feedback for run 123
      - GET /api/feedback?region=Khartoum       -> only feedback for that region
      - GET /api/feedback?run_id=123&region=Khartoum -> both filters
    """
    if run_id:
        rows = store.list_by_run(run_id)
    elif region:
        rows = store.list_by_region(region)
    else:
        rows = store.list_all()

    return [FeedbackRecord(**r) for r in rows]


@router.get(
    "/feedback/run/{run_id}/summary",
    response_model=FeedbackSummary,
    summary="Get aggregated feedback summary for a run",
)
def get_feedback_summary_for_run(
    run_id: str,
    store: FeedbackStore = Depends(get_feedback_store),
) -> FeedbackSummary:
    """
    Provide an aggregated view of feedback for a given run:

      - total_feedback
      - counts by feedback_type
      - counts by severity
      - latest_created_at
      - a best-guess region (if all feedback shares the same region)
    """
    rows = store.list_by_run(run_id)

    if not rows:
        # You can either return an empty summary or 404.
        # Here we choose to return an empty but valid summary.
        return FeedbackSummary(
            run_id=run_id,
            region=None,
            total_feedback=0,
            by_type={},
            by_severity={},
            latest_created_at=None,
        )

    by_type: Dict[str, int] = {}
    by_severity: Dict[str, int] = {}
    regions_seen: Dict[str, int] = {}

    latest: Optional[datetime] = None

    for r in rows:
        ftype = _get_field(r, "feedback_type", "OTHER")
        sev = _get_field(r, "severity", "LOW")
        region = _get_field(r, "region")

        by_type[ftype] = by_type.get(ftype, 0) + 1
        by_severity[sev] = by_severity.get(sev, 0) + 1

        if region:
            regions_seen[region] = regions_seen.get(region, 0) + 1

        created_at = _get_field(r, "created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except Exception:
                created_at = None

        if isinstance(created_at, datetime):
            if latest is None or created_at > latest:
                latest = created_at

    # Pick the region that appears most often, if any
    dominant_region: Optional[str] = None
    if regions_seen:
        dominant_region = max(regions_seen.items(), key=lambda kv: kv[1])[0]

    summary = FeedbackSummary(
        run_id=run_id,
        region=dominant_region,
        total_feedback=len(rows),
        by_type=by_type,
        by_severity=by_severity,
        latest_created_at=latest,
    )

    return summary
