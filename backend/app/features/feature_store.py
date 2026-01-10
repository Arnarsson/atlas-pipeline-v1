"""
Atlas Feature Store
===================

Feature store for ML/AI teams to discover, version, and consume features.

Features:
- Feature group registration and versioning (semantic versioning)
- Schema tracking and evolution
- Quality metrics integration
- Export formats (Parquet, CSV, TFRecord, JSON)
- Lineage tracking integration
- Feature metadata and statistics

Reference: Standard feature store patterns (Feast, Tecton, Hopsworks)
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

import pandas as pd

logger = logging.getLogger(__name__)


# ============================================================================
# Models
# ============================================================================


class ExportFormat(str, Enum):
    """Supported export formats for features."""

    PARQUET = "parquet"
    CSV = "csv"
    JSON = "json"
    TFRECORD = "tfrecord"


@dataclass
class FeatureGroupMetadata:
    """Metadata for a feature group."""

    feature_group_id: str
    name: str
    description: str
    version: str
    schema_definition: dict[str, Any]
    created_at: datetime
    created_by: str
    tags: list[str] | None = None


@dataclass
class FeatureVersion:
    """Version information for a feature group."""

    version_id: str
    feature_group_id: str
    version: str
    dataset_location: str
    row_count: int
    quality_score: float
    created_at: datetime
    is_latest: bool


@dataclass
class FeatureMetadata:
    """Metadata for individual features."""

    feature_id: str
    feature_group_id: str
    feature_name: str
    data_type: str
    importance_score: float | None = None
    null_percentage: float | None = None
    unique_percentage: float | None = None
    description: str | None = None


# ============================================================================
# Feature Store
# ============================================================================


class FeatureStore:
    """
    Feature store for ML/AI feature management.

    Handles:
    - Feature group registration
    - Semantic versioning (major.minor.patch)
    - Schema tracking
    - Quality metrics
    - Export to multiple formats
    """

    def __init__(self):
        """Initialize feature store (in-memory for Week 5-6)."""
        # In-memory storage (Week 5-6 simple version)
        # Week 7+ will add database persistence
        self.feature_groups: dict[str, FeatureGroupMetadata] = {}
        self.feature_versions: dict[str, list[FeatureVersion]] = {}
        self.feature_metadata: dict[str, list[FeatureMetadata]] = {}

        logger.info("Initialized FeatureStore (in-memory mode)")

    def register_feature_group(
        self,
        name: str,
        description: str,
        df: pd.DataFrame,
        version: str = "1.0.0",
        created_by: str = "system",
        tags: list[str] | None = None,
    ) -> FeatureGroupMetadata:
        """
        Register a new feature group or new version.

        Args:
            name: Unique feature group name (e.g., "customer_demographics")
            description: Human-readable description
            df: DataFrame containing features
            version: Semantic version (major.minor.patch)
            created_by: User or system that created it
            tags: Optional tags for categorization

        Returns:
            FeatureGroupMetadata for the registered group
        """
        logger.info(f"Registering feature group: {name}, version: {version}")

        # Generate schema from DataFrame
        schema_definition = {
            "fields": [
                {
                    "name": col,
                    "type": str(df[col].dtype),
                    "nullable": bool(df[col].isnull().any()),
                }
                for col in df.columns
            ]
        }

        # Check if feature group exists
        if name in self.feature_groups:
            feature_group = self.feature_groups[name]
            logger.info(f"Feature group {name} already exists, adding new version")
        else:
            # Create new feature group
            feature_group_id = str(uuid4())
            feature_group = FeatureGroupMetadata(
                feature_group_id=feature_group_id,
                name=name,
                description=description,
                version=version,
                schema_definition=schema_definition,
                created_at=datetime.utcnow(),
                created_by=created_by,
                tags=tags or [],
            )
            self.feature_groups[name] = feature_group
            self.feature_versions[name] = []
            self.feature_metadata[name] = []

        # Add version
        version_id = str(uuid4())
        dataset_location = f"s3://atlas-features/{name}/{version}/data.parquet"

        # Mark all existing versions as not latest
        for existing_version in self.feature_versions[name]:
            existing_version.is_latest = False

        new_version = FeatureVersion(
            version_id=version_id,
            feature_group_id=feature_group.feature_group_id,
            version=version,
            dataset_location=dataset_location,
            row_count=len(df),
            quality_score=self._calculate_quality_score(df),
            created_at=datetime.utcnow(),
            is_latest=True,
        )
        self.feature_versions[name].append(new_version)

        # Extract feature metadata
        self._extract_feature_metadata(name, feature_group.feature_group_id, df)

        logger.info(
            f"Registered feature group {name} v{version}, "
            f"{len(df)} rows, {len(df.columns)} features"
        )

        return feature_group

    def get_feature_group(self, name: str) -> FeatureGroupMetadata | None:
        """
        Get feature group metadata by name.

        Args:
            name: Feature group name

        Returns:
            FeatureGroupMetadata or None if not found
        """
        return self.feature_groups.get(name)

    def list_feature_groups(
        self, tags: list[str] | None = None
    ) -> list[FeatureGroupMetadata]:
        """
        List all feature groups, optionally filtered by tags.

        Args:
            tags: Optional tags to filter by

        Returns:
            List of FeatureGroupMetadata
        """
        groups = list(self.feature_groups.values())

        if tags:
            groups = [
                g
                for g in groups
                if g.tags and any(tag in g.tags for tag in tags)
            ]

        logger.info(f"Listing {len(groups)} feature groups")
        return groups

    def get_versions(self, name: str) -> list[FeatureVersion]:
        """
        Get all versions for a feature group.

        Args:
            name: Feature group name

        Returns:
            List of FeatureVersion, sorted by created_at descending
        """
        versions = self.feature_versions.get(name, [])
        return sorted(versions, key=lambda v: v.created_at, reverse=True)

    def get_latest_version(self, name: str) -> FeatureVersion | None:
        """
        Get latest version for a feature group.

        Args:
            name: Feature group name

        Returns:
            FeatureVersion or None if not found
        """
        versions = self.get_versions(name)
        for version in versions:
            if version.is_latest:
                return version
        return versions[0] if versions else None

    def get_feature_metadata(self, name: str) -> list[FeatureMetadata]:
        """
        Get metadata for all features in a feature group.

        Args:
            name: Feature group name

        Returns:
            List of FeatureMetadata
        """
        return self.feature_metadata.get(name, [])

    def export_features(
        self,
        name: str,
        format: ExportFormat,
        version: str | None = None,
    ) -> dict[str, Any]:
        """
        Export features in specified format.

        Args:
            name: Feature group name
            format: Export format (parquet, csv, json, tfrecord)
            version: Optional specific version (default: latest)

        Returns:
            Export result with location and metadata
        """
        logger.info(f"Exporting feature group {name} as {format}")

        # Get version
        if version:
            versions = [v for v in self.get_versions(name) if v.version == version]
            if not versions:
                raise ValueError(f"Version {version} not found for {name}")
            feature_version = versions[0]
        else:
            feature_version = self.get_latest_version(name)
            if not feature_version:
                raise ValueError(f"No versions found for feature group {name}")

        # Generate export location
        export_location = f"s3://atlas-exports/{name}/{feature_version.version}/{format}"

        # In production, this would:
        # 1. Load data from dataset_location
        # 2. Convert to requested format
        # 3. Upload to export_location
        # 4. Return download URL/path

        result = {
            "feature_group": name,
            "version": feature_version.version,
            "format": format,
            "export_location": export_location,
            "row_count": feature_version.row_count,
            "exported_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Export complete: {export_location}")
        return result

    def _calculate_quality_score(self, df: pd.DataFrame) -> float:
        """
        Calculate overall quality score for features.

        Factors:
        - Completeness (non-null percentage)
        - Validity (no invalid values)
        - Consistency (reasonable distributions)

        Args:
            df: DataFrame to analyze

        Returns:
            Quality score (0.0 to 1.0)
        """
        # Completeness score
        non_null_pct = (
            df.notna().sum().sum() / (len(df) * len(df.columns))
        )

        # Validity score (all numeric columns have finite values)
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) > 0:
            finite_pct = (
                df[numeric_cols].apply(lambda x: x.notna() & pd.isfinite(x)).sum().sum()
                / (len(df) * len(numeric_cols))
            )
        else:
            finite_pct = 1.0

        # Overall quality (simple average for now)
        quality_score = (non_null_pct + finite_pct) / 2.0

        return round(quality_score, 3)

    def _extract_feature_metadata(
        self, name: str, feature_group_id: str, df: pd.DataFrame
    ):
        """
        Extract metadata for each feature in the DataFrame.

        Args:
            name: Feature group name
            feature_group_id: Feature group ID
            df: DataFrame containing features
        """
        metadata_list = []

        for col in df.columns:
            null_pct = df[col].isnull().sum() / len(df) if len(df) > 0 else 0.0
            unique_pct = (
                df[col].nunique() / len(df) if len(df) > 0 else 0.0
            )

            metadata = FeatureMetadata(
                feature_id=str(uuid4()),
                feature_group_id=feature_group_id,
                feature_name=col,
                data_type=str(df[col].dtype),
                importance_score=None,  # Would be calculated from model training
                null_percentage=round(null_pct, 3),
                unique_percentage=round(unique_pct, 3),
                description=None,  # Could be added via API
            )
            metadata_list.append(metadata)

        self.feature_metadata[name] = metadata_list

    def add_tags(self, name: str, tags: list[str]):
        """
        Add tags to a feature group.

        Args:
            name: Feature group name
            tags: Tags to add
        """
        feature_group = self.feature_groups.get(name)
        if not feature_group:
            raise ValueError(f"Feature group {name} not found")

        if not feature_group.tags:
            feature_group.tags = []

        feature_group.tags.extend([t for t in tags if t not in feature_group.tags])
        logger.info(f"Added tags to {name}: {tags}")

    def remove_tags(self, name: str, tags: list[str]):
        """
        Remove tags from a feature group.

        Args:
            name: Feature group name
            tags: Tags to remove
        """
        feature_group = self.feature_groups.get(name)
        if not feature_group:
            raise ValueError(f"Feature group {name} not found")

        if feature_group.tags:
            feature_group.tags = [t for t in feature_group.tags if t not in tags]
            logger.info(f"Removed tags from {name}: {tags}")


# ============================================================================
# Singleton Instance
# ============================================================================

_feature_store: FeatureStore | None = None


def get_feature_store() -> FeatureStore:
    """
    Get or create global feature store instance.

    Returns:
        FeatureStore instance
    """
    global _feature_store

    if _feature_store is None:
        _feature_store = FeatureStore()

    return _feature_store
