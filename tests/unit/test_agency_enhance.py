"""Tests for agency enhancement module - Gap Explorer, Fact Validator, Execution Engine."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile

from inception.enhance.agency.explorer.config import (
    ExplorationConfig,
    STRICT_CONFIG,
    BALANCED_CONFIG,
    AUTONOMOUS_CONFIG,
)
from inception.enhance.agency.explorer.classifier import (
    GapClassifier,
    GapType,
    ClassifiedGap,
)
from inception.enhance.agency.explorer.search import (
    WebSearcher,
    SearchResult,
    SearchSession,
)
from inception.enhance.agency.explorer.resolver import (
    GapExplorer,
    ResolutionResult,
    ExplorationStats,
)
from inception.enhance.agency.validator.sources import (
    WikipediaSource,
    WikidataSource,
    SourceEvidence,
)
from inception.enhance.agency.validator.validator import (
    FactValidator,
    ValidationResult,
    ValidationStatus,
)
from inception.enhance.agency.executor.parser import (
    SkillParser,
    ParsedSkill,
    SkillStep,
)
from inception.enhance.agency.executor.runner import (
    ExecutionEngine,
    ExecutionConfig,
    ExecutionResult,
    ExecutionStatus,
)


# ============ GAP EXPLORER TESTS ============

class TestExplorationConfig:
    """Tests for ExplorationConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ExplorationConfig()
        
        assert config.max_requests_per_minute == 10
        assert config.budget_cap_usd == 0.50
        assert config.require_confirmation is True
    
    def test_domain_blocklist(self):
        """Test domain blocklist."""
        config = ExplorationConfig()
        
        assert config.is_domain_allowed("wikipedia.org") is True
        assert config.is_domain_allowed("reddit.com") is False
        assert config.is_domain_allowed("www.twitter.com") is False
    
    def test_domain_allowlist(self):
        """Test domain allowlist mode."""
        config = ExplorationConfig(
            domain_allowlist=["wikipedia.org", "docs.python.org"]
        )
        
        assert config.is_domain_allowed("wikipedia.org") is True
        assert config.is_domain_allowed("stackoverflow.com") is False
    
    def test_preset_configs(self):
        """Test preset configurations."""
        assert STRICT_CONFIG.budget_cap_usd == 0.10
        assert BALANCED_CONFIG.budget_cap_usd == 0.50
        assert AUTONOMOUS_CONFIG.require_confirmation is False


class TestGapClassifier:
    """Tests for GapClassifier."""
    
    @pytest.fixture
    def classifier(self):
        return GapClassifier()
    
    def test_classify_undefined_term(self, classifier):
        """Test classification of undefined term."""
        gap = classifier.classify(
            nid=1,
            payload={
                "term": "monoid",
                "context": "A monoid is used but not defined",
            },
        )
        
        assert gap.gap_type == GapType.UNDEFINED_TERM
        assert len(gap.suggested_queries) > 0
    
    def test_classify_incomplete_procedure(self, classifier):
        """Test classification of incomplete procedure."""
        gap = classifier.classify(
            nid=2,
            payload={
                "term": "deployment",
                "context": "The deployment step is incomplete",
            },
        )
        
        assert gap.gap_type == GapType.INCOMPLETE_PROCEDURE
    
    def test_priority_calculation(self, classifier):
        """Test gap priority."""
        undefined = classifier.classify(1, {"term": "x", "context": "undefined"})
        unknown = ClassifiedGap(
            nid=2, gap_type=GapType.UNKNOWN, term="", context="",
            confidence=0.5, suggested_queries=[],
        )
        
        assert undefined.priority > unknown.priority


class TestSearchResult:
    """Tests for SearchResult."""
    
    def test_from_ddg(self):
        """Test creating from DuckDuckGo result."""
        result = SearchResult.from_ddg(
            {"title": "Test", "href": "https://example.com/page", "body": "..."},
            position=1,
        )
        
        assert result.title == "Test"
        assert result.domain == "example.com"


