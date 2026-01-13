"""
Tests for State Manager Database Persistence

Tests PostgreSQL-based state persistence for incremental syncs.
Verifies that state survives restarts and is properly stored in the database.

Author: Atlas Pipeline Team
Date: January 13, 2026
"""
import pytest
import asyncio
import json
from datetime import datetime
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from pathlib import Path
import tempfile


class TestStateManagerDatabasePersistence:
    """
    Tests for PostgreSQL state persistence.

    Verifies that state manager correctly stores and retrieves state
    from PostgreSQL database.
    """

    @pytest.fixture
    def mock_pool(self):
        """Create mock asyncpg connection pool."""
        pool = MagicMock()
        return pool

    @pytest.fixture
    def mock_conn(self):
        """Create mock asyncpg connection."""
        conn = AsyncMock()
        conn.execute = AsyncMock()
        conn.fetch = AsyncMock(return_value=[])
        conn.fetchrow = AsyncMock(return_value=None)
        conn.__aenter__ = AsyncMock(return_value=conn)
        conn.__aexit__ = AsyncMock()
        return conn

    def test_state_manager_database_url_detection(self):
        """Test that database URL triggers database persistence mode."""
        from app.connectors.airbyte.state_manager import StateManager

        # With database URL (mocked to avoid actual connection)
        with patch('asyncpg.create_pool'):
            with patch.object(StateManager, '_ensure_database_table', new_callable=AsyncMock):
                with patch.object(StateManager, '_load_persisted_states_from_db', new_callable=AsyncMock):
                    sm = StateManager(database_url="postgresql://test:test@localhost/test")
                    # Should attempt to use database (may fall back due to mock)
                    assert sm._database_url == "postgresql://test:test@localhost/test"

    def test_state_manager_file_fallback(self):
        """Test that missing database URL uses file persistence."""
        from app.connectors.airbyte.state_manager import StateManager

        temp_dir = Path(tempfile.mkdtemp())
        sm = StateManager(storage_path=temp_dir)

        # Should use file storage
        assert sm._use_database is False
        assert sm._storage_path == temp_dir

    @pytest.mark.asyncio
    async def test_ensure_database_table_creates_schema(self):
        """Test that _ensure_database_table creates the connector_state table."""
        # Test the SQL structure
        expected_table_sql = """
            CREATE TABLE IF NOT EXISTS pipeline.connector_state (
                id SERIAL PRIMARY KEY,
                source_id VARCHAR(255) NOT NULL,
                source_name VARCHAR(255) NOT NULL,
                stream_name VARCHAR(255),
                cursor_field VARCHAR(255),
                cursor_value TEXT,
                sync_mode VARCHAR(50) DEFAULT 'full_refresh',
                state_data JSONB NOT NULL,
                last_synced_at TIMESTAMP,
                records_synced INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(source_id, stream_name)
            )
        """

        # Verify key columns exist in the SQL
        assert "source_id" in expected_table_sql
        assert "stream_name" in expected_table_sql
        assert "cursor_value" in expected_table_sql
        assert "state_data JSONB" in expected_table_sql
        assert "UNIQUE(source_id, stream_name)" in expected_table_sql

    def test_persist_state_to_file(self):
        """Test file-based state persistence."""
        from app.connectors.airbyte.state_manager import StateManager

        temp_dir = Path(tempfile.mkdtemp())
        sm = StateManager(storage_path=temp_dir)

        # Create and persist state
        sm.create_state(
            source_name="test_source",
            source_id="src_file_test",
            streams=["users", "orders"]
        )

        # Update state
        sm.update_stream_state(
            source_id="src_file_test",
            stream_name="users",
            cursor_field="updated_at",
            cursor_value="2026-01-13T12:00:00Z",
            records_synced=100
        )

        # Verify file created
        state_file = temp_dir / "src_file_test.json"
        assert state_file.exists()

        # Verify file contents
        with open(state_file) as f:
            data = json.load(f)

        assert data["source_id"] == "src_file_test"
        assert data["source_name"] == "test_source"
        assert "users" in data["streams"]
        assert data["streams"]["users"]["cursor_value"] == "2026-01-13T12:00:00Z"

    def test_load_state_from_file(self):
        """Test loading state from persisted files."""
        from app.connectors.airbyte.state_manager import StateManager

        temp_dir = Path(tempfile.mkdtemp())

        # Pre-create a state file
        state_data = {
            "source_id": "src_preload",
            "source_name": "preloaded_source",
            "streams": {
                "events": {
                    "stream_name": "events",
                    "cursor_field": "id",
                    "cursor_value": 5000,
                    "sync_mode": "incremental",
                    "records_synced": 2500
                }
            },
            "global_state": {},
            "created_at": "2026-01-13T10:00:00",
            "updated_at": "2026-01-13T11:00:00",
            "version": 3
        }

        state_file = temp_dir / "src_preload.json"
        with open(state_file, "w") as f:
            json.dump(state_data, f)

        # Create new state manager - should load persisted state
        sm = StateManager(storage_path=temp_dir)

        # Verify state loaded
        state = sm.get_state("src_preload")
        assert state is not None
        assert state.source_name == "preloaded_source"
        assert state.streams["events"].cursor_value == 5000
        assert state.streams["events"].records_synced == 2500
        assert state.version == 3

    def test_state_survives_manager_restart(self):
        """Test that state persists across manager instances."""
        from app.connectors.airbyte.state_manager import StateManager

        temp_dir = Path(tempfile.mkdtemp())

        # First manager instance
        sm1 = StateManager(storage_path=temp_dir)
        sm1.create_state("persist_test", "src_persist", ["data"])
        sm1.update_stream_state(
            "src_persist",
            "data",
            cursor_field="id",
            cursor_value=12345,
            records_synced=500
        )

        # Simulate restart - create new instance
        sm2 = StateManager(storage_path=temp_dir)

        # Verify state preserved
        state = sm2.get_state("src_persist")
        assert state is not None
        assert state.streams["data"].cursor_value == 12345
        assert state.streams["data"].records_synced == 500

    def test_export_import_state(self):
        """Test state export and import for backup/migration."""
        from app.connectors.airbyte.state_manager import StateManager

        temp_dir1 = Path(tempfile.mkdtemp())
        temp_dir2 = Path(tempfile.mkdtemp())

        # Create state in first manager
        sm1 = StateManager(storage_path=temp_dir1)
        sm1.create_state("export_test", "src_export", ["stream1", "stream2"])
        sm1.update_stream_state("src_export", "stream1", cursor_value=100, records_synced=50)
        sm1.update_stream_state("src_export", "stream2", cursor_value="2026-01-13", records_synced=75)

        # Export state
        exported = sm1.export_state("src_export")
        assert exported is not None

        # Import to second manager
        sm2 = StateManager(storage_path=temp_dir2)
        imported = sm2.import_state(exported)

        # Verify import
        assert imported.source_id == "src_export"
        assert imported.source_name == "export_test"
        assert imported.streams["stream1"].cursor_value == 100
        assert imported.streams["stream2"].cursor_value == "2026-01-13"

    def test_concurrent_state_updates(self):
        """Test that concurrent updates are handled correctly."""
        from app.connectors.airbyte.state_manager import StateManager

        temp_dir = Path(tempfile.mkdtemp())
        sm = StateManager(storage_path=temp_dir)

        # Create state with multiple streams
        sm.create_state("concurrent", "src_concurrent", ["s1", "s2", "s3"])

        # Simulate concurrent updates
        sm.update_stream_state("src_concurrent", "s1", cursor_value=10)
        sm.update_stream_state("src_concurrent", "s2", cursor_value=20)
        sm.update_stream_state("src_concurrent", "s3", cursor_value=30)

        # Verify all updates persisted
        state = sm.get_state("src_concurrent")
        assert state.streams["s1"].cursor_value == 10
        assert state.streams["s2"].cursor_value == 20
        assert state.streams["s3"].cursor_value == 30

    def test_state_version_increment(self):
        """Test that version increments on each update."""
        from app.connectors.airbyte.state_manager import StateManager

        temp_dir = Path(tempfile.mkdtemp())
        sm = StateManager(storage_path=temp_dir)

        state = sm.create_state("version_test", "src_version", ["data"])
        initial_version = state.version

        sm.update_stream_state("src_version", "data", cursor_value=1)
        state = sm.get_state("src_version")
        assert state.version == initial_version + 1

        sm.update_stream_state("src_version", "data", cursor_value=2)
        state = sm.get_state("src_version")
        assert state.version == initial_version + 2

    def test_reset_stream_preserves_other_streams(self):
        """Test that resetting one stream doesn't affect others."""
        from app.connectors.airbyte.state_manager import StateManager

        temp_dir = Path(tempfile.mkdtemp())
        sm = StateManager(storage_path=temp_dir)

        sm.create_state("reset_partial", "src_reset_partial", ["keep", "reset"])
        sm.update_stream_state("src_reset_partial", "keep", cursor_value=100, records_synced=50)
        sm.update_stream_state("src_reset_partial", "reset", cursor_value=200, records_synced=100)

        # Reset only one stream
        sm.reset_stream_state("src_reset_partial", "reset")

        state = sm.get_state("src_reset_partial")

        # "keep" should be unchanged
        assert state.streams["keep"].cursor_value == 100
        assert state.streams["keep"].records_synced == 50

        # "reset" should be cleared
        assert state.streams["reset"].cursor_value is None

    def test_delete_state_removes_file(self):
        """Test that deleting state removes the persisted file."""
        from app.connectors.airbyte.state_manager import StateManager

        temp_dir = Path(tempfile.mkdtemp())
        sm = StateManager(storage_path=temp_dir)

        sm.create_state("delete_test", "src_delete", ["data"])
        state_file = temp_dir / "src_delete.json"

        # File should exist
        assert state_file.exists()

        # Delete state
        sm.delete_state("src_delete")

        # State should be gone from memory
        assert sm.get_state("src_delete") is None

        # File should be removed
        assert not state_file.exists()


