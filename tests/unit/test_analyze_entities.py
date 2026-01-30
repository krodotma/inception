"""
Unit tests for analyze/entities.py

Tests for entity extraction:
- Entity, EntityCluster: Data classes
- EntityExtractionResult: Result class
- EntityExtractor: Main extractor
"""

import pytest

try:
    from inception.analyze.entities import (
        Entity,
        EntityCluster,
        EntityExtractionResult,
        EntityExtractor,
        normalize_entity_type,
        ENTITY_TYPE_MAP,
    )
    HAS_ENTITIES = True
except ImportError:
    HAS_ENTITIES = False


@pytest.mark.skipif(not HAS_ENTITIES, reason="entities module not available")
class TestEntity:
    """Tests for Entity dataclass."""
    
    def test_creation(self):
        """Test creating entity."""
        entity = Entity(text="Apple", entity_type="ORG")
        
        assert entity.text == "Apple"
        assert entity.entity_type == "ORG"
    
    def test_kind_property(self):
        """Test kind property returns NodeKind."""
        entity = Entity(text="Test", entity_type="PERSON")
        
        from inception.db.keys import NodeKind
        assert entity.kind == NodeKind.ENTITY
    
    def test_with_positions(self):
        """Test entity with character positions."""
        entity = Entity(
            text="Microsoft",
            entity_type="ORG",
            start_char=10,
            end_char=19,
        )
        
        assert entity.end_char - entity.start_char == 9
    
    def test_with_linking(self):
        """Test entity with Wikidata linking."""
        entity = Entity(
            text="Paris",
            entity_type="GPE",
            wikidata_id="Q90",
            wikipedia_url="https://en.wikipedia.org/wiki/Paris",
        )
        
        assert entity.wikidata_id == "Q90"


@pytest.mark.skipif(not HAS_ENTITIES, reason="entities module not available")
class TestEntityCluster:
    """Tests for EntityCluster dataclass."""
    
    def test_creation(self):
        """Test creating cluster."""
        cluster = EntityCluster(cluster_id=0)
        
        assert cluster.cluster_id == 0
        assert cluster.mention_count == 0
    
    def test_with_entities(self):
        """Test cluster with entities."""
        entities = [
            Entity(text="Apple Inc", entity_type="ORG"),
            Entity(text="Apple", entity_type="ORG"),
        ]
        cluster = EntityCluster(
            cluster_id=1,
            entities=entities,
            representative=entities[0],
        )
        
        assert cluster.mention_count == 2
        assert cluster.canonical_text == "Apple Inc"


@pytest.mark.skipif(not HAS_ENTITIES, reason="entities module not available")
class TestEntityExtractionResult:
    """Tests for EntityExtractionResult dataclass."""
    
    def test_creation(self):
        """Test creating result."""
        result = EntityExtractionResult()
        
        assert len(result.entities) == 0
        assert len(result.clusters) == 0
    
    def test_get_by_type(self):
        """Test filtering by type."""
        entities = [
            Entity(text="Apple", entity_type="ORG"),
            Entity(text="John", entity_type="PERSON"),
            Entity(text="Google", entity_type="ORG"),
        ]
        result = EntityExtractionResult(entities=entities)
        
        orgs = result.get_by_type("ORG")
        
        assert len(orgs) == 2
    
    def test_get_unique_entities(self):
        """Test getting unique entities."""
        entities = [
            Entity(text="Apple", entity_type="ORG", is_representative=True),
            Entity(text="Apple Inc", entity_type="ORG", is_representative=False),
        ]
        result = EntityExtractionResult(entities=entities)
        
        unique = result.get_unique_entities()
        
        assert len(unique) == 1


@pytest.mark.skipif(not HAS_ENTITIES, reason="entities module not available")
class TestEntityExtractor:
    """Tests for EntityExtractor."""
    
    def test_creation_default(self):
        """Test creating with defaults."""
        extractor = EntityExtractor()
        
        assert extractor.model_name == "en_core_web_sm"
        assert extractor.use_coreference is False
    
    def test_creation_custom(self):
        """Test creating with custom model."""
        extractor = EntityExtractor(model_name="en_core_web_lg")
        
        assert extractor.model_name == "en_core_web_lg"


@pytest.mark.skipif(not HAS_ENTITIES, reason="entities module not available")
class TestNormalizeEntityType:
    """Tests for normalize_entity_type function."""
    
    def test_known_type(self):
        """Test normalizing a known type."""
        assert normalize_entity_type("ORG") == "ORGANIZATION"
        assert normalize_entity_type("GPE") == "LOCATION"
    
    def test_unknown_type(self):
        """Test normalizing an unknown type."""
        assert normalize_entity_type("CUSTOM") == "CUSTOM"


@pytest.mark.skipif(not HAS_ENTITIES, reason="entities module not available")
class TestEntityTypeMap:
    """Tests for ENTITY_TYPE_MAP constant."""
    
    def test_contains_common_types(self):
        """Test map has common types."""
        assert "PERSON" in ENTITY_TYPE_MAP
        assert "ORG" in ENTITY_TYPE_MAP
        assert "GPE" in ENTITY_TYPE_MAP


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
