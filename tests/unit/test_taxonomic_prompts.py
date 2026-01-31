"""
Tests for extract/taxonomic_prompts.py (0%) - targeting ExtractionPrompt and prompts
"""
import pytest

try:
    from inception.extract.taxonomic_prompts import (
        ExtractionPrompt,
        EXTRACTION_PROMPTS,
        get_extraction_prompt,
        format_prompt,
        DOMAIN_EXTRACTION_SYSTEM,
        IDEA_EXTRACTION_SYSTEM,
    )
    HAS_PROMPTS = True
except ImportError:
    HAS_PROMPTS = False


@pytest.mark.skipif(not HAS_PROMPTS, reason="taxonomic_prompts not available")
class TestExtractionPrompt:
    """Test ExtractionPrompt dataclass."""
    
    def test_creation(self):
        prompt = ExtractionPrompt(
            name="test",
            target_type="Test",
            system_message="You are a test.",
            user_template="Test: {text}",
        )
        assert prompt.name == "test"
        assert prompt.target_type == "Test"
    
    def test_output_schema_default(self):
        prompt = ExtractionPrompt(
            name="test",
            target_type="Test",
            system_message="System",
            user_template="User",
        )
        assert prompt.output_schema is None


@pytest.mark.skipif(not HAS_PROMPTS, reason="taxonomic_prompts not available")
class TestExtractionPromptsRegistry:
    """Test EXTRACTION_PROMPTS registry."""
    
    def test_has_domain(self):
        assert "domain" in EXTRACTION_PROMPTS
    
    def test_has_idea(self):
        assert "idea" in EXTRACTION_PROMPTS
    
    def test_has_project(self):
        assert "project" in EXTRACTION_PROMPTS
    
    def test_has_contact(self):
        assert "contact" in EXTRACTION_PROMPTS
    
    def test_has_synthesis(self):
        assert "synthesis" in EXTRACTION_PROMPTS
    
    def test_all_are_extraction_prompts(self):
        for name, prompt in EXTRACTION_PROMPTS.items():
            assert isinstance(prompt, ExtractionPrompt)


@pytest.mark.skipif(not HAS_PROMPTS, reason="taxonomic_prompts not available")
class TestGetExtractionPrompt:
    """Test get_extraction_prompt function."""
    
    def test_get_domain(self):
        prompt = get_extraction_prompt("domain")
        assert prompt is not None
        assert prompt.target_type == "Domain"
    
    def test_get_idea(self):
        prompt = get_extraction_prompt("idea")
        assert prompt is not None
        assert prompt.target_type == "Idea"
    
    def test_get_invalid(self):
        with pytest.raises(ValueError):
            get_extraction_prompt("invalid")


@pytest.mark.skipif(not HAS_PROMPTS, reason="taxonomic_prompts not available")
class TestFormatPrompt:
    """Test format_prompt function."""
    
    def test_format_domain(self):
        system, user = format_prompt("domain", text="Sample text about AI")
        assert system is not None
        assert "Sample text about AI" in user
    
    def test_format_idea(self):
        system, user = format_prompt("idea", text="An idea about machine learning")
        assert system is not None
        assert "machine learning" in user


@pytest.mark.skipif(not HAS_PROMPTS, reason="taxonomic_prompts not available")
class TestPromptConstants:
    """Test prompt constants are defined."""
    
    def test_domain_system_not_empty(self):
        assert len(DOMAIN_EXTRACTION_SYSTEM) > 0
    
    def test_idea_system_not_empty(self):
        assert len(IDEA_EXTRACTION_SYSTEM) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
