"""
Fusion engine - orchestrates multi-source knowledge fusion.

Design by OPUS-3: Clean orchestration of all fusion components.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from inception.enhance.synthesis.fusion.sources import SourceRegistry, SourceInfo
from inception.enhance.synthesis.fusion.matcher import ClaimMatcher, ClaimInfo, MatchResult, MatchType
from inception.enhance.synthesis.fusion.resolver import ConflictResolver, Resolution, ContradictionType
from inception.enhance.synthesis.fusion.uncertainty import (
    UncertainClaim,
    bayesian_fuse,
    compute_fusion_stats,
    FusionStats,
)

logger = logging.getLogger(__name__)


@dataclass
class FusedClaim:
    """A claim after fusion with multiple sources."""
    
    text: str
    nids: list[int]           # All contributing claim NIDs
    source_nids: list[int]    # All contributing source NIDs
    confidence: float
    uncertainty: float
    provenance: list[str]     # Source names/URLs
    resolved_conflicts: int   # Number of conflicts resolved
    
    @property
    def is_well_supported(self) -> bool:
        """Check if claim is well-supported by multiple sources."""
        return len(self.nids) >= 2 and self.confidence > 0.7


@dataclass
class FusionResult:
    """Result of a fusion operation."""
    
    fused_claims: list[FusedClaim]
    claims_processed: int
    conflicts_resolved: int
    unresolved_conflicts: int
    stats: FusionStats
    
    @property
    def success_rate(self) -> float:
        """Percentage of claims successfully fused."""
        if self.claims_processed == 0:
            return 0.0
        return len(self.fused_claims) / self.claims_processed


class FusionEngine:
    """
    Orchestrates multi-source knowledge fusion.
    
    Workflow:
    1. Register sources with reliability scores
    2. Match claims across sources
    3. Detect and resolve contradictions
    4. Fuse agreeing claims with uncertainty quantification
    5. Update confidence scores
    """
    
    def __init__(
        self,
        source_registry: SourceRegistry | None = None,
        claim_matcher: ClaimMatcher | None = None,
        conflict_resolver: ConflictResolver | None = None,
    ):
        """Initialize fusion engine."""
        self.source_registry = source_registry or SourceRegistry()
        self.claim_matcher = claim_matcher or ClaimMatcher()
        self.conflict_resolver = conflict_resolver or ConflictResolver(self.source_registry)
        
        self._fusion_log: list[dict[str, Any]] = []
    
    def fuse(
        self,
        claims: list[ClaimInfo],
        sources: list[SourceInfo] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> FusionResult:
        """
        Fuse claims from multiple sources.
        
        Args:
            claims: Claims to fuse
            sources: Source information (auto-registered)
            progress_callback: Progress callback (current, total)
        
        Returns:
            Fusion result with fused claims
        """
        # Register sources
        if sources:
            for source in sources:
                self.source_registry.register(source)
        
        # Find all matches
        matches = self.claim_matcher.find_matches(claims, threshold=0.65)
        
        # Group claims by similarity clusters
        clusters = self._cluster_claims(claims, matches)
        
        fused_claims = []
        conflicts_resolved = 0
        unresolved = 0
        
        for i, cluster in enumerate(clusters):
            if progress_callback:
                progress_callback(i + 1, len(clusters))
            
            # Separate agreeing and conflicting claims
            conflicts = [m for m in matches if m.is_conflict and self._in_cluster(m, cluster)]
            
            # Resolve conflicts
            if conflicts:
                for conflict_match in conflicts:
                    conflict_claims = [c for c in cluster if c.nid in (conflict_match.claim1_nid, conflict_match.claim2_nid)]
                    resolution = self.conflict_resolver.resolve(
                        conflict_claims,
                        self.conflict_resolver.detect_type(conflict_claims[0], conflict_claims[1]) if len(conflict_claims) >= 2 else None,
                    )
                    
                    if resolution.is_resolved:
                        conflicts_resolved += 1
                        # Remove losing claims from cluster
                        cluster = [c for c in cluster if c.nid not in resolution.losing_nids]
                    else:
                        unresolved += 1
            
            # Fuse remaining claims in cluster
            if cluster:
                fused = self._fuse_cluster(cluster)
                fused_claims.append(fused)
        
        # Compute stats
        total_uncertainty = sum(
            1.0 - c.metadata.get("confidence", 0.5)
            for c in claims
        ) / max(len(claims), 1)
        
        fused_uncertainty = sum(
            fc.uncertainty for fc in fused_claims
        ) / max(len(fused_claims), 1)
        
        stats = FusionStats(
            claims_fused=len(claims),
            original_uncertainty=total_uncertainty,
            fused_uncertainty=fused_uncertainty,
            uncertainty_reduction=total_uncertainty - fused_uncertainty,
        )
        
        result = FusionResult(
            fused_claims=fused_claims,
            claims_processed=len(claims),
            conflicts_resolved=conflicts_resolved,
            unresolved_conflicts=unresolved,
            stats=stats,
        )
        
        self._log_fusion(result)
        
        return result
    
    def _cluster_claims(
        self,
        claims: list[ClaimInfo],
        matches: list[MatchResult],
    ) -> list[list[ClaimInfo]]:
        """Cluster claims by similarity using union-find."""
        # Simple clustering: group by strong matches
        claim_map = {c.nid: c for c in claims}
        clusters: dict[int, set[int]] = {}
        
        # Initialize each claim in its own cluster
        for claim in claims:
            clusters[claim.nid] = {claim.nid}
        
        # Merge clusters for matching claims
        for match in matches:
            if match.match_type in (MatchType.IDENTICAL, MatchType.PARAPHRASE, MatchType.SUBSUMES):
                nid1, nid2 = match.claim1_nid, match.claim2_nid
                
                # Find clusters
                cluster1 = None
                cluster2 = None
                for root, members in clusters.items():
                    if nid1 in members:
                        cluster1 = root
                    if nid2 in members:
                        cluster2 = root
                
                # Merge if different clusters
                if cluster1 is not None and cluster2 is not None and cluster1 != cluster2:
                    clusters[cluster1] |= clusters[cluster2]
                    del clusters[cluster2]
        
        # Convert to claim lists
        return [
            [claim_map[nid] for nid in members if nid in claim_map]
            for members in clusters.values()
        ]
    
    def _in_cluster(self, match: MatchResult, cluster: list[ClaimInfo]) -> bool:
        """Check if match involves claims in cluster."""
        nids = {c.nid for c in cluster}
        return match.claim1_nid in nids or match.claim2_nid in nids
    
    def _fuse_cluster(self, cluster: list[ClaimInfo]) -> FusedClaim:
        """Fuse a cluster of related claims."""
        if not cluster:
            return FusedClaim(
                text="",
                nids=[],
                source_nids=[],
                confidence=0.0,
                uncertainty=1.0,
                provenance=[],
                resolved_conflicts=0,
            )
        
        # Create uncertain claims for Bayesian fusion
        uncertain_claims = []
        for claim in cluster:
            source_weight = 1.0
            if claim.source_nid:
                source_weight = self.source_registry.get_weight(claim.source_nid)
            
            uc = UncertainClaim(
                nid=claim.nid,
                text=claim.text,
                mean_confidence=claim.metadata.get("confidence", 0.5),
                std_confidence=claim.metadata.get("uncertainty", 0.3),
                source_nid=claim.source_nid,
                source_weight=source_weight,
            )
            uncertain_claims.append(uc)
        
        # Bayesian fusion
        fused = bayesian_fuse(uncertain_claims)
        
        # Use longest/most detailed claim as text
        best_claim = max(cluster, key=lambda c: len(c.text))
        
        # Collect provenance
        provenance = []
        for claim in cluster:
            if claim.source_nid:
                source = self.source_registry.get(claim.source_nid)
                if source and source.url:
                    provenance.append(source.url)
                elif source:
                    provenance.append(source.name or f"source-{claim.source_nid}")
        
        return FusedClaim(
            text=best_claim.text,
            nids=[c.nid for c in cluster],
            source_nids=[c.source_nid for c in cluster if c.source_nid],
            confidence=fused.mean_confidence,
            uncertainty=fused.std_confidence,
            provenance=list(set(provenance)),
            resolved_conflicts=0,
        )
    
    def _log_fusion(self, result: FusionResult) -> None:
        """Log fusion operation."""
        self._fusion_log.append({
            "claims_processed": result.claims_processed,
            "fused_claims": len(result.fused_claims),
            "conflicts_resolved": result.conflicts_resolved,
            "unresolved": result.unresolved_conflicts,
            "uncertainty_reduction": result.stats.uncertainty_reduction,
        })
    
    def get_fusion_log(self) -> list[dict[str, Any]]:
        """Get fusion operation log."""
        return self._fusion_log.copy()
