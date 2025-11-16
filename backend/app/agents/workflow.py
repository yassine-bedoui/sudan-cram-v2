# app/agents/workflow.py
from datetime import datetime
from collections import Counter
from typing import List, Optional, Dict

from langgraph.graph import StateGraph, END

from app.agents.state import SudanCRAMState
from app.agents.langgraph_agents import (
    rag_retrieval_node,
    event_extractor_node,
    trend_analyst_node,
    scenario_generator_node,
    consistency_checker_node,
    human_approval_node,
    should_request_human_input,
)


# ---- 1. Build LangGraph workflow ----

workflow = StateGraph(SudanCRAMState)

# Add nodes
workflow.add_node("rag_retrieval", rag_retrieval_node)
workflow.add_node("event_extractor", event_extractor_node)
workflow.add_node("trend_analyst", trend_analyst_node)
workflow.add_node("scenario_generator", scenario_generator_node)
workflow.add_node("consistency_checker", consistency_checker_node)
workflow.add_node("human_approval", human_approval_node)

# Define flow
workflow.set_entry_point("rag_retrieval")
workflow.add_edge("rag_retrieval", "event_extractor")
workflow.add_edge("event_extractor", "trend_analyst")
workflow.add_edge("trend_analyst", "scenario_generator")
workflow.add_edge("scenario_generator", "consistency_checker")
workflow.add_edge("consistency_checker", "human_approval")

# Conditional edge
workflow.add_conditional_edges(
    "human_approval",
    should_request_human_input,
    {"request_approval": END, "finalize": END},
)

# Compile
app = workflow.compile()


# ---- 2. Explainability helper  -----------------------------------------
# NEW: build a small, structured snapshot summarising what drove the result.

def _build_explainability(state: SudanCRAMState) -> Dict:
    """Create a lightweight explainability payload from the final state."""
    region = state.get("region")
    raw_data = state.get("raw_data")
    interventions = state.get("interventions") or []
    retrieved = state.get("retrieved_events") or []
    trend = state.get("trend_analysis") or {}
    scenarios = state.get("scenarios") or {}
    validation = state.get("validation") or {}
    confidence = float(state.get("confidence_score", 0.0))

    # --- Retrieval summary ---
    total_events = len(retrieved)
    sources_counter = Counter()
    dates = []

    for e in retrieved:
        meta = e.get("metadata") or {}
        src = meta.get("source", "UNKNOWN")
        sources_counter[src] += 1

        d_str = meta.get("date")
        if d_str:
            try:
                dates.append(datetime.fromisoformat(d_str))
            except Exception:
                # if format is weird, just skip
                pass

    time_span_days = None
    if dates:
        time_span_days = (max(dates) - min(dates)).days

    # --- Scenario summary ---
    scenario_list = scenarios.get("scenarios") or []
    recommendations = [
        s.get("recommendation")
        for s in scenario_list
        if s.get("recommendation")
    ]

    max_success = None
    max_risk = None
    if scenario_list:
        max_success = max(
            (s.get("optimistic", {}).get("success_probability", 0) for s in scenario_list),
            default=None,
        )
        max_risk = max(
            (s.get("pessimistic", {}).get("risk_probability", 0) for s in scenario_list),
            default=None,
        )

    # --- Validation summary ---
    issues = validation.get("issues") or []
    validation_status = validation.get("validation_status")
    overall_conf = validation.get("overall_confidence")

    # Package everything
    explainability = {
        "input": {
            "region": region,
            "has_raw_data": bool(raw_data),
            "interventions_count": len(interventions),
            "interventions": interventions,
        },
        "retrieval": {
            "total_events_considered": total_events,
            "sources": dict(sources_counter),
            "time_span_days": time_span_days,
        },
        "trend": {
            "trend_classification": trend.get("trend_classification"),
            "confidence_label": trend.get("confidence"),
            "drivers": trend.get("drivers") or [],
            "forecast_7_days": trend.get("forecast_7_days"),
        },
        "scenarios": {
            "num_scenarios": len(scenario_list),
            "recommendations": recommendations,
            "max_success_probability": max_success,
            "max_risk_probability": max_risk,
        },
        "validation": {
            "status": validation_status,
            "issue_count": len(issues),
            "issues": issues,
            "overall_confidence": overall_conf,
        },
        "meta": {
            "pipeline_confidence_score": confidence,
            "timestamp": state.get("timestamp"),
        },
    }

    return explainability


# ---- 3. Public entrypoint: run_analysis -------------------------------

def run_analysis(
    region: str,
    raw_data: Optional[str] = None,
    interventions: Optional[List[str]] = None,
) -> dict:
    print("\n" + "=" * 60)
    print(f"🚀 LANGGRAPH WORKFLOW START: {region}")
    print("=" * 60)

    initial_state: SudanCRAMState = {
        "region": region,
        "raw_data": raw_data,
        "interventions": interventions or [],
        "retrieved_events": [],
        "extracted_events": None,
        "trend_analysis": None,
        "scenarios": None,
        "validation": None,
        "human_approval_required": False,
        "approval_status": None,
        "messages": [],
        "confidence_score": 0.0,
        "timestamp": datetime.now().isoformat(),
        # NEW: initialise explainability to None; we populate it after the graph runs
        "explainability": None,
    }

    # Run LangGraph
    result: SudanCRAMState = app.invoke(initial_state)

    # Build explainability snapshot
    result["explainability"] = _build_explainability(result)

    print("\n" + "=" * 60)
    print("✅ WORKFLOW COMPLETE")
    print("=" * 60)

    return result
