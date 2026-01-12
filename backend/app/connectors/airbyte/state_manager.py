"""
PyAirbyte State Manager - Persist sync state for incremental loads.

Manages state persistence for Airbyte connectors to enable incremental syncs.
State is stored in-memory by default, with optional PostgreSQL persistence.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class StreamState:
    """State for a single stream within a source."""
    stream_name: str
    cursor_field: Optional[str] = None
    cursor_value: Optional[Any] = None
    sync_mode: str = "full_refresh"
    last_synced_at: Optional[datetime] = None
    records_synced: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stream_name": self.stream_name,
            "cursor_field": self.cursor_field,
            "cursor_value": self.cursor_value,
            "sync_mode": self.sync_mode,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
            "records_synced": self.records_synced,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamState":
        """Create from dictionary."""
        last_synced = data.get("last_synced_at")
        if last_synced and isinstance(last_synced, str):
            last_synced = datetime.fromisoformat(last_synced)

        return cls(
            stream_name=data["stream_name"],
            cursor_field=data.get("cursor_field"),
            cursor_value=data.get("cursor_value"),
            sync_mode=data.get("sync_mode", "full_refresh"),
            last_synced_at=last_synced,
            records_synced=data.get("records_synced", 0),
            metadata=data.get("metadata", {})
        )


@dataclass
class SourceState:
    """Complete state for a source connector."""
    source_name: str
    source_id: str
    streams: Dict[str, StreamState] = field(default_factory=dict)
    global_state: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "source_name": self.source_name,
            "source_id": self.source_id,
            "streams": {name: state.to_dict() for name, state in self.streams.items()},
            "global_state": self.global_state,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceState":
        """Create from dictionary."""
        streams = {}
        for name, stream_data in data.get("streams", {}).items():
            streams[name] = StreamState.from_dict(stream_data)

        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        else:
            created_at = datetime.utcnow()

        updated_at = data.get("updated_at")
        if updated_at and isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        else:
            updated_at = datetime.utcnow()

        return cls(
            source_name=data["source_name"],
            source_id=data["source_id"],
            streams=streams,
            global_state=data.get("global_state", {}),
            created_at=created_at,
            updated_at=updated_at,
            version=data.get("version", 1)
        )

    def get_stream_state(self, stream_name: str) -> Optional[StreamState]:
        """Get state for a specific stream."""
        return self.streams.get(stream_name)

    def set_stream_state(
        self,
        stream_name: str,
        cursor_field: Optional[str] = None,
        cursor_value: Optional[Any] = None,
        sync_mode: str = "full_refresh",
        records_synced: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StreamState:
        """Set or update state for a stream."""
        if stream_name in self.streams:
            state = self.streams[stream_name]
            if cursor_field is not None:
                state.cursor_field = cursor_field
            if cursor_value is not None:
                state.cursor_value = cursor_value
            state.sync_mode = sync_mode
            state.last_synced_at = datetime.utcnow()
            state.records_synced += records_synced
            if metadata:
                state.metadata.update(metadata)
        else:
            state = StreamState(
                stream_name=stream_name,
                cursor_field=cursor_field,
                cursor_value=cursor_value,
                sync_mode=sync_mode,
                last_synced_at=datetime.utcnow(),
                records_synced=records_synced,
                metadata=metadata or {}
            )
            self.streams[stream_name] = state

        self.updated_at = datetime.utcnow()
        self.version += 1
        return state


class StateManager:
    """
    Manages state persistence for PyAirbyte connectors.

    Provides in-memory caching with optional file-based persistence.
    For production, extend to use PostgreSQL.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize state manager.

        Args:
            storage_path: Path for file-based persistence (optional)
        """
        self._states: Dict[str, SourceState] = {}
        self._storage_path = storage_path or Path("/tmp/atlas_airbyte_state")
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._load_persisted_states()

    def _load_persisted_states(self) -> None:
        """Load states from disk on startup."""
        try:
            for state_file in self._storage_path.glob("*.json"):
                with open(state_file, "r") as f:
                    data = json.load(f)
                    state = SourceState.from_dict(data)
                    self._states[state.source_id] = state
            logger.info(f"Loaded {len(self._states)} persisted states")
        except Exception as e:
            logger.warning(f"Failed to load persisted states: {e}")

    def _persist_state(self, source_id: str) -> None:
        """Persist a single source's state to disk."""
        if source_id not in self._states:
            return

        try:
            state = self._states[source_id]
            state_file = self._storage_path / f"{source_id}.json"
            with open(state_file, "w") as f:
                json.dump(state.to_dict(), f, indent=2)
            logger.debug(f"Persisted state for {source_id}")
        except Exception as e:
            logger.error(f"Failed to persist state for {source_id}: {e}")

    def get_state(self, source_id: str) -> Optional[SourceState]:
        """
        Get state for a source.

        Args:
            source_id: Unique identifier for the source

        Returns:
            SourceState if exists, None otherwise
        """
        return self._states.get(source_id)

    def create_state(
        self,
        source_name: str,
        source_id: str,
        streams: Optional[List[str]] = None,
        global_state: Optional[Dict[str, Any]] = None
    ) -> SourceState:
        """
        Create a new state for a source.

        Args:
            source_name: Name of the Airbyte source
            source_id: Unique identifier for this source instance
            streams: List of stream names to initialize
            global_state: Initial global state

        Returns:
            Created SourceState
        """
        state = SourceState(
            source_name=source_name,
            source_id=source_id,
            global_state=global_state or {}
        )

        if streams:
            for stream_name in streams:
                state.streams[stream_name] = StreamState(stream_name=stream_name)

        self._states[source_id] = state
        self._persist_state(source_id)

        logger.info(f"Created state for source {source_name} ({source_id})")
        return state

    def update_stream_state(
        self,
        source_id: str,
        stream_name: str,
        cursor_field: Optional[str] = None,
        cursor_value: Optional[Any] = None,
        sync_mode: str = "incremental",
        records_synced: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[StreamState]:
        """
        Update state for a specific stream.

        Args:
            source_id: Source identifier
            stream_name: Name of the stream
            cursor_field: Field used for incremental sync
            cursor_value: Current cursor value
            sync_mode: Sync mode (full_refresh or incremental)
            records_synced: Number of records synced in this batch
            metadata: Additional metadata

        Returns:
            Updated StreamState or None if source not found
        """
        state = self._states.get(source_id)
        if not state:
            logger.warning(f"Source {source_id} not found for state update")
            return None

        stream_state = state.set_stream_state(
            stream_name=stream_name,
            cursor_field=cursor_field,
            cursor_value=cursor_value,
            sync_mode=sync_mode,
            records_synced=records_synced,
            metadata=metadata
        )

        self._persist_state(source_id)
        return stream_state

    def get_cursor_value(
        self,
        source_id: str,
        stream_name: str
    ) -> Optional[Any]:
        """
        Get the current cursor value for incremental sync.

        Args:
            source_id: Source identifier
            stream_name: Stream name

        Returns:
            Cursor value or None
        """
        state = self._states.get(source_id)
        if not state:
            return None

        stream_state = state.get_stream_state(stream_name)
        if not stream_state:
            return None

        return stream_state.cursor_value

    def reset_stream_state(self, source_id: str, stream_name: str) -> bool:
        """
        Reset state for a specific stream (force full refresh).

        Args:
            source_id: Source identifier
            stream_name: Stream name

        Returns:
            True if reset successful, False otherwise
        """
        state = self._states.get(source_id)
        if not state:
            return False

        if stream_name in state.streams:
            state.streams[stream_name] = StreamState(
                stream_name=stream_name,
                sync_mode="full_refresh"
            )
            state.updated_at = datetime.utcnow()
            state.version += 1
            self._persist_state(source_id)
            logger.info(f"Reset state for stream {stream_name} in {source_id}")
            return True

        return False

    def reset_source_state(self, source_id: str) -> bool:
        """
        Reset all state for a source (force full refresh on all streams).

        Args:
            source_id: Source identifier

        Returns:
            True if reset successful, False otherwise
        """
        state = self._states.get(source_id)
        if not state:
            return False

        for stream_name in list(state.streams.keys()):
            state.streams[stream_name] = StreamState(
                stream_name=stream_name,
                sync_mode="full_refresh"
            )

        state.global_state = {}
        state.updated_at = datetime.utcnow()
        state.version += 1
        self._persist_state(source_id)

        logger.info(f"Reset all state for source {source_id}")
        return True

    def delete_state(self, source_id: str) -> bool:
        """
        Delete all state for a source.

        Args:
            source_id: Source identifier

        Returns:
            True if deleted, False if not found
        """
        if source_id not in self._states:
            return False

        del self._states[source_id]

        # Remove persisted file
        state_file = self._storage_path / f"{source_id}.json"
        if state_file.exists():
            state_file.unlink()

        logger.info(f"Deleted state for source {source_id}")
        return True

    def list_sources(self) -> List[Dict[str, Any]]:
        """
        List all sources with state.

        Returns:
            List of source summaries
        """
        return [
            {
                "source_id": source_id,
                "source_name": state.source_name,
                "stream_count": len(state.streams),
                "version": state.version,
                "created_at": state.created_at.isoformat(),
                "updated_at": state.updated_at.isoformat()
            }
            for source_id, state in self._states.items()
        ]

    def get_sync_summary(self, source_id: str) -> Optional[Dict[str, Any]]:
        """
        Get sync summary for a source.

        Args:
            source_id: Source identifier

        Returns:
            Sync summary or None if not found
        """
        state = self._states.get(source_id)
        if not state:
            return None

        total_records = sum(s.records_synced for s in state.streams.values())
        last_sync = max(
            (s.last_synced_at for s in state.streams.values() if s.last_synced_at),
            default=None
        )

        streams_summary = []
        for stream_name, stream_state in state.streams.items():
            streams_summary.append({
                "stream_name": stream_name,
                "sync_mode": stream_state.sync_mode,
                "cursor_field": stream_state.cursor_field,
                "cursor_value": stream_state.cursor_value,
                "records_synced": stream_state.records_synced,
                "last_synced_at": stream_state.last_synced_at.isoformat() if stream_state.last_synced_at else None
            })

        return {
            "source_id": source_id,
            "source_name": state.source_name,
            "total_streams": len(state.streams),
            "total_records_synced": total_records,
            "last_sync_at": last_sync.isoformat() if last_sync else None,
            "version": state.version,
            "streams": streams_summary
        }

    def export_state(self, source_id: str) -> Optional[Dict[str, Any]]:
        """
        Export complete state for backup/migration.

        Args:
            source_id: Source identifier

        Returns:
            Complete state dictionary or None
        """
        state = self._states.get(source_id)
        if not state:
            return None
        return state.to_dict()

    def import_state(self, state_data: Dict[str, Any]) -> SourceState:
        """
        Import state from backup/migration.

        Args:
            state_data: State dictionary

        Returns:
            Imported SourceState
        """
        state = SourceState.from_dict(state_data)
        self._states[state.source_id] = state
        self._persist_state(state.source_id)
        logger.info(f"Imported state for source {state.source_name} ({state.source_id})")
        return state


# Global state manager instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get or create global state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager
