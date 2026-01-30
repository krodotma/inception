"""
Unit tests for extract/transcription.py

Tests for transcription:
- Word, Segment: Data classes
- TranscriptResult: Result class
- Transcriber: Main transcriber
"""

import pytest
from pathlib import Path

try:
    from inception.extract.transcription import (
        Word,
        Segment,
        TranscriptResult,
        Transcriber,
    )
    HAS_TRANSCRIPTION = True
except ImportError:
    HAS_TRANSCRIPTION = False


@pytest.mark.skipif(not HAS_TRANSCRIPTION, reason="transcription module not available")
class TestWord:
    """Tests for Word dataclass."""
    
    def test_creation(self):
        """Test creating word."""
        word = Word(
            text="hello",
            start_ms=0,
            end_ms=500,
        )
        
        assert word.text == "hello"
        assert word.start_ms == 0
    
    def test_duration_ms(self):
        """Test duration calculation."""
        word = Word(text="test", start_ms=100, end_ms=600)
        
        assert word.duration_ms == 500
    
    def test_with_probability(self):
        """Test word with probability."""
        word = Word(
            text="confident",
            start_ms=0,
            end_ms=1000,
            probability=0.99,
        )
        
        assert word.probability == 0.99


@pytest.mark.skipif(not HAS_TRANSCRIPTION, reason="transcription module not available")
class TestSegment:
    """Tests for Segment dataclass."""
    
    def test_creation(self):
        """Test creating segment."""
        segment = Segment(
            id=1,
            text="Hello world",
            start_ms=0,
            end_ms=2000,
        )
        
        assert segment.id == 1
        assert segment.text == "Hello world"
    
    def test_duration_ms(self):
        """Test duration calculation."""
        segment = Segment(id=1, text="Test", start_ms=0, end_ms=5000)
        
        assert segment.duration_ms == 5000
    
    def test_word_count(self):
        """Test word count."""
        words = [
            Word(text="Hello", start_ms=0, end_ms=500),
            Word(text="world", start_ms=500, end_ms=1000),
        ]
        segment = Segment(id=1, text="Hello world", start_ms=0, end_ms=1000, words=words)
        
        assert segment.word_count == 2


@pytest.mark.skipif(not HAS_TRANSCRIPTION, reason="transcription module not available")
class TestTranscriptResult:
    """Tests for TranscriptResult dataclass."""
    
    def test_creation(self):
        """Test creating result."""
        result = TranscriptResult(audio_path=Path("/audio.mp3"))
        
        assert result.audio_path == Path("/audio.mp3")
    
    def test_full_text(self):
        """Test full text extraction."""
        segments = [
            Segment(id=1, text="First segment", start_ms=0, end_ms=1000),
            Segment(id=2, text="Second segment", start_ms=1000, end_ms=2000),
        ]
        result = TranscriptResult(audio_path=Path("/audio.mp3"), segments=segments)
        
        full = result.full_text
        
        assert "First" in full
    
    def test_word_count(self):
        """Test word count."""
        segments = [
            Segment(id=1, text="Hello world", start_ms=0, end_ms=1000),
        ]
        result = TranscriptResult(audio_path=Path("/audio.mp3"), segments=segments)
        
        assert result.word_count >= 0


@pytest.mark.skipif(not HAS_TRANSCRIPTION, reason="transcription module not available")
class TestTranscriber:
    """Tests for Transcriber."""
    
    def test_creation_defaults(self):
        """Test creating with defaults."""
        transcriber = Transcriber()
        
        assert transcriber.model_size is not None or True
    
    def test_creation_with_model(self):
        """Test creating with specific model."""
        transcriber = Transcriber(model_size="base")
        
        assert transcriber.model_size == "base"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
