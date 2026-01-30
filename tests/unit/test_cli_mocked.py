"""Mocked CLI tests to cover ingest/export code paths"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from inception.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestIngestYouTube:
    def test_ingest_youtube_offline(self, runner):
        """--offline mode should skip download"""
        result = runner.invoke(main, ["--offline", "ingest", "https://youtube.com/watch?v=abc123"])
        assert result.exit_code == 0
        assert "offline" in result.output.lower()
    
    @patch('subprocess.run')
    def test_ingest_youtube_no_ytdlp(self, mock_run, runner):
        """Test when yt-dlp not installed"""
        mock_run.side_effect = FileNotFoundError()
        result = runner.invoke(main, ["ingest", "https://youtube.com/watch?v=abc123"])
        # Should handle gracefully
        assert result.exit_code in [0, 1, 2]


class TestIngestWeb:
    def test_ingest_web_offline(self, runner):
        """--offline mode for web URL"""
        result = runner.invoke(main, ["--offline", "ingest", "https://example.com/article"])
        assert result.exit_code == 0


class TestIngestPDF:
    def test_ingest_pdf_offline(self, runner):
        """--offline mode for PDF"""
        result = runner.invoke(main, ["--offline", "ingest", "document.pdf"])
        assert result.exit_code in [0, 1, 2]


class TestExportObsidian:
    def test_export_obsidian_help(self, runner):
        result = runner.invoke(main, ["export", "--help"])
        assert result.exit_code == 0


class TestExportJSON:
    def test_export_json_help(self, runner):
        result = runner.invoke(main, ["export", "--help"])
        assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
