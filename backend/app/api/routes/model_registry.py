"""
Model Registry API Routes (Phase 6)
====================================

API endpoints for ML Model Registry management.

Endpoints:
- Model registration and management
- Version creation and lifecycle transitions
- Metrics tracking
- Model comparison
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.ml.model_registry import (
    ModelFramework,
    ModelLineage,
    ModelMetrics,
    ModelStage,
    get_model_registry,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["model-registry"])


# ============================================================================
# Request/Response Models
# ============================================================================


class RegisterModelRequest(BaseModel):
    """Request to register a new model."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=1000)
    tags: list[str] = Field(default_factory=list)


class CreateVersionRequest(BaseModel):
    """Request to create a new model version."""

    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+.*$")  # Semantic version
    framework: str = Field(...)
    description: str = Field("")
    tags: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)
    lineage: dict[str, Any] = Field(default_factory=dict)


class UpdateMetricsRequest(BaseModel):
    """Request to update model metrics."""

    metrics: dict[str, float] = Field(...)


class TransitionStageRequest(BaseModel):
    """Request to transition model stage."""

    stage: str = Field(...)
    archive_existing: bool = Field(True)


# ============================================================================
# Model Registration Endpoints
# ============================================================================


@router.post("/register")
async def register_model(request: RegisterModelRequest):
    """
    Register a new model.

    Creates a new model entry that can have multiple versions.
    """
    try:
        registry = get_model_registry()

        model = registry.register_model(
            name=request.name,
            description=request.description,
            tags=request.tags,
        )

        return {
            "model_id": model.model_id,
            "name": model.name,
            "description": model.description,
            "tags": model.tags,
            "created_at": model.created_at.isoformat(),
            "message": f"Model '{model.name}' registered successfully",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_models(
    tags: list[str] | None = Query(None),
):
    """
    List all registered models.

    Args:
        tags: Optional filter by tags
    """
    try:
        registry = get_model_registry()
        models = registry.list_models(tags=tags)

        return {
            "total": len(models),
            "models": [
                {
                    "model_id": m.model_id,
                    "name": m.name,
                    "description": m.description,
                    "tags": m.tags,
                    "latest_version": m.latest_version,
                    "production_version": m.production_version,
                    "created_at": m.created_at.isoformat(),
                    "updated_at": m.updated_at.isoformat(),
                }
                for m in models
            ],
        }

    except Exception as e:
        logger.error(f"Error listing models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_name}")
async def get_model(model_name: str):
    """
    Get model details.

    Returns model metadata and all versions.
    """
    try:
        registry = get_model_registry()

        model = registry.get_model(model_name)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")

        versions = registry.list_versions(model_name)

        return {
            "model_id": model.model_id,
            "name": model.name,
            "description": model.description,
            "tags": model.tags,
            "latest_version": model.latest_version,
            "production_version": model.production_version,
            "staging_version": model.staging_version,
            "created_at": model.created_at.isoformat(),
            "updated_at": model.updated_at.isoformat(),
            "versions": [
                {
                    "version_id": v.version_id,
                    "version": v.version,
                    "stage": v.stage.value,
                    "framework": v.framework.value,
                    "created_at": v.created_at.isoformat(),
                }
                for v in versions
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{model_name}")
async def delete_model(model_name: str):
    """
    Delete a registered model.

    Will fail if model has production versions.
    """
    try:
        registry = get_model_registry()

        success = registry.delete_model(model_name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")

        return {"message": f"Model '{model_name}' deleted successfully"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Version Management Endpoints
# ============================================================================


@router.post("/{model_name}/versions")
async def create_version(model_name: str, request: CreateVersionRequest):
    """
    Create a new model version.

    Args:
        model_name: Name of the parent model
        request: Version details
    """
    try:
        registry = get_model_registry()

        # Validate framework
        try:
            framework = ModelFramework(request.framework)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid framework: {request.framework}. "
                       f"Valid: {[f.value for f in ModelFramework]}"
            )

        # Build metrics
        metrics = ModelMetrics()
        for key, value in request.metrics.items():
            if hasattr(metrics, key):
                setattr(metrics, key, value)
            else:
                metrics.custom_metrics[key] = value

        # Build lineage
        lineage = ModelLineage(
            feature_group=request.lineage.get("feature_group"),
            feature_version=request.lineage.get("feature_version"),
            training_dataset_id=request.lineage.get("training_dataset_id"),
            features_used=request.lineage.get("features_used", []),
        )

        version = registry.create_version(
            model_name=model_name,
            version=request.version,
            framework=framework,
            description=request.description,
            tags=request.tags,
            parameters=request.parameters,
            metrics=metrics,
            lineage=lineage,
        )

        return {
            "version_id": version.version_id,
            "model_name": version.model_name,
            "version": version.version,
            "stage": version.stage.value,
            "framework": version.framework.value,
            "created_at": version.created_at.isoformat(),
            "message": f"Version {version.version} created successfully",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating version: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_name}/versions")
async def list_versions(
    model_name: str,
    stage: str | None = Query(None),
):
    """
    List all versions of a model.

    Args:
        model_name: Model name
        stage: Optional filter by stage
    """
    try:
        registry = get_model_registry()

        stage_filter = None
        if stage:
            try:
                stage_filter = ModelStage(stage)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid stage: {stage}"
                )

        versions = registry.list_versions(model_name, stage=stage_filter)

        return {
            "model_name": model_name,
            "total": len(versions),
            "versions": [
                {
                    "version_id": v.version_id,
                    "version": v.version,
                    "stage": v.stage.value,
                    "framework": v.framework.value,
                    "description": v.description,
                    "tags": v.tags,
                    "metrics": v.metrics.to_dict(),
                    "parameters": v.parameters,
                    "created_at": v.created_at.isoformat(),
                    "deployed_at": v.deployed_at.isoformat() if v.deployed_at else None,
                    "served_count": v.served_count,
                }
                for v in versions
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing versions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_name}/versions/{version}")
async def get_version(model_name: str, version: str):
    """
    Get detailed version information.
    """
    try:
        registry = get_model_registry()

        model_version = registry.get_version(model_name, version)
        if not model_version:
            raise HTTPException(
                status_code=404,
                detail=f"Version '{version}' not found for model '{model_name}'"
            )

        return {
            "version_id": model_version.version_id,
            "model_name": model_version.model_name,
            "version": model_version.version,
            "stage": model_version.stage.value,
            "framework": model_version.framework.value,
            "description": model_version.description,
            "tags": model_version.tags,
            "parameters": model_version.parameters,
            "metrics": model_version.metrics.to_dict(),
            "lineage": {
                "feature_group": model_version.lineage.feature_group,
                "feature_version": model_version.lineage.feature_version,
                "training_dataset_id": model_version.lineage.training_dataset_id,
                "features_used": model_version.lineage.features_used,
                "preprocessing_steps": model_version.lineage.preprocessing_steps,
            },
            "created_at": model_version.created_at.isoformat(),
            "created_by": model_version.created_by,
            "deployed_at": model_version.deployed_at.isoformat() if model_version.deployed_at else None,
            "archived_at": model_version.archived_at.isoformat() if model_version.archived_at else None,
            "served_count": model_version.served_count,
            "model_path": model_version.model_path,
            "model_hash": model_version.model_hash,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting version: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_name}/latest")
async def get_latest_version(model_name: str):
    """
    Get the latest version of a model.
    """
    try:
        registry = get_model_registry()

        version = registry.get_latest_version(model_name)
        if not version:
            raise HTTPException(status_code=404, detail=f"No versions found for '{model_name}'")

        return {
            "version_id": version.version_id,
            "version": version.version,
            "stage": version.stage.value,
            "framework": version.framework.value,
            "metrics": version.metrics.to_dict(),
            "created_at": version.created_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest version: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_name}/production")
async def get_production_version(model_name: str):
    """
    Get the production version of a model.
    """
    try:
        registry = get_model_registry()

        version = registry.get_production_version(model_name)
        if not version:
            raise HTTPException(status_code=404, detail=f"No production version for '{model_name}'")

        return {
            "version_id": version.version_id,
            "version": version.version,
            "stage": version.stage.value,
            "framework": version.framework.value,
            "metrics": version.metrics.to_dict(),
            "deployed_at": version.deployed_at.isoformat() if version.deployed_at else None,
            "served_count": version.served_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting production version: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Lifecycle Management Endpoints
# ============================================================================


@router.post("/{model_name}/versions/{version}/transition")
async def transition_stage(
    model_name: str,
    version: str,
    request: TransitionStageRequest,
):
    """
    Transition a model version to a new stage.

    Stages: development -> staging -> production -> archived
    """
    try:
        registry = get_model_registry()

        try:
            stage = ModelStage(request.stage)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid stage: {request.stage}. "
                       f"Valid: {[s.value for s in ModelStage]}"
            )

        model_version = registry.transition_stage(
            model_name=model_name,
            version=version,
            stage=stage,
            archive_existing=request.archive_existing,
        )

        return {
            "version_id": model_version.version_id,
            "version": model_version.version,
            "stage": model_version.stage.value,
            "message": f"Transitioned to {stage.value}",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error transitioning stage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_name}/versions/{version}/promote-staging")
async def promote_to_staging(model_name: str, version: str):
    """
    Promote a version to staging.
    """
    try:
        registry = get_model_registry()
        model_version = registry.promote_to_staging(model_name, version)

        return {
            "version_id": model_version.version_id,
            "version": model_version.version,
            "stage": model_version.stage.value,
            "message": "Promoted to staging",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error promoting to staging: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_name}/versions/{version}/promote-production")
async def promote_to_production(model_name: str, version: str):
    """
    Promote a version to production.
    """
    try:
        registry = get_model_registry()
        model_version = registry.promote_to_production(model_name, version)

        return {
            "version_id": model_version.version_id,
            "version": model_version.version,
            "stage": model_version.stage.value,
            "deployed_at": model_version.deployed_at.isoformat() if model_version.deployed_at else None,
            "message": "Promoted to production",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error promoting to production: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Metrics and Comparison Endpoints
# ============================================================================


@router.put("/{model_name}/versions/{version}/metrics")
async def update_metrics(
    model_name: str,
    version: str,
    request: UpdateMetricsRequest,
):
    """
    Update metrics for a model version.
    """
    try:
        registry = get_model_registry()

        model_version = registry.update_metrics(
            model_name=model_name,
            version=version,
            metrics=request.metrics,
        )

        return {
            "version_id": model_version.version_id,
            "version": model_version.version,
            "metrics": model_version.metrics.to_dict(),
            "message": "Metrics updated",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_name}/compare")
async def compare_versions(
    model_name: str,
    version_a: str = Query(...),
    version_b: str = Query(...),
    metrics: list[str] | None = Query(None),
):
    """
    Compare two model versions.

    Args:
        model_name: Model name
        version_a: First version to compare
        version_b: Second version to compare
        metrics: Optional specific metrics to compare
    """
    try:
        registry = get_model_registry()

        comparison = registry.compare_versions(
            model_name=model_name,
            version_a=version_a,
            version_b=version_b,
            metrics_to_compare=metrics,
        )

        return {
            "model_name": model_name,
            "version_a": version_a,
            "version_b": version_b,
            "compared_at": comparison.compared_at.isoformat(),
            "metric_differences": comparison.metric_differences,
            "winner": comparison.winner,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error comparing versions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Search and Export Endpoints
# ============================================================================


@router.get("/search")
async def search_models(
    query: str | None = Query(None),
    framework: str | None = Query(None),
    stage: str | None = Query(None),
    min_accuracy: float | None = Query(None, ge=0.0, le=1.0),
):
    """
    Search models with filters.
    """
    try:
        registry = get_model_registry()

        framework_filter = None
        if framework:
            try:
                framework_filter = ModelFramework(framework)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid framework: {framework}")

        stage_filter = None
        if stage:
            try:
                stage_filter = ModelStage(stage)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")

        results = registry.search_models(
            query=query,
            framework=framework_filter,
            stage=stage_filter,
            min_accuracy=min_accuracy,
        )

        return {
            "total": len(results),
            "results": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_name}/export")
async def export_model_metadata(
    model_name: str,
    version: str | None = Query(None),
):
    """
    Export model metadata as JSON.
    """
    try:
        registry = get_model_registry()

        metadata = registry.export_model_metadata(model_name, version)
        return metadata

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
