"""Tests for extract/scenes.py (37%) and extract/transcription.py (44%)"""
import pytest

try:
    import cv2
    from inception.extract.scenes import SceneDetector, Scene
    HAS_SCENES = True
except ImportError:
    HAS_SCENES = False

try:
    from inception.extract.transcription import TranscriptionEngine, Segment
    HAS_TRANSCRIPTION = True
except ImportError:
    HAS_TRANSCRIPTION = False


@pytest.mark.skipif(not HAS_SCENES, reason="SceneDetector not available")
class TestSceneDetector:
    def test_creation(self):
        detector = SceneDetector()
        assert detector is not None


@pytest.mark.skipif(not HAS_SCENES, reason="Scene not available")
class TestScene:
    def test_creation(self):
        scene = Scene(start_time=0.0, end_time=10.0)
        assert scene.start_time == 0.0
        assert scene.end_time == 10.0


@pytest.mark.skipif(not HAS_TRANSCRIPTION, reason="TranscriptionEngine not available")
class TestTranscriptionEngine:
    def test_creation(self):
        engine = TranscriptionEngine()
        assert engine is not None


@pytest.mark.skipif(not HAS_TRANSCRIPTION, reason="Segment not available")
class TestSegment:
    def test_creation(self):
        seg = Segment(start=0.0, end=5.0, text="Hello world")
        assert seg.text == "Hello world"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
