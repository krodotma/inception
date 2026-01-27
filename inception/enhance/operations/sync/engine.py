"""
Sync engine - orchestrates incremental synchronization.

Combines watcher, detector, and queue for full sync workflow.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import Event, Thread
from typing import Any, Callable

from inception.enhance.operations.sync.watcher import FileWatcher, WatchConfig, WatchEvent
from inception.enhance.operations.sync.detector import ChangeDetector, ChangeEvent, ChangeType
from inception.enhance.operations.sync.queue import SyncQueue, SyncJob, JobPriority

logger = logging.getLogger(__name__)


@dataclass
class SyncConfig:
    """Configuration for sync engine."""
    
    watch_paths: list[Path]
    state_path: Path | None = None
    
    # Processing
    batch_size: int = 10          # Files to process per batch
    worker_threads: int = 2       # Parallel workers
    
    # Timing
    poll_interval: float = 1.0
    debounce_delay: float = 2.0
    
    # Callbacks
    on_sync_start: Callable[[Path], None] | None = None
    on_sync_complete: Callable[[Path, Any], None] | None = None
    on_sync_error: Callable[[Path, Exception], None] | None = None


@dataclass
class SyncResult:
    """Result of a sync operation."""
    
    path: Path
    success: bool
    nid: int | None = None        # Node ID if created
    duration_ms: float = 0.0
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class SyncEngine:
    """
    Orchestrates incremental synchronization.
    
    Workflow:
    1. Watch for file changes
    2. Detect actual content changes
    3. Queue for processing
    4. Invoke ingestion pipeline
    5. Record sync state
    """
    
    def __init__(
        self,
        config: SyncConfig,
        ingest_callback: Callable[[Path], SyncResult] | None = None,
    ):
        """
        Initialize sync engine.
        
        Args:
            config: Sync configuration
            ingest_callback: Function to call for ingesting files
        """
        self.config = config
        self.ingest_callback = ingest_callback
        
        # Initialize components
        self.detector = ChangeDetector(state_path=config.state_path)
        self.queue = SyncQueue()
        
        watch_config = WatchConfig(
            watch_paths=config.watch_paths,
            poll_interval=config.poll_interval,
            debounce_delay=config.debounce_delay,
        )
        self.watcher = FileWatcher(
            config=watch_config,
            on_change=self._handle_watch_event,
        )
        
        self._stop_event = Event()
        self._workers: list[Thread] = []
        self._stats = {
            "files_synced": 0,
            "files_failed": 0,
            "bytes_processed": 0,
        }
    
    def start(self) -> None:
        """Start the sync engine."""
        logger.info("Starting sync engine")
        
        self._stop_event.clear()
        
        # Start watcher
        self.watcher.start()
        
        # Start worker threads
        for i in range(self.config.worker_threads):
            worker = Thread(
                target=self._worker_loop,
                name=f"sync-worker-{i}",
                daemon=True,
            )
            worker.start()
            self._workers.append(worker)
        
        logger.info(f"Sync engine started with {self.config.worker_threads} workers")
    
    def stop(self) -> None:
        """Stop the sync engine."""
        logger.info("Stopping sync engine")
        
        self._stop_event.set()
        self.watcher.stop()
        
        for worker in self._workers:
            worker.join(timeout=5)
        
        self._workers = []
        logger.info("Sync engine stopped")
    
    def scan(self) -> list[ChangeEvent]:
        """
        Scan for changes without watching.
        
        Returns:
            List of detected changes
        """
        changes = []
        
        for watch_path in self.config.watch_paths:
            if not watch_path.exists():
                continue
            
            # Use watcher's file iterator
            for path in self._iter_files(watch_path):
                event = self.detector.detect_change(path)
                if event.change_type != ChangeType.UNCHANGED:
                    changes.append(event)
        
        return changes
    
    def sync_path(
        self,
        path: Path,
        priority: JobPriority = JobPriority.HIGH,
    ) -> SyncJob:
        """
        Manually queue a path for sync.
        
        Args:
            path: Path to sync
            priority: Job priority
        
        Returns:
            Created job
        """
        return self.queue.enqueue(path, priority=priority)
    
    def sync_all(self) -> int:
        """
        Sync all changed files immediately.
        
        Returns:
            Number of files queued
        """
        changes = self.scan()
        
        for change in changes:
            self.queue.enqueue(
                change.path,
                priority=JobPriority.BATCH,
                change_type=change.change_type.name,
            )
        
        return len(changes)
    
    def get_stats(self) -> dict[str, Any]:
        """Get sync statistics."""
        queue_stats = self.queue.get_stats()
        
        return {
            **self._stats,
            **queue_stats,
            "watching": len(self.config.watch_paths),
        }
    
    def _handle_watch_event(self, event: WatchEvent) -> None:
        """Handle event from file watcher."""
        # Verify it's an actual change
        change = self.detector.detect_change(event.path)
        
        if change.change_type == ChangeType.UNCHANGED:
            return
        
        # Queue for processing
        self.queue.enqueue(
            event.path,
            priority=JobPriority.NORMAL,
            change_type=change.change_type.name,
            content_hash=change.content_hash,
        )
    
    def _worker_loop(self) -> None:
        """Worker thread main loop."""
        while not self._stop_event.is_set():
            job = self.queue.dequeue()
            
            if job is None:
                self._stop_event.wait(0.5)
                continue
            
            try:
                result = self._process_job(job)
                
                if result.success:
                    self.queue.complete(job)
                    self.detector.record_sync(
                        job.path,
                        nid=result.nid,
                    )
                    self._stats["files_synced"] += 1
                else:
                    self.queue.fail(job, result.error)
                    
            except Exception as e:
                logger.exception(f"Worker error processing {job.path}")
                self.queue.fail(job, str(e))
                self._stats["files_failed"] += 1
    
    def _process_job(self, job: SyncJob) -> SyncResult:
        """Process a single sync job."""
        import time
        start = time.time()
        
        # Notify start
        if self.config.on_sync_start:
            try:
                self.config.on_sync_start(job.path)
            except Exception:
                pass
        
        # Call ingest callback
        if self.ingest_callback:
            try:
                result = self.ingest_callback(job.path)
            except Exception as e:
                result = SyncResult(
                    path=job.path,
                    success=False,
                    error=str(e),
                )
        else:
            # No callback - just record that we synced
            result = SyncResult(
                path=job.path,
                success=True,
            )
        
        result.duration_ms = (time.time() - start) * 1000
        
        # Notify complete
        if result.success and self.config.on_sync_complete:
            try:
                self.config.on_sync_complete(job.path, result)
            except Exception:
                pass
        elif not result.success and self.config.on_sync_error:
            try:
                self.config.on_sync_error(job.path, Exception(result.error))
            except Exception:
                pass
        
        return result
    
    def _iter_files(self, root: Path):
        """Iterate over files in directory."""
        import os
        
        for entry in os.scandir(root):
            if entry.name.startswith("."):
                continue
            
            if entry.is_dir():
                yield from self._iter_files(Path(entry.path))
            elif entry.is_file():
                yield Path(entry.path)
