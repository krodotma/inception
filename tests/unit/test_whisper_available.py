"""Tests for audio transcription with whisper"""
import pytest

try:
    import whisper
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False

try:
    from inception.extract.audio import AudioExtractor, TranscriptionResult
    HAS_AUDIO = True
except ImportError:
    try:
        from inception.extract.audio import AudioExtractor
        HAS_AUDIO = True
        TranscriptionResult = None
    except ImportError:
        HAS_AUDIO = False
        TranscriptionResult = None


@pytest.mark.skipif(not HAS_WHISPER, reason="whisper not installed")
class TestWhisperAvailable:
    def test_whisper_loads(self):
        """Verify whisper is available"""
        model = whisper.load_model("tiny")
        assert model is not None


@pytest.mark.skipif(not HAS_AUDIO, reason="AudioExtractor not available")
class TestAudioExtractor:
    def test_creation(self):
        extractor = AudioExtractor()
        assert extractor is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
