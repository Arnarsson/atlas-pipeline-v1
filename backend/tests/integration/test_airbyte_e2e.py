"""
End-to-End Integration Tests for Airbyte Pipeline

Tests complete data flow from Airbyte sync through all database layers:
1. Read from Airbyte (mock)
2. Write to explore layer (raw JSONB)
3. PII detection
4. Quality validation
5. Write to chart layer (validated)
6. Write to navigate layer (SCD Type 2)
7. State persistence

Author: Atlas Pipeline Team
Date: January 13, 2026
"""
import pytest
import asyncio
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestAirbyteOrchestratorE2E:
    """
    End-to-end tests for AirbyteOrchestrator.

    Verifies complete pipeline execution from source to all database layers.
    """

    @pytest.fixture
    def mock_records(self) -> List[Dict[str, Any]]:
        """Sample records simulating Airbyte sync output."""
        return [
            {"id": 1, "name": "John Doe", "email": "john@example.com", "updated_at": "2026-01-13T10:00:00Z"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "updated_at": "2026-01-13T10:01:00Z"},
            {"id": 3, "name": "Bob Wilson", "email": "bob@example.com", "updated_at": "2026-01-13T10:02:00Z"},
        ]

    @pytest.fixture
    def mock_executor(self, mock_records):
        """Create mock PyAirbyte executor."""
        executor = MagicMock()

        async def mock_read_stream(*args, **kwargs):
            for record in mock_records:
                yield record

        executor.read_stream = mock_read_stream
        return executor

    @pytest.fixture
    def mock_writer(self):
        """Create mock database writer."""
        writer = AsyncMock()
        writer.write_to_explore = AsyncMock(return_value=3)
        writer.write_to_chart = AsyncMock(return_value=3)
        writer.write_to_navigate = AsyncMock(return_value=3)
        return writer

    @pytest.fixture
    def mock_state_manager(self):
        """Create mock state manager."""
        state_manager = MagicMock()
        state_manager.update_stream_state = AsyncMock()
        state_manager.get_cursor_value = MagicMock(return_value=None)
        return state_manager

    @pytest.fixture
    def mock_pii_detector(self):
        """Create mock PII detector."""
        detector = MagicMock()
        detector.detect_pii = AsyncMock(return_value={
            "total_detections": 3,
            "detections_by_type": {"email": 3},
            "detections": [
                {"type": "email", "value": "john@example.com", "column": "email", "confidence": 0.95},
                {"type": "email", "value": "jane@example.com", "column": "email", "confidence": 0.95},
                {"type": "email", "value": "bob@example.com", "column": "email", "confidence": 0.95},
            ]
        })
        return detector

    @pytest.fixture
    def mock_quality_validator(self):
        """Create mock quality validator."""
        validator = MagicMock()
        validator.validate_data = AsyncMock(return_value={
            "overall_score": 95.5,
            "dimensions": {
                "completeness": {"score": 100, "status": "pass"},
                "uniqueness": {"score": 100, "status": "pass"},
                "validity": {"score": 90, "status": "pass"},
                "accuracy": {"score": 95, "status": "pass"},
                "consistency": {"score": 93, "status": "pass"},
                "timeliness": {"score": 95, "status": "pass"},
            }
        })
        return validator

    @pytest.mark.asyncio
    async def test_execute_full_sync_success(
        self,
        mock_executor,
        mock_writer,
        mock_state_manager,
        mock_pii_detector,
        mock_quality_validator,
        mock_records
    ):
        """Test successful full sync execution."""
        from app.connectors.airbyte.airbyte_orchestrator import AirbyteOrchestrator

        orchestrator = AirbyteOrchestrator(
            executor=mock_executor,
            writer=mock_writer,
            state_manager=mock_state_manager,
            pii_detector=mock_pii_detector,
            quality_validator=mock_quality_validator
        )

        result = await orchestrator.execute_full_sync(
            source_id="test-postgres",
            stream_name="users",
            sync_mode="incremental"
        )

        # Verify success
        assert result["status"] == "completed"
        assert result["records_synced"] == 3
        assert result["source_id"] == "test-postgres"
        assert result["stream_name"] == "users"

        # Verify all layers written
        assert result["explore_records"] == 3
        assert result["chart_records"] == 3
        assert result["navigate_records"] == 3
        assert result["layers_written"] == ["explore", "chart", "navigate"]

        # Verify PII and quality metrics
        assert result["pii_detections"] == 3
        assert result["quality_score"] == 95.5

        # Verify checks performed
        assert result["checks_performed"]["pii_detection"] is True
        assert result["checks_performed"]["quality_validation"] is True
        assert result["checks_performed"]["state_updated"] is True
        assert result["checks_performed"]["lineage_tracked"] is True

    @pytest.mark.asyncio
    async def test_execute_full_sync_writes_to_explore(
        self,
        mock_executor,
        mock_writer,
        mock_state_manager,
        mock_records
    ):
        """Test that sync writes raw data to explore layer."""
        from app.connectors.airbyte.airbyte_orchestrator import AirbyteOrchestrator

        orchestrator = AirbyteOrchestrator(
            executor=mock_executor,
            writer=mock_writer,
            state_manager=mock_state_manager
        )

        await orchestrator.execute_full_sync(
            source_id="test-postgres",
            stream_name="users",
            sync_mode="full_refresh"
        )

        # Verify explore layer write was called
        mock_writer.write_to_explore.assert_called_once()
        call_args = mock_writer.write_to_explore.call_args

        assert call_args[1]["source_id"] == "test-postgres"
        assert call_args[1]["stream_name"] == "users"
        assert len(call_args[1]["records"]) == 3

    @pytest.mark.asyncio
    async def test_execute_full_sync_writes_to_chart_with_metadata(
        self,
        mock_executor,
        mock_writer,
        mock_state_manager,
        mock_pii_detector,
        mock_quality_validator
    ):
        """Test that sync writes validated data with PII/quality metadata to chart layer."""
        from app.connectors.airbyte.airbyte_orchestrator import AirbyteOrchestrator

        orchestrator = AirbyteOrchestrator(
            executor=mock_executor,
            writer=mock_writer,
            state_manager=mock_state_manager,
            pii_detector=mock_pii_detector,
            quality_validator=mock_quality_validator
        )

        await orchestrator.execute_full_sync(
            source_id="test-postgres",
            stream_name="users",
            sync_mode="incremental"
        )

        # Verify chart layer write was called with PII and quality results
        mock_writer.write_to_chart.assert_called_once()
        call_args = mock_writer.write_to_chart.call_args

        assert call_args[1]["source_id"] == "test-postgres"
        assert call_args[1]["stream_name"] == "users"
        assert "pii_results" in call_args[1]
        assert "quality_results" in call_args[1]
        assert call_args[1]["pii_results"]["total_detections"] == 3
        assert call_args[1]["quality_results"]["overall_score"] == 95.5

    @pytest.mark.asyncio
    async def test_execute_full_sync_writes_to_navigate_scd2(
        self,
        mock_executor,
        mock_writer,
        mock_state_manager
    ):
        """Test that sync writes business data to navigate layer with SCD Type 2."""
        from app.connectors.airbyte.airbyte_orchestrator import AirbyteOrchestrator

        orchestrator = AirbyteOrchestrator(
            executor=mock_executor,
            writer=mock_writer,
            state_manager=mock_state_manager
        )

        await orchestrator.execute_full_sync(
            source_id="test-postgres",
            stream_name="users",
            sync_mode="incremental",
            natural_key_column="id"
        )

        # Verify navigate layer write was called
        mock_writer.write_to_navigate.assert_called_once()
        call_args = mock_writer.write_to_navigate.call_args

        assert call_args[1]["source_id"] == "test-postgres"
        assert call_args[1]["stream_name"] == "users"
        assert call_args[1]["natural_key_column"] == "id"

    @pytest.mark.asyncio
    async def test_execute_full_sync_updates_state_incremental(
        self,
        mock_executor,
        mock_writer,
        mock_state_manager
    ):
        """Test that incremental sync updates state cursor."""
        from app.connectors.airbyte.airbyte_orchestrator import AirbyteOrchestrator

        orchestrator = AirbyteOrchestrator(
            executor=mock_executor,
            writer=mock_writer,
            state_manager=mock_state_manager
        )

        await orchestrator.execute_full_sync(
            source_id="test-postgres",
            stream_name="users",
            sync_mode="incremental"
        )

        # Verify state was updated
        mock_state_manager.update_stream_state.assert_called()

    @pytest.mark.asyncio
    async def test_execute_full_sync_skips_state_full_refresh(
        self,
        mock_executor,
        mock_writer,
        mock_state_manager
    ):
        """Test that full refresh does not update incremental state."""
        from app.connectors.airbyte.airbyte_orchestrator import AirbyteOrchestrator

        orchestrator = AirbyteOrchestrator(
            executor=mock_executor,
            writer=mock_writer,
            state_manager=mock_state_manager
        )

        result = await orchestrator.execute_full_sync(
            source_id="test-postgres",
            stream_name="users",
            sync_mode="full_refresh"
        )

        # State should not be updated for full refresh
        mock_state_manager.update_stream_state.assert_not_called()
        assert result["checks_performed"]["state_updated"] is False

    @pytest.mark.asyncio
    async def test_execute_full_sync_empty_records(
        self,
        mock_writer,
        mock_state_manager
    ):
        """Test handling of empty record set."""
        from app.connectors.airbyte.airbyte_orchestrator import AirbyteOrchestrator

        # Create executor that returns no records
        empty_executor = MagicMock()
        async def mock_empty_read(*args, **kwargs):
            return
            yield  # Empty generator
        empty_executor.read_stream = mock_empty_read

        orchestrator = AirbyteOrchestrator(
            executor=empty_executor,
            writer=mock_writer,
            state_manager=mock_state_manager
        )

        result = await orchestrator.execute_full_sync(
            source_id="test-postgres",
            stream_name="users",
            sync_mode="incremental"
        )

        assert result["status"] == "completed"
        assert result["records_synced"] == 0
        assert "No new records" in result["message"]

    @pytest.mark.asyncio
    async def test_execute_full_sync_without_pii_detector(
        self,
        mock_executor,
        mock_writer,
        mock_state_manager,
        mock_quality_validator
    ):
        """Test sync works gracefully without PII detector."""
        from app.connectors.airbyte.airbyte_orchestrator import AirbyteOrchestrator

        orchestrator = AirbyteOrchestrator(
            executor=mock_executor,
            writer=mock_writer,
            state_manager=mock_state_manager,
            pii_detector=None,  # No PII detector
            quality_validator=mock_quality_validator
        )

        result = await orchestrator.execute_full_sync(
            source_id="test-postgres",
            stream_name="users",
            sync_mode="incremental"
        )

        assert result["status"] == "completed"
        assert result["pii_detections"] == 0
        assert result["checks_performed"]["pii_detection"] is False

    @pytest.mark.asyncio
    async def test_execute_full_sync_without_quality_validator(
        self,
        mock_executor,
        mock_writer,
        mock_state_manager,
        mock_pii_detector
    ):
        """Test sync works gracefully without quality validator."""
        from app.connectors.airbyte.airbyte_orchestrator import AirbyteOrchestrator

        orchestrator = AirbyteOrchestrator(
            executor=mock_executor,
            writer=mock_writer,
            state_manager=mock_state_manager,
            pii_detector=mock_pii_detector,
            quality_validator=None  # No quality validator
        )

        result = await orchestrator.execute_full_sync(
            source_id="test-postgres",
            stream_name="users",
            sync_mode="incremental"
        )

        assert result["status"] == "completed"
        assert result["quality_score"] == 100  # Default score when skipped
        assert result["checks_performed"]["quality_validation"] is False

    @pytest.mark.asyncio
    async def test_execute_full_sync_handles_pii_error(
        self,
        mock_executor,
        mock_writer,
        mock_state_manager
    ):
        """Test graceful handling of PII detection errors."""
        from app.connectors.airbyte.airbyte_orchestrator import AirbyteOrchestrator

        # Create failing PII detector
        failing_pii_detector = MagicMock()
        failing_pii_detector.detect_pii = AsyncMock(side_effect=Exception("PII service unavailable"))

        orchestrator = AirbyteOrchestrator(
            executor=mock_executor,
            writer=mock_writer,
            state_manager=mock_state_manager,
            pii_detector=failing_pii_detector
        )

        result = await orchestrator.execute_full_sync(
            source_id="test-postgres",
            stream_name="users",
            sync_mode="incremental"
        )

        # Sync should still complete despite PII error
        assert result["status"] == "completed"
        assert result["records_synced"] == 3

    @pytest.mark.asyncio
    async def test_execute_full_sync_handles_quality_error(
        self,
        mock_executor,
        mock_writer,
        mock_state_manager
    ):
        """Test graceful handling of quality validation errors."""
        from app.connectors.airbyte.airbyte_orchestrator import AirbyteOrchestrator

        # Create failing quality validator
        failing_validator = MagicMock()
        failing_validator.validate_data = AsyncMock(side_effect=Exception("Quality service unavailable"))

        orchestrator = AirbyteOrchestrator(
            executor=mock_executor,
            writer=mock_writer,
            state_manager=mock_state_manager,
            quality_validator=failing_validator
        )

        result = await orchestrator.execute_full_sync(
            source_id="test-postgres",
            stream_name="users",
            sync_mode="incremental"
        )

        # Sync should still complete despite quality error
        assert result["status"] == "completed"
        assert result["records_synced"] == 3