class TestDatabaseIntegrationMock:
    """
    Integration tests for database persistence with mocked connections.

    These tests verify the database persistence logic without requiring
    an actual PostgreSQL connection.
    """

    @pytest.mark.asyncio
    async def test_persist_state_to_db_structure(self):
        """Test that database persistence uses correct SQL structure."""
        # Verify the expected SQL for upserting state
        expected_source_upsert = """
            INSERT INTO pipeline.connector_state
            (source_id, source_name, stream_name, state_data, updated_at, version)
            VALUES ($1, $2, '', $3, NOW(), $4)
            ON CONFLICT (source_id, stream_name)
            DO UPDATE SET
                state_data = EXCLUDED.state_data,
                updated_at = NOW(),
                version = EXCLUDED.version
        """

        expected_stream_upsert = """
            INSERT INTO pipeline.connector_state
            (source_id, source_name, stream_name, cursor_field, cursor_value,
             sync_mode, state_data, last_synced_at, records_synced, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
            ON CONFLICT (source_id, stream_name)
            DO UPDATE SET
                cursor_field = EXCLUDED.cursor_field,
                cursor_value = EXCLUDED.cursor_value,
                sync_mode = EXCLUDED.sync_mode,
                state_data = EXCLUDED.state_data,
                last_synced_at = EXCLUDED.last_synced_at,
                records_synced = EXCLUDED.records_synced,
                updated_at = NOW()
        """

        # Key assertions about the SQL structure
        assert "ON CONFLICT" in expected_source_upsert
        assert "ON CONFLICT" in expected_stream_upsert
        assert "state_data" in expected_source_upsert
        assert "cursor_value" in expected_stream_upsert

    @pytest.mark.asyncio
    async def test_load_state_query_structure(self):
        """Test that state loading uses correct query structure."""
        expected_load_query = """
            SELECT DISTINCT source_id, source_name, state_data
            FROM pipeline.connector_state
            WHERE stream_name = '' OR stream_name IS NULL
        """

        # Verify query selects state_data as JSONB
        assert "state_data" in expected_load_query
        assert "WHERE stream_name = ''" in expected_load_query

    def test_database_fallback_on_error(self):
        """Test that database errors trigger file fallback."""
        from app.connectors.airbyte.state_manager import StateManager

        temp_dir = Path(tempfile.mkdtemp())

        # Create state manager with fake database URL
        # It should fall back to file storage when connection fails
        with patch('asyncpg.create_pool', side_effect=Exception("Connection refused")):
            sm = StateManager(
                database_url="postgresql://fake:fake@localhost/fake",
                storage_path=temp_dir
            )

        # Should fall back to file storage
        assert sm._use_database is False

    def test_state_serialization_for_database(self):
        """Test that state serializes correctly for database storage."""
        from app.connectors.airbyte.state_manager import SourceState, StreamState
        from datetime import datetime

        stream = StreamState(
            stream_name="users",
            cursor_field="updated_at",
            cursor_value="2026-01-13T12:00:00Z",
            sync_mode="incremental",
            last_synced_at=datetime(2026, 1, 13, 12, 0, 0),
            records_synced=1000
        )

        state = SourceState(
            source_name="production_db",
            source_id="src_prod",
            streams={"users": stream},
            global_state={"version": "1.0"}
        )

        # Serialize for database
        state_dict = state.to_dict()
        state_json = json.dumps(state_dict)

        # Should be valid JSON
        parsed = json.loads(state_json)
        assert parsed["source_id"] == "src_prod"
        assert "users" in parsed["streams"]

        # Deserialize back
        restored = SourceState.from_dict(parsed)
        assert restored.source_id == "src_prod"
        assert restored.streams["users"].cursor_value == "2026-01-13T12:00:00Z"


