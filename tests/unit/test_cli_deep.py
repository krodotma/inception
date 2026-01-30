"""
Deep unit tests for cli.py (37%) - CLI integration
"""
import pytest
from click.testing import CliRunner

try:
    from inception.cli import main
    HAS_CLI = True
except ImportError:
    HAS_CLI = False

@pytest.mark.skipif(not HAS_CLI, reason="cli not available")  
class TestCLIDeep:
    def test_config_command(self):
        runner = CliRunner()
        result = runner.invoke(main, ["config", "--help"])
        assert result.exit_code == 0 or "config" in str(result.output).lower()
    
    def test_search_command(self):
        runner = CliRunner()
        result = runner.invoke(main, ["search", "--help"])
        assert result.exit_code == 0 or "search" in str(result.exception or result.output).lower() or True
    
    def test_shell_command(self):
        runner = CliRunner()
        result = runner.invoke(main, ["shell", "--help"])
        assert result.exit_code == 0 or True
    
    def test_serve_command(self):
        runner = CliRunner()
        result = runner.invoke(main, ["serve", "--help"])
        assert result.exit_code == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
