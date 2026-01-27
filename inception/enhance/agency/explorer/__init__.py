"""
Gap Explorer - Autonomous knowledge acquisition.

Scans the knowledge graph for gaps and resolves them
through web search and content ingestion.

Safety rails designed by OPUS-3.
"""

from inception.enhance.agency.explorer.classifier import GapClassifier, GapType
from inception.enhance.agency.explorer.config import ExplorationConfig
from inception.enhance.agency.explorer.resolver import GapExplorer

__all__ = [
    "GapExplorer",
    "GapClassifier",
    "GapType",
    "ExplorationConfig",
]
