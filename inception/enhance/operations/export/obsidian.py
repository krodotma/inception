"""
Obsidian exporter - Markdown with [[wikilinks]].

The most requested export format for knowledge management.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from inception.enhance.operations.export.pipeline import Exporter, ExportConfig, ExportResult

logger = logging.getLogger(__name__)


class ObsidianExporter(Exporter):
    """
    Exports to Obsidian-compatible Markdown.
    
    Features:
    - [[wikilinks]] for entity connections
    - YAML frontmatter with metadata
    - Tags for entity types
    - Backlinks section
    """
    
    def export(self, data: dict[str, Any]) -> ExportResult:
        """Export data to Obsidian vault format."""
        files_created = 0
        total_size = 0
        errors = []
        
        # Create subdirectories
        (self.config.output_dir / "entities").mkdir(exist_ok=True)
        (self.config.output_dir / "claims").mkdir(exist_ok=True)
        (self.config.output_dir / "procedures").mkdir(exist_ok=True)
        (self.config.output_dir / "sources").mkdir(exist_ok=True)
        
        # Export entities
        if self.config.include_entities:
            for entity in data.get("entities", []):
                try:
                    content = self._render_entity(entity, data)
                    path = self.config.output_dir / "entities" / f"{self._slugify(entity.get('name', 'unknown'))}.md"
                    path.write_text(content)
                    files_created += 1
                    total_size += len(content.encode())
                except Exception as e:
                    errors.append(f"Entity {entity.get('name')}: {e}")
        
        # Export claims
        if self.config.include_claims:
            for claim in data.get("claims", []):
                try:
                    content = self._render_claim(claim, data)
                    path = self.config.output_dir / "claims" / f"claim-{claim.get('nid', 0)}.md"
                    path.write_text(content)
                    files_created += 1
                    total_size += len(content.encode())
                except Exception as e:
                    errors.append(f"Claim {claim.get('nid')}: {e}")
        
        # Export procedures
        if self.config.include_procedures:
            for proc in data.get("procedures", []):
                try:
                    content = self._render_procedure(proc, data)
                    path = self.config.output_dir / "procedures" / f"{self._slugify(proc.get('name', 'procedure'))}.md"
                    path.write_text(content)
                    files_created += 1
                    total_size += len(content.encode())
                except Exception as e:
                    errors.append(f"Procedure {proc.get('name')}: {e}")
        
        # Create index
        if self.config.create_index:
            index_content = self._create_index(data)
            index_path = self.config.output_dir / "INDEX.md"
            index_path.write_text(index_content)
            files_created += 1
            total_size += len(index_content.encode())
        
        return ExportResult(
            success=len(errors) == 0,
            output_dir=self.config.output_dir,
            files_created=files_created,
            total_size_bytes=total_size,
            errors=errors,
        )
    
    def _render_entity(self, entity: dict[str, Any], data: dict[str, Any]) -> str:
        """Render entity to Obsidian markdown."""
        lines = []
        
        # YAML frontmatter
        lines.append("---")
        lines.append(f"entity_type: {entity.get('type', 'unknown')}")
        if entity.get('nid'):
            lines.append(f"nid: {entity['nid']}")
        lines.append(f"tags: [entity, {entity.get('type', 'unknown')}]")
        lines.append("---")
        lines.append("")
        
        # Title
        lines.append(f"# {entity.get('name', 'Unknown Entity')}")
        lines.append("")
        
        # Description
        if entity.get('description'):
            lines.append(entity['description'])
            lines.append("")
        
        # Aliases
        if entity.get('aliases'):
            lines.append("## Also Known As")
            for alias in entity['aliases']:
                lines.append(f"- {alias}")
            lines.append("")
        
        # Related claims
        claims = [c for c in data.get("claims", []) if entity.get('nid') in [c.get('subject'), c.get('object')]]
        if claims:
            lines.append("## Related Claims")
            for claim in claims[:10]:
                lines.append(f"- {claim.get('text', '')}")
            lines.append("")
        
        # Linked entities
        linked = self._find_linked_entities(entity, data)
        if linked:
            lines.append("## Related Entities")
            for link in linked[:10]:
                lines.append(f"- [[{link}]]")
            lines.append("")
        
        return "\n".join(lines)
    
    def _render_claim(self, claim: dict[str, Any], data: dict[str, Any]) -> str:
        """Render claim to Obsidian markdown."""
        lines = []
        
        lines.append("---")
        lines.append(f"claim_type: assertion")
        lines.append(f"confidence: {claim.get('confidence', 0.5)}")
        lines.append(f"nid: {claim.get('nid', 0)}")
        lines.append("tags: [claim]")
        lines.append("---")
        lines.append("")
        
        lines.append(f"# {claim.get('text', 'Unknown Claim')[:60]}...")
        lines.append("")
        lines.append(f"> {claim.get('text', '')}")
        lines.append("")
        
        if claim.get('sources'):
            lines.append("## Sources")
            for source in claim.get('sources', []):
                lines.append(f"- {source}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _render_procedure(self, proc: dict[str, Any], data: dict[str, Any]) -> str:
        """Render procedure to Obsidian markdown."""
        lines = []
        
        lines.append("---")
        lines.append(f"procedure_type: {proc.get('type', 'howto')}")
        lines.append(f"nid: {proc.get('nid', 0)}")
        lines.append("tags: [procedure]")
        lines.append("---")
        lines.append("")
        
        lines.append(f"# {proc.get('name', 'Procedure')}")
        lines.append("")
        
        if proc.get('description'):
            lines.append(proc['description'])
            lines.append("")
        
        if proc.get('steps'):
            lines.append("## Steps")
            for i, step in enumerate(proc['steps'], 1):
                lines.append(f"{i}. {step}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _create_index(self, data: dict[str, Any]) -> str:
        """Create index file."""
        lines = []
        
        lines.append("# Knowledge Base Index")
        lines.append("")
        lines.append(f"*Exported: {data.get('metadata', {}).get('exported_at', 'Unknown')}*")
        lines.append("")
        
        # Summary
        lines.append("## Summary")
        lines.append(f"- **Entities**: {len(data.get('entities', []))}")
        lines.append(f"- **Claims**: {len(data.get('claims', []))}")
        lines.append(f"- **Procedures**: {len(data.get('procedures', []))}")
        lines.append(f"- **Sources**: {len(data.get('sources', []))}")
        lines.append("")
        
        # Entity index
        if data.get('entities'):
            lines.append("## Entities")
            for entity in sorted(data['entities'], key=lambda e: e.get('name', '')):
                name = entity.get('name', 'Unknown')
                lines.append(f"- [[entities/{self._slugify(name)}|{name}]]")
            lines.append("")
        
        return "\n".join(lines)
    
    def _find_linked_entities(
        self,
        entity: dict[str, Any],
        data: dict[str, Any],
    ) -> list[str]:
        """Find entities linked to this one."""
        linked = set()
        entity_nid = entity.get('nid')
        
        for edge in data.get('edges', []):
            if edge.get('from_nid') == entity_nid:
                # Find target entity
                for e in data.get('entities', []):
                    if e.get('nid') == edge.get('to_nid'):
                        linked.add(e.get('name', ''))
            elif edge.get('to_nid') == entity_nid:
                # Find source entity
                for e in data.get('entities', []):
                    if e.get('nid') == edge.get('from_nid'):
                        linked.add(e.get('name', ''))
        
        return list(linked)
    
    def _slugify(self, text: str) -> str:
        """Convert text to URL-safe slug."""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '-', text)
        return text[:100]
