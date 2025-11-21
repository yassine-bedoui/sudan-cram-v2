from datetime import datetime
import json
import os
from typing import Any, Dict, List, Optional

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from app.agents.state import SudanCRAMState
from app.services.vector_store import VectorStore

# 🔹 NEW: Explainability helpers & audit logger
from app.explainability.builder import (
    build_reasoning_tree,
    build_decision_prompts,
    build_narrative_evidence,
)
from app.explainability.logger import (
    log_analysis_run,
    get_model_and_data_metadata,
)


# ---- 1. LLM + Vector Store setup (LAZY, for fast startup) ----
# We keep *only* lightweight globals at import time. Heavy objects are created on-demand.

_llm: Optional[ChatOllama] = None
_vector_store: Optional[VectorStore] = None


def _get_llm() -> ChatOllama:
    """
    Lazily initialize the LLM client.

    This avoids hitting the Ollama server at import time, which can slow down or
    break startup on platforms like Render if the model server is slow/unavailable.
    """
    global _llm
    if _llm is None:
        print("🧠 Initializing LLM client (lazy)...")
        _llm = ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "qwen2.5:14b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.7,
        )
    return _llm


def _get_vector_store() -> VectorStore:
    """
    Lazily initialize the VectorStore.

    This avoids heavy embedding/model loading at import time, which can cause
    cloud platforms like Render to think the service isn't listening on a port yet.
    """
    global _vector_store
    if _vector_store is None:
        print("🔧 Initializing Vector Store (lazy)...")
        _vector_store = VectorStore()
    return _vector_store


# ---- Small helper: build canonical events timeline ----


