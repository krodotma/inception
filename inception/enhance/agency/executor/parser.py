"""
SKILL.md parser for execution engine.

Parses SKILL.md files into structured executable steps.
"""

from __future__ import annotations

import re
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SkillStep:
    """A single step in a skill."""
    
    index: int
    title: str
    description: str
    command: str | None = None       # Shell command to execute
    code: str | None = None          # Code block to run
    language: str | None = None      # Code language
    verification: str | None = None  # How to verify success
    warning: str | None = None       # Safety warning
    optional: bool = False
    preconditions: list[str] = field(default_factory=list)


@dataclass
class ParsedSkill:
    """A parsed SKILL.md file."""
    
    name: str
    description: str
    goal: str
    difficulty: str = "intermediate"
    time_estimate: str = ""
    tags: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    steps: list[SkillStep] = field(default_factory=list)
    safety_notes: list[str] = field(default_factory=list)
    source_path: str = ""
    
    def get_executable_steps(self) -> list[SkillStep]:
        """Get steps that can be executed (have command or code)."""
        return [
            step for step in self.steps
            if step.command or step.code
        ]


class SkillParser:
    """
    Parses SKILL.md files into structured format.
    
    Expected SKILL.md format:
    ```yaml
    ---
    name: Skill Name
    description: What this skill does
    difficulty: beginner/intermediate/advanced
    time_estimate: 30 minutes
    tags: [tag1, tag2]
    prerequisites: [prereq1, prereq2]
    ---
    
    # Goal
    What this skill accomplishes
    
    ## Step 1: Title
    Description of the step
    
    ```bash
    command to run
    ```
    
    **Verification**: How to check success
    
    ## Step 2: ...
    ```
    """
    
    def parse(self, path: Path | str) -> ParsedSkill:
        """
        Parse a SKILL.md file.
        
        Args:
            path: Path to SKILL.md file
        
        Returns:
            Parsed skill structure
        """
        path = Path(path)
        content = path.read_text()
        
        return self.parse_content(content, source_path=str(path))
    
    def parse_content(
        self,
        content: str,
        source_path: str = "",
    ) -> ParsedSkill:
        """
        Parse SKILL.md content directly.
        
        Args:
            content: SKILL.md content
            source_path: Optional source path for reference
        
        Returns:
            Parsed skill structure
        """
        # Extract frontmatter
        frontmatter, body = self._extract_frontmatter(content)
        
        # Parse frontmatter
        metadata = {}
        if frontmatter:
            try:
                metadata = yaml.safe_load(frontmatter) or {}
            except yaml.YAMLError:
                metadata = {}
        
        # Extract goal
        goal = self._extract_goal(body)
        
        # Parse steps
        steps = self._parse_steps(body)
        
        # Extract safety notes
        safety = self._extract_safety_notes(body)
        
        return ParsedSkill(
            name=metadata.get("name", "Untitled Skill"),
            description=metadata.get("description", ""),
            goal=goal,
            difficulty=metadata.get("difficulty", "intermediate"),
            time_estimate=metadata.get("time_estimate", ""),
            tags=metadata.get("tags", []),
            prerequisites=metadata.get("prerequisites", []),
            steps=steps,
            safety_notes=safety,
            source_path=source_path,
        )
    
    def _extract_frontmatter(self, content: str) -> tuple[str, str]:
        """Extract YAML frontmatter from content."""
        pattern = r"^---\s*\n(.*?)\n---\s*\n"
        match = re.match(pattern, content, re.DOTALL)
        
        if match:
            frontmatter = match.group(1)
            body = content[match.end():]
            return frontmatter, body
        
        return "", content
    
    def _extract_goal(self, body: str) -> str:
        """Extract goal section."""
        pattern = r"#\s*Goal\s*\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        return ""
    
    def _parse_steps(self, body: str) -> list[SkillStep]:
        """Parse step sections."""
        steps = []
        
        # Match ## Step N: Title or ## Step N
        pattern = r"##\s*Step\s*(\d+)[:\s]*([^\n]*)\n(.*?)(?=\n##\s*Step|\n#[^#]|\Z)"
        matches = re.findall(pattern, body, re.DOTALL | re.IGNORECASE)
        
        for index_str, title, content in matches:
            index = int(index_str)
            step = self._parse_step_content(index, title.strip(), content)
            steps.append(step)
        
        return steps
    
    def _parse_step_content(
        self,
        index: int,
        title: str,
        content: str,
    ) -> SkillStep:
        """Parse a single step's content."""
        # Extract code blocks
        code_pattern = r"```(\w+)?\n(.*?)```"
        code_matches = re.findall(code_pattern, content, re.DOTALL)
        
        command = None
        code = None
        language = None
        
        for lang, code_content in code_matches:
            lang = lang.lower() if lang else "bash"
            
            if lang in ("bash", "sh", "shell", "zsh"):
                command = code_content.strip()
            else:
                code = code_content.strip()
                language = lang
            
            break  # Take first code block
        
        # Extract verification
        verification = None
        verif_pattern = r"\*\*Verification\*\*:\s*([^\n]+)"
        verif_match = re.search(verif_pattern, content, re.IGNORECASE)
        if verif_match:
            verification = verif_match.group(1).strip()
        
        # Extract warning
        warning = None
        warn_pattern = r"(?:⚠️|Warning|CAUTION|NOTE)[:\s]*([^\n]+)"
        warn_match = re.search(warn_pattern, content, re.IGNORECASE)
        if warn_match:
            warning = warn_match.group(1).strip()
        
        # Check if optional
        optional = "optional" in title.lower() or "optional" in content.lower()
        
        # Get description (content without code blocks and special sections)
        description = re.sub(code_pattern, "", content)
        description = re.sub(verif_pattern, "", description, flags=re.IGNORECASE)
        description = description.strip()
        
        return SkillStep(
            index=index,
            title=title or f"Step {index}",
            description=description[:500],  # Limit length
            command=command,
            code=code,
            language=language,
            verification=verification,
            warning=warning,
            optional=optional,
        )
    
    def _extract_safety_notes(self, body: str) -> list[str]:
        """Extract safety notes from content."""
        notes = []
        
        # Match safety-related patterns
        patterns = [
            r"⚠️\s*([^\n]+)",
            r"\*\*Warning\*\*:\s*([^\n]+)",
            r"\*\*CAUTION\*\*:\s*([^\n]+)",
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, body, re.IGNORECASE):
                notes.append(match.group(1).strip())
        
        return notes