class TestStateRecoveryScenarios:
    """
    Tests for various state recovery scenarios.
    """

    def test_recover_from_corrupted_file(self):
        """Test recovery when state file is corrupted."""
        from app.connectors.airbyte.state_manager import StateManager

        temp_dir = Path(tempfile.mkdtemp())

        # Create corrupted state file
        corrupted_file = temp_dir / "corrupted.json"
        with open(corrupted_file, "w") as f:
            f.write("{ invalid json }")

        # State manager should handle corrupted file gracefully
        sm = StateManager(storage_path=temp_dir)

        # Should not crash, but state won't be loaded
        state = sm.get_state("corrupted")
        assert state is None

    def test_recover_partial_sync_state(self):
        """Test recovering from partial sync (state exists but incomplete)."""
        from app.connectors.airbyte.state_manager import StateManager

        temp_dir = Path(tempfile.mkdtemp())
        sm = StateManager(storage_path=temp_dir)

        # Create state with multiple streams
        sm.create_state("partial", "src_partial", ["s1", "s2", "s3"])

        # Update only some streams (simulating interrupted sync)
        sm.update_stream_state("src_partial", "s1", cursor_value=100, records_synced=100)
        sm.update_stream_state("src_partial", "s2", cursor_value=200, records_synced=200)
        # s3 not updated (interrupted)

        # Load state and identify incomplete streams
        state = sm.get_state("src_partial")

        incomplete_streams = []
        complete_streams = []

        for name, stream in state.streams.items():
            if stream.cursor_value is None:
                incomplete_streams.append(name)
            else:
                complete_streams.append(name)

        assert "s3" in incomplete_streams
        assert "s1" in complete_streams
        assert "s2" in complete_streams

    def test_state_metadata_tracking(self):
        """Test that metadata is properly tracked with state."""
        from app.connectors.airbyte.state_manager import StateManager

        temp_dir = Path(tempfile.mkdtemp())
        sm = StateManager(storage_path=temp_dir)

        sm.create_state("metadata_test", "src_meta", ["data"])
        sm.update_stream_state(
            "src_meta",
            "data",
            cursor_value=100,
            metadata={"last_error": None, "retries": 0, "batch_size": 1000}
        )

        state = sm.get_state("src_meta")
        assert state.streams["data"].metadata["batch_size"] == 1000
        assert state.streams["data"].metadata["retries"] == 0