def _build_events_timeline_from_retrieved(
    retrieved_events: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Turn raw vector-store hits into a canonical events timeline.

    ✅ Deduplicates events so the same GDELT row (same db_id/event_id) does not appear twice.
    """
    events_timeline: List[Dict[str, Any]] = []
    seen_keys = set()

    # Sort by date for temporal coherence
    for e in sorted(
        retrieved_events,
        key=lambda x: x.get("metadata", {}).get("date", ""),
    ):
        meta = e.get("metadata", {}) or {}

        source = meta.get("source", "GDELT")
        db_id = meta.get("db_id")
        event_id = meta.get("event_id")

        # Prefer a stable numerical / string id for deduplication
        if db_id is not None:
            key = (source, "db_id", db_id)
        elif event_id is not None:
            key = (source, "event_id", event_id)
        else:
            # Fallback to a composite key if ids are missing
            key = (
                source,
                meta.get("date"),
                meta.get("region"),
                meta.get("event_type"),
                tuple(meta.get("actors", []) or []),
            )

        if key in seen_keys:
            # Skip duplicates
            continue
        seen_keys.add(key)

        events_timeline.append(
            {
                "date": meta.get("date"),
                "source": source,
                "region": meta.get("region"),
                "event_type": meta.get("event_type"),
                "actors": meta.get("actors", []),
                "fatalities": meta.get("fatalities"),
            }
        )

    return events_timeline


# ---- 2. Nodes ----


def rag_retrieval_node(state: SudanCRAMState) -> SudanCRAMState:
    """
    Retrieve relevant events from Qdrant for the given region.

    ✅ Behavior:
    - Try exact payload filter on region field first: {"region": region}
    - If that fails, run Sudan-wide semantic search and THEN:
        • If region provided: prefer hits whose metadata.region contains the region string.
        • Otherwise: treat as national context.
    - Store retrieval query + filter mode in `state["retrieval_context"]` for explainability.
    """
    print("\n🔍 RAG Retrieval...")

    vs = _get_vector_store()
    region_raw = state.get("region") or ""
    region = region_raw.strip()

    # Base query text
    if region:
        query_text = f"recent conflict events in {region}"
    else:
        query_text = "recent conflict events in Sudan"

    results: List[Dict[str, Any]] = []
    retrieval_filters_for_log: Dict[str, Any] = {}

    # 1) Try region-focused search with exact filter on payload["region"]
    if region:
        try:
            strict_filter = {"region": region}
            region_results = vs.semantic_search(
                query=query_text,
                filters=strict_filter,
                top_k=20,
            )
        except Exception as e:
            state["messages"].append(f"⚠️ Region-filtered RAG search error: {e}")
            region_results = []

        if region_results:
            # We actually got exact region hits
            results = region_results
            retrieval_filters_for_log = {
                "region": region,
                "mode": "region_exact",
            }
            state["messages"].append(
                f"Retrieved {len(results)} region-focused events for {region} (exact filter)"
            )
        else:
            state["messages"].append(
                "No region-specific matches from exact filter; using semantic fallback"
            )

    # 2) Fallback / main search if no region-specific results yet
    if not results:
        try:
            # Ask for a few more results so semantic region-filtering has material
            fallback_results = vs.semantic_search(
                query=query_text,
                filters=None,
                top_k=50,
            )
        except Exception as e:
            state["messages"].append(f"⚠️ Fallback RAG search error: {e}")
            fallback_results = []

        if region and fallback_results:
            # Try to emulate region-specific behavior by checking substring inside metadata.region
            region_lower = region.lower()
            region_semantic = [
                r
                for r in fallback_results
                if region_lower
                in str(r.get("metadata", {}).get("region", "")).lower()
            ]

            if region_semantic:
                results = region_semantic[:20]
                retrieval_filters_for_log = {
                    "region": region,
                    "mode": "semantic_region_filter",
                }
                state["messages"].append(
                    f"Retrieved {len(results)} region-focused events for {region} (semantic filter)"
                )
            else:
                # Nothing clearly region-specific → treat as national context
                results = fallback_results
                retrieval_filters_for_log = {
                    "region": "Sudan",
                    "mode": "national_fallback",
                }
                state["messages"].append(
                    "No region-specific matches; used Sudan-wide context instead"
                )
                state["messages"].append(
                    f"Retrieved {len(results)} events for region {region}"
                )
        else:
            # No region given OR no results at all
            results = fallback_results
            retrieval_filters_for_log = {
                "region": "Sudan" if region else "Sudan (no_region_specified)",
                "mode": "national" if region else "national_no_region",
            }
            state["messages"].append(
                f"Retrieved {len(results)} Sudan-wide events "
                f"({'no region specified' if not region else 'fallback'})"
            )

    state["retrieved_events"] = results

    # ✅ Build canonical events timeline early so all downstream nodes see it
    events_timeline = _build_events_timeline_from_retrieved(results)
    state["events"] = events_timeline

    # ✅ Stash retrieval metadata for explainability
    state["retrieval_context"] = {
        "query": query_text,
        "filters": retrieval_filters_for_log,
    }

    return state


def event_extractor_node(state: SudanCRAMState) -> SudanCRAMState:
    """Extract structured events from raw text, using retrieved events as context."""
    print("\n📝 Event Extractor...")

    raw = state.get("raw_data")
    if not raw:
        state["extracted_events"] = None
        state["messages"].append("No raw_data provided; skipping event extraction")
        return state

    llm = _get_llm()

    # Use a few retrieved events as context for the LLM
    context_lines: List[str] = []
    for e in state.get("retrieved_events", [])[:5]:
        meta = e.get("metadata", {}) or {}
        event_type = meta.get("event_type", "unknown")
        actors = meta.get("actors", [])
        context_lines.append(f"- {event_type}: {actors}")

    context = "\n".join(context_lines)

    prompt = f"""
You are an analyst extracting conflict events from reports.

CONTEXT (recent similar events):
{context}

TEXT TO ANALYZE:
{raw}

Extract events as JSON. Use this exact schema:

{{
  "events": [
    {{
      "event_type": "string",
      "date": "YYYY-MM-DD or null",
      "location": "string or null",
      "actors": ["Actor A", "Actor B"],
      "fatalities": 0
    }}
  ],
  "confidence": 0.0
}}
"""

    response = llm.invoke(
        [
            SystemMessage(content="Extract conflict events from the text. Output JSON ONLY."),
            HumanMessage(content=prompt),
        ]
    )

    try:
        result = json.loads(response.content)
        state["extracted_events"] = result
        n = len(result.get("events", []))
        state["messages"].append(f"Extracted {n} events from raw_data")
    except Exception as e:
        state["extracted_events"] = {"error": "parse_failed", "raw": response.content}
        state["messages"].append(f"⚠️ Event extraction JSON parse failed: {e}")

    return state


def trend_analyst_node(state: SudanCRAMState) -> SudanCRAMState:
    """Analyze trends using the retrieved events timeline."""
    print("\n📊 Trend Analyst...")

    llm = _get_llm()

    # Build a simple timeline summary directly from retrieved_events
    timeline_lines: List[str] = []
    for e in sorted(
        state.get("retrieved_events", []),
        key=lambda x: x.get("metadata", {}).get("date", ""),
    )[:15]:
        meta = e.get("metadata", {}) or {}
        date = meta.get("date", "unknown_date")
        event_type = meta.get("event_type", "unknown_type")
        fatalities = meta.get("fatalities")
        if fatalities is None:
            fat_str = "fatalities unknown"
        else:
            fat_str = f"{fatalities} fatalities"
        timeline_lines.append(f"{date}: {event_type} ({fat_str})")

    timeline = "\n".join(timeline_lines)

    prompt = f"""
You are a conflict trend analyst for Sudan.

REGION: {state['region']}

EVENT TIMELINE:
{timeline}

Analyze trends and produce JSON ONLY in this schema:

{{
  "trend_classification": "ESCALATING" | "STABLE" | "DEESCALATING" | "VOLATILE",
  "drivers": ["short bullet point string", "..."],
  "forecast_7_days": {{
    "armed_clash_likelihood": 0-100,
    "civilian_targeting_likelihood": 0-100
  }},
  "confidence": "LOW" | "MEDIUM" | "HIGH"
}}
"""

    response = llm.invoke(
        [
            SystemMessage(content="Analyze conflict trends and output JSON ONLY."),
            HumanMessage(content=prompt),
        ]
    )

    try:
        result = json.loads(response.content)
        state["trend_analysis"] = result
        state["messages"].append(
            f"Trend classification: {result.get('trend_classification', 'UNKNOWN')}"
        )
    except Exception as e:
        state["trend_analysis"] = {"error": "parse_failed", "raw": response.content}
        state["messages"].append(f"⚠️ Trend analysis JSON parse failed: {e}")

    return state


def scenario_generator_node(state: SudanCRAMState) -> SudanCRAMState:
    """Generate intervention scenarios."""
    print("\n🔮 Scenario Generator...")

    interventions = state.get("interventions")
    if not interventions:
        state["scenarios"] = None
        state["messages"].append(
            "No interventions provided; skipping scenario generation"
        )
        return state

    llm = _get_llm()
    trend = state.get("trend_analysis")

    prompt = f"""
You are advising on conflict response options in {state['region']}.

CURRENT TREND (may be null):
{json.dumps(trend, ensure_ascii=False, indent=2)}

INTERVENTIONS TO EVALUATE:
{chr(10).join(f"- {i}" for i in interventions)}

Return JSON ONLY with this schema:

{{
  "scenarios": [
    {{
      "intervention": "string",
      "optimistic": {{
        "description": "string",
        "success_probability": 0-100
      }},
      "pessimistic": {{
        "description": "string",
        "risk_probability": 0-100
      }},
      "recommendation": "PROCEED" | "MODIFY" | "AVOID"
    }}
  ]
}}
"""

    response = llm.invoke(
        [
            SystemMessage(content="Generate policy scenarios and output JSON ONLY."),
            HumanMessage(content=prompt),
        ]
    )

    try:
        result = json.loads(response.content)
        state["scenarios"] = result
        n = len(result.get("scenarios", []))
        state["messages"].append(f"Generated {n} scenarios")
    except Exception as e:
        state["scenarios"] = {"error": "parse_failed", "raw": response.content}
        state["messages"].append(f"⚠️ Scenario generation JSON parse failed: {e}")

    return state


def consistency_checker_node(state: SudanCRAMState) -> SudanCRAMState:
    """Check for contradictions and produce an overall confidence score."""
    print("\n✅ Consistency Checker...")

    llm = _get_llm()

    events = state.get("events") or []
    trends = state.get("trend_analysis") or {}
    scenarios = state.get("scenarios") or {}

    # ---- Heuristic: detect "STABLE trend + high escalation risk" ----
    max_escalation_prob: Optional[float] = None

    # 1) From trend forecast (armed clashes / civilian targeting)
    forecast = (trends or {}).get("forecast_7_days") or {}
    for key in ("armed_clash_likelihood", "civilian_targeting_likelihood"):
        v = forecast.get(key)
        if isinstance(v, (int, float)):
            max_escalation_prob = (
                v if max_escalation_prob is None else max(max_escalation_prob, v)
            )

    # 2) From pessimistic scenario risk probabilities
    for s in (scenarios.get("scenarios") or []):
        pess = (s or {}).get("pessimistic") or {}
        rp = pess.get("risk_probability")
        if isinstance(rp, (int, float)):
            max_escalation_prob = (
                rp if max_escalation_prob is None else max(max_escalation_prob, rp)
            )

    trend_label = trends.get("trend_classification")
    escalation_flag_threshold = 60  # can be tuned later

    stable_with_high_escalation = (
        trend_label == "STABLE"
        and max_escalation_prob is not None
        and max_escalation_prob >= escalation_flag_threshold
    )

    consistency_hints: Dict[str, Any] = {
        "trend_classification": trend_label,
        "max_escalation_probability": max_escalation_prob,
        "stable_with_high_escalation": stable_with_high_escalation,
        "escalation_flag_threshold": escalation_flag_threshold,
        "num_events": len(events),
    }

    payload = {
        "events": events,
        "trends": trends,
        "scenarios": scenarios,
        "consistency_hints": consistency_hints,
    }

    prompt = f"""
You are checking internal consistency of a conflict risk analysis.

DATA (JSON):
{json.dumps(payload, ensure_ascii=False, indent=2)}

Guidelines (important):

1) About the events list:
- If "events" is null or an empty list, you may treat this as a DATA_GAP.
- If "events" contains items, DO NOT say it is null or missing. Instead, treat it as observed data.

