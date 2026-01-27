"""
Uncertainty quantification for claims.

Design by OPUS-2: Bayesian fusion of uncertain claims.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence


@dataclass
class UncertainClaim:
    """
    A claim with uncertainty quantification.
    
    Represents epistemic uncertainty (knowledge gap) and
    aleatoric uncertainty (inherent randomness).
    """
    
    nid: int
    text: str
    
    # Mean confidence (0-1)
    mean_confidence: float = 0.5
    
    # Standard deviation of confidence (higher = more uncertain)
    std_confidence: float = 0.2
    
    # Source of the claim
    source_nid: int | None = None
    source_weight: float = 1.0
    
    @property
    def precision(self) -> float:
        """Get precision (inverse variance)."""
        if self.std_confidence <= 0:
            return 100.0  # High precision for certain claims
        return 1.0 / (self.std_confidence ** 2)
    
    @property
    def lower_bound(self) -> float:
        """95% confidence lower bound."""
        return max(0, self.mean_confidence - 1.96 * self.std_confidence)
    
    @property
    def upper_bound(self) -> float:
        """95% confidence upper bound."""
        return min(1, self.mean_confidence + 1.96 * self.std_confidence)
    
    @property
    def is_highly_uncertain(self) -> bool:
        """Check if claim has high uncertainty."""
        return self.std_confidence > 0.3
    
    @property
    def is_confident(self) -> bool:
        """Check if we're confident in this claim."""
        return self.mean_confidence > 0.7 and self.std_confidence < 0.2


def bayesian_fuse(claims: Sequence[UncertainClaim]) -> UncertainClaim:
    """
    Fuse multiple uncertain claims using Bayesian inference.
    
    Uses precision-weighted averaging where higher precision (lower variance)
    claims contribute more to the fused result.
    
    Args:
        claims: Sequence of uncertain claims to fuse
    
    Returns:
        Fused claim with updated confidence and uncertainty
    """
    if not claims:
        return UncertainClaim(nid=-1, text="", mean_confidence=0.5, std_confidence=1.0)
    
    if len(claims) == 1:
        return claims[0]
    
    # Weight by precision (inverse variance) and source weight
    weights = []
    for claim in claims:
        w = claim.precision * claim.source_weight
        weights.append(w)
    
    total_weight = sum(weights)
    if total_weight == 0:
        total_weight = 1.0
    
    # Weighted mean
    fused_mean = sum(
        w * c.mean_confidence 
        for w, c in zip(weights, claims)
    ) / total_weight
    
    # Fused precision is sum of precisions (weighted)
    fused_precision = sum(weights)
    
    # Fused standard deviation
    fused_std = 1.0 / math.sqrt(fused_precision) if fused_precision > 0 else 1.0
    
    # Clamp values
    fused_mean = max(0, min(1, fused_mean))
    fused_std = max(0.01, min(1, fused_std))
    
    return UncertainClaim(
        nid=claims[0].nid,  # Keep first claim's NID
        text=claims[0].text,
        mean_confidence=fused_mean,
        std_confidence=fused_std,
    )


def entropy_fusion(claims: Sequence[UncertainClaim]) -> UncertainClaim:
    """
    Fuse claims using minimum entropy criterion.
    
    Prefers claims with lower uncertainty (entropy).
    """
    if not claims:
        return UncertainClaim(nid=-1, text="", mean_confidence=0.5, std_confidence=1.0)
    
    if len(claims) == 1:
        return claims[0]
    
    # Calculate entropy for each claim
    # Higher std = higher entropy (more uncertain)
    entropies = [c.std_confidence for c in claims]
    
    # Inverse entropy weighting
    inv_entropies = [1.0 / (e + 0.01) for e in entropies]
    total_inv = sum(inv_entropies)
    
    weights = [ie / total_inv for ie in inv_entropies]
    
    # Weighted fusion
    fused_mean = sum(w * c.mean_confidence for w, c in zip(weights, claims))
    fused_std = sum(w * c.std_confidence for w, c in zip(weights, claims))
    
    return UncertainClaim(
        nid=claims[0].nid,
        text=claims[0].text,
        mean_confidence=fused_mean,
        std_confidence=fused_std,
    )


def dempster_shafer_combine(
    belief1: tuple[float, float],  # (belief, plausibility)
    belief2: tuple[float, float],
) -> tuple[float, float]:
    """
    Combine two belief functions using Dempster-Shafer theory.
    
    Returns:
        Combined (belief, plausibility) tuple
    """
    b1, p1 = belief1
    b2, p2 = belief2
    
    # Calculate conflict mass
    conflict = b1 * (1 - p2) + b2 * (1 - p1)
    
    if conflict >= 1:
        return (0.0, 1.0)  # Complete conflict
    
    # Normalize
    norm = 1 - conflict
    
    combined_belief = (b1 * b2) / norm
    combined_plausibility = 1 - ((1 - p1) * (1 - p2)) / norm
    
    return (combined_belief, combined_plausibility)


@dataclass
class FusionStats:
    """Statistics from a fusion operation."""
    
    claims_fused: int = 0
    original_uncertainty: float = 0.0
    fused_uncertainty: float = 0.0
    uncertainty_reduction: float = 0.0
    
    @property
    def improvement_pct(self) -> float:
        """Percentage improvement in uncertainty."""
        if self.original_uncertainty == 0:
            return 0.0
        return (self.uncertainty_reduction / self.original_uncertainty) * 100


def compute_fusion_stats(
    original_claims: Sequence[UncertainClaim],
    fused_claim: UncertainClaim,
) -> FusionStats:
    """Compute statistics about a fusion operation."""
    if not original_claims:
        return FusionStats()
    
    original_uncertainty = sum(c.std_confidence for c in original_claims) / len(original_claims)
    
    return FusionStats(
        claims_fused=len(original_claims),
        original_uncertainty=original_uncertainty,
        fused_uncertainty=fused_claim.std_confidence,
        uncertainty_reduction=original_uncertainty - fused_claim.std_confidence,
    )
