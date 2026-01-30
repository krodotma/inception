"""
Skill Compiler - Swarm Track 6

Compiles skill definitions into executable pipelines.
Transforms SKILL.md declarative specs into Python workflows.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


class StepType(Enum):
    """Types of skill steps."""
    COMMAND = "command"       # Shell command
    PYTHON = "python"         # Python code
    LLM = "llm"               # LLM invocation
    API = "api"               # API call
    TRANSFORM = "transform"   # Data transformation
    VALIDATE = "validate"     # Validation check
    CONDITIONAL = "conditional"  # Branching logic


class SkillStatus(Enum):
    """Skill execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class SkillStep:
    """A single step in a skill."""
    step_id: str
    step_type: StepType
    name: str
    description: str = ""
    
    # Content
    code: str = ""
    command: str = ""
    prompt: str = ""
    
    # Dependencies
    requires: list[str] = field(default_factory=list)
    produces: list[str] = field(default_factory=list)
    
    # Execution
    timeout_seconds: int = 300
    retries: int = 0
    condition: str | None = None
    
    # Runtime
    status: SkillStatus = SkillStatus.PENDING
    result: Any = None
    error: str | None = None


@dataclass
class CompiledSkill:
    """A compiled skill ready for execution."""
    skill_id: str
    name: str
    description: str
    version: str
    
    # Steps in execution order
    steps: list[SkillStep] = field(default_factory=list)
    
    # Inputs/outputs
    inputs: list[dict] = field(default_factory=list)
    outputs: list[dict] = field(default_factory=list)
    
    # Metadata
    source_path: str = ""
    compiled_at: str = ""
    
    def get_step(self, step_id: str) -> SkillStep | None:
        """Get step by ID."""
        return next((s for s in self.steps if s.step_id == step_id), None)