2) About escalation vs trend:
- The field "consistency_hints.stable_with_high_escalation" indicates whether the system detected:
  • trend_classification == "STABLE"
  • AND a high max escalation probability (>= consistency_hints.escalation_flag_threshold)
- If this flag is true, you MUST treat this as a likely inconsistency between:
  • the trend label ("STABLE"), and
  • the escalation probabilities (forecast and/or scenario risk probabilities).
- In that case, explicitly state in "issues" whether:
  • the trend label is probably too mild and should be closer to "VOLATILE" or "ESCALATING", OR
  • the escalation probabilities (forecast and/or scenarios) are probably too high for a truly "STABLE" trend.

3) General rules:
- Base your reasoning strictly on the DATA above (do not invent fields).
- Focus on mismatches between:
  • events (if present),
  • trend classification and probabilities,
  • scenario success / risk probabilities.
- If everything is internally coherent, you may return "PASSED" with no issues.

Return JSON ONLY:

{{
  "validation_status": "PASSED" | "WARNING" | "FAILED",
  "issues": [
    {{
      "type": "INCONSISTENCY" | "DATA_GAP",
      "description": "string",
      "severity": "LOW" | "MEDIUM" | "HIGH"
    }}
  ],
  "overall_confidence": 0.0-1.0
}}
"""

    response = llm.invoke(
        [
            SystemMessage(content="Validate consistency and output JSON ONLY."),
            HumanMessage(content=prompt),
        ]
    )

    try:
        result = json.loads(response.content)
        state["validation"] = result
        state["confidence_score"] = float(result.get("overall_confidence", 0.5))
        state["messages"].append(
            f"Validation: {result.get('validation_status', 'UNKNOWN')} "
            f"(confidence={state['confidence_score']:.2f})"
        )
    except Exception as e:
        state["validation"] = {"error": "parse_failed", "raw": response.content}
        state["confidence_score"] = 0.5
        state["messages"].append(f"⚠️ Validation JSON parse failed: {e}")

    return state


def human_approval_node(state: SudanCRAMState) -> SudanCRAMState:
    """Decide if human approval is required based on confidence."""
    print("\n👤 Human Approval Check...")

    conf = state.get("confidence_score", 0.0)

    if conf < 0.7:
        state["human_approval_required"] = True
        state["approval_status"] = "pending"
        state["messages"].append(
            f"⚠️ Human approval required (confidence={conf:.2f})"
        )
    else:
        state["human_approval_required"] = False
        state["approval_status"] = "auto-approved"
        state["messages"].append(
            f"✅ Auto-approved (confidence={conf:.2f})"
        )

    return state


def should_request_human_input(state: SudanCRAMState) -> str:
    """
    Routing function for LangGraph conditional edge.

    Use the same confidence threshold as human_approval_node.
    """
    conf = state.get("confidence_score", 0.0)
    return "request_approval" if conf < 0.7 else "finalize"


def narrative_generator_node(state: SudanCRAMState) -> SudanCRAMState:
    """
    Agent E – Narrative Generator.

    Turns structured outputs (events, trends, scenarios, validation) into
    a polished human brief (Markdown) for the frontend.
    """
    print("\n📰 Narrative Generator...")

    llm = _get_llm()

    region = state.get("region") or "the region"
    events = state.get("events") or []
    trends = state.get("trend_analysis") or {}
    scenarios = state.get("scenarios") or {}
    validation = state.get("validation") or {}
    approval_status = state.get("approval_status")

    # For the prompt, we pass a compact JSON snapshot
    payload = {
        "region": region,
        "events": events,
        "trend_analysis": trends,
        "scenarios": scenarios,
        "validation": validation,
        "approval_status": approval_status,
        "confidence_score": state.get("confidence_score"),
    }

    prompt = f"""
