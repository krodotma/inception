"""
Entity extraction and resolution module.

Uses spaCy for NER with entity type classification and coreference resolution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

import spacy
from spacy.tokens import Doc, Span as SpacySpan

from inception.config import get_config
from inception.db.keys import NodeKind
from inception.db.records import Confidence


@dataclass
class Entity:
    """An extracted entity."""
    
    text: str
    entity_type: str
    
    # Position in source text
    start_char: int = 0
    end_char: int = 0
    
    # Normalized form
    normalized: str | None = None
    
    # Linking
    wikidata_id: str | None = None
    wikipedia_url: str | None = None
    
    # Confidence
    confidence: float = 1.0
    
    # Coreference
    coreferent_cluster: int | None = None
    is_representative: bool = True
    
    # Source span info
    source_span_nid: int | None = None
    
    @property
    def kind(self) -> NodeKind:
        return NodeKind.ENTITY


@dataclass
class EntityCluster:
    """A cluster of coreferent entity mentions."""
    
    cluster_id: int
    entities: list[Entity] = field(default_factory=list)
    representative: Entity | None = None
    
    @property
    def mention_count(self) -> int:
        return len(self.entities)
    
    @property
    def canonical_text(self) -> str:
        if self.representative:
            return self.representative.text
        return self.entities[0].text if self.entities else ""


@dataclass
class EntityExtractionResult:
    """Result of entity extraction from text."""
    
    entities: list[Entity] = field(default_factory=list)
    clusters: list[EntityCluster] = field(default_factory=list)
    
    # Statistics
    entity_counts: dict[str, int] = field(default_factory=dict)
    
    def get_by_type(self, entity_type: str) -> list[Entity]:
        """Get entities of a specific type."""
        return [e for e in self.entities if e.entity_type == entity_type]
    
    def get_unique_entities(self) -> list[Entity]:
        """Get only representative entities from clusters."""
        return [e for e in self.entities if e.is_representative]


class EntityExtractor:
    """
    Entity extractor using spaCy.
    
    Extracts named entities with type classification and
    optional coreference resolution.
    """
    
    def __init__(
        self,
        model_name: str = "en_core_web_sm",
        use_coreference: bool = False,
    ):
        """
        Initialize the extractor.
        
        Args:
            model_name: spaCy model name
            use_coreference: Whether to use coreference resolution
        """
        self.model_name = model_name
        self.use_coreference = use_coreference
        self._nlp = None
    
    def _get_nlp(self):
        """Lazy-load spaCy model."""
        if self._nlp is None:
            self._nlp = spacy.load(self.model_name)
        return self._nlp
    
    def extract(self, text: str) -> EntityExtractionResult:
        """
        Extract entities from text.
        
        Args:
            text: Input text
        
        Returns:
            EntityExtractionResult with entities and clusters
        """
        nlp = self._get_nlp()
        doc = nlp(text)
        
        entities = []
        entity_counts: dict[str, int] = {}
        
        for ent in doc.ents:
            entity = Entity(
                text=ent.text,
                entity_type=ent.label_,
                start_char=ent.start_char,
                end_char=ent.end_char,
                normalized=ent.text.lower(),
            )
            entities.append(entity)
            
            # Count by type
            entity_counts[ent.label_] = entity_counts.get(ent.label_, 0) + 1
        
        # Build clusters based on exact text match (simple dedup)
        clusters = self._build_clusters(entities)
        
        return EntityExtractionResult(
            entities=entities,
            clusters=clusters,
            entity_counts=entity_counts,
        )
    
    def extract_batch(
        self,
        texts: list[str],
    ) -> Iterator[EntityExtractionResult]:
        """
        Extract entities from multiple texts efficiently.
        
        Args:
            texts: List of input texts
        
        Yields:
            EntityExtractionResult for each text
        """
        nlp = self._get_nlp()
        
        for doc in nlp.pipe(texts, batch_size=50):
            entities = []
            entity_counts: dict[str, int] = {}
            
            for ent in doc.ents:
                entity = Entity(
                    text=ent.text,
                    entity_type=ent.label_,
                    start_char=ent.start_char,
                    end_char=ent.end_char,
                    normalized=ent.text.lower(),
                )
                entities.append(entity)
                entity_counts[ent.label_] = entity_counts.get(ent.label_, 0) + 1
            
            clusters = self._build_clusters(entities)
            
            yield EntityExtractionResult(
                entities=entities,
                clusters=clusters,
                entity_counts=entity_counts,
            )
    
    def _build_clusters(
        self,
        entities: list[Entity],
    ) -> list[EntityCluster]:
        """Build entity clusters based on normalized text."""
        cluster_map: dict[str, list[Entity]] = {}
        
        for entity in entities:
            key = (entity.normalized or entity.text.lower(), entity.entity_type)
            key_str = f"{key[0]}|{key[1]}"
            
            if key_str not in cluster_map:
                cluster_map[key_str] = []
            cluster_map[key_str].append(entity)
        
        clusters = []
        for i, (key, ents) in enumerate(cluster_map.items()):
            # Mark representative
            representative = max(ents, key=lambda e: len(e.text))
            representative.is_representative = True
            
            for ent in ents:
                ent.coreferent_cluster = i
                if ent != representative:
                    ent.is_representative = False
            
            cluster = EntityCluster(
                cluster_id=i,
                entities=ents,
                representative=representative,
            )
            clusters.append(cluster)
        
        return clusters


# Entity type mapping from spaCy to our canonical types
ENTITY_TYPE_MAP = {
    "PERSON": "PERSON",
    "ORG": "ORGANIZATION",
    "GPE": "LOCATION",
    "LOC": "LOCATION",
    "PRODUCT": "PRODUCT",
    "WORK_OF_ART": "WORK",
    "EVENT": "EVENT",
    "LAW": "LAW",
    "LANGUAGE": "LANGUAGE",
    "DATE": "DATE",
    "TIME": "TIME",
    "MONEY": "MONEY",
    "QUANTITY": "QUANTITY",
    "ORDINAL": "ORDINAL",
    "CARDINAL": "NUMBER",
    "PERCENT": "PERCENT",
    "NORP": "GROUP",  # Nationalities or religious or political groups
    "FAC": "FACILITY",
}


def normalize_entity_type(spacy_type: str) -> str:
    """Normalize spaCy entity type to canonical type."""
    return ENTITY_TYPE_MAP.get(spacy_type, spacy_type)


def extract_entities(text: str) -> EntityExtractionResult:
    """
    Convenience function to extract entities from text.
    
    Args:
        text: Input text
    
    Returns:
        EntityExtractionResult
    """
    extractor = EntityExtractor()
    return extractor.extract(text)


def resolve_entity(
    entity: Entity,
    context: str | None = None,
) -> Entity:
    """
    Resolve an entity to a canonical representation.
    
    This is a placeholder for entity linking/resolution.
    Could be enhanced with:
    - Wikidata/Wikipedia linking
    - Knowledge graph lookup
    - Embedding-based similarity
    
    Args:
        entity: Entity to resolve
        context: Optional context text
    
    Returns:
        Entity with resolved linking info
    """
    # For now, just normalize the text
    entity.normalized = entity.text.strip().lower()
    return entity
