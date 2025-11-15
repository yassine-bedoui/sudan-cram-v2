# backend/app/agents/state.py
from typing import TypedDict, List, Dict, Optional


class SudanCRAMState(TypedDict):
    # Input
    region: str
    raw_data: Optional[str]
    interventions: Optional[List[str]]

    # RAG Context
    retrieved_events: List[Dict]

    # Agent Outputs
    extracted_events: Optional[Dict]
    trend_analysis: Optional[Dict]
    scenarios: Optional[Dict]
    validation: Optional[Dict]

    # Control
    human_approval_required: bool
    approval_status: Optional[str]

    # Metadata
    messages: List[str]
    confidence_score: float
    timestamp: str