class TestDatabaseWriterE2E:
    """
    End-to-end tests for AirbyteDatabaseWriter.

    Tests actual database operations (mocked pool).
    """

    @pytest.fixture
    def sample_records(self) -> List[Dict[str, Any]]:
        """Sample records for testing."""
        return [
            {"id": 1, "name": "Alice", "email": "alice@test.com"},
            {"id": 2, "name": "Bob", "email": "bob@test.com"},
        ]

    @pytest.fixture
    def sample_df(self, sample_records) -> pd.DataFrame:
        """Sample DataFrame for testing."""
        return pd.DataFrame(sample_records)

    @pytest.mark.asyncio
    async def test_write_to_explore_creates_table(self):
        """Test that write_to_explore creates table if not exists."""
        from app.connectors.airbyte.database_writer import AirbyteDatabaseWriter

        # Create mock pool and connection
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock()

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)

        writer = AirbyteDatabaseWriter(mock_pool)

        records = [{"id": 1, "name": "Test"}]
        run_id = str(uuid4())

        await writer.write_to_explore("test-source", "users", records, run_id)

        # Verify CREATE TABLE was called
        create_table_calls = [
            call for call in mock_conn.execute.call_args_list
            if "CREATE TABLE IF NOT EXISTS" in str(call)
        ]
        assert len(create_table_calls) > 0

    @pytest.mark.asyncio
    async def test_sanitize_table_name(self):
        """Test table name sanitization."""
        from app.connectors.airbyte.database_writer import AirbyteDatabaseWriter

        mock_pool = MagicMock()
        writer = AirbyteDatabaseWriter(mock_pool)

        # Test various inputs
        assert writer._sanitize_table_name("source-postgres_users_raw") == "source_postgres_users_raw"
        assert writer._sanitize_table_name("My-Special-Table!") == "my_special_table_"
        assert writer._sanitize_table_name("123_table") == "_123_table"
        assert writer._sanitize_table_name("normal_table") == "normal_table"

    @pytest.mark.asyncio
    async def test_infer_sql_type(self):
        """Test SQL type inference from pandas dtypes."""
        from app.connectors.airbyte.database_writer import AirbyteDatabaseWriter

        mock_pool = MagicMock()
        writer = AirbyteDatabaseWriter(mock_pool)

        # Test various dtypes
        df = pd.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.1, 2.2, 3.3],
            "str_col": ["a", "b", "c"],
            "bool_col": [True, False, True],
            "date_col": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
        })

        assert writer._infer_sql_type(df["int_col"].dtype) == "BIGINT"
        assert writer._infer_sql_type(df["float_col"].dtype) == "DOUBLE PRECISION"
        assert writer._infer_sql_type(df["str_col"].dtype) == "TEXT"
        assert writer._infer_sql_type(df["bool_col"].dtype) == "BOOLEAN"
        assert writer._infer_sql_type(df["date_col"].dtype) == "TIMESTAMP"

    @pytest.mark.asyncio
    async def test_convert_value_handles_nan(self):
        """Test value conversion handles NaN values."""
        from app.connectors.airbyte.database_writer import AirbyteDatabaseWriter
        import numpy as np

        mock_pool = MagicMock()
        writer = AirbyteDatabaseWriter(mock_pool)

        assert writer._convert_value(np.nan) is None
        assert writer._convert_value(pd.NA) is None
        assert writer._convert_value(None) is None
        assert writer._convert_value(42) == 42
        assert writer._convert_value("test") == "test"


