"""
Unit tests for Phase 3: Semantic Bridge Layer

Tests MeaningExtractor, EnrichmentGenerator, ClarificationHandler,
and DialecticalQuestioner components.
"""

import pytest
from datetime import datetime


# =============================================================================
# Test MeaningExtractor
# =============================================================================

def test_meaning_extractor_basic():
    """Test basic meaning extraction."""
    from inception.interpret.semantic_bridge import MeaningExtractor
    
    extractor = MeaningExtractor()
    meaning = extractor.extract_meaning("Explain the thought process for debugging")
    
    assert meaning.original == "Explain the thought process for debugging"
    assert meaning.core_intent == "seeks understanding of process"
    assert "thought" in meaning.frozen_concepts
    assert "thinking" in meaning.implicit_processes


def test_meaning_extractor_finds_gerunds():
    """Test that frozen concepts are identified and verbified."""
    from inception.interpret.semantic_bridge import MeaningExtractor
    
    extractor = MeaningExtractor()
    meaning = extractor.extract_meaning("The knowledge and understanding are key")
    
    assert "knowledge" in meaning.frozen_concepts
    assert "understanding" in meaning.frozen_concepts
    assert "knowing" in meaning.implicit_processes


def test_meaning_extractor_confidence():
    """Test confidence varies based on extraction quality."""
    from inception.interpret.semantic_bridge import MeaningExtractor
    
    extractor = MeaningExtractor()
    
    # With frozen concepts should have higher confidence
    meaning1 = extractor.extract_meaning("Explain the thought")
    # Without should have lower
    meaning2 = extractor.extract_meaning("Hello world")
    
    assert meaning1.confidence >= meaning2.confidence


# =============================================================================
# Test EnrichmentGenerator
# =============================================================================

def test_enrichment_generator_basic():
    """Test basic enrichment."""
    from inception.interpret.semantic_bridge import (
        MeaningExtractor,
        EnrichmentGenerator,
        RheoLevel,
    )
    
    extractor = MeaningExtractor()
    enricher = EnrichmentGenerator()
    
    meaning = extractor.extract_meaning("Explain the analysis")
    enriched = enricher.enrich(meaning, RheoLevel.GERUNDIVE)
    
    assert enriched.original == "Explain the analysis"
    assert enriched.rheo_level == RheoLevel.GERUNDIVE
    assert len(enriched.context_injections) > 0


def test_enrichment_processual_level():
    """Test processual level enrichment."""
    from inception.interpret.semantic_bridge import (
        MeaningExtractor,
        EnrichmentGenerator,
        RheoLevel,
    )
    
    extractor = MeaningExtractor()
    enricher = EnrichmentGenerator()
    
    meaning = extractor.extract_meaning("Check the code")
    enriched = enricher.enrich(meaning, RheoLevel.PROCESSUAL)
    
    assert "process" in enriched.enriched.lower()
    assert enriched.rheo_level == RheoLevel.PROCESSUAL


# =============================================================================
# Test ClarificationHandler
# =============================================================================

def test_clarification_meaning():
    """Test meaning clarification."""
    from inception.interpret.semantic_bridge import ClarificationHandler
    
    handler = ClarificationHandler()
    request = handler.clarify_meaning("thought", "debugging context")
    
    assert request.clarification_type == "meaning"
    assert "thought" in request.question
    assert len(request.options) > 0


def test_clarification_intent():
    """Test intent clarification."""
    from inception.interpret.semantic_bridge import ClarificationHandler
    
    handler = ClarificationHandler()
    request = handler.clarify_intent("explain", "user prompt context")
    
    assert request.clarification_type == "intent"
    assert "explain" in request.question
    assert len(request.options) >= 3


def test_clarification_implications():
    """Test implications exploration."""
    from inception.interpret.semantic_bridge import ClarificationHandler
    
    handler = ClarificationHandler()
    request = handler.explore_implications("TypeScript is better than JavaScript")
    
    assert request.clarification_type == "implications"
    assert "TypeScript" in request.question
    assert len(request.options) >= 3


# =============================================================================
# Test FlowState
# =============================================================================

def test_flow_state_momentum():
    """Test flow state momentum updates."""
    from inception.interpret.semantic_bridge import FlowState
    
    state = FlowState(session_id="test")
    initial_momentum = state.momentum
    
    state.update_momentum(0.2)
    assert state.momentum > initial_momentum
    
    state.update_momentum(-0.5)
    assert state.momentum >= 0.0


