"""
Temporal constraint network for reasoning.

Design by OPUS-1: Constraint propagation using Allen's Interval Algebra.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Set

from inception.enhance.synthesis.temporal.relations import (
    AllenRelation,
    allen_compose,
    allen_inverse,
)

logger = logging.getLogger(__name__)


@dataclass
class TemporalConstraint:
    """A temporal constraint between two events."""
    
    event1_nid: int
    event2_nid: int
    relation: AllenRelation
    confidence: float = 1.0
    source_nid: int | None = None  # Where this constraint came from
    is_inferred: bool = False
    
    def inverse(self) -> "TemporalConstraint":
        """Get the inverse constraint (swapped events)."""
        return TemporalConstraint(
            event1_nid=self.event2_nid,
            event2_nid=self.event1_nid,
            relation=allen_inverse(self.relation),
            confidence=self.confidence,
            source_nid=self.source_nid,
            is_inferred=self.is_inferred,
        )


@dataclass
class InferredRelation:
    """A relation inferred through constraint propagation."""
    
    event1_nid: int
    event2_nid: int
    possible_relations: Set[AllenRelation]
    inference_path: list[int]  # NIDs of events in inference chain
    confidence: float = 1.0
    
    @property
    def is_determinate(self) -> bool:
        """Check if inference resulted in single relation."""
        return len(self.possible_relations) == 1
    
    @property
    def single_relation(self) -> AllenRelation | None:
        """Get single relation if determinate."""
        if self.is_determinate:
            return next(iter(self.possible_relations))
        return None


@dataclass
class Inconsistency:
    """Represents an inconsistency in the constraint network."""
    
    constraint1: TemporalConstraint
    constraint2: TemporalConstraint
    inferred: InferredRelation
    existing: TemporalConstraint
    explanation: str


class TemporalNetwork:
    """
    Temporal constraint network with propagation.
    
    Stores temporal constraints between events and
    propagates inferences using Allen's composition table.
    """
    
    def __init__(self):
        """Initialize empty network."""
        self._constraints: dict[tuple[int, int], TemporalConstraint] = {}
        self._events: set[int] = set()
        self._inferred: list[InferredRelation] = []
        self._inconsistencies: list[Inconsistency] = []
    
    @property
    def events(self) -> set[int]:
        """Get all event NIDs in the network."""
        return self._events.copy()
    
    @property
    def constraints(self) -> list[TemporalConstraint]:
        """Get all constraints."""
        return list(self._constraints.values())
    
    @property
    def is_consistent(self) -> bool:
        """Check if network is consistent."""
        return len(self._inconsistencies) == 0
    
    def add_constraint(
        self,
        constraint: TemporalConstraint,
        propagate: bool = True,
    ) -> list[InferredRelation]:
        """
        Add a constraint to the network.
        
        Args:
            constraint: Constraint to add
            propagate: Whether to propagate inferences
        
        Returns:
            List of newly inferred relations
        """
        key = (constraint.event1_nid, constraint.event2_nid)
        
        # Check for existing constraint
        if key in self._constraints:
            existing = self._constraints[key]
            if existing.relation != constraint.relation:
                logger.warning(
                    f"Overwriting constraint {key}: "
                    f"{existing.relation.name} -> {constraint.relation.name}"
                )
        
        self._constraints[key] = constraint
        self._events.add(constraint.event1_nid)
        self._events.add(constraint.event2_nid)
        
        # Also store inverse
        inv_key = (constraint.event2_nid, constraint.event1_nid)
        self._constraints[inv_key] = constraint.inverse()
        
        if propagate:
            return self.propagate()
        return []
    
    def get_constraint(
        self,
        event1_nid: int,
        event2_nid: int,
    ) -> TemporalConstraint | None:
        """Get constraint between two events."""
        return self._constraints.get((event1_nid, event2_nid))
    
    def propagate(self) -> list[InferredRelation]:
        """
        Propagate constraints using Allen's composition.
        
        For each pair of constraints A->B and B->C, infer A->C.
        
        Returns:
            List of newly inferred relations
        """
        inferred = []
        
        # Group constraints by event
        outgoing: dict[int, list[TemporalConstraint]] = {}
        for c in self._constraints.values():
            if c.event1_nid not in outgoing:
                outgoing[c.event1_nid] = []
            outgoing[c.event1_nid].append(c)
        
        # For each event B, find A->B->C chains
        for b in self._events:
            # Constraints into B (A->B)
            into_b = [
                c for c in self._constraints.values()
                if c.event2_nid == b
            ]
            
            # Constraints out of B (B->C)
            out_of_b = outgoing.get(b, [])
            
            for ab in into_b:
                for bc in out_of_b:
                    if ab.event1_nid == bc.event2_nid:
                        continue  # Skip A->B->A
                    
                    a = ab.event1_nid
                    c = bc.event2_nid
                    
                    # Check if we already have A->C
                    existing = self.get_constraint(a, c)
                    
                    # Compose relations
                    possible = allen_compose(ab.relation, bc.relation)
                    
                    if existing:
                        # Check consistency
                        if existing.relation not in possible:
                            self._inconsistencies.append(Inconsistency(
                                constraint1=ab,
                                constraint2=bc,
                                inferred=InferredRelation(
                                    event1_nid=a,
                                    event2_nid=c,
                                    possible_relations=possible,
                                    inference_path=[a, b, c],
                                ),
                                existing=existing,
                                explanation=f"Inferred {possible} but have {existing.relation}",
                            ))
                    else:
                        # Record inference
                        inf = InferredRelation(
                            event1_nid=a,
                            event2_nid=c,
                            possible_relations=possible,
                            inference_path=[a, b, c],
                            confidence=ab.confidence * bc.confidence,
                        )
                        inferred.append(inf)
                        self._inferred.append(inf)
                        
                        # If determinate, add as constraint
                        if inf.is_determinate:
                            new_constraint = TemporalConstraint(
                                event1_nid=a,
                                event2_nid=c,
                                relation=inf.single_relation,
                                confidence=inf.confidence,
                                is_inferred=True,
                            )
                            self._constraints[(a, c)] = new_constraint
                            self._constraints[(c, a)] = new_constraint.inverse()
        
        return inferred
    
    def get_inconsistencies(self) -> list[Inconsistency]:
        """Get all detected inconsistencies."""
        return self._inconsistencies.copy()
    
    def get_inferred(self) -> list[InferredRelation]:
        """Get all inferred relations."""
        return self._inferred.copy()
    
    def transitive_closure(self) -> dict[tuple[int, int], Set[AllenRelation]]:
        """
        Compute transitive closure of the network.
        
        Returns:
            Mapping from event pairs to possible relations
        """
        closure: dict[tuple[int, int], Set[AllenRelation]] = {}
        
        # Initialize with known constraints
        for (e1, e2), c in self._constraints.items():
            closure[(e1, e2)] = {c.relation}
        
        # Iterate until fixed point
        changed = True
        while changed:
            changed = False
            
            for e1 in self._events:
                for e2 in self._events:
                    if e1 == e2:
                        continue
                    
                    for e3 in self._events:
                        if e3 in (e1, e2):
                            continue
                        
                        r12 = closure.get((e1, e2))
                        r23 = closure.get((e2, e3))
                        
                        if r12 and r23:
                            # Compute composition
                            composed: Set[AllenRelation] = set()
                            for r1 in r12:
                                for r2 in r23:
                                    composed |= allen_compose(r1, r2)
                            
                            key = (e1, e3)
                            if key not in closure:
                                closure[key] = composed
                                changed = True
                            elif not composed.issubset(closure[key]):
                                closure[key] |= composed
                                changed = True
        
        return closure
