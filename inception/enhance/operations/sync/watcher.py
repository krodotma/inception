"""
File watcher for incremental sync.

Uses filesystem polling for cross-platform compatibility.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event, Thread
from typing import Callable, Set

logger = logging.getLogger(__name__)


@dataclass
class WatchConfig:
    """Configuration for file watching."""
    
    watch_paths: list[Path]
    
    # File patterns
    include_extensions: Set[str] = field(default_factory=lambda: {
        ".mp4", ".mkv", ".avi", ".mov", ".webm",  # Video
        ".mp3", ".wav", ".m4a", ".flac",          # Audio
        ".pdf", ".epub", ".docx", ".txt",         # Documents
        ".html", ".htm", ".md",                   # Web
    })
    exclude_patterns: Set[str] = field(default_factory=lambda: {
        ".*",           # Hidden files
        "__pycache__",
        "node_modules",
        "*.tmp",
        "*.temp",
        "~$*",          # Office temp files
    })
    
    # Timing
    poll_interval: float = 1.0  # Seconds
    debounce_delay: float = 2.0  # Wait before processing
    
    # Limits
    max_file_size_mb: int = 2048  # 2GB limit
    
    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@dataclass
class WatchEvent:
    """Event from file watcher."""
    
    path: Path
    event_type: str  # "created", "modified", "deleted"
    timestamp: float
    size: int = 0


class FileWatcher:
    """
    File system watcher for detecting changes.
    
    Uses polling for maximum compatibility.
    Future: Add inotify/FSEvents support.
    """
    
    def __init__(
        self,
        config: WatchConfig,
        on_change: Callable[[WatchEvent], None] | None = None,
    ):
        """Initialize file watcher."""
        self.config = config
        self.on_change = on_change
        
        self._file_states: dict[Path, tuple[float, int]] = {}  # (mtime, size)
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._pending_events: dict[Path, WatchEvent] = {}
        self._pending_times: dict[Path, float] = {}
    
    def start(self) -> None:
        """Start watching in background thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("Watcher already running")
            return
        
        self._stop_event.clear()
        self._thread = Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        logger.info(f"Started watching {len(self.config.watch_paths)} paths")
    
    def stop(self) -> None:
        """Stop watching."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Stopped file watcher")
    
    def scan_once(self) -> list[WatchEvent]:
        """Perform single scan and return events."""
        events = []
        
        for watch_path in self.config.watch_paths:
            if not watch_path.exists():
                continue
            
            for path in self._iter_files(watch_path):
                event = self._check_file(path)
                if event:
                    events.append(event)
        
        # Check for deleted files
        for path in list(self._file_states.keys()):
            if not path.exists():
                events.append(WatchEvent(
                    path=path,
                    event_type="deleted",
                    timestamp=time.time(),
                ))
                del self._file_states[path]
        
        return events
    
    def _watch_loop(self) -> None:
        """Main watch loop."""
        while not self._stop_event.is_set():
            try:
                events = self.scan_once()
                
                # Apply debouncing
                now = time.time()
                
                for event in events:
                    self._pending_events[event.path] = event
                    self._pending_times[event.path] = now
                
                # Emit debounced events
                for path, pending_time in list(self._pending_times.items()):
                    if now - pending_time >= self.config.debounce_delay:
                        event = self._pending_events.pop(path, None)
                        del self._pending_times[path]
                        
                        if event and self.on_change:
                            try:
                                self.on_change(event)
                            except Exception as e:
                                logger.error(f"Error in change handler: {e}")
                
            except Exception as e:
                logger.error(f"Watch loop error: {e}")
            
            self._stop_event.wait(self.config.poll_interval)
    
    def _iter_files(self, root: Path):
        """Iterate over files in directory."""
        try:
            for entry in os.scandir(root):
                # Skip excluded patterns
                if self._is_excluded(entry.name):
                    continue
                
                if entry.is_dir():
                    yield from self._iter_files(Path(entry.path))
                elif entry.is_file():
                    path = Path(entry.path)
                    if self._is_included(path):
                        yield path
        except PermissionError:
            pass
    
    def _is_excluded(self, name: str) -> bool:
        """Check if name matches exclude pattern."""
        import fnmatch
        
        for pattern in self.config.exclude_patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False
    
    def _is_included(self, path: Path) -> bool:
        """Check if file matches include patterns."""
        return path.suffix.lower() in self.config.include_extensions
    
    def _check_file(self, path: Path) -> WatchEvent | None:
        """Check file for changes."""
        try:
            stat = path.stat()
            mtime = stat.st_mtime
            size = stat.st_size
            
            # Skip files over size limit
            if size > self.config.max_file_size_bytes:
                return None
            
            prev_state = self._file_states.get(path)
            
            if prev_state is None:
                # New file
                self._file_states[path] = (mtime, size)
                return WatchEvent(
                    path=path,
                    event_type="created",
                    timestamp=mtime,
                    size=size,
                )
            
            prev_mtime, prev_size = prev_state
            
            if mtime != prev_mtime or size != prev_size:
                # Modified
                self._file_states[path] = (mtime, size)
                return WatchEvent(
                    path=path,
                    event_type="modified",
                    timestamp=mtime,
                    size=size,
                )
            
            return None
            
        except (OSError, IOError) as e:
            logger.debug(f"Error checking {path}: {e}")
            return None
