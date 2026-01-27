"""
Multi-Source Fusion - Knowledge combination with conflict resolution.

Design by OPUS-1: Weighted fusion model with contradiction resolution.
Enhanced by OPUS-2: Bayesian uncertainty quantification.
"""

from inception.enhance.synthesis.fusion.sources import SourceRegistry, SourceInfo
from inception.enhance.synthesis.fusion.matcher import ClaimMatcher, MatchResult
from inception.enhance.synthesis.fusion.resolver import (
    ConflictResolver,
    ContradictionType,
    Resolution,
)
from inception.enhance.synthesis.fusion.uncertainty import (
    UncertainClaim,
    bayesian_fuse,
)
from inception.enhance.synthesis.fusion.engine import FusionEngine, FusionResult

__all__ = [
    "FusionEngine",
    "FusionResult",
    "SourceRegistry",
    "SourceInfo",
    "ClaimMatcher",
    "MatchResult",
    "ConflictResolver",
    "ContradictionType",
    "Resolution",
    "UncertainClaim",
    "bayesian_fuse",
]
