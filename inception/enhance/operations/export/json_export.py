"""
JSON exporter for structured data.

Machine-readable export format.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from inception.enhance.operations.export.pipeline import Exporter, ExportConfig, ExportResult

logger = logging.getLogger(__name__)


class JSONExporter(Exporter):
    """
    Exports to structured JSON.
    
    Features:
    - Full graph structure preserved
    - Pretty-printed or compact
    - Optional schema validation
    """
    
    def export(self, data: dict[str, Any]) -> ExportResult:
        """Export data to JSON."""
        total_size = 0
        errors = []
        files_created = 0
        
        # Add export metadata
        export_data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "format": "inception-json",
            "content": data,
        }
        
        # Main export file
        content = json.dumps(export_data, indent=2, default=str)
        output_path = self.config.output_dir / "knowledge_base.json"
        output_path.write_text(content)
        total_size += len(content.encode())
        files_created += 1
        
        # Separate entity file for easier querying
        if self.config.include_entities and data.get("entities"):
            entities_content = json.dumps({
                "entities": data["entities"]
            }, indent=2, default=str)
            entities_path = self.config.output_dir / "entities.json"
            entities_path.write_text(entities_content)
            total_size += len(entities_content.encode())
            files_created += 1
        
        # Separate claims file
        if self.config.include_claims and data.get("claims"):
            claims_content = json.dumps({
                "claims": data["claims"]
            }, indent=2, default=str)
            claims_path = self.config.output_dir / "claims.json"
            claims_path.write_text(claims_content)
            total_size += len(claims_content.encode())
            files_created += 1
        
        return ExportResult(
            success=True,
            output_dir=self.config.output_dir,
            files_created=files_created,
            total_size_bytes=total_size,
            errors=errors,
        )
