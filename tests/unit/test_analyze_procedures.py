"""
Unit tests for analyze/procedures.py

Tests for procedure extraction:
- ProcedureStep: Step data class
- Procedure: Full procedure
- ProcedureExtractor: Main extractor
"""

import pytest

try:
    from inception.analyze.procedures import (
        ProcedureStep,
        Procedure,
        ProcedureExtractionResult,
        ProcedureExtractor,
        extract_procedures,
        procedure_to_skill,
        STEP_PATTERNS,
        ACTION_VERBS,
    )
    HAS_PROCEDURES = True
except ImportError:
    HAS_PROCEDURES = False


@pytest.mark.skipif(not HAS_PROCEDURES, reason="procedures module not available")
class TestProcedureStep:
    """Tests for ProcedureStep dataclass."""
    
    def test_creation(self):
        """Test creating a step."""
        step = ProcedureStep(
            index=1,
            text="Open the terminal",
            action_verb="open",
            object="terminal",
        )
        
        assert step.index == 1
        assert step.action_verb == "open"
    
    def test_with_conditions(self):
        """Test step with conditions."""
        step = ProcedureStep(
            index=2,
            text="If logged in, click settings",
            conditions=["logged in"],
        )
        
        assert len(step.conditions) == 1
    
    def test_with_dependencies(self):
        """Test step with dependencies."""
        step = ProcedureStep(
            index=3,
            text="Save the file",
            depends_on=[1, 2],
        )
        
        assert 1 in step.depends_on


@pytest.mark.skipif(not HAS_PROCEDURES, reason="procedures module not available")
class TestProcedure:
    """Tests for Procedure dataclass."""
    
    def test_creation_minimal(self):
        """Test creating minimal procedure."""
        proc = Procedure()
        
        assert proc.steps == []
        assert proc.step_count() == 0
    
    def test_creation_with_steps(self):
        """Test creating procedure with steps."""
        steps = [
            ProcedureStep(index=1, text="Step 1"),
            ProcedureStep(index=2, text="Step 2"),
        ]
        proc = Procedure(title="Test", steps=steps)
        
        assert proc.step_count() == 2
    
    def test_with_title_and_goal(self):
        """Test procedure with title and goal."""
        proc = Procedure(
            title="Install Python",
            goal="Get Python running on your system",
        )
        
        assert proc.title == "Install Python"
        assert proc.goal is not None
    
    def test_kind(self):
        """Test procedure kind."""
        proc = Procedure()
        
        kind = proc.kind()
        
        assert kind is not None
    
    def test_to_markdown(self):
        """Test markdown conversion."""
        steps = [ProcedureStep(index=1, text="Do this")]
        proc = Procedure(title="Test", steps=steps)
        
        md = proc.to_markdown()
        
        assert "Test" in md or "Do this" in md


@pytest.mark.skipif(not HAS_PROCEDURES, reason="procedures module not available")
class TestProcedureExtractionResult:
    """Tests for ProcedureExtractionResult."""
    
    def test_creation(self):
        """Test creating result."""
        result = ProcedureExtractionResult()
        
        assert result.procedures == []
        assert result.procedure_count() == 0
    
    def test_with_procedures(self):
        """Test with procedures."""
        procs = [Procedure(), Procedure()]
        result = ProcedureExtractionResult(procedures=procs)
        
        assert result.procedure_count() == 2


@pytest.mark.skipif(not HAS_PROCEDURES, reason="procedures module not available")
class TestProcedureExtractor:
    """Tests for ProcedureExtractor."""
    
    def test_creation(self):
        """Test creating extractor."""
        extractor = ProcedureExtractor()
        
        assert extractor is not None


@pytest.mark.skipif(not HAS_PROCEDURES, reason="procedures module not available")
class TestProcedureFunctions:
    """Tests for module-level functions."""
    
    def test_action_verbs_defined(self):
        """Test action verbs are defined."""
        assert "click" in ACTION_VERBS
        assert "open" in ACTION_VERBS
    
    def test_procedure_to_skill(self):
        """Test converting procedure to skill."""
        steps = [ProcedureStep(index=1, text="Open file")]
        proc = Procedure(title="Open File", steps=steps)
        
        skill = procedure_to_skill(proc)
        
        assert isinstance(skill, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
