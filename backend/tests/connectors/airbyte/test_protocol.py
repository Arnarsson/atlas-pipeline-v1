"""
Tests for Airbyte Protocol Models
=================================

Tests the AirbyteMessage protocol implementation for Docker-based connector execution.
"""

import json
import pytest
from datetime import datetime

from app.connectors.airbyte.protocol import (
    # Enums
    AirbyteMessageType,
    AirbyteLogLevel,
    AirbyteConnectionStatus,
    SyncMode,
    DestinationSyncMode,
    AirbyteTraceType,
    # Models
    AirbyteMessage,
    AirbyteRecordMessage,
    AirbyteStateMessage,
    AirbyteLogMessage,
    AirbyteCatalog,
    AirbyteStream,
    ConfiguredAirbyteCatalog,
    ConfiguredAirbyteStream,
    AirbyteSpecification,
    AirbyteConnectionStatusMessage,
    AirbyteTraceMessage,
    AirbyteErrorTraceMessage,
    # Utilities
    parse_messages_from_output,
    filter_records,
    filter_state,
    get_last_state,
    get_errors,
    create_record_message,
    create_state_message,
    create_log_message,
    create_error_trace,
)


class TestAirbyteMessageTypes:
    """Test message type enums."""

    def test_message_types(self):
        """Test all message types are defined."""
        assert AirbyteMessageType.RECORD == "RECORD"
        assert AirbyteMessageType.STATE == "STATE"
        assert AirbyteMessageType.LOG == "LOG"
        assert AirbyteMessageType.SPEC == "SPEC"
        assert AirbyteMessageType.CATALOG == "CATALOG"
        assert AirbyteMessageType.CONNECTION_STATUS == "CONNECTION_STATUS"
        assert AirbyteMessageType.TRACE == "TRACE"
        assert AirbyteMessageType.CONTROL == "CONTROL"

    def test_log_levels(self):
        """Test all log levels are defined."""
        assert AirbyteLogLevel.FATAL == "FATAL"
        assert AirbyteLogLevel.ERROR == "ERROR"
        assert AirbyteLogLevel.WARN == "WARN"
        assert AirbyteLogLevel.INFO == "INFO"
        assert AirbyteLogLevel.DEBUG == "DEBUG"
        assert AirbyteLogLevel.TRACE == "TRACE"

    def test_connection_status(self):
        """Test connection status values."""
        assert AirbyteConnectionStatus.SUCCEEDED == "SUCCEEDED"
        assert AirbyteConnectionStatus.FAILED == "FAILED"

    def test_sync_modes(self):
        """Test sync modes."""
        assert SyncMode.FULL_REFRESH == "full_refresh"
        assert SyncMode.INCREMENTAL == "incremental"

    def test_destination_sync_modes(self):
        """Test destination sync modes."""
        assert DestinationSyncMode.APPEND == "append"
        assert DestinationSyncMode.OVERWRITE == "overwrite"
        assert DestinationSyncMode.APPEND_DEDUP == "append_dedup"


