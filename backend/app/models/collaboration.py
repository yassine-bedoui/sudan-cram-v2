# app/models/collaboration.py

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---- Feedback / red-team loop models ----

class FeedbackType(str, Enum):
    ERROR_REPORT = "error_report"     # "this is factually wrong"
    OVERRIDE = "override"             # "I disagree, here is the correct label"
    COMMENT = "comment"               # general comment / note


class FeedbackTarget(str, Enum):
    NARRATIVE = "narrative"           # narrative section / sentence
    TREND = "trend"                   # trend_classification / forecast
    SCENARIO = "scenario"             # specific intervention scenario
    EVENT = "event"                   # specific event in events list
    OTHER = "other"


class FeedbackCreate(BaseModel):
    """
    Payload used when an analyst submits new feedback / correction.
    """
    run_id: str = Field(..., description="ID of the analysis run (from run_analysis)")
    region: str = Field(..., description="Region this feedback refers to")
    feedback_type: FeedbackType
    target: FeedbackTarget

    # Optional: point to a specific thing (e.g., section_id, scenario_id, event index)
    target_id: Optional[str] = Field(
        None, description="Identifier of target (e.g. section_id, scenario_id, event index)"
    )

    # Free-text analyst comment explaining what is wrong / should change
    comment: str = Field(..., min_length=3)

    # Optional suggestion for correction (e.g., new label, alternative text)
    suggested_change: Optional[str] = None

    # Optional analyst identifier (could be email, username, org)
    analyst_id: Optional[str] = None

    # Arbitrary tags, e.g. ["high_priority", "red_team"]
    tags: List[str] = Field(default_factory=list)


class FeedbackRecord(FeedbackCreate):
    """
    Full persisted record with server-side fields added.
    """
    id: str
    created_at: str  # ISO timestamp
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[str] = None


# ---- Local actor input / contestation ----

class LocalActorRole(str, Enum):
    NGO = "ngo"
    COMMUNITY_LEADER = "community_leader"
    LOCAL_OFFICIAL = "local_official"
    JOURNALIST = "journalist"
    OTHER = "other"


class LocalActorInputCreate(BaseModel):
    """
    Local partner / community feedback about how the model sees their region.
    """
    region: str
    actor_name: Optional[str] = Field(
        None, description="Name or alias (can be pseudonymous for safety)."
    )
    actor_role: LocalActorRole = LocalActorRole.OTHER
    affiliation: Optional[str] = Field(
        None, description="Org / community / group name, if safe to share."
    )

    # Their perspective: what do they think the model gets wrong or misses?
    view_on_risk: str = Field(
        ...,
        min_length=5,
        description="How they see the risk situation, and where they agree/disagree with the model.",
    )

    # If referring to a specific run / narrative / section, they can point to it
    run_id: Optional[str] = None
    section_id: Optional[str] = None  # e.g. 'trend_&_risk_outlook_(next_7_days)'


class LocalActorInputRecord(LocalActorInputCreate):
    id: str
    created_at: str  # ISO timestamp


# ---- Scenario exploration API models ----

class ScenarioPreviewRequest(BaseModel):
    """
    Request from the frontend to explore 'what if we tried these interventions?'
    """
    region: str
    interventions: List[str] = Field(
        default_factory=list,
        description="Candidate interventions (plain language).",
    )
    raw_data: Optional[str] = Field(
        None,
        description="Optional raw text report to feed Agent A.",
    )


class ScenarioPreviewResponse(BaseModel):
    """
    Lightweight response for scenario dashboard / sandbox.
    """
    run_id: str
    region: str
    scenarios: Optional[Dict[str, Any]]
    trend_analysis: Optional[Dict[str, Any]]
    approval_status: Optional[str]
    confidence_score: float
    decision_prompts: List[str] = Field(
        default_factory=list,
        description="Decision-friction questions from the explainability layer.",
    )
