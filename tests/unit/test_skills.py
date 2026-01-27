"""Unit tests for skills layer modules."""

import pytest
from pathlib import Path
import tempfile

from inception.skills.synthesizer import (
    SkillStep,
    Skill,
    SkillSynthesizer,
)


class TestSkillStep:
    """Tests for SkillStep dataclass."""
    
    def test_skill_step_creation(self):
        """Test creating a skill step."""
        step = SkillStep(
            action="click",
            description="Click the submit button",
        )
        
        assert step.action == "click"
        assert step.description == "Click the submit button"
        assert not step.optional
    
    def test_step_with_preconditions(self):
        """Test step with preconditions."""
        step = SkillStep(
            action="deploy",
            description="Deploy to production",
            preconditions=["Tests pass", "Approved by reviewer"],
            warnings=["This is irreversible"],
        )
        
        assert len(step.preconditions) == 2
        assert len(step.warnings) == 1
    
    def test_optional_step(self):
        """Test optional step."""
        step = SkillStep(
            action="cleanup",
            description="Clean up temporary files",
            optional=True,
            fallback="Skip if not needed",
        )
        
        assert step.optional
        assert step.fallback == "Skip if not needed"


class TestSkill:
    """Tests for Skill dataclass."""
    
    def test_skill_creation(self):
        """Test creating a skill."""
        skill = Skill(
            name="Deploy Application",
            description="Deploy the app to production",
        )
        
        assert skill.name == "Deploy Application"
        assert skill.description == "Deploy the app to production"
        assert skill.difficulty == "medium"
    
    def test_skill_with_steps(self):
        """Test skill with steps."""
        steps = [
            SkillStep(action="build", description="Build the app"),
            SkillStep(action="test", description="Run tests"),
            SkillStep(action="deploy", description="Deploy to server"),
        ]
        
        skill = Skill(
            name="Full Deploy",
            description="Complete deployment workflow",
            steps=steps,
        )
        
        assert len(skill.steps) == 3
    
    def test_skill_to_dict(self):
        """Test skill to dictionary conversion."""
        skill = Skill(
            name="Test Skill",
            description="A test skill",
            steps=[SkillStep(action="test", description="Run test")],
            tags=["testing"],
            difficulty="easy",
        )
        
        data = skill.to_dict()
        
        assert data["name"] == "Test Skill"
        assert data["difficulty"] == "easy"
        assert len(data["steps"]) == 1
    
    def test_skill_to_skill_md(self):
        """Test SKILL.md generation."""
        steps = [
            SkillStep(
                action="install",
                description="Install dependencies",
                preconditions=["Python 3.11+ installed"],
            ),
            SkillStep(
                action="configure",
                description="Configure settings",
                warnings=["Backup existing config first"],
            ),
        ]
        
        skill = Skill(
            name="Setup Project",
            description="Set up a new Python project",
            steps=steps,
            prerequisites=["Git installed", "Terminal access"],
            tags=["python", "setup"],
            difficulty="easy",
        )
        
        md = skill.to_skill_md()
        
        # Check frontmatter
        assert "---" in md
        assert "name: Setup Project" in md
        assert "difficulty: easy" in md
        
        # Check content
        assert "# Setup Project" in md
        assert "## Prerequisites" in md
        assert "- Git installed" in md
        assert "## Steps" in md
        assert "### Step 1: Install" in md
        assert "### Step 2: Configure" in md
        assert "⚠️ **Warning:**" in md


