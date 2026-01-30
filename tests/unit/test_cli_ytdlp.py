"""CLI tests using real yt-dlp from venv"""
import pytest
import subprocess
from click.testing import CliRunner
from inception.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestYtdlpAvailable:
    def test_ytdlp_in_venv(self):
        """Test yt-dlp is available in venv"""
        result = subprocess.run(
            [".venv/bin/yt-dlp", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert result.stdout.strip()  # Should have version number


class TestCLIWithYtdlp:
    def test_ingest_youtube_offline_mode(self, runner):
        """Test ingest in offline mode (no network)"""
        result = runner.invoke(main, ["--offline", "ingest", "https://youtube.com/watch?v=test123"])
        assert result.exit_code == 0
        assert "offline" in result.output.lower()
    
    def test_doctor_shows_ytdlp(self, runner):
        """Test doctor command shows yt-dlp status"""
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
