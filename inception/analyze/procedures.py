"""
Procedure extraction module.

Extracts step-by-step procedures and how-to instructions
from text content.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import spacy

from inception.db.keys import NodeKind
from inception.db.records import Confidence


@dataclass
class ProcedureStep:
    """A single step in a procedure."""
    
    index: int
    text: str
    
    # Parsed components
    action_verb: str | None = None
    object: str | None = None
    conditions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    # Dependencies
    depends_on: list[int] = field(default_factory=list)  # Step indices
    
    # Source
    start_char: int = 0
    end_char: int = 0
    source_span_nid: int | None = None
    
    # Confidence
    confidence: float = 1.0


@dataclass
class Procedure:
    """A complete procedure extracted from text."""
    
    title: str | None = None
    goal: str | None = None
    
    steps: list[ProcedureStep] = field(default_factory=list)
    
    # Prerequisites
    prerequisites: list[str] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)
    
    # Metadata
    estimated_time: str | None = None
    difficulty: str | None = None
    
    # Source
    start_char: int = 0
    end_char: int = 0
    source_span_nid: int | None = None
    
    # Confidence
    confidence: Confidence = field(default_factory=Confidence)
    
    @property
    def kind(self) -> NodeKind:
        return NodeKind.PROCEDURE
    
    @property
    def step_count(self) -> int:
        return len(self.steps)
    
    def to_markdown(self) -> str:
        """Convert procedure to markdown format."""
        lines = []
        
        if self.title:
            lines.append(f"## {self.title}")
        
        if self.goal:
            lines.append(f"\n**Goal:** {self.goal}")
        
        if self.prerequisites:
            lines.append("\n**Prerequisites:**")
            for prereq in self.prerequisites:
                lines.append(f"- {prereq}")
        
        if self.required_tools:
            lines.append("\n**Required Tools:**")
            for tool in self.required_tools:
                lines.append(f"- {tool}")
        
        if self.steps:
            lines.append("\n**Steps:**")
            for step in self.steps:
                lines.append(f"{step.index + 1}. {step.text}")
                for warning in step.warnings:
                    lines.append(f"   ⚠️ {warning}")
        
        return "\n".join(lines)


@dataclass
class ProcedureExtractionResult:
    """Result of procedure extraction."""
    
    procedures: list[Procedure] = field(default_factory=list)
    
    # Statistics
    total_steps: int = 0
    
    @property
    def procedure_count(self) -> int:
        return len(self.procedures)


# Patterns for detecting procedure indicators
STEP_PATTERNS = [
    r"^\s*(?:step\s+)?(\d+)[.):]\s*(.+)",  # "1. Do this" or "Step 1: Do this"
    r"^\s*[-•*]\s*(.+)",  # Bullet points
    r"^\s*(?:first|second|third|then|next|finally)[,:]?\s*(.+)",  # Ordinal markers
]

PROCEDURE_INDICATORS = [
    "how to", "steps to", "guide to", "tutorial",
    "instructions", "procedure", "process",
    "follow these steps", "here's how",
]

ACTION_VERBS = {
    "click", "tap", "select", "choose", "open", "close",
    "create", "delete", "add", "remove", "insert",
    "install", "download", "upload", "configure", "setup",
    "enter", "type", "input", "submit", "save",
    "navigate", "go", "visit", "access",
    "run", "execute", "start", "stop", "restart",
    "copy", "paste", "move", "rename", "find",
    "enable", "disable", "turn on", "turn off",
    "connect", "disconnect", "attach", "detach",
}


class ProcedureExtractor:
    """
    Procedure extractor from text.
    
    Identifies and parses step-by-step instructions.
    """
    
    def __init__(
        self,
        model_name: str = "en_core_web_sm",
    ):
        """
        Initialize the extractor.
        
        Args:
            model_name: spaCy model name
        """
        self.model_name = model_name
        self._nlp = None
    
    def _get_nlp(self):
        """Lazy-load spaCy model."""
        if self._nlp is None:
            self._nlp = spacy.load(self.model_name)
        return self._nlp
    
    def extract(self, text: str) -> ProcedureExtractionResult:
        """
        Extract procedures from text.
        
        Args:
            text: Input text
        
        Returns:
            ProcedureExtractionResult with extracted procedures
        """
        nlp = self._get_nlp()
        
        procedures = []
        
        # Check if text contains procedure indicators
        text_lower = text.lower()
        has_procedure_indicator = any(
            ind in text_lower for ind in PROCEDURE_INDICATORS
        )
        
        # Try to extract numbered steps
        steps = self._extract_numbered_steps(text)
        
        if steps:
            # Create a procedure from the steps
            procedure = Procedure(
                steps=steps,
                start_char=steps[0].start_char if steps else 0,
                end_char=steps[-1].end_char if steps else len(text),
            )
            
            # Try to extract title (first line before steps)
            title = self._extract_title(text, steps[0].start_char if steps else 0)
            if title:
                procedure.title = title
            
            # Extract prerequisites
            procedure.prerequisites = self._extract_prerequisites(text)
            
            procedures.append(procedure)
        
        elif has_procedure_indicator:
            # Try to extract imperative sentences as steps
            doc = nlp(text)
            steps = self._extract_imperative_steps(doc)
            
            if steps:
                procedure = Procedure(
                    steps=steps,
                    start_char=0,
                    end_char=len(text),
                )
                procedures.append(procedure)
        
        total_steps = sum(p.step_count for p in procedures)
        
        return ProcedureExtractionResult(
            procedures=procedures,
            total_steps=total_steps,
        )
    
    def _extract_numbered_steps(self, text: str) -> list[ProcedureStep]:
        """Extract numbered or bulleted steps."""
        steps = []
        lines = text.split("\n")
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check for numbered steps
            match = re.match(r"^\s*(?:step\s+)?(\d+)[.):]\s*(.+)", line, re.IGNORECASE)
            if match:
                step_num = int(match.group(1)) - 1
                step_text = match.group(2)
                
                step = ProcedureStep(
                    index=len(steps),
                    text=step_text,
                    action_verb=self._extract_action_verb(step_text),
                )
                steps.append(step)
                continue
            
            # Check for bullet points (only if we already have numbered steps or strong indicators)
            if steps:  # Only append bullets if we have context
                bullet_match = re.match(r"^\s*[-•*]\s*(.+)", line)
                if bullet_match:
                    step_text = bullet_match.group(1)
                    step = ProcedureStep(
                        index=len(steps),
                        text=step_text,
                        action_verb=self._extract_action_verb(step_text),
                    )
                    steps.append(step)
        
        return steps
    
    def _extract_imperative_steps(self, doc) -> list[ProcedureStep]:
        """Extract steps from imperative sentences."""
        steps = []
        
        for sent in doc.sents:
            # Check if sentence starts with a verb (imperative)
            first_token = next(
                (t for t in sent if not t.is_punct and not t.is_space),
                None
            )
            
            if first_token and first_token.pos_ == "VERB":
                if first_token.text.lower() in ACTION_VERBS:
                    step = ProcedureStep(
                        index=len(steps),
                        text=sent.text.strip(),
                        action_verb=first_token.text,
                        start_char=sent.start_char,
                        end_char=sent.end_char,
                    )
                    steps.append(step)
        
        return steps
    
    def _extract_action_verb(self, text: str) -> str | None:
        """Extract the primary action verb from step text."""
        nlp = self._get_nlp()
        doc = nlp(text)
        
        for token in doc:
            if token.pos_ == "VERB" and token.text.lower() in ACTION_VERBS:
                return token.text.lower()
            if token.pos_ == "VERB":
                return token.text.lower()
        
        return None
    
    def _extract_title(self, text: str, first_step_char: int) -> str | None:
        """Extract procedure title from text before first step."""
        if first_step_char <= 0:
            return None
        
        prefix = text[:first_step_char].strip()
        lines = prefix.split("\n")
        
        # Take last non-empty line as title
        for line in reversed(lines):
            line = line.strip()
            if line:
                # Remove common prefixes
                for indicator in ["how to", "steps to", "guide to"]:
                    if line.lower().startswith(indicator):
                        return line
                return line
        
        return None
    
    def _extract_prerequisites(self, text: str) -> list[str]:
        """Extract prerequisites section."""
        prereqs = []
        
        # Look for prerequisites section
        patterns = [
            r"prerequisites?[:\s]+(.+?)(?=\n\n|steps?|$)",
            r"before you begin[:\s]+(.+?)(?=\n\n|steps?|$)",
            r"requirements?[:\s]+(.+?)(?=\n\n|steps?|$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                prereq_text = match.group(1)
                # Split by bullets or newlines
                items = re.split(r"[•\-*]\s*|\n", prereq_text)
                prereqs.extend(item.strip() for item in items if item.strip())
                break
        
        return prereqs


def extract_procedures(text: str) -> ProcedureExtractionResult:
    """
    Convenience function to extract procedures from text.
    
    Args:
        text: Input text
    
    Returns:
        ProcedureExtractionResult
    """
    extractor = ProcedureExtractor()
    return extractor.extract(text)


def procedure_to_skill(procedure: Procedure) -> dict[str, Any]:
    """
    Convert a procedure to a skill format.
    
    This generates a structure suitable for the skills layer.
    
    Args:
        procedure: Procedure to convert
    
    Returns:
        Skill dictionary with YAML-compatible structure
    """
    skill = {
        "name": procedure.title or "Untitled Procedure",
        "description": procedure.goal or "",
        "prerequisites": procedure.prerequisites,
        "steps": [],
    }
    
    for step in procedure.steps:
        skill_step = {
            "action": step.action_verb or "execute",
            "description": step.text,
            "conditions": step.conditions,
            "warnings": step.warnings,
        }
        skill["steps"].append(skill_step)
    
    return skill
