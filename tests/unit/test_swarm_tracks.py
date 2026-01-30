"""
Tests for Swarm Enhancement Tracks.
"""

import pytest
from datetime import datetime

# Track 1: Visual Grammar
from inception.enhance.vision.grammar import (
    VisualTokenType,
    VisualToken,
    VisualGrammar,
    VisualParser,
    GrammarEnhancedAnalyzer,
    ParseResult,
)


class TestVisualToken:
    """Tests for VisualToken."""
    
    def test_create_token(self):
        """Test creating a visual token."""
        token = VisualToken(
            id="vt_1",
            token_type=VisualTokenType.BUTTON,
            text="Submit",
            confidence=0.9,
        )
        assert token.id == "vt_1"
        assert token.token_type == VisualTokenType.BUTTON
        assert token.text == "Submit"
    
    def test_to_dict(self):
        """Test token serialization."""
        token = VisualToken(
            id="vt_1",
            token_type=VisualTokenType.NODE,
            text="Database",
        )
        d = token.to_dict()
        assert d["id"] == "vt_1"
        assert d["type"] == "node"
        assert d["text"] == "Database"


class TestVisualGrammar:
    """Tests for VisualGrammar."""
    
    def test_get_ui_rules(self):
        """Test getting UI grammar rules."""
        rules = VisualGrammar.get_rules_for_content_type("ui")
        assert len(rules) > 0
        assert all(hasattr(r, "name") for r in rules)
    
    def test_get_code_rules(self):
        """Test getting code grammar rules."""
        rules = VisualGrammar.get_rules_for_content_type("code")
        assert any(r.name == "function_def" for r in rules)
        assert any(r.name == "class_def" for r in rules)
    
    def test_get_diagram_rules(self):
        """Test getting diagram grammar rules."""
        rules = VisualGrammar.get_rules_for_content_type("diagram")
        assert any(r.name == "flow_node" for r in rules)


class TestVisualParser:
    """Tests for VisualParser."""
    
    def test_parse_code(self):
        """Test parsing code content."""
        parser = VisualParser()
        description = """
        def process_data(items):
            return [x * 2 for x in items]
        
        class DataProcessor:
            pass
        
        import pandas as pd
        """
        result = parser.parse(description, content_type="code")
        
        assert isinstance(result, ParseResult)
        assert len(result.tokens) > 0
        assert any(t.token_type == VisualTokenType.FUNCTION for t in result.tokens)
    
    def test_parse_diagram(self):
        """Test parsing diagram content."""
        parser = VisualParser()
        description = """
        The diagram shows:
        - box: Database
        - box: API Server
        Database → API Server
        API Server → Frontend
        """
        result = parser.parse(description, content_type="diagram")
        
        assert len(result.tokens) > 0
        assert "diagram_edge" in result.grammar_matches
    
    def test_parse_ui(self):
        """Test parsing UI content."""
        parser = VisualParser()
        description = """
        The interface contains:
        - button "Submit"
        - input field
        - menu item "Settings"
        - panel "Dashboard"
        """
        result = parser.parse(description, content_type="ui")
        
        assert len(result.tokens) > 0
        assert any(t.token_type == VisualTokenType.BUTTON for t in result.tokens)
    
    def test_confidence_calculation(self):
        """Test confidence is calculated."""
        parser = VisualParser()
        result = parser.parse("def foo(): pass", content_type="code")
        assert 0 <= result.confidence <= 1


class TestGrammarEnhancedAnalyzer:
    """Tests for GrammarEnhancedAnalyzer."""
    
    def test_analyze_code(self):
        """Test enhanced code analysis."""
        analyzer = GrammarEnhancedAnalyzer()
        result = analyzer.analyze(
            "import numpy\nclass Model:\n  def forward(self, x):",
            content_type="code",
        )
        
        assert "parse" in result
        assert "program" in result
        assert "summary" in result
        assert result["program"]["type"] == "code_module"
    
    def test_analyze_with_entities(self):
        """Test analysis with entity linking."""
        analyzer = GrammarEnhancedAnalyzer()
        result = analyzer.analyze(
            "The Database connects to API",
            content_type="diagram",
            entities=["Database", "API"],
        )
        
        assert "parse" in result


# Track 2: Swarm Learning
from inception.enhance.learning.swarm_coordinator import (
    LearningStrategy,
    LearningEpisode,
    SwarmSession,
    SwarmLearningCoordinator,
)


