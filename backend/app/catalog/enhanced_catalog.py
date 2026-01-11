"""
Enhanced Data Catalog (Phase 4.1)
==================================

Advanced data catalog features:
- Smart search with relevance ranking (TF-IDF)
- Usage analytics and access tracking
- Statistical data profiling
- Collaboration features (comments, ratings, annotations)
- Interactive lineage visualization support

Reference: DataHub, Apache Atlas, Amundsen patterns
"""

import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

import numpy as np
import pandas as pd

from .catalog import (
    DataCatalog,
    DatasetMetadata,
    DatasetNamespace,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Enhanced Models
# ============================================================================


@dataclass
class DatasetComment:
    """User comment on a dataset."""

    comment_id: str
    dataset_id: str
    user_id: str
    user_name: str
    comment_text: str
    created_at: datetime
    updated_at: datetime | None = None


@dataclass
class DatasetRating:
    """User rating for a dataset."""

    rating_id: str
    dataset_id: str
    user_id: str
    user_name: str
    rating: int  # 1-5 stars
    review_text: str | None = None
    created_at: datetime


@dataclass
class DatasetAnnotation:
    """Annotation on a dataset or column."""

    annotation_id: str
    dataset_id: str
    column_name: str | None  # None means dataset-level annotation
    annotation_type: str  # "note", "warning", "deprecated", "recommendation"
    annotation_text: str
    created_by: str
    created_at: datetime


@dataclass
class UsageStatistics:
    """Usage statistics for a dataset."""

    dataset_id: str
    access_count: int = 0
    unique_users: set[str] = field(default_factory=set)
    last_accessed: datetime | None = None
    access_history: list[dict[str, Any]] = field(default_factory=list)

    def record_access(self, user_id: str):
        """Record a dataset access."""
        self.access_count += 1
        self.unique_users.add(user_id)
        self.last_accessed = datetime.utcnow()
        self.access_history.append({
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Keep only last 1000 accesses
        if len(self.access_history) > 1000:
            self.access_history = self.access_history[-1000:]


@dataclass
class ColumnProfile:
    """Statistical profile for a column."""

    column_name: str
    data_type: str

    # Basic statistics
    total_count: int = 0
    null_count: int = 0
    null_percentage: float = 0.0
    unique_count: int = 0
    cardinality: float = 0.0  # unique_count / total_count

    # Numerical statistics
    min_value: float | None = None
    max_value: float | None = None
    mean_value: float | None = None
    median_value: float | None = None
    std_dev: float | None = None
    percentile_25: float | None = None
    percentile_75: float | None = None

    # String statistics
    min_length: int | None = None
    max_length: int | None = None
    avg_length: float | None = None

    # Frequency distribution (top 10 values)
    top_values: list[tuple[Any, int]] = field(default_factory=list)

    # Histogram data
    histogram: dict[str, Any] | None = None


@dataclass
class DatasetProfile:
    """Complete statistical profile for a dataset."""

    dataset_id: str
    profiled_at: datetime
    total_rows: int
    total_columns: int
    column_profiles: list[ColumnProfile]

    # Dataset-level metrics
    completeness_score: float  # Average non-null percentage across columns
    memory_usage_bytes: int
    profile_duration_seconds: float


@dataclass
class SearchResult:
    """Search result with relevance score."""

    dataset: DatasetMetadata
    relevance_score: float
    matched_fields: list[str]  # Which fields matched the search
    highlighted_snippets: dict[str, str]  # Field -> highlighted text


# ============================================================================
# Enhanced Data Catalog
# ============================================================================


class EnhancedDataCatalog(DataCatalog):
    """
    Enhanced data catalog with advanced features.

    New features:
    - Smart search with TF-IDF relevance ranking
    - Usage analytics and tracking
    - Statistical data profiling
    - Collaboration (comments, ratings, annotations)
    - Enhanced lineage visualization support
    """

    def __init__(self):
        """Initialize enhanced catalog."""
        super().__init__()

        # Usage tracking
        self.usage_stats: dict[str, UsageStatistics] = {}

        # Collaboration
        self.comments: dict[str, list[DatasetComment]] = defaultdict(list)
        self.ratings: dict[str, list[DatasetRating]] = defaultdict(list)
        self.annotations: dict[str, list[DatasetAnnotation]] = defaultdict(list)

        # Data profiling
        self.profiles: dict[str, DatasetProfile] = {}

        logger.info("Initialized EnhancedDataCatalog with advanced features")

    # ========================================================================
    # Smart Search with Relevance Ranking
    # ========================================================================

    def smart_search(
        self,
        query: str,
        namespace: DatasetNamespace | None = None,
        tags: list[str] | None = None,
        owner: str | None = None,
        min_relevance: float = 0.0,
        limit: int = 20,
    ) -> list[SearchResult]:
        """
        Smart search with TF-IDF relevance ranking.

        Args:
            query: Search query
            namespace: Optional namespace filter
            tags: Optional tag filter
            owner: Optional owner filter
            min_relevance: Minimum relevance score (0.0 to 1.0)
            limit: Maximum number of results

        Returns:
            List of SearchResult, sorted by relevance descending
        """
        if not query:
            return []

        # Get candidate datasets (apply filters first)
        candidates = list(self.datasets.values())

        if namespace:
            candidates = [d for d in candidates if d.namespace == namespace]
        if tags:
            candidates = [d for d in candidates if any(tag in d.tags for tag in tags)]
        if owner:
            candidates = [d for d in candidates if d.owner == owner]

        # Tokenize query
        query_tokens = self._tokenize(query)

        # Score each candidate
        results = []
        for dataset in candidates:
            score, matched_fields, snippets = self._calculate_relevance(
                dataset, query_tokens
            )

            if score >= min_relevance:
                results.append(SearchResult(
                    dataset=dataset,
                    relevance_score=score,
                    matched_fields=matched_fields,
                    highlighted_snippets=snippets,
                ))

        # Sort by relevance descending
        results.sort(key=lambda r: r.relevance_score, reverse=True)

        logger.info(
            f"Smart search: query='{query}', found={len(results)} results, "
            f"top_score={results[0].relevance_score:.3f if results else 0}"
        )

        return results[:limit]

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into words."""
        # Convert to lowercase, remove special chars, split
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        tokens = text.split()
        return [t for t in tokens if len(t) > 2]  # Filter short words

    def _calculate_relevance(
        self, dataset: DatasetMetadata, query_tokens: list[str]
    ) -> tuple[float, list[str], dict[str, str]]:
        """
        Calculate relevance score for a dataset.

        Uses TF-IDF-inspired scoring with field weighting.

        Returns:
            (score, matched_fields, highlighted_snippets)
        """
        score = 0.0
        matched_fields = []
        snippets = {}

        # Field weights (importance)
        field_weights = {
            "name": 3.0,
            "description": 2.0,
            "tags": 2.5,
            "columns": 1.5,
            "owner": 1.0,
        }

        # Search in name (highest weight)
        name_tokens = self._tokenize(dataset.name)
        name_matches = sum(1 for token in query_tokens if token in name_tokens)
        if name_matches > 0:
            score += (name_matches / len(query_tokens)) * field_weights["name"]
            matched_fields.append("name")
            snippets["name"] = self._highlight_text(dataset.name, query_tokens)

        # Search in description
        desc_tokens = self._tokenize(dataset.description)
        desc_matches = sum(1 for token in query_tokens if token in desc_tokens)
        if desc_matches > 0:
            score += (desc_matches / len(query_tokens)) * field_weights["description"]
            matched_fields.append("description")
            snippets["description"] = self._highlight_text(
                dataset.description[:200], query_tokens
            )

        # Search in tags
        tags_text = " ".join(dataset.tags)
        tags_tokens = self._tokenize(tags_text)
        tags_matches = sum(1 for token in query_tokens if token in tags_tokens)
        if tags_matches > 0:
            score += (tags_matches / len(query_tokens)) * field_weights["tags"]
            matched_fields.append("tags")
            snippets["tags"] = ", ".join(dataset.tags)

        # Search in column names and descriptions
        if dataset.columns:
            col_matches = 0
            matched_columns = []
            for col in dataset.columns:
                col_tokens = self._tokenize(col.column_name)
                if col.description:
                    col_tokens.extend(self._tokenize(col.description))

                if any(token in col_tokens for token in query_tokens):
                    col_matches += 1
                    matched_columns.append(col.column_name)

            if col_matches > 0:
                score += (col_matches / len(dataset.columns)) * field_weights["columns"]
                matched_fields.append("columns")
                snippets["columns"] = ", ".join(matched_columns[:5])

        # Boost recently updated datasets (slight recency bias)
        days_since_update = (datetime.utcnow() - dataset.last_updated).days
        recency_boost = max(0, 1.0 - (days_since_update / 365))  # Decay over 1 year
        score *= (1.0 + recency_boost * 0.2)  # Up to 20% boost

        # Boost frequently accessed datasets
        if dataset.dataset_id in self.usage_stats:
            usage = self.usage_stats[dataset.dataset_id]
            if usage.access_count > 10:
                popularity_boost = min(1.0, usage.access_count / 100)
                score *= (1.0 + popularity_boost * 0.1)  # Up to 10% boost

        return score, matched_fields, snippets

    def _highlight_text(self, text: str, query_tokens: list[str]) -> str:
        """Highlight matched query tokens in text."""
        highlighted = text
        for token in query_tokens:
            pattern = re.compile(re.escape(token), re.IGNORECASE)
            highlighted = pattern.sub(f"**{token}**", highlighted)
        return highlighted

    # ========================================================================
    # Usage Analytics
    # ========================================================================

    def record_dataset_access(
        self, dataset_id: str, user_id: str = "anonymous"
    ):
        """
        Record a dataset access for analytics.

        Args:
            dataset_id: Dataset ID
            user_id: User ID (default: "anonymous")
        """
        if dataset_id not in self.usage_stats:
            self.usage_stats[dataset_id] = UsageStatistics(dataset_id=dataset_id)

        self.usage_stats[dataset_id].record_access(user_id)

        logger.debug(f"Recorded access: dataset={dataset_id}, user={user_id}")

    def get_usage_statistics(
        self, dataset_id: str
    ) -> UsageStatistics | None:
        """
        Get usage statistics for a dataset.

        Args:
            dataset_id: Dataset ID

        Returns:
            UsageStatistics or None if no data
        """
        return self.usage_stats.get(dataset_id)

    def get_most_popular_datasets(self, limit: int = 10) -> list[tuple[DatasetMetadata, UsageStatistics]]:
        """
        Get most popular datasets by access count.

        Args:
            limit: Maximum number of datasets to return

        Returns:
            List of (DatasetMetadata, UsageStatistics) tuples
        """
        popular = []

        for dataset_id, stats in self.usage_stats.items():
            dataset = self.get_dataset_by_id(dataset_id)
            if dataset:
                popular.append((dataset, stats))

        # Sort by access count descending
        popular.sort(key=lambda x: x[1].access_count, reverse=True)

        logger.info(f"Top {limit} popular datasets retrieved")

        return popular[:limit]

    # ========================================================================
    # Data Profiling
    # ========================================================================

    def profile_dataset(
        self, dataset_id: str, data: pd.DataFrame
    ) -> DatasetProfile:
        """
        Generate statistical profile for a dataset.

        Args:
            dataset_id: Dataset ID
            data: DataFrame with dataset data

        Returns:
            DatasetProfile with comprehensive statistics
        """
        start_time = datetime.utcnow()

        column_profiles = []

        for col_name in data.columns:
            col_data = data[col_name]
            profile = self._profile_column(col_name, col_data)
            column_profiles.append(profile)

        # Dataset-level metrics
        total_rows = len(data)
        total_columns = len(data.columns)

        # Completeness: average non-null percentage
        completeness = np.mean([
            (1.0 - profile.null_percentage) for profile in column_profiles
        ])

        # Memory usage
        memory_bytes = data.memory_usage(deep=True).sum()

        # Duration
        duration = (datetime.utcnow() - start_time).total_seconds()

        dataset_profile = DatasetProfile(
            dataset_id=dataset_id,
            profiled_at=datetime.utcnow(),
            total_rows=total_rows,
            total_columns=total_columns,
            column_profiles=column_profiles,
            completeness_score=completeness,
            memory_usage_bytes=int(memory_bytes),
            profile_duration_seconds=duration,
        )

        # Store profile
        self.profiles[dataset_id] = dataset_profile

        logger.info(
            f"Profiled dataset {dataset_id}: {total_rows} rows, "
            f"{total_columns} columns, completeness={completeness:.1%}, "
            f"duration={duration:.2f}s"
        )

        return dataset_profile

    def _profile_column(
        self, col_name: str, col_data: pd.Series
    ) -> ColumnProfile:
        """Profile a single column."""
        profile = ColumnProfile(
            column_name=col_name,
            data_type=str(col_data.dtype),
        )

        # Basic statistics
        profile.total_count = len(col_data)
        profile.null_count = int(col_data.isna().sum())
        profile.null_percentage = profile.null_count / profile.total_count if profile.total_count > 0 else 0.0
        profile.unique_count = int(col_data.nunique())
        profile.cardinality = profile.unique_count / profile.total_count if profile.total_count > 0 else 0.0

        # Remove nulls for further analysis
        non_null_data = col_data.dropna()

        if len(non_null_data) == 0:
            return profile

        # Numerical statistics
        if pd.api.types.is_numeric_dtype(col_data):
            try:
                profile.min_value = float(non_null_data.min())
                profile.max_value = float(non_null_data.max())
                profile.mean_value = float(non_null_data.mean())
                profile.median_value = float(non_null_data.median())
                profile.std_dev = float(non_null_data.std())
                profile.percentile_25 = float(non_null_data.quantile(0.25))
                profile.percentile_75 = float(non_null_data.quantile(0.75))

                # Histogram
                hist, bin_edges = np.histogram(non_null_data, bins=10)
                profile.histogram = {
                    "counts": hist.tolist(),
                    "bin_edges": bin_edges.tolist(),
                }
            except Exception as e:
                logger.warning(f"Error profiling numeric column {col_name}: {e}")

        # String statistics
        if pd.api.types.is_string_dtype(col_data) or pd.api.types.is_object_dtype(col_data):
            try:
                str_lengths = non_null_data.astype(str).str.len()
                profile.min_length = int(str_lengths.min())
                profile.max_length = int(str_lengths.max())
                profile.avg_length = float(str_lengths.mean())
            except Exception as e:
                logger.warning(f"Error profiling string column {col_name}: {e}")

        # Top values frequency distribution
        try:
            value_counts = non_null_data.value_counts().head(10)
            profile.top_values = [(val, int(count)) for val, count in value_counts.items()]
        except Exception as e:
            logger.warning(f"Error calculating top values for {col_name}: {e}")

        return profile

    def get_dataset_profile(self, dataset_id: str) -> DatasetProfile | None:
        """
        Get stored profile for a dataset.

        Args:
            dataset_id: Dataset ID

        Returns:
            DatasetProfile or None if not profiled
        """
        return self.profiles.get(dataset_id)

    # ========================================================================
    # Collaboration Features
    # ========================================================================

    def add_comment(
        self,
        dataset_id: str,
        user_id: str,
        user_name: str,
        comment_text: str,
    ) -> DatasetComment:
        """
        Add a comment to a dataset.

        Args:
            dataset_id: Dataset ID
            user_id: User ID
            user_name: User display name
            comment_text: Comment text

        Returns:
            DatasetComment
        """
        comment = DatasetComment(
            comment_id=str(uuid4()),
            dataset_id=dataset_id,
            user_id=user_id,
            user_name=user_name,
            comment_text=comment_text,
            created_at=datetime.utcnow(),
        )

        self.comments[dataset_id].append(comment)

        logger.info(f"Added comment to dataset {dataset_id} by {user_name}")

        return comment

    def get_comments(self, dataset_id: str) -> list[DatasetComment]:
        """
        Get all comments for a dataset.

        Args:
            dataset_id: Dataset ID

        Returns:
            List of DatasetComment, sorted by created_at descending
        """
        comments = self.comments.get(dataset_id, [])
        return sorted(comments, key=lambda c: c.created_at, reverse=True)

    def add_rating(
        self,
        dataset_id: str,
        user_id: str,
        user_name: str,
        rating: int,
        review_text: str | None = None,
    ) -> DatasetRating:
        """
        Add a rating to a dataset.

        Args:
            dataset_id: Dataset ID
            user_id: User ID
            user_name: User display name
            rating: Star rating (1-5)
            review_text: Optional review text

        Returns:
            DatasetRating
        """
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        rating_obj = DatasetRating(
            rating_id=str(uuid4()),
            dataset_id=dataset_id,
            user_id=user_id,
            user_name=user_name,
            rating=rating,
            review_text=review_text,
            created_at=datetime.utcnow(),
        )

        self.ratings[dataset_id].append(rating_obj)

        logger.info(f"Added {rating}-star rating to dataset {dataset_id} by {user_name}")

        return rating_obj

    def get_ratings(self, dataset_id: str) -> list[DatasetRating]:
        """
        Get all ratings for a dataset.

        Args:
            dataset_id: Dataset ID

        Returns:
            List of DatasetRating
        """
        return self.ratings.get(dataset_id, [])

    def get_average_rating(self, dataset_id: str) -> tuple[float, int]:
        """
        Get average rating for a dataset.

        Args:
            dataset_id: Dataset ID

        Returns:
            (average_rating, total_ratings)
        """
        ratings = self.ratings.get(dataset_id, [])

        if not ratings:
            return (0.0, 0)

        avg = sum(r.rating for r in ratings) / len(ratings)
        return (avg, len(ratings))

    def add_annotation(
        self,
        dataset_id: str,
        annotation_type: str,
        annotation_text: str,
        created_by: str,
        column_name: str | None = None,
    ) -> DatasetAnnotation:
        """
        Add an annotation to a dataset or column.

        Args:
            dataset_id: Dataset ID
            annotation_type: Type: "note", "warning", "deprecated", "recommendation"
            annotation_text: Annotation text
            created_by: Creator username
            column_name: Optional column name (None for dataset-level)

        Returns:
            DatasetAnnotation
        """
        annotation = DatasetAnnotation(
            annotation_id=str(uuid4()),
            dataset_id=dataset_id,
            column_name=column_name,
            annotation_type=annotation_type,
            annotation_text=annotation_text,
            created_by=created_by,
            created_at=datetime.utcnow(),
        )

        self.annotations[dataset_id].append(annotation)

        logger.info(
            f"Added {annotation_type} annotation to dataset {dataset_id} "
            f"(column={column_name or 'dataset'})"
        )

        return annotation

    def get_annotations(
        self, dataset_id: str, column_name: str | None = None
    ) -> list[DatasetAnnotation]:
        """
        Get annotations for a dataset or specific column.

        Args:
            dataset_id: Dataset ID
            column_name: Optional column name filter

        Returns:
            List of DatasetAnnotation
        """
        annotations = self.annotations.get(dataset_id, [])

        if column_name is not None:
            annotations = [a for a in annotations if a.column_name == column_name]

        return sorted(annotations, key=lambda a: a.created_at, reverse=True)

    # ========================================================================
    # Enhanced Analytics
    # ========================================================================

    def get_catalog_health(self) -> dict[str, Any]:
        """
        Get catalog health metrics.

        Returns:
            Dictionary with health metrics
        """
        total_datasets = len(self.datasets)

        # Calculate average quality from profiles
        avg_completeness = 0.0
        if self.profiles:
            avg_completeness = np.mean([
                p.completeness_score for p in self.profiles.values()
            ])

        # Calculate average rating
        all_ratings = []
        for ratings in self.ratings.values():
            all_ratings.extend([r.rating for r in ratings])
        avg_rating = np.mean(all_ratings) if all_ratings else 0.0

        # Popular datasets
        popular = self.get_most_popular_datasets(limit=5)

        # Recently updated
        recent = sorted(
            self.datasets.values(),
            key=lambda d: d.last_updated,
            reverse=True
        )[:5]

        return {
            "total_datasets": total_datasets,
            "profiled_datasets": len(self.profiles),
            "avg_completeness": avg_completeness,
            "total_comments": sum(len(c) for c in self.comments.values()),
            "total_ratings": len(all_ratings),
            "avg_rating": avg_rating,
            "total_annotations": sum(len(a) for a in self.annotations.values()),
            "popular_datasets": [
                {
                    "name": dataset.name,
                    "namespace": dataset.namespace,
                    "access_count": stats.access_count,
                }
                for dataset, stats in popular
            ],
            "recently_updated": [
                {
                    "name": dataset.name,
                    "namespace": dataset.namespace,
                    "last_updated": dataset.last_updated.isoformat(),
                }
                for dataset in recent
            ],
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_enhanced_catalog: EnhancedDataCatalog | None = None


def get_enhanced_catalog() -> EnhancedDataCatalog:
    """
    Get or create global enhanced catalog instance.

    Returns:
        EnhancedDataCatalog instance
    """
    global _enhanced_catalog

    if _enhanced_catalog is None:
        _enhanced_catalog = EnhancedDataCatalog()

    return _enhanced_catalog
