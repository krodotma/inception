"""
Skill synthesis module.

Converts extracted procedures into executable skill definitions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from inception.db import InceptionDB, get_db
from inception.db.records import NodeRecord
from inception.db.keys import NodeKind


@dataclass
class SkillStep:
    """A single step in a skill."""
    
    action: str
    description: str
    
    # Parameters
    parameters: dict[str, Any] = field(default_factory=dict)
    
    # Conditions
    preconditions: list[str] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)
    
    # Warnings
    warnings: list[str] = field(default_factory=list)
    
    # Optional
    optional: bool = False
    fallback: str | None = None


@dataclass
class Skill:
    """A synthesized skill definition."""
    
    name: str
    description: str
    
    # Steps
    steps: list[SkillStep] = field(default_factory=list)
    
    # Prerequisites
    prerequisites: list[str] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)
    
    # Metadata
    source_nids: list[int] = field(default_factory=list)
    confidence: float = 1.0
    
    # Tags
    tags: list[str] = field(default_factory=list)
    difficulty: str = "medium"  # easy, medium, hard
    estimated_time: str | None = None
    
    def to_skill_md(self) -> str:
        """Generate SKILL.md content."""
        lines = []
        
        # Frontmatter
        lines.append("---")
        lines.append(f"name: {self.name}")
        lines.append(f"description: {self.description}")
        if self.tags:
            lines.append(f"tags: [{', '.join(self.tags)}]")
        lines.append(f"difficulty: {self.difficulty}")
        if self.estimated_time:
            lines.append(f"estimated_time: {self.estimated_time}")
        lines.append("---")
        lines.append("")
        
        # Description
        lines.append(f"# {self.name}")
        lines.append("")
        lines.append(self.description)
        lines.append("")
        
        # Prerequisites
        if self.prerequisites:
            lines.append("## Prerequisites")
            lines.append("")
            for prereq in self.prerequisites:
                lines.append(f"- {prereq}")
            lines.append("")
        
        # Required tools
        if self.required_tools:
            lines.append("## Required Tools")
            lines.append("")
            for tool in self.required_tools:
                lines.append(f"- {tool}")
            lines.append("")
        
        # Steps
        lines.append("## Steps")
        lines.append("")
        
        for i, step in enumerate(self.steps, 1):
            # Step header
            optional_marker = " (optional)" if step.optional else ""
            lines.append(f"### Step {i}: {step.action.title()}{optional_marker}")
            lines.append("")
            lines.append(step.description)
            lines.append("")
            
            # Preconditions
            if step.preconditions:
                lines.append("**Before:**")
                for pre in step.preconditions:
                    lines.append(f"- {pre}")
                lines.append("")
            
            # Parameters
            if step.parameters:
                lines.append("**Parameters:**")
                for param, value in step.parameters.items():
                    lines.append(f"- `{param}`: {value}")
                lines.append("")
            
            # Warnings
            if step.warnings:
                for warning in step.warnings:
                    lines.append(f"> ⚠️ **Warning:** {warning}")
                lines.append("")
            
            # Fallback
            if step.fallback:
                lines.append(f"**Fallback:** {step.fallback}")
                lines.append("")
            
            # Postconditions
            if step.postconditions:
                lines.append("**After:**")
                for post in step.postconditions:
                    lines.append(f"- {post}")
                lines.append("")
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "steps": [
                {
                    "action": s.action,
                    "description": s.description,
                    "parameters": s.parameters,
                    "preconditions": s.preconditions,
                    "postconditions": s.postconditions,
                    "warnings": s.warnings,
                    "optional": s.optional,
                    "fallback": s.fallback,
                }
                for s in self.steps
            ],
            "prerequisites": self.prerequisites,
            "required_tools": self.required_tools,
            "tags": self.tags,
            "difficulty": self.difficulty,
            "estimated_time": self.estimated_time,
            "confidence": self.confidence,
        }


class SkillSynthesizer:
    """
    Synthesizer for converting procedures to skills.
    """
    
    def __init__(self, db: InceptionDB | None = None):
        """
        Initialize the synthesizer.
        
        Args:
            db: Database instance
        """
        self.db = db or get_db()
    
    def synthesize_from_procedure(
        self,
        procedure_node: NodeRecord,
    ) -> Skill:
        """
        Synthesize a skill from a procedure node.
        
        Args:
            procedure_node: Procedure node record
        
        Returns:
            Synthesized Skill
        """
        payload = procedure_node.payload
        
        # Extract basic info
        name = payload.get("title", "Untitled Skill")
        description = payload.get("goal", "")
        
        # Convert steps
        steps = []
        for step_data in payload.get("steps", []):
            step = SkillStep(
                action=step_data.get("action_verb", "execute"),
                description=step_data.get("text", ""),
                warnings=step_data.get("warnings", []),
            )
            steps.append(step)
        
        # Extract prerequisites
        prerequisites = payload.get("prerequisites", [])
        
        # Infer tags from name and description
        tags = self._infer_tags(name, description)
        
        # Estimate difficulty
        difficulty = self._estimate_difficulty(steps)
        
        skill = Skill(
            name=name,
            description=description,
            steps=steps,
            prerequisites=prerequisites,
            source_nids=[procedure_node.nid],
            confidence=procedure_node.confidence.combined,
            tags=tags,
            difficulty=difficulty,
        )
        
        return skill
    
    def synthesize_from_source(
        self,
        source_nid: int,
    ) -> list[Skill]:
        """
        Synthesize all skills from procedures in a source.
        
        Args:
            source_nid: Source NID
        
        Returns:
            List of synthesized skills
        """
        skills = []
        
        for node in self.db.iter_nodes():
            if node.kind != NodeKind.PROCEDURE:
                continue
            
            if source_nid not in (node.source_nids or []):
                continue
            
            skill = self.synthesize_from_procedure(node)
            skills.append(skill)
        
        return skills
    
    def synthesize_all(self) -> list[Skill]:
        """
        Synthesize all skills from all procedures.
        
        Returns:
            List of all synthesized skills
        """
        skills = []
        
        for node in self.db.iter_nodes():
            if node.kind != NodeKind.PROCEDURE:
                continue
            
            skill = self.synthesize_from_procedure(node)
            skills.append(skill)
        
        return skills
    
    def _infer_tags(self, name: str, description: str) -> list[str]:
        """Infer tags from name and description."""
        tags = []
        text = f"{name} {description}".lower()
        
        # Domain tags
        domain_keywords = {
            "programming": ["code", "program", "script", "python", "javascript"],
            "devops": ["deploy", "docker", "kubernetes", "ci", "cd", "pipeline"],
            "database": ["sql", "database", "query", "table", "schema"],
            "web": ["html", "css", "website", "frontend", "backend", "api"],
            "system": ["install", "configure", "setup", "terminal", "command"],
            "testing": ["test", "debug", "verify", "check", "validate"],
        }
        
        for tag, keywords in domain_keywords.items():
            if any(kw in text for kw in keywords):
                tags.append(tag)
        
        return tags[:5]  # Limit tags
    
    def _estimate_difficulty(self, steps: list[SkillStep]) -> str:
        """Estimate difficulty based on steps."""
        step_count = len(steps)
        
        if step_count <= 3:
            return "easy"
        elif step_count <= 7:
            return "medium"
        else:
            return "hard"
    
    def save_skill(
        self,
        skill: Skill,
        output_dir: Path,
        filename: str | None = None,
    ) -> Path:
        """
        Save skill to SKILL.md file.
        
        Args:
            skill: Skill to save
            output_dir: Output directory
            filename: Optional filename (default: skill name slugified)
        
        Returns:
            Path to saved file
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if filename is None:
            # Slugify name
            slug = re.sub(r"[^a-z0-9]+", "-", skill.name.lower()).strip("-")
            filename = f"{slug}.md"
        
        skill_path = output_dir / filename
        
        with open(skill_path, "w") as f:
            f.write(skill.to_skill_md())
        
        return skill_path
    
    def validate_skill(self, skill: Skill) -> tuple[bool, list[str]]:
        """
        Validate a skill definition.
        
        Args:
            skill: Skill to validate
        
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        
        # Check required fields
        if not skill.name:
            issues.append("Skill must have a name")
        
        if not skill.description:
            issues.append("Skill should have a description")
        
        if not skill.steps:
            issues.append("Skill must have at least one step")
        
        # Check steps
        for i, step in enumerate(skill.steps):
            if not step.description:
                issues.append(f"Step {i+1} should have a description")
            
            if not step.action:
                issues.append(f"Step {i+1} should have an action")
        
        return len(issues) == 0, issues


def synthesize_skills(source_nid: int | None = None) -> list[Skill]:
    """
    Convenience function to synthesize skills.
    
    Args:
        source_nid: Optional source to filter by
    
    Returns:
        List of synthesized skills
    """
    synthesizer = SkillSynthesizer()
    
    if source_nid:
        return synthesizer.synthesize_from_source(source_nid)
    else:
        return synthesizer.synthesize_all()


def save_skill_md(skill: Skill, output_dir: Path) -> Path:
    """
    Convenience function to save skill to file.
    
    Args:
        skill: Skill to save
        output_dir: Output directory
    
    Returns:
        Path to saved file
    """
    synthesizer = SkillSynthesizer()
    return synthesizer.save_skill(skill, output_dir)
