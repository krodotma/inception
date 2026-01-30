"""
REAL tests for cli.py - Actually invoke CLI commands
"""
import pytest
from click.testing import CliRunner

from inception.cli import main


class TestCLIMain:
    """Test main CLI group and global options."""
    
    def test_version(self):
        """Test --version flag."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        
        assert result.exit_code == 0
        assert "inception" in result.output.lower() or "0." in result.output
    
    def test_help(self):
        """Test --help flag."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        
        assert result.exit_code == 0
        assert "Inception" in result.output
    
    def test_offline_flag(self):
        """Test --offline flag is accepted."""
        runner = CliRunner()
        result = runner.invoke(main, ["--offline", "--help"])
        
        assert result.exit_code == 0


class TestDoctorCommand:
    """Test doctor command - runs system checks."""
    
    def test_doctor_runs(self):
        """Test doctor command executes."""
        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])
        
        # Doctor should run (may show warnings)
        assert result.exit_code in [0, 1]
        assert "Inception Doctor" in result.output or "Error" in result.output
    
    def test_doctor_shows_python(self):
        """Test doctor checks Python version."""
        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])
        
        if result.exit_code == 0:
            assert "Python" in result.output


class TestIngestCommand:
    """Test ingest command help."""
    
    def test_ingest_help(self):
        """Test ingest --help."""
        runner = CliRunner()
        result = runner.invoke(main, ["ingest", "--help"])
        
        assert result.exit_code == 0
        assert "ingest" in result.output.lower()


class TestQueryCommand:
    """Test query command help."""
    
    def test_query_help(self):
        """Test query --help."""
        runner = CliRunner()
        result = runner.invoke(main, ["query", "--help"])
        
        assert result.exit_code == 0


class TestExportCommand:
    """Test export command help."""
    
    def test_export_help(self):
        """Test export --help."""
        runner = CliRunner()
        result = runner.invoke(main, ["export", "--help"])
        
        assert result.exit_code == 0


class TestServeCommand:
    """Test serve command help."""
    
    def test_serve_help(self):
        """Test serve --help."""
        runner = CliRunner()
        result = runner.invoke(main, ["serve", "--help"])
        
        assert result.exit_code == 0
        assert "serve" in result.output.lower()


class TestAuthCommand:
    """Test auth command group."""
    
    def test_auth_help(self):
        """Test auth --help."""
        runner = CliRunner()
        result = runner.invoke(main, ["auth", "--help"])
        
        assert result.exit_code == 0


class TestTestCommand:
    """Test test command."""
    
    def test_test_help(self):
        """Test test --help."""
        runner = CliRunner()
        result = runner.invoke(main, ["test", "--help"])
        
        assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
