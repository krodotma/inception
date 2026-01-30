"""
REAL tests for extract/ocr.py (0% coverage)
Requires cv2 - skipped if not available
"""
import pytest
from pathlib import Path

try:
    from inception.extract.ocr import TextBox, OCRResult, OCREngine
    HAS_OCR = True
except ImportError:
    HAS_OCR = False


@pytest.mark.skipif(not HAS_OCR, reason="cv2 not available")
class TestTextBox:
    def test_creation(self):
        box = TextBox(
            text="Hello",
            confidence=0.95,
            x0=10.0, y0=20.0, x1=100.0, y1=40.0
        )
        assert box.text == "Hello"
        assert box.confidence == 0.95


@pytest.mark.skipif(not HAS_OCR, reason="cv2 not available")
class TestOCRResult:
    def test_creation(self):
        result = OCRResult(image_path=Path("/tmp/test.png"))
        assert result.text_boxes == []


@pytest.mark.skipif(not HAS_OCR, reason="cv2 not available")
class TestOCREngine:
    def test_creation(self):
        engine = OCREngine()
        assert engine is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
