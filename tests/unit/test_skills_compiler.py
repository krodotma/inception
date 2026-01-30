"""
Unit tests for skills/compiler.py

Tests for skill compilation and execution:
- SkillCompiler: Compiles SKILL.md to executable pipelines
- SkillExecutor: Executes compiled skills
"""

import pytest
from inception.skills.compiler import (
    # Enums
    StepType,
    SkillStatus,
    # Data classes
    SkillStep,
    CompiledSkill,
    # Compiler and Executor
    SkillCompiler,
    SkillExecutor,
)


# =============================================================================
# Test: Enums
# =============================================================================

class TestStepType:
    """Tests for StepType enum."""
    
    def test_step_type_values(self):
        """Test step type values."""
        assert StepType.COMMAND.value == "command"
        assert StepType.PYTHON.value == "python"
        assert StepType.LLM.value == "llm"
        assert StepType.VALIDATE.value == "validate"


class TestSkillStatus:
    """Tests for SkillStatus enum."""
    
    def test_status_values(self):
        """Test skill status values."""
        assert SkillStatus.PENDING.value == "pending"
        assert SkillStatus.RUNNING.value == "running"
        assert SkillStatus.SUCCESS.value == "success"
        assert SkillStatus.FAILED.value == "failed"


# =============================================================================
# Test: SkillStep
# =============================================================================

class TestSkillStep:
    """Tests for SkillStep dataclass."""
    
    def test_creation(self):
        """Test creating a skill step."""
        step = SkillStep(
            step_id="step-001",
            step_type=StepType.PYTHON,
            name="Test Step",
        )
        
        assert step.step_id == "step-001"
        assert step.step_type == StepType.PYTHON
        assert step.status == SkillStatus.PENDING
    
    def test_with_code(self):
        """Test creating step with code."""
        step = SkillStep(
            step_id="step-002",
            step_type=StepType.PYTHON,
            name="Python Step",
            code="print('hello')",
        )
        
        assert step.code == "print('hello')"
    
    def test_with_command(self):
        """Test creating step with command."""
        step = SkillStep(
            step_id="step-003",
            step_type=StepType.COMMAND,
            name="Shell Step",
            command="echo hello",
        )
        
        assert step.command == "echo hello"


# =============================================================================
# Test: CompiledSkill
# =============================================================================

class TestCompiledSkill:
    """Tests for CompiledSkill dataclass."""
    
    def test_creation(self):
        """Test creating a compiled skill."""
        skill = CompiledSkill(
            skill_id="skill-001",
            name="Test Skill",
            description="A test skill",
            version="1.0.0",
        )
        
        assert skill.name == "Test Skill"
        assert len(skill.steps) == 0
    
    def test_with_steps(self):
        """Test creating skill with steps."""
        step = SkillStep(
            step_id="s1",
            step_type=StepType.PYTHON,
            name="Step 1",
        )
        skill = CompiledSkill(
            skill_id="skill-001",
            name="Test Skill",
            description="Test",
            version="1.0.0",
            steps=[step],
        )
        
        assert len(skill.steps) == 1
    
    def test_get_step(self):
        """Test getting step by ID."""
        step = SkillStep(
            step_id="s1",
            step_type=StepType.PYTHON,
            name="Step 1",
        )
        skill = CompiledSkill(
            skill_id="skill-001",
            name="Test",
            description="Test",
            version="1.0.0",
            steps=[step],
        )
        
        found = skill.get_step("s1")
        
        assert found is not None
        assert found.step_id == "s1"
    
    def test_get_step_not_found(self):
        """Test getting non-existent step."""
        skill = CompiledSkill(
            skill_id="skill-001",
            name="Test",
            description="Test",
            version="1.0.0",
        )
        
        found = skill.get_step("nonexistent")
        
        assert found is None


# =============================================================================
# Test: SkillCompiler
# =============================================================================

class TestSkillCompiler:
    """Tests for SkillCompiler."""
    
    def test_creation(self):
        """Test creating a compiler."""
        compiler = SkillCompiler()
        
        assert compiler is not None
    
    def test_compile_simple_skill(self):
        """Test compiling a simple skill."""
        compiler = SkillCompiler()
        
        skill_md = """---
name: Simple Skill
description: A simple test skill
version: 1.0.0
---

## Steps

### Step 1: Echo Hello

```python
print("Hello World")
```
"""
        skill = compiler.compile(skill_md)
        
        assert skill is not None
        assert skill.name == "Simple Skill"
    
    def test_compile_with_inputs(self):
        """Test compiling skill with inputs."""
        compiler = SkillCompiler()
        
        skill_md = """---
name: Input Skill
description: Skill with inputs
version: 1.0.0
---

## Inputs

- name: input_text
  type: string
  description: Input text

## Steps

### Step 1: Process

```python
result = input_text.upper()
```
"""
        skill = compiler.compile(skill_md)
        
        assert skill is not None
        assert skill.name == "Input Skill"


# =============================================================================
# Test: SkillExecutor
# =============================================================================

class TestSkillExecutor:
    """Tests for SkillExecutor."""
    
    def test_creation(self):
        """Test creating an executor."""
        executor = SkillExecutor()
        
        assert executor.dry_run is False
        assert executor.sandbox is True
    
    def test_creation_dry_run(self):
        """Test creating executor with dry_run."""
        executor = SkillExecutor(dry_run=True)
        
        assert executor.dry_run is True
    
    def test_execute_empty_skill(self):
        """Test executing skill with no steps."""
        executor = SkillExecutor(dry_run=True)
        
        skill = CompiledSkill(
            skill_id="skill-001",
            name="Empty Skill",
            description="No steps",
            version="1.0.0",
        )
        
        result = executor.execute(skill)
        
        assert result is not None
        assert "status" in result or isinstance(result, dict)
    
    def test_execute_with_inputs(self):
        """Test executing skill with inputs."""
        executor = SkillExecutor(dry_run=True)
        
        skill = CompiledSkill(
            skill_id="skill-001",
            name="Input Skill",
            description="With inputs",
            version="1.0.0",
        )
        
        result = executor.execute(skill, inputs={"text": "hello"})
        
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
