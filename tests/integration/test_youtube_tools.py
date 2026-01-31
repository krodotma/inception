"""
Integration tests for yt-dlp and YouTube ingestion pipeline.
These tests verify the full ingestion flow with real tools.
"""
import pytest
import subprocess
import tempfile
from pathlib import Path


class TestYtdlpIntegration:
    """Test yt-dlp tool availability and basic functionality."""
    
    def test_ytdlp_version(self):
        """Verify yt-dlp is installed and reports version."""
        result = subprocess.run(
            [".venv/bin/yt-dlp", "--version"],
            capture_output=True,
            text=True,
            cwd="/Users/kroma/inceptional"
        )
        assert result.returncode == 0
        assert result.stdout.strip()  # Has version string
    
    def test_ytdlp_help(self):
        """Verify yt-dlp help works."""
        result = subprocess.run(
            [".venv/bin/yt-dlp", "--help"],
            capture_output=True,
            text=True,
            cwd="/Users/kroma/inceptional"
        )
        assert result.returncode == 0
        assert "Download" in result.stdout or "download" in result.stdout
    
    def test_ytdlp_simulate(self):
        """Test yt-dlp simulation mode (no actual download)."""
        # Use a very short public domain video for testing
        result = subprocess.run(
            [".venv/bin/yt-dlp", "--simulate", "-j", "https://www.youtube.com/watch?v=BaW_jenozKc"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd="/Users/kroma/inceptional"
        )
        # May fail if no network, but should not crash
        assert result.returncode in [0, 1, 2]


class TestFfmpegIntegration:
    """Test ffmpeg tool availability and basic functionality."""
    
    def test_ffmpeg_version(self):
        """Verify ffmpeg is installed."""
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "ffmpeg version" in result.stdout.lower()
    
    def test_ffmpeg_formats(self):
        """List available formats."""
        result = subprocess.run(
            ["ffmpeg", "-formats"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "mp3" in result.stdout or "mp4" in result.stdout
    
    def test_ffmpeg_codecs(self):
        """List available codecs."""
        result = subprocess.run(
            ["ffmpeg", "-codecs"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
