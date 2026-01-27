"""
Inception: Local-first multimodal learning ingestion with temporal LMDB knowledge hypergraph.

This package provides tools for ingesting learning materials (YouTube, web pages, PDFs, etc.),
extracting structured knowledge into a temporal hypergraph stored in LMDB, and producing
actionable outputs (Action Packs) with evidence linking.
"""

__version__ = "0.1.0"
__author__ = "Inception Team"

from inception.config import Config, get_config

__all__ = ["__version__", "Config", "get_config"]
