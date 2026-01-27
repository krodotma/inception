"""
Plain Markdown exporter.

Universal documentation format.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from inception.enhance.operations.export.pipeline import Exporter, ExportConfig, ExportResult

logger = logging.getLogger(__name__)


class MarkdownExporter(Exporter):
    """
    Exports to plain Markdown.
    
    Features:
    - Standard markdown links
    - Single-file or multi-file output
    - Table of contents
    """
    
    def export(self, data: dict[str, Any]) -> ExportResult:
        """Export data to plain Markdown."""
        total_size = 0
        errors = []
        
        # Single comprehensive file
        content = self._render_all(data)
        
        output_path = self.config.output_dir / "knowledge_base.md"
        output_path.write_text(content)
        
        total_size = len(content.encode())
        
        return ExportResult(
            success=True,
            output_dir=self.config.output_dir,
            files_created=1,
            total_size_bytes=total_size,
            errors=errors,
        )
    
    def _render_all(self, data: dict[str, Any]) -> str:
        """Render all content to single markdown file."""
        lines = []
        
        lines.append("# Knowledge Base")
        lines.append("")
        lines.append(f"*Generated: {data.get('metadata', {}).get('exported_at', '')}*")
        lines.append("")
        
        # Table of contents
        lines.append("## Table of Contents")
        lines.append("")
        lines.append("- [Entities](#entities)")
        lines.append("- [Claims](#claims)")
        lines.append("- [Procedures](#procedures)")
        lines.append("- [Sources](#sources)")
        lines.append("")
        
        # Entities
        lines.append("## Entities")
        lines.append("")
        for entity in data.get("entities", []):
            lines.append(f"### {entity.get('name', 'Unknown')}")
            lines.append("")
            if entity.get('type'):
                lines.append(f"**Type**: {entity['type']}")
            if entity.get('description'):
                lines.append("")
                lines.append(entity['description'])
            lines.append("")
        
        # Claims
        lines.append("## Claims")
        lines.append("")
        for claim in data.get("claims", []):
            lines.append(f"- {claim.get('text', '')}")
        lines.append("")
        
        # Procedures
        lines.append("## Procedures")
        lines.append("")
        for proc in data.get("procedures", []):
            lines.append(f"### {proc.get('name', 'Procedure')}")
            lines.append("")
            if proc.get('steps'):
                for i, step in enumerate(proc['steps'], 1):
                    lines.append(f"{i}. {step}")
            lines.append("")
        
        # Sources
        lines.append("## Sources")
        lines.append("")
        for source in data.get("sources", []):
            lines.append(f"- {source.get('title', source.get('url', 'Unknown'))}")
        lines.append("")
        
        return "\n".join(lines)
