"""
Enhanced Catalog API Routes (Phase 4.1)
========================================

API endpoints for advanced catalog features:
- Smart search with relevance ranking
- Usage analytics
- Data profiling
- Collaboration (comments, ratings, annotations)
"""

import logging
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.catalog.enhanced_catalog import (
    DatasetAnnotation,
    DatasetComment,
    DatasetProfile,
    DatasetRating,
    SearchResult,
    UsageStatistics,
    get_enhanced_catalog,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/catalog", tags=["enhanced-catalog"])


# ============================================================================
# Request/Response Models
# ============================================================================


class SmartSearchRequest(BaseModel):
    """Smart search request."""

    query: str = Field(..., min_length=1, description="Search query")
    namespace: str | None = Field(None, description="Filter by namespace")
    tags: list[str] | None = Field(None, description="Filter by tags")
    owner: str | None = Field(None, description="Filter by owner")
    min_relevance: float = Field(0.0, ge=0.0, le=1.0, description="Minimum relevance score")
    limit: int = Field(20, ge=1, le=100, description="Maximum results")


class SearchResultResponse(BaseModel):
    """Search result response."""

    dataset_id: str
    namespace: str
    name: str
    description: str
    tags: list[str]
    owner: str
    relevance_score: float
    matched_fields: list[str]
    highlighted_snippets: dict[str, str]
    last_updated: str


class CommentRequest(BaseModel):
    """Add comment request."""

    user_id: str
    user_name: str
    comment_text: str


class RatingRequest(BaseModel):
    """Add rating request."""

    user_id: str
    user_name: str
    rating: int = Field(..., ge=1, le=5)
    review_text: str | None = None


class AnnotationRequest(BaseModel):
    """Add annotation request."""

    annotation_type: str = Field(..., pattern="^(note|warning|deprecated|recommendation)$")
    annotation_text: str
    created_by: str
    column_name: str | None = None


# ============================================================================
# Smart Search Endpoints
# ============================================================================


@router.post("/smart-search", response_model=list[SearchResultResponse])
async def smart_search(request: SmartSearchRequest):
    """
    Smart search with relevance ranking and highlighting.

    Features:
    - TF-IDF relevance scoring
    - Search across name, description, tags, columns
    - Relevance-based ranking
    - Result highlighting
    - Recency and popularity boost
    """
    try:
        catalog = get_enhanced_catalog()

        # Convert namespace string to enum if provided
        namespace = None
        if request.namespace:
            from app.catalog.catalog import DatasetNamespace
            try:
                namespace = DatasetNamespace(request.namespace)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid namespace: {request.namespace}"
                )

        results = catalog.smart_search(
            query=request.query,
            namespace=namespace,
            tags=request.tags,
            owner=request.owner,
            min_relevance=request.min_relevance,
            limit=request.limit,
        )

        # Convert to response models
        return [
            SearchResultResponse(
                dataset_id=result.dataset.dataset_id,
                namespace=result.dataset.namespace,
                name=result.dataset.name,
                description=result.dataset.description,
                tags=result.dataset.tags,
                owner=result.dataset.owner,
                relevance_score=result.relevance_score,
                matched_fields=result.matched_fields,
                highlighted_snippets=result.highlighted_snippets,
                last_updated=result.dataset.last_updated.isoformat(),
            )
            for result in results
        ]

    except Exception as e:
        logger.error(f"Smart search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Usage Analytics Endpoints
# ============================================================================


@router.post("/datasets/{dataset_id}/record-access")
async def record_dataset_access(dataset_id: str, user_id: str = "anonymous"):
    """
    Record a dataset access for analytics.

    Args:
        dataset_id: Dataset ID
        user_id: User ID (default: anonymous)
    """
    try:
        catalog = get_enhanced_catalog()
        catalog.record_dataset_access(dataset_id, user_id)

        return {"status": "success", "message": "Access recorded"}

    except Exception as e:
        logger.error(f"Record access error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}/usage-stats")
async def get_usage_stats(dataset_id: str):
    """
    Get usage statistics for a dataset.

    Returns:
        Usage statistics including access count, unique users, last accessed
    """
    try:
        catalog = get_enhanced_catalog()
        stats = catalog.get_usage_statistics(dataset_id)

        if not stats:
            return {
                "dataset_id": dataset_id,
                "access_count": 0,
                "unique_users_count": 0,
                "last_accessed": None,
            }

        return {
            "dataset_id": stats.dataset_id,
            "access_count": stats.access_count,
            "unique_users_count": len(stats.unique_users),
            "last_accessed": stats.last_accessed.isoformat() if stats.last_accessed else None,
            "recent_accesses": stats.access_history[-10:],  # Last 10 accesses
        }

    except Exception as e:
        logger.error(f"Get usage stats error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/popular-datasets")
async def get_popular_datasets(limit: int = Query(10, ge=1, le=50)):
    """
    Get most popular datasets by access count.

    Args:
        limit: Maximum number of datasets to return

    Returns:
        List of popular datasets with usage stats
    """
    try:
        catalog = get_enhanced_catalog()
        popular = catalog.get_most_popular_datasets(limit)

        return [
            {
                "dataset_id": dataset.dataset_id,
                "namespace": dataset.namespace,
                "name": dataset.name,
                "description": dataset.description,
                "access_count": stats.access_count,
                "unique_users": len(stats.unique_users),
                "last_accessed": stats.last_accessed.isoformat() if stats.last_accessed else None,
            }
            for dataset, stats in popular
        ]

    except Exception as e:
        logger.error(f"Get popular datasets error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Data Profiling Endpoints
# ============================================================================


@router.post("/datasets/{dataset_id}/profile")
async def profile_dataset(dataset_id: str):
    """
    Generate statistical profile for a dataset.

    Analyzes the dataset and generates:
    - Column statistics (min, max, mean, median, std dev)
    - Null percentages and cardinality
    - Top value frequencies
    - Histograms for numerical columns
    - String length statistics

    NOTE: Requires dataset data to be available.
    """
    try:
        catalog = get_enhanced_catalog()

        # Get dataset
        dataset = catalog.get_dataset_by_id(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        # TODO: Fetch actual dataset data from database
        # For now, return error indicating data is needed
        raise HTTPException(
            status_code=501,
            detail="Data profiling requires dataset data access (not yet implemented)"
        )

        # When implemented:
        # data = fetch_dataset_data(dataset_id)
        # profile = catalog.profile_dataset(dataset_id, data)
        # return profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile dataset error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}/profile")
async def get_dataset_profile(dataset_id: str):
    """
    Get stored statistical profile for a dataset.

    Returns:
        DatasetProfile with column statistics, if available
    """
    try:
        catalog = get_enhanced_catalog()
        profile = catalog.get_dataset_profile(dataset_id)

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="No profile found for dataset (run POST /profile first)"
            )

        # Convert to dict for JSON response
        return {
            "dataset_id": profile.dataset_id,
            "profiled_at": profile.profiled_at.isoformat(),
            "total_rows": profile.total_rows,
            "total_columns": profile.total_columns,
            "completeness_score": profile.completeness_score,
            "memory_usage_bytes": profile.memory_usage_bytes,
            "profile_duration_seconds": profile.profile_duration_seconds,
            "column_profiles": [
                {
                    "column_name": col.column_name,
                    "data_type": col.data_type,
                    "total_count": col.total_count,
                    "null_count": col.null_count,
                    "null_percentage": col.null_percentage,
                    "unique_count": col.unique_count,
                    "cardinality": col.cardinality,
                    "min_value": col.min_value,
                    "max_value": col.max_value,
                    "mean_value": col.mean_value,
                    "median_value": col.median_value,
                    "std_dev": col.std_dev,
                    "percentile_25": col.percentile_25,
                    "percentile_75": col.percentile_75,
                    "min_length": col.min_length,
                    "max_length": col.max_length,
                    "avg_length": col.avg_length,
                    "top_values": col.top_values,
                    "histogram": col.histogram,
                }
                for col in profile.column_profiles
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get dataset profile error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Collaboration Endpoints
# ============================================================================


@router.post("/datasets/{dataset_id}/comments")
async def add_comment(dataset_id: str, request: CommentRequest):
    """
    Add a comment to a dataset.

    Args:
        dataset_id: Dataset ID
        request: Comment details (user_id, user_name, comment_text)

    Returns:
        Created comment
    """
    try:
        catalog = get_enhanced_catalog()

        # Verify dataset exists
        dataset = catalog.get_dataset_by_id(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        comment = catalog.add_comment(
            dataset_id=dataset_id,
            user_id=request.user_id,
            user_name=request.user_name,
            comment_text=request.comment_text,
        )

        return {
            "comment_id": comment.comment_id,
            "dataset_id": comment.dataset_id,
            "user_id": comment.user_id,
            "user_name": comment.user_name,
            "comment_text": comment.comment_text,
            "created_at": comment.created_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add comment error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}/comments")
async def get_comments(dataset_id: str):
    """
    Get all comments for a dataset.

    Args:
        dataset_id: Dataset ID

    Returns:
        List of comments, sorted by created_at descending
    """
    try:
        catalog = get_enhanced_catalog()
        comments = catalog.get_comments(dataset_id)

        return [
            {
                "comment_id": comment.comment_id,
                "dataset_id": comment.dataset_id,
                "user_id": comment.user_id,
                "user_name": comment.user_name,
                "comment_text": comment.comment_text,
                "created_at": comment.created_at.isoformat(),
            }
            for comment in comments
        ]

    except Exception as e:
        logger.error(f"Get comments error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/datasets/{dataset_id}/ratings")
async def add_rating(dataset_id: str, request: RatingRequest):
    """
    Add a rating to a dataset.

    Args:
        dataset_id: Dataset ID
        request: Rating details (user_id, user_name, rating 1-5, optional review)

    Returns:
        Created rating
    """
    try:
        catalog = get_enhanced_catalog()

        # Verify dataset exists
        dataset = catalog.get_dataset_by_id(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        rating = catalog.add_rating(
            dataset_id=dataset_id,
            user_id=request.user_id,
            user_name=request.user_name,
            rating=request.rating,
            review_text=request.review_text,
        )

        return {
            "rating_id": rating.rating_id,
            "dataset_id": rating.dataset_id,
            "user_id": rating.user_id,
            "user_name": rating.user_name,
            "rating": rating.rating,
            "review_text": rating.review_text,
            "created_at": rating.created_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add rating error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}/ratings")
async def get_ratings(dataset_id: str):
    """
    Get all ratings for a dataset.

    Args:
        dataset_id: Dataset ID

    Returns:
        Ratings summary and individual ratings
    """
    try:
        catalog = get_enhanced_catalog()
        ratings = catalog.get_ratings(dataset_id)
        avg_rating, total_ratings = catalog.get_average_rating(dataset_id)

        return {
            "average_rating": avg_rating,
            "total_ratings": total_ratings,
            "ratings": [
                {
                    "rating_id": rating.rating_id,
                    "user_id": rating.user_id,
                    "user_name": rating.user_name,
                    "rating": rating.rating,
                    "review_text": rating.review_text,
                    "created_at": rating.created_at.isoformat(),
                }
                for rating in ratings
            ],
        }

    except Exception as e:
        logger.error(f"Get ratings error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/datasets/{dataset_id}/annotations")
async def add_annotation(dataset_id: str, request: AnnotationRequest):
    """
    Add an annotation to a dataset or column.

    Annotation types:
    - note: General informational note
    - warning: Important warning or caveat
    - deprecated: Mark as deprecated
    - recommendation: Usage recommendation

    Args:
        dataset_id: Dataset ID
        request: Annotation details

    Returns:
        Created annotation
    """
    try:
        catalog = get_enhanced_catalog()

        # Verify dataset exists
        dataset = catalog.get_dataset_by_id(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        annotation = catalog.add_annotation(
            dataset_id=dataset_id,
            annotation_type=request.annotation_type,
            annotation_text=request.annotation_text,
            created_by=request.created_by,
            column_name=request.column_name,
        )

        return {
            "annotation_id": annotation.annotation_id,
            "dataset_id": annotation.dataset_id,
            "column_name": annotation.column_name,
            "annotation_type": annotation.annotation_type,
            "annotation_text": annotation.annotation_text,
            "created_by": annotation.created_by,
            "created_at": annotation.created_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add annotation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}/annotations")
async def get_annotations(
    dataset_id: str,
    column_name: str | None = Query(None, description="Filter by column name")
):
    """
    Get annotations for a dataset or specific column.

    Args:
        dataset_id: Dataset ID
        column_name: Optional column name filter

    Returns:
        List of annotations
    """
    try:
        catalog = get_enhanced_catalog()
        annotations = catalog.get_annotations(dataset_id, column_name)

        return [
            {
                "annotation_id": annotation.annotation_id,
                "dataset_id": annotation.dataset_id,
                "column_name": annotation.column_name,
                "annotation_type": annotation.annotation_type,
                "annotation_text": annotation.annotation_text,
                "created_by": annotation.created_by,
                "created_at": annotation.created_at.isoformat(),
            }
            for annotation in annotations
        ]

    except Exception as e:
        logger.error(f"Get annotations error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Catalog Health Endpoint
# ============================================================================


@router.get("/health")
async def get_catalog_health():
    """
    Get catalog health metrics.

    Returns:
        Comprehensive catalog health statistics including:
        - Total datasets, profiles, comments, ratings, annotations
        - Average completeness and rating
        - Popular datasets
        - Recently updated datasets
    """
    try:
        catalog = get_enhanced_catalog()
        return catalog.get_catalog_health()

    except Exception as e:
        logger.error(f"Get catalog health error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
