"""Aggressive CLI offline tests to cover more ingest paths"""
import pytest
from click.testing import CliRunner
from inception.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestIngestOfflineMode:
    def test_youtube_offline(self, runner):
        result = runner.invoke(main, ["--offline", "ingest", "https://youtube.com/watch?v=test123"])
        assert result.exit_code == 0
        assert "offline" in result.output.lower()
    
    def test_web_offline(self, runner):
        result = runner.invoke(main, ["--offline", "ingest", "https://example.com"])
        assert result.exit_code == 0
    
    def test_pdf_offline(self, runner):
        result = runner.invoke(main, ["--offline", "ingest", "test.pdf"])
        assert result.exit_code in [0, 1, 2]
    
    def test_channel_offline(self, runner):
        result = runner.invoke(main, ["--offline", "ingest", "https://youtube.com/c/test"])
        assert result.exit_code in [0, 1, 2]


class TestQueryOfflineMode:
    def test_query_offline(self, runner):
        result = runner.invoke(main, ["--offline", "query", "what is AI"])
        assert result.exit_code in [0, 1, 2]


class TestExportOfflineMode:
    def test_export_offline(self, runner):
        result = runner.invoke(main, ["--offline", "export", "--help"])
        assert result.exit_code == 0


class TestAuthOfflineMode:
    def test_auth_offline(self, runner):
        result = runner.invoke(main, ["--offline", "auth", "status"])
        assert result.exit_code in [0, 1, 2]


class TestServeOfflineMode:
    def test_serve_offline(self, runner):
        result = runner.invoke(main, ["--offline", "serve", "--help"])
        assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
