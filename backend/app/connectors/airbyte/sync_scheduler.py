"""
PyAirbyte Sync Scheduler - Schedule and manage data sync jobs.

Provides job scheduling, execution tracking, and history for PyAirbyte connectors.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from threading import Lock

logger = logging.getLogger(__name__)


class SyncStatus(str, Enum):
    """Status of a sync job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SyncMode(str, Enum):
    """Sync mode for data extraction."""
    FULL_REFRESH = "full_refresh"
    INCREMENTAL = "incremental"


@dataclass
class SyncJob:
    """Represents a sync job."""
    job_id: str
    source_id: str
    source_name: str
    streams: List[str]
    sync_mode: SyncMode
    status: SyncStatus = SyncStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    records_synced: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "streams": self.streams,
            "sync_mode": self.sync_mode.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self._get_duration(),
            "records_synced": self.records_synced,
            "error_message": self.error_message,
            "metadata": self.metadata
        }

    def _get_duration(self) -> Optional[float]:
        """Get job duration in seconds."""
        if not self.started_at:
            return None
        end = self.completed_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()


@dataclass
class ScheduledSync:
    """Represents a scheduled recurring sync."""
    schedule_id: str
    source_id: str
    source_name: str
    streams: List[str]
    sync_mode: SyncMode
    cron_expression: str  # e.g., "0 * * * *" for hourly
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    run_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "schedule_id": self.schedule_id,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "streams": self.streams,
            "sync_mode": self.sync_mode.value,
            "cron_expression": self.cron_expression,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "run_count": self.run_count,
            "metadata": self.metadata
        }