class TestLearningStrategy:
    """Tests for LearningStrategy enum."""
    
    def test_strategies_exist(self):
        """Test all strategies defined."""
        assert LearningStrategy.DSPY_MIPRO.value == "dspy_mipro"
        assert LearningStrategy.GRPO_V2.value == "grpo_v2"


class TestSwarmLearningCoordinator:
    """Tests for SwarmLearningCoordinator."""
    
    def test_initialization(self):
        """Test coordinator initialization."""
        coord = SwarmLearningCoordinator(max_workers=2)
        assert coord.max_workers == 2
        assert coord.exploration_rate == 0.3
    
    def test_run_swarm_simple(self):
        """Test simple swarm run."""
        coord = SwarmLearningCoordinator(max_workers=2)
        
        # Simple objective: longer strings score higher
        def objective(s: str) -> float:
            return len(s) / 100.0
        
        best, score = coord.run_swarm(
            objective=objective,
            initial_population=["hello world", "test string"],
            iterations_per_strategy=3,
            max_rounds=2,
        )
        
        assert isinstance(best, str)
        assert score > 0
    
    def test_strategy_stats(self):
        """Test strategy statistics."""
        coord = SwarmLearningCoordinator()
        stats = coord.get_stats()
        
        assert isinstance(stats, dict)


# Track 3: Source Intelligence
from inception.enhance.operations.source_intelligence import (
    ContentDomain,
    SourceQuality,
    SourceProfile,
    SourceIntelligence,
    ContentTracker,
)


class TestContentDomain:
    """Tests for ContentDomain enum."""
    
    def test_domains_exist(self):
        """Test domains defined."""
        assert ContentDomain.TECHNICAL.value == "technical"
        assert ContentDomain.ACADEMIC.value == "academic"


class TestSourceProfile:
    """Tests for SourceProfile."""
    
    def test_create_profile(self):
        """Test creating source profile."""
        profile = SourceProfile(
            uri="https://github.com/example/repo",
            domain=ContentDomain.TECHNICAL,
            quality=SourceQuality.REPUTABLE,
            authority_score=0.8,
        )
        
        assert profile.uri.startswith("https://")
        assert profile.domain == ContentDomain.TECHNICAL
    
    def test_overall_score(self):
        """Test overall score calculation."""
        profile = SourceProfile(
            uri="https://example.edu/paper",
            domain=ContentDomain.ACADEMIC,
            quality=SourceQuality.VERIFIED,
            authority_score=0.9,
            freshness_score=0.8,
            coverage_score=0.7,
        )
        
        score = profile.overall_score()
        assert 0 <= score <= 1


class TestSourceIntelligence:
    """Tests for SourceIntelligence."""
    
    def test_analyze_technical(self):
        """Test analyzing technical source."""
        intel = SourceIntelligence()
        profile = intel.analyze_source("https://github.com/user/repo")
        
        assert profile.domain == ContentDomain.TECHNICAL
    
    def test_analyze_academic(self):
        """Test analyzing academic source."""
        intel = SourceIntelligence()
        profile = intel.analyze_source("https://arxiv.org/abs/2024.12345")
        
        assert profile.domain == ContentDomain.ACADEMIC
    
    def test_rank_sources(self):
        """Test ranking sources."""
        intel = SourceIntelligence()
        
        # Analyze several sources
        intel.analyze_source("https://github.com/example")
        intel.analyze_source("https://example.edu/paper")
        intel.analyze_source("https://random-blog.com")
        
        ranked = intel.rank_sources([
            "https://github.com/example",
            "https://example.edu/paper",
            "https://random-blog.com",
        ])
        
        assert len(ranked) == 3
        assert all(isinstance(r[1], float) for r in ranked)


class TestContentTracker:
    """Tests for ContentTracker."""
    
    def test_record_content(self):
        """Test recording content signature."""
        tracker = ContentTracker()
        sig = tracker.record("https://example.com/doc", "This is test content.")
        
        assert sig.content_hash
        assert sig.word_count == 4
    
    def test_has_changed(self):
        """Test change detection."""
        tracker = ContentTracker()
        uri = "https://example.com/doc"
        
        tracker.record(uri, "Original content")
        
        assert not tracker.has_changed(uri, "Original content")
        assert tracker.has_changed(uri, "Modified content")
    
    def test_get_evolution(self):
        """Test evolution history."""
        tracker = ContentTracker()
        uri = "https://example.com/doc"
        
        tracker.record(uri, "Version 1")
        tracker.record(uri, "Version 2 with more content")
        
        evolution = tracker.get_evolution(uri)
        assert len(evolution) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
