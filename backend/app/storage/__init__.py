"""
Storage module for Atlas Data Pipeline.

Provides data persistence for processed pipeline data.
"""

from .data_store import (
    DataStore,
    StoredDataset,
    get_data_store,
    get_pipeline_data,
    store_pipeline_data,
)

__all__ = [
    "DataStore",
    "StoredDataset",
    "get_data_store",
    "get_pipeline_data",
    "store_pipeline_data",
]
