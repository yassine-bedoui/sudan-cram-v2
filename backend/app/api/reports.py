# app/api/reports.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.services.report_store import ReportStore, get_report_store


router = APIRouter(
    prefix="/reports",
    tags=["reports"],
)


class ReportCreate(BaseModel):
    region: str = Field(..., description="Region name, e.g. 'Khartoum'")
    source: str = Field(
        ...,
        description="Source label, e.g. 'local_actor', 'ngo', 'analyst', 'media'",
    )
    report_type: str = Field(
        "FIELD_REPORT",
        description="Type of report, e.g. FIELD_REPORT, SECURITY_UPDATE, COMMENT",
    )
    text: str = Field(..., description="Free-form report text / narrative")
    language: str = Field("en", description="Language code (e.g. 'en')")
    tags: List[str] = Field(default_factory=list, description="Optional tags")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional structured metadata about the report",
    )
    created_by: Optional[str] = Field(
        None,
        description="User identifier (e.g. analyst username or email)",
    )
    run_id: Optional[str] = Field(
        None,
        description="Optional link to an analysis run_id this report refers to",
    )


class ReportOut(BaseModel):
    id: str
    run_id: Optional[str]
    region: str
    source: str
    report_type: str
    text: str
    language: str
    tags: List[str]
    metadata: Dict[str, Any]
    created_by: Optional[str]
    created_at: str
    updated_at: str


@router.post("", response_model=ReportOut)
def create_report(
    req: ReportCreate,
    store: ReportStore = Depends(get_report_store),
):
    """
    Ingest a new local/analyst/partner report.

    This gives local actors a safe way to contest or enrich the model’s view
    of a region. The report is persisted and can later be wired into RAG.
    """
    stored = store.append_report(req.dict())
    return stored  # Pydantic will coerce to ReportOut


@router.get("", response_model=List[ReportOut])
def list_reports(
    region: Optional[str] = Query(
        None,
        description="Optional region filter (exact match)",
    ),
    source: Optional[str] = Query(
        None,
        description="Optional source filter (exact match)",
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Maximum number of reports to return",
    ),
    store: ReportStore = Depends(get_report_store),
):
    """
    List reports, optionally filtered by region and/or source.
    """
    items = store.list_reports(region=region, source=source, limit=limit)
    return items


@router.get("/run/{run_id}", response_model=List[ReportOut])
def list_reports_for_run(
    run_id: str,
    store: ReportStore = Depends(get_report_store),
):
    """
    List all reports that explicitly reference a given analysis run_id.
    """
    items = store.list_reports_for_run(run_id=run_id)
    return items
