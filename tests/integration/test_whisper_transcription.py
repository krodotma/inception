"""
Integration tests for Whisper audio transcription.
These tests verify the whisper pipeline with the installed model.
"""
import pytest
import tempfile
import wave
import struct
from pathlib import Path

try:
    import whisper
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False


@pytest.fixture
def sample_audio_file():
    """Create a sample audio file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        # Create a simple sine wave audio file
        sample_rate = 16000
        duration = 1  # 1 second
        frequency = 440  # A4 note
        
        with wave.open(f.name, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            
            for i in range(sample_rate * duration):
                import math
                value = int(32767 * 0.5 * math.sin(2 * math.pi * frequency * i / sample_rate))
                wav.writeframes(struct.pack('<h', value))
        
        yield Path(f.name)


@pytest.mark.skipif(not HAS_WHISPER, reason="whisper not installed")
class TestWhisperIntegration:
    """Test whisper model loading and transcription."""
    
    def test_whisper_import(self):
        """Verify whisper can be imported."""
        import whisper
        assert whisper is not None
    
    def test_whisper_load_tiny(self):
        """Test loading the tiny model (fastest)."""
        model = whisper.load_model("tiny")
        assert model is not None
    
    def test_whisper_transcribe_empty(self, sample_audio_file):
        """Test transcribing a sample audio file."""
        model = whisper.load_model("tiny")
        result = model.transcribe(str(sample_audio_file))
        assert result is not None
        assert "text" in result
    
    def test_whisper_detect_language(self, sample_audio_file):
        """Test language detection."""
        model = whisper.load_model("tiny")
        audio = whisper.load_audio(str(sample_audio_file))
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(model.device)
        _, probs = model.detect_language(mel)
        assert probs is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