class TestAirbyteMessage:
    """Test AirbyteMessage model."""

    def test_parse_record_message(self):
        """Test parsing a RECORD message."""
        json_str = json.dumps({
            "type": "RECORD",
            "record": {
                "stream": "users",
                "data": {"id": 1, "name": "Alice"},
                "emitted_at": 1704067200000,
            }
        })

        msg = AirbyteMessage.from_json(json_str)

        assert msg.type == AirbyteMessageType.RECORD
        assert msg.record is not None
        assert msg.record.stream == "users"
        assert msg.record.data == {"id": 1, "name": "Alice"}
        assert msg.record.emitted_at == 1704067200000

    def test_parse_state_message(self):
        """Test parsing a STATE message."""
        json_str = json.dumps({
            "type": "STATE",
            "state": {
                "type": "STREAM",
                "stream": {
                    "stream_descriptor": {"name": "users"},
                    "stream_state": {"cursor": "2024-01-01"}
                }
            }
        })

        msg = AirbyteMessage.from_json(json_str)

        assert msg.type == AirbyteMessageType.STATE
        assert msg.state is not None
        assert msg.state.type == "STREAM"
        assert msg.state.stream.stream_descriptor == {"name": "users"}

    def test_parse_log_message(self):
        """Test parsing a LOG message."""
        json_str = json.dumps({
            "type": "LOG",
            "log": {
                "level": "INFO",
                "message": "Starting sync..."
            }
        })

        msg = AirbyteMessage.from_json(json_str)

        assert msg.type == AirbyteMessageType.LOG
        assert msg.log is not None
        assert msg.log.level == AirbyteLogLevel.INFO
        assert msg.log.message == "Starting sync..."

    def test_parse_catalog_message(self):
        """Test parsing a CATALOG message."""
        json_str = json.dumps({
            "type": "CATALOG",
            "catalog": {
                "streams": [
                    {
                        "name": "users",
                        "jsonSchema": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "name": {"type": "string"}
                            }
                        },
                        "supported_sync_modes": ["full_refresh", "incremental"]
                    }
                ]
            }
        })

        msg = AirbyteMessage.from_json(json_str)

        assert msg.type == AirbyteMessageType.CATALOG
        assert msg.catalog is not None
        assert len(msg.catalog.streams) == 1
        assert msg.catalog.streams[0].name == "users"

    def test_parse_spec_message(self):
        """Test parsing a SPEC message."""
        json_str = json.dumps({
            "type": "SPEC",
            "spec": {
                "documentationUrl": "https://docs.example.com",
                "connectionSpecification": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"},
                        "port": {"type": "integer"}
                    }
                },
                "supportsIncremental": True
            }
        })

        msg = AirbyteMessage.from_json(json_str)

        assert msg.type == AirbyteMessageType.SPEC
        assert msg.spec is not None
        assert msg.spec.supportsIncremental is True
        assert "host" in msg.spec.connectionSpecification.get("properties", {})

    def test_parse_connection_status_message(self):
        """Test parsing a CONNECTION_STATUS message."""
        json_str = json.dumps({
            "type": "CONNECTION_STATUS",
            "connectionStatus": {
                "status": "SUCCEEDED",
                "message": "Connection successful"
            }
        })

        msg = AirbyteMessage.from_json(json_str)

        assert msg.type == AirbyteMessageType.CONNECTION_STATUS
        assert msg.connectionStatus is not None
        assert msg.connectionStatus.status == AirbyteConnectionStatus.SUCCEEDED
        assert msg.connectionStatus.message == "Connection successful"

    def test_parse_trace_error_message(self):
        """Test parsing a TRACE error message."""
        json_str = json.dumps({
            "type": "TRACE",
            "trace": {
                "type": "ERROR",
                "emitted_at": 1704067200.0,
                "error": {
                    "message": "Connection failed",
                    "internal_message": "ECONNREFUSED",
                    "failure_type": "config_error"
                }
            }
        })

        msg = AirbyteMessage.from_json(json_str)

        assert msg.type == AirbyteMessageType.TRACE
        assert msg.trace is not None
        assert msg.trace.type == AirbyteTraceType.ERROR
        assert msg.trace.error is not None
        assert msg.trace.error.message == "Connection failed"

    def test_to_json(self):
        """Test serializing message to JSON."""
        msg = AirbyteMessage(
            type=AirbyteMessageType.LOG,
            log=AirbyteLogMessage(
                level=AirbyteLogLevel.INFO,
                message="Test message"
            )
        )

        json_str = msg.to_json()
        parsed = json.loads(json_str)

        assert parsed["type"] == "LOG"
        assert parsed["log"]["level"] == "INFO"
        assert parsed["log"]["message"] == "Test message"

    def test_invalid_json_raises_error(self):
        """Test that invalid JSON raises ValueError."""
        with pytest.raises(ValueError):
            AirbyteMessage.from_json("not valid json")


