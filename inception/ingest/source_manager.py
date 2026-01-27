"""
Source manager for tracking ingestion state.

Handles watermarks, incremental updates, and batch processing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlparse

from inception.config import get_config
from inception.db import InceptionDB, get_db
from inception.db.records import SourceRecord, IngestPolicy
from inception.db.keys import SourceType
from inception.db.graphtag import compute_graphtag
from inception.ingest.youtube import parse_youtube_url


@dataclass
class SourceFeed:
    """A feed of sources to ingest."""
    
    feed_type: str  # 'youtube_channel', 'youtube_playlist', 'site', 'batch'
    uri: str
    
    # Filters
    since: datetime | None = None
    until: datetime | None = None
    topic_rules: list[str] = field(default_factory=list)
    
    # Processing state
    last_processed: datetime | None = None
    watermark: str | None = None  # Last processed item identifier


@dataclass
class IngestJob:
    """A single ingestion job."""
    
    uri: str
    source_type: SourceType
    
    # Options
    since: datetime | None = None
    until: datetime | None = None
    topics: list[str] = field(default_factory=list)
    profile: str | None = None
    
    # State
    status: str = "pending"  # pending, running, completed, failed
    error: str | None = None
    source_nid: int | None = None


class SourceManager:
    """
    Manager for source ingestion and tracking.
    
    Handles:
    - Determining source types from URIs
    - Tracking ingestion state (watermarks)
    - Managing incremental updates
    - Batch processing
    """
    
    def __init__(self, db: InceptionDB | None = None):
        self.db = db or get_db()
        self._watermarks: dict[str, dict[str, Any]] = {}
    
    def detect_source_type(self, uri: str) -> SourceType:
        """
        Detect the type of source from a URI.
        
        Args:
            uri: URI or file path
        
        Returns:
            SourceType enum value
        """
        # Check if it's a file path
        path = Path(uri)
        if path.exists():
            ext = path.suffix.lower()
            ext_map = {
                ".pdf": SourceType.PDF,
                ".docx": SourceType.DOCX,
                ".doc": SourceType.DOCX,
                ".pptx": SourceType.PPTX,
                ".ppt": SourceType.PPTX,
                ".xlsx": SourceType.XLSX,
                ".xls": SourceType.XLSX,
                ".epub": SourceType.EPUB,
            }
            if ext in ext_map:
                return ext_map[ext]
            
            # Check for video/audio files
            video_exts = {".mp4", ".mkv", ".avi", ".mov", ".webm"}
            audio_exts = {".mp3", ".wav", ".m4a", ".flac", ".ogg"}
            if ext in video_exts:
                return SourceType.LOCAL_VIDEO
            if ext in audio_exts:
                return SourceType.LOCAL_AUDIO
        
        # Check for URLs
        parsed = urlparse(uri)
        
        if parsed.hostname in ("youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"):
            yt_info = parse_youtube_url(uri)
            if yt_info["type"] == "video":
                return SourceType.YOUTUBE_VIDEO
            elif yt_info["type"] == "playlist":
                return SourceType.YOUTUBE_PLAYLIST
            elif yt_info["type"] == "channel":
                return SourceType.YOUTUBE_CHANNEL
        
        if parsed.scheme in ("http", "https"):
            return SourceType.WEB_PAGE
        
        raise ValueError(f"Cannot determine source type for: {uri}")
    
    def create_source(
        self,
        uri: str,
        source_type: SourceType | None = None,
        title: str | None = None,
        policy: IngestPolicy | None = None,
        parent_nid: int | None = None,
    ) -> SourceRecord:
        """
        Create a new source record.
        
        Args:
            uri: Source URI or path
            source_type: Override detected source type
            title: Optional title
            policy: Ingestion policy
            parent_nid: Parent source NID (for channel/playlist items)
        
        Returns:
            Created SourceRecord
        """
        if source_type is None:
            source_type = self.detect_source_type(uri)
        
        if policy is None:
            policy = IngestPolicy()
        
        nid = self.db.allocate_nid()
        
        source = SourceRecord(
            nid=nid,
            source_type=source_type,
            uri=uri,
            title=title,
            ingest_policy=policy,
            parent_nid=parent_nid,
        )
        
        self.db.put_source(source)
        
        return source
    
    def get_or_create_source(
        self,
        uri: str,
        source_type: SourceType | None = None,
    ) -> tuple[SourceRecord, bool]:
        """
        Get existing source or create new one.
        
        Args:
            uri: Source URI
            source_type: Optional source type
        
        Returns:
            Tuple of (SourceRecord, is_new)
        """
        # Generate graphtag for deduplication
        graphtag = compute_graphtag({"uri": uri})
        
        # Check if exists
        result = self.db.get_nid_by_graphtag(graphtag)
        if result:
            _, nid = result
            source = self.db.get_source(nid)
            if source:
                return source, False
        
        # Create new
        source = self.create_source(uri, source_type)
        
        # Store graphtag mapping
        from inception.db.keys import ObjectType
        self.db.put_graphtag(graphtag, ObjectType.SOURCE, source.nid)
        
        return source, True
    
    def update_watermark(
        self,
        feed_uri: str,
        watermark: str,
        timestamp: datetime | None = None,
    ) -> None:
        """
        Update the watermark for a feed.
        
        Args:
            feed_uri: Feed URI (channel, playlist, site)
            watermark: New watermark value
            timestamp: Timestamp for the watermark
        """
        self._watermarks[feed_uri] = {
            "watermark": watermark,
            "timestamp": timestamp or datetime.utcnow(),
        }
    
    def get_watermark(self, feed_uri: str) -> dict[str, Any] | None:
        """
        Get the watermark for a feed.
        
        Args:
            feed_uri: Feed URI
        
        Returns:
            Watermark dict with 'watermark' and 'timestamp' keys, or None
        """
        return self._watermarks.get(feed_uri)
    
    def should_process(
        self,
        uri: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> bool:
        """
        Check if a source should be processed based on watermarks and dates.
        
        Args:
            uri: Source URI
            since: Only process if after this date
            until: Only process if before this date
        
        Returns:
            True if should process
        """
        # Check if already ingested
        graphtag = compute_graphtag({"uri": uri})
        result = self.db.get_nid_by_graphtag(graphtag)
        if result:
            # Already exists - could check for updates here
            return False
        
        return True
    
    def iter_pending_sources(
        self,
        feed: SourceFeed,
        max_items: int | None = None,
    ) -> Iterator[str]:
        """
        Iterate over pending sources in a feed.
        
        Args:
            feed: SourceFeed to process
            max_items: Maximum items to yield
        
        Yields:
            URIs of sources to process
        """
        # This would be implemented differently for each feed type
        # For now, just a placeholder
        count = 0
        
        if feed.feed_type == "youtube_channel":
            from inception.ingest.youtube import list_channel_videos
            
            videos = list_channel_videos(
                feed.uri,
                since=feed.since,
                until=feed.until,
                max_videos=max_items,
            )
            
            for video in videos:
                if self.should_process(video["url"], feed.since, feed.until):
                    yield video["url"]
                    count += 1
                    if max_items and count >= max_items:
                        return
        
        elif feed.feed_type == "youtube_playlist":
            from inception.ingest.youtube import list_playlist_videos
            
            videos = list_playlist_videos(feed.uri, max_videos=max_items)
            
            for video in videos:
                if self.should_process(video["url"]):
                    yield video["url"]
                    count += 1
                    if max_items and count >= max_items:
                        return


def parse_batch_file(path: Path) -> list[IngestJob]:
    """
    Parse a batch ingestion file (JSONL format).
    
    Each line should contain JSON with:
    - uri: Required source URI
    - since: Optional start date (YYYY-MM-DD)
    - until: Optional end date (YYYY-MM-DD)
    - topics: Optional list of topic filters
    - profile: Optional ingestion profile
    
    Args:
        path: Path to JSONL file
    
    Returns:
        List of IngestJob objects
    """
    import json
    
    jobs = []
    
    with open(path) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {line_num}: {e}")
            
            if "uri" not in data:
                raise ValueError(f"Missing 'uri' on line {line_num}")
            
            uri = data["uri"]
            
            # Parse dates
            since = None
            if data.get("since"):
                since = datetime.strptime(data["since"], "%Y-%m-%d")
            
            until = None
            if data.get("until"):
                until = datetime.strptime(data["until"], "%Y-%m-%d")
            
            # Try to detect source type
            try:
                sm = SourceManager()
                source_type = sm.detect_source_type(uri)
            except ValueError:
                source_type = SourceType.WEB_PAGE  # Default
            
            job = IngestJob(
                uri=uri,
                source_type=source_type,
                since=since,
                until=until,
                topics=data.get("topics", []),
                profile=data.get("profile"),
            )
            jobs.append(job)
    
    return jobs
