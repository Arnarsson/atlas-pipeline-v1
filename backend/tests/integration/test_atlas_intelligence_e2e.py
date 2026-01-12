"""
End-to-End Integration Tests for AtlasIntelligence

Tests complete workflows from connector configuration to data sync.
"""
import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any, List

from app.connectors.airbyte.pyairbyte_executor import PyAirbyteExecutor, get_pyairbyte_executor
from app.connectors.airbyte.state_manager import StateManager, get_state_manager
from app.connectors.airbyte.sync_scheduler import SyncScheduler, get_sync_scheduler, SyncStatus


class TestCompleteConnectorWorkflow:
    """
    End-to-end test for complete connector workflow:
    1. List available connectors
    2. Configure a source
    3. Discover streams
    4. Create sync job
    5. Run sync
    6. Track state
    7. Run incremental sync
    """

    @pytest.fixture
    def executor(self):
        return PyAirbyteExecutor()

    @pytest.fixture
    def state_manager(self):
        return StateManager()

    @pytest.fixture
    def scheduler(self):
        return SyncScheduler(max_concurrent_jobs=3)

    @pytest.mark.asyncio
    async def test_complete_postgres_workflow(self, executor, state_manager, scheduler):
        """Test complete workflow for PostgreSQL connector."""

        # Step 1: List connectors and find PostgreSQL
        connectors = executor.list_available_connectors(category="database")
        postgres_connectors = [c for c in connectors if "postgres" in c["name"].lower()]
        assert len(postgres_connectors) > 0, "PostgreSQL connector should be available"

        postgres = postgres_connectors[0]
        assert postgres["category"] == "database"

        # Step 2: Configure the source
        config = {
            "host": "localhost",
            "port": 5432,
            "database": "atlas_test",
            "username": "atlas_user",
            "password": "test_password",
            "ssl_mode": "prefer"
        }
        source_id = await executor.configure_source("source-postgres", config)
        assert source_id is not None
        assert source_id.startswith("src_")

        # Step 3: Discover streams
        streams = await executor.discover_streams(source_id)
        assert isinstance(streams, list)
        assert len(streams) > 0

        stream_names = [s["name"] for s in streams]

        # Step 4: Initialize state for incremental sync
        state_manager.create_source_state(
            source_id=source_id,
            source_name="postgres_test",
            streams=stream_names
        )

        # Verify state created
        source_state = state_manager.get_source_state(source_id)
        assert source_state is not None
        assert source_state.source_name == "postgres_test"
        assert len(source_state.streams) == len(stream_names)

        # Step 5: Create and run sync job
        job = scheduler.create_job(
            source_id=source_id,
            source_name="postgres_test",
            streams=stream_names[:2],  # Just first 2 streams
            sync_mode="full_refresh"
        )
        assert job.status == SyncStatus.PENDING

        # Mock executor for sync
        async def mock_sync_executor():
            await asyncio.sleep(0.1)  # Simulate work
            return {"records_synced": 150, "status": "success"}

        result = await scheduler.run_sync_job(job.job_id, executor_fn=mock_sync_executor)
        assert result.status == SyncStatus.COMPLETED

        # Step 6: Update state after sync
        state_manager.update_stream_state(
            source_id=source_id,
            stream_name=stream_names[0],
            cursor_field="updated_at",
            cursor_value="2024-01-15T12:00:00Z",
            records_synced=100
        )

        state_manager.update_stream_state(
            source_id=source_id,
            stream_name=stream_names[1],
            cursor_field="id",
            cursor_value=500,
            records_synced=50
        )

        # Verify state updated
        updated_state = state_manager.get_source_state(source_id)
        assert updated_state.streams[stream_names[0]].cursor_value == "2024-01-15T12:00:00Z"
        assert updated_state.streams[stream_names[1]].cursor_value == 500

        # Step 7: Create incremental sync job
        incremental_job = scheduler.create_job(
            source_id=source_id,
            source_name="postgres_test",
            streams=stream_names[:2],
            sync_mode="incremental"
        )
        assert incremental_job.sync_mode == "incremental"

        # Run incremental sync
        result2 = await scheduler.run_sync_job(incremental_job.job_id, executor_fn=mock_sync_executor)
        assert result2.status == SyncStatus.COMPLETED

        # Verify job history
        all_jobs = scheduler.list_jobs()
        assert len(all_jobs) >= 2

        # Verify stats
        stats = scheduler.get_stats()
        assert stats["completed_jobs"] >= 2

    @pytest.mark.asyncio
    async def test_complete_crm_workflow(self, executor, state_manager, scheduler):
        """Test complete workflow for CRM connector (Salesforce)."""

        # Step 1: List CRM connectors
        connectors = executor.list_available_connectors(category="crm")
        salesforce_connectors = [c for c in connectors if "salesforce" in c["name"].lower()]
        assert len(salesforce_connectors) > 0

        # Step 2: Configure Salesforce source
        config = {
            "client_id": "test_client_id",
            "client_secret": "test_secret",
            "refresh_token": "test_refresh_token",
            "instance_url": "https://test.salesforce.com"
        }
        source_id = await executor.configure_source("source-salesforce", config)
        assert source_id is not None

        # Step 3: Discover streams
        streams = await executor.discover_streams(source_id)
        stream_names = [s["name"] for s in streams]

        # Step 4: Create schedule for regular syncs
        schedule = scheduler.create_schedule(
            source_id=source_id,
            source_name="salesforce_crm",
            streams=stream_names,
            cron_expression="0 */6 * * *",  # Every 6 hours
            sync_mode="incremental"
        )
        assert schedule.enabled is True
        assert schedule.cron_expression == "0 */6 * * *"

        # Step 5: Trigger schedule manually
        async def mock_crm_sync():
            return {"records": 500}

        triggered_job = await scheduler.trigger_schedule(schedule.schedule_id)
        assert triggered_job is not None
        assert triggered_job.source_id == source_id

        # Step 6: Verify schedule updated
        updated_schedule = scheduler.get_schedule(schedule.schedule_id)
        assert updated_schedule.run_count == 1
        assert updated_schedule.last_run_at is not None


