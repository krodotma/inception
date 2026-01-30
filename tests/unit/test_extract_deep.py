"""Tests for extract/* modules"""
import pytest

try:
    from inception.extract.alignment import TextAlignment, AlignmentEngine
    HAS_ALIGNMENT = True
except ImportError:
    HAS_ALIGNMENT = False

try:
    from inception.extract.scene_transcript import TranscriptSegment
    HAS_TRANSCRIPT = True
except ImportError:
    HAS_TRANSCRIPT = False


@pytest.mark.skipif(not HAS_ALIGNMENT, reason="TextAlignment not available")
class TestTextAlignment:
    def test_creation(self):
        alignment = TextAlignment()
        assert alignment is not None


@pytest.mark.skipif(not HAS_TRANSCRIPT, reason="TranscriptSegment not available")
class TestTranscriptSegment:
    def test_creation(self):
        segment = TranscriptSegment(text="Hello", start_time=0.0, end_time=1.0)
        assert segment.text == "Hello"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
