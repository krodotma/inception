"""
Unit tests for pipeline/unified.py

Tests for unified extraction pipeline:
- ExtractionMode, ContentType: Enums
- ExtractionConfig: Configuration
- ExtractedEntity, ExtractedRelationship, ExtractedFact: Results
- ExtractionResult: Full result
- Source extractors
"""

import pytest
from pathlib import Path
from datetime import datetime

try:
    from inception.pipeline.unified import (
        ExtractionMode,
        ContentType,
        ExtractionConfig,
        ExtractedEntity,
        ExtractedRelationship,
        ExtractedFact,
        ExtractionResult,
        SourceExtractor,
        VideoExtractor,
        ImageExtractor,
        DocumentExtractor,
    )
    HAS_PIPELINE = True
except ImportError:
    HAS_PIPELINE = False


@pytest.mark.skipif(not HAS_PIPELINE, reason="pipeline module not available")
class TestExtractionMode:
    """Tests for ExtractionMode enum."""
    
    def test_values(self):
        """Test mode values."""
        assert ExtractionMode.FULL.value == "full"
        assert ExtractionMode.INCREMENTAL.value == "incremental"
        assert ExtractionMode.TARGETED.value == "targeted"
        assert ExtractionMode.STREAMING.value == "streaming"


@pytest.mark.skipif(not HAS_PIPELINE, reason="pipeline module not available")
class TestContentType:
    """Tests for ContentType enum."""
    
    def test_values(self):
        """Test content type values."""
        assert ContentType.VIDEO.value == "video"
        assert ContentType.IMAGE.value == "image"
        assert ContentType.DOCUMENT.value == "document"
        assert ContentType.TEXT.value == "text"


@pytest.mark.skipif(not HAS_PIPELINE, reason="pipeline module not available")
class TestExtractionConfig:
    """Tests for ExtractionConfig dataclass."""
    
    def test_creation_defaults(self):
        """Test creating with defaults."""
        config = ExtractionConfig()
        
        assert config.mode == ExtractionMode.FULL
        assert config.ocr_engine == "paddleocr"
    
    def test_creation_custom(self):
        """Test creating with custom values."""
        config = ExtractionConfig(
            mode=ExtractionMode.INCREMENTAL,
            ocr_engine="tesseract",
            parallel_workers=8,
        )
        
        assert config.mode == ExtractionMode.INCREMENTAL
        assert config.parallel_workers == 8


@pytest.mark.skipif(not HAS_PIPELINE, reason="pipeline module not available")
class TestExtractedEntity:
    """Tests for ExtractedEntity dataclass."""
    
    def test_creation(self):
        """Test creating entity."""
        entity = ExtractedEntity(
            id="ent-001",
            text="Albert Einstein",
            entity_type="PERSON",
            confidence=0.95,
        )
        
        assert entity.id == "ent-001"
        assert entity.entity_type == "PERSON"
    
    def test_with_uncertainty(self):
        """Test entity with uncertainty."""
        entity = ExtractedEntity(
            id="ent-002",
            text="Uncertain Entity",
            entity_type="ORG",
            confidence=0.7,
            epistemic_uncertainty=0.2,
            aleatoric_uncertainty=0.1,
        )
        
        assert entity.epistemic_uncertainty == 0.2


@pytest.mark.skipif(not HAS_PIPELINE, reason="pipeline module not available")
class TestExtractedRelationship:
    """Tests for ExtractedRelationship dataclass."""
    
    def test_creation(self):
        """Test creating relationship."""
        rel = ExtractedRelationship(
            id="rel-001",
            source_entity_id="ent-001",
            target_entity_id="ent-002",
            relation_type="works_at",
            confidence=0.9,
        )
        
        assert rel.relation_type == "works_at"
    
    def test_with_evidence(self):
        """Test relationship with evidence."""
        rel = ExtractedRelationship(
            id="rel-002",
            source_entity_id="ent-001",
            target_entity_id="ent-002",
            relation_type="knows",
            confidence=0.85,
            evidence_text="They worked together",
        )
        
        assert rel.evidence_text is not None


