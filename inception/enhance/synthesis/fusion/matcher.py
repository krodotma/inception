"""
Claim matcher for finding related claims across sources.

Design by OPUS-2: Uses vector embeddings for semantic matching.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

logger = logging.getLogger(__name__)


class MatchType(Enum):
    """Type of claim match."""
    
    IDENTICAL = auto()    # Same claim, same wording
    PARAPHRASE = auto()   # Same meaning, different words
    SUBSUMES = auto()     # One claim contains the other
    RELATED = auto()      # Related but not same claim
    CONTRADICTS = auto()  # Claims contradict each other
    UNRELATED = auto()    # No relationship


@dataclass
class MatchResult:
    """Result of matching two claims."""
    
    claim1_nid: int
    claim2_nid: int
    match_type: MatchType
    similarity: float  # 0-1 semantic similarity
    confidence: float  # Confidence in the match type
    details: str = ""
    
    @property
    def is_agreement(self) -> bool:
        """Check if claims agree."""
        return self.match_type in (
            MatchType.IDENTICAL,
            MatchType.PARAPHRASE,
            MatchType.SUBSUMES,
        )
    
    @property
    def is_conflict(self) -> bool:
        """Check if claims conflict."""
        return self.match_type == MatchType.CONTRADICTS


@dataclass
class ClaimInfo:
    """Information about a claim for matching."""
    
    nid: int
    text: str
    subject: str = ""
    predicate: str = ""
    obj: str = ""
    source_nid: int | None = None
    embedding: list[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ClaimMatcher:
    """
    Matches claims across sources using semantic similarity.
    
    Workflow:
    1. Compute embeddings for all claims
    2. Find similar claims using cosine similarity
    3. Classify match type (paraphrase, contradiction, etc.)
    """
    
    # Thresholds for match types
    IDENTICAL_THRESHOLD = 0.98
    PARAPHRASE_THRESHOLD = 0.85
    RELATED_THRESHOLD = 0.65
    
    def __init__(
        self,
        embedding_model: Any = None,  # EmbeddingModel from vectors
        use_llm_for_contradiction: bool = False,
    ):
        """
        Initialize the claim matcher.
        
        Args:
            embedding_model: Vector embedding model
            use_llm_for_contradiction: Use LLM to detect contradictions
        """
        self._embedding_model = embedding_model
        self._use_llm = use_llm_for_contradiction
        self._cache: dict[tuple[int, int], MatchResult] = {}
    
    def match(self, claim1: ClaimInfo, claim2: ClaimInfo) -> MatchResult:
        """
        Match two claims and determine their relationship.
        
        Args:
            claim1: First claim
            claim2: Second claim
        
        Returns:
            Match result with type and similarity
        """
        # Check cache
        key = (min(claim1.nid, claim2.nid), max(claim1.nid, claim2.nid))
        if key in self._cache:
            return self._cache[key]
        
        # Compute similarity
        similarity = self._compute_similarity(claim1, claim2)
        
        # Determine match type
        match_type, confidence = self._classify_match(
            claim1, claim2, similarity
        )
        
        result = MatchResult(
            claim1_nid=claim1.nid,
            claim2_nid=claim2.nid,
            match_type=match_type,
            similarity=similarity,
            confidence=confidence,
        )
        
        # Cache result
        self._cache[key] = result
        
        return result
    
    def find_matches(
        self,
        claims: list[ClaimInfo],
        threshold: float = 0.65,
    ) -> list[MatchResult]:
        """
        Find all matching claim pairs above threshold.
        
        Args:
            claims: List of claims to compare
            threshold: Minimum similarity threshold
        
        Returns:
            List of match results
        """
        matches = []
        
        for i, claim1 in enumerate(claims):
            for claim2 in claims[i + 1:]:
                result = self.match(claim1, claim2)
                
                if result.similarity >= threshold:
                    matches.append(result)
        
        return sorted(matches, key=lambda m: m.similarity, reverse=True)
    
    def find_contradictions(
        self,
        claims: list[ClaimInfo],
    ) -> list[MatchResult]:
        """Find all contradicting claim pairs."""
        all_matches = self.find_matches(claims, threshold=0.5)
        
        return [m for m in all_matches if m.is_conflict]
    
    def _compute_similarity(
        self,
        claim1: ClaimInfo,
        claim2: ClaimInfo,
    ) -> float:
        """Compute semantic similarity between claims."""
        # Use pre-computed embeddings if available
        if claim1.embedding and claim2.embedding:
            return self._cosine_similarity(claim1.embedding, claim2.embedding)
        
        # Compute embeddings on the fly
        if self._embedding_model:
            emb1 = self._embedding_model.encode(claim1.text)
            emb2 = self._embedding_model.encode(claim2.text)
            return self._cosine_similarity(emb1, emb2)
        
        # Fallback: Simple word overlap
        return self._word_overlap(claim1.text, claim2.text)
    
    def _cosine_similarity(self, v1: list[float], v2: list[float]) -> float:
        """Compute cosine similarity between vectors."""
        import math
        
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot / (norm1 * norm2)
    
    def _word_overlap(self, text1: str, text2: str) -> float:
        """Compute word overlap similarity."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _classify_match(
        self,
        claim1: ClaimInfo,
        claim2: ClaimInfo,
        similarity: float,
    ) -> tuple[MatchType, float]:
        """Classify the type of match between claims."""
        # Exact or near-exact match
        if similarity >= self.IDENTICAL_THRESHOLD:
            return MatchType.IDENTICAL, 0.95
        
        if similarity >= self.PARAPHRASE_THRESHOLD:
            # Check for contradiction in paraphrase
            if self._detect_negation(claim1.text, claim2.text):
                return MatchType.CONTRADICTS, 0.85
            return MatchType.PARAPHRASE, 0.85
        
        if similarity >= self.RELATED_THRESHOLD:
            # Check for subsumption
            if self._check_subsumption(claim1, claim2):
                return MatchType.SUBSUMES, 0.7
            
            # Check for contradiction
            if self._detect_contradiction(claim1, claim2):
                return MatchType.CONTRADICTS, 0.7
            
            return MatchType.RELATED, 0.6
        
        return MatchType.UNRELATED, 0.9
    
    def _detect_negation(self, text1: str, text2: str) -> bool:
        """Simple negation detection."""
        negation_words = {"not", "no", "never", "none", "without", "false"}
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        neg1 = bool(words1 & negation_words)
        neg2 = bool(words2 & negation_words)
        
        # One has negation, other doesn't
        return neg1 != neg2
    
    def _detect_contradiction(
        self,
        claim1: ClaimInfo,
        claim2: ClaimInfo,
    ) -> bool:
        """Detect if claims contradict each other."""
        # Same subject/predicate but different objects
        if claim1.subject and claim2.subject:
            if (
                claim1.subject.lower() == claim2.subject.lower() and
                claim1.predicate.lower() == claim2.predicate.lower() and
                claim1.obj.lower() != claim2.obj.lower()
            ):
                return True
        
        # Check for negation
        if self._detect_negation(claim1.text, claim2.text):
            return True
        
        return False
    
    def _check_subsumption(
        self,
        claim1: ClaimInfo,
        claim2: ClaimInfo,
    ) -> bool:
        """Check if one claim subsumes the other."""
        # Simple heuristic: longer claim might contain shorter
        text1 = claim1.text.lower()
        text2 = claim2.text.lower()
        
        if len(text1) > len(text2) * 1.5:
            # Check if key content of text2 is in text1
            words2 = set(text2.split())
            words1 = set(text1.split())
            if len(words2 - words1) < len(words2) * 0.3:
                return True
        
        return False
