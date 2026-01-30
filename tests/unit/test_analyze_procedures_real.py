"""
REAL tests for analyze/procedures.py
"""
import pytest
from inception.analyze.procedures import ProcedureExtractor, Procedure, ProcedureStep


class TestProcedureStep:
    def test_creation(self):
        step = ProcedureStep(
            index=1,
            text="Preheat oven to 350F",
        )
        assert step.index == 1
        assert step.text == "Preheat oven to 350F"


class TestProcedure:
    def test_creation(self):
        step1 = ProcedureStep(index=1, text="Step 1")
        step2 = ProcedureStep(index=2, text="Step 2")
        proc = Procedure(
            title="Recipe",
            goal="Make a cake",
            steps=[step1, step2],
        )
        assert proc.title == "Recipe"
        assert len(proc.steps) == 2


class TestProcedureExtractor:
    def test_creation(self):
        extractor = ProcedureExtractor()
        assert extractor is not None
    
    def test_extract_simple(self):
        extractor = ProcedureExtractor()
        text = "First, mix the ingredients. Then, bake for 30 minutes."
        result = extractor.extract(text)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
