"""
Incremental Sync - Watch and auto-ingest changed files.

Design by OPUS-3: File watching, change detection, sync queue.
Optimized by OPUS-1: Debouncing, batching, efficient hashing.
"""

from inception.enhance.operations.sync.watcher import FileWatcher, WatchConfig
from inception.enhance.operations.sync.detector import ChangeDetector, ChangeEvent, ChangeType
from inception.enhance.operations.sync.queue import SyncQueue, SyncJob
from inception.enhance.operations.sync.engine import SyncEngine, SyncConfig, SyncResult

__all__ = [
    "FileWatcher",
    "WatchConfig",
    "ChangeDetector",
    "ChangeEvent",
    "ChangeType",
    "SyncQueue",
    "SyncJob",
    "SyncEngine",
    "SyncConfig",
    "SyncResult",
]