class TestSearchSession:
    """Tests for SearchSession."""
    
    def test_budget_limit(self):
        """Test budget limit checking."""
        config = ExplorationConfig(budget_cap_usd=1.0)
        session = SearchSession(cost_usd=0.5)
        
        assert session.can_make_request(config) is True
        
        session.cost_usd = 1.5
        assert session.can_make_request(config) is False


# ============ FACT VALIDATOR TESTS ============

class TestSourceEvidence:
    """Tests for SourceEvidence."""
    
    def test_creation(self):
        """Test evidence creation."""
        evidence = SourceEvidence(
            source_name="Wikipedia",
            source_url="https://en.wikipedia.org/wiki/Python",
            relevant_text="Python is a programming language",
            confidence=0.8,
        )
        
        assert evidence.confidence == 0.8
        assert evidence.qid is None


class TestWikipediaSource:
    """Tests for WikipediaSource."""
    
    def test_is_available(self):
        """Test availability check."""
        source = WikipediaSource()
        assert source.is_available() is True
    
    def test_name(self):
        """Test source name."""
        source = WikipediaSource()
        assert source.name == "wikipedia"


class TestWikidataSource:
    """Tests for WikidataSource."""
    
    def test_is_available(self):
        """Test availability check."""
        source = WikidataSource()
        assert source.is_available() is True
    
    def test_name(self):
        """Test source name."""
        source = WikidataSource()
        assert source.name == "wikidata"


class TestValidationStatus:
    """Tests for ValidationStatus enum."""
    
    def test_all_statuses(self):
        """Test all validation statuses exist."""
        assert ValidationStatus.VERIFIED
        assert ValidationStatus.CONTRADICTED
        assert ValidationStatus.PARTIAL
        assert ValidationStatus.UNVERIFIED


class TestValidationResult:
    """Tests for ValidationResult."""
    
    def test_is_reliable_verified(self):
        """Test reliability check for verified claims."""
        result = ValidationResult(
            nid=1,
            claim_text="Test claim",
            status=ValidationStatus.VERIFIED,
            confidence=0.8,
        )
        
        assert result.is_reliable is True
    
    def test_is_reliable_low_confidence(self):
        """Test reliability check for low confidence."""
        result = ValidationResult(
            nid=1,
            claim_text="Test claim",
            status=ValidationStatus.VERIFIED,
            confidence=0.5,
        )
        
        assert result.is_reliable is False


class TestFactValidator:
    """Tests for FactValidator."""
    
    @pytest.fixture
    def mock_sources(self):
        """Create mock validation sources."""
        mock_wiki = Mock()
        mock_wiki.is_available.return_value = True
        mock_wiki.search.return_value = [
            SourceEvidence(
                source_name="Wikipedia",
                source_url="https://example.com",
                relevant_text="Python programming language created",
                confidence=0.8,
            )
        ]
        return [mock_wiki]
    
    def test_validation_with_evidence(self, mock_sources):
        """Test validation when evidence is found."""
        validator = FactValidator(sources=mock_sources)
        
        result = validator.validate(
            nid=1,
            payload={
                "text": "Python is a programming language",
                "subject": "Python",
                "predicate": "is",
                "object": "programming language",
            },
        )
        
        assert result.status in (
            ValidationStatus.VERIFIED,
            ValidationStatus.PARTIAL,
        )
    
    def test_stats_tracking(self, mock_sources):
        """Test statistics tracking."""
        validator = FactValidator(sources=mock_sources)
        
        validator.validate(1, {"text": "Test claim"})
        
        assert validator.stats["validated"] == 1


# ============ EXECUTION ENGINE TESTS ============

