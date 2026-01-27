"""
Temporal reasoner - orchestrates temporal reasoning.

Combines parsing, constraint networks, and validation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from inception.enhance.synthesis.temporal.relations import (
    AllenRelation,
    TemporalRelation,
    relation_from_timestamps,
)
from inception.enhance.synthesis.temporal.parser import TemporalParser, TemporalExpression
from inception.enhance.synthesis.temporal.network import (
    TemporalNetwork,
    TemporalConstraint,
    InferredRelation,
    Inconsistency,
)

logger = logging.getLogger(__name__)


@dataclass
class TemporalFact:
    """A fact with temporal scope."""
    
    subject_nid: int
    predicate: str
    object_nid: int | None = None
    object_value: str | None = None
    
    # Temporal scope
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    
    # Metadata
    confidence: float = 1.0
    source_nids: list[int] = field(default_factory=list)
    
    @property
    def is_eternally_valid(self) -> bool:
        """Check if fact has no temporal bounds."""
        return self.valid_from is None and self.valid_to is None
    
    @property
    def is_currently_valid(self) -> bool:
        """Check if fact is currently valid."""
        now = datetime.now()
        
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        
        return True
    
    def overlaps(self, other: "TemporalFact") -> bool:
        """Check if two facts have overlapping validity."""
        if self.is_eternally_valid or other.is_eternally_valid:
            return True
        
        # Check for overlap
        if self.valid_from and other.valid_to:
            if self.valid_from > other.valid_to:
                return False
        if self.valid_to and other.valid_from:
            if self.valid_to < other.valid_from:
                return False
        
        return True


@dataclass
class TemporalReasoningResult:
    """Result of temporal reasoning."""
    
    facts_processed: int
    events_identified: int
    constraints_added: int
    inferences_made: int
    inconsistencies_found: int
    
    @property
    def has_inconsistencies(self) -> bool:
        return self.inconsistencies_found > 0


class TemporalReasoner:
    """
    Orchestrates temporal reasoning.
    
    Capabilities:
    - Extract temporal expressions from text
    - Build constraint network from events
    - Infer temporal relationships
    - Validate temporal consistency
    - Track fact validity over time
    """
    
    def __init__(
        self,
        parser: TemporalParser | None = None,
        network: TemporalNetwork | None = None,
    ):
        """Initialize temporal reasoner."""
        self.parser = parser or TemporalParser()
        self.network = network or TemporalNetwork()
        
        self._facts: dict[int, list[TemporalFact]] = {}  # By subject NID
    
    def add_event(
        self,
        nid: int,
        text: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[InferredRelation]:
        """
        Add an event to the temporal network.
        
        Args:
            nid: Event node ID
            text: Event text (may contain temporal expressions)
            start: Start time (if known)
            end: End time (if known)
        
        Returns:
            Any newly inferred relations
        """
        # Parse temporal expressions from text if times not provided
        if not start:
            expressions = self.parser.parse(text)
            if expressions:
                start = expressions[0].start
                if expressions[0].end:
                    end = expressions[0].end
        
        # Find constraints with existing events
        inferred = []
        
        if start:
            for existing_nid in self.network.events:
                existing_constraint = self.network.get_constraint(existing_nid, nid)
                
                if not existing_constraint:
                    # Try to determine relation
                    # Get existing event's time (would need to store this)
                    pass
        
        return inferred
    
    def add_temporal_relation(
        self,
        event1_nid: int,
        event2_nid: int,
        relation: AllenRelation | str,
        confidence: float = 1.0,
    ) -> list[InferredRelation]:
        """
        Add a temporal relation between events.
        
        Args:
            event1_nid: First event NID
            event2_nid: Second event NID
            relation: Allen relation or string name
            confidence: Confidence in relation
        
        Returns:
            Newly inferred relations from propagation
        """
        if isinstance(relation, str):
            relation = AllenRelation[relation.upper()]
        
        constraint = TemporalConstraint(
            event1_nid=event1_nid,
            event2_nid=event2_nid,
            relation=relation,
            confidence=confidence,
        )
        
        return self.network.add_constraint(constraint)
    
    def add_temporal_fact(self, fact: TemporalFact) -> None:
        """Add a temporal fact."""
        if fact.subject_nid not in self._facts:
            self._facts[fact.subject_nid] = []
        self._facts[fact.subject_nid].append(fact)
    
    def get_facts_at_time(
        self,
        subject_nid: int,
        time: datetime,
    ) -> list[TemporalFact]:
        """Get facts valid at a specific time."""
        facts = self._facts.get(subject_nid, [])
        
        return [
            f for f in facts
            if (f.valid_from is None or f.valid_from <= time) and
               (f.valid_to is None or f.valid_to >= time)
        ]
    
    def get_current_facts(self, subject_nid: int) -> list[TemporalFact]:
        """Get currently valid facts for a subject."""
        return self.get_facts_at_time(subject_nid, datetime.now())
    
    def order_events(
        self,
        event_nids: list[int],
    ) -> list[int]:
        """
        Order events temporally using network constraints.
        
        Args:
            event_nids: NIDs of events to order
        
        Returns:
            NIDs in temporal order (earliest first)
        """
        if len(event_nids) <= 1:
            return event_nids
        
        # Build ordering from constraints
        before_count: dict[int, int] = {nid: 0 for nid in event_nids}
        
        for e1 in event_nids:
            for e2 in event_nids:
                if e1 == e2:
                    continue
                
                constraint = self.network.get_constraint(e1, e2)
                if constraint:
                    if constraint.relation in (
                        AllenRelation.BEFORE,
                        AllenRelation.MEETS,
                    ):
                        # e1 is before e2
                        before_count[e2] = before_count.get(e2, 0) + 1
                    elif constraint.relation in (
                        AllenRelation.AFTER,
                        AllenRelation.MET_BY,
                    ):
                        # e1 is after e2
                        before_count[e1] = before_count.get(e1, 0) + 1
        
        # Sort by before count (fewer = earlier)
        return sorted(event_nids, key=lambda n: before_count.get(n, 0))
    
    def validate_consistency(self) -> list[Inconsistency]:
        """
        Validate temporal consistency.
        
        Returns:
            List of inconsistencies
        """
        # Propagate to find inconsistencies
        self.network.propagate()
        return self.network.get_inconsistencies()
    
    def infer_relations(self) -> list[InferredRelation]:
        """
        Infer all possible relations.
        
        Returns:
            All inferred relations
        """
        self.network.propagate()
        return self.network.get_inferred()
    
    def reason_about_events(
        self,
        events: list[tuple[int, str, datetime | None, datetime | None]],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> TemporalReasoningResult:
        """
        Perform full temporal reasoning on a set of events.
        
        Args:
            events: List of (nid, text, start, end) tuples
            progress_callback: Progress callback
        
        Returns:
            Reasoning result
        """
        constraints_added = 0
        
        # Add all events and build initial constraints
        event_times: dict[int, tuple[datetime | None, datetime | None]] = {}
        
        for i, (nid, text, start, end) in enumerate(events):
            if progress_callback:
                progress_callback(i + 1, len(events))
            
            # Parse times if not provided
            if not start:
                expressions = self.parser.parse(text)
                if expressions:
                    start = expressions[0].start
                    end = expressions[0].end
            
            if start:
                event_times[nid] = (start, end)
        
        # Build constraints between events with known times
        for nid1, (s1, e1) in event_times.items():
            for nid2, (s2, e2) in event_times.items():
                if nid1 >= nid2:
                    continue
                
                # Determine relation from timestamps
                start1 = s1.timestamp() if s1 else 0
                end1 = (e1 or s1).timestamp() if s1 else 0
                start2 = s2.timestamp() if s2 else 0
                end2 = (e2 or s2).timestamp() if s2 else 0
                
                if start1 and start2:
                    relation = relation_from_timestamps(start1, end1, start2, end2)
                    
                    constraint = TemporalConstraint(
                        event1_nid=nid1,
                        event2_nid=nid2,
                        relation=relation,
                    )
                    self.network.add_constraint(constraint, propagate=False)
                    constraints_added += 1
        
        # Propagate
        inferred = self.network.propagate()
        
        return TemporalReasoningResult(
            facts_processed=len(events),
            events_identified=len(event_times),
            constraints_added=constraints_added,
            inferences_made=len(inferred),
            inconsistencies_found=len(self.network.get_inconsistencies()),
        )
