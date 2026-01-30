"""
Source Intelligence Layer - Swarm Track 3

Enhanced source understanding with content-aware processing.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ContentDomain(Enum):
    """Content domain classification."""
    TECHNICAL = "technical"      # Code, docs, tutorials
    ACADEMIC = "academic"        # Papers, research
    NEWS = "news"                # News, current events
    SOCIAL = "social"            # Social media
    REFERENCE = "reference"      # Wikipedia, encyclopedias
    CREATIVE = "creative"        # Art, music, entertainment
    BUSINESS = "business"        # Business, finance
    UNKNOWN = "unknown"


class SourceQuality(Enum):
    """Source quality tiers."""
    AUTHORITATIVE = "authoritative"  # Primary sources, official
    VERIFIED = "verified"            # Peer-reviewed, vetted
    REPUTABLE = "reputable"          # Known reliable sources
    MIXED = "mixed"                  # Variable quality
    UNVERIFIED = "unverified"        # Unknown reliability
    LOW = "low"                      # Known issues


@dataclass
class SourceProfile:
    """Profile for a source with intelligence."""
    uri: str
    domain: ContentDomain = ContentDomain.UNKNOWN
    quality: SourceQuality = SourceQuality.UNVERIFIED
    authority_score: float = 0.5
    freshness_score: float = 0.5
    coverage_score: float = 0.5
    bias_indicators: list[str] = field(default_factory=list)
    expertise_areas: list[str] = field(default_factory=list)
    last_verified: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def overall_score(self) -> float:
        """Compute overall reliability score."""
        weights = {"authority": 0.4, "freshness": 0.2, "coverage": 0.2, "quality": 0.2}
        quality_scores = {
            SourceQuality.AUTHORITATIVE: 1.0,
            SourceQuality.VERIFIED: 0.9,
            SourceQuality.REPUTABLE: 0.7,
            SourceQuality.MIXED: 0.5,
            SourceQuality.UNVERIFIED: 0.3,
            SourceQuality.LOW: 0.1,
        }
        return (
            weights["authority"] * self.authority_score +
            weights["freshness"] * self.freshness_score +
            weights["coverage"] * self.coverage_score +
            weights["quality"] * quality_scores.get(self.quality, 0.5)
        )


class SourceIntelligence:
    """
    Intelligent source analysis and profiling.
    """
    
    # Domain patterns
    DOMAIN_PATTERNS = {
        ContentDomain.TECHNICAL: [
            r"github\.com", r"stackoverflow\.com", r"docs\.", r"\.dev$",
            r"developer\.", r"api\.", r"\.io$",
        ],
        ContentDomain.ACADEMIC: [
            r"arxiv\.org", r"\.edu$", r"scholar\.google", r"pubmed",
            r"researchgate", r"academia\.edu",
        ],
        ContentDomain.NEWS: [
            r"news\.", r"\.news$", r"bbc\.com", r"cnn\.com", r"reuters",
        ],
        ContentDomain.REFERENCE: [
            r"wikipedia\.org", r"wikidata\.org", r"britannica",
        ],
    }
    
    # Quality patterns
    QUALITY_PATTERNS = {
        SourceQuality.AUTHORITATIVE: [
            r"\.gov$", r"\.edu$", r"official", r"primary",
        ],
        SourceQuality.VERIFIED: [
            r"peer-reviewed", r"journal\.", r"arxiv\.org",
        ],
    }
    
    def __init__(self):
        self.profiles: dict[str, SourceProfile] = {}
    
    def analyze_source(self, uri: str, content: str | None = None) -> SourceProfile:
        """
        Analyze a source and build intelligence profile.
        """
        # Check cache
        cache_key = self._cache_key(uri)
        if cache_key in self.profiles:
            return self.profiles[cache_key]
        
        profile = SourceProfile(uri=uri)
        
        # Classify domain
        profile.domain = self._classify_domain(uri)
        
        # Assess quality
        profile.quality = self._assess_quality(uri, content)
        
        # Compute scores
        profile.authority_score = self._compute_authority(uri, profile.domain)
        profile.freshness_score = self._compute_freshness(uri)
        profile.coverage_score = self._compute_coverage(content) if content else 0.5
        
        # Extract expertise areas
        if content:
            profile.expertise_areas = self._extract_expertise(content)
        
        profile.last_verified = datetime.utcnow()
        
        # Cache
        self.profiles[cache_key] = profile
        return profile
    
    def _cache_key(self, uri: str) -> str:
        """Generate cache key for URI."""
        parsed = urlparse(uri)
        return hashlib.md5(f"{parsed.netloc}{parsed.path}".encode()).hexdigest()[:16]
    
    def _classify_domain(self, uri: str) -> ContentDomain:
        """Classify content domain from URI."""
        for domain, patterns in self.DOMAIN_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, uri, re.IGNORECASE):
                    return domain
        return ContentDomain.UNKNOWN
    
    def _assess_quality(self, uri: str, content: str | None) -> SourceQuality:
        """Assess source quality."""
        for quality, patterns in self.QUALITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, uri, re.IGNORECASE):
                    return quality
        
        # Domain-based quality
        domain = urlparse(uri).netloc.lower()
        if domain.endswith((".gov", ".edu")):
            return SourceQuality.AUTHORITATIVE
        if domain.endswith(".org"):
            return SourceQuality.REPUTABLE
        
        return SourceQuality.UNVERIFIED
    
    def _compute_authority(self, uri: str, domain: ContentDomain) -> float:
        """Compute authority score."""
        base = 0.5
        
        # Domain bonus
        domain_bonuses = {
            ContentDomain.ACADEMIC: 0.3,
            ContentDomain.REFERENCE: 0.25,
            ContentDomain.TECHNICAL: 0.2,
        }
        base += domain_bonuses.get(domain, 0)
        
        # TLD bonus
        parsed = urlparse(uri)
        if parsed.netloc.endswith(".edu"):
            base += 0.15
        elif parsed.netloc.endswith(".gov"):
            base += 0.2
        
        return min(base, 1.0)
    
    def _compute_freshness(self, uri: str) -> float:
        """Compute freshness score (placeholder)."""
        # Would check Last-Modified headers, publication dates, etc.
        return 0.7
    
    def _compute_coverage(self, content: str) -> float:
        """Compute coverage score from content depth."""
        if not content:
            return 0.5
        
        # Heuristics: longer = more comprehensive
        word_count = len(content.split())
        if word_count > 5000:
            return 0.9
        elif word_count > 2000:
            return 0.7
        elif word_count > 500:
            return 0.5
        else:
            return 0.3
    
    def _extract_expertise(self, content: str) -> list[str]:
        """Extract expertise areas from content."""
        # Simple keyword extraction (would use NLP in production)
        tech_terms = [
            "machine learning", "artificial intelligence", "neural network",
            "python", "javascript", "kubernetes", "docker", "api",
            "database", "algorithm", "security", "cloud",
        ]
        
        found = []
        content_lower = content.lower()
        for term in tech_terms:
            if term in content_lower:
                found.append(term)
        
        return found[:10]
    
    def get_profile(self, uri: str) -> SourceProfile | None:
        """Get cached profile for URI."""
        return self.profiles.get(self._cache_key(uri))
    
    def rank_sources(
        self,
        uris: list[str],
        for_domain: ContentDomain | None = None,
    ) -> list[tuple[str, float]]:
        """Rank sources by reliability."""
        ranked = []
        
        for uri in uris:
            profile = self.profiles.get(self._cache_key(uri))
            if profile:
                score = profile.overall_score()
                # Domain match bonus
                if for_domain and profile.domain == for_domain:
                    score += 0.1
                ranked.append((uri, min(score, 1.0)))
            else:
                ranked.append((uri, 0.3))  # Unknown = low score
        
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked


@dataclass
class ContentSignature:
    """Signature for tracking content evolution."""
    content_hash: str
    structure_hash: str
    key_terms: list[str]
    word_count: int
    timestamp: datetime


class ContentTracker:
    """
    Tracks content evolution across versions.
    """
    
    def __init__(self):
        self.signatures: dict[str, list[ContentSignature]] = {}
    
    def record(self, uri: str, content: str) -> ContentSignature:
        """Record content signature."""
        sig = ContentSignature(
            content_hash=hashlib.sha256(content.encode()).hexdigest()[:16],
            structure_hash=self._structure_hash(content),
            key_terms=self._extract_terms(content),
            word_count=len(content.split()),
            timestamp=datetime.utcnow(),
        )
        
        if uri not in self.signatures:
            self.signatures[uri] = []
        self.signatures[uri].append(sig)
        
        return sig
    
    def has_changed(self, uri: str, content: str) -> bool:
        """Check if content has changed since last record."""
        if uri not in self.signatures:
            return True
        
        current_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return current_hash != self.signatures[uri][-1].content_hash
    
    def get_evolution(self, uri: str) -> list[dict[str, Any]]:
        """Get content evolution history."""
        if uri not in self.signatures:
            return []
        
        return [
            {
                "timestamp": sig.timestamp.isoformat(),
                "word_count": sig.word_count,
                "key_terms": sig.key_terms[:5],
            }
            for sig in self.signatures[uri]
        ]
    
    def _structure_hash(self, content: str) -> str:
        """Hash content structure (headers, sections)."""
        lines = content.split("\n")
        structure = [l[:10] for l in lines if l.startswith("#") or l.startswith("##")]
        return hashlib.md5("".join(structure).encode()).hexdigest()[:8]
    
    def _extract_terms(self, content: str) -> list[str]:
        """Extract key terms."""
        words = re.findall(r'\b[A-Z][a-z]+\b', content)
        freq: dict[str, int] = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        sorted_terms = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [t[0] for t in sorted_terms[:10]]
