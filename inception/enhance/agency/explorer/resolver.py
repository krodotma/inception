"""
Gap resolver - orchestrates gap exploration.

Combines classifier, search, and ingestion to resolve knowledge gaps.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from inception.enhance.agency.explorer.classifier import (
    GapClassifier,
    ClassifiedGap,
    GapType,
)
from inception.enhance.agency.explorer.config import ExplorationConfig
from inception.enhance.agency.explorer.search import WebSearcher, SearchResult

logger = logging.getLogger(__name__)


@dataclass
class ResolutionResult:
    """Result of attempting to resolve a gap."""
    
    gap: ClassifiedGap
    resolved: bool
    sources_found: list[SearchResult]
    content_ingested: list[str]
    new_nids: list[int]  # NIDs of new nodes created
    error: str | None = None


@dataclass
class ExplorationStats:
    """Statistics from an exploration session."""
    
    gaps_explored: int = 0
    gaps_resolved: int = 0
    sources_fetched: int = 0
    requests_made: int = 0
    cost_usd: float = 0.0


class GapExplorer:
    """
    Autonomous gap exploration with safety rails.
    
    Workflow:
    1. Scan knowledge graph for GAP nodes
    2. Classify and prioritize gaps
    3. Search for resolution sources
    4. Fetch and validate content
    5. Ingest new content (with confirmation)
    6. Link to resolve original gap
    """
    
    def __init__(
        self,
        config: ExplorationConfig | None = None,
        classifier: GapClassifier | None = None,
        searcher: WebSearcher | None = None,
    ):
        """
        Initialize the gap explorer.
        
        Args:
            config: Exploration configuration
            classifier: Gap classifier instance
            searcher: Web searcher instance
        """
        self.config = config or ExplorationConfig()
        self.classifier = classifier or GapClassifier()
        self.searcher = searcher or WebSearcher(self.config)
        
        self._stats = ExplorationStats()
        self._exploration_log: list[dict[str, Any]] = []
    
    @property
    def stats(self) -> ExplorationStats:
        """Get exploration statistics."""
        return self._stats
    
    def explore_gap(
        self,
        nid: int,
        payload: dict[str, Any],
        ingest_callback: Callable[[str, str], int] | None = None,
    ) -> ResolutionResult:
        """
        Explore and attempt to resolve a single gap.
        
        Args:
            nid: Gap node ID
            payload: Gap node payload
            ingest_callback: Callback to ingest content (url, content) -> nid
        
        Returns:
            Resolution result
        """
        # Classify the gap
        gap = self.classifier.classify(nid, payload)
        logger.info(f"Exploring gap: {gap.term} ({gap.gap_type.name})")
        
        self._stats.gaps_explored += 1
        
        # Search for resolution sources
        all_results: list[SearchResult] = []
        for query in gap.suggested_queries:
            results = self.searcher.search(query)
            all_results.extend(results)
            
            if len(all_results) >= self.config.max_sources_per_gap:
                break
        
        # Deduplicate by URL
        seen_urls: set[str] = set()
        unique_results = []
        for r in all_results:
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                unique_results.append(r)
        
        unique_results = unique_results[:self.config.max_sources_per_gap]
        
        if not unique_results:
            return ResolutionResult(
                gap=gap,
                resolved=False,
                sources_found=[],
                content_ingested=[],
                new_nids=[],
                error="No sources found",
            )
        
        # Fetch and ingest content
        content_ingested = []
        new_nids = []
        
        for result in unique_results:
            # Confirm if required
            if self.config.require_confirmation:
                action = f"Fetch and ingest: {result.url}"
                if not self.config.confirm(action):
                    logger.info(f"Skipped (not confirmed): {result.url}")
                    continue
            
            # Fetch content
            content = self.searcher.fetch_content(result.url)
            if not content:
                continue
            
            self._stats.sources_fetched += 1
            
            # Ingest if callback provided
            if ingest_callback:
                try:
                    new_nid = ingest_callback(result.url, content)
                    new_nids.append(new_nid)
                    content_ingested.append(result.url)
                except Exception as e:
                    logger.error(f"Failed to ingest {result.url}: {e}")
        
        resolved = len(content_ingested) > 0
        if resolved:
            self._stats.gaps_resolved += 1
        
        # Log exploration
        self._exploration_log.append({
            "gap_nid": nid,
            "gap_term": gap.term,
            "gap_type": gap.gap_type.name,
            "sources_found": len(unique_results),
            "content_ingested": len(content_ingested),
            "resolved": resolved,
        })
        
        return ResolutionResult(
            gap=gap,
            resolved=resolved,
            sources_found=unique_results,
            content_ingested=content_ingested,
            new_nids=new_nids,
        )
    
    def explore_all_gaps(
        self,
        gaps: list[tuple[int, dict[str, Any]]],
        ingest_callback: Callable[[str, str], int] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[ResolutionResult]:
        """
        Explore multiple gaps with prioritization.
        
        Args:
            gaps: List of (nid, payload) tuples
            ingest_callback: Callback to ingest content
            progress_callback: Callback for progress updates (current, total)
        
        Returns:
            List of resolution results
        """
        # Classify and prioritize
        classified = [
            self.classifier.classify(nid, payload)
            for nid, payload in gaps
        ]
        
        # Sort by priority (highest first)
        classified.sort(key=lambda g: g.priority, reverse=True)
        
        # Apply session limit
        to_explore = classified[:self.config.max_gaps_per_session]
        
        results = []
        for i, gap in enumerate(to_explore):
            if progress_callback:
                progress_callback(i + 1, len(to_explore))
            
            # Find original payload
            payload = next(
                p for nid, p in gaps if nid == gap.nid
            )
            
            result = self.explore_gap(gap.nid, payload, ingest_callback)
            results.append(result)
            
            # Check budget
            if self.searcher.session.cost_usd >= self.config.budget_cap_usd:
                logger.warning("Budget limit reached, stopping exploration")
                break
        
        return results
    
    def get_exploration_log(self) -> list[dict[str, Any]]:
        """Get the exploration log."""
        return self._exploration_log.copy()