class TestMultiSourceSyncOrchestration:
    """Test orchestrating syncs across multiple data sources."""

    @pytest.fixture
    def executor(self):
        return PyAirbyteExecutor()

    @pytest.fixture
    def state_manager(self):
        return StateManager()

    @pytest.fixture
    def scheduler(self):
        return SyncScheduler(max_concurrent_jobs=3)

    @pytest.mark.asyncio
    async def test_concurrent_syncs(self, executor, state_manager, scheduler):
        """Test running multiple syncs concurrently."""

        # Configure multiple sources
        sources = []
        for i, connector_id in enumerate(["source-postgres", "source-mysql", "source-mongodb"]):
            source_id = await executor.configure_source(connector_id, {"host": f"db{i}.local"})
            sources.append({
                "source_id": source_id,
                "connector_id": connector_id,
                "name": f"source_{i}"
            })

        # Create jobs for all sources
        jobs = []
        for source in sources:
            job = scheduler.create_job(
                source_id=source["source_id"],
                source_name=source["name"],
                streams=["table1", "table2"],
                sync_mode="full_refresh"
            )
            jobs.append(job)

        assert len(jobs) == 3

        # Run all jobs concurrently (respecting max_concurrent limit)
        async def quick_sync():
            await asyncio.sleep(0.05)
            return {"ok": True}

        # Start all jobs
        tasks = []
        for job in jobs:
            task = scheduler.run_sync_job(job.job_id, executor_fn=quick_sync)
            tasks.append(task)

        # Wait for all to complete
        results = await asyncio.gather(*tasks)

        # Verify all completed
        assert all(r.status == SyncStatus.COMPLETED for r in results)

        # Check stats
        stats = scheduler.get_stats()
        assert stats["completed_jobs"] == 3
        assert stats["running_jobs"] == 0

    @pytest.mark.asyncio
    async def test_sync_failure_handling(self, executor, state_manager, scheduler):
        """Test handling sync failures gracefully."""

        source_id = await executor.configure_source("source-postgres", {"host": "failing.local"})

        job = scheduler.create_job(
            source_id=source_id,
            source_name="failing_source",
            streams=["data"],
            sync_mode="full_refresh"
        )

        # Simulate failure
        async def failing_sync():
            raise ConnectionError("Database connection refused")

        result = await scheduler.run_sync_job(job.job_id, executor_fn=failing_sync)

        assert result.status == SyncStatus.FAILED
        assert result.error_message == "Database connection refused"

        # Verify stats reflect failure
        stats = scheduler.get_stats()
        assert stats["failed_jobs"] >= 1


