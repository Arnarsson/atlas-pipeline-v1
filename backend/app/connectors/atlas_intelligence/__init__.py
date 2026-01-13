"""AtlasIntelligence connector integration for Atlas Pipeline.

Unified connector platform with 400+ data sources.
Uses PyAirbyte under the hood for reliable data extraction.
"""

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
    # Real PyAirbyte integration
    "RealPyAirbyteExecutor",
    "get_real_pyairbyte_executor",
    "is_pyairbyte_available",
]
