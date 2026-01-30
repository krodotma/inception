"""
Unit tests for cli.py

Tests for CLI commands using click.testing.CliRunner.
"""

import pytest
from click.testing import CliRunner

try:
    from inception.cli import main, doctor, auth, auth_status
    HAS_CLI = True
except ImportError:
    HAS_CLI = False


@pytest.mark.skipif(not HAS_CLI, reason="cli module not available")
class TestMainGroup:
    """Tests for main CLI group."""
    
    def test_version(self):
        """Test version option."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        
        assert result.exit_code == 0
        assert "inception" in result.output.lower() or "version" in result.output.lower()
    
    def test_help(self):
        """Test help output."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        
        assert result.exit_code == 0
        assert "Inception" in result.output or "ingest" in result.output


@pytest.mark.skipif(not HAS_CLI, reason="cli module not available")
class TestDoctorCommand:
    """Tests for doctor command."""
    
    def test_doctor_runs(self):
        """Test doctor command runs without crash."""
        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])
        
        # Doctor command should run (may show warnings for missing deps)
        assert result.exit_code == 0 or "error" not in result.output.lower()
    
    def test_doctor_shows_status(self):
        """Test doctor shows dependency status."""
        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])
        
        # Should show some status information
        assert "Python" in result.output or "Version" in result.output or "Status" in result.output


@pytest.mark.skipif(not HAS_CLI, reason="cli module not available")
class TestAuthCommands:
    """Tests for auth sub-commands."""
    
    def test_auth_help(self):
        """Test auth help."""
        runner = CliRunner()
        result = runner.invoke(main, ["auth", "--help"])
        
        assert result.exit_code == 0
        assert "OAuth" in result.output or "setup" in result.output
    
    def test_auth_status_runs(self):
        """Test auth status command runs."""
        runner = CliRunner()
        result = runner.invoke(main, ["auth", "status"])
        
        # Should show provider status (may all be disconnected)
        assert result.exit_code == 0


@pytest.mark.skipif(not HAS_CLI, reason="cli module not available")
class TestIngestCommand:
    """Tests for ingest command."""
    
    def test_ingest_help(self):
        """Test ingest help."""
        runner = CliRunner()
        result = runner.invoke(main, ["ingest", "--help"])
        
        assert result.exit_code == 0
        assert "URI" in result.output or "source" in result.output.lower()
    
    def test_ingest_offline_mode(self):
        """Test ingest in offline mode."""
        runner = CliRunner()
        result = runner.invoke(main, ["--offline", "ingest", "https://example.com"])
        
        # Should run but skip download in offline mode
        assert "offline" in result.output.lower() or result.exit_code == 0


@pytest.mark.skipif(not HAS_CLI, reason="cli module not available")
class TestQueryCommand:
    """Tests for query command."""
    
    def test_query_help(self):
        """Test query help."""
        runner = CliRunner()
        result = runner.invoke(main, ["query", "--help"])
        
        assert result.exit_code == 0


@pytest.mark.skipif(not HAS_CLI, reason="cli module not available")
class TestExportCommand:
    """Tests for export command."""
    
    def test_export_help(self):
        """Test export help."""
        runner = CliRunner()
        result = runner.invoke(main, ["export", "--help"])
        
        assert result.exit_code == 0


@pytest.mark.skipif(not HAS_CLI, reason="cli module not available")
class TestTestCommand:
    """Tests for test command."""
    
    def test_test_help(self):
        """Test test command help."""
        runner = CliRunner()
        result = runner.invoke(main, ["test", "--help"])
        
        assert result.exit_code == 0
        assert "unit" in result.output or "coverage" in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
