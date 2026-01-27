"""
Source registry for tracking source reliability.

Design by OPUS-1:
SourceWeight = BaseReliability × Freshness × Specificity
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """Type of knowledge source."""
    
    ACADEMIC = auto()      # Peer-reviewed papers
    DOCUMENTATION = auto() # Official documentation
    ENCYCLOPEDIA = auto()  # Wikipedia, Britannica
    NEWS = auto()          # News articles
    BLOG = auto()          # Blog posts
    SOCIAL = auto()        # Social media
    VIDEO = auto()         # Video content
    UNKNOWN = auto()


@dataclass
class SourceInfo:
    """Information about a knowledge source."""
    
    nid: int
    url: str | None = None
    name: str = ""
    source_type: SourceType = SourceType.UNKNOWN
    
    # Reliability factors
    base_reliability: float = 0.5  # 0-1
    citation_count: int = 0        # How often cited
    domain_authority: float = 0.5  # Domain reputation
    
    # Temporal factors
    published_at: datetime | None = None
    last_verified: datetime | None = None
    
    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def freshness(self) -> float:
        """Calculate freshness score (0-1)."""
        if not self.published_at:
            return 0.5  # Unknown freshness
        
        age_days = (datetime.now() - self.published_at).days
        
        if age_days < 30:
            return 1.0
        elif age_days < 365:
            return 0.8
        elif age_days < 365 * 3:
            return 0.6
        elif age_days < 365 * 10:
            return 0.4
        else:
            return 0.2
    
    @property
    def weight(self) -> float:
        """Calculate overall source weight."""
        type_bonus = {
            SourceType.ACADEMIC: 1.2,
            SourceType.DOCUMENTATION: 1.1,
            SourceType.ENCYCLOPEDIA: 1.0,
            SourceType.NEWS: 0.8,
            SourceType.BLOG: 0.6,
            SourceType.SOCIAL: 0.4,
            SourceType.VIDEO: 0.7,
            SourceType.UNKNOWN: 0.5,
        }
        
        return (
            self.base_reliability *
            self.freshness *
            type_bonus[self.source_type] *
            (1 + min(self.citation_count, 100) / 100)
        )


class SourceRegistry:
    """
    Registry for tracking source reliability across the knowledge graph.
    
    Enables weighted fusion based on source quality.
    """
    
    def __init__(self):
        """Initialize the source registry."""
        self._sources: dict[int, SourceInfo] = {}
        self._domain_scores: dict[str, float] = self._init_domain_scores()
    
    def _init_domain_scores(self) -> dict[str, float]:
        """Initialize default domain authority scores."""
        return {
            # Highly authoritative
            "wikipedia.org": 0.85,
            "docs.python.org": 0.95,
            "developer.mozilla.org": 0.9,
            "arxiv.org": 0.85,
            "nature.com": 0.95,
            "science.org": 0.95,
            "acm.org": 0.9,
            "ieee.org": 0.9,
            
            # Good sources
            "stackoverflow.com": 0.75,
            "github.com": 0.7,
            "medium.com": 0.5,
            
            # Lower authority
            "reddit.com": 0.3,
            "twitter.com": 0.2,
            "x.com": 0.2,
        }
    
    def register(self, source: SourceInfo) -> None:
        """Register a source."""
        # Auto-detect domain authority
        if source.url and source.domain_authority == 0.5:
            domain = self._extract_domain(source.url)
            if domain in self._domain_scores:
                source.domain_authority = self._domain_scores[domain]
        
        self._sources[source.nid] = source
        logger.debug(f"Registered source {source.nid}: weight={source.weight:.2f}")
    
    def get(self, nid: int) -> SourceInfo | None:
        """Get source info by NID."""
        return self._sources.get(nid)
    
    def get_weight(self, nid: int) -> float:
        """Get source weight, defaulting to 0.5 if unknown."""
        source = self._sources.get(nid)
        if source:
            return source.weight
        return 0.5
    
    def update_reliability(
        self,
        nid: int,
        delta: float,
        reason: str = "",
    ) -> None:
        """Update source reliability based on evidence."""
        source = self._sources.get(nid)
        if source:
            old_reliability = source.base_reliability
            source.base_reliability = max(0, min(1, source.base_reliability + delta))
            logger.info(
                f"Source {nid} reliability: {old_reliability:.2f} → "
                f"{source.base_reliability:.2f} ({reason})"
            )
    
    def cite(self, nid: int) -> None:
        """Record a citation of this source."""
        source = self._sources.get(nid)
        if source:
            source.citation_count += 1
    
    def all_sources(self) -> list[SourceInfo]:
        """Get all registered sources."""
        return list(self._sources.values())
    
    def top_sources(self, n: int = 10) -> list[SourceInfo]:
        """Get top N sources by weight."""
        return sorted(
            self._sources.values(),
            key=lambda s: s.weight,
            reverse=True,
        )[:n]
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        if domain.startswith("www."):
            domain = domain[4:]
        
        return domain
    
    def infer_source_type(self, url: str, content: str = "") -> SourceType:
        """Infer source type from URL and content."""
        domain = self._extract_domain(url)
        
        if "arxiv.org" in domain or "nature.com" in domain or "acm." in domain:
            return SourceType.ACADEMIC
        elif "docs." in domain or "documentation" in url:
            return SourceType.DOCUMENTATION
        elif "wikipedia.org" in domain or "britannica.com" in domain:
            return SourceType.ENCYCLOPEDIA
        elif "news." in domain or any(x in domain for x in ["bbc.", "cnn.", "nytimes."]):
            return SourceType.NEWS
        elif "blog." in domain or "medium.com" in domain:
            return SourceType.BLOG
        elif any(x in domain for x in ["twitter.", "x.com", "reddit.", "facebook."]):
            return SourceType.SOCIAL
        elif any(x in domain for x in ["youtube.", "vimeo.", "twitch."]):
            return SourceType.VIDEO
        else:
            return SourceType.UNKNOWN