class TestSyncSchedulerE2E:
    """
    End-to-end tests for SyncScheduler with orchestrator integration.
    """

    @pytest.fixture
    def scheduler(self):
        """Create scheduler instance."""
        from app.connectors.airbyte.sync_scheduler import SyncScheduler
        return SyncScheduler(max_concurrent_jobs=3)

    @pytest.mark.asyncio
    async def test_scheduler_with_orchestrator_executor(self, scheduler):
        """Test scheduler executes jobs using orchestrator."""

        # Create mock orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_full_sync = AsyncMock(return_value={
            "run_id": str(uuid4()),
            "status": "completed",
            "records_synced": 100,
            "explore_records": 100,
            "chart_records": 100,
            "navigate_records": 100,
            "pii_detections": 5,
            "quality_score": 95.0
        })

        # Create job
        job = scheduler.create_job(
            source_id="test-source",
            source_name="Test Source",
            streams=["users", "orders"],
            sync_mode="incremental"
        )

        # Define executor function that uses orchestrator
        async def orchestrator_executor():
            return await mock_orchestrator.execute_full_sync(
                source_id="test-source",
                stream_name="users",
                sync_mode="incremental"
            )

        result = await scheduler.run_sync_job(job.job_id, executor_fn=orchestrator_executor)

        from app.connectors.airbyte.sync_scheduler import SyncStatus
        assert result.status == SyncStatus.COMPLETED
        mock_orchestrator.execute_full_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_scheduler_tracks_job_metrics(self, scheduler):
        """Test scheduler tracks comprehensive job metrics."""

        job = scheduler.create_job(
            source_id="metrics-source",
            source_name="Metrics Test",
            streams=["data"],
            sync_mode="full_refresh"
        )

        async def mock_executor():
            await asyncio.sleep(0.1)  # Simulate work
            return {
                "records_synced": 500,
                "pii_detections": 10,
                "quality_score": 98.5
            }

        result = await scheduler.run_sync_job(job.job_id, executor_fn=mock_executor)

        from app.connectors.airbyte.sync_scheduler import SyncStatus
        assert result.status == SyncStatus.COMPLETED

        # Verify stats updated
        stats = scheduler.get_stats()
        assert stats["completed_jobs"] >= 1
        assert stats["total_records_synced"] >= 500