class TestParseMessagesFromOutput:
    """Test parsing multiple messages from connector output."""

    def test_parse_multiple_messages(self):
        """Test parsing multi-line output."""
        output = """
{"type": "LOG", "log": {"level": "INFO", "message": "Starting"}}
{"type": "RECORD", "record": {"stream": "users", "data": {"id": 1}, "emitted_at": 1704067200000}}
{"type": "RECORD", "record": {"stream": "users", "data": {"id": 2}, "emitted_at": 1704067200001}}
{"type": "STATE", "state": {"type": "STREAM", "stream": {"stream_descriptor": {"name": "users"}, "stream_state": {"cursor": "2"}}}}
"""

        messages = parse_messages_from_output(output)

        assert len(messages) == 4
        assert messages[0].type == AirbyteMessageType.LOG
        assert messages[1].type == AirbyteMessageType.RECORD
        assert messages[2].type == AirbyteMessageType.RECORD
        assert messages[3].type == AirbyteMessageType.STATE

    def test_skip_invalid_lines(self):
        """Test that invalid lines are skipped."""
        output = """
{"type": "LOG", "log": {"level": "INFO", "message": "Starting"}}
not valid json
{"type": "RECORD", "record": {"stream": "users", "data": {"id": 1}, "emitted_at": 1704067200000}}
"""

        messages = parse_messages_from_output(output)

        # Should skip the invalid line
        assert len(messages) == 2

    def test_empty_output(self):
        """Test parsing empty output."""
        messages = parse_messages_from_output("")
        assert len(messages) == 0

        messages = parse_messages_from_output("   \n   \n   ")
        assert len(messages) == 0


class TestFilterFunctions:
    """Test message filtering functions."""

    def setup_method(self):
        """Set up test messages."""
        self.messages = [
            AirbyteMessage(
                type=AirbyteMessageType.LOG,
                log=AirbyteLogMessage(level=AirbyteLogLevel.INFO, message="Starting")
            ),
            AirbyteMessage(
                type=AirbyteMessageType.RECORD,
                record=AirbyteRecordMessage(stream="users", data={"id": 1}, emitted_at=1704067200000)
            ),
            AirbyteMessage(
                type=AirbyteMessageType.RECORD,
                record=AirbyteRecordMessage(stream="users", data={"id": 2}, emitted_at=1704067200001)
            ),
            AirbyteMessage(
                type=AirbyteMessageType.STATE,
                state=AirbyteStateMessage(type="STREAM")
            ),
            AirbyteMessage(
                type=AirbyteMessageType.STATE,
                state=AirbyteStateMessage(type="STREAM")
            ),
        ]

    def test_filter_records(self):
        """Test filtering record messages."""
        records = filter_records(self.messages)

        assert len(records) == 2
        assert records[0].stream == "users"
        assert records[0].data == {"id": 1}
        assert records[1].data == {"id": 2}

    def test_filter_state(self):
        """Test filtering state messages."""
        states = filter_state(self.messages)

        assert len(states) == 2
        assert states[0].type == "STREAM"

    def test_get_last_state(self):
        """Test getting last state message."""
        last_state = get_last_state(self.messages)

        assert last_state is not None
        assert last_state.type == "STREAM"

    def test_get_last_state_empty(self):
        """Test getting last state from messages without state."""
        messages = [
            AirbyteMessage(
                type=AirbyteMessageType.RECORD,
                record=AirbyteRecordMessage(stream="users", data={"id": 1}, emitted_at=1704067200000)
            )
        ]

        last_state = get_last_state(messages)
        assert last_state is None


class TestGetErrors:
    """Test error extraction."""

    def test_get_errors(self):
        """Test extracting error traces."""
        messages = [
            AirbyteMessage(
                type=AirbyteMessageType.LOG,
                log=AirbyteLogMessage(level=AirbyteLogLevel.INFO, message="Starting")
            ),
            AirbyteMessage(
                type=AirbyteMessageType.TRACE,
                trace=AirbyteTraceMessage(
                    type=AirbyteTraceType.ERROR,
                    emitted_at=1704067200.0,
                    error=AirbyteErrorTraceMessage(
                        message="Connection failed",
                        failure_type="config_error"
                    )
                )
            ),
        ]

        errors = get_errors(messages)

        assert len(errors) == 1
        assert errors[0].message == "Connection failed"
        assert errors[0].failure_type == "config_error"

    def test_no_errors(self):
        """Test when there are no errors."""
        messages = [
            AirbyteMessage(
                type=AirbyteMessageType.LOG,
                log=AirbyteLogMessage(level=AirbyteLogLevel.INFO, message="Starting")
            ),
        ]

        errors = get_errors(messages)
        assert len(errors) == 0


