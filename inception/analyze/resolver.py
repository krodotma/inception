"""
Entity Resolution Enhancement - Swarm Track 4

Advanced entity linking, disambiguation, and knowledge graph integration.
Enhances the base EntityExtractor with embedding-based resolution.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class ResolutionStrategy(Enum):
    """Entity resolution strategies."""
    EXACT = "exact"           # Exact text match
    FUZZY = "fuzzy"           # Fuzzy string match
    EMBEDDING = "embedding"   # Embedding similarity
    GRAPH = "graph"           # Knowledge graph lookup
    ENSEMBLE = "ensemble"     # Multiple strategies


class EntityConfidence(Enum):
    """Confidence levels for entity resolution."""
    HIGH = "high"         # >0.9 confidence
    MEDIUM = "medium"     # 0.7-0.9
    LOW = "low"           # 0.5-0.7
    UNCERTAIN = "uncertain"  # <0.5


@dataclass
class ResolvedEntity:
    """An entity with resolution metadata."""
    text: str
    entity_type: str
    
    # Canonical form
    canonical_name: str = ""
    canonical_id: str | None = None
    
    # External IDs
    wikidata_qid: str | None = None
    dbpedia_uri: str | None = None
    wikipedia_url: str | None = None
    
    # Disambiguation
    disambiguation_context: str = ""
    alternative_resolutions: list[dict] = field(default_factory=list)
    
    # Confidence
    confidence: float = 0.0
    confidence_level: EntityConfidence = EntityConfidence.UNCERTAIN
    strategy_used: ResolutionStrategy = ResolutionStrategy.EXACT
    
    # Relations discovered
    related_entities: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "type": self.entity_type,
            "canonical_name": self.canonical_name,
            "canonical_id": self.canonical_id,
            "wikidata": self.wikidata_qid,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level.value,
        }


@dataclass
class EntityCandidate:
    """A candidate for entity resolution."""
    name: str
    entity_id: str
    entity_type: str
    description: str = ""
    aliases: list[str] = field(default_factory=list)
    score: float = 0.0


class EntityResolver:
    """
    Advanced entity resolution with multiple strategies.
    """
    
    def __init__(
        self,
        strategy: ResolutionStrategy = ResolutionStrategy.ENSEMBLE,
        embedding_threshold: float = 0.75,
        fuzzy_threshold: float = 0.85,
    ):
        self.strategy = strategy
        self.embedding_threshold = embedding_threshold
        self.fuzzy_threshold = fuzzy_threshold
        
        # Entity cache
        self._cache: dict[str, ResolvedEntity] = {}
        
        # Knowledge base (in production, would be external)
        self._kb: dict[str, EntityCandidate] = {}
    
    def resolve(
        self,
        text: str,
        entity_type: str,
        context: str = "",
    ) -> ResolvedEntity:
        """
        Resolve an entity mention to a canonical form.
        
        Args:
            text: Entity text
            entity_type: Entity type
            context: Surrounding context for disambiguation
        
        Returns:
            ResolvedEntity with resolution metadata
        """
        cache_key = self._cache_key(text, entity_type)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Generate candidates
        candidates = self._generate_candidates(text, entity_type)
        
        # Score candidates
        if self.strategy == ResolutionStrategy.EXACT:
            scored = self._score_exact(text, candidates)
        elif self.strategy == ResolutionStrategy.FUZZY:
            scored = self._score_fuzzy(text, candidates)
        elif self.strategy == ResolutionStrategy.EMBEDDING:
            scored = self._score_embedding(text, context, candidates)
        else:
            scored = self._score_ensemble(text, context, candidates)
        
        # Select best candidate
        if scored:
            best = max(scored, key=lambda c: c.score)
            resolved = self._create_resolved(text, entity_type, best)
            
            # Add alternatives
            alternatives = [c for c in scored if c != best][:3]
            resolved.alternative_resolutions = [
                {"name": c.name, "id": c.entity_id, "score": c.score}
                for c in alternatives
            ]
        else:
            resolved = self._create_nil_entity(text, entity_type)
        
        self._cache[cache_key] = resolved
        return resolved
    
    def resolve_batch(
        self,
        entities: list[tuple[str, str, str]],
    ) -> list[ResolvedEntity]:
        """
        Resolve multiple entities.
        
        Args:
            entities: List of (text, entity_type, context) tuples
        
        Returns:
            List of ResolvedEntity
        """
        return [
            self.resolve(text, etype, ctx)
            for text, etype, ctx in entities
        ]
    
    def _cache_key(self, text: str, entity_type: str) -> str:
        """Generate cache key."""
        return hashlib.md5(f"{text}|{entity_type}".encode()).hexdigest()[:16]
    
    def _generate_candidates(
        self,
        text: str,
        entity_type: str,
    ) -> list[EntityCandidate]:
        """Generate resolution candidates."""
        candidates = []
        
        # Check knowledge base
        for entity_id, candidate in self._kb.items():
            if candidate.entity_type == entity_type:
                # Check name match
                if text.lower() in candidate.name.lower():
                    candidates.append(candidate)
                # Check aliases
                elif any(text.lower() in a.lower() for a in candidate.aliases):
                    candidates.append(candidate)
        
        # Generate synthetic candidate from text
        if not candidates:
            synthetic = EntityCandidate(
                name=text,
                entity_id=f"nil:{hashlib.md5(text.encode()).hexdigest()[:8]}",
                entity_type=entity_type,
            )
            candidates.append(synthetic)
        
        return candidates
    
    def _score_exact(
        self,
        text: str,
        candidates: list[EntityCandidate],
    ) -> list[EntityCandidate]:
        """Score candidates with exact matching."""
        for c in candidates:
            if text.lower() == c.name.lower():
                c.score = 1.0
            elif text.lower() in [a.lower() for a in c.aliases]:
                c.score = 0.95
            else:
                c.score = 0.0
        return candidates
    
    def _score_fuzzy(
        self,
        text: str,
        candidates: list[EntityCandidate],
    ) -> list[EntityCandidate]:
        """Score candidates with fuzzy matching."""
        for c in candidates:
            c.score = self._levenshtein_similarity(text.lower(), c.name.lower())
        return candidates
    
    def _score_embedding(
        self,
        text: str,
        context: str,
        candidates: list[EntityCandidate],
    ) -> list[EntityCandidate]:
        """Score candidates with embedding similarity."""
        # Placeholder - would use actual embeddings
        for c in candidates:
            base_score = self._levenshtein_similarity(text.lower(), c.name.lower())
            
            # Context bonus if description matches
            context_bonus = 0.0
            if context and c.description:
                overlap = len(set(context.lower().split()) & 
                            set(c.description.lower().split()))
                context_bonus = min(overlap * 0.05, 0.2)
            
            c.score = min(base_score + context_bonus, 1.0)
        return candidates
    
    def _score_ensemble(
        self,
        text: str,
        context: str,
        candidates: list[EntityCandidate],
    ) -> list[EntityCandidate]:
        """Score with multiple strategies combined."""
        # Get scores from each strategy
        exact_scores = {c.entity_id: c.score for c in self._score_exact(text, candidates)}
        fuzzy_scores = {c.entity_id: c.score for c in self._score_fuzzy(text, candidates)}
        embed_scores = {c.entity_id: c.score for c in self._score_embedding(text, context, candidates)}
        
        # Combine with weights
        weights = {"exact": 0.4, "fuzzy": 0.3, "embedding": 0.3}
        
        for c in candidates:
            c.score = (
                weights["exact"] * exact_scores.get(c.entity_id, 0) +
                weights["fuzzy"] * fuzzy_scores.get(c.entity_id, 0) +
                weights["embedding"] * embed_scores.get(c.entity_id, 0)
            )
        
        return candidates
    
    def _levenshtein_similarity(self, s1: str, s2: str) -> float:
        """Compute Levenshtein similarity."""
        if not s1 or not s2:
            return 0.0
        
        len_s1, len_s2 = len(s1), len(s2)
        if len_s1 < len_s2:
            s1, s2 = s2, s1
            len_s1, len_s2 = len_s2, len_s1
        
        # Use prefix for efficiency
        if len_s1 > 50:
            s1, s2 = s1[:50], s2[:50]
            len_s1, len_s2 = len(s1), len(s2)
        
        distances = range(len_s2 + 1)
        for i, c1 in enumerate(s1):
            new_distances = [i + 1]
            for j, c2 in enumerate(s2):
                if c1 == c2:
                    new_distances.append(distances[j])
                else:
                    new_distances.append(1 + min(
                        distances[j], distances[j + 1], new_distances[-1]
                    ))
            distances = new_distances
        
        distance = distances[-1]
        max_len = max(len_s1, len_s2)
        return 1.0 - (distance / max_len)
    
    def _create_resolved(
        self,
        text: str,
        entity_type: str,
        candidate: EntityCandidate,
    ) -> ResolvedEntity:
        """Create ResolvedEntity from candidate."""
        confidence = candidate.score
        if confidence >= 0.9:
            level = EntityConfidence.HIGH
        elif confidence >= 0.7:
            level = EntityConfidence.MEDIUM
        elif confidence >= 0.5:
            level = EntityConfidence.LOW
        else:
            level = EntityConfidence.UNCERTAIN
        
        return ResolvedEntity(
            text=text,
            entity_type=entity_type,
            canonical_name=candidate.name,
            canonical_id=candidate.entity_id,
            confidence=confidence,
            confidence_level=level,
            strategy_used=self.strategy,
        )
    
    def _create_nil_entity(
        self,
        text: str,
        entity_type: str,
    ) -> ResolvedEntity:
        """Create NIL entity for unresolved mentions."""
        return ResolvedEntity(
            text=text,
            entity_type=entity_type,
            canonical_name=text,
            canonical_id=f"nil:{hashlib.md5(text.encode()).hexdigest()[:8]}",
            confidence=0.0,
            confidence_level=EntityConfidence.UNCERTAIN,
        )
    
    def register_entity(self, candidate: EntityCandidate) -> None:
        """Register an entity in the knowledge base."""
        self._kb[candidate.entity_id] = candidate
    
    def stats(self) -> dict[str, Any]:
        """Get resolver statistics."""
        return {
            "cache_size": len(self._cache),
            "kb_size": len(self._kb),
            "strategy": self.strategy.value,
        }


class RelationExtractor:
    """
    Extract relationships between entities.
    """
    
    # Common relation patterns
    PATTERNS = [
        (r"(\w+)\s+is\s+the\s+(\w+)\s+of\s+(\w+)", "role_of"),
        (r"(\w+)\s+works?\s+(?:at|for)\s+(\w+)", "works_for"),
        (r"(\w+)\s+founded\s+(\w+)", "founded"),
        (r"(\w+)\s+is\s+located\s+in\s+(\w+)", "located_in"),
        (r"(\w+)\s+acquired\s+(\w+)", "acquired"),
        (r"(\w+)\s+partnered?\s+with\s+(\w+)", "partners_with"),
    ]
    
    def __init__(self):
        self._compiled = [(re.compile(p, re.I), rel) for p, rel in self.PATTERNS]
    
    def extract(
        self,
        text: str,
        entities: list[tuple[str, str]],
    ) -> list[tuple[str, str, str]]:
        """
        Extract relations from text.
        
        Args:
            text: Source text
            entities: List of (text, type) tuples
        
        Returns:
            List of (subject, relation, object) tuples
        """
        relations = []
        entity_texts = {e[0].lower() for e in entities}
        
        for pattern, rel_type in self._compiled:
            for match in pattern.finditer(text):
                groups = match.groups()
                if len(groups) >= 2:
                    subj = groups[0]
                    obj = groups[-1]
                    
                    # Verify entities exist
                    if (subj.lower() in entity_texts or 
                        obj.lower() in entity_texts):
                        relations.append((subj, rel_type, obj))
        
        return relations
