"""
Unit tests for analyze/resolver.py

Tests for entity resolution:
- ResolutionStrategy, EntityConfidence: Enums
- ResolvedEntity, EntityCandidate: Data classes
- EntityResolver: Main resolver
"""

import pytest

try:
    from inception.analyze.resolver import (
        ResolutionStrategy,
        EntityConfidence,
        ResolvedEntity,
        EntityCandidate,
        EntityResolver,
    )
    HAS_RESOLVER = True
except ImportError:
    HAS_RESOLVER = False


@pytest.mark.skipif(not HAS_RESOLVER, reason="resolver module not available")
class TestResolutionStrategy:
    """Tests for ResolutionStrategy enum."""
    
    def test_values(self):
        """Test strategy values."""
        assert ResolutionStrategy.EXACT.value == "exact"
        assert ResolutionStrategy.FUZZY.value == "fuzzy"
        assert ResolutionStrategy.EMBEDDING.value == "embedding"
        assert ResolutionStrategy.ENSEMBLE.value == "ensemble"


@pytest.mark.skipif(not HAS_RESOLVER, reason="resolver module not available")
class TestEntityConfidence:
    """Tests for EntityConfidence enum."""
    
    def test_values(self):
        """Test confidence values."""
        assert EntityConfidence.HIGH.value == "high"
        assert EntityConfidence.MEDIUM.value == "medium"
        assert EntityConfidence.LOW.value == "low"
        assert EntityConfidence.UNCERTAIN.value == "uncertain"


@pytest.mark.skipif(not HAS_RESOLVER, reason="resolver module not available")
class TestResolvedEntity:
    """Tests for ResolvedEntity dataclass."""
    
    def test_creation_minimal(self):
        """Test creating minimal entity."""
        entity = ResolvedEntity(
            text="Albert Einstein",
            entity_type="PERSON",
        )
        
        assert entity.text == "Albert Einstein"
        assert entity.entity_type == "PERSON"
    
    def test_creation_full(self):
        """Test creating full entity."""
        entity = ResolvedEntity(
            text="Einstein",
            entity_type="PERSON",
            canonical_name="Albert Einstein",
            canonical_id="Q937",
            wikidata_qid="Q937",
            confidence=0.95,
            confidence_level=EntityConfidence.HIGH,
        )
        
        assert entity.canonical_name == "Albert Einstein"
        assert entity.wikidata_qid == "Q937"
    
    def test_to_dict(self):
        """Test conversion to dict."""
        entity = ResolvedEntity(
            text="Test",
            entity_type="ORG",
        )
        
        d = entity.to_dict()
        
        assert isinstance(d, dict)
        assert "text" in d
        assert "type" in d  # API uses 'type' not 'entity_type'


@pytest.mark.skipif(not HAS_RESOLVER, reason="resolver module not available")
class TestEntityCandidate:
    """Tests for EntityCandidate dataclass."""
    
    def test_creation(self):
        """Test creating candidate."""
        candidate = EntityCandidate(
            name="Google",
            entity_id="Q95",
            entity_type="ORG",
            description="Technology company",
        )
        
        assert candidate.name == "Google"
        assert candidate.entity_id == "Q95"
    
    def test_with_aliases(self):
        """Test candidate with aliases."""
        candidate = EntityCandidate(
            name="Google",
            entity_id="Q95",
            entity_type="ORG",
            aliases=["Alphabet", "Google LLC"],
        )
        
        assert "Alphabet" in candidate.aliases


@pytest.mark.skipif(not HAS_RESOLVER, reason="resolver module not available")
class TestEntityResolver:
    """Tests for EntityResolver."""
    
    def test_creation_defaults(self):
        """Test creating with defaults."""
        resolver = EntityResolver()
        
        assert resolver is not None
        assert resolver.strategy == ResolutionStrategy.ENSEMBLE
    
    def test_creation_with_strategy(self):
        """Test creating with custom strategy."""
        resolver = EntityResolver(strategy=ResolutionStrategy.EXACT)
        
        assert resolver.strategy == ResolutionStrategy.EXACT
    
    def test_creation_with_thresholds(self):
        """Test creating with custom thresholds."""
        resolver = EntityResolver(
            embedding_threshold=0.8,
            fuzzy_threshold=0.9,
        )
        
        assert resolver.embedding_threshold == 0.8
        assert resolver.fuzzy_threshold == 0.9
    
    def test_resolve(self):
        """Test resolving an entity."""
        resolver = EntityResolver()
        
        resolved = resolver.resolve(
            text="Einstein",
            entity_type="PERSON",
        )
        
        assert isinstance(resolved, ResolvedEntity)
        assert resolved.text == "Einstein"
    
    def test_resolve_with_context(self):
        """Test resolving with context."""
        resolver = EntityResolver()
        
        resolved = resolver.resolve(
            text="Einstein",
            entity_type="PERSON",
            context="The famous physicist Albert Einstein",
        )
        
        assert resolved is not None
    
    def test_resolve_batch(self):
        """Test batch resolution."""
        resolver = EntityResolver()
        
        entities = [
            ("Einstein", "PERSON", ""),
            ("MIT", "ORG", ""),
        ]
        
        results = resolver.resolve_batch(entities)
        
        assert len(results) == 2
    
    def test_register_entity(self):
        """Test registering an entity."""
        resolver = EntityResolver()
        
        candidate = EntityCandidate(
            name="Custom Entity",
            entity_id="custom-001",
            entity_type="CUSTOM",
        )
        
        resolver.register_entity(candidate)
        
        # Should not raise
        assert True
    
    def test_stats(self):
        """Test getting stats."""
        resolver = EntityResolver()
        
        # Do some resolves
        resolver.resolve("Test", "PERSON")
        
        stats = resolver.stats()
        
        assert isinstance(stats, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
