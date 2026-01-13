"""
Tests for Data Store (Phase 6)
==============================

Tests data storage functionality for profiling.
"""

import pandas as pd
import pytest

from app.storage.data_store import DataStore, get_data_store, store_pipeline_data


class TestDataStore:
    """Test cases for DataStore."""

    def setup_method(self):
        """Set up test fixtures."""
        self.store = DataStore(
            storage_dir="/tmp/atlas_test_data",
            max_memory_datasets=10,
            persist_to_disk=False,  # Don't persist for tests
        )

    def test_store_and_retrieve(self):
        """Test storing and retrieving a DataFrame."""
        # Create test data
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "value": [10.5, 20.5, 30.5],
        })

        # Store
        metadata = self.store.store(
            run_id="test-run-001",
            dataset_name="test_dataset",
            filename="test.csv",
            df=df,
        )

        # Verify metadata
        assert metadata.dataset_id == "ds_test-run-001"
        assert metadata.run_id == "test-run-001"
        assert metadata.dataset_name == "test_dataset"
        assert metadata.row_count == 3
        assert metadata.column_count == 3
        assert set(metadata.columns) == {"id", "name", "value"}

        # Retrieve by dataset_id
        retrieved = self.store.get("ds_test-run-001")
        assert retrieved is not None
        assert len(retrieved) == 3
        assert list(retrieved.columns) == ["id", "name", "value"]

        # Retrieve by run_id
        retrieved2 = self.store.get_by_run_id("test-run-001")
        assert retrieved2 is not None
        pd.testing.assert_frame_equal(retrieved, retrieved2)

    def test_get_metadata(self):
        """Test getting metadata without data."""
        df = pd.DataFrame({"x": [1, 2, 3]})

        self.store.store(
            run_id="meta-test",
            dataset_name="meta_dataset",
            filename="meta.csv",
            df=df,
        )

        metadata = self.store.get_metadata("ds_meta-test")
        assert metadata is not None
        assert metadata.dataset_name == "meta_dataset"

        metadata2 = self.store.get_metadata_by_run_id("meta-test")
        assert metadata2 is not None
        assert metadata2.dataset_id == metadata.dataset_id

    def test_list_datasets(self):
        """Test listing stored datasets."""
        # Store multiple datasets
        for i in range(5):
            df = pd.DataFrame({"value": [i]})
            self.store.store(
                run_id=f"list-test-{i}",
                dataset_name=f"dataset_{i}",
                filename=f"file_{i}.csv",
                df=df,
            )

        datasets = self.store.list_datasets(limit=10)
        assert len(datasets) == 5

        # Test limit
        datasets_limited = self.store.list_datasets(limit=3)
        assert len(datasets_limited) == 3

    def test_delete_dataset(self):
        """Test deleting a dataset."""
        df = pd.DataFrame({"x": [1]})

        self.store.store(
            run_id="delete-test",
            dataset_name="delete_me",
            filename="delete.csv",
            df=df,
        )

        # Verify exists
        assert self.store.get("ds_delete-test") is not None

        # Delete
        result = self.store.delete("ds_delete-test")
        assert result is True

        # Verify deleted
        assert self.store.get("ds_delete-test") is None

        # Delete non-existent
        result = self.store.delete("ds_non-existent")
        assert result is False

    def test_search_datasets(self):
        """Test searching datasets."""
        df1 = pd.DataFrame({"user_id": [1], "user_name": ["test"]})
        df2 = pd.DataFrame({"product_id": [1], "price": [9.99]})

        self.store.store("search-1", "user_data", "users.csv", df1)
        self.store.store("search-2", "product_data", "products.csv", df2)

        # Search by query
        results = self.store.search(query="user")
        assert len(results) == 1
        assert results[0].dataset_name == "user_data"

        # Search by dataset name
        results = self.store.search(dataset_name="product_data")
        assert len(results) == 1
        assert results[0].dataset_name == "product_data"

    def test_memory_eviction(self):
        """Test that old datasets are evicted from memory."""
        # Create store with small memory limit
        small_store = DataStore(
            max_memory_datasets=3,
            persist_to_disk=False,
        )

        # Store 5 datasets
        for i in range(5):
            df = pd.DataFrame({"x": [i]})
            small_store.store(
                run_id=f"evict-{i}",
                dataset_name=f"evict_{i}",
                filename=f"evict_{i}.csv",
                df=df,
            )

        # Should only have 3 in memory
        assert len(small_store._datasets) <= 3

    def test_data_types_preserved(self):
        """Test that data types are preserved."""
        df = pd.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.1, 2.2, 3.3],
            "str_col": ["a", "b", "c"],
            "bool_col": [True, False, True],
        })

        self.store.store("types-test", "types_dataset", "types.csv", df)

        retrieved = self.store.get("ds_types-test")
        assert retrieved is not None

        assert retrieved["int_col"].dtype == df["int_col"].dtype
        assert retrieved["float_col"].dtype == df["float_col"].dtype
        assert retrieved["str_col"].dtype == df["str_col"].dtype
        assert retrieved["bool_col"].dtype == df["bool_col"].dtype


class TestDataStoreSingleton:
    """Test singleton pattern."""

    def test_get_data_store_returns_same_instance(self):
        """Test that get_data_store returns same instance."""
        store1 = get_data_store()
        store2 = get_data_store()
        assert store1 is store2


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_store_pipeline_data(self):
        """Test store_pipeline_data function."""
        df = pd.DataFrame({"test": [1, 2, 3]})

        metadata = store_pipeline_data(
            run_id="convenience-test",
            dataset_name="convenience_dataset",
            filename="convenience.csv",
            df=df,
        )

        assert metadata is not None
        assert metadata.run_id == "convenience-test"