def test_flow_state_dialectical():
    """Test dialectical mode in flow state."""
    from inception.interpret.semantic_bridge import FlowState, MeaningFlow
    
    state = FlowState(session_id="test")
    state.enter_dialectical("TypeScript is essential")
    
    assert state.thesis_active == "TypeScript is essential"
    assert state.overall_direction == MeaningFlow.SPIRALING
    
    state.propose_antithesis("JavaScript is sufficient")
    assert state.antithesis_active == "JavaScript is sufficient"
    
    state.begin_synthesis()
    assert state.synthesis_forming is True
    assert state.overall_direction == MeaningFlow.CRYSTALLIZING


# =============================================================================
# Test SemanticBridge
# =============================================================================

def test_semantic_bridge_process():
    """Test unified semantic bridge processing."""
    from inception.interpret.semantic_bridge import SemanticBridge
    
    bridge = SemanticBridge("test-session")
    enriched, clarifications = bridge.process_prompt("Explain the thought process")
    
    assert enriched.original == "Explain the thought process"
    assert len(enriched.enriched) >= len(enriched.original)


def test_semantic_bridge_agent_registration():
    """Test agent registration."""
    from inception.interpret.semantic_bridge import SemanticBridge
    
    bridge = SemanticBridge("test-session")
    annotator = bridge.register_agent("DIALECTICA")
    
    ann = annotator.add_meaning_annotation("This is about debugging")
    assert ann.agent_id == "DIALECTICA"
    assert ann.annotation_type == "meaning"


def test_semantic_bridge_flow_summary():
    """Test flow summary generation."""
    from inception.interpret.semantic_bridge import SemanticBridge
    
    bridge = SemanticBridge("test-session")
    bridge.process_prompt("Test prompt 1")
    bridge.process_prompt("Test prompt 2")
    
    summary = bridge.get_flow_summary()
    assert summary["turn_count"] == 2
    assert "momentum" in summary


# =============================================================================
# Test DialecticalQuestioner
# =============================================================================

def test_questioner_why_mode():
    """Test WHY mode questioning."""
    from inception.interpret.questioning_modes import (
        DialecticalQuestioner,
        QuestioningMode,
    )
    
    questioner = DialecticalQuestioner()
    question = questioner.question("TypeScript improves code quality", QuestioningMode.WHY)
    
    assert question.mode == QuestioningMode.WHY
    assert "why" in question.transformed_question.lower() or "cause" in question.transformed_question.lower()


def test_questioner_steelman_mode():
    """Test STEELMAN mode questioning."""
    from inception.interpret.questioning_modes import (
        DialecticalQuestioner,
        QuestioningMode,
    )
    
    questioner = DialecticalQuestioner()
    question = questioner.question("Microservices are better", QuestioningMode.STEELMAN)
    
    assert question.mode == QuestioningMode.STEELMAN
    # Steelman mode asks for strongest counter-arguments
    q = question.transformed_question.lower()
    assert any(word in q for word in ["against", "critic", "undermine", "strongest", "counter"])


def test_questioner_full_examination():
    """Test full dialectical examination."""
    from inception.interpret.questioning_modes import DialecticalQuestioner
    
    questioner = DialecticalQuestioner()
    questions = questioner.full_examination("REST API is the best choice")
    
    assert len(questions) == 5  # One for each mode
    modes = {q.mode for q in questions}
    assert len(modes) == 5  # All different modes


def test_questioner_socratic_chain():
    """Test Socratic chain generation."""
    from inception.interpret.questioning_modes import DialecticalQuestioner
    
    questioner = DialecticalQuestioner()
    chain = list(questioner.socratic_chain("Tests are important", max_depth=3))
    
    assert len(chain) == 3
    for i, q in enumerate(chain):
        assert q.depth == i + 1


def test_questioner_dialectical_spiral():
    """Test dialectical spiral generation."""
    from inception.interpret.questioning_modes import DialecticalQuestioner
    
    questioner = DialecticalQuestioner()
    questions = questioner.dialectical_spiral(
        thesis="Use SQL",
        antithesis="Use NoSQL",
    )
    
    assert len(questions) >= 5
    # Should have hidden assumptions for both
    # Should have steelman for both
    # Should have what-if for synthesis


# =============================================================================
# Test Integration
# =============================================================================

def test_integrate_with_flow():
    """Test integration helper."""
    from inception.interpret.questioning_modes import (
        DialecticalQuestioner,
        integrate_with_flow,
    )
    
    questioner = DialecticalQuestioner()
    result = integrate_with_flow(questioner, "Test claim")
    
    assert "claim" in result
    assert "questions" in result
    assert len(result["questions"]) == 5
    assert "recommended_next" in result
