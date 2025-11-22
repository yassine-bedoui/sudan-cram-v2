# app/routers/analysis.py

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.workflow import run_analysis


router = APIRouter(
    prefix="/analysis",   # will be combined with "/api" in main.py
    tags=["analysis"],
)


class AnalysisRequest(BaseModel):
    region: str
    raw_data: Optional[str] = None
    # use default_factory to avoid mutable default list
    interventions: List[str] = Field(default_factory=list)


class ScenarioRunRequest(BaseModel):
    """
    Request body for running a 'what-if' scenario analysis.

    - base_run_id: the original analysis run this scenario is built on
    - region:      region to analyze; frontend should pass it from the base run
    - raw_data:    optional raw text (news / reports) to include
    - interventions: hypothetical interventions to evaluate
    """

    base_run_id: str = Field(
        ...,
        description="The original analysis run_id that this scenario builds on.",
    )
    region: Optional[str] = Field(
        None,
        description="Region for the scenario (frontend should send the base run's region).",
    )
    raw_data: Optional[str] = Field(
        default=None,
        description="Optional raw text report to include in the scenario analysis.",
    )
    interventions: List[str] = Field(
        ...,
        min_items=1,
        description="List of hypothetical interventions to evaluate.",
    )


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


@router.post("/scenario-run")
def run_scenario_analysis(req: ScenarioRunRequest):
    """
    Run a 'what-if' scenario using the multi-agent analysis pipeline.

    This reuses the same run_analysis(...) function as /analysis/run,
    but:
    - attaches the base_run_id to the result
    - flags the response as a scenario run

    NOTE: For simplicity, this endpoint expects the caller to pass `region`
    explicitly (copied from the base run). We don't yet look up the base run
    from the audit log.
    """
    region = (req.region or "").strip()
    if not region:
        raise HTTPException(
            status_code=400,
            detail=(
                "region is required for scenario runs. "
                "Frontend should pass the region from the base run."
            ),
        )

    result = run_analysis(
        region=region,
        raw_data=req.raw_data,
        interventions=req.interventions,
    )

    # Attach scenario metadata so the frontend can link this back to the
    # original run and display it as a scenario.
    result["base_run_id"] = req.base_run_id
    result["is_scenario_run"] = True

    return result
