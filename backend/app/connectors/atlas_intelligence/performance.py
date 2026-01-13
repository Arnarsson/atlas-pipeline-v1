"""
Performance Optimization Module for AtlasIntelligence

Handles large-scale data syncs with:
- Batch processing with configurable sizes
- Memory-efficient streaming
- Progress tracking and checkpointing
- Parallel stream processing
- Backpressure handling
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    AsyncGenerator,
    Callable,
    Dict,
    List,
    Optional,
    Any,
    TypeVar,
    Generic
)
from enum import Enum
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SyncStrategy(str, Enum):
    """Sync strategy based on data volume."""
    SMALL = "small"      # < 10K records - single batch
    MEDIUM = "medium"    # 10K - 100K records - batched
    LARGE = "large"      # 100K - 1M records - streaming with checkpoints
    XLARGE = "xlarge"    # > 1M records - parallel streaming


@dataclass
class BatchConfig:
    """Configuration for batch processing."""
    batch_size: int = 10000
    max_memory_mb: int = 512
    checkpoint_interval: int = 50000
    parallel_streams: int = 4
    backpressure_threshold: int = 100000
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0


@dataclass
class SyncProgress:
    """Track sync progress for large operations."""
    total_records: int = 0
    processed_records: int = 0
    failed_records: int = 0
    current_batch: int = 0
    total_batches: int = 0
    start_time: Optional[datetime] = None
    last_checkpoint: Optional[datetime] = None
    last_checkpoint_record: int = 0
    estimated_completion: Optional[datetime] = None
    records_per_second: float = 0.0
    memory_usage_mb: float = 0.0
    status: str = "pending"
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_records": self.total_records,
            "processed_records": self.processed_records,
            "failed_records": self.failed_records,
            "current_batch": self.current_batch,
            "total_batches": self.total_batches,
            "progress_percent": round(
                (self.processed_records / self.total_records * 100)
                if self.total_records > 0 else 0, 2
            ),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_checkpoint": self.last_checkpoint.isoformat() if self.last_checkpoint else None,
            "estimated_completion": self.estimated_completion.isoformat() if self.estimated_completion else None,
            "records_per_second": round(self.records_per_second, 2),
            "memory_usage_mb": round(self.memory_usage_mb, 2),
            "status": self.status,
            "errors": self.errors[-10:]  # Last 10 errors
        }


class RecordBuffer(Generic[T]):
    """Memory-efficient buffer for batch processing."""

    def __init__(self, max_size: int = 10000, max_memory_mb: int = 256):
        self._buffer: List[T] = []
        self._max_size = max_size
        self._max_memory_mb = max_memory_mb
        self._current_memory_mb = 0.0

    def add(self, record: T) -> bool:
        """Add record to buffer. Returns True if buffer is full."""
        self._buffer.append(record)
        # Rough memory estimate (100 bytes per simple record)
        self._current_memory_mb += 0.0001
        return len(self._buffer) >= self._max_size or self._current_memory_mb >= self._max_memory_mb

    def flush(self) -> List[T]:
        """Return and clear buffer."""
        records = self._buffer
        self._buffer = []
        self._current_memory_mb = 0.0
        return records

    def __len__(self) -> int:
        return len(self._buffer)

    @property
    def memory_mb(self) -> float:
        return self._current_memory_mb


class PerformanceOptimizedSync:
    """
    Performance-optimized sync executor for large datasets.

    Features:
    - Automatic strategy selection based on data volume
    - Memory-efficient streaming with backpressure
    - Checkpoint-based recovery
    - Progress tracking with ETA
    - Parallel stream processing
    """

    def __init__(self, config: Optional[BatchConfig] = None):
        self.config = config or BatchConfig()
        self._active_syncs: Dict[str, SyncProgress] = {}
        self._checkpoints: Dict[str, Dict[str, Any]] = {}

    def determine_strategy(self, estimated_records: int) -> SyncStrategy:
        """Determine optimal sync strategy based on data volume."""
        if estimated_records < 10000:
            return SyncStrategy.SMALL
        elif estimated_records < 100000:
            return SyncStrategy.MEDIUM
        elif estimated_records < 1000000:
            return SyncStrategy.LARGE
        else:
            return SyncStrategy.XLARGE

    def get_progress(self, sync_id: str) -> Optional[SyncProgress]:
        """Get progress for a sync operation."""
        return self._active_syncs.get(sync_id)

    def get_all_progress(self) -> Dict[str, Dict[str, Any]]:
        """Get progress for all active syncs."""
        return {
            sync_id: progress.to_dict()
            for sync_id, progress in self._active_syncs.items()
        }

    async def sync_with_batching(
        self,
        sync_id: str,
        record_generator: AsyncGenerator[Dict[str, Any], None],
        process_batch: Callable[[List[Dict[str, Any]]], Any],
        estimated_records: int = 0,
        on_progress: Optional[Callable[[SyncProgress], None]] = None
    ) -> SyncProgress:
        """
        Execute sync with batching and progress tracking.

        Args:
            sync_id: Unique identifier for this sync
            record_generator: Async generator yielding records
            process_batch: Function to process each batch
            estimated_records: Estimated total records (for progress)
            on_progress: Callback for progress updates

        Returns:
            Final SyncProgress
        """
        strategy = self.determine_strategy(estimated_records)
        logger.info(f"Starting sync {sync_id} with strategy: {strategy.value}")

        progress = SyncProgress(
            total_records=estimated_records,
            start_time=datetime.utcnow(),
            status="running"
        )
        self._active_syncs[sync_id] = progress

        buffer = RecordBuffer(
            max_size=self.config.batch_size,
            max_memory_mb=self.config.max_memory_mb
        )

        try:
            batch_num = 0
            async for record in record_generator:
                if buffer.add(record):
                    # Buffer full, process batch
                    batch_num += 1
                    batch = buffer.flush()

                    await self._process_batch_with_retry(
                        batch, process_batch, progress, batch_num
                    )

                    # Update progress
                    progress.current_batch = batch_num
                    progress.memory_usage_mb = buffer.memory_mb
                    self._update_progress_stats(progress)

                    # Checkpoint if needed
                    if progress.processed_records - progress.last_checkpoint_record >= self.config.checkpoint_interval:
                        await self._save_checkpoint(sync_id, progress)

                    # Progress callback
                    if on_progress:
                        on_progress(progress)

                    # Backpressure handling
                    if progress.processed_records % self.config.backpressure_threshold == 0:
                        await asyncio.sleep(0.1)  # Brief pause to prevent memory buildup

            # Process remaining records
            if len(buffer) > 0:
                batch_num += 1
                batch = buffer.flush()
                await self._process_batch_with_retry(
                    batch, process_batch, progress, batch_num
                )

            progress.status = "completed"
            progress.total_batches = batch_num

        except Exception as e:
            progress.status = "failed"
            progress.errors.append(str(e))
            logger.error(f"Sync {sync_id} failed: {e}")
            raise

        finally:
            self._update_progress_stats(progress)
            if on_progress:
                on_progress(progress)

        return progress

    async def _process_batch_with_retry(
        self,
        batch: List[Dict[str, Any]],
        process_batch: Callable,
        progress: SyncProgress,
        batch_num: int
    ):
        """Process batch with retry logic."""
        last_error = None

        for attempt in range(self.config.retry_attempts):
            try:
                await asyncio.to_thread(process_batch, batch)
                progress.processed_records += len(batch)
                return
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Batch {batch_num} attempt {attempt + 1} failed: {e}"
                )
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(
                        self.config.retry_delay_seconds * (attempt + 1)
                    )

        # All retries failed
        progress.failed_records += len(batch)
        progress.errors.append(f"Batch {batch_num}: {last_error}")

    def _update_progress_stats(self, progress: SyncProgress):
        """Update progress statistics."""
        if progress.start_time:
            elapsed = (datetime.utcnow() - progress.start_time).total_seconds()
            if elapsed > 0:
                progress.records_per_second = progress.processed_records / elapsed

                # Estimate completion
                if progress.total_records > 0 and progress.records_per_second > 0:
                    remaining = progress.total_records - progress.processed_records
                    remaining_seconds = remaining / progress.records_per_second
                    progress.estimated_completion = datetime.utcnow() + \
                        __import__('datetime').timedelta(seconds=remaining_seconds)

    async def _save_checkpoint(self, sync_id: str, progress: SyncProgress):
        """Save checkpoint for recovery."""
        progress.last_checkpoint = datetime.utcnow()
        progress.last_checkpoint_record = progress.processed_records

        self._checkpoints[sync_id] = {
            "processed_records": progress.processed_records,
            "checkpoint_time": progress.last_checkpoint.isoformat(),
            "batch_num": progress.current_batch
        }
        logger.info(
            f"Checkpoint saved for {sync_id}: {progress.processed_records} records"
        )

    def get_checkpoint(self, sync_id: str) -> Optional[Dict[str, Any]]:
        """Get checkpoint for recovery."""
        return self._checkpoints.get(sync_id)

    async def sync_parallel_streams(
        self,
        sync_id: str,
        streams: List[str],
        stream_reader: Callable[[str], AsyncGenerator[Dict[str, Any], None]],
        process_batch: Callable[[str, List[Dict[str, Any]]], Any],
        records_per_stream: Optional[Dict[str, int]] = None
    ) -> Dict[str, SyncProgress]:
        """
        Sync multiple streams in parallel.

        Args:
            sync_id: Base sync ID
            streams: List of stream names
            stream_reader: Function to get record generator for a stream
            process_batch: Function to process batch for a stream
            records_per_stream: Estimated records per stream

        Returns:
            Progress for each stream
        """
        records_per_stream = records_per_stream or {}

        # Limit concurrency
        semaphore = asyncio.Semaphore(self.config.parallel_streams)

        async def sync_stream(stream: str) -> SyncProgress:
            async with semaphore:
                stream_sync_id = f"{sync_id}_{stream}"
                generator = stream_reader(stream)
                estimated = records_per_stream.get(stream, 0)

                return await self.sync_with_batching(
                    sync_id=stream_sync_id,
                    record_generator=generator,
                    process_batch=lambda batch: process_batch(stream, batch),
                    estimated_records=estimated
                )

        # Run all streams in parallel (with semaphore limiting)
        tasks = [sync_stream(stream) for stream in streams]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        stream_progress = {}
        for stream, result in zip(streams, results):
            if isinstance(result, Exception):
                progress = SyncProgress(status="failed")
                progress.errors.append(str(result))
                stream_progress[stream] = progress
            else:
                stream_progress[stream] = result

        return stream_progress

    def cleanup_sync(self, sync_id: str):
        """Clean up completed sync."""
        self._active_syncs.pop(sync_id, None)
        self._checkpoints.pop(sync_id, None)


# Singleton instance
_performance_optimizer: Optional[PerformanceOptimizedSync] = None


def get_performance_optimizer() -> PerformanceOptimizedSync:
    """Get singleton performance optimizer instance."""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizedSync()
    return _performance_optimizer


# Utility functions for common operations
async def estimate_record_count(
    source_id: str,
    stream: str,
    sample_size: int = 1000
) -> int:
    """
    Estimate total record count for a stream.
    Uses sampling if count query not available.
    """
    # This would be implemented based on connector capabilities
    # For now, return a default estimate
    return 100000


def calculate_optimal_batch_size(
    available_memory_mb: int,
    avg_record_size_bytes: int = 500
) -> int:
    """Calculate optimal batch size based on available memory."""
    # Use 50% of available memory for batching
    usable_memory = available_memory_mb * 0.5 * 1024 * 1024  # Convert to bytes
    batch_size = int(usable_memory / avg_record_size_bytes)
    # Clamp between 1000 and 100000
    return max(1000, min(100000, batch_size))
