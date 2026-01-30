"""Tests for extract/ocr.py (30%) - needs OpenCV"""
import pytest

try:
    import cv2
    from inception.extract.ocr import OCREngine, TextBox, OCRResult
    HAS_OCR = True
except ImportError:
    HAS_OCR = False


@pytest.mark.skipif(not HAS_OCR, reason="OCR not available")
class TestOCREngine:
    def test_creation(self):
        engine = OCREngine()
        assert engine is not None
    
    def test_has_config(self):
        engine = OCREngine()
        if hasattr(engine, 'config'):
            assert engine.config is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
