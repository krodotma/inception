"""
Conflict resolver for handling contradicting claims.

Design by OPUS-1: Formal contradiction resolution model.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable

from inception.enhance.synthesis.fusion.sources import SourceRegistry, SourceInfo
from inception.enhance.synthesis.fusion.matcher import ClaimInfo

logger = logging.getLogger(__name__)


class ContradictionType(Enum):
    """Type of contradiction between claims."""
    
    DIRECT = auto()       # A says X, B says NOT X
    TEMPORAL = auto()     # A says X@t1, B says Y@t2 where X contradicts Y
    QUANTITATIVE = auto() # A says 100, B says 200
    DEFINITIONAL = auto() # Different definitions of same term
    SCOPE = auto()        # Different scopes (e.g., global vs local)


class ResolutionStrategy(Enum):
    """Strategy for resolving contradictions."""
    
    MAJORITY = auto()         # Most sources win
    WEIGHTED_MAJORITY = auto() # Weighted by source reliability
    RECENCY = auto()          # Most recent wins
    AUTHORITY = auto()        # Most authoritative source wins
    SPECIFICITY = auto()      # Most specific claim wins
    MERGE = auto()            # Merge into qualified statement
    DEFER = auto()            # Mark as unresolved


@dataclass
class Resolution:
    """Result of resolving a contradiction."""
    
    winning_nid: int | None      # NID of winning claim, None if merged/deferred
    losing_nids: list[int]       # NIDs of losing claims
    strategy: ResolutionStrategy
    confidence: float            # Confidence in resolution
    explanation: str
    merged_claim: str | None = None  # Merged statement if applicable
    
    @property
    def is_resolved(self) -> bool:
        """Check if contradiction was resolved."""
        return self.strategy != ResolutionStrategy.DEFER


@dataclass
class Contradiction:
    """Represents a detected contradiction."""
    
    claim1: ClaimInfo
    claim2: ClaimInfo
    type: ContradictionType
    confidence: float
    detected_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution: Resolution | None = None


class ConflictResolver:
    """
    Resolves contradictions between claims.
    
    Uses multiple strategies based on contradiction type
    and available metadata.
    """
    
    def __init__(
        self,
        source_registry: SourceRegistry | None = None,
        default_strategy: ResolutionStrategy = ResolutionStrategy.WEIGHTED_MAJORITY,
    ):
        """
        Initialize conflict resolver.
        
        Args:
            source_registry: Registry for source weights
            default_strategy: Default resolution strategy
        """
        self.source_registry = source_registry or SourceRegistry()
        self.default_strategy = default_strategy
        
        self._contradictions: list[Contradiction] = []
        self._resolutions: list[Resolution] = []
    
    def detect_type(
        self,
        claim1: ClaimInfo,
        claim2: ClaimInfo,
    ) -> ContradictionType:
        """Detect the type of contradiction."""
        text1 = claim1.text.lower()
        text2 = claim2.text.lower()
        
        # Check for quantitative contradiction
        if self._has_numbers(text1) and self._has_numbers(text2):
            nums1 = self._extract_numbers(text1)
            nums2 = self._extract_numbers(text2)
            if nums1 and nums2 and nums1 != nums2:
                return ContradictionType.QUANTITATIVE
        
        # Check for definitional contradiction
        if "is defined as" in text1 or "is defined as" in text2:
            return ContradictionType.DEFINITIONAL
        
        # Check for temporal contradiction
        if claim1.metadata.get("timestamp") and claim2.metadata.get("timestamp"):
            return ContradictionType.TEMPORAL
        
        # Check for scope-based contradiction
        scope_words = {"global", "local", "general", "specific", "always", "sometimes"}
        if any(w in text1 for w in scope_words) or any(w in text2 for w in scope_words):
            return ContradictionType.SCOPE
        
        return ContradictionType.DIRECT
    
    def resolve(
        self,
        claims: list[ClaimInfo],
        contradiction_type: ContradictionType | None = None,
        strategy: ResolutionStrategy | None = None,
    ) -> Resolution:
        """
        Resolve a contradiction between claims.
        
        Args:
            claims: Conflicting claims (minimum 2)
            contradiction_type: Type of contradiction
            strategy: Resolution strategy to use
        
        Returns:
            Resolution result
        """
        if len(claims) < 2:
            return Resolution(
                winning_nid=claims[0].nid if claims else None,
                losing_nids=[],
                strategy=ResolutionStrategy.DEFER,
                confidence=0.0,
                explanation="Need at least 2 claims to resolve",
            )
        
        strategy = strategy or self._choose_strategy(claims, contradiction_type)
        
        if strategy == ResolutionStrategy.WEIGHTED_MAJORITY:
            return self._resolve_weighted_majority(claims)
        elif strategy == ResolutionStrategy.RECENCY:
            return self._resolve_recency(claims)
        elif strategy == ResolutionStrategy.AUTHORITY:
            return self._resolve_authority(claims)
        elif strategy == ResolutionStrategy.SPECIFICITY:
            return self._resolve_specificity(claims)
        elif strategy == ResolutionStrategy.MERGE:
            return self._resolve_merge(claims, contradiction_type)
        else:
            return self._resolve_defer(claims)
    
    def _choose_strategy(
        self,
        claims: list[ClaimInfo],
        contradiction_type: ContradictionType | None,
    ) -> ResolutionStrategy:
        """Choose appropriate resolution strategy."""
        if contradiction_type == ContradictionType.QUANTITATIVE:
            return ResolutionStrategy.WEIGHTED_MAJORITY
        elif contradiction_type == ContradictionType.TEMPORAL:
            return ResolutionStrategy.RECENCY
        elif contradiction_type == ContradictionType.DEFINITIONAL:
            return ResolutionStrategy.AUTHORITY
        elif contradiction_type == ContradictionType.SCOPE:
            return ResolutionStrategy.MERGE
        else:
            return self.default_strategy
    
    def _resolve_weighted_majority(
        self,
        claims: list[ClaimInfo],
    ) -> Resolution:
        """Resolve using weighted source voting."""
        # Group by claim text (similar claims)
        # For simplicity, treat each claim separately
        
        weights = []
        for claim in claims:
            if claim.source_nid:
                weight = self.source_registry.get_weight(claim.source_nid)
            else:
                weight = 0.5
            weights.append((claim, weight))
        
        # Sort by weight
        weights.sort(key=lambda x: x[1], reverse=True)
        
        winner = weights[0][0]
        losers = [c.nid for c, _ in weights[1:]]
        
        total_weight = sum(w for _, w in weights)
        winner_weight = weights[0][1]
        confidence = winner_weight / total_weight if total_weight > 0 else 0.5
        
        return Resolution(
            winning_nid=winner.nid,
            losing_nids=losers,
            strategy=ResolutionStrategy.WEIGHTED_MAJORITY,
            confidence=confidence,
            explanation=f"Winning claim has weight {winner_weight:.2f} of {total_weight:.2f} total",
        )
    
    def _resolve_recency(self, claims: list[ClaimInfo]) -> Resolution:
        """Resolve by choosing most recent claim."""
        dated_claims = []
        
        for claim in claims:
            timestamp = claim.metadata.get("timestamp") or claim.metadata.get("published_at")
            if timestamp:
                if isinstance(timestamp, str):
                    from dateutil import parser
                    timestamp = parser.parse(timestamp)
                dated_claims.append((claim, timestamp))
            else:
                dated_claims.append((claim, datetime.min))
        
        dated_claims.sort(key=lambda x: x[1], reverse=True)
        
        winner = dated_claims[0][0]
        losers = [c.nid for c, _ in dated_claims[1:]]
        
        return Resolution(
            winning_nid=winner.nid,
            losing_nids=losers,
            strategy=ResolutionStrategy.RECENCY,
            confidence=0.7,
            explanation="Most recent claim wins",
        )
    
    def _resolve_authority(self, claims: list[ClaimInfo]) -> Resolution:
        """Resolve by choosing most authoritative source."""
        authority_scores = []
        
        for claim in claims:
            if claim.source_nid:
                source = self.source_registry.get(claim.source_nid)
                if source:
                    score = source.domain_authority * source.base_reliability
                else:
                    score = 0.5
            else:
                score = 0.3
            authority_scores.append((claim, score))
        
        authority_scores.sort(key=lambda x: x[1], reverse=True)
        
        winner = authority_scores[0][0]
        losers = [c.nid for c, _ in authority_scores[1:]]
        
        return Resolution(
            winning_nid=winner.nid,
            losing_nids=losers,
            strategy=ResolutionStrategy.AUTHORITY,
            confidence=authority_scores[0][1],
            explanation="Most authoritative source wins",
        )
    
    def _resolve_specificity(self, claims: list[ClaimInfo]) -> Resolution:
        """Resolve by choosing most specific claim."""
        # More specific = longer, more detailed
        scored = [(c, len(c.text) + len(c.obj or "")) for c in claims]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        winner = scored[0][0]
        losers = [c.nid for c, _ in scored[1:]]
        
        return Resolution(
            winning_nid=winner.nid,
            losing_nids=losers,
            strategy=ResolutionStrategy.SPECIFICITY,
            confidence=0.6,
            explanation="Most specific claim wins",
        )
    
    def _resolve_merge(
        self,
        claims: list[ClaimInfo],
        contradiction_type: ContradictionType | None,
    ) -> Resolution:
        """Merge claims into qualified statement."""
        if contradiction_type == ContradictionType.SCOPE:
            merged = f"In general, {claims[0].text}; however, in specific cases, {claims[1].text}"
        else:
            merged = f"While some sources say '{claims[0].text}', others contend '{claims[1].text}'"
        
        return Resolution(
            winning_nid=None,
            losing_nids=[c.nid for c in claims],
            strategy=ResolutionStrategy.MERGE,
            confidence=0.8,
            explanation="Claims merged into qualified statement",
            merged_claim=merged,
        )
    
    def _resolve_defer(self, claims: list[ClaimInfo]) -> Resolution:
        """Defer resolution (mark as unresolved)."""
        return Resolution(
            winning_nid=None,
            losing_nids=[],
            strategy=ResolutionStrategy.DEFER,
            confidence=0.0,
            explanation="Contradiction unresolved - requires manual review",
        )
    
    def _has_numbers(self, text: str) -> bool:
        """Check if text contains numbers."""
        import re
        return bool(re.search(r'\d+', text))
    
    def _extract_numbers(self, text: str) -> list[float]:
        """Extract numbers from text."""
        import re
        matches = re.findall(r'[\d,]+\.?\d*', text)
        return [float(m.replace(',', '')) for m in matches if m]
    
    def get_all_contradictions(self) -> list[Contradiction]:
        """Get all detected contradictions."""
        return self._contradictions.copy()
    
    def get_unresolved(self) -> list[Contradiction]:
        """Get unresolved contradictions."""
        return [c for c in self._contradictions if not c.resolved]
