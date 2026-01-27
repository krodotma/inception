"""
Sync queue for managing sync jobs.

Priority queue with retry support.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from heapq import heappush, heappop
from pathlib import Path
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Status of a sync job."""
    
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    RETRYING = auto()


class JobPriority(Enum):
    """Priority levels for sync jobs."""
    
    HIGH = 1     # User-requested
    NORMAL = 2   # Auto-detected changes
    LOW = 3      # Background sync
    BATCH = 4    # Bulk operations


@dataclass(order=True)
class SyncJob:
    """A sync job in the queue."""
    
    priority: int = field(compare=True)
    created_at: float = field(compare=True, default_factory=time.time)
    
    # Non-comparable fields
    path: Path = field(compare=False, default_factory=lambda: Path("."))
    job_id: str = field(compare=False, default="")
    status: JobStatus = field(compare=False, default=JobStatus.PENDING)
    
    # Retry tracking
    attempt: int = field(compare=False, default=0)
    max_attempts: int = field(compare=False, default=3)
    last_error: str = field(compare=False, default="")
    
    # Metadata
    metadata: dict[str, Any] = field(compare=False, default_factory=dict)
    
    @property
    def can_retry(self) -> bool:
        return self.attempt < self.max_attempts


class SyncQueue:
    """
    Priority queue for sync jobs.
    
    Thread-safe with retry support.
    """
    
    def __init__(self, max_size: int = 10000):
        """Initialize sync queue."""
        self.max_size = max_size
        
        self._queue: list[SyncJob] = []
        self._lock = Lock()
        self._job_counter = 0
        self._in_progress: dict[str, SyncJob] = {}
        self._completed: list[SyncJob] = []
        self._failed: list[SyncJob] = []
    
    @property
    def size(self) -> int:
        """Get current queue size."""
        with self._lock:
            return len(self._queue)
    
    @property
    def in_progress_count(self) -> int:
        """Get number of in-progress jobs."""
        with self._lock:
            return len(self._in_progress)
    
    def enqueue(
        self,
        path: Path,
        priority: JobPriority = JobPriority.NORMAL,
        **metadata,
    ) -> SyncJob:
        """
        Add a job to the queue.
        
        Args:
            path: Path to sync
            priority: Job priority
            **metadata: Additional metadata
        
        Returns:
            Created job
        """
        with self._lock:
            if len(self._queue) >= self.max_size:
                raise RuntimeError("Sync queue is full")
            
            self._job_counter += 1
            job = SyncJob(
                priority=priority.value,
                path=path,
                job_id=f"sync-{self._job_counter}",
                metadata=metadata,
            )
            
            heappush(self._queue, job)
            logger.debug(f"Enqueued {job.job_id}: {path}")
            
            return job
    
    def dequeue(self) -> SyncJob | None:
        """Get next job from queue."""
        with self._lock:
            if not self._queue:
                return None
            
            job = heappop(self._queue)
            job.status = JobStatus.RUNNING
            self._in_progress[job.job_id] = job
            
            return job
    
    def complete(self, job: SyncJob) -> None:
        """Mark job as completed."""
        with self._lock:
            job.status = JobStatus.COMPLETED
            self._in_progress.pop(job.job_id, None)
            self._completed.append(job)
        
        logger.debug(f"Completed {job.job_id}")
    
    def fail(self, job: SyncJob, error: str = "") -> None:
        """Mark job as failed, maybe retry."""
        with self._lock:
            job.attempt += 1
            job.last_error = error
            
            self._in_progress.pop(job.job_id, None)
            
            if job.can_retry:
                job.status = JobStatus.RETRYING
                # Increase priority for retries
                job.priority = min(job.priority + 1, JobPriority.BATCH.value)
                job.created_at = time.time()  # Reset for fair ordering
                heappush(self._queue, job)
                logger.info(f"Retrying {job.job_id} (attempt {job.attempt})")
            else:
                job.status = JobStatus.FAILED
                self._failed.append(job)
                logger.warning(f"Failed {job.job_id}: {error}")
    
    def get_stats(self) -> dict[str, int]:
        """Get queue statistics."""
        with self._lock:
            return {
                "pending": len(self._queue),
                "in_progress": len(self._in_progress),
                "completed": len(self._completed),
                "failed": len(self._failed),
            }
    
    def clear_completed(self) -> int:
        """Clear completed job history."""
        with self._lock:
            count = len(self._completed)
            self._completed = []
            return count
    
    def get_failed(self) -> list[SyncJob]:
        """Get all failed jobs."""
        with self._lock:
            return self._failed.copy()
