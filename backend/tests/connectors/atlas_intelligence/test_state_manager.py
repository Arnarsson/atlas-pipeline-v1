"""
Tests for State Manager

Tests state persistence, stream state tracking, and incremental sync support.
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from app.connectors.atlas_intelligence.state_manager import (
    StateManager,
    get_state_manager,
    StreamState,
    SourceState
)


class TestStreamState:
    """Tests for StreamState dataclass."""

    def test_default_values(self):
        """Test StreamState default values."""
        state = StreamState(stream_name="users")
        assert state.stream_name == "users"
        assert state.cursor_field is None
        assert state.cursor_value is None
        assert state.sync_mode == "full_refresh"
        assert state.last_synced_at is None
        assert state.records_synced == 0

    def test_with_cursor(self):
        """Test StreamState with cursor values."""
        now = datetime.utcnow()
        state = StreamState(
            stream_name="orders",
            cursor_field="updated_at",
            cursor_value="2024-01-15T10:00:00Z",
            sync_mode="incremental",
            last_synced_at=now,
            records_synced=1500
        )
        assert state.cursor_field == "updated_at"
        assert state.cursor_value == "2024-01-15T10:00:00Z"
        assert state.sync_mode == "incremental"
        assert state.records_synced == 1500

    def test_to_dict(self):
        """Test StreamState serialization."""
        state = StreamState(
            stream_name="products",
            cursor_field="id",
            cursor_value=100,
            sync_mode="incremental"
        )
        d = state.to_dict()
        assert d["stream_name"] == "products"
        assert d["cursor_field"] == "id"
        assert d["cursor_value"] == 100

    def test_from_dict(self):
        """Test StreamState deserialization."""
        data = {
            "stream_name": "customers",
            "cursor_field": "created_at",
            "cursor_value": "2024-01-01",
            "sync_mode": "incremental",
            "records_synced": 500
        }
        state = StreamState.from_dict(data)
        assert state.stream_name == "customers"
        assert state.cursor_field == "created_at"
        assert state.records_synced == 500


class TestSourceState:
    """Tests for SourceState dataclass."""

    def test_default_values(self):
        """Test SourceState default values."""
        state = SourceState(source_id="src_123", source_name="my_postgres")
        assert state.source_id == "src_123"
        assert state.source_name == "my_postgres"
        assert state.streams == {}
        assert state.global_state == {}
        assert state.last_synced_at is None
        assert state.total_records_synced == 0

    def test_with_streams(self):
        """Test SourceState with stream states."""
        stream1 = StreamState(stream_name="users", records_synced=100)
        stream2 = StreamState(stream_name="orders", records_synced=200)

        state = SourceState(
            source_id="src_456",
            source_name="production_db",
            streams={"users": stream1, "orders": stream2},
            total_records_synced=300
        )
        assert len(state.streams) == 2
        assert state.streams["users"].records_synced == 100
        assert state.total_records_synced == 300

    def test_to_dict(self):
        """Test SourceState serialization."""
        stream = StreamState(stream_name="events", records_synced=50)
        state = SourceState(
            source_id="src_789",
            source_name="analytics",
            streams={"events": stream}
        )
        d = state.to_dict()
        assert d["source_id"] == "src_789"
        assert "streams" in d
        assert "events" in d["streams"]

    def test_from_dict(self):
        """Test SourceState deserialization."""
        data = {
            "source_id": "src_abc",
            "source_name": "warehouse",
            "streams": {
                "fact_sales": {
                    "stream_name": "fact_sales",
                    "cursor_field": "date",
                    "cursor_value": "2024-01-15",
                    "records_synced": 10000
                }
            },
            "total_records_synced": 10000
        }
        state = SourceState.from_dict(data)
        assert state.source_id == "src_abc"
        assert "fact_sales" in state.streams
        assert state.streams["fact_sales"].records_synced == 10000


class TestStateManager:
    """Tests for StateManager class."""

    @pytest.fixture
    def manager(self):
        """Create a fresh StateManager instance."""
        return StateManager()

    def test_create_source_state(self, manager):
        """Test creating new source state."""
        state = manager.create_source_state("src_001", "test_source")
        assert state.source_id == "src_001"
        assert state.source_name == "test_source"
        assert state.streams == {}

    def test_create_source_state_with_streams(self, manager):
        """Test creating source state with initial streams."""
        state = manager.create_source_state(
            "src_002",
            "multi_stream",
            streams=["users", "orders", "products"]
        )
        assert len(state.streams) == 3
        assert "users" in state.streams
        assert "orders" in state.streams
        assert "products" in state.streams

    def test_get_source_state_exists(self, manager):
        """Test getting existing source state."""
        manager.create_source_state("src_003", "existing")
        state = manager.get_source_state("src_003")
        assert state is not None
        assert state.source_name == "existing"

    def test_get_source_state_not_exists(self, manager):
        """Test getting non-existent source state returns None."""
        state = manager.get_source_state("nonexistent")
        assert state is None

    def test_update_stream_state(self, manager):
        """Test updating stream state."""
        manager.create_source_state("src_004", "updates")
        manager.update_stream_state(
            "src_004",
            "users",
            cursor_field="id",
            cursor_value=1000,
            records_synced=500
        )

        state = manager.get_source_state("src_004")
        assert "users" in state.streams
        assert state.streams["users"].cursor_value == 1000
        assert state.streams["users"].records_synced == 500

    def test_update_stream_state_creates_stream(self, manager):
        """Test that updating creates stream if not exists."""
        manager.create_source_state("src_005", "new_stream")
        manager.update_stream_state(
            "src_005",
            "new_table",
            cursor_field="created_at",
            cursor_value="2024-01-01"
        )

        state = manager.get_source_state("src_005")
        assert "new_table" in state.streams

    def test_update_stream_state_invalid_source(self, manager):
        """Test updating stream for invalid source raises error."""
        with pytest.raises(ValueError, match="Source .* not found"):
            manager.update_stream_state("invalid", "stream", cursor_field="id")

    def test_reset_source_state(self, manager):
        """Test resetting source state."""
        manager.create_source_state("src_006", "to_reset", streams=["a", "b"])
        manager.update_stream_state("src_006", "a", cursor_value=100, records_synced=50)

        manager.reset_source_state("src_006")
        state = manager.get_source_state("src_006")

        # Streams should still exist but be reset
        assert state.total_records_synced == 0
        for stream in state.streams.values():
            assert stream.cursor_value is None
            assert stream.records_synced == 0

    def test_reset_specific_stream(self, manager):
        """Test resetting specific stream only."""
        manager.create_source_state("src_007", "partial_reset", streams=["keep", "reset"])
        manager.update_stream_state("src_007", "keep", cursor_value=100, records_synced=50)
        manager.update_stream_state("src_007", "reset", cursor_value=200, records_synced=75)

        manager.reset_stream_state("src_007", "reset")
        state = manager.get_source_state("src_007")

        # "keep" should retain values
        assert state.streams["keep"].cursor_value == 100
        # "reset" should be cleared
        assert state.streams["reset"].cursor_value is None
        assert state.streams["reset"].records_synced == 0

    def test_list_sources(self, manager):
        """Test listing all source states."""
        manager.create_source_state("src_a", "source_a")
        manager.create_source_state("src_b", "source_b")
        manager.create_source_state("src_c", "source_c")

        sources = manager.list_sources()
        assert len(sources) == 3
        source_ids = [s["source_id"] for s in sources]
        assert "src_a" in source_ids
        assert "src_b" in source_ids
        assert "src_c" in source_ids

    def test_delete_source_state(self, manager):
        """Test deleting source state."""
        manager.create_source_state("src_delete", "to_delete")
        assert manager.get_source_state("src_delete") is not None

        manager.delete_source_state("src_delete")
        assert manager.get_source_state("src_delete") is None

    def test_export_state(self, manager):
        """Test exporting all state."""
        manager.create_source_state("exp_1", "export_test", streams=["data"])
        manager.update_stream_state("exp_1", "data", cursor_value="test", records_synced=10)

        exported = manager.export_state()
        assert "sources" in exported
        assert "exp_1" in exported["sources"]
        assert exported["sources"]["exp_1"]["source_name"] == "export_test"

    def test_import_state(self, manager):
        """Test importing state from export."""
        export_data = {
            "sources": {
                "imp_1": {
                    "source_id": "imp_1",
                    "source_name": "imported",
                    "streams": {
                        "table1": {
                            "stream_name": "table1",
                            "cursor_field": "id",
                            "cursor_value": 500,
                            "records_synced": 250
                        }
                    },
                    "total_records_synced": 250
                }
            }
        }

        manager.import_state(export_data)
        state = manager.get_source_state("imp_1")
        assert state is not None
        assert state.source_name == "imported"
        assert state.streams["table1"].cursor_value == 500


class TestGetStateManager:
    """Tests for the singleton state manager getter."""

    def test_returns_same_instance(self):
        """Test that get_state_manager returns singleton."""
        manager1 = get_state_manager()
        manager2 = get_state_manager()
        assert manager1 is manager2

    def test_returns_state_manager_instance(self):
        """Test that returned instance is correct type."""
        manager = get_state_manager()
        assert isinstance(manager, StateManager)


class TestIncrementalSyncFlow:
    """Integration tests for incremental sync flow."""

    @pytest.fixture
    def manager(self):
        return StateManager()

    def test_full_incremental_sync_flow(self, manager):
        """Test complete incremental sync workflow."""
        # 1. Create source
        source_id = "inc_source"
        manager.create_source_state(source_id, "incremental_test", streams=["events"])

        # 2. Configure for incremental
        manager.update_stream_state(
            source_id,
            "events",
            cursor_field="timestamp",
            sync_mode="incremental"
        )

        # 3. First sync - simulate reading 100 records up to timestamp X
        manager.update_stream_state(
            source_id,
            "events",
            cursor_value="2024-01-15T12:00:00Z",
            records_synced=100
        )

        # 4. Verify state
        state = manager.get_source_state(source_id)
        assert state.streams["events"].cursor_value == "2024-01-15T12:00:00Z"
        assert state.streams["events"].records_synced == 100

        # 5. Second sync - simulate reading 50 more records
        manager.update_stream_state(
            source_id,
            "events",
            cursor_value="2024-01-15T18:00:00Z",
            records_synced=150  # Cumulative
        )

        # 6. Verify updated state
        state = manager.get_source_state(source_id)
        assert state.streams["events"].cursor_value == "2024-01-15T18:00:00Z"
        assert state.streams["events"].records_synced == 150

    def test_multi_stream_incremental(self, manager):
        """Test incremental sync with multiple streams."""
        source_id = "multi_inc"
        streams = ["users", "orders", "products"]
        manager.create_source_state(source_id, "multi_stream", streams=streams)

        # Update each stream independently
        manager.update_stream_state(source_id, "users", cursor_value=1000, records_synced=100)
        manager.update_stream_state(source_id, "orders", cursor_value=5000, records_synced=500)
        manager.update_stream_state(source_id, "products", cursor_value=200, records_synced=50)

        state = manager.get_source_state(source_id)

        # Each stream maintains independent state
        assert state.streams["users"].cursor_value == 1000
        assert state.streams["orders"].cursor_value == 5000
        assert state.streams["products"].cursor_value == 200
