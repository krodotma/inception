"""
ENTELECHEIA+ Reactive Surface — Core Implementation

The Reactive Surface that intelligently processes any input blob
(URL, repo, video, article, idea, plan, project, domain).

Phase 1: Steps 21-50
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, TypeVar
from urllib.parse import urlparse
import re


# =============================================================================
# BLOB TYPE ENUM (Step 21)
# =============================================================================

class BlobType(Enum):
    """Types of input blobs the surface can process."""
    
    URL = auto()           # Web page, API endpoint
    REPOSITORY = auto()    # GitHub, GitLab, Bitbucket
    VIDEO = auto()         # YouTube, Vimeo, local video
    ARTICLE = auto()       # Blog, paper, documentation
    IDEA = auto()          # Natural language concept
    PLAN = auto()          # Structured intent
    PROJECT = auto()       # Active work context
    DOMAIN = auto()        # Knowledge area
    CODE = auto()          # Code snippet or file
    DATA = auto()          # Structured data (JSON, CSV)
    UNKNOWN = auto()       # Unclassified


# =============================================================================
# BLOB DETECTORS (Steps 22-29)
# =============================================================================

@dataclass
class DetectionResult:
    """Result of blob type detection."""
    
    blob_type: BlobType
    confidence: float  # 0.0 to 1.0
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class BlobDetector:
    """Base class for blob type detectors."""
    
    def detect(self, content: str) -> DetectionResult | None:
        """Detect if content matches this blob type."""
        raise NotImplementedError


class URLDetector(BlobDetector):
    """Detect URLs (Step 22)."""
    
    URL_PATTERN = re.compile(
        r'^https?://[^\s<>"{}|\\^`\[\]]+$',
        re.IGNORECASE
    )
    
    def detect(self, content: str) -> DetectionResult | None:
        content = content.strip()
        if self.URL_PATTERN.match(content):
            parsed = urlparse(content)
            return DetectionResult(
                blob_type=BlobType.URL,
                confidence=0.95,
                evidence=["Matches URL pattern"],
                metadata={
                    "scheme": parsed.scheme,
                    "domain": parsed.netloc,
                    "path": parsed.path,
                }
            )
        return None


class RepositoryDetector(BlobDetector):
    """Detect repository URLs (Step 23)."""
    
    REPO_PATTERNS = [
        (re.compile(r'github\.com/[\w-]+/[\w.-]+', re.I), "github"),
        (re.compile(r'gitlab\.com/[\w-]+/[\w.-]+', re.I), "gitlab"),
        (re.compile(r'bitbucket\.org/[\w-]+/[\w.-]+', re.I), "bitbucket"),
    ]
    
    def detect(self, content: str) -> DetectionResult | None:
        content = content.strip()
        for pattern, platform in self.REPO_PATTERNS:
            if pattern.search(content):
                return DetectionResult(
                    blob_type=BlobType.REPOSITORY,
                    confidence=0.98,
                    evidence=[f"Matches {platform} repository pattern"],
                    metadata={"platform": platform}
                )
        return None


class VideoDetector(BlobDetector):
    """Detect video URLs (Step 24)."""
    
    VIDEO_PATTERNS = [
        (re.compile(r'youtube\.com/watch\?v=[\w-]+', re.I), "youtube"),
        (re.compile(r'youtu\.be/[\w-]+', re.I), "youtube"),
        (re.compile(r'vimeo\.com/\d+', re.I), "vimeo"),
        (re.compile(r'\.(mp4|webm|mov|avi|mkv)$', re.I), "local"),
    ]
    
    def detect(self, content: str) -> DetectionResult | None:
        content = content.strip()
        for pattern, platform in self.VIDEO_PATTERNS:
            if pattern.search(content):
                return DetectionResult(
                    blob_type=BlobType.VIDEO,
                    confidence=0.95,
                    evidence=[f"Matches {platform} video pattern"],
                    metadata={"platform": platform}
                )
        return None


class ArticleDetector(BlobDetector):
    """Detect articles/documentation (Step 25)."""
    
    # Article indicators
    ARTICLE_KEYWORDS = [
        "abstract", "introduction", "conclusion", "references",
        "summary", "overview", "documentation", "guide",
    ]
    
    def detect(self, content: str) -> DetectionResult | None:
        content_lower = content.lower()
        
        # Check for document structure
        matches = sum(1 for kw in self.ARTICLE_KEYWORDS if kw in content_lower)
        
        if matches >= 2 or len(content) > 500:
            return DetectionResult(
                blob_type=BlobType.ARTICLE,
                confidence=0.6 + (matches * 0.1),
                evidence=[f"Contains {matches} article keywords"],
                metadata={"keyword_count": matches}
            )
        return None


class IdeaDetector(BlobDetector):
    """Detect natural language ideas (Step 26)."""
    
    IDEA_INDICATORS = [
        "what if", "i think", "maybe we could", "an idea",
        "consider", "imagine", "suppose", "how about",
    ]
    
    def detect(self, content: str) -> DetectionResult | None:
        content_lower = content.lower()
        
        for indicator in self.IDEA_INDICATORS:
            if indicator in content_lower:
                return DetectionResult(
                    blob_type=BlobType.IDEA,
                    confidence=0.75,
                    evidence=[f"Contains idea indicator: '{indicator}'"],
                    metadata={"indicator": indicator}
                )
        
        # Default to idea if short and no other match
        if 10 < len(content) < 500 and not content.startswith("http"):
            return DetectionResult(
                blob_type=BlobType.IDEA,
                confidence=0.5,
                evidence=["Short text, defaulting to idea"],
                metadata={}
            )
        return None


class PlanDetector(BlobDetector):
    """Detect structured plans (Step 27)."""
    
    PLAN_INDICATORS = [
        "step 1", "phase 1", "first,", "then,", "finally,",
        "objective:", "goal:", "milestone", "timeline",
        "- [ ]", "1.", "2.", "3.",
    ]
    
    def detect(self, content: str) -> DetectionResult | None:
        content_lower = content.lower()
        
        matches = sum(1 for ind in self.PLAN_INDICATORS if ind in content_lower)
        
        if matches >= 2:
            return DetectionResult(
                blob_type=BlobType.PLAN,
                confidence=0.7 + (matches * 0.05),
                evidence=[f"Contains {matches} plan indicators"],
                metadata={"indicator_count": matches}
            )
        return None


class ProjectDetector(BlobDetector):
    """Detect project contexts (Step 28)."""
    
    PROJECT_INDICATORS = [
        "project:", "team:", "deadline:", "budget:",
        "sprint", "kanban", "backlog", "release",
    ]
    
    def detect(self, content: str) -> DetectionResult | None:
        content_lower = content.lower()
        
        matches = sum(1 for ind in self.PROJECT_INDICATORS if ind in content_lower)
        
        if matches >= 1:
            return DetectionResult(
                blob_type=BlobType.PROJECT,
                confidence=0.7 + (matches * 0.1),
                evidence=[f"Contains {matches} project indicators"],
                metadata={"indicator_count": matches}
            )
        return None


class DomainDetector(BlobDetector):
    """Detect knowledge domains (Step 29)."""
    
    DOMAIN_PATTERNS = [
        r"domain:\s*(\w+)",
        r"field of\s+(\w+)",
        r"area:\s*(\w+)",
    ]
    
    def detect(self, content: str) -> DetectionResult | None:
        content_lower = content.lower()
        
        for pattern in self.DOMAIN_PATTERNS:
            match = re.search(pattern, content_lower)
            if match:
                return DetectionResult(
                    blob_type=BlobType.DOMAIN,
                    confidence=0.8,
                    evidence=[f"Matches domain pattern"],
                    metadata={"domain_name": match.group(1)}
                )
        return None


# =============================================================================
# UNIFIED BLOB CLASSIFIER (Step 30)
# =============================================================================

class BlobClassifier:
    """
    Unified classifier for all blob types.
    
    Runs all detectors and returns the highest-confidence match.
    """
    
    def __init__(self):
        # Order matters: more specific detectors first
        self.detectors: list[BlobDetector] = [
            RepositoryDetector(),  # Repo before URL
            VideoDetector(),       # Video before URL
            URLDetector(),
            PlanDetector(),
            ProjectDetector(),
            DomainDetector(),
            ArticleDetector(),
            IdeaDetector(),        # Fallback
        ]
    
    def classify(self, content: str) -> DetectionResult:
        """
        Classify content into a blob type.
        
        Returns the highest-confidence detection.
        """
        results: list[DetectionResult] = []
        
        for detector in self.detectors:
            result = detector.detect(content)
            if result:
                results.append(result)
        
        if not results:
            return DetectionResult(
                blob_type=BlobType.UNKNOWN,
                confidence=0.0,
                evidence=["No detector matched"],
            )
        
        # Return highest confidence
        return max(results, key=lambda r: r.confidence)
    
    def classify_all(self, content: str) -> list[DetectionResult]:
        """Return all matching detections, sorted by confidence."""
        results = []
        for detector in self.detectors:
            result = detector.detect(content)
            if result:
                results.append(result)
        return sorted(results, key=lambda r: -r.confidence)


# =============================================================================
# NORMALIZED BLOB (Step 31)
# =============================================================================

@dataclass
class NormalizedBlob:
    """A normalized representation of any input blob."""
    
    blob_id: str
    blob_type: BlobType
    raw_content: str
    normalized_content: str
    
    # Classification
    confidence: float
    evidence: list[str]
    
    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: datetime | None = None
    
    # Processing state
    state: str = "pending"  # pending, processing, processed, failed
    
    # Co-objects (populated during inference)
    co_objects: list[str] = field(default_factory=list)


# =============================================================================
# INPUT NORMALIZER (Step 40)
# =============================================================================

class InputNormalizer:
    """
    Normalizes input blobs into a standard format.
    """
    
    def __init__(self):
        from uuid import uuid4
        self._uuid = uuid4
    
    def normalize(self, content: str, detection: DetectionResult) -> NormalizedBlob:
        """Normalize content based on its detected type."""
        blob_id = f"blob_{self._uuid().hex[:12]}"
        
        # Type-specific normalization
        normalized = content.strip()
        
        if detection.blob_type == BlobType.URL:
            normalized = self._normalize_url(content)
        elif detection.blob_type == BlobType.REPOSITORY:
            normalized = self._normalize_repo(content)
        elif detection.blob_type == BlobType.VIDEO:
            normalized = self._normalize_video(content)
        elif detection.blob_type == BlobType.ARTICLE:
            normalized = self._normalize_article(content)
        elif detection.blob_type in (BlobType.IDEA, BlobType.PLAN):
            normalized = self._normalize_text(content)
        
        return NormalizedBlob(
            blob_id=blob_id,
            blob_type=detection.blob_type,
            raw_content=content,
            normalized_content=normalized,
            confidence=detection.confidence,
            evidence=detection.evidence,
            metadata=detection.metadata,
        )
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL to canonical form."""
        url = url.strip()
        # Remove trailing slashes
        url = url.rstrip("/")
        # Ensure https
        if url.startswith("http://"):
            url = "https://" + url[7:]
        return url
    
    def _normalize_repo(self, url: str) -> str:
        """Extract canonical repo identifier."""
        # Extract owner/repo from GitHub URL
        match = re.search(r'github\.com/([\w-]+/[\w.-]+)', url)
        if match:
            return f"github:{match.group(1)}"
        return url
    
    def _normalize_video(self, url: str) -> str:
        """Extract canonical video identifier."""
        # Extract YouTube video ID
        match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)', url)
        if match:
            return f"youtube:{match.group(1)}"
        return url
    
    def _normalize_article(self, content: str) -> str:
        """Normalize article content."""
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        return content.strip()
    
    def _normalize_text(self, content: str) -> str:
        """Normalize general text."""
        return content.strip()


