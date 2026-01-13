"""
Tests for Airbyte to Atlas Adapter
==================================

Tests the AirbyteSourceAdapter that implements Atlas's SourceConnector interface.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import pandas as pd

from app.connectors.base import ConnectionConfig
from app.connectors.airbyte.adapter import (
    AirbyteSourceAdapter,
    create_airbyte_adapter,
    sync_airbyte_source,
)
from app.connectors.airbyte.protocol import (
    AirbyteCatalog,
    AirbyteStream,
    AirbyteConnectionStatus,
    AirbyteConnectionStatusMessage,
    AirbyteSpecification,
    SyncMode,
)
from app.connectors.airbyte.executor import ExecutionResult, AirbyteCommand


class TestAirbyteSourceAdapter:
    """Test AirbyteSourceAdapter class."""

    def test_initialization_with_airbyte_prefix(self):
        """Test initialization with 'airbyte:' prefix."""
        config = ConnectionConfig(
            source_type="airbyte:source-postgres",
            source_name="test_postgres",
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="pass",
        )

        adapter = AirbyteSourceAdapter(config)

        assert adapter.connector_name == "source-postgres"
        assert adapter.docker_image == "airbyte/source-postgres:latest"

    def test_initialization_with_source_prefix(self):
        """Test initialization with 'source-' prefix."""
        config = ConnectionConfig(
            source_type="source-mysql",
            source_name="test_mysql",
            host="localhost",
        )

        adapter = AirbyteSourceAdapter(config)

        assert adapter.connector_name == "source-mysql"
        assert adapter.docker_image == "airbyte/source-mysql:latest"

    def test_initialization_short_name(self):
        """Test initialization with short name."""
        config = ConnectionConfig(
            source_type="postgres",
            source_name="test_postgres",
            host="localhost",
        )

        adapter = AirbyteSourceAdapter(config)

        assert adapter.connector_name == "source-postgres"

    def test_build_airbyte_config(self):
        """Test building Airbyte config from ConnectionConfig."""
        config = ConnectionConfig(
            source_type="airbyte:source-postgres",
            source_name="test",
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="pass",
            additional_params={"ssl": True},
        )

        adapter = AirbyteSourceAdapter(config)

        assert adapter.airbyte_config["host"] == "localhost"
        assert adapter.airbyte_config["port"] == 5432
        assert adapter.airbyte_config["database"] == "testdb"
        assert adapter.airbyte_config["username"] == "user"
        assert adapter.airbyte_config["password"] == "pass"
        assert adapter.airbyte_config["ssl"] is True


class TestAdapterWithMockedExecutor:
    """Test adapter with mocked executor."""

    @pytest.fixture
    def mock_executor(self):
        """Create mock executor."""
        executor = MagicMock()
        executor.check = AsyncMock()
        executor.discover = AsyncMock()
        executor.read = AsyncMock()
        executor.read_stream = AsyncMock()
        return executor

    @pytest.fixture
    def adapter(self, mock_executor):
        """Create adapter with mock executor."""
        config = ConnectionConfig(
            source_type="airbyte:source-postgres",
            source_name="test_postgres",
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="pass",
        )
        return AirbyteSourceAdapter(config, executor=mock_executor)

    @pytest.mark.asyncio
    async def test_test_connection_success(self, adapter, mock_executor):
        """Test successful connection test."""
        mock_executor.check.return_value = AirbyteConnectionStatusMessage(
            status=AirbyteConnectionStatus.SUCCEEDED,
            message="Connection successful"
        )

        with patch.object(adapter, "ensure_image_pulled", return_value=True):
            result = await adapter.test_connection()

        assert result is True
        mock_executor.check.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_connection_failure(self, adapter, mock_executor):
        """Test failed connection test."""
        mock_executor.check.return_value = AirbyteConnectionStatusMessage(
            status=AirbyteConnectionStatus.FAILED,
            message="Connection refused"
        )

        with patch.object(adapter, "ensure_image_pulled", return_value=True):
            with pytest.raises(ConnectionError) as exc_info:
                await adapter.test_connection()

        assert "Connection refused" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_discover(self, adapter, mock_executor):
        """Test stream discovery."""
        mock_catalog = AirbyteCatalog(
            streams=[
                AirbyteStream(name="users", supported_sync_modes=[SyncMode.FULL_REFRESH]),
                AirbyteStream(name="orders", supported_sync_modes=[SyncMode.FULL_REFRESH, SyncMode.INCREMENTAL]),
            ]
        )
        mock_executor.discover.return_value = mock_catalog

        with patch.object(adapter, "ensure_image_pulled", return_value=True):
            catalog = await adapter.discover()

        assert len(catalog.streams) == 2
        assert catalog.streams[0].name == "users"
        assert catalog.streams[1].name == "orders"

    @pytest.mark.asyncio
    async def test_list_tables(self, adapter, mock_executor):
        """Test listing tables."""
        mock_catalog = AirbyteCatalog(
            streams=[
                AirbyteStream(name="users"),
                AirbyteStream(name="orders"),
                AirbyteStream(name="products"),
            ]
        )
        mock_executor.discover.return_value = mock_catalog

        with patch.object(adapter, "ensure_image_pulled", return_value=True):
            tables = await adapter.list_tables()

        assert tables == ["users", "orders", "products"]

    @pytest.mark.asyncio
    async def test_get_data_success(self, adapter, mock_executor):
        """Test getting data from a stream."""
        from app.connectors.airbyte.protocol import (
            AirbyteMessage,
            AirbyteMessageType,
            AirbyteRecordMessage,
        )

        mock_catalog = AirbyteCatalog(
            streams=[
                AirbyteStream(name="users", supported_sync_modes=[SyncMode.FULL_REFRESH]),
            ]
        )
        mock_executor.discover.return_value = mock_catalog

        mock_result = ExecutionResult(
            success=True,
            command=AirbyteCommand.READ,
            messages=[
                AirbyteMessage(
                    type=AirbyteMessageType.RECORD,
                    record=AirbyteRecordMessage(stream="users", data={"id": 1, "name": "Alice"}, emitted_at=1704067200000)
                ),
                AirbyteMessage(
                    type=AirbyteMessageType.RECORD,
                    record=AirbyteRecordMessage(stream="users", data={"id": 2, "name": "Bob"}, emitted_at=1704067200001)
                ),
            ],
            records_count=2,
            duration_seconds=1.5,
        )
        mock_executor.read.return_value = mock_result

        with patch.object(adapter, "ensure_image_pulled", return_value=True):
            df = await adapter.get_data(table="users")

        assert len(df) == 2
        assert list(df.columns) == ["id", "name"]
        assert df.iloc[0]["name"] == "Alice"
        assert df.iloc[1]["name"] == "Bob"

    @pytest.mark.asyncio
    async def test_get_data_stream_not_found(self, adapter, mock_executor):
        """Test getting data from non-existent stream."""
        mock_catalog = AirbyteCatalog(
            streams=[
                AirbyteStream(name="users"),
            ]
        )
        mock_executor.discover.return_value = mock_catalog

        with patch.object(adapter, "ensure_image_pulled", return_value=True):
            with pytest.raises(ValueError) as exc_info:
                await adapter.get_data(table="orders")

        assert "orders" in str(exc_info.value)
        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_data_no_table_provided(self, adapter):
        """Test getting data without table parameter."""
        with pytest.raises(ValueError) as exc_info:
            await adapter.get_data()

        assert "required" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_schema(self, adapter, mock_executor):
        """Test getting schema for a stream."""
        mock_catalog = AirbyteCatalog(
            streams=[
                AirbyteStream(
                    name="users",
                    json_schema={
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "email": {"type": "string", "format": "email"},
                            "created_at": {"type": "string", "format": "date-time"},
                            "is_active": {"type": "boolean"},
                            "metadata": {"type": "object"},
                        }
                    }
                ),
            ]
        )
        mock_executor.discover.return_value = mock_catalog

        with patch.object(adapter, "ensure_image_pulled", return_value=True):
            schema = await adapter.get_schema("users")

        assert schema["id"] == "INTEGER"
        assert schema["name"] == "VARCHAR"
        assert schema["created_at"] == "TIMESTAMP"
        assert schema["is_active"] == "BOOLEAN"
        assert schema["metadata"] == "JSONB"

    @pytest.mark.asyncio
    async def test_close(self, adapter):
        """Test closing adapter."""
        adapter._catalog = AirbyteCatalog(streams=[])
        adapter._state = {"users": {"cursor": "123"}}

        await adapter.close()

        assert adapter._catalog is None
        assert adapter._state == {}


class TestStateManagement:
    """Test adapter state management."""

    @pytest.fixture
    def adapter(self):
        """Create adapter for testing."""
        config = ConnectionConfig(
            source_type="airbyte:source-postgres",
            source_name="test",
            host="localhost",
        )
        return AirbyteSourceAdapter(config)

    def test_set_state(self, adapter):
        """Test setting state."""
        adapter.set_state("users", {"cursor": "2024-01-01"})

        assert adapter._state["users"] == {"cursor": "2024-01-01"}

    def test_get_state(self, adapter):
        """Test getting state."""
        adapter._state["users"] = {"cursor": "2024-01-01"}

        state = adapter.get_state("users")

        assert state == {"cursor": "2024-01-01"}

    def test_get_state_not_found(self, adapter):
        """Test getting non-existent state."""
        state = adapter.get_state("orders")

        assert state is None

    def test_clear_state_specific(self, adapter):
        """Test clearing specific stream state."""
        adapter._state["users"] = {"cursor": "1"}
        adapter._state["orders"] = {"cursor": "2"}

        adapter.clear_state("users")

        assert "users" not in adapter._state
        assert "orders" in adapter._state

    def test_clear_state_all(self, adapter):
        """Test clearing all state."""
        adapter._state["users"] = {"cursor": "1"}
        adapter._state["orders"] = {"cursor": "2"}

        adapter.clear_state()

        assert adapter._state == {}


class TestCreateAirbyteAdapter:
    """Test create_airbyte_adapter factory function."""

    def test_create_adapter(self):
        """Test creating adapter from connector name and config."""
        adapter = create_airbyte_adapter(
            "source-postgres",
            {
                "host": "localhost",
                "port": 5432,
                "database": "testdb",
            },
            source_name="my_postgres",
        )

        assert adapter.connector_name == "source-postgres"
        assert adapter.config.source_name == "my_postgres"
        assert adapter.airbyte_config["host"] == "localhost"

    def test_create_adapter_default_name(self):
        """Test creating adapter with default name."""
        adapter = create_airbyte_adapter(
            "source-mysql",
            {"host": "localhost"},
        )

        assert adapter.config.source_name == "source-mysql"


class TestSyncAirbyteSource:
    """Test sync_airbyte_source convenience function."""

    @pytest.mark.asyncio
    async def test_sync_all_streams(self):
        """Test syncing all streams."""
        from app.connectors.airbyte.protocol import (
            AirbyteMessage,
            AirbyteMessageType,
            AirbyteRecordMessage,
        )

        mock_catalog = AirbyteCatalog(
            streams=[
                AirbyteStream(name="users", supported_sync_modes=[SyncMode.FULL_REFRESH]),
                AirbyteStream(name="orders", supported_sync_modes=[SyncMode.FULL_REFRESH]),
            ]
        )

        mock_result = ExecutionResult(
            success=True,
            command=AirbyteCommand.READ,
            messages=[
                AirbyteMessage(
                    type=AirbyteMessageType.RECORD,
                    record=AirbyteRecordMessage(stream="users", data={"id": 1}, emitted_at=1704067200000)
                ),
            ],
            records_count=1,
        )

        with patch("app.connectors.airbyte.adapter.AirbyteSourceAdapter") as MockAdapter:
            mock_adapter = MagicMock()
            mock_adapter.test_connection = AsyncMock(return_value=True)
            mock_adapter.list_tables = AsyncMock(return_value=["users", "orders"])
            mock_adapter.get_data = AsyncMock(return_value=pd.DataFrame({"id": [1]}))
            mock_adapter.close = AsyncMock()
            MockAdapter.return_value = mock_adapter

            results = await sync_airbyte_source(
                "source-postgres",
                {"host": "localhost"},
            )

        assert "users" in results
        assert "orders" in results

    @pytest.mark.asyncio
    async def test_sync_specific_streams(self):
        """Test syncing specific streams."""
        with patch("app.connectors.airbyte.adapter.AirbyteSourceAdapter") as MockAdapter:
            mock_adapter = MagicMock()
            mock_adapter.test_connection = AsyncMock(return_value=True)
            mock_adapter.get_data = AsyncMock(return_value=pd.DataFrame({"id": [1]}))
            mock_adapter.close = AsyncMock()
            MockAdapter.return_value = mock_adapter

            results = await sync_airbyte_source(
                "source-postgres",
                {"host": "localhost"},
                streams=["users"],
            )

        assert "users" in results
        assert "orders" not in results


class TestConfiguredCatalogBuilding:
    """Test building configured catalogs."""

    @pytest.fixture
    def adapter(self):
        """Create adapter for testing."""
        config = ConnectionConfig(
            source_type="airbyte:source-postgres",
            source_name="test",
            host="localhost",
        )
        return AirbyteSourceAdapter(config)

    def test_build_full_refresh_catalog(self, adapter):
        """Test building full refresh catalog."""
        stream = AirbyteStream(
            name="users",
            supported_sync_modes=[SyncMode.FULL_REFRESH],
        )

        catalog = adapter._build_configured_catalog(stream, incremental=False, cursor_field=None)

        assert len(catalog.streams) == 1
        assert catalog.streams[0].sync_mode == SyncMode.FULL_REFRESH

    def test_build_incremental_catalog(self, adapter):
        """Test building incremental catalog."""
        stream = AirbyteStream(
            name="users",
            supported_sync_modes=[SyncMode.FULL_REFRESH, SyncMode.INCREMENTAL],
            default_cursor_field=["updated_at"],
        )

        catalog = adapter._build_configured_catalog(stream, incremental=True, cursor_field=None)

        assert catalog.streams[0].sync_mode == SyncMode.INCREMENTAL
        assert catalog.streams[0].cursor_field == ["updated_at"]

    def test_build_catalog_with_custom_cursor(self, adapter):
        """Test building catalog with custom cursor field."""
        stream = AirbyteStream(
            name="users",
            supported_sync_modes=[SyncMode.FULL_REFRESH, SyncMode.INCREMENTAL],
        )

        catalog = adapter._build_configured_catalog(stream, incremental=True, cursor_field="created_at")

        assert catalog.streams[0].cursor_field == ["created_at"]

    def test_fallback_to_full_refresh(self, adapter):
        """Test fallback to full refresh when incremental not supported."""
        stream = AirbyteStream(
            name="users",
            supported_sync_modes=[SyncMode.FULL_REFRESH],  # No incremental
        )

        catalog = adapter._build_configured_catalog(stream, incremental=True, cursor_field=None)

        # Should fall back to full refresh
        assert catalog.streams[0].sync_mode == SyncMode.FULL_REFRESH


class TestJsonTypeMapping:
    """Test JSON schema type to SQL type mapping."""

    @pytest.fixture
    def adapter(self):
        """Create adapter for testing."""
        config = ConnectionConfig(
            source_type="airbyte:source-postgres",
            source_name="test",
            host="localhost",
        )
        return AirbyteSourceAdapter(config)

    def test_string_type(self, adapter):
        """Test string type mapping."""
        assert adapter._json_type_to_sql("string", {}) == "VARCHAR"

    def test_integer_type(self, adapter):
        """Test integer type mapping."""
        assert adapter._json_type_to_sql("integer", {}) == "INTEGER"

    def test_number_type(self, adapter):
        """Test number type mapping."""
        assert adapter._json_type_to_sql("number", {}) == "DECIMAL"

    def test_boolean_type(self, adapter):
        """Test boolean type mapping."""
        assert adapter._json_type_to_sql("boolean", {}) == "BOOLEAN"

    def test_object_type(self, adapter):
        """Test object type mapping."""
        assert adapter._json_type_to_sql("object", {}) == "JSONB"

    def test_array_type(self, adapter):
        """Test array type mapping."""
        assert adapter._json_type_to_sql("array", {}) == "JSONB"

    def test_datetime_format(self, adapter):
        """Test date-time format override."""
        assert adapter._json_type_to_sql("string", {"format": "date-time"}) == "TIMESTAMP"

    def test_date_format(self, adapter):
        """Test date format override."""
        assert adapter._json_type_to_sql("string", {"format": "date"}) == "DATE"

    def test_time_format(self, adapter):
        """Test time format override."""
        assert adapter._json_type_to_sql("string", {"format": "time"}) == "TIME"

    def test_unknown_type(self, adapter):
        """Test unknown type defaults to VARCHAR."""
        assert adapter._json_type_to_sql("unknown", {}) == "VARCHAR"
