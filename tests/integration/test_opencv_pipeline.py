"""
Integration tests for OpenCV image/video processing.
Tests OCR and scene detection with real OpenCV.
"""
import pytest
import tempfile
import numpy as np
from pathlib import Path

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from inception.extract.ocr import OCREngine
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

try:
    from inception.extract.scenes import SceneDetector
    HAS_SCENES = True
except ImportError:
    HAS_SCENES = False


@pytest.fixture
def sample_image():
    """Create a sample image for testing."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        # Create a simple test image with text
        img = np.zeros((100, 300, 3), dtype=np.uint8)
        img.fill(255)  # White background
        cv2.putText(img, "Hello World", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.imwrite(f.name, img)
        yield Path(f.name)


@pytest.mark.skipif(not HAS_CV2, reason="OpenCV not available")
class TestOpenCVIntegration:
    """Test OpenCV basic functionality."""
    
    def test_opencv_version(self):
        """Verify OpenCV version."""
        assert cv2.__version__ is not None
    
    def test_opencv_imread(self, sample_image):
        """Test image reading."""
        img = cv2.imread(str(sample_image))
        assert img is not None
        assert img.shape[0] > 0
    
    def test_opencv_color_conversion(self, sample_image):
        """Test color conversion."""
        img = cv2.imread(str(sample_image))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        assert gray is not None
        assert len(gray.shape) == 2
    
    def test_opencv_resize(self, sample_image):
        """Test image resizing."""
        img = cv2.imread(str(sample_image))
        resized = cv2.resize(img, (150, 50))
        assert resized.shape[:2] == (50, 150)


@pytest.mark.skipif(not HAS_OCR or not HAS_CV2, reason="OCR or OpenCV not available")
class TestOCRIntegration:
    """Test OCR engine with real OpenCV."""
    
    def test_ocr_engine_creation(self):
        """Create OCR engine."""
        engine = OCREngine()
        assert engine is not None


@pytest.mark.skipif(not HAS_SCENES or not HAS_CV2, reason="SceneDetector or OpenCV not available")
class TestSceneDetectionIntegration:
    """Test scene detection with real OpenCV."""
    
    def test_scene_detector_creation(self):
        """Create scene detector."""
        detector = SceneDetector()
        assert detector is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
