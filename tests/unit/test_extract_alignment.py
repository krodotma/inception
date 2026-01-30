"""
Unit tests for extract/alignment.py

Tests for multimodal alignment:
- AlignedSpan: Span data class
- AlignmentResult: Result class
- MultimodalAligner: Main aligner
"""

import pytest
from pathlib import Path

try:
    from inception.extract.alignment import (
        AlignedSpan,
        AlignmentResult,
        MultimodalAligner,
        compute_text_similarity,
    )
    HAS_ALIGNMENT = True
except ImportError:
    HAS_ALIGNMENT = False


@pytest.mark.skipif(not HAS_ALIGNMENT, reason="alignment module not available")
class TestAlignedSpan:
    """Tests for AlignedSpan dataclass."""
    
    def test_creation(self):
        """Test creating span."""
        span = AlignedSpan(
            start_ms=0,
            end_ms=5000,
        )
        
        assert span.start_ms == 0
        assert span.end_ms == 5000
    
    def test_duration_ms(self):
        """Test duration calculation."""
        span = AlignedSpan(start_ms=1000, end_ms=6000)
        
        assert span.duration_ms == 5000  # property
    
    def test_has_transcript(self):
        """Test has_transcript method."""
        span_no_text = AlignedSpan(start_ms=0, end_ms=5000)
        span_with_text = AlignedSpan(
            start_ms=0,
            end_ms=5000,
            transcript_text="Hello world",
        )
        
        assert span_no_text.has_transcript is False
        assert span_with_text.has_transcript is True
    
    def test_has_ocr(self):
        """Test has_ocr method."""
        span_no_ocr = AlignedSpan(start_ms=0, end_ms=5000)
        span_with_ocr = AlignedSpan(
            start_ms=0,
            end_ms=5000,
            ocr_text="OCR content",
        )
        
        assert span_no_ocr.has_ocr is False
        assert span_with_ocr.has_ocr is True
    
    def test_combined_text(self):
        """Test combined text extraction."""
        span = AlignedSpan(
            start_ms=0,
            end_ms=5000,
            transcript_text="Spoken text",
            ocr_text="Visual text",
        )
        
        combined = span.combined_text
        
        assert "Spoken text" in combined or "Visual text" in combined


@pytest.mark.skipif(not HAS_ALIGNMENT, reason="alignment module not available")
class TestAlignmentResult:
    """Tests for AlignmentResult dataclass."""
    
    def test_creation(self):
        """Test creating result."""
        result = AlignmentResult()
        
        assert result.span_count == 0  # property
    
    def test_with_spans(self):
        """Test result with spans."""
        spans = [
            AlignedSpan(start_ms=0, end_ms=5000),
            AlignedSpan(start_ms=5000, end_ms=10000),
        ]
        result = AlignmentResult(spans=spans, duration_ms=10000)
        
        assert result.span_count == 2
    
    def test_get_spans_at_time(self):
        """Test getting spans at timestamp."""
        spans = [
            AlignedSpan(start_ms=0, end_ms=5000),
            AlignedSpan(start_ms=5000, end_ms=10000),
        ]
        result = AlignmentResult(spans=spans)
        
        found = result.get_spans_at_time(2500)
        
        assert len(found) >= 1


@pytest.mark.skipif(not HAS_ALIGNMENT, reason="alignment module not available")
class TestMultimodalAligner:
    """Tests for MultimodalAligner."""
    
    def test_creation_defaults(self):
        """Test creating with defaults."""
        aligner = MultimodalAligner()
        
        assert aligner.scene_boundary_weight == 0.8
    
    def test_creation_custom(self):
        """Test creating with custom params."""
        aligner = MultimodalAligner(
            scene_boundary_weight=0.5,
            transcript_pause_threshold_ms=4000,
        )
        
        assert aligner.scene_boundary_weight == 0.5


@pytest.mark.skipif(not HAS_ALIGNMENT, reason="alignment module not available")
class TestComputeTextSimilarity:
    """Tests for compute_text_similarity function."""
    
    def test_identical_text(self):
        """Test similarity of identical text."""
        score = compute_text_similarity("hello world", "hello world")
        
        assert score == 1.0
    
    def test_completely_different(self):
        """Test similarity of completely different text."""
        score = compute_text_similarity("abc", "xyz")
        
        assert score < 0.5
    
    def test_partial_overlap(self):
        """Test similarity of partially overlapping text."""
        score = compute_text_similarity("hello world", "hello there")
        
        assert 0 < score < 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
