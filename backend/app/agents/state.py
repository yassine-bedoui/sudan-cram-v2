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
    country_iso3: str               # NEW: country context, e.g. "SDN", "SOM"
    region: str                     # e.g. "Khartoum", "Banadir"
    raw_data: Optional[str]         # Optional raw text report for Agent A
    interventions: List[str]        # Candidate interventions for Agent C

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
    # Markdown brief for the frontend
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
    #   "filters": {
    #       "country_iso3": "SDN",
    #       "region": "Khartoum",
    #       "mode": "semantic_region_filter"
    #   }
    # }
    retrieval_context: Optional[Dict[str, Any]]

    # ---- Explainability / interpretability ----
    # Structured reasoning tree for this run (built at the end)
    reasoning_tree: Optional[Dict[str, Any]]

    # Decision-friction prompts for human analysts
    decision_prompts: List[str]

    # Narrative evidence mapping (sections -> supporting events)
    narrative_evidence: Optional[List[Dict[str, Any]]]

    # ---- Auditing / versioning ----
    # Unique id for this analysis run
    run_id: Optional[str]

    # Path to the JSONL audit log file where this run is stored (if any)
    audit_log_path: Optional[str]

    # ---- Final explainability snapshot ----
    # Built by run_analysis via _build_explainability_payload(...)
    explainability: Optional[Dict[str, Any]]
