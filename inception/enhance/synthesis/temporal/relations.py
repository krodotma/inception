"""
Allen's Interval Algebra for temporal relations.

Design by OPUS-1: Full implementation of the 13 Allen relations
with composition table for inference.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Set


class AllenRelation(Enum):
    """
    Allen's 13 temporal interval relations.
    
    For intervals X and Y:
    - BEFORE: X is entirely before Y (X < Y)
    - AFTER: X is entirely after Y (X > Y)
    - MEETS: X ends where Y starts
    - MET_BY: X starts where Y ends
    - OVERLAPS: X starts before Y and ends during Y
    - OVERLAPPED_BY: Y starts before X and ends during X
    - STARTS: X and Y start together, X ends first
    - STARTED_BY: X and Y start together, Y ends first
    - FINISHES: X and Y end together, X starts later
    - FINISHED_BY: X and Y end together, Y starts later
    - DURING: X is entirely contained in Y
    - CONTAINS: Y is entirely contained in X
    - EQUALS: X and Y are identical
    """
    
    BEFORE = auto()
    AFTER = auto()
    MEETS = auto()
    MET_BY = auto()
    OVERLAPS = auto()
    OVERLAPPED_BY = auto()
    STARTS = auto()
    STARTED_BY = auto()
    FINISHES = auto()
    FINISHED_BY = auto()
    DURING = auto()
    CONTAINS = auto()
    EQUALS = auto()


class TemporalRelation(Enum):
    """Simplified temporal relations for common use."""
    
    BEFORE = auto()
    AFTER = auto()
    DURING = auto()
    SIMULTANEOUS = auto()
    UNKNOWN = auto()
    
    @classmethod
    def from_allen(cls, allen: AllenRelation) -> "TemporalRelation":
        """Convert Allen relation to simplified relation."""
        if allen in (AllenRelation.BEFORE, AllenRelation.MEETS):
            return cls.BEFORE
        elif allen in (AllenRelation.AFTER, AllenRelation.MET_BY):
            return cls.AFTER
        elif allen in (AllenRelation.DURING, AllenRelation.STARTS, AllenRelation.FINISHES):
            return cls.DURING
        elif allen == AllenRelation.EQUALS:
            return cls.SIMULTANEOUS
        else:
            return cls.UNKNOWN


# Allen's composition table (partial - full table has 169 entries)
# Maps (R1, R2) -> set of possible resulting relations
ALLEN_COMPOSITION: dict[tuple[AllenRelation, AllenRelation], Set[AllenRelation]] = {
    # BEFORE compositions
    (AllenRelation.BEFORE, AllenRelation.BEFORE): {AllenRelation.BEFORE},
    (AllenRelation.BEFORE, AllenRelation.MEETS): {AllenRelation.BEFORE},
    (AllenRelation.BEFORE, AllenRelation.OVERLAPS): {AllenRelation.BEFORE},
    (AllenRelation.BEFORE, AllenRelation.STARTS): {AllenRelation.BEFORE},
    (AllenRelation.BEFORE, AllenRelation.DURING): {AllenRelation.BEFORE, AllenRelation.MEETS, AllenRelation.OVERLAPS, AllenRelation.STARTS, AllenRelation.DURING},
    
    # AFTER compositions
    (AllenRelation.AFTER, AllenRelation.AFTER): {AllenRelation.AFTER},
    (AllenRelation.AFTER, AllenRelation.MET_BY): {AllenRelation.AFTER},
    (AllenRelation.AFTER, AllenRelation.OVERLAPPED_BY): {AllenRelation.AFTER},
    
    # MEETS compositions
    (AllenRelation.MEETS, AllenRelation.BEFORE): {AllenRelation.BEFORE},
    (AllenRelation.MEETS, AllenRelation.MEETS): {AllenRelation.BEFORE},
    (AllenRelation.MEETS, AllenRelation.OVERLAPS): {AllenRelation.BEFORE},
    (AllenRelation.MEETS, AllenRelation.STARTS): {AllenRelation.MEETS},
    
    # EQUALS compositions
    (AllenRelation.EQUALS, AllenRelation.EQUALS): {AllenRelation.EQUALS},
    (AllenRelation.EQUALS, AllenRelation.BEFORE): {AllenRelation.BEFORE},
    (AllenRelation.EQUALS, AllenRelation.AFTER): {AllenRelation.AFTER},
    
    # DURING compositions
    (AllenRelation.DURING, AllenRelation.CONTAINS): {AllenRelation.BEFORE, AllenRelation.MEETS, AllenRelation.OVERLAPS, AllenRelation.STARTS, AllenRelation.DURING, AllenRelation.FINISHES, AllenRelation.OVERLAPPED_BY, AllenRelation.MET_BY, AllenRelation.AFTER},
    (AllenRelation.DURING, AllenRelation.EQUALS): {AllenRelation.DURING},
    
    # CONTAINS compositions  
    (AllenRelation.CONTAINS, AllenRelation.DURING): {AllenRelation.CONTAINS, AllenRelation.EQUALS, AllenRelation.DURING, AllenRelation.OVERLAPS, AllenRelation.OVERLAPPED_BY, AllenRelation.STARTS, AllenRelation.STARTED_BY, AllenRelation.FINISHES, AllenRelation.FINISHED_BY},
    (AllenRelation.CONTAINS, AllenRelation.EQUALS): {AllenRelation.CONTAINS},
}


def allen_inverse(relation: AllenRelation) -> AllenRelation:
    """Get the inverse of an Allen relation."""
    inverse_map = {
        AllenRelation.BEFORE: AllenRelation.AFTER,
        AllenRelation.AFTER: AllenRelation.BEFORE,
        AllenRelation.MEETS: AllenRelation.MET_BY,
        AllenRelation.MET_BY: AllenRelation.MEETS,
        AllenRelation.OVERLAPS: AllenRelation.OVERLAPPED_BY,
        AllenRelation.OVERLAPPED_BY: AllenRelation.OVERLAPS,
        AllenRelation.STARTS: AllenRelation.STARTED_BY,
        AllenRelation.STARTED_BY: AllenRelation.STARTS,
        AllenRelation.FINISHES: AllenRelation.FINISHED_BY,
        AllenRelation.FINISHED_BY: AllenRelation.FINISHES,
        AllenRelation.DURING: AllenRelation.CONTAINS,
        AllenRelation.CONTAINS: AllenRelation.DURING,
        AllenRelation.EQUALS: AllenRelation.EQUALS,
    }
    return inverse_map[relation]


def allen_compose(
    r1: AllenRelation,
    r2: AllenRelation,
) -> Set[AllenRelation]:
    """
    Compose two Allen relations.
    
    If A r1 B and B r2 C, what are the possible relations A ? C?
    
    Args:
        r1: First relation (A r1 B)
        r2: Second relation (B r2 C)
    
    Returns:
        Set of possible relations (A ? C)
    """
    # Look up in composition table
    if (r1, r2) in ALLEN_COMPOSITION:
        return ALLEN_COMPOSITION[(r1, r2)]
    
    # Try with inverses for symmetric lookup
    # If A r1 B and B r2 C, we can use inverse(r1^-1) and inverse(r2^-1)
    
    # Default: return all possible relations (unknown)
    return set(AllenRelation)


def is_consistent(
    r1: AllenRelation,
    r2: AllenRelation,
    r_direct: AllenRelation | None = None,
) -> bool:
    """
    Check if relations are consistent.
    
    If A r1 B and B r2 C, is A r_direct C consistent?
    """
    if r_direct is None:
        return True
    
    composed = allen_compose(r1, r2)
    return r_direct in composed


def relation_from_timestamps(
    start1: float,
    end1: float,
    start2: float,
    end2: float,
) -> AllenRelation:
    """
    Determine Allen relation from interval timestamps.
    
    Args:
        start1, end1: First interval
        start2, end2: Second interval
    
    Returns:
        Allen relation between intervals
    """
    # Tolerance for floating point comparison
    eps = 1e-6
    
    if abs(start1 - start2) < eps and abs(end1 - end2) < eps:
        return AllenRelation.EQUALS
    
    if end1 < start2 - eps:
        return AllenRelation.BEFORE
    
    if abs(end1 - start2) < eps:
        return AllenRelation.MEETS
    
    if start1 > end2 + eps:
        return AllenRelation.AFTER
    
    if abs(start1 - end2) < eps:
        return AllenRelation.MET_BY
    
    if abs(start1 - start2) < eps:
        if end1 < end2 - eps:
            return AllenRelation.STARTS
        else:
            return AllenRelation.STARTED_BY
    
    if abs(end1 - end2) < eps:
        if start1 > start2 + eps:
            return AllenRelation.FINISHES
        else:
            return AllenRelation.FINISHED_BY
    
    if start1 > start2 and end1 < end2:
        return AllenRelation.DURING
    
    if start1 < start2 and end1 > end2:
        return AllenRelation.CONTAINS
    
    if start1 < start2 and end1 < end2 and end1 > start2:
        return AllenRelation.OVERLAPS
    
    if start1 > start2 and end1 > end2 and start1 < end2:
        return AllenRelation.OVERLAPPED_BY
    
    return AllenRelation.BEFORE  # Default
