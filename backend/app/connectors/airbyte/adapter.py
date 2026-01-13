"""
Airbyte to Atlas Adapter
========================

Wraps Airbyte Docker connector execution and implements the Atlas
SourceConnector interface for seamless integration.

This enables Atlas to use ANY of the 300+ Airbyte connectors through
a unified interface.
"""

import json
import logging
from datetime import datetime
from typing import Any, AsyncIterator

import pandas as pd

from ..base import ConnectionConfig, SourceConnector
from .executor import (
    AirbyteDockerExecutor,
    ExecutionResult,
    ExecutorConfig,
    get_docker_executor,
    pull_image,
)
from .protocol import (
    AirbyteCatalog,
    AirbyteConnectionStatus,
    AirbyteMessage,
    AirbyteMessageType,
    AirbyteRecordMessage,
    AirbyteStream,
    ConfiguredAirbyteCatalog,
    ConfiguredAirbyteStream,
    DestinationSyncMode,
    SyncMode,
    filter_records,
    get_last_state,
)
from .registry import get_connector_image, get_connector_info

logger = logging.getLogger(__name__)


class AirbyteSourceAdapter(SourceConnector):
    """
    Adapts Airbyte connectors to Atlas's SourceConnector interface.

    This adapter:
    - Wraps Airbyte Docker execution
    - Converts between Airbyte and Atlas formats
    - Handles state management for incremental syncs
    - Provides schema discovery via DISCOVER command

    Usage:
        config = ConnectionConfig(
            source_type="airbyte:source-postgres",
            source_name="my_postgres",
            additional_params={
                "host": "localhost",
                "port": 5432,
                "database": "mydb",
                "username": "user",
                "password": "pass",
            }
        )
        adapter = AirbyteSourceAdapter(config)
        await adapter.test_connection()
        df = await adapter.get_data(table="users")
    """

    def __init__(
        self,
        config: ConnectionConfig,
        executor: AirbyteDockerExecutor | None = None,
    ):
        """
        Initialize Airbyte adapter.

        Args:
            config: Connection configuration.
                    source_type should be "airbyte:<connector-name>" or just "<connector-name>"
                    additional_params contains the Airbyte connector config
            executor: Optional custom Docker executor
        """
        super().__init__(config)
        self.executor = executor or get_docker_executor()

        # Parse connector name from source_type
        self.connector_name = self._parse_connector_name(config.source_type)
        self.docker_image = get_connector_image(self.connector_name)

        # Build Airbyte config from ConnectionConfig
        self.airbyte_config = self._build_airbyte_config()

        # Cached catalog from DISCOVER
        self._catalog: AirbyteCatalog | None = None

        # State for incremental syncs (stream_name -> state_data)
        self._state: dict[str, Any] = {}

        logger.info(
            f"Initialized AirbyteSourceAdapter: connector={self.connector_name}, "
            f"image={self.docker_image}"
        )

    def _parse_connector_name(self, source_type: str) -> str:
        """Parse connector name from source_type."""
        # Handle "airbyte:source-postgres" format
        if source_type.startswith("airbyte:"):
            return source_type.replace("airbyte:", "")

        # Handle just "source-postgres"
        if source_type.startswith("source-"):
            return source_type

        # Assume it's a short name like "postgres"
        return f"source-{source_type}"

    def _build_airbyte_config(self) -> dict[str, Any]:
        """Build Airbyte connector config from Atlas ConnectionConfig."""
        config = {}

        # Copy database connection params if present
        if self.config.host:
            config["host"] = self.config.host
        if self.config.port:
            config["port"] = self.config.port
        if self.config.database:
            config["database"] = self.config.database
        if self.config.username:
            config["username"] = self.config.username
        if self.config.password:
            config["password"] = self.config.password

        # Copy REST API params if present
        if self.config.base_url:
            config["base_url"] = self.config.base_url
        if self.config.auth_token:
            config["access_token"] = self.config.auth_token
        if self.config.api_key:
            config["api_key"] = self.config.api_key

        # Copy connection string if present
        if self.config.connection_string:
            config["connection_string"] = self.config.connection_string

        # Merge additional params (these override defaults)
        config.update(self.config.additional_params)

        return config

    async def ensure_image_pulled(self) -> bool:
        """Ensure Docker image is available locally."""
        return await pull_image(self.docker_image)

    async def test_connection(self) -> bool:
        """
        Test connection using Airbyte CHECK command.

        Returns:
            True if connection successful

        Raises:
            ConnectionError: If connection fails with details
        """
        try:
            # Ensure image is available
            await self.ensure_image_pulled()

            # Run CHECK command
            status = await self.executor.check(self.docker_image, self.airbyte_config)

            if status.status == AirbyteConnectionStatus.SUCCEEDED:
                logger.info(f"Connection test succeeded for {self.connector_name}")
                return True
            else:
                error_msg = status.message or "Connection check failed"
                logger.error(f"Connection test failed: {error_msg}")
                raise ConnectionError(error_msg)

        except Exception as e:
            logger.error(f"Connection test error: {e}")
            raise ConnectionError(str(e))

    async def discover(self) -> AirbyteCatalog:
        """
        Discover available streams (tables) from source.

        Returns:
            AirbyteCatalog with available streams

        Raises:
            RuntimeError: If discovery fails
        """
        if self._catalog is not None:
            return self._catalog

        try:
            await self.ensure_image_pulled()
            self._catalog = await self.executor.discover(
                self.docker_image, self.airbyte_config
            )
            logger.info(
                f"Discovered {len(self._catalog.streams)} streams from {self.connector_name}"
            )
            return self._catalog

        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            raise RuntimeError(f"Failed to discover streams: {e}")

    async def list_tables(self) -> list[str]:
        """
        List available tables (streams) from source.

        Returns:
            List of stream/table names
        """
        catalog = await self.discover()
        return [stream.name for stream in catalog.streams]

    async def get_data(
        self,
        query: str | None = None,
        table: str | None = None,
        incremental: bool = False,
        timestamp_column: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        """
        Fetch data from source using Airbyte READ command.

        Args:
            query: Not used for Airbyte (use table/stream name)
            table: Stream name to read from
            incremental: Whether to use incremental sync
            timestamp_column: Cursor field for incremental sync
            filters: Not used for Airbyte (use configured catalog)

        Returns:
            DataFrame with fetched data

        Raises:
            ValueError: If table is not provided
            RuntimeError: If read fails
        """
        if not table:
            raise ValueError("table (stream name) is required for Airbyte connectors")

        try:
            # Ensure image is available
            await self.ensure_image_pulled()

            # Get catalog
            catalog = await self.discover()

            # Find the stream
            stream = self._find_stream(catalog, table)
            if not stream:
                raise ValueError(f"Stream '{table}' not found. Available: {await self.list_tables()}")

            # Build configured catalog for single stream
            configured_catalog = self._build_configured_catalog(
                stream, incremental, timestamp_column
            )

            # Get state for incremental sync
            state = self._state.get(table) if incremental else None

            # Execute READ
            result = await self.executor.read(
                self.docker_image,
                self.airbyte_config,
                configured_catalog,
                state,
            )

            if not result.success:
                raise RuntimeError(f"Read failed: {result.error}")

            # Extract records
            records = filter_records(result.messages)

            # Update state for incremental sync
            last_state = get_last_state(result.messages)
            if last_state and incremental:
                self._state[table] = self._extract_state_data(last_state)

            # Convert to DataFrame
            df = self._records_to_dataframe(records, table)

            self.last_sync_timestamp = datetime.utcnow()

            logger.info(
                f"Read {len(df)} records from {table} in {result.duration_seconds:.2f}s"
            )
            return df

        except Exception as e:
            logger.error(f"Read failed for {table}: {e}")
            raise RuntimeError(f"Failed to read from {table}: {e}")

    async def get_data_stream(
        self,
        table: str,
        incremental: bool = False,
        timestamp_column: str | None = None,
    ) -> AsyncIterator[pd.DataFrame]:
        """
        Stream data from source in batches.

        Useful for large datasets where buffering all records is impractical.

        Args:
            table: Stream name to read from
            incremental: Whether to use incremental sync
            timestamp_column: Cursor field for incremental sync

        Yields:
            DataFrame batches (1000 records each)
        """
        await self.ensure_image_pulled()

        catalog = await self.discover()
        stream = self._find_stream(catalog, table)
        if not stream:
            raise ValueError(f"Stream '{table}' not found")

        configured_catalog = self._build_configured_catalog(
            stream, incremental, timestamp_column
        )

        state = self._state.get(table) if incremental else None
        batch_size = 1000
        batch: list[dict[str, Any]] = []

        async for msg in self.executor.read_stream(
            self.docker_image,
            self.airbyte_config,
            configured_catalog,
            state,
        ):
            if msg.type == AirbyteMessageType.RECORD and msg.record:
                if msg.record.stream == table:
                    batch.append(msg.record.data)

                    if len(batch) >= batch_size:
                        yield pd.DataFrame(batch)
                        batch = []

            elif msg.type == AirbyteMessageType.STATE and msg.state:
                self._state[table] = self._extract_state_data(msg.state)

        # Yield remaining records
        if batch:
            yield pd.DataFrame(batch)

    async def get_schema(self, table: str) -> dict[str, str]:
        """
        Get table schema from Airbyte catalog.

        Args:
            table: Stream name

        Returns:
            Dictionary mapping column names to data types
        """
        catalog = await self.discover()
        stream = self._find_stream(catalog, table)

        if not stream:
            raise ValueError(f"Stream '{table}' not found")

        schema = {}
        properties = stream.json_schema.get("properties", {})

        for col_name, col_def in properties.items():
            # Map JSON Schema types to SQL-like types
            json_type = col_def.get("type", "string")
            if isinstance(json_type, list):
                # Handle ["null", "string"] format
                json_type = next((t for t in json_type if t != "null"), "string")

            sql_type = self._json_type_to_sql(json_type, col_def)
            schema[col_name] = sql_type

        return schema

    async def get_row_count(
        self,
        table: str,
        where: str | None = None,
    ) -> int:
        """
        Get row count for a stream.

        Note: Airbyte doesn't support direct row counts, so this fetches
        all data and counts records. For large datasets, consider using
        get_data_stream and counting incrementally.

        Args:
            table: Stream name
            where: Not used for Airbyte

        Returns:
            Number of rows
        """
        # For Airbyte, we need to do a full read to count
        # This is not efficient, but Airbyte doesn't support COUNT queries
        df = await self.get_data(table=table)
        return len(df)

    async def close(self) -> None:
        """Close adapter and cleanup resources."""
        self._catalog = None
        self._state = {}
        logger.info(f"Closed AirbyteSourceAdapter for {self.connector_name}")

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _find_stream(
        self, catalog: AirbyteCatalog, stream_name: str
    ) -> AirbyteStream | None:
        """Find a stream by name in the catalog."""
        for stream in catalog.streams:
            if stream.name == stream_name:
                return stream
        return None

    def _build_configured_catalog(
        self,
        stream: AirbyteStream,
        incremental: bool,
        cursor_field: str | None,
    ) -> ConfiguredAirbyteCatalog:
        """Build configured catalog for a single stream."""
        # Determine sync mode
        if incremental and SyncMode.INCREMENTAL in stream.supported_sync_modes:
            sync_mode = SyncMode.INCREMENTAL
        else:
            sync_mode = SyncMode.FULL_REFRESH

        # Determine cursor field
        cursor = []
        if sync_mode == SyncMode.INCREMENTAL:
            if cursor_field:
                cursor = [cursor_field]
            elif stream.default_cursor_field:
                cursor = stream.default_cursor_field

        configured_stream = ConfiguredAirbyteStream(
            stream=stream,
            sync_mode=sync_mode,
            destination_sync_mode=DestinationSyncMode.APPEND,
            cursor_field=cursor,
            primary_key=stream.source_defined_primary_key,
        )

        return ConfiguredAirbyteCatalog(streams=[configured_stream])

    def _records_to_dataframe(
        self, records: list[AirbyteRecordMessage], stream_name: str
    ) -> pd.DataFrame:
        """Convert Airbyte records to pandas DataFrame."""
        # Filter records for the specified stream
        stream_records = [r for r in records if r.stream == stream_name]

        if not stream_records:
            return pd.DataFrame()

        # Extract data dictionaries
        data = [r.data for r in stream_records]
        return pd.DataFrame(data)

    def _extract_state_data(self, state) -> dict[str, Any]:
        """Extract state data from AirbyteStateMessage."""
        if state.stream and state.stream.stream_state:
            return state.stream.stream_state
        elif state.global_ and state.global_.shared_state:
            return state.global_.shared_state
        elif state.data:
            return state.data
        return {}

    def _json_type_to_sql(self, json_type: str, col_def: dict) -> str:
        """Map JSON Schema type to SQL-like type."""
        type_mapping = {
            "string": "VARCHAR",
            "integer": "INTEGER",
            "number": "DECIMAL",
            "boolean": "BOOLEAN",
            "object": "JSONB",
            "array": "JSONB",
        }

        sql_type = type_mapping.get(json_type, "VARCHAR")

        # Check for format hints
        fmt = col_def.get("format", "")
        if fmt == "date-time":
            sql_type = "TIMESTAMP"
        elif fmt == "date":
            sql_type = "DATE"
        elif fmt == "time":
            sql_type = "TIME"

        return sql_type

    def set_state(self, stream_name: str, state: dict[str, Any]) -> None:
        """
        Set state for a stream (for resuming incremental syncs).

        Args:
            stream_name: Name of the stream
            state: State data to restore
        """
        self._state[stream_name] = state

    def get_state(self, stream_name: str) -> dict[str, Any] | None:
        """
        Get current state for a stream.

        Args:
            stream_name: Name of the stream

        Returns:
            State data or None if no state exists
        """
        return self._state.get(stream_name)

    def clear_state(self, stream_name: str | None = None) -> None:
        """
        Clear state for a stream or all streams.

        Args:
            stream_name: Specific stream to clear, or None for all
        """
        if stream_name:
            self._state.pop(stream_name, None)
        else:
            self._state = {}


# =============================================================================
# Factory Function
# =============================================================================


def create_airbyte_adapter(
    connector_name: str,
    config: dict[str, Any],
    source_name: str | None = None,
) -> AirbyteSourceAdapter:
    """
    Create an AirbyteSourceAdapter for a specific connector.

    Args:
        connector_name: Airbyte connector name (e.g., "source-postgres")
        config: Airbyte connector configuration
        source_name: Optional display name for the source

    Returns:
        Configured AirbyteSourceAdapter
    """
    connection_config = ConnectionConfig(
        source_type=f"airbyte:{connector_name}",
        source_name=source_name or connector_name,
        additional_params=config,
    )
    return AirbyteSourceAdapter(connection_config)


async def sync_airbyte_source(
    connector_name: str,
    config: dict[str, Any],
    streams: list[str] | None = None,
    incremental: bool = False,
) -> dict[str, pd.DataFrame]:
    """
    Convenience function to sync data from an Airbyte source.

    Args:
        connector_name: Airbyte connector name
        config: Airbyte connector configuration
        streams: List of streams to sync (None = all)
        incremental: Whether to use incremental sync

    Returns:
        Dictionary mapping stream names to DataFrames
    """
    adapter = create_airbyte_adapter(connector_name, config)

    try:
        # Test connection
        await adapter.test_connection()

        # Get streams to sync
        if streams is None:
            streams = await adapter.list_tables()

        # Sync each stream
        results = {}
        for stream in streams:
            try:
                df = await adapter.get_data(table=stream, incremental=incremental)
                results[stream] = df
                logger.info(f"Synced {len(df)} records from {stream}")
            except Exception as e:
                logger.error(f"Failed to sync {stream}: {e}")
                results[stream] = pd.DataFrame()  # Empty DataFrame on error

        return results

    finally:
        await adapter.close()
