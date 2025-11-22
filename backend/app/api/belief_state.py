# app/api/belief_state.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.services.belief_state_store import (
    BeliefStateStore,
    get_belief_state_store,
)


router = APIRouter(
    prefix="/belief-state",
    tags=["belief-state"],
)


class BaselineUpdateRequest(BaseModel):
    region: str = Field(..., description="Region name, e.g. 'Khartoum'")
    run_id: str = Field(..., description="Baseline analysis run_id")
    trend_classification: Optional[str] = Field(
        None,
        description="Trend label, e.g. ESCALATING, STABLE, ...",
    )
    armed_clash_likelihood: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="0–100 risk probability for armed clashes",
    )
    civilian_targeting_likelihood: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="0–100 risk probability for civilian targeting",
    )
    notes: Optional[str] = Field(
        None,
        description="Optional analyst note about this baseline",
    )


class InterventionItem(BaseModel):
    id: Optional[str] = Field(
        None,
        description="Intervention id (omit for new interventions)",
    )
    description: str = Field(..., description="What the intervention is")
    status: str = Field(
        "PLANNED",
        description="PLANNED|ONGOING|COMPLETED|CANCELLED",
    )
    notes: Optional[str] = Field(
        None,
        description="Optional note/comment",
    )


class InterventionsUpdateRequest(BaseModel):
    region: str = Field(..., description="Region name")
    scenario_run_id: Optional[str] = Field(
        None,
        description="Scenario run_id this intervention set is based on",
    )
    interventions: List[InterventionItem]


@router.get("/region/{region}")
def get_region_belief_state(
    region: str,
    store: BeliefStateStore = Depends(get_belief_state_store),
) -> Dict[str, Any]:
    """
    Get the current belief state for a region.

    This includes last baseline run, last scenario run, current trend and
    risk estimates, and any active interventions.
    """
    return store.get_region_state(region)


@router.post("/baseline")
def update_baseline(
    req: BaselineUpdateRequest,
    store: BeliefStateStore = Depends(get_belief_state_store),
) -> Dict[str, Any]:
    """
    Update the baseline belief state for a region from an analysis run.

    Typical flow:
    - Client calls /api/analysis/run and gets trend_analysis + run_id.
    - Client then POSTs to /api/belief-state/baseline with these values.
    """
    state = store.update_baseline(
        region=req.region,
        run_id=req.run_id,
        trend_classification=req.trend_classification,
        armed_clash_likelihood=req.armed_clash_likelihood,
        civilian_targeting_likelihood=req.civilian_targeting_likelihood,
        notes=req.notes,
    )
    return state


@router.post("/interventions")
def apply_interventions(
    req: InterventionsUpdateRequest,
    store: BeliefStateStore = Depends(get_belief_state_store),
) -> Dict[str, Any]:
    """
    Add or update interventions in the belief state for a region.

    Typical flow:
    - Client runs /api/analysis/scenario-run with some interventions.
    - Client calls /api/belief-state/interventions with the same region,
      scenario_run_id, and a list of interventions (PLANNED/ONGOING/etc.).
    """
    interventions_dicts = [iv.dict() for iv in req.interventions]
    state = store.apply_interventions(
        region=req.region,
        interventions=interventions_dicts,
        scenario_run_id=req.scenario_run_id,
    )
    return state
