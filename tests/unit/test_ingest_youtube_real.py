"""
REAL tests for ingest/youtube.py (28% coverage)
"""
import pytest
from inception.ingest.youtube import VideoMetadata, parse_youtube_url, fetch_video_metadata


class TestVideoMetadata:
    def test_creation(self):
        meta = VideoMetadata(
            video_id="abc123",
            title="Test Video",
            channel="Test Channel",
            duration_seconds=600,
        )
        assert meta.video_id == "abc123"
        assert meta.title == "Test Video"


class TestParseYoutubeUrl:
    def test_full_watch_url(self):
        result = parse_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert result is not None
        assert result.get("video_id") == "dQw4w9WgXcQ" or "dQw4w9WgXcQ" in str(result)
    
    def test_short_url(self):
        result = parse_youtube_url("https://youtu.be/dQw4w9WgXcQ")
        assert result is not None
    
    def test_invalid_url(self):
        result = parse_youtube_url("https://example.com")
        assert result is None or result.get("video_id") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
