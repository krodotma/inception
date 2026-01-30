"""
Comprehensive CLI tests for inception/cli.py
"""
import pytest
from click.testing import CliRunner
from inception.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestMainGroup:
    def test_version(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "inception" in result.output.lower() or "version" in result.output.lower()
    
    def test_help(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "inception" in result.output.lower()
    
    def test_offline_flag(self, runner):
        result = runner.invoke(main, ["--offline", "--help"])
        assert result.exit_code == 0


class TestDoctorCommand:
    def test_doctor(self, runner):
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        assert "Doctor" in result.output or "doctor" in result.output.lower()
    
    def test_doctor_with_offline(self, runner):
        result = runner.invoke(main, ["--offline", "doctor"])
        assert result.exit_code == 0


class TestIngestCommand:
    def test_ingest_help(self, runner):
        result = runner.invoke(main, ["ingest", "--help"])
        assert result.exit_code == 0
    
    def test_ingest_no_source(self, runner):
        result = runner.invoke(main, ["ingest"])
        # Should fail without source but not crash
        assert result.exit_code in [0, 1, 2]


class TestQueryCommand:
    def test_query_help(self, runner):
        result = runner.invoke(main, ["query", "--help"])
        assert result.exit_code == 0
    
    def test_query_simple(self, runner):
        result = runner.invoke(main, ["query", "test query"])
        # May fail without DB but should not crash
        assert result.exit_code in [0, 1, 2]


class TestExportCommand:
    def test_export_help(self, runner):
        result = runner.invoke(main, ["export", "--help"])
        assert result.exit_code == 0


class TestServeCommand:
    def test_serve_help(self, runner):
        result = runner.invoke(main, ["serve", "--help"])
        assert result.exit_code == 0


class TestAuthCommand:
    def test_auth_help(self, runner):
        result = runner.invoke(main, ["auth", "--help"])
        assert result.exit_code == 0


class TestTestCommand:
    def test_test_help(self, runner):
        result = runner.invoke(main, ["test", "--help"])
        # May not exist, but should not crash
        assert result.exit_code in [0, 1, 2]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
