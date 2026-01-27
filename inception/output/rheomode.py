"""
RheoMode multi-resolution output module.

Provides output at 5 resolution levels:
- Level 0: 1-line gist + why it matters
- Level 1: Key takeaways + action candidates
- Level 2: Evidence-linked claims/procedures
- Level 3: Full structured deconstruction
- Level 4: Derived skills/playbooks/tests
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

from inception.db import InceptionDB, get_db
from inception.db.records import NodeRecord, SpanRecord
from inception.db.keys import NodeKind


class RheoLevel(IntEnum):
    """RheoMode resolution levels."""
    GIST = 0  # 1-line summary
    TAKEAWAYS = 1  # Key points
    EVIDENCE = 2  # Evidence-linked content
    FULL = 3  # Complete deconstruction
    SKILLS = 4  # Derived skills


@dataclass
class ActionItem:
    """An actionable item extracted from content."""
    
    action: str
    context: str | None = None
    priority: int = 0  # 0-9, higher is more important
    evidence_nids: list[int] = field(default_factory=list)
    
    # Classification
    action_type: str = "general"  # do, learn, decide, check
    
    # Confidence
    confidence: float = 1.0


@dataclass
class KeyTakeaway:
    """A key takeaway from the content."""
    
    text: str
    category: str | None = None  # insight, fact, warning, tip
    importance: float = 1.0
    evidence_nids: list[int] = field(default_factory=list)


@dataclass
class EvidenceLink:
    """Link to source evidence."""
    
    span_nid: int
    timestamp_ms: int | None = None
    page: int | None = None
    text_preview: str | None = None


@dataclass
class ActionPack:
    """
    Multi-resolution output package.
    
    Contains output at all rheomode levels for a source.
    """
    
    source_nid: int
    title: str | None = None
    
    # Level 0: Gist
    gist: str | None = None
    why_it_matters: str | None = None
    
    # Level 1: Takeaways
    key_takeaways: list[KeyTakeaway] = field(default_factory=list)
    action_items: list[ActionItem] = field(default_factory=list)
    
    # Level 2: Evidence-linked
    claims: list[dict[str, Any]] = field(default_factory=list)
    procedures: list[dict[str, Any]] = field(default_factory=list)
    
    # Level 3: Full deconstruction
    entities: list[dict[str, Any]] = field(default_factory=list)
    sections: list[dict[str, Any]] = field(default_factory=list)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    
    # Level 4: Skills
    skills: list[dict[str, Any]] = field(default_factory=list)
    playbooks: list[dict[str, Any]] = field(default_factory=list)
    
    # Gaps and uncertainties
    gaps: list[dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    rheo_level: int = 3
    generated_at: str | None = None
    
    def at_level(self, level: RheoLevel) -> dict[str, Any]:
        """Get output at a specific rheomode level."""
        result: dict[str, Any] = {
            "source_nid": self.source_nid,
            "title": self.title,
        }
        
        if level >= RheoLevel.GIST:
            result["gist"] = self.gist
            result["why_it_matters"] = self.why_it_matters
        
        if level >= RheoLevel.TAKEAWAYS:
            result["key_takeaways"] = [
                {"text": t.text, "category": t.category}
                for t in self.key_takeaways
            ]
            result["action_items"] = [
                {"action": a.action, "type": a.action_type, "priority": a.priority}
                for a in self.action_items
            ]
        
        if level >= RheoLevel.EVIDENCE:
            result["claims"] = self.claims
            result["procedures"] = self.procedures
        
        if level >= RheoLevel.FULL:
            result["entities"] = self.entities
            result["sections"] = self.sections
            result["timeline"] = self.timeline
            result["gaps"] = self.gaps
        
        if level >= RheoLevel.SKILLS:
            result["skills"] = self.skills
            result["playbooks"] = self.playbooks
        
        return result
    
    def to_markdown(self, level: RheoLevel = RheoLevel.EVIDENCE) -> str:
        """Render action pack as markdown at specified level."""
        lines = []
        
        if self.title:
            lines.append(f"# {self.title}")
        
        if level >= RheoLevel.GIST and self.gist:
            lines.append(f"\n> **TL;DR:** {self.gist}")
            if self.why_it_matters:
                lines.append(f">\n> **Why it matters:** {self.why_it_matters}")
        
        if level >= RheoLevel.TAKEAWAYS and self.key_takeaways:
            lines.append("\n## Key Takeaways")
            for takeaway in self.key_takeaways:
                prefix = ""
                if takeaway.category == "warning":
                    prefix = "⚠️ "
                elif takeaway.category == "tip":
                    prefix = "💡 "
                lines.append(f"- {prefix}{takeaway.text}")
        
        if level >= RheoLevel.TAKEAWAYS and self.action_items:
            lines.append("\n## Action Items")
            for item in sorted(self.action_items, key=lambda x: -x.priority):
                lines.append(f"- [ ] {item.action}")
        
        if level >= RheoLevel.EVIDENCE and self.claims:
            lines.append("\n## Claims")
            for claim in self.claims:
                lines.append(f"- {claim.get('text', '')}")
        
        if level >= RheoLevel.EVIDENCE and self.procedures:
            lines.append("\n## Procedures")
            for proc in self.procedures:
                lines.append(f"\n### {proc.get('title', 'Procedure')}")
                for step in proc.get("steps", []):
                    lines.append(f"{step.get('index', 0) + 1}. {step.get('text', '')}")
        
        if level >= RheoLevel.FULL and self.entities:
            lines.append("\n## Key Entities")
            entity_types = {}
            for ent in self.entities:
                etype = ent.get("entity_type", "OTHER")
                if etype not in entity_types:
                    entity_types[etype] = []
                entity_types[etype].append(ent.get("name", ""))
            
            for etype, names in entity_types.items():
                lines.append(f"- **{etype}:** {', '.join(names[:5])}")
        
        if self.gaps:
            lines.append("\n## Uncertainties & Gaps")
            for gap in self.gaps[:5]:
                lines.append(f"- ❓ {gap.get('description', '')}")
        
        return "\n".join(lines)


class ActionPackGenerator:
    """
    Generator for ActionPack output.
    
    Produces multi-resolution output from the knowledge graph.
    """
    
    def __init__(self, db: InceptionDB | None = None):
        """
        Initialize the generator.
        
        Args:
            db: Database instance
        """
        self.db = db or get_db()
    
    def generate(
        self,
        source_nid: int,
        level: RheoLevel = RheoLevel.EVIDENCE,
    ) -> ActionPack:
        """
        Generate an ActionPack for a source.
        
        Args:
            source_nid: Source NID to generate pack for
            level: Maximum rheomode level to include
        
        Returns:
            ActionPack with content at specified level
        """
        import datetime
        
        # Get source info
        source = self.db.get_source(source_nid)
        title = source.title if source else None
        
        pack = ActionPack(
            source_nid=source_nid,
            title=title,
            rheo_level=level,
            generated_at=datetime.datetime.utcnow().isoformat(),
        )
        
        # Collect nodes
        entities = []
        claims = []
        procedures = []
        gaps = []
        
        for node in self.db.iter_nodes():
            if source_nid in (node.source_nids or []):
                if node.kind == NodeKind.ENTITY:
                    entities.append(node.payload)
                elif node.kind == NodeKind.CLAIM:
                    claims.append(node.payload)
                elif node.kind == NodeKind.PROCEDURE:
                    procedures.append(node.payload)
                elif node.kind == NodeKind.GAP:
                    gaps.append(node.payload)
        
        pack.entities = entities
        pack.claims = claims
        pack.procedures = procedures
        pack.gaps = gaps
        
        # Generate gist (Level 0)
        pack.gist = self._generate_gist(claims, procedures)
        pack.why_it_matters = self._generate_why_it_matters(claims)
        
        # Generate takeaways (Level 1)
        pack.key_takeaways = self._generate_takeaways(claims)
        pack.action_items = self._generate_action_items(procedures, claims)
        
        # Generate skills (Level 4)
        if level >= RheoLevel.SKILLS:
            pack.skills = self._generate_skills(procedures)
        
        return pack
    
    def _generate_gist(
        self,
        claims: list[dict],
        procedures: list[dict],
    ) -> str:
        """Generate 1-line summary."""
        if procedures:
            proc = procedures[0]
            return f"How-to guide: {proc.get('title', 'procedure')}"
        elif claims:
            # Take first claim as gist
            return claims[0].get("text", "Content summary")[:100]
        return "Ingested content"
    
    def _generate_why_it_matters(self, claims: list[dict]) -> str:
        """Generate 'why it matters' statement."""
        if claims:
            return f"Contains {len(claims)} key claims you can apply."
        return "Provides actionable knowledge."
    
    def _generate_takeaways(self, claims: list[dict]) -> list[KeyTakeaway]:
        """Generate key takeaways from claims."""
        takeaways = []
        
        for claim in claims[:5]:  # Top 5
            hedges = claim.get("hedges", [])
            category = "insight"
            if hedges:
                category = "warning"
            elif claim.get("modality") == "necessity":
                category = "tip"
            
            takeaway = KeyTakeaway(
                text=claim.get("text", ""),
                category=category,
            )
            takeaways.append(takeaway)
        
        return takeaways
    
    def _generate_action_items(
        self,
        procedures: list[dict],
        claims: list[dict],
    ) -> list[ActionItem]:
        """Generate action items from procedures and claims."""
        items = []
        
        # Extract actions from procedures
        for proc in procedures:
            for step in proc.get("steps", []):
                item = ActionItem(
                    action=step.get("text", ""),
                    action_type="do",
                    priority=5,
                )
                items.append(item)
        
        # Extract implied actions from claims
        for claim in claims:
            text = claim.get("text", "").lower()
            if any(word in text for word in ["should", "must", "need to", "important to"]):
                item = ActionItem(
                    action=f"Consider: {claim.get('text', '')}",
                    action_type="decide",
                    priority=3,
                )
                items.append(item)
        
        return items[:10]  # Limit to 10
    
    def _generate_skills(self, procedures: list[dict]) -> list[dict]:
        """Generate skill definitions from procedures."""
        skills = []
        
        for proc in procedures:
            skill = {
                "name": proc.get("title", "Skill"),
                "description": proc.get("goal", ""),
                "steps": [
                    {
                        "action": step.get("action_verb", "execute"),
                        "description": step.get("text", ""),
                    }
                    for step in proc.get("steps", [])
                ],
            }
            skills.append(skill)
        
        return skills


def generate_action_pack(
    source_nid: int,
    level: RheoLevel = RheoLevel.EVIDENCE,
) -> ActionPack:
    """
    Convenience function to generate an action pack.
    
    Args:
        source_nid: Source NID
        level: RheoMode level
    
    Returns:
        ActionPack
    """
    generator = ActionPackGenerator()
    return generator.generate(source_nid, level)
