# app/explainability/models.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EvidenceItem:
    """Single piece of evidence supporting a reasoning step."""
    source: str                      # e.g. "GDELT", "trend_analysis", "validation"
    description: str                 # Human-readable description
    event: Optional[Dict[str, Any]] = None  # Optional structured event payload


@dataclass
class ReasoningNode:
    """A node in the reasoning tree."""
    id: str
    name: str
    description: str
    status: str                      # e.g. "completed", "skipped", "error"
    evidence: List[EvidenceItem] = field(default_factory=list)
    children: List["ReasoningNode"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the reasoning node (and children) to a pure-JSON dict."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "evidence": [
                {
                    "source": ev.source,
                    "description": ev.description,
                    "event": ev.event,
                }
                for ev in self.evidence
            ],
            "children": [child.to_dict() for child in self.children],
        }
