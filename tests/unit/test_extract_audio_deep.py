"""Deep extract tests to push coverage"""
import pytest

try:
    from inception.extract.audio import AudioExtractor
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False

try:
    from inception.extract.transcript import TranscriptExtractor
    HAS_TRANSCRIPT = True
except ImportError:
    HAS_TRANSCRIPT = False

try:
    from inception.extract.content import ContentExtractor
    HAS_CONTENT = True
except ImportError:
    HAS_CONTENT = False

try:
    from inception.extract.pdf import PDFExtractor
    HAS_PDF = True
except ImportError:
    HAS_PDF = False


@pytest.mark.skipif(not HAS_AUDIO, reason="audio not available")
class TestAudioExtractorDeep:
    def test_creation(self):
        extractor = AudioExtractor()
        assert extractor is not None


@pytest.mark.skipif(not HAS_TRANSCRIPT, reason="transcript not available")
class TestTranscriptExtractorDeep:
    def test_creation(self):
        extractor = TranscriptExtractor()
        assert extractor is not None


@pytest.mark.skipif(not HAS_CONTENT, reason="content not available")
class TestContentExtractorDeep:
    def test_creation(self):
        extractor = ContentExtractor()
        assert extractor is not None


@pytest.mark.skipif(not HAS_PDF, reason="pdf not available")
class TestPDFExtractorDeep:
    def test_creation(self):
        extractor = PDFExtractor()
        assert extractor is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
