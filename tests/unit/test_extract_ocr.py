"""
Unit tests for extract/ocr.py

Tests for OCR:
- TextBox: Data class
- OCRResult: Result class
- OCREngine: Main engine
"""

import pytest
from pathlib import Path

try:
    from inception.extract.ocr import (
        TextBox,
        OCRResult,
        OCREngine,
        merge_duplicate_boxes,
    )
    HAS_OCR = True
except ImportError:
    HAS_OCR = False


@pytest.mark.skipif(not HAS_OCR, reason="ocr module not available")
class TestTextBox:
    """Tests for TextBox dataclass."""
    
    def test_creation(self):
        """Test creating text box."""
        box = TextBox(
            text="Hello World",
            confidence=0.95,
            x0=0.1,
            y0=0.1,
            x1=0.5,
            y1=0.2,
        )
        
        assert box.text == "Hello World"
        assert box.confidence == 0.95
    
    def test_width(self):
        """Test width calculation."""
        box = TextBox(
            text="Test",
            confidence=0.9,
            x0=0.1,
            y0=0.1,
            x1=0.5,
            y1=0.2,
        )
        
        assert box.width() == pytest.approx(0.4)
    
    def test_height(self):
        """Test height calculation."""
        box = TextBox(
            text="Test",
            confidence=0.9,
            x0=0.1,
            y0=0.1,
            x1=0.5,
            y1=0.3,
        )
        
        assert box.height() == pytest.approx(0.2)
    
    def test_center(self):
        """Test center calculation."""
        box = TextBox(
            text="Test",
            confidence=0.9,
            x0=0.0,
            y0=0.0,
            x1=1.0,
            y1=1.0,
        )
        
        cx, cy = box.center()
        
        assert cx == pytest.approx(0.5)
        assert cy == pytest.approx(0.5)


@pytest.mark.skipif(not HAS_OCR, reason="ocr module not available")
class TestOCRResult:
    """Tests for OCRResult dataclass."""
    
    def test_creation(self):
        """Test creating result."""
        result = OCRResult(image_path=Path("/test/image.png"))
        
        assert result.image_path == Path("/test/image.png")
        assert len(result.text_boxes) == 0
    
    def test_with_boxes(self):
        """Test result with text boxes."""
        boxes = [
            TextBox(text="Hello", confidence=0.9, x0=0, y0=0, x1=0.5, y1=0.1),
            TextBox(text="World", confidence=0.8, x0=0.5, y0=0, x1=1.0, y1=0.1),
        ]
        result = OCRResult(
            image_path=Path("/test.png"),
            text_boxes=boxes,
        )
        
        assert len(result.text_boxes) == 2
    
    def test_full_text(self):
        """Test full text extraction."""
        boxes = [
            TextBox(text="Hello", confidence=0.9, x0=0, y0=0, x1=0.5, y1=0.1),
            TextBox(text="World", confidence=0.8, x0=0.5, y0=0, x1=1.0, y1=0.1),
        ]
        result = OCRResult(
            image_path=Path("/test.png"),
            text_boxes=boxes,
        )
        
        full = result.full_text()
        
        assert "Hello" in full
        assert "World" in full
    
    def test_avg_confidence_empty(self):
        """Test avg confidence with no boxes."""
        result = OCRResult(image_path=Path("/test.png"))
        
        avg = result.avg_confidence()
        
        assert avg == 0.0
    
    def test_avg_confidence(self):
        """Test avg confidence calculation."""
        boxes = [
            TextBox(text="A", confidence=0.8, x0=0, y0=0, x1=1, y1=1),
            TextBox(text="B", confidence=1.0, x0=0, y0=0, x1=1, y1=1),
        ]
        result = OCRResult(image_path=Path("/test.png"), text_boxes=boxes)
        
        avg = result.avg_confidence()
        
        assert avg == pytest.approx(0.9)


@pytest.mark.skipif(not HAS_OCR, reason="ocr module not available")
class TestOCREngine:
    """Tests for OCREngine."""
    
    def test_creation_defaults(self):
        """Test creating with defaults."""
        engine = OCREngine()
        
        assert engine is not None
    
    def test_creation_with_engine(self):
        """Test creating with specific engine."""
        engine = OCREngine(engine="tesseract")
        
        assert engine.engine == "tesseract"
    
    def test_creation_with_languages(self):
        """Test creating with languages."""
        engine = OCREngine(languages=["en", "es"])
        
        assert "en" in engine.languages


@pytest.mark.skipif(not HAS_OCR, reason="ocr module not available")
class TestMergeDuplicateBoxes:
    """Tests for merge_duplicate_boxes function."""
    
    def test_empty_list(self):
        """Test merging empty list."""
        result = merge_duplicate_boxes([])
        
        assert result == []
    
    def test_single_box(self):
        """Test merging single box."""
        box = TextBox(text="Test", confidence=0.9, x0=0, y0=0, x1=1, y1=1)
        
        result = merge_duplicate_boxes([box])
        
        assert len(result) == 1
    
    def test_non_overlapping(self):
        """Test non-overlapping boxes aren't merged."""
        box1 = TextBox(text="A", confidence=0.9, x0=0, y0=0, x1=0.4, y1=0.4)
        box2 = TextBox(text="B", confidence=0.9, x0=0.6, y0=0.6, x1=1.0, y1=1.0)
        
        result = merge_duplicate_boxes([box1, box2])
        
        assert len(result) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