You are Agent E, a narrative generator for a conflict risk dashboard.

Your job is to turn structured analysis (events, trends, scenarios, validation)
into a concise, policy-friendly brief for analysts and decision-makers.

Region: {region}

Structured DATA (JSON):
{json.dumps(payload, ensure_ascii=False, indent=2)}

Write a clear, neutral, and non-technical brief in **Markdown** with these sections:

1. **Situation Overview**
   - 2–4 sentences describing the current situation in {region}.

2. **Recent Conflict Events**
   - 3–6 bullet points highlighting the most relevant recent events
     (dates, who was involved, and what happened). Focus on patterns.

3. **Trend & Risk Outlook (Next 7 Days)**
   - Explain the trend classification (e.g. ESCALATING, STABLE) in plain language.
   - Summarize armed_clash_likelihood and civilian_targeting_likelihood
     as qualitative risk levels (e.g. low / moderate / high).

4. **Scenarios & Recommendations**
   - If scenarios are present, summarize the main intervention options and their
     optimistic vs pessimistic outcomes.
   - If no scenarios are available, say that no specific interventions were evaluated.

5. **Confidence & Data Notes**
   - Reflect the validation_status and overall confidence.
   - Note any key caveats or data gaps (e.g. limited events, model uncertainty).
   - If approval_status is "pending", clearly mention that human review is required
     before using this assessment for high-stakes decisions.

