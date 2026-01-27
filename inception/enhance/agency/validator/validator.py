"""
Fact validator for claim verification.

Validates claims against authoritative sources and
updates knowledge graph with validation status.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from inception.enhance.agency.validator.sources import (
    ValidationSource,
    WikipediaSource,
    WikidataSource,
    SourceEvidence,
)

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Result of fact validation."""
    
    VERIFIED = auto()      # Claim confirmed by source
    CONTRADICTED = auto()  # Claim contradicted by source
    PARTIAL = auto()       # Partially supported
    UNVERIFIED = auto()    # No evidence found
    ERROR = auto()         # Validation failed


@dataclass
class ValidationResult:
    """Result of validating a claim."""
    
    nid: int
    claim_text: str
    status: ValidationStatus
    confidence: float  # Overall confidence (0-1)
    evidence: list[SourceEvidence] = field(default_factory=list)
    explanation: str = ""
    
    @property
    def is_reliable(self) -> bool:
        """Check if claim is considered reliable."""
        return (
            self.status == ValidationStatus.VERIFIED and
            self.confidence >= 0.7
        )


class FactValidator:
    """
    Validates claims against authoritative sources.
    
    Workflow:
    1. Extract claim components (subject, predicate, object)
    2. Search sources for evidence
    3. Compare claim with evidence
    4. Return validation status
    """
    
    def __init__(
        self,
        sources: list[ValidationSource] | None = None,
        use_llm: bool = False,
    ):
        """
        Initialize fact validator.
        
        Args:
            sources: Validation sources to use
            use_llm: Use LLM for claim-evidence comparison
        """
        if sources is None:
            sources = [
                WikipediaSource(),
                WikidataSource(),
            ]
        
        self.sources = sources
        self.use_llm = use_llm
        self._llm = None
        
        self._validation_cache: dict[int, ValidationResult] = {}
        self._stats = {"validated": 0, "verified": 0, "contradicted": 0}
    
    @property
    def stats(self) -> dict[str, int]:
        """Get validation statistics."""
        return self._stats.copy()
    
    def validate(
        self,
        nid: int,
        payload: dict[str, Any],
    ) -> ValidationResult:
        """
        Validate a claim node.
        
        Args:
            nid: Claim node ID
            payload: Claim payload with text, subject, predicate, object
        
        Returns:
            Validation result
        """
        # Check cache
        if nid in self._validation_cache:
            return self._validation_cache[nid]
        
        # Extract claim components
        claim_text = payload.get("text", "")
        subject = payload.get("subject", "")
        predicate = payload.get("predicate", "")
        obj = payload.get("object", "")
        
        if not claim_text and subject:
            claim_text = f"{subject} {predicate} {obj}"
        
        # Generate search query
        query = self._generate_query(subject, predicate, obj, claim_text)
        
        # Search all sources
        all_evidence: list[SourceEvidence] = []
        for source in self.sources:
            if source.is_available():
                evidence = source.search(query)
                all_evidence.extend(evidence)
        
        if not all_evidence:
            result = ValidationResult(
                nid=nid,
                claim_text=claim_text,
                status=ValidationStatus.UNVERIFIED,
                confidence=0.0,
                explanation="No evidence found in any source",
            )
        else:
            # Analyze evidence
            result = self._analyze_evidence(nid, claim_text, all_evidence)
        
        # Update stats
        self._stats["validated"] += 1
        if result.status == ValidationStatus.VERIFIED:
            self._stats["verified"] += 1
        elif result.status == ValidationStatus.CONTRADICTED:
            self._stats["contradicted"] += 1
        
        # Cache result
        self._validation_cache[nid] = result
        
        return result
    
    def _generate_query(
        self,
        subject: str,
        predicate: str,
        obj: str,
        text: str,
    ) -> str:
        """Generate search query from claim components."""
        if subject and obj:
            return f"{subject} {obj}"
        elif subject:
            return subject
        else:
            # Use first few words of text
            words = text.split()[:5]
            return " ".join(words)
    
    def _analyze_evidence(
        self,
        nid: int,
        claim_text: str,
        evidence: list[SourceEvidence],
    ) -> ValidationResult:
        """Analyze evidence to determine validation status."""
        claim_lower = claim_text.lower()
        
        # Simple keyword matching (would use LLM for production)
        support_score = 0.0
        contradict_score = 0.0
        
        relevant_evidence = []
        
        for ev in evidence:
            ev_text = ev.relevant_text.lower()
            
            # Check for keyword overlap
            claim_words = set(claim_lower.split())
            ev_words = set(ev_text.split())
            
            overlap = len(claim_words & ev_words)
            overlap_ratio = overlap / max(len(claim_words), 1)
            
            if overlap_ratio > 0.3:
                relevant_evidence.append(ev)
                support_score += ev.confidence * overlap_ratio
            
            # Simple contradiction detection (very basic)
            negations = ["not", "never", "false", "incorrect", "wrong"]
            has_negation = any(n in ev_text for n in negations)
            
            if has_negation and overlap_ratio > 0.3:
                contradict_score += 0.3
        
        # Determine status
        if support_score > 0.7 and contradict_score < 0.3:
            status = ValidationStatus.VERIFIED
            confidence = min(support_score, 1.0)
            explanation = f"Supported by {len(relevant_evidence)} source(s)"
        elif contradict_score > support_score:
            status = ValidationStatus.CONTRADICTED
            confidence = min(contradict_score, 1.0)
            explanation = "Evidence suggests contradiction"
        elif support_score > 0.3:
            status = ValidationStatus.PARTIAL
            confidence = support_score / 2
            explanation = "Partial support found"
        else:
            status = ValidationStatus.UNVERIFIED
            confidence = 0.0
            explanation = "Insufficient evidence"
        
        return ValidationResult(
            nid=nid,
            claim_text=claim_text,
            status=status,
            confidence=confidence,
            evidence=relevant_evidence,
            explanation=explanation,
        )
    
    def validate_batch(
        self,
        claims: list[tuple[int, dict[str, Any]]],
        progress_callback=None,
    ) -> list[ValidationResult]:
        """
        Validate multiple claims.
        
        Args:
            claims: List of (nid, payload) tuples
            progress_callback: Optional progress callback (current, total)
        
        Returns:
            List of validation results
        """
        results = []
        
        for i, (nid, payload) in enumerate(claims):
            if progress_callback:
                progress_callback(i + 1, len(claims))
            
            result = self.validate(nid, payload)
            results.append(result)
        
        return results