class TestStateRecoveryScenarios:
    """Test state management recovery scenarios."""

    @pytest.fixture
    def state_manager(self):
        return StateManager()

    def test_export_import_state_recovery(self, state_manager):
        """Test exporting and importing state for disaster recovery."""

        # Create multiple source states
        state_manager.create_source_state("src_1", "production_db", ["users", "orders"])
        state_manager.update_stream_state("src_1", "users", cursor_field="id", cursor_value=10000, records_synced=5000)
        state_manager.update_stream_state("src_1", "orders", cursor_field="created_at", cursor_value="2024-01-15", records_synced=15000)

        state_manager.create_source_state("src_2", "analytics_db", ["events"])
        state_manager.update_stream_state("src_2", "events", cursor_field="timestamp", cursor_value="2024-01-15T23:59:59Z", records_synced=1000000)

        # Export all state
        exported = state_manager.export_state()

        # Verify export structure
        assert "sources" in exported
        assert "src_1" in exported["sources"]
        assert "src_2" in exported["sources"]

        # Create new state manager (simulating recovery)
        new_state_manager = StateManager()

        # Import state
        new_state_manager.import_state(exported)

        # Verify recovery
        recovered_src1 = new_state_manager.get_source_state("src_1")
        assert recovered_src1 is not None
        assert recovered_src1.streams["users"].cursor_value == 10000
        assert recovered_src1.streams["orders"].records_synced == 15000

        recovered_src2 = new_state_manager.get_source_state("src_2")
        assert recovered_src2 is not None
        assert recovered_src2.streams["events"].records_synced == 1000000

    def test_partial_sync_state_recovery(self, state_manager):
        """Test recovering from a partial sync failure."""

        # Setup initial state
        state_manager.create_source_state("partial_src", "partial_db", ["stream_a", "stream_b", "stream_c"])

        # Simulate partial sync - stream_a completed, stream_b partial, stream_c not started
        state_manager.update_stream_state(
            "partial_src", "stream_a",
            cursor_field="id", cursor_value=1000,
            records_synced=1000, sync_mode="incremental"
        )

        state_manager.update_stream_state(
            "partial_src", "stream_b",
            cursor_field="id", cursor_value=500,  # Partial progress
            records_synced=500, sync_mode="incremental"
        )

        # stream_c has no cursor (not started)

        # Get state for recovery planning
        state = state_manager.get_source_state("partial_src")

        # Determine what needs to be synced
        needs_full_refresh = []
        needs_incremental = []

        for stream_name, stream_state in state.streams.items():
            if stream_state.cursor_value is None:
                needs_full_refresh.append(stream_name)
            else:
                needs_incremental.append(stream_name)

        assert "stream_c" in needs_full_refresh
        assert "stream_a" in needs_incremental
        assert "stream_b" in needs_incremental