@pytest.mark.skipif(not HAS_PIPELINE, reason="pipeline module not available")
class TestExtractedFact:
    """Tests for ExtractedFact dataclass."""
    
    def test_creation(self):
        """Test creating fact."""
        fact = ExtractedFact(
            id="fact-001",
            subject="Einstein",
            predicate="was born in",
            object="Germany",
            confidence=0.99,
        )
        
        assert fact.subject == "Einstein"
        assert fact.predicate == "was born in"
    
    def test_with_temporal(self):
        """Test fact with temporal bounds."""
        fact = ExtractedFact(
            id="fact-002",
            subject="Company",
            predicate="has CEO",
            object="Person",
            confidence=0.8,
            valid_from=datetime(2020, 1, 1),
            valid_until=datetime(2023, 12, 31),
        )
        
        assert fact.valid_from is not None
    
    def test_uncertain_fact(self):
        """Test uncertain fact."""
        fact = ExtractedFact(
            id="fact-003",
            subject="X",
            predicate="might be",
            object="Y",
            confidence=0.5,
            is_uncertain=True,
            uncertainty_reason="Hedged language",
        )
        
        assert fact.is_uncertain is True


@pytest.mark.skipif(not HAS_PIPELINE, reason="pipeline module not available")
class TestExtractionResult:
    """Tests for ExtractionResult dataclass."""
    
    def test_creation_minimal(self):
        """Test creating minimal result."""
        result = ExtractionResult(
            content_id="content-001",
            content_type=ContentType.DOCUMENT,
            source_path=Path("/test/doc.pdf"),
        )
        
        assert result.content_id == "content-001"
        assert len(result.entities) == 0
    
    def test_creation_full(self):
        """Test creating full result."""
        entities = [
            ExtractedEntity(id="e1", text="A", entity_type="X", confidence=0.9),
        ]
        result = ExtractionResult(
            content_id="content-002",
            content_type=ContentType.TEXT,
            source_path=Path("/test/text.txt"),
            raw_text="Full document text here",
            entities=entities,
            overall_confidence=0.85,
        )
        
        assert len(result.entities) == 1
        assert result.overall_confidence == 0.85


@pytest.mark.skipif(not HAS_PIPELINE, reason="pipeline module not available")
class TestVideoExtractor:
    """Tests for VideoExtractor."""
    
    def test_can_handle_mp4(self):
        """Test can handle MP4."""
        extractor = VideoExtractor()
        
        assert extractor.can_handle(Path("/video.mp4")) is True
    
    def test_cannot_handle_pdf(self):
        """Test cannot handle PDF."""
        extractor = VideoExtractor()
        
        assert extractor.can_handle(Path("/doc.pdf")) is False


@pytest.mark.skipif(not HAS_PIPELINE, reason="pipeline module not available")
class TestImageExtractor:
    """Tests for ImageExtractor."""
    
    def test_can_handle_png(self):
        """Test can handle PNG."""
        extractor = ImageExtractor()
        
        assert extractor.can_handle(Path("/image.png")) is True
    
    def test_can_handle_jpg(self):
        """Test can handle JPG."""
        extractor = ImageExtractor()
        
        assert extractor.can_handle(Path("/photo.jpg")) is True


@pytest.mark.skipif(not HAS_PIPELINE, reason="pipeline module not available")
class TestDocumentExtractor:
    """Tests for DocumentExtractor."""
    
    def test_can_handle_pdf(self):
        """Test can handle PDF."""
        extractor = DocumentExtractor()
        
        assert extractor.can_handle(Path("/doc.pdf")) is True
    
    def test_can_handle_docx(self):
        """Test can handle DOCX."""
        extractor = DocumentExtractor()
        
        assert extractor.can_handle(Path("/doc.docx")) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
