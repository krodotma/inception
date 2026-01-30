#!/usr/bin/env python3
"""
Temporal Reasoner Skill
Advanced temporal inference and timeline construction.

SUBAGENT: OPUS-1 (IRKG Specialist)
TIER: 3 - Synthesis

Features:
- Allen's Interval Algebra (13 relations)
- Event timeline construction
- Temporal queries
- Anachronism detection
- Duration estimation
- Constraint satisfaction
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Optional
from pathlib import Path


# =============================================================================
# Allen's Interval Algebra
# =============================================================================

class AllenRelation(Enum):
    """The 13 Allen interval relations."""
    BEFORE = "before"           # X ends before Y starts
    AFTER = "after"             # X starts after Y ends
    MEETS = "meets"             # X ends exactly when Y starts
    MET_BY = "met_by"           # X starts exactly when Y ends
    OVERLAPS = "overlaps"       # X starts before Y, ends during Y
    OVERLAPPED_BY = "overlapped_by"  # X starts during Y, ends after Y
    STARTS = "starts"           # X and Y start together, X ends first
    STARTED_BY = "started_by"   # X and Y start together, Y ends first
    DURING = "during"           # X is contained in Y
    CONTAINS = "contains"       # Y is contained in X
    FINISHES = "finishes"       # X and Y end together, X starts after Y
    FINISHED_BY = "finished_by" # X and Y end together, X starts before Y
    EQUALS = "equals"           # X and Y are identical


@dataclass
class TemporalInterval:
    """A temporal interval with start and end times."""
    id: str
    start: datetime
    end: datetime
    label: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> timedelta:
        """Get interval duration."""
        return self.end - self.start
    
    @property
    def duration_ms(self) -> int:
        """Get duration in milliseconds."""
        return int(self.duration.total_seconds() * 1000)
    
    def relation_to(self, other: "TemporalInterval") -> AllenRelation:
        """Determine Allen relation to another interval."""
        if self.end < other.start:
            return AllenRelation.BEFORE
        if self.start > other.end:
            return AllenRelation.AFTER
        if self.end == other.start:
            return AllenRelation.MEETS
        if self.start == other.end:
            return AllenRelation.MET_BY
        
        # Overlapping cases
        if self.start == other.start and self.end == other.end:
            return AllenRelation.EQUALS
        if self.start == other.start:
            return AllenRelation.STARTS if self.end < other.end else AllenRelation.STARTED_BY
        if self.end == other.end:
            return AllenRelation.FINISHES if self.start > other.start else AllenRelation.FINISHED_BY
        
        if self.start < other.start and self.end > other.end:
            return AllenRelation.CONTAINS
        if self.start > other.start and self.end < other.end:
            return AllenRelation.DURING
        
        if self.start < other.start and self.end > other.start and self.end < other.end:
            return AllenRelation.OVERLAPS
        if self.start > other.start and self.start < other.end and self.end > other.end:
            return AllenRelation.OVERLAPPED_BY
        
        return AllenRelation.EQUALS  # Default
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "label": self.label,
            "duration_ms": self.duration_ms,
            "properties": self.properties,
        }


# =============================================================================
# Event Timeline
# =============================================================================

@dataclass
class TimelineEvent:
    """An event on a timeline."""
    id: str
    timestamp: datetime
    event_type: str  # 'start', 'end', 'instant', 'marker'
    label: str
    interval_id: Optional[str] = None
    properties: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "type": self.event_type,
            "label": self.label,
            "interval_id": self.interval_id,
        }


class Timeline:
    """Ordered timeline of events."""
    
    def __init__(self):
        self.events: list[TimelineEvent] = []
        self.intervals: dict[str, TemporalInterval] = {}
    
    def add_interval(self, interval: TemporalInterval) -> None:
        """Add interval to timeline."""
        self.intervals[interval.id] = interval
        
        # Create start/end events
        self.events.append(TimelineEvent(
            id=f"{interval.id}_start",
            timestamp=interval.start,
            event_type="start",
            label=f"Start: {interval.label}",
            interval_id=interval.id,
        ))
        self.events.append(TimelineEvent(
            id=f"{interval.id}_end",
            timestamp=interval.end,
            event_type="end",
            label=f"End: {interval.label}",
            interval_id=interval.id,
        ))
        
        # Keep sorted
        self.events.sort(key=lambda e: e.timestamp)
    
    def add_instant_event(self, event_id: str, timestamp: datetime, label: str) -> None:
        """Add an instant event (point in time)."""
        self.events.append(TimelineEvent(
            id=event_id,
            timestamp=timestamp,
            event_type="instant",
            label=label,
        ))
        self.events.sort(key=lambda e: e.timestamp)
    
    def get_events_in_range(self, start: datetime, end: datetime) -> list[TimelineEvent]:
        """Get events within a time range."""
        return [e for e in self.events if start <= e.timestamp <= end]
    
    def get_active_intervals_at(self, timestamp: datetime) -> list[TemporalInterval]:
        """Get intervals active at a specific time."""
        return [
            interval for interval in self.intervals.values()
            if interval.start <= timestamp <= interval.end
        ]
    
    def get_timeline_bounds(self) -> tuple[datetime, datetime]:
        """Get earliest and latest timestamps."""
        if not self.events:
            now = datetime.utcnow()
            return now, now
        return self.events[0].timestamp, self.events[-1].timestamp
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "events": [e.to_dict() for e in self.events],
            "intervals": {k: v.to_dict() for k, v in self.intervals.items()},
            "bounds": {
                "start": self.get_timeline_bounds()[0].isoformat(),
                "end": self.get_timeline_bounds()[1].isoformat(),
            },
        }


# =============================================================================
# Temporal Reasoner
# =============================================================================

@dataclass
class TemporalConstraint:
    """A constraint between intervals."""
    interval_a_id: str
    interval_b_id: str
    relation: AllenRelation
    confidence: float = 1.0


class TemporalReasoner:
    """
    Temporal reasoning engine.
    
    Features:
    - Allen interval algebra
    - Constraint satisfaction
    - Timeline construction
    - Anachronism detection
    """
    
    def __init__(self):
        self.timeline = Timeline()
        self.constraints: list[TemporalConstraint] = []
        self.relation_cache: dict[tuple[str, str], AllenRelation] = {}
    
    def add_interval(self, interval: TemporalInterval) -> None:
        """Add an interval to the reasoner."""
        self.timeline.add_interval(interval)
        
        # Compute relations with existing intervals
        for existing_id, existing in self.timeline.intervals.items():
            if existing_id != interval.id:
                relation = interval.relation_to(existing)
                self.relation_cache[(interval.id, existing_id)] = relation
                # Store inverse
                inverse = self._inverse_relation(relation)
                self.relation_cache[(existing_id, interval.id)] = inverse
    
    def get_relation(self, interval_a_id: str, interval_b_id: str) -> Optional[AllenRelation]:
        """Get Allen relation between two intervals."""
        return self.relation_cache.get((interval_a_id, interval_b_id))
    
    def add_constraint(self, constraint: TemporalConstraint) -> bool:
        """Add a temporal constraint."""
        # Check if constraint is satisfiable
        actual_relation = self.get_relation(constraint.interval_a_id, constraint.interval_b_id)
        
        if actual_relation and actual_relation != constraint.relation:
            return False  # Contradiction
        
        self.constraints.append(constraint)
        return True
    
    def detect_anachronisms(self) -> list[dict[str, Any]]:
        """Detect temporal inconsistencies."""
        anachronisms = []
        
        for constraint in self.constraints:
            actual = self.get_relation(constraint.interval_a_id, constraint.interval_b_id)
            if actual and actual != constraint.relation:
                anachronisms.append({
                    "type": "constraint_violation",
                    "expected": constraint.relation.value,
                    "actual": actual.value if actual else None,
                    "interval_a": constraint.interval_a_id,
                    "interval_b": constraint.interval_b_id,
                    "confidence": constraint.confidence,
                })
        
        return anachronisms
    
    def query_before(self, interval_id: str) -> list[str]:
        """Find all intervals that come before the given interval."""
        result = []
        for (a_id, b_id), relation in self.relation_cache.items():
            if b_id == interval_id and relation in [AllenRelation.BEFORE, AllenRelation.MEETS]:
                result.append(a_id)
        return result
    
    def query_after(self, interval_id: str) -> list[str]:
        """Find all intervals that come after the given interval."""
        result = []
        for (a_id, b_id), relation in self.relation_cache.items():
            if b_id == interval_id and relation in [AllenRelation.AFTER, AllenRelation.MET_BY]:
                result.append(a_id)
        return result
    
    def query_concurrent(self, interval_id: str) -> list[str]:
        """Find all intervals concurrent with the given interval."""
        result = []
        concurrent_relations = [
            AllenRelation.OVERLAPS, AllenRelation.OVERLAPPED_BY,
            AllenRelation.CONTAINS, AllenRelation.DURING,
            AllenRelation.STARTS, AllenRelation.STARTED_BY,
            AllenRelation.FINISHES, AllenRelation.FINISHED_BY,
            AllenRelation.EQUALS,
        ]
        for (a_id, b_id), relation in self.relation_cache.items():
            if b_id == interval_id and relation in concurrent_relations:
                result.append(a_id)
        return result
    
    def get_summary(self) -> dict[str, Any]:
        """Get reasoning summary."""
        return {
            "total_intervals": len(self.timeline.intervals),
            "total_events": len(self.timeline.events),
            "total_constraints": len(self.constraints),
            "cached_relations": len(self.relation_cache),
            "anachronisms": self.detect_anachronisms(),
            "timeline_bounds": {
                "start": self.timeline.get_timeline_bounds()[0].isoformat(),
                "end": self.timeline.get_timeline_bounds()[1].isoformat(),
            },
        }
    
    def _inverse_relation(self, relation: AllenRelation) -> AllenRelation:
        """Get inverse of an Allen relation."""
        inverses = {
            AllenRelation.BEFORE: AllenRelation.AFTER,
            AllenRelation.AFTER: AllenRelation.BEFORE,
            AllenRelation.MEETS: AllenRelation.MET_BY,
            AllenRelation.MET_BY: AllenRelation.MEETS,
            AllenRelation.OVERLAPS: AllenRelation.OVERLAPPED_BY,
            AllenRelation.OVERLAPPED_BY: AllenRelation.OVERLAPS,
            AllenRelation.STARTS: AllenRelation.STARTED_BY,
            AllenRelation.STARTED_BY: AllenRelation.STARTS,
            AllenRelation.DURING: AllenRelation.CONTAINS,
            AllenRelation.CONTAINS: AllenRelation.DURING,
            AllenRelation.FINISHES: AllenRelation.FINISHED_BY,
            AllenRelation.FINISHED_BY: AllenRelation.FINISHES,
            AllenRelation.EQUALS: AllenRelation.EQUALS,
        }
        return inverses.get(relation, relation)


# =============================================================================
# CLI Interface
# =============================================================================

def parse_datetime(s: str) -> datetime:
    """Parse datetime from string."""
    for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse datetime: {s}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Temporal Reasoner Skill")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Add interval
    add_parser = subparsers.add_parser("add", help="Add interval")
    add_parser.add_argument("--id", required=True, help="Interval ID")
    add_parser.add_argument("--start", required=True, help="Start datetime")
    add_parser.add_argument("--end", required=True, help="End datetime")
    add_parser.add_argument("--label", default="", help="Label")
    
    # Query
    query_parser = subparsers.add_parser("query", help="Query intervals")
    query_parser.add_argument("--at", help="Get active intervals at timestamp")
    query_parser.add_argument("--before", help="Get intervals before ID")
    query_parser.add_argument("--after", help="Get intervals after ID")
    
    # Relation
    rel_parser = subparsers.add_parser("relation", help="Get relation between intervals")
    rel_parser.add_argument("--a", required=True, help="First interval ID")
    rel_parser.add_argument("--b", required=True, help="Second interval ID")
    
    # Demo
    subparsers.add_parser("demo", help="Run demonstration")
    
    args = parser.parse_args()
    
    if args.command == "demo":
        run_demo()
    else:
        print("=== Temporal Reasoner ===")
        print("")
        print("Capabilities:")
        print("  ✓ Allen's Interval Algebra (13 relations)")
        print("  ✓ Event timeline construction")
        print("  ✓ Temporal queries (before/after/concurrent)")
        print("  ✓ Anachronism detection")
        print("  ✓ Constraint satisfaction")
        print("")
        print("Use --help for available commands.")


def run_demo():
    """Run a demonstration of temporal reasoning."""
    print("=== Temporal Reasoner Demo ===\n")
    
    reasoner = TemporalReasoner()
    
    # Add some intervals
    now = datetime.utcnow()
    
    intervals = [
        TemporalInterval(
            id="meeting_1",
            start=now,
            end=now + timedelta(hours=1),
            label="Project Planning",
        ),
        TemporalInterval(
            id="meeting_2",
            start=now + timedelta(hours=2),
            end=now + timedelta(hours=3),
            label="Code Review",
        ),
        TemporalInterval(
            id="task_1",
            start=now + timedelta(minutes=30),
            end=now + timedelta(hours=2, minutes=30),
            label="Implementation",
        ),
    ]
    
    print("Adding intervals:")
    for interval in intervals:
        reasoner.add_interval(interval)
        print(f"  + {interval.label}: {interval.start.strftime('%H:%M')} - {interval.end.strftime('%H:%M')}")
    
    print("\nAllen Relations:")
    for i, int_a in enumerate(intervals):
        for int_b in intervals[i+1:]:
            relation = reasoner.get_relation(int_a.id, int_b.id)
            if relation:
                print(f"  {int_a.label} <{relation.value}> {int_b.label}")
    
    print("\nConcurrent with 'Implementation':")
    concurrent = reasoner.query_concurrent("task_1")
    for int_id in concurrent:
        interval = reasoner.timeline.intervals.get(int_id)
        if interval:
            print(f"  - {interval.label}")
    
    print("\nSummary:")
    summary = reasoner.get_summary()
    print(f"  Total intervals: {summary['total_intervals']}")
    print(f"  Total events: {summary['total_events']}")
    print(f"  Cached relations: {summary['cached_relations']}")
    
    print("\n✓ Temporal reasoning complete!")


if __name__ == "__main__":
    main()
