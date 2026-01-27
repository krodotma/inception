"""
Change detection for incremental sync.

Uses hashing for accurate change detection.
"""

from __future__ import annotations

import hashlib
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Type of file change."""
    
    CREATED = auto()
    MODIFIED = auto()
    DELETED = auto()
    UNCHANGED = auto()


@dataclass
class ChangeEvent:
    """Detected change event."""
    
    path: Path
    change_type: ChangeType
    
    # File metadata
    size: int = 0
    mtime: float = 0.0
    content_hash: str = ""
    
    # Previous state (for modifications)
    prev_hash: str = ""
    prev_mtime: float = 0.0
    
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class FileState:
    """Stored state of a file."""
    
    path: str
    content_hash: str
    size: int
    mtime: float
    last_synced: datetime
    nid: int | None = None  # Node ID if ingested


class ChangeDetector:
    """
    Detects actual content changes using hashing.
    
    Stores state in SQLite for persistence.
    """
    
    def __init__(
        self,
        state_path: Path | None = None,
        hash_chunk_size: int = 8192,
    ):
        """
        Initialize change detector.
        
        Args:
            state_path: Path to SQLite state database
            hash_chunk_size: Chunk size for hashing
        """
        self.state_path = state_path or Path.home() / ".inception" / "sync_state.db"
        self.hash_chunk_size = hash_chunk_size
        
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize state database."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.state_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_states (
                    path TEXT PRIMARY KEY,
                    content_hash TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    mtime REAL NOT NULL,
                    last_synced TEXT NOT NULL,
                    nid INTEGER
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_states_hash 
                ON file_states(content_hash)
            """)
    
    def detect_change(self, path: Path) -> ChangeEvent:
        """
        Detect if a file has changed.
        
        Args:
            path: Path to check
        
        Returns:
            ChangeEvent with change type
        """
        if not path.exists():
            # Check if we knew about it
            prev_state = self._get_state(path)
            
            if prev_state:
                self._delete_state(path)
                return ChangeEvent(
                    path=path,
                    change_type=ChangeType.DELETED,
                    prev_hash=prev_state.content_hash,
                    prev_mtime=prev_state.mtime,
                )
            else:
                # Never knew about it
                return ChangeEvent(
                    path=path,
                    change_type=ChangeType.UNCHANGED,
                )
        
        # Get current file info
        try:
            stat = path.stat()
            size = stat.st_size
            mtime = stat.st_mtime
        except OSError as e:
            logger.warning(f"Cannot stat {path}: {e}")
            return ChangeEvent(path=path, change_type=ChangeType.UNCHANGED)
        
        # Get previous state
        prev_state = self._get_state(path)
        
        if prev_state is None:
            # New file
            content_hash = self._hash_file(path)
            return ChangeEvent(
                path=path,
                change_type=ChangeType.CREATED,
                size=size,
                mtime=mtime,
                content_hash=content_hash,
            )
        
        # Quick check: same mtime and size = probably unchanged
        if prev_state.mtime == mtime and prev_state.size == size:
            return ChangeEvent(
                path=path,
                change_type=ChangeType.UNCHANGED,
                size=size,
                mtime=mtime,
                content_hash=prev_state.content_hash,
            )
        
        # Need to hash to confirm
        content_hash = self._hash_file(path)
        
        if content_hash == prev_state.content_hash:
            # Content unchanged, just metadata
            return ChangeEvent(
                path=path,
                change_type=ChangeType.UNCHANGED,
                size=size,
                mtime=mtime,
                content_hash=content_hash,
            )
        
        # Actually modified
        return ChangeEvent(
            path=path,
            change_type=ChangeType.MODIFIED,
            size=size,
            mtime=mtime,
            content_hash=content_hash,
            prev_hash=prev_state.content_hash,
            prev_mtime=prev_state.mtime,
        )
    
    def record_sync(
        self,
        path: Path,
        content_hash: str | None = None,
        nid: int | None = None,
    ) -> None:
        """Record that a file was synced."""
        if not path.exists():
            return
        
        try:
            stat = path.stat()
            
            if content_hash is None:
                content_hash = self._hash_file(path)
            
            state = FileState(
                path=str(path),
                content_hash=content_hash,
                size=stat.st_size,
                mtime=stat.st_mtime,
                last_synced=datetime.now(),
                nid=nid,
            )
            
            self._save_state(state)
            
        except OSError as e:
            logger.warning(f"Cannot record sync for {path}: {e}")
    
    def get_pending_changes(
        self,
        paths: list[Path],
    ) -> list[ChangeEvent]:
        """Get all pending changes for given paths."""
        changes = []
        
        for path in paths:
            event = self.detect_change(path)
            if event.change_type != ChangeType.UNCHANGED:
                changes.append(event)
        
        return changes
    
    def _hash_file(self, path: Path) -> str:
        """Compute SHA256 hash of file."""
        hasher = hashlib.sha256()
        
        try:
            with open(path, "rb") as f:
                while chunk := f.read(self.hash_chunk_size):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except IOError as e:
            logger.error(f"Cannot hash {path}: {e}")
            return ""
    
    def _get_state(self, path: Path) -> FileState | None:
        """Get stored state for a file."""
        with sqlite3.connect(self.state_path) as conn:
            row = conn.execute(
                "SELECT path, content_hash, size, mtime, last_synced, nid "
                "FROM file_states WHERE path = ?",
                (str(path),)
            ).fetchone()
            
            if row:
                return FileState(
                    path=row[0],
                    content_hash=row[1],
                    size=row[2],
                    mtime=row[3],
                    last_synced=datetime.fromisoformat(row[4]),
                    nid=row[5],
                )
            return None
    
    def _save_state(self, state: FileState) -> None:
        """Save file state."""
        with sqlite3.connect(self.state_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO file_states 
                (path, content_hash, size, mtime, last_synced, nid)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    state.path,
                    state.content_hash,
                    state.size,
                    state.mtime,
                    state.last_synced.isoformat(),
                    state.nid,
                )
            )
    
    def _delete_state(self, path: Path) -> None:
        """Delete file state."""
        with sqlite3.connect(self.state_path) as conn:
            conn.execute(
                "DELETE FROM file_states WHERE path = ?",
                (str(path),)
            )
