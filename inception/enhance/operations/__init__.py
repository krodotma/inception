"""
Operations enhancement modules.

Production-ready operational capabilities:
- Incremental Sync: Watch and auto-ingest changed files
- Export Pipeline: Multiple output formats
- Interactive TUI: Terminal UI for knowledge exploration

Team Design:
- OPUS-3: Sync architecture, state management
- OPUS-1: Efficiency optimizations, debouncing
- SONNET: Export formats, TUI design
- OPUS-2: Template rendering, watch patterns
"""

from inception.enhance.operations.sync import (
    SyncEngine,
    SyncConfig,
    ChangeEvent,
    FileWatcher,
)
from inception.enhance.operations.export import (
    ExportPipeline,
    ExportFormat,
    ObsidianExporter,
    MarkdownExporter,
    JSONExporter,
)
from inception.enhance.operations.tui import (
    InceptionTUI,
)

__all__ = [
    # Sync
    "SyncEngine",
    "SyncConfig",
    "ChangeEvent",
    "FileWatcher",
    # Export
    "ExportPipeline",
    "ExportFormat",
    "ObsidianExporter",
    "MarkdownExporter",
    "JSONExporter",
    # TUI
    "InceptionTUI",
]