class SyncScheduler:
    """
    Manages sync job scheduling and execution.

    Provides:
    - Manual sync job creation and execution
    - Scheduled recurring syncs with cron expressions
    - Job history and status tracking
    - Concurrent job management
    """

    def __init__(self, max_concurrent_jobs: int = 5):
        """
        Initialize sync scheduler.

        Args:
            max_concurrent_jobs: Maximum concurrent sync jobs
        """
        self._jobs: Dict[str, SyncJob] = {}
        self._schedules: Dict[str, ScheduledSync] = {}
        self._job_history: List[SyncJob] = []
        self._running_jobs: set = set()
        self._lock = Lock()
        self._max_concurrent = max_concurrent_jobs
        self._callbacks: Dict[str, List[Callable]] = {
            "on_job_start": [],
            "on_job_complete": [],
            "on_job_fail": [],
        }

    def create_sync_job(
        self,
        source_id: str,
        source_name: str,
        streams: List[str],
        sync_mode: SyncMode = SyncMode.FULL_REFRESH,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SyncJob:
        """
        Create a new sync job.

        Args:
            source_id: Source connector ID
            source_name: Source connector name
            streams: List of streams to sync
            sync_mode: Full refresh or incremental
            metadata: Additional metadata

        Returns:
            Created SyncJob
        """
        job_id = f"sync_{uuid.uuid4().hex[:12]}"

        job = SyncJob(
            job_id=job_id,
            source_id=source_id,
            source_name=source_name,
            streams=streams,
            sync_mode=sync_mode,
            metadata=metadata or {}
        )

        with self._lock:
            self._jobs[job_id] = job

        logger.info(f"Created sync job {job_id} for {source_name}")
        return job

    async def run_sync_job(
        self,
        job_id: str,
        executor_fn: Optional[Callable] = None
    ) -> SyncJob:
        """
        Run a sync job.

        Args:
            job_id: Job ID to run
            executor_fn: Optional custom executor function

        Returns:
            Updated SyncJob
        """
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.status == SyncStatus.RUNNING:
            raise ValueError(f"Job {job_id} is already running")

        # Check concurrent job limit
        with self._lock:
            if len(self._running_jobs) >= self._max_concurrent:
                raise ValueError(f"Maximum concurrent jobs ({self._max_concurrent}) reached")
            self._running_jobs.add(job_id)

        # Update job status
        job.status = SyncStatus.RUNNING
        job.started_at = datetime.utcnow()

        # Fire start callbacks
        for callback in self._callbacks["on_job_start"]:
            try:
                callback(job)
            except Exception as e:
                logger.warning(f"Callback error: {e}")

        try:
            # Execute sync
            if executor_fn:
                result = await executor_fn(job)
                job.records_synced = result.get("records_synced", 0)
            else:
                # Simulate sync for demo
                await asyncio.sleep(0.1)  # Simulate work
                job.records_synced = len(job.streams) * 100  # Mock records

            job.status = SyncStatus.COMPLETED
            job.completed_at = datetime.utcnow()

            # Fire complete callbacks
            for callback in self._callbacks["on_job_complete"]:
                try:
                    callback(job)
                except Exception as e:
                    logger.warning(f"Callback error: {e}")

            logger.info(f"Sync job {job_id} completed: {job.records_synced} records")

        except Exception as e:
            job.status = SyncStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()

            # Fire fail callbacks
            for callback in self._callbacks["on_job_fail"]:
                try:
                    callback(job, e)
                except Exception as ce:
                    logger.warning(f"Callback error: {ce}")

            logger.error(f"Sync job {job_id} failed: {e}")

        finally:
            with self._lock:
                self._running_jobs.discard(job_id)
                # Move to history
                self._job_history.append(job)
                # Keep only last 100 jobs in history
                if len(self._job_history) > 100:
                    self._job_history = self._job_history[-100:]

        return job

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending or running job.

        Args:
            job_id: Job ID to cancel

        Returns:
            True if cancelled, False otherwise
        """
        job = self._jobs.get(job_id)
        if not job:
            return False

        if job.status in [SyncStatus.COMPLETED, SyncStatus.FAILED, SyncStatus.CANCELLED]:
            return False

        job.status = SyncStatus.CANCELLED
        job.completed_at = datetime.utcnow()

        with self._lock:
            self._running_jobs.discard(job_id)

        logger.info(f"Cancelled sync job {job_id}")
        return True

    def get_job(self, job_id: str) -> Optional[SyncJob]:
        """Get a job by ID."""
        return self._jobs.get(job_id)

    def get_running_jobs(self) -> List[SyncJob]:
        """Get all running jobs."""
        return [
            job for job in self._jobs.values()
            if job.status == SyncStatus.RUNNING
        ]

    def get_job_history(
        self,
        source_id: Optional[str] = None,
        limit: int = 20
    ) -> List[SyncJob]:
        """
        Get job history.

        Args:
            source_id: Filter by source (optional)
            limit: Maximum jobs to return

        Returns:
            List of historical jobs
        """
        history = self._job_history.copy()

        if source_id:
            history = [j for j in history if j.source_id == source_id]

        # Sort by created_at descending
        history.sort(key=lambda j: j.created_at, reverse=True)

        return history[:limit]

    # ========================================================================
    # Scheduled Syncs
    # ========================================================================

    def create_schedule(
        self,
        source_id: str,
        source_name: str,
        streams: List[str],
        cron_expression: str,
        sync_mode: SyncMode = SyncMode.INCREMENTAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ScheduledSync:
        """
        Create a scheduled recurring sync.

        Args:
            source_id: Source connector ID
            source_name: Source connector name
            streams: Streams to sync
            cron_expression: Cron expression (e.g., "0 * * * *" for hourly)
            sync_mode: Sync mode
            metadata: Additional metadata

        Returns:
            Created ScheduledSync
        """
        schedule_id = f"schedule_{uuid.uuid4().hex[:8]}"

        schedule = ScheduledSync(
            schedule_id=schedule_id,
            source_id=source_id,
            source_name=source_name,
            streams=streams,
            sync_mode=sync_mode,
            cron_expression=cron_expression,
            next_run_at=self._calculate_next_run(cron_expression),
            metadata=metadata or {}
        )

        with self._lock:
            self._schedules[schedule_id] = schedule

        logger.info(f"Created schedule {schedule_id} for {source_name}: {cron_expression}")
        return schedule

    def _calculate_next_run(self, cron_expression: str) -> datetime:
        """Calculate next run time from cron expression (simplified)."""
        # Simplified: just add 1 hour for demo
        # In production, use croniter library
        parts = cron_expression.split()
        if len(parts) >= 5:
            minute = parts[0]
            hour = parts[1]

            now = datetime.utcnow()

            if minute == "*" and hour == "*":
                # Every minute
                return now + timedelta(minutes=1)
            elif minute.isdigit() and hour == "*":
                # Every hour at minute X
                return now.replace(minute=int(minute), second=0, microsecond=0) + timedelta(hours=1)
            elif minute.isdigit() and hour.isdigit():
                # Daily at specific time
                return now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0) + timedelta(days=1)

        return datetime.utcnow() + timedelta(hours=1)

    def get_schedule(self, schedule_id: str) -> Optional[ScheduledSync]:
        """Get a schedule by ID."""
        return self._schedules.get(schedule_id)

    def list_schedules(self, source_id: Optional[str] = None) -> List[ScheduledSync]:
        """
        List all schedules.

        Args:
            source_id: Filter by source (optional)

        Returns:
            List of schedules
        """
        schedules = list(self._schedules.values())

        if source_id:
            schedules = [s for s in schedules if s.source_id == source_id]

        return schedules

    def update_schedule(
        self,
        schedule_id: str,
        enabled: Optional[bool] = None,
        cron_expression: Optional[str] = None,
        streams: Optional[List[str]] = None
    ) -> Optional[ScheduledSync]:
        """
        Update a schedule.

        Args:
            schedule_id: Schedule ID
            enabled: Enable/disable
            cron_expression: New cron expression
            streams: New streams list

        Returns:
            Updated schedule or None
        """
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return None

        if enabled is not None:
            schedule.enabled = enabled

        if cron_expression:
            schedule.cron_expression = cron_expression
            schedule.next_run_at = self._calculate_next_run(cron_expression)

        if streams is not None:
            schedule.streams = streams

        logger.info(f"Updated schedule {schedule_id}")
        return schedule

    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule."""
        if schedule_id not in self._schedules:
            return False

        with self._lock:
            del self._schedules[schedule_id]

        logger.info(f"Deleted schedule {schedule_id}")
        return True

    async def run_scheduled_sync(self, schedule_id: str) -> Optional[SyncJob]:
        """
        Manually trigger a scheduled sync.

        Args:
            schedule_id: Schedule ID to run

        Returns:
            Created and executed SyncJob
        """
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return None

        # Create and run job
        job = self.create_sync_job(
            source_id=schedule.source_id,
            source_name=schedule.source_name,
            streams=schedule.streams,
            sync_mode=schedule.sync_mode,
            metadata={"schedule_id": schedule_id}
        )

        await self.run_sync_job(job.job_id)

        # Update schedule
        schedule.last_run_at = datetime.utcnow()
        schedule.next_run_at = self._calculate_next_run(schedule.cron_expression)
        schedule.run_count += 1

        return job

    # ========================================================================
    # Statistics
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        all_jobs = list(self._jobs.values()) + self._job_history

        completed_jobs = [j for j in all_jobs if j.status == SyncStatus.COMPLETED]
        failed_jobs = [j for j in all_jobs if j.status == SyncStatus.FAILED]

        total_records = sum(j.records_synced for j in completed_jobs)

        return {
            "total_jobs": len(all_jobs),
            "running_jobs": len(self._running_jobs),
            "completed_jobs": len(completed_jobs),
            "failed_jobs": len(failed_jobs),
            "total_records_synced": total_records,
            "active_schedules": sum(1 for s in self._schedules.values() if s.enabled),
            "total_schedules": len(self._schedules),
            "max_concurrent_jobs": self._max_concurrent
        }

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register a callback for job events."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)


# Global scheduler instance
_scheduler: Optional[SyncScheduler] = None


def get_sync_scheduler() -> SyncScheduler:
    """Get or create global sync scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = SyncScheduler()
    return _scheduler
