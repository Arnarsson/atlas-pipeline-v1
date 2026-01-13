"""
Data Storage Service (Phase 6)
==============================

Provides persistent storage for processed pipeline data.
Supports:
- In-memory storage (development)
- File-based storage (parquet/csv)
- Database storage (PostgreSQL) - future

This enables data profiling, re-processing, and data access APIs.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class StoredDataset:
    """Metadata for a stored dataset."""

    dataset_id: str
    run_id: str
    dataset_name: str
    filename: str
    row_count: int
    column_count: int
    columns: list[str]
    dtypes: dict[str, str]
    created_at: datetime
    storage_path: str | None = None
    size_bytes: int = 0


class DataStore:
    """
    Data storage service for Atlas pipeline.

    Stores processed DataFrames for:
    - Data profiling
    - Re-analysis
    - Export operations
    - GDPR data access
    """

    def __init__(
        self,
        storage_dir: str | None = None,
        max_memory_datasets: int = 100,
        persist_to_disk: bool = True,
    ):
        """
        Initialize data store.

        Args:
            storage_dir: Directory for file storage (default: /tmp/atlas_data)
            max_memory_datasets: Max datasets to keep in memory
            persist_to_disk: Whether to persist to disk (parquet)
        """
        self.storage_dir = Path(storage_dir or "/tmp/atlas_data")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.max_memory_datasets = max_memory_datasets
        self.persist_to_disk = persist_to_disk

        # In-memory storage
        self._datasets: dict[str, pd.DataFrame] = {}
        self._metadata: dict[str, StoredDataset] = {}

        # Index by run_id for quick lookup
        self._run_id_index: dict[str, str] = {}  # run_id -> dataset_id

        logger.info(
            f"Initialized DataStore: storage_dir={self.storage_dir}, "
            f"max_memory={max_memory_datasets}, persist={persist_to_disk}"
        )

    def store(
        self,
        run_id: str,
        dataset_name: str,
        filename: str,
        df: pd.DataFrame,
    ) -> StoredDataset:
        """
        Store a DataFrame.

        Args:
            run_id: Pipeline run ID
            dataset_name: Dataset name
            filename: Original filename
            df: DataFrame to store

        Returns:
            StoredDataset metadata
        """
        dataset_id = f"ds_{run_id}"

        # Create metadata
        metadata = StoredDataset(
            dataset_id=dataset_id,
            run_id=run_id,
            dataset_name=dataset_name,
            filename=filename,
            row_count=len(df),
            column_count=len(df.columns),
            columns=df.columns.tolist(),
            dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
            created_at=datetime.utcnow(),
            size_bytes=df.memory_usage(deep=True).sum(),
        )

        # Store in memory
        self._datasets[dataset_id] = df.copy()
        self._metadata[dataset_id] = metadata
        self._run_id_index[run_id] = dataset_id

        # Persist to disk if enabled
        if self.persist_to_disk:
            storage_path = self._persist_to_disk(dataset_id, df)
            metadata.storage_path = storage_path

        # Evict old datasets if over limit
        self._evict_if_needed()

        logger.info(
            f"Stored dataset: id={dataset_id}, name={dataset_name}, "
            f"rows={len(df)}, cols={len(df.columns)}"
        )

        return metadata

    def get(self, dataset_id: str) -> pd.DataFrame | None:
        """
        Get a DataFrame by dataset ID.

        Args:
            dataset_id: Dataset ID

        Returns:
            DataFrame or None if not found
        """
        # Try memory first
        if dataset_id in self._datasets:
            logger.debug(f"Retrieved dataset {dataset_id} from memory")
            return self._datasets[dataset_id].copy()

        # Try loading from disk
        metadata = self._metadata.get(dataset_id)
        if metadata and metadata.storage_path:
            df = self._load_from_disk(metadata.storage_path)
            if df is not None:
                # Re-cache in memory
                self._datasets[dataset_id] = df
                self._evict_if_needed()
                logger.debug(f"Retrieved dataset {dataset_id} from disk")
                return df.copy()

        logger.warning(f"Dataset {dataset_id} not found")
        return None

    def get_by_run_id(self, run_id: str) -> pd.DataFrame | None:
        """
        Get DataFrame by pipeline run ID.

        Args:
            run_id: Pipeline run ID

        Returns:
            DataFrame or None if not found
        """
        dataset_id = self._run_id_index.get(run_id)
        if dataset_id:
            return self.get(dataset_id)
        return None

    def get_metadata(self, dataset_id: str) -> StoredDataset | None:
        """
        Get metadata for a dataset.

        Args:
            dataset_id: Dataset ID

        Returns:
            StoredDataset or None
        """
        return self._metadata.get(dataset_id)

    def get_metadata_by_run_id(self, run_id: str) -> StoredDataset | None:
        """
        Get metadata by pipeline run ID.

        Args:
            run_id: Pipeline run ID

        Returns:
            StoredDataset or None
        """
        dataset_id = self._run_id_index.get(run_id)
        if dataset_id:
            return self._metadata.get(dataset_id)
        return None

    def list_datasets(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[StoredDataset]:
        """
        List stored datasets.

        Args:
            limit: Maximum number to return
            offset: Offset for pagination

        Returns:
            List of StoredDataset metadata
        """
        all_metadata = sorted(
            self._metadata.values(),
            key=lambda m: m.created_at,
            reverse=True,
        )
        return all_metadata[offset:offset + limit]

    def delete(self, dataset_id: str) -> bool:
        """
        Delete a stored dataset.

        Args:
            dataset_id: Dataset ID

        Returns:
            True if deleted, False if not found
        """
        if dataset_id not in self._metadata:
            return False

        # Remove from memory
        self._datasets.pop(dataset_id, None)
        metadata = self._metadata.pop(dataset_id)

        # Remove from index
        if metadata.run_id in self._run_id_index:
            del self._run_id_index[metadata.run_id]

        # Remove from disk
        if metadata.storage_path:
            self._delete_from_disk(metadata.storage_path)

        logger.info(f"Deleted dataset: {dataset_id}")
        return True

    def search(
        self,
        query: str | None = None,
        dataset_name: str | None = None,
    ) -> list[StoredDataset]:
        """
        Search datasets.

        Args:
            query: Search query (matches name, filename, columns)
            dataset_name: Exact dataset name match

        Returns:
            List of matching StoredDataset
        """
        results = []

        for metadata in self._metadata.values():
            # Exact name match
            if dataset_name and metadata.dataset_name != dataset_name:
                continue

            # Query search
            if query:
                query_lower = query.lower()
                searchable = (
                    metadata.dataset_name.lower() +
                    metadata.filename.lower() +
                    " ".join(metadata.columns).lower()
                )
                if query_lower not in searchable:
                    continue

            results.append(metadata)

        return sorted(results, key=lambda m: m.created_at, reverse=True)

    def _persist_to_disk(self, dataset_id: str, df: pd.DataFrame) -> str:
        """Persist DataFrame to disk as parquet."""
        try:
            storage_path = self.storage_dir / f"{dataset_id}.parquet"
            df.to_parquet(storage_path, index=False)
            logger.debug(f"Persisted dataset {dataset_id} to {storage_path}")
            return str(storage_path)
        except Exception as e:
            logger.warning(f"Failed to persist dataset {dataset_id}: {e}")
            return ""

    def _load_from_disk(self, storage_path: str) -> pd.DataFrame | None:
        """Load DataFrame from disk."""
        try:
            path = Path(storage_path)
            if path.exists():
                return pd.read_parquet(path)
        except Exception as e:
            logger.warning(f"Failed to load from {storage_path}: {e}")
        return None

    def _delete_from_disk(self, storage_path: str):
        """Delete file from disk."""
        try:
            path = Path(storage_path)
            if path.exists():
                path.unlink()
                logger.debug(f"Deleted file: {storage_path}")
        except Exception as e:
            logger.warning(f"Failed to delete {storage_path}: {e}")

    def _evict_if_needed(self):
        """Evict oldest datasets from memory if over limit."""
        if len(self._datasets) <= self.max_memory_datasets:
            return

        # Sort by created_at and evict oldest
        sorted_ids = sorted(
            self._datasets.keys(),
            key=lambda d: self._metadata[d].created_at,
        )

        to_evict = len(self._datasets) - self.max_memory_datasets
        for dataset_id in sorted_ids[:to_evict]:
            del self._datasets[dataset_id]
            logger.debug(f"Evicted dataset {dataset_id} from memory cache")


# Global singleton instance
_data_store: DataStore | None = None


def get_data_store() -> DataStore:
    """
    Get or create global data store instance.

    Returns:
        DataStore instance
    """
    global _data_store

    if _data_store is None:
        _data_store = DataStore()

    return _data_store


def store_pipeline_data(
    run_id: str,
    dataset_name: str,
    filename: str,
    df: pd.DataFrame,
) -> StoredDataset:
    """
    Convenience function to store pipeline data.

    Args:
        run_id: Pipeline run ID
        dataset_name: Dataset name
        filename: Original filename
        df: DataFrame to store

    Returns:
        StoredDataset metadata
    """
    store = get_data_store()
    return store.store(run_id, dataset_name, filename, df)


def get_pipeline_data(run_id: str) -> pd.DataFrame | None:
    """
    Convenience function to get pipeline data.

    Args:
        run_id: Pipeline run ID

    Returns:
        DataFrame or None
    """
    store = get_data_store()
    return store.get_by_run_id(run_id)
