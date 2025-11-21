# app/explainability/builder.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.agents.state import SudanCRAMState
from app.explainability.models import EvidenceItem, ReasoningNode


def _sample_events(events: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
    """Return the first few events as illustrative evidence."""
    return events[:limit]


def build_reasoning_tree(state: SudanCRAMState) -> Dict[str, Any]:
    """
    Build a structured reasoning tree for the analysis run.

    Each agent (RAG, A, B, C, D, E) becomes a node with:
      - description of what it did
      - evidence snippets (events, drivers, issues, logs)
    """
    events = state.get("events") or []
    trends = state.get("trend_analysis") or {}
    scenarios = state.get("scenarios") or {}
    validation = state.get("validation") or {}
    retrieval_context = state.get("retrieval_context") or {}
    messages = state.get("messages") or []
    narrative = state.get("narrative")

    # Root node
    root = ReasoningNode(
        id="root",
        name="SudanCRAM Analysis",
        description=f"End-to-end analysis for region {state.get('region')}",
        status="completed",
    )

    # ---- RAG Retrieval node ----
    filters = retrieval_context.get("filters") or {}
    mode = filters.get("mode") or "unknown"
    n_events = len(events)

    retrieval_node = ReasoningNode(
        id="rag_retrieval",
        name="Information Retrieval (RAG)",
        description=f"Retrieved {n_events} events using mode '{mode}'.",
        status="completed",
    )

    for ev in _sample_events(events, limit=3):
        retrieval_node.evidence.append(
            EvidenceItem(
                source=ev.get("source", "unknown"),
                description=(
                    f"{ev.get('date')} – {ev.get('event_type')} "
                    f"in {ev.get('region')} "
                    f"involving {', '.join(ev.get('actors', []) or [])}"
                ),
                event=ev,
            )
        )

    # ---- Agent A – Event Extraction ----
    ext = state.get("extracted_events")
    if ext is None:
        a_desc = "No raw_data provided; event extraction was skipped."
        a_status = "skipped"
    elif "error" in (ext or {}):
        a_desc = "Event extraction attempted but JSON parsing failed."
        a_status = "error"
    else:
        a_desc = f"Extracted {len(ext.get('events') or [])} events from raw text."
        a_status = "completed"

    event_node = ReasoningNode(
        id="event_extractor",
        name="Agent A – Event Extraction",
        description=a_desc,
        status=a_status,
    )

    # ---- Agent B – Trend & Forecast ----
    if not trends or "error" in (trends or {}):
        b_desc = "Trend analysis not available or failed."
        b_status = "error"
    else:
        b_desc = (
            f"Trend classified as {trends.get('trend_classification')} "
            f"with confidence {trends.get('confidence')}."
        )
        b_status = "completed"

    trend_node = ReasoningNode(
        id="trend_analyst",
        name="Agent B – Trend & Forecast",
        description=b_desc,
        status=b_status,
    )

    for driver in trends.get("drivers") or []:
        trend_node.evidence.append(
            EvidenceItem(
                source="trend_analysis",
                description=f"Driver: {driver}",
                event=None,
            )
        )

    forecast = (trends or {}).get("forecast_7_days") or {}
    if forecast:
        trend_node.evidence.append(
            EvidenceItem(
                source="trend_analysis",
                description=(
                    f"7-day forecast – armed_clash_likelihood="
                    f"{forecast.get('armed_clash_likelihood')}, "
                    f"civilian_targeting_likelihood="
                    f"{forecast.get('civilian_targeting_likelihood')}"
                ),
                event=None,
            )
        )

    # ---- Agent C – Scenario Generator ----
    scenario_list = (scenarios or {}).get("scenarios") or []
    if not scenario_list:
        c_desc = "No interventions provided; no scenarios were generated."
        c_status = "skipped"
    else:
        c_desc = f"Evaluated {len(scenario_list)} intervention scenarios."
        c_status = "completed"

    scenario_node = ReasoningNode(
        id="scenario_generator",
        name="Agent C – Scenario Generator",
        description=c_desc,
        status=c_status,
    )

    for s in scenario_list[:3]:
        scenario_node.evidence.append(
            EvidenceItem(
                source="scenario_generator",
                description=(
                    f"Intervention '{s.get('intervention')}': "
                    f"recommend {s.get('recommendation')} "
                    f"(success {((s.get('optimistic') or {}).get('success_probability'))}%, "
                    f"risk {((s.get('pessimistic') or {}).get('risk_probability'))}%)"
                ),
                event=None,
            )
        )

    # ---- Agent D – Consistency Checker ----
    val_status = (validation or {}).get("validation_status")
    if not validation or "error" in (validation or {}):
        d_desc = "Validation not available or failed."
        d_status = "error"
    else:
        d_desc = f"Validation status: {val_status}."
        d_status = "completed"

    validation_node = ReasoningNode(
        id="consistency_checker",
        name="Agent D – Consistency Checker",
        description=d_desc,
        status=d_status,
    )

    for issue in validation.get("issues") or []:
        validation_node.evidence.append(
            EvidenceItem(
                source="validation",
                description=f"{issue.get('type')}: {issue.get('description')}",
                event=None,
            )
        )

    # ---- Agent E – Narrative Generator ----
    if narrative:
        e_desc = "Generated a human-readable brief summarizing the assessment."
        e_status = "completed"
    else:
        e_desc = "Narrative brief not generated."
        e_status = "skipped"

    narrative_node = ReasoningNode(
        id="narrative",
        name="Agent E – Narrative Generator",
        description=e_desc,
        status=e_status,
    )

    # Attach last few log messages as evidence
    for msg in messages[-5:]:
        narrative_node.evidence.append(
            EvidenceItem(
                source="log",
                description=msg,
                event=None,
            )
        )

    # Final tree
    root.children = [
        retrieval_node,
        event_node,
        trend_node,
        scenario_node,
        validation_node,
        narrative_node,
    ]

    return root.to_dict()


def build_decision_prompts(state: SudanCRAMState) -> List[str]:
    """
    Generate 'decision friction' prompts that encourage analysts to question
    the model output before acting on it.
    """
    prompts: List[str] = []

    conf = float(state.get("confidence_score") or 0.0)
    validation = state.get("validation") or {}
    events = state.get("events") or []
    trends = state.get("trend_analysis") or {}

    # Low overall confidence
    if conf < 0.7:
        prompts.append(
            "Overall confidence is below 0.7. Which parts of this assessment "
            "would you want to double-check manually before acting?"
        )

    # Validation warnings / failures
    status = validation.get("validation_status")
    if status in {"WARNING", "FAILED"}:
        prompts.append(
            "Validation reported issues. Do you agree with the identified "
            "inconsistencies, or do they suggest a problem in the data or "
            "in the model's assumptions?"
        )

    # Possible data gaps
    if len(events) < 5:
        prompts.append(
            "The system only found a small number of recent events. Could "
            "there be missing data sources or reporting gaps for this region?"
        )

    # High short-term risk
    forecast = (trends or {}).get("forecast_7_days") or {}
    risk_candidates: List[float] = []
    for key in ("armed_clash_likelihood", "civilian_targeting_likelihood"):
        v = forecast.get(key)
        if isinstance(v, (int, float)):
            risk_candidates.append(float(v))

    if risk_candidates:
        max_risk = max(risk_candidates)
        if max_risk >= 70.0:
            prompts.append(
                "Short-term escalation risk is high. What contingency plans "
                "or alternative scenarios should be considered if this forecast "
                "turns out to be wrong?"
            )

    if not prompts:
        # Always provide at least one generic reflection prompt
        prompts.append(
            "Which assumption in this assessment, if wrong, would most change "
            "your decision?"
        )

    return prompts


def build_narrative_evidence(state: SudanCRAMState) -> List[Dict[str, Any]]:
    """
    Provide a simple mapping from narrative sections to supporting events.

    This is a lightweight 'citation' mechanism: the frontend can show
    which concrete events underlie each narrative section.
    """
    narrative = state.get("narrative")
    if not narrative:
        return []

    events = state.get("events") or []
    top_events = events[:5]

    lines = narrative.splitlines()
    sections: List[Dict[str, Any]] = []

    current_header = "Full narrative"
    current_lines: List[str] = []

    def _flush_section():
        if not current_lines:
            return
        text = "\n".join(current_lines).strip()
        if not text:
            return
        sections.append(
            {
                "section_id": current_header.lower().replace(" ", "_"),
                "section_label": current_header,
                "text": text,
            }
        )

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            # New section
            _flush_section()
            # Remove leading '#' characters and whitespace
            header = stripped.lstrip("#").strip()
            current_header = header or current_header
            current_lines = []
        else:
            current_lines.append(line)

    _flush_section()

    # Attach supporting events to each section. For now we use the same
    # top events for all sections; the frontend can refine if needed.
    narrative_evidence: List[Dict[str, Any]] = []
    for sec in sections:
        narrative_evidence.append(
            {
                "section_id": sec["section_id"],
                "section_label": sec["section_label"],
                "text": sec["text"],
                "supporting_events": top_events,
            }
        )

    return narrative_evidence