class TestStateManagerE2E:
    """
    End-to-end tests for StateManager integration.
    """

    @pytest.fixture
    def state_manager(self):
        """Create state manager instance (file-based for testing)."""
        from app.connectors.airbyte.state_manager import StateManager
        import tempfile
        from pathlib import Path

        temp_dir = Path(tempfile.mkdtemp())
        return StateManager(storage_path=temp_dir)

    def test_complete_state_lifecycle(self, state_manager):
        """Test complete state lifecycle: create, update, export, import."""

        # Create state
        state = state_manager.create_state(
            source_name="test_postgres",
            source_id="src_001",
            streams=["users", "orders", "products"]
        )

        assert state.source_id == "src_001"
        assert len(state.streams) == 3

        # Update stream states
        state_manager.update_stream_state(
            source_id="src_001",
            stream_name="users",
            cursor_field="updated_at",
            cursor_value="2026-01-13T12:00:00Z",
            records_synced=1000
        )

        state_manager.update_stream_state(
            source_id="src_001",
            stream_name="orders",
            cursor_field="id",
            cursor_value=50000,
            records_synced=5000
        )

        # Verify state updated
        updated_state = state_manager.get_state("src_001")
        assert updated_state.streams["users"].cursor_value == "2026-01-13T12:00:00Z"
        assert updated_state.streams["users"].records_synced == 1000
        assert updated_state.streams["orders"].cursor_value == 50000

        # Export state
        exported = state_manager.export_state("src_001")
        assert exported is not None
        assert exported["source_id"] == "src_001"

        # Import to new state manager
        from app.connectors.airbyte.state_manager import StateManager
        import tempfile
        from pathlib import Path

        new_temp_dir = Path(tempfile.mkdtemp())
        new_state_manager = StateManager(storage_path=new_temp_dir)

        imported_state = new_state_manager.import_state(exported)
        assert imported_state.source_id == "src_001"
        assert imported_state.streams["users"].cursor_value == "2026-01-13T12:00:00Z"

    def test_reset_state_for_full_refresh(self, state_manager):
        """Test resetting state to force full refresh."""

        # Create and update state
        state_manager.create_state("reset_test", "src_reset", ["stream1"])
        state_manager.update_stream_state(
            "src_reset", "stream1",
            cursor_field="id", cursor_value=1000, records_synced=1000
        )

        # Verify cursor set
        assert state_manager.get_cursor_value("src_reset", "stream1") == 1000

        # Reset stream state
        state_manager.reset_stream_state("src_reset", "stream1")

        # Verify cursor cleared
        assert state_manager.get_cursor_value("src_reset", "stream1") is None

    def test_state_persistence(self, state_manager):
        """Test state persists across manager instances."""
        import tempfile
        from pathlib import Path
        from app.connectors.airbyte.state_manager import StateManager

        # Use shared temp directory
        temp_dir = Path(tempfile.mkdtemp())

        # First instance
        sm1 = StateManager(storage_path=temp_dir)
        sm1.create_state("persist_test", "src_persist", ["data"])
        sm1.update_stream_state("src_persist", "data", cursor_value=42)

        # Second instance (simulating restart)
        sm2 = StateManager(storage_path=temp_dir)

        # Verify state persisted
        state = sm2.get_state("src_persist")
        assert state is not None
        assert state.streams["data"].cursor_value == 42


