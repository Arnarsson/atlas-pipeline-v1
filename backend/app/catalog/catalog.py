"""
Atlas Data Catalog
==================

Data catalog for dataset discovery, search, and metadata management.

Features:
- Dataset registry with metadata
- Full-text search across datasets, descriptions, columns
- Schema browser with data types
- Quality history tracking
- Lineage graph integration
- Tag-based categorization

Reference: Data catalog patterns (DataHub, Apache Atlas, Amundsen)
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


# ============================================================================
# Models
# ============================================================================


class DatasetNamespace(str, Enum):
    """Dataset namespace (layer)."""

    EXPLORE = "explore"
    CHART = "chart"
    NAVIGATE = "navigate"
    FEATURES = "features"


@dataclass
class ColumnMetadata:
    """Column metadata."""

    column_id: str
    dataset_id: str
    column_name: str
    data_type: str
    nullable: bool
    pii_type: str | None = None
    description: str | None = None
    sample_values: list[str] | None = None


@dataclass
class DatasetMetadata:
    """Dataset metadata."""

    dataset_id: str
    namespace: DatasetNamespace
    name: str
    description: str
    schema_definition: dict[str, Any]
    tags: list[str]
    owner: str
    created_at: datetime
    last_updated: datetime
    row_count_estimate: int
    size_bytes: int
    columns: list[ColumnMetadata] | None = None


@dataclass
class Tag:
    """Tag for categorizing datasets."""

    tag_id: str
    tag_name: str
    color: str
    description: str | None = None


@dataclass
class QualityHistory:
    """Quality history for a dataset."""

    history_id: str
    dataset_id: str
    timestamp: datetime
    completeness_score: float
    validity_score: float
    consistency_score: float
    overall_score: float


# ============================================================================
# Data Catalog
# ============================================================================


class DataCatalog:
    """
    Data catalog for dataset discovery and metadata management.

    Handles:
    - Dataset registration
    - Full-text search
    - Schema browsing
    - Quality history
    - Tag management
    - Lineage integration
    """

    def __init__(self):
        """Initialize data catalog (in-memory for Week 5-6)."""
        # In-memory storage (Week 5-6 simple version)
        # Week 7+ will add database persistence
        self.datasets: dict[str, DatasetMetadata] = {}
        self.tags: dict[str, Tag] = {}
        self.quality_history: dict[str, list[QualityHistory]] = {}

        # Create default tags
        self._create_default_tags()

        logger.info("Initialized DataCatalog (in-memory mode)")

    def _create_default_tags(self):
        """Create default tags for categorization."""
        default_tags = [
            Tag(
                tag_id=str(uuid4()),
                tag_name="finance",
                color="#10B981",
                description="Financial data and transactions",
            ),
            Tag(
                tag_id=str(uuid4()),
                tag_name="marketing",
                color="#F59E0B",
                description="Marketing and customer engagement data",
            ),
            Tag(
                tag_id=str(uuid4()),
                tag_name="pii",
                color="#EF4444",
                description="Contains personally identifiable information",
            ),
            Tag(
                tag_id=str(uuid4()),
                tag_name="gdpr",
                color="#DC2626",
                description="GDPR-regulated data",
            ),
            Tag(
                tag_id=str(uuid4()),
                tag_name="production",
                color="#3B82F6",
                description="Production-ready data",
            ),
            Tag(
                tag_id=str(uuid4()),
                tag_name="deprecated",
                color="#6B7280",
                description="Deprecated dataset",
            ),
        ]

        for tag in default_tags:
            self.tags[tag.tag_name] = tag

    def register_dataset(
        self,
        namespace: DatasetNamespace,
        name: str,
        description: str,
        schema_definition: dict[str, Any],
        owner: str = "system",
        tags: list[str] | None = None,
        row_count: int = 0,
        size_bytes: int = 0,
    ) -> DatasetMetadata:
        """
        Register a dataset in the catalog.

        Args:
            namespace: Dataset namespace (explore, chart, navigate)
            name: Dataset name (e.g., "raw_data", "validated_customers")
            description: Human-readable description
            schema_definition: Schema definition (columns, types)
            owner: Dataset owner
            tags: Optional tags for categorization
            row_count: Estimated row count
            size_bytes: Estimated size in bytes

        Returns:
            DatasetMetadata for the registered dataset
        """
        dataset_id = str(uuid4())

        # Extract columns from schema
        columns = []
        for field in schema_definition.get("fields", []):
            column = ColumnMetadata(
                column_id=str(uuid4()),
                dataset_id=dataset_id,
                column_name=field["name"],
                data_type=field["type"],
                nullable=field.get("nullable", True),
                pii_type=field.get("pii_type"),
                description=field.get("description"),
                sample_values=field.get("sample_values"),
            )
            columns.append(column)

        dataset = DatasetMetadata(
            dataset_id=dataset_id,
            namespace=namespace,
            name=name,
            description=description,
            schema_definition=schema_definition,
            tags=tags or [],
            owner=owner,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            row_count_estimate=row_count,
            size_bytes=size_bytes,
            columns=columns,
        )

        # Store dataset
        dataset_key = f"{namespace}.{name}"
        self.datasets[dataset_key] = dataset

        logger.info(
            f"Registered dataset: {dataset_key}, "
            f"columns={len(columns)}, rows={row_count}"
        )

        return dataset

    def get_dataset(self, namespace: DatasetNamespace, name: str) -> DatasetMetadata | None:
        """
        Get dataset by namespace and name.

        Args:
            namespace: Dataset namespace
            name: Dataset name

        Returns:
            DatasetMetadata or None if not found
        """
        dataset_key = f"{namespace}.{name}"
        return self.datasets.get(dataset_key)

    def get_dataset_by_id(self, dataset_id: str) -> DatasetMetadata | None:
        """
        Get dataset by ID.

        Args:
            dataset_id: Dataset ID

        Returns:
            DatasetMetadata or None if not found
        """
        for dataset in self.datasets.values():
            if dataset.dataset_id == dataset_id:
                return dataset
        return None

    def search_datasets(
        self,
        query: str | None = None,
        namespace: DatasetNamespace | None = None,
        tags: list[str] | None = None,
        owner: str | None = None,
    ) -> list[DatasetMetadata]:
        """
        Search datasets with optional filters.

        Args:
            query: Full-text search query (searches name, description, columns)
            namespace: Optional filter by namespace
            tags: Optional filter by tags
            owner: Optional filter by owner

        Returns:
            List of matching DatasetMetadata
        """
        results = list(self.datasets.values())

        # Filter by namespace
        if namespace:
            results = [d for d in results if d.namespace == namespace]

        # Filter by tags
        if tags:
            results = [
                d for d in results if any(tag in d.tags for tag in tags)
            ]

        # Filter by owner
        if owner:
            results = [d for d in results if d.owner == owner]

        # Full-text search
        if query:
            query_lower = query.lower()
            filtered_results = []

            for dataset in results:
                # Search in name
                if query_lower in dataset.name.lower():
                    filtered_results.append(dataset)
                    continue

                # Search in description
                if query_lower in dataset.description.lower():
                    filtered_results.append(dataset)
                    continue

                # Search in column names
                if dataset.columns:
                    for col in dataset.columns:
                        if query_lower in col.column_name.lower():
                            filtered_results.append(dataset)
                            break

            results = filtered_results

        logger.info(
            f"Search results: query='{query}', namespace={namespace}, "
            f"tags={tags}, found={len(results)}"
        )

        return sorted(results, key=lambda d: d.last_updated, reverse=True)

    def add_tags_to_dataset(
        self, namespace: DatasetNamespace, name: str, tags: list[str]
    ):
        """
        Add tags to a dataset.

        Args:
            namespace: Dataset namespace
            name: Dataset name
            tags: Tags to add
        """
        dataset_key = f"{namespace}.{name}"
        dataset = self.datasets.get(dataset_key)

        if not dataset:
            raise ValueError(f"Dataset {dataset_key} not found")

        for tag in tags:
            if tag not in dataset.tags:
                dataset.tags.append(tag)

        dataset.last_updated = datetime.utcnow()

        logger.info(f"Added tags to {dataset_key}: {tags}")

    def remove_tags_from_dataset(
        self, namespace: DatasetNamespace, name: str, tags: list[str]
    ):
        """
        Remove tags from a dataset.

        Args:
            namespace: Dataset namespace
            name: Dataset name
            tags: Tags to remove
        """
        dataset_key = f"{namespace}.{name}"
        dataset = self.datasets.get(dataset_key)

        if not dataset:
            raise ValueError(f"Dataset {dataset_key} not found")

        dataset.tags = [t for t in dataset.tags if t not in tags]
        dataset.last_updated = datetime.utcnow()

        logger.info(f"Removed tags from {dataset_key}: {tags}")

    def create_tag(
        self, tag_name: str, color: str, description: str | None = None
    ) -> Tag:
        """
        Create a new tag.

        Args:
            tag_name: Tag name (lowercase, no spaces)
            color: Hex color code (e.g., "#FF0000")
            description: Optional description

        Returns:
            Tag instance
        """
        if tag_name in self.tags:
            raise ValueError(f"Tag {tag_name} already exists")

        tag = Tag(
            tag_id=str(uuid4()),
            tag_name=tag_name.lower(),
            color=color,
            description=description,
        )

        self.tags[tag_name] = tag

        logger.info(f"Created tag: {tag_name}, color={color}")

        return tag

    def list_tags(self) -> list[Tag]:
        """
        List all tags.

        Returns:
            List of Tag
        """
        return list(self.tags.values())

    def add_quality_history(
        self,
        dataset_id: str,
        completeness_score: float,
        validity_score: float,
        consistency_score: float,
    ):
        """
        Add quality history for a dataset.

        Args:
            dataset_id: Dataset ID
            completeness_score: Completeness score (0.0 to 1.0)
            validity_score: Validity score (0.0 to 1.0)
            consistency_score: Consistency score (0.0 to 1.0)
        """
        overall_score = (
            completeness_score + validity_score + consistency_score
        ) / 3.0

        history_entry = QualityHistory(
            history_id=str(uuid4()),
            dataset_id=dataset_id,
            timestamp=datetime.utcnow(),
            completeness_score=completeness_score,
            validity_score=validity_score,
            consistency_score=consistency_score,
            overall_score=overall_score,
        )

        if dataset_id not in self.quality_history:
            self.quality_history[dataset_id] = []

        self.quality_history[dataset_id].append(history_entry)

        # Keep only last 100 entries per dataset
        if len(self.quality_history[dataset_id]) > 100:
            self.quality_history[dataset_id] = self.quality_history[dataset_id][-100:]

        logger.info(
            f"Added quality history for dataset {dataset_id}, "
            f"overall_score={overall_score:.3f}"
        )

    def get_quality_history(
        self, dataset_id: str, limit: int = 10
    ) -> list[QualityHistory]:
        """
        Get quality history for a dataset.

        Args:
            dataset_id: Dataset ID
            limit: Maximum number of entries to return

        Returns:
            List of QualityHistory, sorted by timestamp descending
        """
        history = self.quality_history.get(dataset_id, [])
        return sorted(history, key=lambda h: h.timestamp, reverse=True)[:limit]

    def get_dataset_lineage(self, dataset_id: str) -> dict[str, Any] | None:
        """
        Get lineage graph for a dataset.

        Integration with OpenLineage/Marquez.

        Args:
            dataset_id: Dataset ID

        Returns:
            Lineage graph dict or None if not available
        """
        # This would integrate with OpenLineage client
        # For now, return placeholder

        dataset = self.get_dataset_by_id(dataset_id)
        if not dataset:
            return None

        lineage = {
            "dataset": {
                "id": dataset.dataset_id,
                "namespace": dataset.namespace,
                "name": dataset.name,
            },
            "upstream": [],
            "downstream": [],
            "jobs": [],
        }

        logger.info(f"Retrieved lineage for dataset {dataset_id}")

        return lineage

    def update_dataset_stats(
        self,
        namespace: DatasetNamespace,
        name: str,
        row_count: int | None = None,
        size_bytes: int | None = None,
    ):
        """
        Update dataset statistics.

        Args:
            namespace: Dataset namespace
            name: Dataset name
            row_count: Optional new row count
            size_bytes: Optional new size in bytes
        """
        dataset_key = f"{namespace}.{name}"
        dataset = self.datasets.get(dataset_key)

        if not dataset:
            raise ValueError(f"Dataset {dataset_key} not found")

        if row_count is not None:
            dataset.row_count_estimate = row_count

        if size_bytes is not None:
            dataset.size_bytes = size_bytes

        dataset.last_updated = datetime.utcnow()

        logger.info(
            f"Updated stats for {dataset_key}: "
            f"rows={row_count}, size={size_bytes}"
        )

    def get_datasets_by_namespace(
        self, namespace: DatasetNamespace
    ) -> list[DatasetMetadata]:
        """
        Get all datasets in a namespace.

        Args:
            namespace: Dataset namespace

        Returns:
            List of DatasetMetadata
        """
        datasets = [d for d in self.datasets.values() if d.namespace == namespace]
        return sorted(datasets, key=lambda d: d.name)

    def get_catalog_stats(self) -> dict[str, Any]:
        """
        Get catalog statistics.

        Returns:
            Dictionary with catalog statistics
        """
        total_datasets = len(self.datasets)
        namespace_counts = {}

        for dataset in self.datasets.values():
            namespace = dataset.namespace
            namespace_counts[namespace] = namespace_counts.get(namespace, 0) + 1

        total_size = sum(d.size_bytes for d in self.datasets.values())
        total_rows = sum(d.row_count_estimate for d in self.datasets.values())

        stats = {
            "total_datasets": total_datasets,
            "datasets_by_namespace": namespace_counts,
            "total_size_bytes": total_size,
            "total_rows": total_rows,
            "total_tags": len(self.tags),
        }

        logger.info(f"Catalog stats: {total_datasets} datasets, {total_rows} rows")

        return stats


# ============================================================================
# Singleton Instance
# ============================================================================

_data_catalog: DataCatalog | None = None


def get_data_catalog() -> DataCatalog:
    """
    Get or create global data catalog instance.

    Returns:
        DataCatalog instance
    """
    global _data_catalog

    if _data_catalog is None:
        _data_catalog = DataCatalog()

    return _data_catalog
