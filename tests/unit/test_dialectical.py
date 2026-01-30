"""
Unit tests for dialectical.py

Tests for:
- DialecticalTree and branch management
- AntithesisDetector pattern detection
- SynthesisGenerator candidate generation
- SocraticProtocol question generation
"""

import pytest
from datetime import datetime

from inception.db.dialectical import (
    BranchType,
    DialecticalBranch,
    DialecticalTree,
    AntithesisPattern,
    AntithesisDetection,
    AntithesisDetector,
    SynthesisCandidate,
    SynthesisGenerator,
    QuestionType,
    SocraticQuestion,
    SocraticProtocol,
    create_dialectical_session,
)


# =============================================================================
# Test: DialecticalBranch
# =============================================================================

class TestDialecticalBranch:
    """Tests for DialecticalBranch dataclass."""
    
    def test_branch_creation(self):
        """Test creating a dialectical branch."""
        branch = DialecticalBranch(
            branch_id="test-1",
            branch_type=BranchType.THESIS,
            content="Python is better than JavaScript",
        )
        
        assert branch.branch_id == "test-1"
        assert branch.branch_type == BranchType.THESIS
        assert branch.content == "Python is better than JavaScript"
        assert branch.parent_id is None
        assert branch.children_ids == []
        assert branch.confidence == 0.5
        assert branch.proposing_agent == "DIALECTICA"
        assert branch.resolved is False
        assert branch.resolution_id is None
    
    def test_branch_with_evidence(self):
        """Test branch with evidence tracking."""
        branch = DialecticalBranch(
            branch_id="test-2",
            branch_type=BranchType.EVIDENCE,
            content="Studies show...",
            evidence_nids=[100, 200, 300],
            confidence=0.85,
        )
        
        assert branch.evidence_nids == [100, 200, 300]
        assert branch.confidence == 0.85


# =============================================================================
# Test: DialecticalTree
# =============================================================================

class TestDialecticalTree:
    """Tests for DialecticalTree structure."""
    
    def test_tree_initialization(self):
        """Test creating a dialectical tree with root thesis."""
        tree = DialecticalTree("Microservices are the best architecture")
        
        assert tree.root_id is not None
        assert tree.idea_nid is None
        assert len(tree.branches) == 1
        
        root = tree.branches[tree.root_id]
        assert root.branch_type == BranchType.THESIS
        assert root.content == "Microservices are the best architecture"
    
    def test_tree_with_idea_nid(self):
        """Test tree with associated idea NID."""
        tree = DialecticalTree("Monoliths scale well", idea_nid=42)
        
        assert tree.idea_nid == 42
    
    def test_add_antithesis(self):
        """Test adding antithesis to a thesis."""
        tree = DialecticalTree("REST is better than GraphQL")
        
        antithesis_id = tree.add_antithesis(
            tree.root_id,
            "GraphQL provides more flexibility than REST"
        )
        
        assert antithesis_id in tree.branches
        antithesis = tree.branches[antithesis_id]
        assert antithesis.branch_type == BranchType.ANTITHESIS
        assert antithesis.parent_id == tree.root_id
        
        # Check parent has child reference
        thesis = tree.branches[tree.root_id]
        assert antithesis_id in thesis.children_ids
    
    def test_add_antithesis_invalid_thesis(self):
        """Test adding antithesis to non-existent thesis raises error."""
        tree = DialecticalTree("Some thesis")
        
        with pytest.raises(ValueError, match="not found"):
            tree.add_antithesis("invalid-id", "Some antithesis")
    
    def test_add_synthesis(self):
        """Test adding synthesis to resolve thesis/antithesis."""
        tree = DialecticalTree("Always use SQL databases")
        antithesis_id = tree.add_antithesis(tree.root_id, "NoSQL is better for scale")
        
        synthesis_id = tree.add_synthesis(
            tree.root_id,
            antithesis_id,
            "Use SQL for transactions, NoSQL for scale"
        )
        
        assert synthesis_id in tree.branches
        synthesis = tree.branches[synthesis_id]
        assert synthesis.branch_type == BranchType.SYNTHESIS
        assert synthesis.resolved is True
        
        # Both thesis and antithesis should be resolved
        assert tree.branches[tree.root_id].resolved is True
        assert tree.branches[tree.root_id].resolution_id == synthesis_id
        assert tree.branches[antithesis_id].resolved is True
        assert tree.branches[antithesis_id].resolution_id == synthesis_id
    
    def test_add_question(self):
        """Test adding Socratic questions."""
        tree = DialecticalTree("Testing is always good")
        
        question_id = tree.add_question(
            tree.root_id,
            "What do you mean by 'always'?"
        )
        
        assert question_id in tree.branches
        question = tree.branches[question_id]
        assert question.branch_type == BranchType.QUESTION
        assert question.parent_id == tree.root_id
    
    def test_get_unresolved_pairs(self):
        """Test finding unresolved thesis/antithesis pairs."""
        tree = DialecticalTree("Python is slow")
        antithesis_id = tree.add_antithesis(tree.root_id, "Python is fast enough")
        
        pairs = tree.get_unresolved_pairs()
        
        assert len(pairs) == 1
        thesis, antithesis = pairs[0]
        assert thesis.branch_type == BranchType.THESIS
        assert antithesis.branch_type == BranchType.ANTITHESIS
        
        # After synthesis, no unresolved pairs
        tree.add_synthesis(tree.root_id, antithesis_id, "Python is fast for most use cases")
        pairs = tree.get_unresolved_pairs()
        assert len(pairs) == 0
    
    def test_to_mermaid(self):
        """Test Mermaid diagram export."""
        tree = DialecticalTree("Thesis statement here")
        tree.add_antithesis(tree.root_id, "Antithesis statement")
        
        mermaid = tree.to_mermaid()
        
        assert "flowchart TB" in mermaid
        assert "Thesis statement here" in mermaid
        assert "Antithesis statement" in mermaid
        assert "-->" in mermaid  # Edge arrow
    
    def test_to_mermaid_long_content_truncated(self):
        """Test Mermaid truncates long content."""
        long_content = "This is a very long thesis that should be truncated for display purposes"
        tree = DialecticalTree(long_content)
        
        mermaid = tree.to_mermaid()
        
        # Content should be truncated with "..."
        assert "..." in mermaid


