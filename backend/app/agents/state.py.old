# app/agents/state.py

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class SudanCRAMState(TypedDict, total=False):
    """
    Shared state that flows through the LangGraph multi-agent workflow.

    This is the single source of truth that all agents (nodes) read from
    and write to. Each field here is used somewhere in workflow.py.
    """

    # ---- Core inputs ----
    region: str                      # e.g. "Khartoum"
    raw_data: Optional[str]          # Optional raw text report for Agent A
    interventions: List[str]         # Candidate interventions for Agent C

    # ---- RAG context ----
    # Raw hits from the vector store (Qdrant)
    retrieved_events: List[Dict[str, Any]]

    # Canonical, deduplicated events timeline built from retrieved_events
    # Each item has: date, source, region, event_type, actors, fatalities
    events: List[Dict[str, Any]]

    # ---- Agent outputs ----
    # Agent A (event_extractor_node)
    extracted_events: Optional[Dict[str, Any]]

    # Agent B (trend_analyst_node)
    trend_analysis: Optional[Dict[str, Any]]

    # Agent C (scenario_generator_node)
    scenarios: Optional[Dict[str, Any]]

    # Agent D (consistency_checker_node)
    validation: Optional[Dict[str, Any]]

    # Agent E (narrative_generator_node)
    # Human-readable markdown brief for the frontend (policy / situation brief)
    narrative: Optional[str]

    # ---- Human-in-the-loop control ----
    human_approval_required: bool
    approval_status: Optional[str]   # "pending", "auto-approved", or None

    # ---- Metadata / tracing ----
    messages: List[str]              # Human-readable steps taken by agents
    confidence_score: float          # Overall pipeline confidence (0–1)
    timestamp: str                   # ISO timestamp when state was created

    # ---- RAG retrieval explainability ----
    # Set by rag_retrieval_node:
    # {
    #   "query": "recent conflict events in Khartoum",
    #   "filters": {"region": "Khartoum", "mode": "semantic_region_filter"}
    # }
    retrieval_context: Optional[Dict[str, Any]]

    # ---- Final explainability snapshot ----
    # Built by run_analysis via _build_explainability_payload(...)
    explainability: Optional[Dict[str, Any]]
