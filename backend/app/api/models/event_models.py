from typing import List, Optional
from pydantic import BaseModel

class Actor(BaseModel):
    name: str
    role: Optional[str] = None

class AnnotatedEvent(BaseModel):
    event_id: str
    date: str  # ISO 8601 date string (e.g., "2025-10-01T00:00:00Z")
    location: str  # Normalized location name
    actors: List[Actor]
    event_type: str  # Event code or category
    severity: Optional[float] = None  # e.g., Goldstein scale score
    sources: Optional[List[str]] = None  # Source URLs or references
    annotations: Optional[dict] = None  # Additional metadata or tags
