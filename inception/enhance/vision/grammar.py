"""
Visual Grammar Analysis - Swarm Track 1

Advanced visual program understanding using grammar-based decomposition.
Goes beyond VLM descriptions to extract structured program representations.

Features:
- Visual token extraction (UI elements, code blocks, diagram nodes)
- Grammar-based structure parsing
- Hierarchical decomposition
- Cross-reference linking
- Layout semantics
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Visual Token Types
# =============================================================================

class VisualTokenType(Enum):
    """Types of visual tokens in images."""
    # UI Elements
    BUTTON = "button"
    INPUT = "input"
    LABEL = "label"
    MENU = "menu"
    PANEL = "panel"
    ICON = "icon"
    
    # Code Elements
    FUNCTION = "function"
    CLASS = "class"
    VARIABLE = "variable"
    IMPORT = "import"
    COMMENT = "comment"
    DECORATOR = "decorator"
    
    # Diagram Elements
    NODE = "node"
    EDGE = "edge"
    ARROW = "arrow"
    CONTAINER = "container"
    SWIMLANE = "swimlane"
    
    # Chart Elements
    AXIS = "axis"
    BAR = "bar"
    LINE = "line"
    POINT = "point"
    LEGEND = "legend"
    
    # Document Elements
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    FIGURE = "figure"
    
    # Generic
    TEXT = "text"
    REGION = "region"
    UNKNOWN = "unknown"


@dataclass
class VisualToken:
    """A single visual token extracted from an image."""
    id: str
    token_type: VisualTokenType
    text: str | None = None
    
    # Bounding box (relative coordinates 0-1)
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    
    # Hierarchy
    parent_id: str | None = None
    children_ids: list[str] = field(default_factory=list)
    
    # Relationships
    connects_to: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    
    # Metadata
    confidence: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.token_type.value,
            "text": self.text,
            "bounds": {"x": self.x, "y": self.y, "w": self.width, "h": self.height},
            "parent": self.parent_id,
            "children": self.children_ids,
            "connects_to": self.connects_to,
            "confidence": self.confidence,
        }


# =============================================================================
# Grammar Rules
# =============================================================================

@dataclass
class GrammarRule:
    """A rule in the visual grammar."""
    name: str
    pattern: str  # Regex or structural pattern
    produces: VisualTokenType
    child_types: list[VisualTokenType] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)


class VisualGrammar:
    """Grammar definitions for visual content parsing."""
    
    # UI Grammar Rules
    UI_RULES = [
        GrammarRule(
            name="form",
            pattern="input+ button",
            produces=VisualTokenType.PANEL,
            child_types=[VisualTokenType.INPUT, VisualTokenType.BUTTON],
        ),
        GrammarRule(
            name="nav_menu",
            pattern="menu_item+",
            produces=VisualTokenType.MENU,
            child_types=[VisualTokenType.BUTTON, VisualTokenType.LABEL],
        ),
        GrammarRule(
            name="modal",
            pattern="heading content button+",
            produces=VisualTokenType.PANEL,
            child_types=[VisualTokenType.HEADING, VisualTokenType.PARAGRAPH],
        ),
    ]
    
    # Code Grammar Rules
    CODE_RULES = [
        GrammarRule(
            name="function_def",
            pattern=r"(def|function|fn)\s+\w+\s*\(",
            produces=VisualTokenType.FUNCTION,
        ),
        GrammarRule(
            name="class_def",
            pattern=r"(class|interface|struct)\s+\w+",
            produces=VisualTokenType.CLASS,
        ),
        GrammarRule(
            name="import_stmt",
            pattern=r"(import|from|require|use)\s+",
            produces=VisualTokenType.IMPORT,
        ),
        GrammarRule(
            name="decorator",
            pattern=r"@\w+",
            produces=VisualTokenType.DECORATOR,
        ),
    ]
    
    # Diagram Grammar Rules
    DIAGRAM_RULES = [
        GrammarRule(
            name="flow_node",
            pattern="rectangle|circle|diamond",
            produces=VisualTokenType.NODE,
        ),
        GrammarRule(
            name="connection",
            pattern="node arrow node",
            produces=VisualTokenType.EDGE,
        ),
        GrammarRule(
            name="container",
            pattern="node+",
            produces=VisualTokenType.CONTAINER,
        ),
    ]
    
    @classmethod
    def get_rules_for_content_type(cls, content_type: str) -> list[GrammarRule]:
        """Get grammar rules for a content type."""
        if content_type == "ui":
            return cls.UI_RULES
        elif content_type == "code":
            return cls.CODE_RULES
        elif content_type == "diagram":
            return cls.DIAGRAM_RULES
        else:
            return cls.UI_RULES + cls.CODE_RULES + cls.DIAGRAM_RULES


# =============================================================================
# Visual Parser
# =============================================================================

@dataclass
class ParseResult:
    """Result of parsing visual content."""
    tokens: list[VisualToken]
    structure: dict[str, Any]
    content_type: str
    grammar_matches: list[str]
    confidence: float = 1.0
    
    def get_root_tokens(self) -> list[VisualToken]:
        """Get tokens without parents."""
        return [t for t in self.tokens if t.parent_id is None]
    
    def get_children(self, token_id: str) -> list[VisualToken]:
        """Get children of a token."""
        return [t for t in self.tokens if t.parent_id == token_id]
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "content_type": self.content_type,
            "token_count": len(self.tokens),
            "tokens": [t.to_dict() for t in self.tokens],
            "structure": self.structure,
            "grammar_matches": self.grammar_matches,
            "confidence": self.confidence,
        }


class VisualParser:
    """
    Parser for visual content using grammar-based decomposition.
    
    Extracts structured program representations from visual content
    by applying visual grammars.
    """
    
    def __init__(self):
        self._token_counter = 0
    
    def _next_token_id(self) -> str:
        """Generate next token ID."""
        self._token_counter += 1
        return f"vt_{self._token_counter}"
    
    def parse(
        self,
        vlm_description: str,
        content_type: str = "unknown",
        image_analysis: dict | None = None,
    ) -> ParseResult:
        """
        Parse visual content from VLM description.
        
        Args:
            vlm_description: Description from VLM
            content_type: Type of visual content
            image_analysis: Optional structured image analysis
        
        Returns:
            ParseResult with extracted tokens and structure
        """
        tokens = []
        grammar_matches = []
        
        # Get applicable rules
        rules = VisualGrammar.get_rules_for_content_type(content_type)
        
        # Extract tokens based on content type
        if content_type == "code":
            tokens, matches = self._parse_code(vlm_description, rules)
            grammar_matches.extend(matches)
        elif content_type == "ui":
            tokens, matches = self._parse_ui(vlm_description, rules)
            grammar_matches.extend(matches)
        elif content_type == "diagram":
            tokens, matches = self._parse_diagram(vlm_description, rules)
            grammar_matches.extend(matches)
        else:
            tokens = self._parse_generic(vlm_description)
        
        # Build structure
        structure = self._build_structure(tokens)
        
        return ParseResult(
            tokens=tokens,
            structure=structure,
            content_type=content_type,
            grammar_matches=grammar_matches,
            confidence=self._compute_confidence(tokens, grammar_matches),
        )
    
    def _parse_code(
        self,
        description: str,
        rules: list[GrammarRule],
    ) -> tuple[list[VisualToken], list[str]]:
        """Parse code content."""
        tokens = []
        matches = []
        
        lines = description.split("\n")
        
        for line in lines:
            for rule in rules:
                if re.search(rule.pattern, line, re.IGNORECASE):
                    matches.append(rule.name)
                    token = VisualToken(
                        id=self._next_token_id(),
                        token_type=rule.produces,
                        text=line.strip()[:100],
                        confidence=0.8,
                    )
                    tokens.append(token)
                    break
            else:
                # Generic text line
                if line.strip():
                    tokens.append(VisualToken(
                        id=self._next_token_id(),
                        token_type=VisualTokenType.TEXT,
                        text=line.strip()[:100],
                        confidence=0.5,
                    ))
        
        return tokens, matches
    
    def _parse_ui(
        self,
        description: str,
        rules: list[GrammarRule],
    ) -> tuple[list[VisualToken], list[str]]:
        """Parse UI content."""
        tokens = []
        matches = []
        
        # Look for UI element patterns
        ui_patterns = [
            (r"button\s*[:\-]?\s*[\"']?(\w+)", VisualTokenType.BUTTON),
            (r"input\s*(field|box)?", VisualTokenType.INPUT),
            (r"menu\s*(item)?", VisualTokenType.MENU),
            (r"panel\s*[:\-]?\s*[\"']?(\w+)", VisualTokenType.PANEL),
            (r"label\s*[:\-]?\s*[\"']?(\w+)", VisualTokenType.LABEL),
            (r"icon\s*[:\-]?\s*[\"']?(\w+)", VisualTokenType.ICON),
        ]
        
        for pattern, token_type in ui_patterns:
            for match in re.finditer(pattern, description, re.IGNORECASE):
                tokens.append(VisualToken(
                    id=self._next_token_id(),
                    token_type=token_type,
                    text=match.group(0)[:50],
                    confidence=0.75,
                ))
                matches.append(f"ui_{token_type.value}")
        
        return tokens, matches
    
    def _parse_diagram(
        self,
        description: str,
        rules: list[GrammarRule],
    ) -> tuple[list[VisualToken], list[str]]:
        """Parse diagram content."""
        tokens = []
        matches = []
        
        # Look for nodes
        node_patterns = [
            r"(?:box|node|entity|component)\s*[:\-]?\s*[\"']?([^\"'\n,]+)",
            r"([A-Z][a-zA-Z]+)\s*(?:→|->|-->|connects to)",
        ]
        
        for pattern in node_patterns:
            for match in re.finditer(pattern, description):
                tokens.append(VisualToken(
                    id=self._next_token_id(),
                    token_type=VisualTokenType.NODE,
                    text=match.group(1).strip() if match.lastindex else match.group(0),
                    confidence=0.7,
                ))
                matches.append("diagram_node")
        
        # Look for edges/arrows
        edge_pattern = r"(\w+)\s*(?:→|->|-->|connects to|links to)\s*(\w+)"
        for match in re.finditer(edge_pattern, description, re.IGNORECASE):
            source = match.group(1)
            target = match.group(2)
            
            tokens.append(VisualToken(
                id=self._next_token_id(),
                token_type=VisualTokenType.EDGE,
                text=f"{source} → {target}",
                connects_to=[source, target],
                confidence=0.8,
            ))
            matches.append("diagram_edge")
        
        return tokens, matches
    
    def _parse_generic(self, description: str) -> list[VisualToken]:
        """Parse generic content."""
        tokens = []
        
        # Split into regions by paragraph
        paragraphs = description.split("\n\n")
        
        for para in paragraphs:
            if para.strip():
                tokens.append(VisualToken(
                    id=self._next_token_id(),
                    token_type=VisualTokenType.REGION,
                    text=para.strip()[:200],
                    confidence=0.5,
                ))
        
        return tokens
    
    def _build_structure(self, tokens: list[VisualToken]) -> dict[str, Any]:
        """Build hierarchical structure from tokens."""
        structure = {
            "total_tokens": len(tokens),
            "by_type": {},
            "hierarchy_depth": 0,
        }
        
        # Count by type
        for token in tokens:
            type_name = token.token_type.value
            structure["by_type"][type_name] = structure["by_type"].get(type_name, 0) + 1
        
        # Compute hierarchy depth
        max_depth = 0
        for token in tokens:
            depth = 0
            current = token
            while current.parent_id:
                depth += 1
                parent = next((t for t in tokens if t.id == current.parent_id), None)
                if parent:
                    current = parent
                else:
                    break
            max_depth = max(max_depth, depth)
        
        structure["hierarchy_depth"] = max_depth
        
        return structure
    
    def _compute_confidence(
        self,
        tokens: list[VisualToken],
        grammar_matches: list[str],
    ) -> float:
        """Compute overall parse confidence."""
        if not tokens:
            return 0.0
        
        # Average token confidence
        avg_token_conf = sum(t.confidence for t in tokens) / len(tokens)
        
        # Grammar match bonus
        grammar_bonus = min(len(grammar_matches) * 0.05, 0.3)
        
        return min(avg_token_conf + grammar_bonus, 1.0)


# =============================================================================
# Grammar-Enhanced Analyzer
# =============================================================================

class GrammarEnhancedAnalyzer:
    """
    Combines VLM analysis with grammar-based parsing for deep visual understanding.
    """
    
    def __init__(self):
        self.parser = VisualParser()
    
    def analyze(
        self,
        vlm_description: str,
        content_type: str = "unknown",
        entities: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Perform grammar-enhanced analysis.
        
        Args:
            vlm_description: Description from VLM
            content_type: Detected content type
            entities: Pre-extracted entities
        
        Returns:
            Enhanced analysis with structure
        """
        # Parse with grammar
        parse_result = self.parser.parse(vlm_description, content_type)
        
        # Enrich with entity linking
        if entities:
            self._link_entities(parse_result, entities)
        
        # Build program representation
        program_repr = self._build_program_repr(parse_result)
        
        return {
            "parse": parse_result.to_dict(),
            "program": program_repr,
            "summary": self._generate_summary(parse_result),
        }
    
    def _link_entities(
        self,
        parse_result: ParseResult,
        entities: list[str],
    ) -> None:
        """Link entities to tokens."""
        for token in parse_result.tokens:
            if token.text:
                for entity in entities:
                    if entity.lower() in token.text.lower():
                        token.references.append(entity)
    
    def _build_program_repr(self, parse_result: ParseResult) -> dict[str, Any]:
        """Build program representation from parse."""
        if parse_result.content_type == "code":
            return self._build_code_program(parse_result)
        elif parse_result.content_type == "ui":
            return self._build_ui_program(parse_result)
        elif parse_result.content_type == "diagram":
            return self._build_diagram_program(parse_result)
        else:
            return {"type": "generic", "tokens": len(parse_result.tokens)}
    
    def _build_code_program(self, parse_result: ParseResult) -> dict[str, Any]:
        """Build code program representation."""
        functions = [t for t in parse_result.tokens if t.token_type == VisualTokenType.FUNCTION]
        classes = [t for t in parse_result.tokens if t.token_type == VisualTokenType.CLASS]
        imports = [t for t in parse_result.tokens if t.token_type == VisualTokenType.IMPORT]
        
        return {
            "type": "code_module",
            "imports": [t.text for t in imports],
            "classes": [{"name": t.text, "id": t.id} for t in classes],
            "functions": [{"name": t.text, "id": t.id} for t in functions],
            "total_elements": len(parse_result.tokens),
        }
    
    def _build_ui_program(self, parse_result: ParseResult) -> dict[str, Any]:
        """Build UI program representation."""
        buttons = [t for t in parse_result.tokens if t.token_type == VisualTokenType.BUTTON]
        inputs = [t for t in parse_result.tokens if t.token_type == VisualTokenType.INPUT]
        panels = [t for t in parse_result.tokens if t.token_type == VisualTokenType.PANEL]
        
        return {
            "type": "ui_layout",
            "components": {
                "buttons": [t.text for t in buttons],
                "inputs": len(inputs),
                "panels": len(panels),
            },
            "action_candidates": [t.text for t in buttons if t.text],
            "total_elements": len(parse_result.tokens),
        }
    
    def _build_diagram_program(self, parse_result: ParseResult) -> dict[str, Any]:
        """Build diagram program representation."""
        nodes = [t for t in parse_result.tokens if t.token_type == VisualTokenType.NODE]
        edges = [t for t in parse_result.tokens if t.token_type == VisualTokenType.EDGE]
        
        return {
            "type": "graph_structure",
            "nodes": [{"name": t.text, "id": t.id} for t in nodes],
            "edges": [{"from_to": t.connects_to, "id": t.id} for t in edges],
            "node_count": len(nodes),
            "edge_count": len(edges),
        }
    
    def _generate_summary(self, parse_result: ParseResult) -> str:
        """Generate human-readable summary."""
        parts = [f"Detected {parse_result.content_type} content"]
        parts.append(f"with {len(parse_result.tokens)} visual tokens")
        
        if parse_result.grammar_matches:
            unique_matches = list(set(parse_result.grammar_matches))[:5]
            parts.append(f"matching patterns: {', '.join(unique_matches)}")
        
        parts.append(f"(confidence: {parse_result.confidence:.2f})")
        
        return " ".join(parts)
