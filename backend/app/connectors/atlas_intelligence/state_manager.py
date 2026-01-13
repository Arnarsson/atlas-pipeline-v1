"""
PyAirbyte State Manager - Persist sync state for incremental loads.

Manages state persistence for Airbyte connectors to enable incremental syncs.
State is stored in PostgreSQL for production use, with in-memory caching.
"""

import asyncpg
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

    Provides in-memory caching with PostgreSQL persistence for production.
    Falls back to file-based persistence if database is unavailable.
    """

    def __init__(self, database_url: Optional[str] = None, storage_path: Optional[Path] = None):
        """
        Initialize state manager.

        Args:
            database_url: PostgreSQL connection URL (preferred)
            storage_path: Path for file-based persistence fallback (optional)
        """
        self._states: Dict[str, SourceState] = {}
        self._database_url = database_url
        self._storage_path = storage_path or Path("/tmp/atlas_airbyte_state")
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._use_database = bool(database_url)

        # Initialize database table if using database
        if self._use_database:
            try:
                import asyncio
                asyncio.get_event_loop().run_until_complete(self._ensure_database_table())
                asyncio.get_event_loop().run_until_complete(self._load_persisted_states_from_db())
                logger.info(f"State manager using PostgreSQL persistence")
            except Exception as e:
                logger.warning(f"Failed to initialize database, falling back to file storage: {e}")
                self._use_database = False
                self._load_persisted_states_from_files()
        else:
            self._load_persisted_states_from_files()

    async def _ensure_database_table(self) -> None:
        """Ensure pipeline.connector_state table exists."""
        try:
            async with asyncpg.create_pool(self._database_url, min_size=1, max_size=3) as pool:
                async with pool.acquire() as conn:
                    await conn.execute("""
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
                            version INTEGER DEFAULT 1,
                            UNIQUE(source_id, stream_name)
                        )
                    """)

                    # Create indexes
                    await conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_connector_state_source
                        ON pipeline.connector_state(source_id)
                    """)

                    await conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_connector_state_stream
                        ON pipeline.connector_state(source_id, stream_name)
                    """)

                    logger.info("Ensured pipeline.connector_state table exists")
        except Exception as e:
            logger.error(f"Failed to create connector_state table: {e}")
            raise

    async def _load_persisted_states_from_db(self) -> None:
        """Load states from PostgreSQL on startup."""
        try:
            async with asyncpg.create_pool(self._database_url, min_size=1, max_size=3) as pool:
                async with pool.acquire() as conn:
                    # Load all source states
                    rows = await conn.fetch("""
                        SELECT DISTINCT source_id, source_name, state_data
                        FROM pipeline.connector_state
                        WHERE stream_name = '' OR stream_name IS NULL
                    """)

                    for row in rows:
                        try:
                            state_data = row['state_data']
                            if isinstance(state_data, str):
                                state_data = json.loads(state_data)

                            state = SourceState.from_dict(state_data)
                            self._states[state.source_id] = state
                        except Exception as e:
                            logger.warning(f"Failed to load state for {row['source_id']}: {e}")

                    logger.info(f"Loaded {len(self._states)} persisted states from database")
        except Exception as e:
            logger.warning(f"Failed to load persisted states from database: {e}")

    def _load_persisted_states_from_files(self) -> None:
        """Load states from disk (fallback mode)."""
        try:
            for state_file in self._storage_path.glob("*.json"):
                with open(state_file, "r") as f:
                    data = json.load(f)
                    state = SourceState.from_dict(data)
                    self._states[state.source_id] = state
            logger.info(f"Loaded {len(self._states)} persisted states from files")
        except Exception as e:
            logger.warning(f"Failed to load persisted states from files: {e}")

    async def _persist_state_to_db(self, source_id: str) -> None:
        """Persist a single source's state to PostgreSQL."""
        if source_id not in self._states:
            return

        try:
            state = self._states[source_id]
            async with asyncpg.create_pool(self._database_url, min_size=1, max_size=3) as pool:
                async with pool.acquire() as conn:
                    # Upsert source-level state
                    await conn.execute("""
                        INSERT INTO pipeline.connector_state
                        (source_id, source_name, stream_name, state_data, updated_at, version)
                        VALUES ($1, $2, '', $3, NOW(), $4)
                        ON CONFLICT (source_id, stream_name)
                        DO UPDATE SET
                            state_data = EXCLUDED.state_data,
                            updated_at = NOW(),
                            version = EXCLUDED.version
                    """,
                        state.source_id,
                        state.source_name,
                        json.dumps(state.to_dict()),
                        state.version
                    )

                    # Upsert each stream state
                    for stream_name, stream_state in state.streams.items():
                        await conn.execute("""
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
                        """,
                            state.source_id,
                            state.source_name,
                            stream_name,
                            stream_state.cursor_field,
                            str(stream_state.cursor_value) if stream_state.cursor_value else None,
                            stream_state.sync_mode,
                            json.dumps(stream_state.to_dict()),
                            stream_state.last_synced_at,
                            stream_state.records_synced
                        )

                    logger.debug(f"Persisted state for {source_id} to database")
        except Exception as e:
            logger.error(f"Failed to persist state to database for {source_id}: {e}")
            # Fallback to file persistence
            self._persist_state_to_file(source_id)

    def _persist_state_to_file(self, source_id: str) -> None:
        """Persist a single source's state to disk (fallback)."""
        if source_id not in self._states:
            return

        try:
            state = self._states[source_id]
            state_file = self._storage_path / f"{source_id}.json"
            with open(state_file, "w") as f:
                json.dump(state.to_dict(), f, indent=2)
            logger.debug(f"Persisted state for {source_id} to file")
        except Exception as e:
            logger.error(f"Failed to persist state to file for {source_id}: {e}")

    def _persist_state(self, source_id: str) -> None:
        """Persist state using configured method."""
        if self._use_database:
            # Run async persistence
            import asyncio
            try:
                asyncio.get_event_loop().run_until_complete(self._persist_state_to_db(source_id))
            except Exception as e:
                logger.warning(f"Database persistence failed, falling back to file: {e}")
                self._persist_state_to_file(source_id)
        else:
            self._persist_state_to_file(source_id)

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


def get_state_manager(database_url: Optional[str] = None) -> StateManager:
    """
    Get or create global state manager instance.

    Args:
        database_url: Optional PostgreSQL connection URL.
                     If not provided, attempts to load from settings.

    Returns:
        StateManager instance with PostgreSQL persistence (or file fallback)
    """
    global _state_manager
    if _state_manager is None:
        # Try to get database URL from settings if not provided
        if database_url is None:
            try:
                from app.core.config import settings
                database_url = settings.DATABASE_URL
            except Exception as e:
                logger.warning(f"Failed to load database URL from settings: {e}")

        _state_manager = StateManager(database_url=database_url)
    return _state_manager