# =============================================================================
# Test: AntithesisDetector
# =============================================================================

class TestAntithesisDetector:
    """Tests for AntithesisDetector."""
    
    def test_detector_negation_pattern(self):
        """Test detecting negation-based antitheses."""
        detector = AntithesisDetector()
        
        thesis = "Python is a good programming language"
        candidates = [
            (1, "Python is not a good programming language"),
            (2, "JavaScript is a programming language"),
        ]
        
        detections = detector.detect_antithesis(thesis, candidates)
        
        # Should detect the negation
        assert len(detections) >= 1
        assert any(d.pattern == AntithesisPattern.NEGATION for d in detections)
    
    def test_detector_opposition_pattern(self):
        """Test detecting opposition-based antitheses."""
        detector = AntithesisDetector()
        
        thesis = "This approach is simple and fast"
        candidates = [
            (1, "This approach is complex and slow"),
            (2, "Other approaches exist"),
        ]
        
        detections = detector.detect_antithesis(thesis, candidates)
        
        # Should detect opposition pairs (simple/complex, fast/slow)
        assert len(detections) >= 1
        opposition_detections = [d for d in detections if d.pattern == AntithesisPattern.OPPOSITION]
        assert len(opposition_detections) >= 1
    
    def test_detector_no_antithesis(self):
        """Test no antithesis found for unrelated claims."""
        detector = AntithesisDetector()
        
        thesis = "Python has good documentation"
        candidates = [
            (1, "TypeScript is popular"),
            (2, "Go was created at Google"),
        ]
        
        detections = detector.detect_antithesis(thesis, candidates)
        
        assert len(detections) == 0
    
    def test_detector_results_sorted_by_confidence(self):
        """Test results are sorted by confidence descending."""
        detector = AntithesisDetector()
        
        thesis = "All code must be tested"
        candidates = [
            (1, "None code needs to be tested"),  # Opposition: all vs none
            (2, "Code is not tested often"),
        ]
        
        detections = detector.detect_antithesis(thesis, candidates)
        
        if len(detections) > 1:
            assert detections[0].confidence >= detections[1].confidence


# =============================================================================
# Test: SynthesisGenerator
# =============================================================================

class TestSynthesisGenerator:
    """Tests for SynthesisGenerator."""
    
    def test_generate_candidates(self):
        """Test generating synthesis candidates."""
        generator = SynthesisGenerator()
        
        candidates = generator.generate_candidates(
            thesis="Always use ORM",
            antithesis="Raw SQL is better",
        )
        
        assert len(candidates) == 3  # Three strategies
        
        strategies = {c.strategy for c in candidates}
        assert "contextualization" in strategies
        assert "scoping" in strategies
        assert "integration" in strategies
    
    def test_candidate_structure(self):
        """Test SynthesisCandidate structure."""
        generator = SynthesisGenerator()
        
        candidates = generator.generate_candidates(
            thesis="Use microservices",
            antithesis="Use monolith",
        )
        
        for candidate in candidates:
            assert candidate.thesis == "Use microservices"
            assert candidate.antithesis == "Use monolith"
            assert isinstance(candidate.synthesis, str)
            assert candidate.strategy in generator.STRATEGIES
            assert 0 <= candidate.confidence <= 1
            assert isinstance(candidate.conditions, list)
    
    def test_generator_strategies_constant(self):
        """Test STRATEGIES constant is available."""
        generator = SynthesisGenerator()
        
        assert len(generator.STRATEGIES) >= 5
        assert "contextualization" in generator.STRATEGIES
        assert "dialectical" in generator.STRATEGIES


