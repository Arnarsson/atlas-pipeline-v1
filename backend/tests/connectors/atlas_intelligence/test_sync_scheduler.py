"""
Tests for Sync Scheduler

Tests job creation, scheduling, execution, and history tracking.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, Any

from app.connectors.atlas_intelligence.sync_scheduler import (
    SyncScheduler,
    get_sync_scheduler,
    SyncJob,
    SyncStatus,
    ScheduledSync
)


class TestSyncStatus:
    """Tests for SyncStatus enum."""

    def test_all_statuses_exist(self):
        """Test that all expected statuses exist."""
        assert SyncStatus.PENDING.value == "pending"
        assert SyncStatus.RUNNING.value == "running"
        assert SyncStatus.COMPLETED.value == "completed"
        assert SyncStatus.FAILED.value == "failed"
        assert SyncStatus.CANCELLED.value == "cancelled"


class TestSyncJob:
    """Tests for SyncJob dataclass."""

    def test_default_values(self):
        """Test SyncJob default values."""
        job = SyncJob(
            job_id="job_001",
            source_id="src_001",
            source_name="test_source",
            streams=["users"]
        )
        assert job.job_id == "job_001"
        assert job.status == SyncStatus.PENDING
        assert job.sync_mode == "full_refresh"
        assert job.records_synced == 0
        assert job.started_at is None
        assert job.completed_at is None
        assert job.error_message is None

    def test_with_all_fields(self):
        """Test SyncJob with all fields populated."""
        now = datetime.utcnow()
        job = SyncJob(
            job_id="job_002",
            source_id="src_002",
            source_name="production",
            streams=["orders", "products"],
            sync_mode="incremental",
            status=SyncStatus.COMPLETED,
            created_at=now - timedelta(minutes=10),
            started_at=now - timedelta(minutes=9),
            completed_at=now,
            records_synced=5000
        )
        assert job.sync_mode == "incremental"
        assert job.status == SyncStatus.COMPLETED
        assert job.records_synced == 5000
        assert len(job.streams) == 2

    def test_to_dict(self):
        """Test SyncJob serialization."""
        job = SyncJob(
            job_id="job_003",
            source_id="src_003",
            source_name="analytics",
            streams=["events"],
            status=SyncStatus.RUNNING,
            records_synced=1000
        )
        d = job.to_dict()
        assert d["job_id"] == "job_003"
        assert d["status"] == "running"
        assert d["streams"] == ["events"]
        assert d["records_synced"] == 1000

    def test_duration_calculation(self):
        """Test duration_seconds property."""
        now = datetime.utcnow()
        job = SyncJob(
            job_id="job_dur",
            source_id="src_dur",
            source_name="test",
            streams=["data"],
            started_at=now - timedelta(seconds=120),
            completed_at=now
        )
        assert job.duration_seconds is not None
        assert 119 <= job.duration_seconds <= 121  # Allow small variance


class TestScheduledSync:
    """Tests for ScheduledSync dataclass."""

    def test_default_values(self):
        """Test ScheduledSync default values."""
        schedule = ScheduledSync(
            schedule_id="sched_001",
            source_id="src_001",
            source_name="scheduled_source",
            streams=["data"],
            cron_expression="0 * * * *"
        )
        assert schedule.enabled is True
        assert schedule.sync_mode == "incremental"
        assert schedule.run_count == 0
        assert schedule.last_run_at is None

    def test_to_dict(self):
        """Test ScheduledSync serialization."""
        schedule = ScheduledSync(
            schedule_id="sched_002",
            source_id="src_002",
            source_name="hourly_sync",
            streams=["users", "orders"],
            cron_expression="0 * * * *",
            enabled=True,
            run_count=24
        )
        d = schedule.to_dict()
        assert d["schedule_id"] == "sched_002"
        assert d["cron_expression"] == "0 * * * *"
        assert d["enabled"] is True
        assert d["run_count"] == 24


class TestSyncScheduler:
    """Tests for SyncScheduler class."""

    @pytest.fixture
    def scheduler(self):
        """Create a fresh SyncScheduler instance."""
        return SyncScheduler(max_concurrent_jobs=3)

    def test_init_with_default_concurrent(self):
        """Test scheduler initializes with default concurrent limit."""
        s = SyncScheduler()
        assert s._max_concurrent_jobs == 5

    def test_init_with_custom_concurrent(self):
        """Test scheduler initializes with custom concurrent limit."""
        s = SyncScheduler(max_concurrent_jobs=10)
        assert s._max_concurrent_jobs == 10

    def test_create_job(self, scheduler):
        """Test creating a new sync job."""
        job = scheduler.create_job(
            source_id="src_001",
            source_name="test_source",
            streams=["users", "orders"]
        )
        assert job.job_id is not None
        assert job.job_id.startswith("job_")
        assert job.source_id == "src_001"
        assert job.status == SyncStatus.PENDING

    def test_create_job_with_sync_mode(self, scheduler):
        """Test creating job with specific sync mode."""
        job = scheduler.create_job(
            source_id="src_002",
            source_name="incremental_source",
            streams=["events"],
            sync_mode="incremental"
        )
        assert job.sync_mode == "incremental"

    def test_get_job_exists(self, scheduler):
        """Test getting existing job."""
        created = scheduler.create_job("src", "name", ["stream"])
        retrieved = scheduler.get_job(created.job_id)
        assert retrieved is not None
        assert retrieved.job_id == created.job_id

    def test_get_job_not_exists(self, scheduler):
        """Test getting non-existent job returns None."""
        job = scheduler.get_job("nonexistent_job")
        assert job is None

    def test_list_jobs_empty(self, scheduler):
        """Test listing jobs when none exist."""
        jobs = scheduler.list_jobs()
        assert jobs == []

    def test_list_jobs_with_jobs(self, scheduler):
        """Test listing jobs returns all jobs."""
        scheduler.create_job("src_1", "name_1", ["a"])
        scheduler.create_job("src_2", "name_2", ["b"])
        scheduler.create_job("src_3", "name_3", ["c"])

        jobs = scheduler.list_jobs()
        assert len(jobs) == 3

    def test_list_jobs_with_limit(self, scheduler):
        """Test listing jobs respects limit."""
        for i in range(10):
            scheduler.create_job(f"src_{i}", f"name_{i}", ["stream"])

        jobs = scheduler.list_jobs(limit=5)
        assert len(jobs) == 5

    def test_list_jobs_filter_by_status(self, scheduler):
        """Test filtering jobs by status."""
        job1 = scheduler.create_job("src_1", "name_1", ["a"])
        job2 = scheduler.create_job("src_2", "name_2", ["b"])

        # Manually set status for testing
        scheduler._jobs[job1.job_id].status = SyncStatus.COMPLETED
        scheduler._jobs[job2.job_id].status = SyncStatus.PENDING

        completed = scheduler.list_jobs(status=SyncStatus.COMPLETED)
        assert len(completed) == 1
        assert completed[0].job_id == job1.job_id

    def test_get_running_jobs(self, scheduler):
        """Test getting only running jobs."""
        job1 = scheduler.create_job("src_1", "name_1", ["a"])
        job2 = scheduler.create_job("src_2", "name_2", ["b"])
        job3 = scheduler.create_job("src_3", "name_3", ["c"])

        scheduler._jobs[job1.job_id].status = SyncStatus.RUNNING
        scheduler._jobs[job2.job_id].status = SyncStatus.RUNNING
        scheduler._jobs[job3.job_id].status = SyncStatus.PENDING

        running = scheduler.get_running_jobs()
        assert len(running) == 2

    @pytest.mark.asyncio
    async def test_run_job_success(self, scheduler):
        """Test running a job successfully."""
        job = scheduler.create_job("src", "name", ["stream"])

        # Mock executor
        async def mock_executor():
            return {"records": 100}

        result = await scheduler.run_sync_job(job.job_id, executor_fn=mock_executor)

        assert result.status == SyncStatus.COMPLETED
        assert result.started_at is not None
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_run_job_failure(self, scheduler):
        """Test job failure is handled correctly."""
        job = scheduler.create_job("src", "name", ["stream"])

        async def failing_executor():
            raise Exception("Connection failed")

        result = await scheduler.run_sync_job(job.job_id, executor_fn=failing_executor)

        assert result.status == SyncStatus.FAILED
        assert result.error_message == "Connection failed"

    @pytest.mark.asyncio
    async def test_run_job_not_found(self, scheduler):
        """Test running non-existent job raises error."""
        with pytest.raises(ValueError, match="Job .* not found"):
            await scheduler.run_sync_job("nonexistent")

    @pytest.mark.asyncio
    async def test_cancel_running_job(self, scheduler):
        """Test cancelling a running job."""
        job = scheduler.create_job("src", "name", ["stream"])
        scheduler._jobs[job.job_id].status = SyncStatus.RUNNING

        result = scheduler.cancel_job(job.job_id)

        assert result is True
        assert scheduler._jobs[job.job_id].status == SyncStatus.CANCELLED

    def test_cancel_completed_job(self, scheduler):
        """Test that completed jobs cannot be cancelled."""
        job = scheduler.create_job("src", "name", ["stream"])
        scheduler._jobs[job.job_id].status = SyncStatus.COMPLETED

        result = scheduler.cancel_job(job.job_id)

        assert result is False
        assert scheduler._jobs[job.job_id].status == SyncStatus.COMPLETED

    def test_get_stats(self, scheduler):
        """Test getting scheduler statistics."""
        # Create jobs with various statuses
        for i in range(3):
            job = scheduler.create_job(f"src_{i}", f"name_{i}", ["s"])
            scheduler._jobs[job.job_id].status = SyncStatus.COMPLETED
            scheduler._jobs[job.job_id].records_synced = 100

        for i in range(2):
            job = scheduler.create_job(f"src_r{i}", f"name_r{i}", ["s"])
            scheduler._jobs[job.job_id].status = SyncStatus.RUNNING

        job = scheduler.create_job("src_f", "name_f", ["s"])
        scheduler._jobs[job.job_id].status = SyncStatus.FAILED

        stats = scheduler.get_stats()

        assert stats["total_jobs"] == 6
        assert stats["completed_jobs"] == 3
        assert stats["running_jobs"] == 2
        assert stats["failed_jobs"] == 1
        assert stats["total_records_synced"] == 300


class TestScheduledSyncs:
    """Tests for scheduled sync management."""

    @pytest.fixture
    def scheduler(self):
        return SyncScheduler()

    def test_create_schedule(self, scheduler):
        """Test creating a new schedule."""
        schedule = scheduler.create_schedule(
            source_id="src_001",
            source_name="hourly_source",
            streams=["data"],
            cron_expression="0 * * * *"
        )
        assert schedule.schedule_id is not None
        assert schedule.cron_expression == "0 * * * *"
        assert schedule.enabled is True

    def test_get_schedule_exists(self, scheduler):
        """Test getting existing schedule."""
        created = scheduler.create_schedule("src", "name", ["s"], "0 * * * *")
        retrieved = scheduler.get_schedule(created.schedule_id)
        assert retrieved is not None
        assert retrieved.schedule_id == created.schedule_id

    def test_get_schedule_not_exists(self, scheduler):
        """Test getting non-existent schedule."""
        schedule = scheduler.get_schedule("nonexistent")
        assert schedule is None

    def test_list_schedules(self, scheduler):
        """Test listing all schedules."""
        scheduler.create_schedule("src_1", "name_1", ["a"], "0 * * * *")
        scheduler.create_schedule("src_2", "name_2", ["b"], "0 0 * * *")

        schedules = scheduler.list_schedules()
        assert len(schedules) == 2

    def test_update_schedule_enable_disable(self, scheduler):
        """Test enabling/disabling schedule."""
        schedule = scheduler.create_schedule("src", "name", ["s"], "0 * * * *")
        assert schedule.enabled is True

        scheduler.update_schedule(schedule.schedule_id, enabled=False)
        updated = scheduler.get_schedule(schedule.schedule_id)
        assert updated.enabled is False

    def test_update_schedule_cron(self, scheduler):
        """Test updating schedule cron expression."""
        schedule = scheduler.create_schedule("src", "name", ["s"], "0 * * * *")

        scheduler.update_schedule(schedule.schedule_id, cron_expression="0 0 * * *")
        updated = scheduler.get_schedule(schedule.schedule_id)
        assert updated.cron_expression == "0 0 * * *"

    def test_delete_schedule(self, scheduler):
        """Test deleting a schedule."""
        schedule = scheduler.create_schedule("src", "name", ["s"], "0 * * * *")
        assert scheduler.get_schedule(schedule.schedule_id) is not None

        scheduler.delete_schedule(schedule.schedule_id)
        assert scheduler.get_schedule(schedule.schedule_id) is None

    @pytest.mark.asyncio
    async def test_trigger_schedule(self, scheduler):
        """Test manually triggering a schedule."""
        schedule = scheduler.create_schedule("src", "name", ["stream"], "0 * * * *")

        job = await scheduler.trigger_schedule(schedule.schedule_id)

        assert job is not None
        assert job.source_id == "src"
        assert job.streams == ["stream"]

        # Check schedule was updated
        updated_schedule = scheduler.get_schedule(schedule.schedule_id)
        assert updated_schedule.run_count == 1
        assert updated_schedule.last_run_at is not None


class TestGetSyncScheduler:
    """Tests for the singleton scheduler getter."""

    def test_returns_same_instance(self):
        """Test that get_sync_scheduler returns singleton."""
        scheduler1 = get_sync_scheduler()
        scheduler2 = get_sync_scheduler()
        assert scheduler1 is scheduler2

    def test_returns_sync_scheduler_instance(self):
        """Test that returned instance is correct type."""
        scheduler = get_sync_scheduler()
        assert isinstance(scheduler, SyncScheduler)


class TestConcurrencyLimits:
    """Tests for concurrent job limits."""

    @pytest.fixture
    def scheduler(self):
        return SyncScheduler(max_concurrent_jobs=2)

    def test_max_concurrent_respected(self, scheduler):
        """Test that max concurrent jobs is enforced."""
        # Create 3 jobs and set 2 as running
        job1 = scheduler.create_job("src_1", "name_1", ["a"])
        job2 = scheduler.create_job("src_2", "name_2", ["b"])
        job3 = scheduler.create_job("src_3", "name_3", ["c"])

        scheduler._jobs[job1.job_id].status = SyncStatus.RUNNING
        scheduler._jobs[job2.job_id].status = SyncStatus.RUNNING

        running = scheduler.get_running_jobs()
        assert len(running) == 2

        # Check if can start new job
        can_start = scheduler.can_start_new_job()
        assert can_start is False

    def test_can_start_when_under_limit(self, scheduler):
        """Test that new jobs can start when under limit."""
        job1 = scheduler.create_job("src_1", "name_1", ["a"])
        scheduler._jobs[job1.job_id].status = SyncStatus.RUNNING

        can_start = scheduler.can_start_new_job()
        assert can_start is True
