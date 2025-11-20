# app/routers/analysis.py

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.workflow import run_analysis


router = APIRouter(
    prefix="/analysis",   # will be combined with "/api" in main.py
    tags=["analysis"],
)


class AnalysisRequest(BaseModel):
    region: str
    raw_data: Optional[str] = None
    interventions: List[str] = []


@router.post("/run")
def run_conflict_analysis(req: AnalysisRequest):
    """
    Run the LangGraph conflict analysis workflow for a given region.
    """
    return run_analysis(
        region=req.region,
        raw_data=req.raw_data,
        interventions=req.interventions,
    )
