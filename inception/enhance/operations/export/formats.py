"""
Export format definitions.
"""

from __future__ import annotations

from enum import Enum, auto


class ExportFormat(Enum):
    """Available export formats."""
    
    OBSIDIAN = auto()   # Markdown with [[wikilinks]]
    MARKDOWN = auto()   # Plain markdown
    JSON = auto()       # Structured JSON
    RDF = auto()        # RDF/Turtle
    HTML = auto()       # Web publishing
    CSV = auto()        # Tabular data


def get_file_extension(fmt: ExportFormat) -> str:
    """Get file extension for format."""
    return {
        ExportFormat.OBSIDIAN: ".md",
        ExportFormat.MARKDOWN: ".md",
        ExportFormat.JSON: ".json",
        ExportFormat.RDF: ".ttl",
        ExportFormat.HTML: ".html",
        ExportFormat.CSV: ".csv",
    }.get(fmt, ".txt")