class TestScheduleManagement:
    """Test schedule lifecycle management."""

    @pytest.fixture
    def scheduler(self):
        return SyncScheduler()

    def test_schedule_lifecycle(self, scheduler):
        """Test complete schedule lifecycle: create, update, disable, delete."""

        # Create schedule
        schedule = scheduler.create_schedule(
            source_id="lifecycle_src",
            source_name="Lifecycle Test",
            streams=["data"],
            cron_expression="0 * * * *",  # Hourly
            sync_mode="incremental"
        )

        assert schedule.enabled is True
        assert schedule.run_count == 0

        # Update cron expression
        scheduler.update_schedule(schedule.schedule_id, cron_expression="0 0 * * *")  # Daily
        updated = scheduler.get_schedule(schedule.schedule_id)
        assert updated.cron_expression == "0 0 * * *"

        # Disable schedule
        scheduler.update_schedule(schedule.schedule_id, enabled=False)
        disabled = scheduler.get_schedule(schedule.schedule_id)
        assert disabled.enabled is False

        # Re-enable
        scheduler.update_schedule(schedule.schedule_id, enabled=True)
        reenabled = scheduler.get_schedule(schedule.schedule_id)
        assert reenabled.enabled is True

        # Delete
        scheduler.delete_schedule(schedule.schedule_id)
        deleted = scheduler.get_schedule(schedule.schedule_id)
        assert deleted is None

    def test_multiple_schedules_same_source(self, scheduler):
        """Test creating multiple schedules for the same source."""

        source_id = "multi_sched_src"

        # Create different schedules for different streams
        schedule1 = scheduler.create_schedule(
            source_id=source_id,
            source_name="Multi Schedule Source",
            streams=["high_priority"],
            cron_expression="*/15 * * * *",  # Every 15 minutes
            sync_mode="incremental"
        )

        schedule2 = scheduler.create_schedule(
            source_id=source_id,
            source_name="Multi Schedule Source",
            streams=["low_priority"],
            cron_expression="0 0 * * *",  # Daily
            sync_mode="full_refresh"
        )

        # Verify both exist
        all_schedules = scheduler.list_schedules()
        source_schedules = [s for s in all_schedules if s.source_id == source_id]
        assert len(source_schedules) == 2

        # Verify different configurations
        assert schedule1.cron_expression != schedule2.cron_expression
        assert schedule1.sync_mode != schedule2.sync_mode


class TestCategoryAndSearchWorkflows:
    """Test connector discovery workflows."""

    @pytest.fixture
    def executor(self):
        return PyAirbyteExecutor()

    def test_browse_by_category(self, executor):
        """Test browsing connectors by category."""

        categories = executor.get_categories()

        # Verify all expected categories
        category_names = [c["category"] for c in categories]
        expected = ["database", "crm", "marketing", "ecommerce", "analytics",
                   "project", "communication", "storage", "hr", "finance", "development"]

        for cat in expected:
            assert cat in category_names

        # Browse each category
        for category_info in categories:
            connectors = executor.list_available_connectors(category=category_info["category"])
            assert len(connectors) == category_info["count"]
            assert all(c["category"] == category_info["category"] for c in connectors)

    def test_search_connectors(self, executor):
        """Test searching for specific connectors."""

        # Search for database connectors
        db_results = executor.list_available_connectors(search="sql")
        assert len(db_results) > 0

        # Search for specific connector
        stripe_results = executor.list_available_connectors(search="stripe")
        assert len(stripe_results) > 0
        assert any("stripe" in c["name"].lower() for c in stripe_results)

        # Combined search and category
        mysql_results = executor.list_available_connectors(category="database", search="mysql")
        assert len(mysql_results) > 0
        assert all(c["category"] == "database" for c in mysql_results)

    def test_connector_metadata(self, executor):
        """Test that connector metadata is complete."""

        all_connectors = executor.list_available_connectors()

        for connector in all_connectors:
            # Verify required fields
            assert "id" in connector
            assert "name" in connector
            assert "category" in connector
            assert "status" in connector

            # Verify ID format
            assert connector["id"].startswith("source-")

            # Verify category is valid
            valid_categories = ["database", "crm", "marketing", "ecommerce", "analytics",
                              "project", "communication", "storage", "hr", "finance", "development"]
            assert connector["category"] in valid_categories
