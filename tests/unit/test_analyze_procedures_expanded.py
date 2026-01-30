"""
Expanded unit tests for analyze/procedures.py

Additional tests to improve coverage on procedures module.
"""

import pytest

try:
    from inception.analyze.procedures import (
        ProcedureStep,
        Procedure,
        ProcedureExtractionResult,
        ProcedureExtractor,
    )
    HAS_PROCEDURES = True
except ImportError:
    HAS_PROCEDURES = False


@pytest.mark.skipif(not HAS_PROCEDURES, reason="procedures module not available")
class TestProcedureStepExpanded:
    """Expanded tests for ProcedureStep dataclass."""
    
    def test_creation_full(self):
        """Test creating step with all fields."""
        step = ProcedureStep(
            step_number=1,
            text="First, preheat the oven to 350°F",
            action_verb="preheat",
            object_noun="oven",
            is_optional=False,
        )
        
        assert step.step_number == 1
        assert step.action_verb == "preheat"
    
    def test_step_with_duration(self):
        """Test step with duration."""
        step = ProcedureStep(
            step_number=2,
            text="Bake for 30 minutes",
            duration_ms=1800000,
        )
        
        assert step.duration_ms == 1800000
    
    def test_optional_step(self):
        """Test optional step."""
        step = ProcedureStep(
            step_number=3,
            text="Optionally, add sprinkles",
            is_optional=True,
        )
        
        assert step.is_optional is True


@pytest.mark.skipif(not HAS_PROCEDURES, reason="procedures module not available")
class TestProcedureExpanded:
    """Expanded tests for Procedure dataclass."""
    
    def test_creation_full(self):
        """Test creating with all fields."""
        steps = [
            ProcedureStep(step_number=1, text="Step 1"),
            ProcedureStep(step_number=2, text="Step 2"),
        ]
        proc = Procedure(
            title="Recipe",
            steps=steps,
            description="A simple recipe",
        )
        
        assert proc.title == "Recipe"
        assert proc.step_count == 2
    
    def test_procedure_duration(self):
        """Test total procedure duration."""
        steps = [
            ProcedureStep(step_number=1, text="Step 1", duration_ms=60000),
            ProcedureStep(step_number=2, text="Step 2", duration_ms=120000),
        ]
        proc = Procedure(title="Test", steps=steps)
        
        total = proc.total_duration_ms
        
        assert total == 180000


@pytest.mark.skipif(not HAS_PROCEDURES, reason="procedures module not available")
class TestProcedureExtractionResultExpanded:
    """Expanded tests for ProcedureExtractionResult."""
    
    def test_filter_by_length(self):
        """Test filtering by step count."""
        procs = [
            Procedure(title="Short", steps=[ProcedureStep(step_number=1, text="S1")]),
            Procedure(title="Long", steps=[ProcedureStep(step_number=i, text=f"S{i}") for i in range(1, 6)]),
        ]
        result = ProcedureExtractionResult(procedures=procs)
        
        long_procs = [p for p in result.procedures if p.step_count >= 5]
        
        assert len(long_procs) == 1


@pytest.mark.skipif(not HAS_PROCEDURES, reason="procedures module not available")
class TestProcedureExtractorExpanded:
    """Expanded tests for ProcedureExtractor."""
    
    def test_creation_with_model(self):
        """Test with custom model."""
        extractor = ProcedureExtractor(model_name="en_core_web_lg")
        
        assert extractor.model_name == "en_core_web_lg"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
