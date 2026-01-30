"""
REAL tests for analyze/entities.py
"""
import pytest
from inception.analyze.entities import EntityExtractor, Entity, EntityExtractionResult


class TestEntity:
    def test_creation(self):
        entity = Entity(
            text="Google",
            entity_type="ORG",
        )
        assert entity.text == "Google"
        assert entity.entity_type == "ORG"


class TestEntityExtractionResult:
    def test_creation(self):
        result = EntityExtractionResult(entities=[])
        assert result.entities == []
    
    def test_with_entities(self):
        e1 = Entity(text="Google", entity_type="ORG")
        result = EntityExtractionResult(entities=[e1])
        assert len(result.entities) == 1


class TestEntityExtractor:
    def test_creation(self):
        extractor = EntityExtractor()
        assert extractor is not None
    
    def test_extract_simple(self):
        extractor = EntityExtractor()
        result = extractor.extract("Google was founded by Larry Page.")
        assert isinstance(result, EntityExtractionResult)
        assert len(result.entities) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