class TestMessageBuilders:
    """Test convenience functions for creating messages."""

    def test_create_record_message(self):
        """Test creating a record message."""
        msg = create_record_message("users", {"id": 1, "name": "Alice"})

        assert msg.type == AirbyteMessageType.RECORD
        assert msg.record.stream == "users"
        assert msg.record.data == {"id": 1, "name": "Alice"}
        assert msg.record.emitted_at > 0

    def test_create_record_message_with_namespace(self):
        """Test creating a record message with namespace."""
        msg = create_record_message("users", {"id": 1}, namespace="public")

        assert msg.record.namespace == "public"

    def test_create_state_message(self):
        """Test creating a state message."""
        msg = create_state_message("users", None, {"cursor": "2024-01-01"})

        assert msg.type == AirbyteMessageType.STATE
        assert msg.state.type == "STREAM"
        assert msg.state.stream.stream_descriptor == {"name": "users"}
        assert msg.state.stream.stream_state == {"cursor": "2024-01-01"}

    def test_create_log_message(self):
        """Test creating a log message."""
        msg = create_log_message(AirbyteLogLevel.INFO, "Test message")

        assert msg.type == AirbyteMessageType.LOG
        assert msg.log.level == AirbyteLogLevel.INFO
        assert msg.log.message == "Test message"

    def test_create_error_trace(self):
        """Test creating an error trace."""
        msg = create_error_trace(
            "Connection failed",
            internal_message="ECONNREFUSED",
            failure_type="config_error"
        )

        assert msg.type == AirbyteMessageType.TRACE
        assert msg.trace.type == AirbyteTraceType.ERROR
        assert msg.trace.error.message == "Connection failed"
        assert msg.trace.error.internal_message == "ECONNREFUSED"
        assert msg.trace.error.failure_type == "config_error"


class TestCatalogModels:
    """Test catalog-related models."""

    def test_airbyte_stream(self):
        """Test AirbyteStream model."""
        stream = AirbyteStream(
            name="users",
            json_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"}
                }
            },
            supported_sync_modes=[SyncMode.FULL_REFRESH, SyncMode.INCREMENTAL],
            source_defined_cursor=True,
            default_cursor_field=["updated_at"],
        )

        assert stream.name == "users"
        assert SyncMode.INCREMENTAL in stream.supported_sync_modes
        assert stream.source_defined_cursor is True
        assert stream.default_cursor_field == ["updated_at"]

    def test_configured_airbyte_stream(self):
        """Test ConfiguredAirbyteStream model."""
        stream = AirbyteStream(
            name="users",
            supported_sync_modes=[SyncMode.FULL_REFRESH, SyncMode.INCREMENTAL],
        )

        configured = ConfiguredAirbyteStream(
            stream=stream,
            sync_mode=SyncMode.INCREMENTAL,
            destination_sync_mode=DestinationSyncMode.APPEND,
            cursor_field=["updated_at"],
        )

        assert configured.stream.name == "users"
        assert configured.sync_mode == SyncMode.INCREMENTAL
        assert configured.cursor_field == ["updated_at"]

    def test_airbyte_catalog(self):
        """Test AirbyteCatalog model."""
        catalog = AirbyteCatalog(
            streams=[
                AirbyteStream(name="users"),
                AirbyteStream(name="orders"),
            ]
        )

        assert len(catalog.streams) == 2
        assert catalog.streams[0].name == "users"
        assert catalog.streams[1].name == "orders"

    def test_configured_airbyte_catalog(self):
        """Test ConfiguredAirbyteCatalog model."""
        catalog = ConfiguredAirbyteCatalog(
            streams=[
                ConfiguredAirbyteStream(
                    stream=AirbyteStream(name="users"),
                    sync_mode=SyncMode.FULL_REFRESH,
                )
            ]
        )

        assert len(catalog.streams) == 1
        assert catalog.streams[0].stream.name == "users"


class TestSpecification:
    """Test AirbyteSpecification model."""

    def test_specification(self):
        """Test AirbyteSpecification model."""
        spec = AirbyteSpecification(
            documentationUrl="https://docs.example.com",
            connectionSpecification={
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer", "default": 5432}
                },
                "required": ["host"]
            },
            supportsIncremental=True,
            supportsNormalization=False,
        )

        assert spec.documentationUrl == "https://docs.example.com"
        assert spec.supportsIncremental is True
        assert spec.supportsNormalization is False
        assert "host" in spec.connectionSpecification.get("properties", {})