Style requirements:
- 300–600 words.
- Use simple language, short paragraphs, and bullet points where helpful.
- Do NOT include any JSON in the output.
- Do NOT talk about yourself; just present the assessment.
"""

    response = llm.invoke(
        [
            SystemMessage(
                content=(
                    "You are a professional conflict analyst writing briefs for a dashboard. "
                    "Always answer in Markdown only."
                )
            ),
            HumanMessage(content=prompt),
        ]
    )

    narrative_text = response.content if isinstance(response.content, str) else str(response.content)
    state["narrative"] = narrative_text
    state["messages"].append("Generated narrative brief for frontend")

    return state


# ---- 3. Graph wiring ----

builder = StateGraph(SudanCRAMState)

builder.add_node("rag_retrieval", rag_retrieval_node)
builder.add_node("event_extractor", event_extractor_node)
builder.add_node("trend_analyst", trend_analyst_node)
builder.add_node("scenario_generator", scenario_generator_node)
builder.add_node("consistency_checker", consistency_checker_node)
builder.add_node("human_approval", human_approval_node)
builder.add_node("narrative_generator", narrative_generator_node)

builder.set_entry_point("rag_retrieval")
builder.add_edge("rag_retrieval", "event_extractor")
builder.add_edge("event_extractor", "trend_analyst")
builder.add_edge("trend_analyst", "scenario_generator")
builder.add_edge("scenario_generator", "consistency_checker")

# After consistency check, either go to human_approval or directly to narrative
builder.add_conditional_edges(
    "consistency_checker",
    should_request_human_input,
    {
        "request_approval": "human_approval",
        "finalize": "narrative_generator",
    },
)

# If human approval is required, narrative comes after that
builder.add_edge("human_approval", "narrative_generator")

# Narrative is the last step before finishing
builder.add_edge("narrative_generator", END)

app = builder.compile()


# ---- 4. Explainability helper ----


def _build_explainability_payload(state: SudanCRAMState) -> Dict[str, Any]:
    events = state.get("events") or []
    trends = state.get("trend_analysis") or {}
    scenarios = state.get("scenarios") or {}
    validation = state.get("validation") or {}
    retrieval_context = state.get("retrieval_context") or {}

    # Time span in days based on events
    if events:
        dates = [e.get("date") for e in events if e.get("date")]
        try:
            parsed = [datetime.fromisoformat(d) for d in dates]
            time_span_days = (max(parsed) - min(parsed)).days
        except Exception:
            time_span_days = None
    else:
        time_span_days = None

    # Scenario stats
    scenario_list = scenarios.get("scenarios") or []
    max_success: Optional[float] = None
    max_risk: Optional[float] = None
    recs: List[str] = []
    for s in scenario_list:
        optimistic = (s or {}).get("optimistic") or {}
        pessimistic = (s or {}).get("pessimistic") or {}
        success_prob = optimistic.get("success_probability")
        risk_prob = pessimistic.get("risk_probability")
        if success_prob is not None:
            max_success = (
                success_prob if max_success is None else max(max_success, success_prob)
            )
        if risk_prob is not None:
            max_risk = (
                risk_prob if max_risk is None else max(max_risk, risk_prob)
            )
        rec = (s or {}).get("recommendation")
        if rec:
            recs.append(rec)

    # 🔹 NEW: reasoning artefacts
    reasoning_tree = build_reasoning_tree(state)
    decision_prompts = build_decision_prompts(state)
    narrative_evidence = build_narrative_evidence(state)

    explainability: Dict[str, Any] = {
        "input": {
            "region": state.get("region"),
            "has_raw_data": bool(state.get("raw_data")),
            "interventions_count": len(state.get("interventions") or []),
            "interventions": state.get("interventions") or [],
        },
        "retrieval": {
            "total_events_considered": len(events),
            "sources": {
                "GDELT": len(events),
            },
            "time_span_days": time_span_days,
            "query": retrieval_context.get("query"),
            "filters": retrieval_context.get("filters") or {},
        },
        "trend": {
            "trend_classification": trends.get("trend_classification"),
            "confidence_label": trends.get("confidence"),
            "drivers": trends.get("drivers") or [],
            "forecast_7_days": trends.get("forecast_7_days") or {},
        },
        "scenarios": {
            "num_scenarios": len(scenario_list),
            "recommendations": recs,
            "max_success_probability": max_success,
            "max_risk_probability": max_risk,
        },
        "validation": {
            "status": validation.get("validation_status"),
            "issue_count": len(validation.get("issues") or []),
            "issues": validation.get("issues") or [],
            "overall_confidence": validation.get("overall_confidence"),
        },
        # 🔹 NEW: structured reasoning & narrative evidence
        "reasoning": {
            "tree": reasoning_tree,
            "decision_prompts": decision_prompts,
            "narrative_evidence": narrative_evidence,
        },
        "meta": {
            "pipeline_confidence_score": state.get("confidence_score"),
            "timestamp": datetime.utcnow().isoformat(),
            # 🔹 NEW: model & data provenance
            "models": get_model_and_data_metadata(),
        },
    }

    return explainability


# ---- 5. Public API ----


def run_analysis(
    region: str,
    raw_data: Optional[str] = None,
    interventions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Entry point used by both CLI and FastAPI to run the workflow."""
    print("\n" + "=" * 60)
    print(f"🚀 LANGGRAPH WORKFLOW START: {region}")
    print("=" * 60)

    initial_state: SudanCRAMState = {
        "region": region,
        "raw_data": raw_data,
        "interventions": interventions or [],

        # RAG context
        "retrieved_events": [],
        "events": [],

        # Agent outputs
        "extracted_events": None,
        "trend_analysis": None,
        "scenarios": None,
        "validation": None,
        "narrative": None,

        # Control
        "human_approval_required": False,
        "approval_status": None,

        # Metadata
        "messages": [],
        "confidence_score": 0.0,
        "timestamp": datetime.utcnow().isoformat(),

        # RAG metadata for explainability (will be overwritten in rag_retrieval_node)
        "retrieval_context": None,

        # Explainability snapshot (final)
        "explainability": None,
    }

    final_state = app.invoke(initial_state)

    # Ensure events timeline is set from retrieved_events (authoritative)
    retrieved_events = final_state.get("retrieved_events") or []
    final_state["events"] = _build_events_timeline_from_retrieved(retrieved_events)

    print("\n" + "=" * 60)
    print("✅ WORKFLOW COMPLETE")
    print("=" * 60)

    # Deduplicate messages while preserving order
    seen = set()
    dedup_messages: List[str] = []
    for m in final_state.get("messages", []):
        if m not in seen:
            seen.add(m)
            dedup_messages.append(m)

    # 🔹 Build explainability bundle (includes reasoning tree, prompts, evidence)
    explainability = _build_explainability_payload(final_state)
    timestamp = explainability["meta"]["timestamp"]

    # 🔹 Audit log: store full reasoning session + explainability
    payload_to_log = {
        "state": final_state,
        "explainability": explainability,
    }
    run_id, audit_log_path = log_analysis_run(payload_to_log)

    # Attach audit info back into explainability meta
    explainability["meta"]["run_id"] = run_id
    explainability["meta"]["audit_log_path"] = audit_log_path

    return {
        "region": final_state["region"],
        "raw_data": final_state.get("raw_data"),
        "interventions": final_state.get("interventions") or [],
        "retrieved_events": retrieved_events,
        "events": final_state.get("events") or [],
        "trend_analysis": final_state.get("trend_analysis"),
        "scenarios": final_state.get("scenarios"),
        "validation": final_state.get("validation"),
        "approval_status": final_state.get("approval_status"),
        "confidence_score": final_state.get("confidence_score", 0.0),
        "messages": dedup_messages,
        "timestamp": timestamp,
        "explainability": explainability,
        # 🔹 Agent E output for the frontend:
        "narrative": final_state.get("narrative"),
        # 🔹 Audit info so the UI can link to logs if needed
        "run_id": run_id,
        "audit_log_path": audit_log_path,
    }