class TestFullPipelineE2E:
    """
    Full pipeline integration tests combining all components.
    """

    @pytest.mark.asyncio
    async def test_complete_sync_workflow(self):
        """Test complete sync workflow from start to finish."""
        from app.connectors.airbyte.pyairbyte_executor import PyAirbyteExecutor
        from app.connectors.airbyte.state_manager import StateManager
        from app.connectors.airbyte.sync_scheduler import SyncScheduler, SyncStatus
        import tempfile
        from pathlib import Path

        # Initialize components
        executor = PyAirbyteExecutor()
        state_manager = StateManager(storage_path=Path(tempfile.mkdtemp()))
        scheduler = SyncScheduler(max_concurrent_jobs=5)

        # Step 1: List available connectors
        connectors = executor.list_available_connectors(category="database")
        assert len(connectors) > 0

        # Step 2: Configure source
        source_id = await executor.configure_source(
            "source-postgres",
            {"host": "localhost", "database": "test"}
        )
        assert source_id.startswith("src_")

        # Step 3: Discover streams
        streams = await executor.discover_streams(source_id)
        assert len(streams) > 0

        # Step 4: Initialize state
        state = state_manager.create_state(
            source_name="postgres_test",
            source_id=source_id,
            streams=[s["name"] for s in streams[:2]]
        )

        # Step 5: Create and run sync job
        job = scheduler.create_job(
            source_id=source_id,
            source_name="postgres_test",
            streams=[s["name"] for s in streams[:2]],
            sync_mode="full_refresh"
        )

        async def mock_sync():
            await asyncio.sleep(0.05)
            return {"records": 100, "status": "success"}

        result = await scheduler.run_sync_job(job.job_id, executor_fn=mock_sync)
        assert result.status == SyncStatus.COMPLETED

        # Step 6: Update state after sync
        state_manager.update_stream_state(
            source_id=source_id,
            stream_name=streams[0]["name"],
            cursor_field="updated_at",
            cursor_value="2026-01-13T12:00:00Z",
            records_synced=100
        )

        # Verify state updated
        cursor = state_manager.get_cursor_value(source_id, streams[0]["name"])
        assert cursor == "2026-01-13T12:00:00Z"

        # Step 7: Run incremental sync
        inc_job = scheduler.create_job(
            source_id=source_id,
            source_name="postgres_test",
            streams=[streams[0]["name"]],
            sync_mode="incremental"
        )

        async def mock_incremental():
            return {"records": 10, "status": "success"}

        inc_result = await scheduler.run_sync_job(inc_job.job_id, executor_fn=mock_incremental)
        assert inc_result.status == SyncStatus.COMPLETED

        # Verify final stats
        stats = scheduler.get_stats()
        assert stats["completed_jobs"] >= 2