class TestExecutionConfig:
    """Tests for ExecutionConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = ExecutionConfig()
        
        assert config.dry_run is False
        assert config.require_confirmation is True
        assert "echo" in config.command_allowlist
    
    def test_command_safety_check(self):
        """Test command safety checking."""
        config = ExecutionConfig()
        
        # Safe commands
        is_safe, _ = config.is_command_safe("echo hello")
        assert is_safe is True
        
        is_safe, _ = config.is_command_safe("python script.py")
        assert is_safe is True
        
        # Blocked commands
        is_safe, _ = config.is_command_safe("rm -rf /")
        assert is_safe is False
        
        is_safe, _ = config.is_command_safe("sudo apt install")
        assert is_safe is False
    
    def test_unknown_command(self):
        """Test unknown command is blocked."""
        config = ExecutionConfig()
        
        is_safe, reason = config.is_command_safe("mycustomcmd arg")
        assert is_safe is False
        assert "allowlist" in reason


class TestSkillStep:
    """Tests for SkillStep."""
    
    def test_creation(self):
        """Test step creation."""
        step = SkillStep(
            index=1,
            title="Run tests",
            description="Execute the test suite",
            command="python -m pytest",
        )
        
        assert step.index == 1
        assert step.command == "python -m pytest"


class TestParsedSkill:
    """Tests for ParsedSkill."""
    
    def test_get_executable_steps(self):
        """Test getting executable steps."""
        skill = ParsedSkill(
            name="Test Skill",
            description="Test",
            goal="Test goal",
            steps=[
                SkillStep(1, "Step 1", "Desc 1", command="echo 1"),
                SkillStep(2, "Step 2", "Desc 2"),  # No command
                SkillStep(3, "Step 3", "Desc 3", command="echo 3"),
            ],
        )
        
        executable = skill.get_executable_steps()
        assert len(executable) == 2


class TestSkillParser:
    """Tests for SkillParser."""
    
    @pytest.fixture
    def parser(self):
        return SkillParser()
    
    def test_parse_content_basic(self, parser):
        """Test parsing basic SKILL.md content."""
        content = """---
name: Test Skill
description: A test skill
difficulty: beginner
---

# Goal
Learn something new

## Step 1: First Step
Do the first thing

```bash
echo "Hello"
```

## Step 2: Second Step
Do the second thing
"""
        skill = parser.parse_content(content)
        
        assert skill.name == "Test Skill"
        assert skill.difficulty == "beginner"
        assert len(skill.steps) == 2
        assert skill.steps[0].command == 'echo "Hello"'
    
    def test_extract_verification(self, parser):
        """Test extracting verification from step."""
        content = """---
name: Test
---

## Step 1: Test
Do something

```bash
echo test
```

**Verification**: Check the output says "test"
"""
        skill = parser.parse_content(content)
        
        assert skill.steps[0].verification is not None
        assert "Check" in skill.steps[0].verification


class TestExecutionEngine:
    """Tests for ExecutionEngine."""
    
    @pytest.fixture
    def engine(self):
        """Create engine with dry run enabled."""
        config = ExecutionConfig(dry_run=True, require_confirmation=False)
        return ExecutionEngine(config=config)
    
    def test_dry_run_execution(self, engine):
        """Test dry run mode."""
        skill = ParsedSkill(
            name="Test",
            description="Test",
            goal="Test",
            steps=[
                SkillStep(1, "Test", "Desc", command="echo hello"),
            ],
        )
        
        result = engine.execute_parsed_skill(skill)
        
        assert result.success is True
        assert "[DRY RUN]" in result.step_results[0].stdout
    
    def test_validate_skill(self, engine):
        """Test skill validation."""
        skill = ParsedSkill(
            name="Test",
            description="Test",
            goal="Test",
            steps=[
                SkillStep(1, "Safe", "Desc", command="echo hello"),
                SkillStep(2, "Unsafe", "Desc", command="rm -rf /"),
            ],
        )
        
        issues = engine.validate_skill(skill)
        
        assert len(issues) >= 1  # Should flag the rm -rf command
    
    def test_execution_summary(self, engine):
        """Test execution result summary."""
        skill = ParsedSkill(
            name="Test",
            description="Test",
            goal="Test",
            steps=[
                SkillStep(1, "Test", "Desc", command="echo 1"),
                SkillStep(2, "Test", "Desc", command="echo 2"),
            ],
        )
        
        result = engine.execute_parsed_skill(skill)
        
        assert "2/2" in result.summary
