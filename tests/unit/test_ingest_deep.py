"""Tests for ingest/* modules"""
import pytest
from pathlib import Path

try:
    from inception.ingest.youtube import parse_youtube_url, VideoMetadata
    HAS_YOUTUBE = True
except ImportError:
    HAS_YOUTUBE = False

try:
    from inception.ingest.web_intelligence import WebAnalyzer
    HAS_WEB = True
except ImportError:
    HAS_WEB = False


@pytest.mark.skipif(not HAS_YOUTUBE, reason="youtube not available")
class TestYoutubeIngest:
    def test_parse_standard_url(self):
        result = parse_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert result is not None
    
    def test_parse_short_url(self):
        result = parse_youtube_url("https://youtu.be/dQw4w9WgXcQ")
        assert result is not None
    
    def test_video_metadata(self):
        meta = VideoMetadata(
            video_id="test123",
            title="Test Video",
            channel="Test Channel",
            duration_seconds=120,
        )
        assert meta.title == "Test Video"


@pytest.mark.skipif(not HAS_WEB, reason="web_intelligence not available")
class TestWebIngest:
    def test_web_analyzer_creation(self):
        analyzer = WebAnalyzer()
        assert analyzer is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
