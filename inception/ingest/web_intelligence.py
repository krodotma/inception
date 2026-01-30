"""
Web Intelligence Layer - Swarm Track 5

Enhanced web content understanding with structure analysis.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)


class PageType(Enum):
    """Web page content types."""
    ARTICLE = "article"
    DOCUMENTATION = "documentation" 
    API_REFERENCE = "api_reference"
    TUTORIAL = "tutorial"
    BLOG = "blog"
    LANDING = "landing"
    PRODUCT = "product"
    FORUM = "forum"
    NEWS = "news"
    UNKNOWN = "unknown"


class ContentReliability(Enum):
    """Content reliability levels."""
    AUTHORITATIVE = "authoritative"
    VERIFIED = "verified"
    STANDARD = "standard"
    USER_GENERATED = "user_generated"
    UNKNOWN = "unknown"


@dataclass
class StructuredSection:
    """A structured section from a web page."""
    title: str
    level: int  # Heading level (1-6)
    content: str
    subsections: list["StructuredSection"] = field(default_factory=list)
    code_blocks: list[dict] = field(default_factory=list)
    lists: list[list[str]] = field(default_factory=list)
    tables: list[list[list[str]]] = field(default_factory=list)


@dataclass 
class WebIntelligence:
    """Intelligence extracted from web content."""
    url: str
    page_type: PageType = PageType.UNKNOWN
    reliability: ContentReliability = ContentReliability.UNKNOWN
    
    # Structure
    sections: list[StructuredSection] = field(default_factory=list)
    toc: list[dict] = field(default_factory=list)
    
    # Key content
    main_topic: str = ""
    key_concepts: list[str] = field(default_factory=list)
    definitions: list[dict] = field(default_factory=list)
    
    # Code analysis
    code_snippets: list[dict] = field(default_factory=list)
    detected_languages: list[str] = field(default_factory=list)
    
    # Links
    internal_links: list[str] = field(default_factory=list)
    external_links: list[str] = field(default_factory=list)
    citations: list[dict] = field(default_factory=list)
    
    # Metadata
    word_count: int = 0
    reading_time_minutes: float = 0.0
    last_modified: datetime | None = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "page_type": self.page_type.value,
            "reliability": self.reliability.value,
            "main_topic": self.main_topic,
            "key_concepts": self.key_concepts,
            "code_snippets_count": len(self.code_snippets),
            "word_count": self.word_count,
        }


class WebAnalyzer:
    """
    Analyze web content for structured knowledge extraction.
    """
    
    # Page type detection patterns
    TYPE_PATTERNS = {
        PageType.DOCUMENTATION: [
            r"documentation", r"docs\.", r"/docs/", r"readme",
            r"api\s*reference", r"getting\s*started",
        ],
        PageType.API_REFERENCE: [
            r"api\s*reference", r"/api/", r"endpoints?",
            r"parameters?", r"response\s*format",
        ],
        PageType.TUTORIAL: [
            r"tutorial", r"how\s*to", r"step\s*by\s*step",
            r"guide", r"walkthrough",
        ],
        PageType.BLOG: [
            r"blog", r"/posts?/", r"article",
        ],
        PageType.FORUM: [
            r"forum", r"discussion", r"stackoverflow",
            r"reddit\.com", r"/questions?/",
        ],
        PageType.NEWS: [
            r"news", r"article", r"breaking",
        ],
    }
    
    # Reliability patterns
    RELIABILITY_PATTERNS = {
        ContentReliability.AUTHORITATIVE: [
            r"\.gov$", r"\.edu$", r"official",
        ],
        ContentReliability.VERIFIED: [
            r"peer.?reviewed", r"journal", r"published",
        ],
    }
    
    def __init__(self):
        self._cache: dict[str, WebIntelligence] = {}
    
    def analyze(
        self,
        url: str,
        html: str | None = None,
        markdown: str | None = None,
        text: str | None = None,
    ) -> WebIntelligence:
        """
        Analyze web content.
        
        Args:
            url: Page URL
            html: Raw HTML (optional)
            markdown: Extracted markdown (optional)
            text: Plain text content (optional)
        
        Returns:
            WebIntelligence with structured analysis
        """
        content = markdown or text or ""
        
        intel = WebIntelligence(url=url)
        
        # Detect page type
        intel.page_type = self._detect_page_type(url, content)
        
        # Assess reliability
        intel.reliability = self._assess_reliability(url, content)
        
        # Extract structure
        if content:
            intel.sections = self._extract_sections(content)
            intel.toc = self._build_toc(intel.sections)
            
            # Extract key content
            intel.main_topic = self._extract_main_topic(content, intel.sections)
            intel.key_concepts = self._extract_concepts(content)
            intel.definitions = self._extract_definitions(content)
            
            # Code analysis
            intel.code_snippets = self._extract_code(content)
            intel.detected_languages = list(set(
                c.get("language", "unknown") for c in intel.code_snippets
            ))
            
            # Links
            intel.internal_links, intel.external_links = self._categorize_links(
                url, content
            )
            
            # Metrics
            intel.word_count = len(content.split())
            intel.reading_time_minutes = intel.word_count / 200  # 200 WPM
        
        return intel
    
    def _detect_page_type(self, url: str, content: str) -> PageType:
        """Detect page type from URL and content."""
        combined = f"{url} {content[:1000]}".lower()
        
        for page_type, patterns in self.TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, combined, re.I):
                    return page_type
        
        return PageType.UNKNOWN
    
    def _assess_reliability(self, url: str, content: str) -> ContentReliability:
        """Assess content reliability."""
        domain = urlparse(url).netloc.lower()
        
        for reliability, patterns in self.RELIABILITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, domain):
                    return reliability
        
        # Check for user-generated indicators
        if re.search(r"stackoverflow|reddit|quora|forum", domain):
            return ContentReliability.USER_GENERATED
        
        return ContentReliability.STANDARD
    
    def _extract_sections(self, content: str) -> list[StructuredSection]:
        """Extract document sections."""
        sections = []
        lines = content.split("\n")
        
        current_section: StructuredSection | None = None
        content_buffer = []
        
        for line in lines:
            # Check for heading
            heading_match = re.match(r"^(#{1,6})\s+(.+)", line)
            
            if heading_match:
                # Save previous section
                if current_section:
                    current_section.content = "\n".join(content_buffer).strip()
                    sections.append(current_section)
                
                # Start new section
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                current_section = StructuredSection(title=title, level=level, content="")
                content_buffer = []
            else:
                content_buffer.append(line)
        
        # Save last section
        if current_section:
            current_section.content = "\n".join(content_buffer).strip()
            sections.append(current_section)
        
        return sections
    
    def _build_toc(self, sections: list[StructuredSection]) -> list[dict]:
        """Build table of contents."""
        return [
            {"title": s.title, "level": s.level}
            for s in sections
        ]
    
    def _extract_main_topic(
        self,
        content: str,
        sections: list[StructuredSection],
    ) -> str:
        """Extract main topic."""
        if sections:
            return sections[0].title
        
        # Fallback to first significant line
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        return lines[0][:100] if lines else ""
    
    def _extract_concepts(self, content: str) -> list[str]:
        """Extract key concepts (capitalized terms, definitions, etc.)."""
        concepts = []
        
        # Find capitalized multi-word terms
        pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"
        for match in re.finditer(pattern, content):
            term = match.group(1)
            if term not in concepts and len(term) < 50:
                concepts.append(term)
        
        # Find quoted terms
        for match in re.finditer(r'"([^"]{3,30})"', content):
            term = match.group(1)
            if term not in concepts:
                concepts.append(term)
        
        return concepts[:20]
    
    def _extract_definitions(self, content: str) -> list[dict]:
        """Extract definitions."""
        definitions = []
        
        patterns = [
            r"(\w+)\s+is\s+(?:defined\s+as|a|an)\s+(.+?)\.(?:\s|$)",
            r"(\w+):\s+(.+?)\.(?:\s|$)",
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content, re.I):
                term = match.group(1)
                definition = match.group(2)[:200]
                if len(term) > 2 and len(definition) > 10:
                    definitions.append({
                        "term": term,
                        "definition": definition,
                    })
        
        return definitions[:10]
    
    def _extract_code(self, content: str) -> list[dict]:
        """Extract code blocks."""
        code_blocks = []
        
        # Fenced code blocks
        pattern = r"```(\w*)\n(.*?)```"
        for match in re.finditer(pattern, content, re.DOTALL):
            language = match.group(1) or "unknown"
            code = match.group(2).strip()
            code_blocks.append({
                "language": language,
                "code": code[:500],  # Limit size
                "lines": len(code.split("\n")),
            })
        
        return code_blocks
    
    def _categorize_links(
        self,
        base_url: str,
        content: str,
    ) -> tuple[list[str], list[str]]:
        """Categorize links as internal/external."""
        base_domain = urlparse(base_url).netloc
        
        internal = []
        external = []
        
        # Find markdown links
        for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", content):
            url = match.group(2)
            
            if url.startswith("#") or url.startswith("/"):
                internal.append(url)
            else:
                try:
                    parsed = urlparse(url)
                    if parsed.netloc == base_domain or not parsed.netloc:
                        internal.append(url)
                    else:
                        external.append(url)
                except Exception:
                    pass
        
        return internal[:50], external[:50]


@dataclass
class ContentDiff:
    """Diff between two versions of content."""
    added_sections: list[str] = field(default_factory=list)
    removed_sections: list[str] = field(default_factory=list)
    modified_sections: list[str] = field(default_factory=list)
    word_count_delta: int = 0
    significance: float = 0.0


class ContentDiffer:
    """
    Compare web content versions.
    """
    
    def diff(
        self,
        old_intel: WebIntelligence,
        new_intel: WebIntelligence,
    ) -> ContentDiff:
        """
        Compute diff between content versions.
        """
        result = ContentDiff()
        
        # Section comparison
        old_titles = {s.title for s in old_intel.sections}
        new_titles = {s.title for s in new_intel.sections}
        
        result.added_sections = list(new_titles - old_titles)
        result.removed_sections = list(old_titles - new_titles)
        
        # Find modified (same title, different content)
        old_map = {s.title: s.content for s in old_intel.sections}
        new_map = {s.title: s.content for s in new_intel.sections}
        
        for title in old_titles & new_titles:
            if old_map[title] != new_map[title]:
                result.modified_sections.append(title)
        
        # Word count delta
        result.word_count_delta = new_intel.word_count - old_intel.word_count
        
        # Compute significance
        total_changes = (
            len(result.added_sections) +
            len(result.removed_sections) +
            len(result.modified_sections)
        )
        total_sections = max(len(old_intel.sections), len(new_intel.sections), 1)
        result.significance = min(total_changes / total_sections, 1.0)
        
        return result
