"""
Airbyte Connector Integration for Atlas Pipeline
=================================================

This module provides two execution modes for Airbyte connectors:

1. **Docker-based Execution** (Recommended for Production)
   - Runs official Airbyte connector Docker images
   - Supports 100+ connectors via Docker Hub
   - Full Airbyte protocol support (SPEC, CHECK, DISCOVER, READ)
   - Uses: protocol.py, executor.py, adapter.py, registry.py

2. **PyAirbyte SDK Execution** (For Development/Testing)
   - Uses Python SDK without Docker dependency
   - 70+ connectors via pip install
   - Simpler setup, faster iteration
   - Uses: pyairbyte_executor.py, real_pyairbyte.py

Usage (Docker-based):
    from app.connectors.airbyte import (
        AirbyteSourceAdapter,
        create_airbyte_adapter,
        list_connectors,
    )

    adapter = create_airbyte_adapter("source-postgres", {"host": "localhost", ...})
    await adapter.test_connection()
    df = await adapter.get_data(table="users")

Usage (PyAirbyte SDK):
    from app.connectors.airbyte import PyAirbyteExecutor

    executor = PyAirbyteExecutor()
    streams = executor.discover_streams("source-postgres", {...})
    records = executor.read_stream("source-postgres", {...}, "users")
"""

# =============================================================================
# Docker-based Airbyte Execution (Production)
# =============================================================================

from .protocol import (
    # Message types
    AirbyteMessage,
    AirbyteMessageType,
    AirbyteRecordMessage,
    AirbyteStateMessage,
    AirbyteLogMessage,
    AirbyteLogLevel,
    # Catalog
    AirbyteCatalog,
    AirbyteStream,
    ConfiguredAirbyteCatalog,
    ConfiguredAirbyteStream,
    SyncMode,
    DestinationSyncMode,
    # Connection
    AirbyteConnectionStatus,
    AirbyteConnectionStatusMessage,
    AirbyteSpecification,
    # Trace
    AirbyteTraceMessage,
    AirbyteErrorTraceMessage,
    AirbyteTraceType,
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

from .executor import (
    AirbyteDockerExecutor,
    ExecutorConfig,
    ExecutionResult,
    AirbyteCommand,
    get_docker_executor,
    pull_image,
    check_docker_available,
)

from .adapter import (
    AirbyteSourceAdapter,
    create_airbyte_adapter,
    sync_airbyte_source,
)

from .registry import (
    ConnectorInfo,
    ConnectorCategory,
    get_connector_image,
    get_connector_info,
    list_connectors,
    list_categories,
    search_connectors,
    get_connector_count,
    get_category_counts,
    AIRBYTE_CONNECTORS,
)

# =============================================================================
# PyAirbyte SDK Execution (Development)
# =============================================================================

from .pyairbyte_executor import PyAirbyteExecutor, get_pyairbyte_executor
from .state_manager import StateManager, get_state_manager, SourceState, StreamState
from .sync_scheduler import SyncScheduler, get_sync_scheduler, SyncJob, SyncStatus, ScheduledSync
from .performance import (
    PerformanceOptimizedSync,
    get_performance_optimizer,
    BatchConfig,
    SyncProgress,
    SyncStrategy
)
from .real_pyairbyte import (
    RealPyAirbyteExecutor,
    get_real_pyairbyte_executor,
    is_pyairbyte_available
)

__all__ = [
    # ==========================================================================
    # Docker-based Execution (Production)
    # ==========================================================================
    # Protocol models
    "AirbyteMessage",
    "AirbyteMessageType",
    "AirbyteRecordMessage",
    "AirbyteStateMessage",
    "AirbyteLogMessage",
    "AirbyteLogLevel",
    "AirbyteCatalog",
    "AirbyteStream",
    "ConfiguredAirbyteCatalog",
    "ConfiguredAirbyteStream",
    "SyncMode",
    "DestinationSyncMode",
    "AirbyteConnectionStatus",
    "AirbyteConnectionStatusMessage",
    "AirbyteSpecification",
    "AirbyteTraceMessage",
    "AirbyteErrorTraceMessage",
    "AirbyteTraceType",
    # Protocol utilities
    "parse_messages_from_output",
    "filter_records",
    "filter_state",
    "get_last_state",
    "get_errors",
    "create_record_message",
    "create_state_message",
    "create_log_message",
    "create_error_trace",
    # Docker executor
    "AirbyteDockerExecutor",
    "ExecutorConfig",
    "ExecutionResult",
    "AirbyteCommand",
    "get_docker_executor",
    "pull_image",
    "check_docker_available",
    # Adapter
    "AirbyteSourceAdapter",
    "create_airbyte_adapter",
    "sync_airbyte_source",
    # Registry
    "ConnectorInfo",
    "ConnectorCategory",
    "get_connector_image",
    "get_connector_info",
    "list_connectors",
    "list_categories",
    "search_connectors",
    "get_connector_count",
    "get_category_counts",
    "AIRBYTE_CONNECTORS",
    # ==========================================================================
    # PyAirbyte SDK Execution (Development)
    # ==========================================================================
    # Core executor
    "PyAirbyteExecutor",
    "get_pyairbyte_executor",
    # State management
    "StateManager",
    "get_state_manager",
    "SourceState",
    "StreamState",
    # Sync scheduling
    "SyncScheduler",
    "get_sync_scheduler",
    "SyncJob",
    "SyncStatus",
    "ScheduledSync",
    # Performance optimization
    "PerformanceOptimizedSync",
    "get_performance_optimizer",
    "BatchConfig",
    "SyncProgress",
    "SyncStrategy",
    # Real PyAirbyte
    "RealPyAirbyteExecutor",
    "get_real_pyairbyte_executor",
    "is_pyairbyte_available",
]
