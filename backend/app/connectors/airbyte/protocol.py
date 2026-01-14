"""
Airbyte Protocol Models
=======================

Implements the Airbyte Connector Protocol for Docker-based connector execution.
This enables Atlas to run ANY Airbyte connector via Docker containers.

Protocol Reference: https://docs.airbyte.com/understanding-airbyte/airbyte-protocol

Message Types:
- RECORD: Data records from source
- STATE: Checkpoint for incremental syncs
- CATALOG: Schema discovery results
- SPEC: Connector configuration specification
- LOG: Logging messages
- TRACE: Error traces and analytics
- CONTROL: Connector control messages
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================


class AirbyteMessageType(str, Enum):
    """Airbyte protocol message types."""

    RECORD = "RECORD"
    STATE = "STATE"
    LOG = "LOG"
    SPEC = "SPEC"
    CATALOG = "CATALOG"
    CONNECTION_STATUS = "CONNECTION_STATUS"
    TRACE = "TRACE"
    CONTROL = "CONTROL"


class AirbyteLogLevel(str, Enum):
    """Log levels for Airbyte LOG messages."""

    FATAL = "FATAL"
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"
    DEBUG = "DEBUG"
    TRACE = "TRACE"


class AirbyteConnectionStatus(str, Enum):
    """Connection status for CHECK command."""

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class SyncMode(str, Enum):
    """Supported sync modes (Fivetran/Airbyte-style)."""

    FULL_REFRESH = "full_refresh"
    INCREMENTAL = "incremental"
    CDC = "cdc"  # Change Data Capture - Fivetran/Airbyte style


class DestinationSyncMode(str, Enum):
    """Destination sync modes."""

    APPEND = "append"
    OVERWRITE = "overwrite"
    APPEND_DEDUP = "append_dedup"


class CDCOperation(str, Enum):
    """CDC operation types (Fivetran/Airbyte-style)."""

    INSERT = "c"    # Create/Insert - Debezium convention
    UPDATE = "u"    # Update
    DELETE = "d"    # Delete
    READ = "r"      # Snapshot read (initial load)
    TRUNCATE = "t"  # Truncate table


class AirbyteTraceType(str, Enum):
    """Types of trace messages."""

    ERROR = "ERROR"
    ESTIMATE = "ESTIMATE"
    STREAM_STATUS = "STREAM_STATUS"
    ANALYTICS = "ANALYTICS"


class AirbyteStreamStatus(str, Enum):
    """Stream status types."""

    STARTED = "STARTED"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"


# ============================================================================
# Spec Models (Connector Configuration Specification)
# ============================================================================


class AirbyteSpecification(BaseModel):
    """Connector specification returned by SPEC command."""

    documentationUrl: str | None = None
    changelogUrl: str | None = None
    connectionSpecification: dict[str, Any] = Field(default_factory=dict)
    supportsIncremental: bool = False
    supportsNormalization: bool = False
    supportsDBT: bool = False
    supported_destination_sync_modes: list[str] = Field(default_factory=list)
    authSpecification: dict[str, Any] | None = None
    advancedAuth: dict[str, Any] | None = None


# ============================================================================
# Catalog Models (Schema Discovery)
# ============================================================================


class AirbyteStreamJsonSchema(BaseModel):
    """JSON Schema for a stream."""

    type: str = "object"
    properties: dict[str, Any] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)
    additionalProperties: bool = True


class AirbyteStream(BaseModel):
    """A stream (table/entity) available from a source."""

    name: str
    json_schema: dict[str, Any] = Field(default_factory=dict, alias="jsonSchema")
    supported_sync_modes: list[SyncMode] = Field(default_factory=lambda: [SyncMode.FULL_REFRESH])
    source_defined_cursor: bool = False
    default_cursor_field: list[str] = Field(default_factory=list)
    source_defined_primary_key: list[list[str]] = Field(default_factory=list)
    namespace: str | None = None

    class Config:
        populate_by_name = True


class ConfiguredAirbyteStream(BaseModel):
    """A stream configured for sync with selected sync mode."""

    stream: AirbyteStream
    sync_mode: SyncMode = SyncMode.FULL_REFRESH
    destination_sync_mode: DestinationSyncMode = DestinationSyncMode.APPEND
    cursor_field: list[str] = Field(default_factory=list)
    primary_key: list[list[str]] = Field(default_factory=list)


class AirbyteCatalog(BaseModel):
    """Catalog of streams returned by DISCOVER command."""

    streams: list[AirbyteStream] = Field(default_factory=list)


class ConfiguredAirbyteCatalog(BaseModel):
    """Configured catalog for READ command."""

    streams: list[ConfiguredAirbyteStream] = Field(default_factory=list)


# ============================================================================
# State Models (Incremental Sync Checkpoints)
# ============================================================================


class AirbyteStreamState(BaseModel):
    """State for a single stream."""

    stream_descriptor: dict[str, str] = Field(default_factory=dict)
    stream_state: dict[str, Any] = Field(default_factory=dict)


class AirbyteGlobalState(BaseModel):
    """Global state across all streams."""

    shared_state: dict[str, Any] = Field(default_factory=dict)
    stream_states: list[AirbyteStreamState] = Field(default_factory=list)


class AirbyteStateMessage(BaseModel):
    """State message for checkpointing."""

    type: str = "STREAM"  # STREAM, GLOBAL, or LEGACY
    stream: AirbyteStreamState | None = None
    global_: AirbyteGlobalState | None = Field(None, alias="global")
    data: dict[str, Any] | None = None  # Legacy format

    class Config:
        populate_by_name = True


# ============================================================================
# Record Models (Data Records)
# ============================================================================


class AirbyteRecordMessage(BaseModel):
    """A data record from a source stream."""

    stream: str
    data: dict[str, Any]
    emitted_at: int  # Unix timestamp in milliseconds
    namespace: str | None = None


# ============================================================================
# Log Models
# ============================================================================


class AirbyteLogMessage(BaseModel):
    """Log message from connector."""

    level: AirbyteLogLevel
    message: str
    stack_trace: str | None = None


# ============================================================================
# Connection Status Models
# ============================================================================


class AirbyteConnectionStatusMessage(BaseModel):
    """Connection status from CHECK command."""

    status: AirbyteConnectionStatus
    message: str | None = None


# ============================================================================
# Trace Models (Errors and Analytics)
# ============================================================================


class AirbyteErrorTraceMessage(BaseModel):
    """Error trace message."""

    message: str
    internal_message: str | None = None
    stack_trace: str | None = None
    failure_type: str | None = None  # system_error, config_error, transient_error


class AirbyteEstimateTraceMessage(BaseModel):
    """Estimate trace for sync progress."""

    name: str
    type: str  # STREAM or SYNC
    namespace: str | None = None
    row_estimate: int | None = None
    byte_estimate: int | None = None


class AirbyteStreamStatusTraceMessage(BaseModel):
    """Stream status trace."""

    stream_descriptor: dict[str, str]
    status: AirbyteStreamStatus
    reasons: list[dict[str, Any]] = Field(default_factory=list)


class AirbyteTraceMessage(BaseModel):
    """Trace message containing error, estimate, or status."""

    type: AirbyteTraceType
    emitted_at: float  # Unix timestamp
    error: AirbyteErrorTraceMessage | None = None
    estimate: AirbyteEstimateTraceMessage | None = None
    stream_status: AirbyteStreamStatusTraceMessage | None = None


# ============================================================================
# Control Models
# ============================================================================


class AirbyteControlConnectorConfigMessage(BaseModel):
    """Control message for connector config updates."""

    config: dict[str, Any]


class AirbyteControlMessage(BaseModel):
    """Control message from connector."""

    type: str  # CONNECTOR_CONFIG
    emitted_at: float
    connectorConfig: AirbyteControlConnectorConfigMessage | None = None


# ============================================================================
# Main Airbyte Message
# ============================================================================


class AirbyteMessage(BaseModel):
    """
    Main Airbyte protocol message.

    All connector output is wrapped in this message type.
    The `type` field determines which sub-message is populated.
    """

    type: AirbyteMessageType
    record: AirbyteRecordMessage | None = None
    state: AirbyteStateMessage | None = None
    log: AirbyteLogMessage | None = None
    spec: AirbyteSpecification | None = None
    catalog: AirbyteCatalog | None = None
    connectionStatus: AirbyteConnectionStatusMessage | None = None
    trace: AirbyteTraceMessage | None = None
    control: AirbyteControlMessage | None = None

    @classmethod
    def from_json(cls, json_str: str) -> "AirbyteMessage":
        """Parse an Airbyte message from JSON string."""
        try:
            data = json.loads(json_str)
            return cls.model_validate(data)
        except Exception as e:
            logger.error(f"Failed to parse Airbyte message: {e}")
            raise ValueError(f"Invalid Airbyte message: {e}")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AirbyteMessage":
        """Parse an Airbyte message from dictionary."""
        return cls.model_validate(data)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(exclude_none=True)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return self.model_dump(exclude_none=True)


# ============================================================================
# Message Builders (Convenience Functions)
# ============================================================================


def create_record_message(
    stream: str,
    data: dict[str, Any],
    namespace: str | None = None,
) -> AirbyteMessage:
    """Create a RECORD message."""
    return AirbyteMessage(
        type=AirbyteMessageType.RECORD,
        record=AirbyteRecordMessage(
            stream=stream,
            data=data,
            emitted_at=int(datetime.utcnow().timestamp() * 1000),
            namespace=namespace,
        ),
    )


def create_state_message(
    stream_name: str,
    stream_namespace: str | None,
    state_data: dict[str, Any],
) -> AirbyteMessage:
    """Create a STATE message for a stream."""
    return AirbyteMessage(
        type=AirbyteMessageType.STATE,
        state=AirbyteStateMessage(
            type="STREAM",
            stream=AirbyteStreamState(
                stream_descriptor={
                    "name": stream_name,
                    **({"namespace": stream_namespace} if stream_namespace else {}),
                },
                stream_state=state_data,
            ),
        ),
    )


def create_log_message(
    level: AirbyteLogLevel,
    message: str,
    stack_trace: str | None = None,
) -> AirbyteMessage:
    """Create a LOG message."""
    return AirbyteMessage(
        type=AirbyteMessageType.LOG,
        log=AirbyteLogMessage(
            level=level,
            message=message,
            stack_trace=stack_trace,
        ),
    )


def create_error_trace(
    message: str,
    internal_message: str | None = None,
    stack_trace: str | None = None,
    failure_type: str = "system_error",
) -> AirbyteMessage:
    """Create an error TRACE message."""
    return AirbyteMessage(
        type=AirbyteMessageType.TRACE,
        trace=AirbyteTraceMessage(
            type=AirbyteTraceType.ERROR,
            emitted_at=datetime.utcnow().timestamp(),
            error=AirbyteErrorTraceMessage(
                message=message,
                internal_message=internal_message,
                stack_trace=stack_trace,
                failure_type=failure_type,
            ),
        ),
    )


# ============================================================================
# Message Parsing Utilities
# ============================================================================


def parse_messages_from_output(output: str) -> list[AirbyteMessage]:
    """
    Parse multiple Airbyte messages from connector output.

    Connectors output one JSON message per line.

    Args:
        output: Multi-line string output from connector

    Returns:
        List of parsed AirbyteMessage objects
    """
    messages = []

    for line in output.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        try:
            msg = AirbyteMessage.from_json(line)
            messages.append(msg)
        except Exception as e:
            # Log but don't fail on unparseable lines
            logger.warning(f"Skipping unparseable line: {e}")

    return messages


def filter_records(messages: list[AirbyteMessage]) -> list[AirbyteRecordMessage]:
    """Extract only RECORD messages."""
    return [
        msg.record
        for msg in messages
        if msg.type == AirbyteMessageType.RECORD and msg.record
    ]


def filter_state(messages: list[AirbyteMessage]) -> list[AirbyteStateMessage]:
    """Extract only STATE messages."""
    return [
        msg.state
        for msg in messages
        if msg.type == AirbyteMessageType.STATE and msg.state
    ]


def get_last_state(messages: list[AirbyteMessage]) -> AirbyteStateMessage | None:
    """Get the last STATE message (final checkpoint)."""
    states = filter_state(messages)
    return states[-1] if states else None


def filter_logs(
    messages: list[AirbyteMessage],
    min_level: AirbyteLogLevel = AirbyteLogLevel.INFO,
) -> list[AirbyteLogMessage]:
    """Extract LOG messages at or above specified level."""
    level_order = [
        AirbyteLogLevel.TRACE,
        AirbyteLogLevel.DEBUG,
        AirbyteLogLevel.INFO,
        AirbyteLogLevel.WARN,
        AirbyteLogLevel.ERROR,
        AirbyteLogLevel.FATAL,
    ]
    min_idx = level_order.index(min_level)

    return [
        msg.log
        for msg in messages
        if msg.type == AirbyteMessageType.LOG
        and msg.log
        and level_order.index(msg.log.level) >= min_idx
    ]


def get_errors(messages: list[AirbyteMessage]) -> list[AirbyteErrorTraceMessage]:
    """Extract error traces from messages."""
    errors = []

    for msg in messages:
        if msg.type == AirbyteMessageType.TRACE and msg.trace:
            if msg.trace.type == AirbyteTraceType.ERROR and msg.trace.error:
                errors.append(msg.trace.error)

    return errors