class TestSkillSynthesizerMethods:
    """Tests for SkillSynthesizer methods (without DB)."""
    
    def test_synthesizer_has_methods(self):
        """Test that synthesizer has expected methods."""
        assert hasattr(SkillSynthesizer, "synthesize_from_procedure")
        assert hasattr(SkillSynthesizer, "synthesize_from_source")
        assert hasattr(SkillSynthesizer, "synthesize_all")
        assert hasattr(SkillSynthesizer, "save_skill")
        assert hasattr(SkillSynthesizer, "validate_skill")
    
    def test_validate_skill(self):
        """Test skill validation."""
        from inception.skills import SkillSynthesizer
        
        # Create synthesizer without DB for validation testing
        synthesizer = SkillSynthesizer.__new__(SkillSynthesizer)
        synthesizer.db = None
        
        # Valid skill
        valid_skill = Skill(
            name="Valid Skill",
            description="A valid skill",
            steps=[SkillStep(action="test", description="Do something")],
        )
        
        is_valid, issues = synthesizer.validate_skill(valid_skill)
        assert is_valid
        assert len(issues) == 0
        
        # Invalid skill (no steps)
        invalid_skill = Skill(
            name="Invalid Skill",
            description="",
            steps=[],
        )
        
        is_valid, issues = synthesizer.validate_skill(invalid_skill)
        assert not is_valid
        assert len(issues) >= 2  # Missing description and steps
    
    def test_save_skill(self):
        """Test saving skill to file."""
        from inception.skills import SkillSynthesizer
        
        synthesizer = SkillSynthesizer.__new__(SkillSynthesizer)
        synthesizer.db = None
        
        skill = Skill(
            name="Test Skill",
            description="A test skill for saving",
            steps=[SkillStep(action="test", description="Test step")],
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            skill_path = synthesizer.save_skill(skill, output_dir)
            
            assert skill_path.exists()
            assert skill_path.suffix == ".md"
            
            content = skill_path.read_text()
            assert "Test Skill" in content
            assert "Test step" in content
    
    def test_skill_filename_slugify(self):
        """Test that skill names are properly slugified for filenames."""
        from inception.skills import SkillSynthesizer
        
        synthesizer = SkillSynthesizer.__new__(SkillSynthesizer)
        synthesizer.db = None
        
        skill = Skill(
            name="How to Deploy on AWS!",
            description="Deploy guide",
            steps=[SkillStep(action="deploy", description="Deploy")],
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            skill_path = synthesizer.save_skill(skill, output_dir)
            
            # Should be slugified
            assert skill_path.name == "how-to-deploy-on-aws.md"


class TestTagInference:
    """Tests for tag inference."""
    
    def test_infer_programming_tags(self):
        """Test inferring programming-related tags."""
        from inception.skills import SkillSynthesizer
        
        synthesizer = SkillSynthesizer.__new__(SkillSynthesizer)
        synthesizer.db = None
        
        tags = synthesizer._infer_tags(
            "Write Python Code",
            "How to write Python scripts for automation"
        )
        
        assert "programming" in tags
    
    def test_infer_devops_tags(self):
        """Test inferring devops-related tags."""
        from inception.skills import SkillSynthesizer
        
        synthesizer = SkillSynthesizer.__new__(SkillSynthesizer)
        synthesizer.db = None
        
        tags = synthesizer._infer_tags(
            "Deploy with Docker",
            "Set up CI/CD pipeline with Docker containers"
        )
        
        assert "devops" in tags


class TestDifficultyEstimation:
    """Tests for difficulty estimation."""
    
    def test_easy_difficulty(self):
        """Test easy difficulty (few steps)."""
        from inception.skills import SkillSynthesizer
        
        synthesizer = SkillSynthesizer.__new__(SkillSynthesizer)
        synthesizer.db = None
        
        steps = [
            SkillStep(action="click", description="Click"),
            SkillStep(action="type", description="Type"),
        ]
        
        difficulty = synthesizer._estimate_difficulty(steps)
        assert difficulty == "easy"
    
    def test_hard_difficulty(self):
        """Test hard difficulty (many steps)."""
        from inception.skills import SkillSynthesizer
        
        synthesizer = SkillSynthesizer.__new__(SkillSynthesizer)
        synthesizer.db = None
        
        steps = [SkillStep(action=f"step{i}", description=f"Step {i}") for i in range(10)]
        
        difficulty = synthesizer._estimate_difficulty(steps)
        assert difficulty == "hard"