class SkillCompiler:
    """
    Compiles SKILL.md files into executable pipelines.
    """
    
    def __init__(self):
        self._compiled_cache: dict[str, CompiledSkill] = {}
    
    def compile(self, source: str | Path) -> CompiledSkill:
        """
        Compile a skill from source.
        
        Args:
            source: SKILL.md path or content string
        
        Returns:
            CompiledSkill ready for execution
        """
        if isinstance(source, Path) or (
            isinstance(source, str) and source.endswith(".md")
        ):
            path = Path(source)
            content = path.read_text()
            source_path = str(path)
        else:
            content = source
            source_path = ""
        
        # Check cache
        cache_key = hashlib.md5(content.encode()).hexdigest()
        if cache_key in self._compiled_cache:
            return self._compiled_cache[cache_key]
        
        # Parse skill
        skill = self._parse_skill(content, source_path)
        
        # Validate
        self._validate_skill(skill)
        
        # Cache
        self._compiled_cache[cache_key] = skill
        
        return skill
    
    def _parse_skill(self, content: str, source_path: str) -> CompiledSkill:
        """Parse skill from markdown content."""
        lines = content.split("\n")
        
        # Extract frontmatter
        name, description, version = self._parse_frontmatter(lines)
        
        # Extract steps
        steps = self._parse_steps(lines)
        
        # Extract inputs/outputs
        inputs = self._parse_ios(lines, "input")
        outputs = self._parse_ios(lines, "output")
        
        skill_id = hashlib.md5(name.encode()).hexdigest()[:12]
        
        return CompiledSkill(
            skill_id=skill_id,
            name=name,
            description=description,
            version=version,
            steps=steps,
            inputs=inputs,
            outputs=outputs,
            source_path=source_path,
        )
    
    def _parse_frontmatter(self, lines: list[str]) -> tuple[str, str, str]:
        """Parse YAML frontmatter."""
        in_frontmatter = False
        name = "unnamed"
        description = ""
        version = "1.0.0"
        
        for line in lines:
            if line.strip() == "---":
                if in_frontmatter:
                    break
                in_frontmatter = True
                continue
            
            if in_frontmatter:
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip().strip('"\'')
                elif line.startswith("description:"):
                    description = line.split(":", 1)[1].strip().strip('"\'')
                elif line.startswith("version:"):
                    version = line.split(":", 1)[1].strip().strip('"\'')
        
        return name, description, version
    
    def _parse_steps(self, lines: list[str]) -> list[SkillStep]:
        """Parse execution steps."""
        steps = []
        step_idx = 0
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for step heading
            step_match = re.match(r"^#{2,3}\s+(?:Step\s+)?(\d+)[.:]\s*(.+)", line)
            if step_match:
                step_num = step_match.group(1)
                step_name = step_match.group(2).strip()
                step_idx += 1
                
                # Collect step content
                content_lines = []
                i += 1
                while i < len(lines) and not re.match(r"^#{1,3}\s+", lines[i]):
                    content_lines.append(lines[i])
                    i += 1
                
                step = self._parse_step_content(
                    step_id=f"step_{step_num}",
                    name=step_name,
                    content="\n".join(content_lines),
                )
                steps.append(step)
                continue
            
            i += 1
        
        return steps
    
    def _parse_step_content(
        self,
        step_id: str,
        name: str,
        content: str,
    ) -> SkillStep:
        """Parse step content into SkillStep."""
        step_type = StepType.COMMAND
        code = ""
        command = ""
        prompt = ""
        description = ""
        
        # Find code blocks
        code_match = re.search(r"```(\w*)\n(.*?)```", content, re.DOTALL)
        if code_match:
            lang = code_match.group(1).lower()
            code_content = code_match.group(2).strip()
            
            if lang in ("python", "py"):
                step_type = StepType.PYTHON
                code = code_content
            elif lang in ("bash", "sh", "shell", ""):
                step_type = StepType.COMMAND
                command = code_content
            else:
                code = code_content
        
        # Check for LLM step
        if re.search(r"(prompt|ask|generate|llm)", name, re.I):
            step_type = StepType.LLM
            # Extract prompt from content
            prompt_lines = [l for l in content.split("\n") 
                          if l.strip() and not l.startswith("```")]
            prompt = "\n".join(prompt_lines)
        
        # Extract description (first paragraph)
        for line in content.split("\n"):
            if line.strip() and not line.startswith("```"):
                description = line.strip()
                break
        
        return SkillStep(
            step_id=step_id,
            step_type=step_type,
            name=name,
            description=description,
            code=code,
            command=command,
            prompt=prompt,
        )
    
    def _parse_ios(self, lines: list[str], io_type: str) -> list[dict]:
        """Parse inputs or outputs."""
        ios = []
        in_section = False
        
        for line in lines:
            # Check for section header
            if re.match(rf"^#{2,3}\s+{io_type}s?", line, re.I):
                in_section = True
                continue
            
            # End section on next header
            if in_section and re.match(r"^#{1,3}\s+", line):
                break
            
            # Parse list items
            if in_section:
                item_match = re.match(r"^\s*-\s+`?(\w+)`?\s*[:-]\s*(.+)", line)
                if item_match:
                    ios.append({
                        "name": item_match.group(1),
                        "description": item_match.group(2),
                    })
        
        return ios
    
    def _validate_skill(self, skill: CompiledSkill) -> None:
        """Validate compiled skill."""
        if not skill.name:
            raise ValueError("Skill must have a name")
        
        if not skill.steps:
            logger.warning(f"Skill {skill.name} has no steps")
        
        # Check for duplicate step IDs
        step_ids = [s.step_id for s in skill.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("Duplicate step IDs found")


class SkillExecutor:
    """
    Execute compiled skills.
    """
    
    def __init__(
        self,
        dry_run: bool = False,
        sandbox: bool = True,
    ):
        self.dry_run = dry_run
        self.sandbox = sandbox
        self._context: dict[str, Any] = {}
    
    def execute(
        self,
        skill: CompiledSkill,
        inputs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a compiled skill.
        
        Args:
            skill: Compiled skill
            inputs: Input values
        
        Returns:
            Execution result with outputs
        """
        self._context = dict(inputs or {})
        results = {}
        
        for step in skill.steps:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would execute: {step.name}")
                step.status = SkillStatus.SKIPPED
                continue
            
            try:
                step.status = SkillStatus.RUNNING
                result = self._execute_step(step)
                step.result = result
                step.status = SkillStatus.SUCCESS
                
                # Store in context for next steps
                for output in step.produces:
                    self._context[output] = result
                
                results[step.step_id] = result
                
            except Exception as e:
                step.status = SkillStatus.FAILED
                step.error = str(e)
                logger.error(f"Step {step.name} failed: {e}")
                
                if step.retries > 0:
                    # Retry logic would go here
                    pass
                else:
                    raise
        
        return {
            "success": all(s.status == SkillStatus.SUCCESS for s in skill.steps),
            "results": results,
            "context": self._context,
        }
    
    def _execute_step(self, step: SkillStep) -> Any:
        """Execute a single step."""
        if step.step_type == StepType.PYTHON:
            return self._execute_python(step)
        elif step.step_type == StepType.COMMAND:
            return self._execute_command(step)
        elif step.step_type == StepType.LLM:
            return self._execute_llm(step)
        else:
            logger.warning(f"Unknown step type: {step.step_type}")
            return None
    
    def _execute_python(self, step: SkillStep) -> Any:
        """Execute Python code step."""
        if not step.code:
            return None
        
        # Create execution namespace
        namespace = {"__context__": self._context}
        exec(step.code, namespace)
        
        return namespace.get("result", None)
    
    def _execute_command(self, step: SkillStep) -> str:
        """Execute shell command step."""
        if not step.command:
            return ""
        
        import subprocess
        
        result = subprocess.run(
            step.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=step.timeout_seconds,
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Command failed: {result.stderr}")
        
        return result.stdout
    
    def _execute_llm(self, step: SkillStep) -> str:
        """Execute LLM step (placeholder)."""
        logger.info(f"LLM step: {step.prompt[:100]}...")
        return f"[LLM would process: {step.prompt[:50]}...]"
