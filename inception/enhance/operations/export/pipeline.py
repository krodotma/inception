"""
Export pipeline orchestrator.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from inception.enhance.operations.export.formats import ExportFormat, get_file_extension

logger = logging.getLogger(__name__)


@dataclass
class ExportConfig:
    """Configuration for export."""
    
    output_dir: Path
    format: ExportFormat = ExportFormat.OBSIDIAN
    
    # Content options
    include_entities: bool = True
    include_claims: bool = True
    include_procedures: bool = True
    include_sources: bool = True
    include_gaps: bool = False
    
    # Formatting
    max_file_size_kb: int = 256  # Split large files
    create_index: bool = True
    link_format: str = "wikilink"  # wikilink, relative, absolute


@dataclass
class ExportResult:
    """Result of an export operation."""
    
    success: bool
    output_dir: Path
    files_created: int = 0
    total_size_bytes: int = 0
    duration_ms: float = 0.0
    errors: list[str] = field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


class Exporter:
    """Base class for exporters."""
    
    def __init__(self, config: ExportConfig):
        self.config = config
    
    def export(self, data: dict[str, Any]) -> ExportResult:
        """Export data to files."""
        raise NotImplementedError


class ExportPipeline:
    """
    Orchestrates knowledge graph export.
    
    Workflow:
    1. Query knowledge graph
    2. Transform to export format
    3. Write to files
    4. Generate index/navigation
    """
    
    def __init__(
        self,
        db: Any = None,  # InceptionDB
        query_layer: Any = None,  # QueryLayer
    ):
        """Initialize export pipeline."""
        self.db = db
        self.query = query_layer
        self._exporters: dict[ExportFormat, type[Exporter]] = {}
    
    def register_exporter(
        self,
        format: ExportFormat,
        exporter_class: type[Exporter],
    ) -> None:
        """Register an exporter for a format."""
        self._exporters[format] = exporter_class
    
    def export(
        self,
        config: ExportConfig,
        node_filter: Callable[[Any], bool] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> ExportResult:
        """
        Export knowledge graph.
        
        Args:
            config: Export configuration
            node_filter: Optional filter for nodes
            progress_callback: Progress callback
        
        Returns:
            Export result
        """
        import time
        start = time.time()
        
        # Ensure output directory exists
        config.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Gather data
        data = self._gather_data(config, node_filter)
        
        # Get exporter
        exporter_class = self._exporters.get(config.format)
        if not exporter_class:
            return ExportResult(
                success=False,
                output_dir=config.output_dir,
                errors=[f"No exporter for format: {config.format.name}"],
            )
        
        exporter = exporter_class(config)
        
        # Export
        result = exporter.export(data)
        result.duration_ms = (time.time() - start) * 1000
        
        return result
    
    def _gather_data(
        self,
        config: ExportConfig,
        node_filter: Callable[[Any], bool] | None,
    ) -> dict[str, Any]:
        """Gather data for export."""
        data = {
            "entities": [],
            "claims": [],
            "procedures": [],
            "sources": [],
            "gaps": [],
            "edges": [],
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "format": config.format.name,
            },
        }
        
        if not self.db:
            return data
        
        # Would query from actual DB here
        # For now return empty structure
        
        return data
    
    def export_node(
        self,
        node_id: int,
        config: ExportConfig,
    ) -> ExportResult:
        """Export a single node and related content."""
        # Would implement single-node export
        pass
    
    def export_query_results(
        self,
        query_results: list[Any],
        config: ExportConfig,
    ) -> ExportResult:
        """Export results from a query."""
        # Would implement query result export
        pass
