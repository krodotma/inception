"""
Ontology linker for connecting entities to semantic web resources.

Design by OPUS-1: Multi-ontology linking with NIL detection.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any
from difflib import SequenceMatcher

from inception.enhance.synthesis.ontology.wikidata import WikidataClient, WikidataEntity
from inception.enhance.synthesis.ontology.dbpedia import DBpediaClient, DBpediaEntity

logger = logging.getLogger(__name__)


@dataclass
class LinkedEntity:
    """An entity linked to ontology resources."""
    
    nid: int
    name: str
    entity_type: str = ""
    
    # Linked resources
    wikidata_qid: str | None = None
    wikidata_label: str = ""
    dbpedia_uri: str | None = None
    dbpedia_label: str = ""
    schema_org_type: str | None = None
    
    # Linking metadata
    linking_confidence: float = 0.0
    is_nil: bool = False  # No matching entity in KBs
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_linked(self) -> bool:
        """Check if entity is linked to any ontology."""
        return bool(self.wikidata_qid or self.dbpedia_uri)
    
    @property
    def best_link(self) -> str | None:
        """Get best available link URL."""
        if self.wikidata_qid:
            return f"https://www.wikidata.org/wiki/{self.wikidata_qid}"
        elif self.dbpedia_uri:
            return self.dbpedia_uri
        return None


@dataclass
class LinkingResult:
    """Result of linking operation."""
    
    linked_entities: list[LinkedEntity]
    total_entities: int
    linked_count: int
    nil_count: int
    
    @property
    def linking_rate(self) -> float:
        """Percentage of entities successfully linked."""
        if self.total_entities == 0:
            return 0.0
        return self.linked_count / self.total_entities


class OntologyLinker:
    """
    Links entities to Wikidata, DBpedia, and Schema.org.
    
    Workflow:
    1. Candidate generation (search KBs)
    2. Candidate ranking (string + context similarity)
    3. NIL detection (no match above threshold)
    4. Link validation (type consistency)
    """
    
    # Thresholds
    LINK_THRESHOLD = 0.7  # Minimum confidence to accept a link
    NIL_THRESHOLD = 0.4   # Below this, mark as NIL
    
    def __init__(
        self,
        wikidata_client: WikidataClient | None = None,
        dbpedia_client: DBpediaClient | None = None,
    ):
        """Initialize ontology linker."""
        self.wikidata = wikidata_client or WikidataClient()
        self.dbpedia = dbpedia_client or DBpediaClient()
        
        self._schema_org_types = self._init_schema_org()
        self._cache: dict[str, LinkedEntity] = {}
    
    def _init_schema_org(self) -> dict[str, str]:
        """Initialize Schema.org type mappings."""
        return {
            # People
            "person": "https://schema.org/Person",
            "human": "https://schema.org/Person",
            "actor": "https://schema.org/Person",
            "author": "https://schema.org/Person",
            
            # Organizations
            "organization": "https://schema.org/Organization",
            "company": "https://schema.org/Corporation",
            "university": "https://schema.org/CollegeOrUniversity",
            
            # Places
            "place": "https://schema.org/Place",
            "city": "https://schema.org/City",
            "country": "https://schema.org/Country",
            
            # Creative works
            "book": "https://schema.org/Book",
            "movie": "https://schema.org/Movie",
            "software": "https://schema.org/SoftwareApplication",
            
            # Events
            "event": "https://schema.org/Event",
            
            # Things
            "product": "https://schema.org/Product",
            "concept": "https://schema.org/Thing",
        }
    
    def link_entity(
        self,
        nid: int,
        name: str,
        entity_type: str = "",
        context: str = "",
    ) -> LinkedEntity:
        """
        Link a single entity to ontology resources.
        
        Args:
            nid: Entity node ID
            name: Entity name
            entity_type: Known entity type
            context: Surrounding context for disambiguation
        
        Returns:
            Linked entity with ontology connections
        """
        # Check cache
        cache_key = f"{name}:{entity_type}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            return LinkedEntity(
                nid=nid,
                name=name,
                entity_type=entity_type,
                wikidata_qid=cached.wikidata_qid,
                wikidata_label=cached.wikidata_label,
                dbpedia_uri=cached.dbpedia_uri,
                dbpedia_label=cached.dbpedia_label,
                schema_org_type=cached.schema_org_type,
                linking_confidence=cached.linking_confidence,
                is_nil=cached.is_nil,
            )
        
        result = LinkedEntity(
            nid=nid,
            name=name,
            entity_type=entity_type,
        )
        
        # Try Wikidata first
        wikidata_result = self._link_wikidata(name, entity_type, context)
        if wikidata_result:
            result.wikidata_qid = wikidata_result.qid
            result.wikidata_label = wikidata_result.label
            result.linking_confidence = max(result.linking_confidence, 0.8)
        
        # Try DBpedia
        dbpedia_result = self._link_dbpedia(name, entity_type)
        if dbpedia_result:
            result.dbpedia_uri = dbpedia_result.uri
            result.dbpedia_label = dbpedia_result.label
            result.linking_confidence = max(result.linking_confidence, 0.7)
        
        # Map to Schema.org type
        result.schema_org_type = self._map_schema_org(entity_type)
        
        # Check if NIL
        if not result.is_linked:
            result.is_nil = True
            result.linking_confidence = 0.0
        
        # Cache result
        self._cache[cache_key] = result
        
        return result
    
    def link_entities(
        self,
        entities: list[tuple[int, str, str]],  # (nid, name, type)
        context_map: dict[int, str] | None = None,
        progress_callback=None,
    ) -> LinkingResult:
        """
        Link multiple entities.
        
        Args:
            entities: List of (nid, name, type) tuples
            context_map: Optional context for each NID
            progress_callback: Progress callback (current, total)
        
        Returns:
            Linking result with all entities
        """
        context_map = context_map or {}
        linked = []
        nil_count = 0
        
        for i, (nid, name, entity_type) in enumerate(entities):
            if progress_callback:
                progress_callback(i + 1, len(entities))
            
            context = context_map.get(nid, "")
            result = self.link_entity(nid, name, entity_type, context)
            linked.append(result)
            
            if result.is_nil:
                nil_count += 1
        
        linked_count = sum(1 for e in linked if e.is_linked)
        
        return LinkingResult(
            linked_entities=linked,
            total_entities=len(entities),
            linked_count=linked_count,
            nil_count=nil_count,
        )
    
    def _link_wikidata(
        self,
        name: str,
        entity_type: str,
        context: str,
    ) -> WikidataEntity | None:
        """Try to link to Wikidata."""
        candidates = self.wikidata.search(name, limit=5)
        
        if not candidates:
            return None
        
        best = None
        best_score = 0.0
        
        for candidate in candidates:
            score = self._score_candidate(
                name, entity_type, context,
                candidate.label, candidate.description,
            )
            
            if score > best_score and score >= self.LINK_THRESHOLD:
                best_score = score
                best = candidate
        
        return best
    
    def _link_dbpedia(
        self,
        name: str,
        entity_type: str,
    ) -> DBpediaEntity | None:
        """Try to link to DBpedia."""
        candidates = self.dbpedia.lookup(name, limit=3)
        
        if not candidates:
            return None
        
        best = None
        best_score = 0.0
        
        for candidate in candidates:
            score = self._score_candidate(
                name, entity_type, "",
                candidate.label, candidate.abstract,
            )
            
            if score > best_score and score >= self.LINK_THRESHOLD:
                best_score = score
                best = candidate
        
        return best
    
    def _score_candidate(
        self,
        query_name: str,
        query_type: str,
        query_context: str,
        candidate_label: str,
        candidate_desc: str,
    ) -> float:
        """Score a candidate match."""
        # String similarity
        name_sim = SequenceMatcher(
            None, query_name.lower(), candidate_label.lower()
        ).ratio()
        
        # Type match bonus
        type_bonus = 0.0
        if query_type and candidate_desc:
            if query_type.lower() in candidate_desc.lower():
                type_bonus = 0.15
        
        # Context overlap
        context_bonus = 0.0
        if query_context and candidate_desc:
            context_words = set(query_context.lower().split())
            desc_words = set(candidate_desc.lower().split())
            if context_words & desc_words:
                context_bonus = 0.1
        
        return min(1.0, name_sim + type_bonus + context_bonus)
    
    def _map_schema_org(self, entity_type: str) -> str | None:
        """Map entity type to Schema.org type."""
        if not entity_type:
            return None
        
        normalized = entity_type.lower().strip()
        return self._schema_org_types.get(normalized)
