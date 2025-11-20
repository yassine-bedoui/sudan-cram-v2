import uuid
from typing import List, Optional

from app.api.models.event_models import AnnotatedEvent, Actor
from app.core.state_name_normalizer import normalize_state_name
from app.core.actor_normalizer import normalize_actor
from app.services.vector_store import VectorStore

class EventExtractionAgent:
    """
    Agent responsible for extracting and annotating conflict events from raw input data.
    """

    def __init__(self):
        self.vector_store = VectorStore()
        self.scratchpad = []  # To hold iterative corrections or notes
        self.raw_events: Optional[List[dict]] = None

    def ingest(self, raw_events: List[dict]) -> None:
        """
        Ingest a list of raw event dictionaries for processing.

        :param raw_events: List of raw event data dicts
        """
        self.raw_events = raw_events

    def extract_events(self) -> List[AnnotatedEvent]:
        """
        Parse and normalize raw events into structured AnnotatedEvent objects.

        :return: List of AnnotatedEvent instances
        """
        if self.raw_events is None:
            return []

        extracted = []
        for raw in self.raw_events:
            event_id = str(uuid.uuid4())
            date = raw.get('date')
            loc_raw = raw.get('location', '')
            location = normalize_state_name(loc_raw)

            actors_raw = raw.get('actors', [])
            if not isinstance(actors_raw, list):
                # Defensive: if a single actor string, convert to list
                actors_raw = [actors_raw]

            actors = [Actor(name=normalize_actor(a)) for a in actors_raw if a]

            event_type = raw.get('event_code', 'UNKNOWN')
            severity = raw.get('severity', None)
            sources = raw.get('sources', None)
            annotations = raw.get('annotations', {})

            event = AnnotatedEvent(
                event_id=event_id,
                date=date,
                location=location,
                actors=actors,
                event_type=event_type,
                severity=severity,
                sources=sources,
                annotations=annotations
            )
            extracted.append(event)

        return extracted

    def annotate_events(self, events: List[AnnotatedEvent]) -> List[AnnotatedEvent]:
        """
        Placeholder for further event annotation or enrichment.
        Extend this method to add metadata such as event cause, sentiment, or links.

        :param events: List of AnnotatedEvent to enhance
        :return: Updated list of AnnotatedEvent
        """
        # For now, return as-is
        return events

    def self_correct(self, events: List[AnnotatedEvent]) -> List[AnnotatedEvent]:
        """
        Implement iterative self-correction logic using AI or rule-based methods.
        Adds events to scratchpad.

        :param events: AnnotatedEvent list to review and correct
        :return: Corrected list of AnnotatedEvent
        """
        self.scratchpad.append(events)
        # Future: implement AI feedback loop here
        return events

    def output(self, events: List[AnnotatedEvent]) -> None:
        """
        Store annotated events into vector store for semantic search and retrieval.

        :param events: List of AnnotatedEvent to save
        """
        for event in events:
            # Convert event to a summary text or JSON string for embedding
            event_text = f"{event.date} {event.location} {event.event_type} " \
                         f"{', '.join([actor.name for actor in event.actors])} " \
                         f"Severity: {event.severity}"
            
            vector = self.vector_store.embed_text(event_text)
            self.vector_store.upsert_event(event.event_id, vector, event.dict())