# =============================================================================
# REACTIVE SURFACE (Steps 41-50)
# =============================================================================

@dataclass
class SurfaceEvent:
    """An event emitted by the reactive surface."""
    
    event_type: str  # blob_added, blob_processed, coobject_inferred, error
    blob_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: dict[str, Any] = field(default_factory=dict)


class ReactiveSurface:
    """
    The ENTELECHEIA+ Reactive Knowledge Surface.
    
    Accepts any input blob and intelligently processes it
    through rheomode transformation and co-object inference.
    """
    
    def __init__(self, session_id: str | None = None):
        from uuid import uuid4
        self.session_id = session_id or f"session_{uuid4().hex[:8]}"
        self.classifier = BlobClassifier()
        self.normalizer = InputNormalizer()
        
        # State
        self._blobs: dict[str, NormalizedBlob] = {}
        self._events: list[SurfaceEvent] = []
        self._listeners: list[Callable[[SurfaceEvent], None]] = []
    
    def __add__(self, content: str) -> NormalizedBlob:
        """
        The + operator: Add a blob to the surface.
        
        Usage: surface + "https://github.com/user/repo"
        """
        return self.add(content)
    
    def add(self, content: str) -> NormalizedBlob:
        """
        Add content to the reactive surface.
        
        Classifies, normalizes, and queues for processing.
        """
        # Classify
        detection = self.classifier.classify(content)
        
        # Normalize
        blob = self.normalizer.normalize(content, detection)
        
        # Store
        self._blobs[blob.blob_id] = blob
        
        # Emit event
        self._emit(SurfaceEvent(
            event_type="blob_added",
            blob_id=blob.blob_id,
            data={
                "blob_type": blob.blob_type.name,
                "confidence": blob.confidence,
            }
        ))
        
        return blob
    
    def get(self, blob_id: str) -> NormalizedBlob | None:
        """Get a blob by ID."""
        return self._blobs.get(blob_id)
    
    def list_blobs(self, blob_type: BlobType | None = None) -> list[NormalizedBlob]:
        """List all blobs, optionally filtered by type."""
        blobs = list(self._blobs.values())
        if blob_type:
            blobs = [b for b in blobs if b.blob_type == blob_type]
        return blobs
    
    def on(self, listener: Callable[[SurfaceEvent], None]) -> None:
        """Register an event listener."""
        self._listeners.append(listener)
    
    def _emit(self, event: SurfaceEvent) -> None:
        """Emit an event to all listeners."""
        self._events.append(event)
        for listener in self._listeners:
            try:
                listener(event)
            except Exception:
                pass  # Don't let listener errors break the surface
    
    def get_events(self, n: int | None = None) -> list[SurfaceEvent]:
        """Get recent events."""
        if n is None:
            return self._events
        return self._events[-n:]
    
    def get_state(self) -> dict[str, Any]:
        """Get current surface state."""
        type_counts = {}
        for blob in self._blobs.values():
            name = blob.blob_type.name
            type_counts[name] = type_counts.get(name, 0) + 1
        
        return {
            "session_id": self.session_id,
            "blob_count": len(self._blobs),
            "event_count": len(self._events),
            "type_distribution": type_counts,
        }