# =============================================================================
# Test: SocraticProtocol
# =============================================================================

class TestSocraticProtocol:
    """Tests for SocraticProtocol."""
    
    def test_generate_questions_default(self):
        """Test generating questions with default types."""
        protocol = SocraticProtocol()
        
        questions = protocol.generate_questions("Testing is essential")
        
        assert len(questions) >= 1
        assert len(questions) <= 3  # max_questions default
        
        for q in questions:
            assert isinstance(q, SocraticQuestion)
            assert q.target_claim == "Testing is essential"
            assert isinstance(q.question, str)
            assert isinstance(q.purpose, str)
    
    def test_generate_questions_specific_types(self):
        """Test generating questions with specific types."""
        protocol = SocraticProtocol()
        
        questions = protocol.generate_questions(
            "Python is the best language",
            question_types=[QuestionType.REQUEST_EVIDENCE, QuestionType.EXPLORE_ALTERNATIVE],
            max_questions=5,
        )
        
        assert len(questions) == 2
        types = {q.question_type for q in questions}
        assert QuestionType.REQUEST_EVIDENCE in types
        assert QuestionType.EXPLORE_ALTERNATIVE in types
    
    def test_generate_questions_steelman(self):
        """Test generating steelman questions."""
        protocol = SocraticProtocol()
        
        questions = protocol.generate_questions(
            "Static typing is superior",
            question_types=[QuestionType.STEELMAN],
        )
        
        assert len(questions) == 1
        # The question may randomly pick from templates, check for any valid keyword
        q = questions[0].question.lower()
        assert any(word in q for word in ["strongest", "opposing", "defender", "antithesis", "merit"])
    
    def test_steelman_opposition(self):
        """Test steelman_opposition method."""
        protocol = SocraticProtocol()
        
        result = protocol.steelman_opposition(
            thesis="Functional programming is better",
            antithesis="OOP is more practical",
        )
        
        assert "OOP is more practical" in result
        assert "Functional programming is better" in result
        assert "[STEELMAN]" in result  # Placeholder for actual steelman
    
    def test_question_templates_exist(self):
        """Test that question templates are defined."""
        protocol = SocraticProtocol()
        
        assert len(protocol.QUESTION_TEMPLATES) >= 5
        assert QuestionType.CLARIFY_MEANING in protocol.QUESTION_TEMPLATES
        assert QuestionType.PROBE_ASSUMPTION in protocol.QUESTION_TEMPLATES
        assert QuestionType.REQUEST_EVIDENCE in protocol.QUESTION_TEMPLATES


# =============================================================================
# Test: Factory Function
# =============================================================================

class TestCreateDialecticalSession:
    """Tests for create_dialectical_session factory."""
    
    def test_create_session(self):
        """Test creating a dialectical session."""
        tree, protocol = create_dialectical_session("AI will transform programming")
        
        assert isinstance(tree, DialecticalTree)
        assert isinstance(protocol, SocraticProtocol)
        assert tree.branches[tree.root_id].content == "AI will transform programming"
    
    def test_create_session_with_idea_nid(self):
        """Test creating session with idea NID."""
        tree, protocol = create_dialectical_session(
            thesis="Cloud is cheaper",
            idea_nid=999,
        )
        
        assert tree.idea_nid == 999


# =============================================================================
# Test: Enums
# =============================================================================

class TestEnums:
    """Test enum definitions."""
    
    def test_branch_type_values(self):
        """Test BranchType enum values."""
        assert BranchType.THESIS.value == "thesis"
        assert BranchType.ANTITHESIS.value == "antithesis"
        assert BranchType.SYNTHESIS.value == "synthesis"
        assert BranchType.QUESTION.value == "question"
        assert BranchType.EVIDENCE.value == "evidence"
        assert BranchType.HYPOTHETICAL.value == "hypothetical"
    
    def test_antithesis_pattern_values(self):
        """Test AntithesisPattern enum values."""
        assert AntithesisPattern.NEGATION.value == "negation"
        assert AntithesisPattern.OPPOSITION.value == "opposition"
        assert AntithesisPattern.ALTERNATIVE.value == "alternative"
    
    def test_question_type_values(self):
        """Test QuestionType enum values."""
        assert QuestionType.CLARIFY_MEANING.value == "clarify_meaning"
        assert QuestionType.PROBE_ASSUMPTION.value == "probe_assumption"
        assert QuestionType.STEELMAN.value == "steelman"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
