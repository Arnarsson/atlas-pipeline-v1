"""
ML Model Registry (Phase 6)
===========================

Provides model versioning and lifecycle management for Atlas Data Pipeline.

Features:
- Model versioning with semantic versioning
- Model metadata storage
- Model lifecycle stages (development, staging, production, archived)
- Model metrics tracking
- Model lineage (which features were used)
- Model comparison and A/B testing support

Reference: MLflow Model Registry, SageMaker Model Registry patterns
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Data Models
# ============================================================================


class ModelStage(str, Enum):
    """Model lifecycle stages."""

    DEVELOPMENT = "development"  # In development, not ready for use
    STAGING = "staging"  # Testing in staging environment
    PRODUCTION = "production"  # Live in production
    ARCHIVED = "archived"  # No longer active, kept for reference


class ModelFramework(str, Enum):
    """Supported ML frameworks."""

    SKLEARN = "sklearn"
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    CATBOOST = "catboost"
    ONNX = "onnx"
    CUSTOM = "custom"


@dataclass
class ModelMetrics:
    """Model performance metrics."""

    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1_score: float | None = None
    auc_roc: float | None = None
    rmse: float | None = None
    mae: float | None = None
    r2_score: float | None = None
    custom_metrics: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {}
        for attr in ["accuracy", "precision", "recall", "f1_score", "auc_roc", "rmse", "mae", "r2_score"]:
            value = getattr(self, attr)
            if value is not None:
                result[attr] = value
        result.update(self.custom_metrics)
        return result


@dataclass
class ModelLineage:
    """Model training lineage."""

    feature_group: str | None = None  # Feature store group used
    feature_version: str | None = None  # Feature version used
    training_dataset_id: str | None = None  # Dataset used for training
    training_run_id: str | None = None  # Pipeline run that created training data
    parent_model_id: str | None = None  # If fine-tuned from another model
    features_used: list[str] = field(default_factory=list)
    preprocessing_steps: list[str] = field(default_factory=list)


@dataclass
class ModelVersion:
    """A specific version of a registered model."""

    version_id: str
    model_name: str
    version: str  # Semantic version (1.0.0, 1.1.0, etc.)
    stage: ModelStage
    framework: ModelFramework
    created_at: datetime
    created_by: str

    # Model artifacts
    model_path: str | None = None  # Path to serialized model
    model_hash: str | None = None  # SHA256 hash of model file

    # Metadata
    description: str = ""
    tags: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)  # Hyperparameters
    metrics: ModelMetrics = field(default_factory=ModelMetrics)
    lineage: ModelLineage = field(default_factory=ModelLineage)

    # Tracking
    deployed_at: datetime | None = None
    archived_at: datetime | None = None
    served_count: int = 0  # Number of inference requests


@dataclass
class RegisteredModel:
    """A registered model with multiple versions."""

    model_id: str
    name: str
    description: str
    created_at: datetime
    created_by: str
    updated_at: datetime
    tags: list[str] = field(default_factory=list)
    latest_version: str | None = None
    production_version: str | None = None
    staging_version: str | None = None


@dataclass
class ModelComparison:
    """Comparison between two model versions."""

    model_a_id: str
    model_b_id: str
    compared_at: datetime
    metric_differences: dict[str, float]  # metric -> (b - a) difference
    winner: str | None = None  # model_a_id or model_b_id
    notes: str = ""


# ============================================================================
# Model Registry
# ============================================================================


class ModelRegistry:
    """
    ML Model Registry for Atlas Data Pipeline.

    Manages the full model lifecycle from development to production.
    """

    def __init__(self, storage_dir: str | None = None):
        """
        Initialize model registry.

        Args:
            storage_dir: Directory for model artifacts
        """
        self.storage_dir = Path(storage_dir or "/tmp/atlas_models")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # In-memory storage (replace with database in production)
        self._models: dict[str, RegisteredModel] = {}
        self._versions: dict[str, dict[str, ModelVersion]] = {}  # model_name -> version -> ModelVersion
        self._comparisons: list[ModelComparison] = []

        logger.info(f"Initialized Model Registry: storage_dir={self.storage_dir}")

    # ========================================================================
    # Model Registration
    # ========================================================================

    def register_model(
        self,
        name: str,
        description: str = "",
        tags: list[str] | None = None,
        created_by: str = "system",
    ) -> RegisteredModel:
        """
        Register a new model.

        Args:
            name: Model name (unique identifier)
            description: Model description
            tags: Optional tags
            created_by: User who registered the model

        Returns:
            RegisteredModel
        """
        if name in self._models:
            raise ValueError(f"Model '{name}' already registered")

        model = RegisteredModel(
            model_id=str(uuid4()),
            name=name,
            description=description,
            created_at=datetime.utcnow(),
            created_by=created_by,
            updated_at=datetime.utcnow(),
            tags=tags or [],
        )

        self._models[name] = model
        self._versions[name] = {}

        logger.info(f"Registered model: {name}")
        return model

    def get_model(self, name: str) -> RegisteredModel | None:
        """Get registered model by name."""
        return self._models.get(name)

    def list_models(self, tags: list[str] | None = None) -> list[RegisteredModel]:
        """
        List all registered models.

        Args:
            tags: Optional filter by tags

        Returns:
            List of RegisteredModel
        """
        models = list(self._models.values())

        if tags:
            models = [m for m in models if any(t in m.tags for t in tags)]

        return sorted(models, key=lambda m: m.updated_at, reverse=True)

    def update_model(
        self,
        name: str,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> RegisteredModel:
        """
        Update model metadata.

        Args:
            name: Model name
            description: New description
            tags: New tags

        Returns:
            Updated RegisteredModel
        """
        model = self._models.get(name)
        if not model:
            raise ValueError(f"Model '{name}' not found")

        if description is not None:
            model.description = description
        if tags is not None:
            model.tags = tags

        model.updated_at = datetime.utcnow()

        logger.info(f"Updated model: {name}")
        return model

    def delete_model(self, name: str) -> bool:
        """
        Delete a registered model and all versions.

        Args:
            name: Model name

        Returns:
            True if deleted
        """
        if name not in self._models:
            return False

        # Check for production versions
        if name in self._versions:
            for version in self._versions[name].values():
                if version.stage == ModelStage.PRODUCTION:
                    raise ValueError(
                        f"Cannot delete model with production version: {version.version}"
                    )

        del self._models[name]
        self._versions.pop(name, None)

        logger.info(f"Deleted model: {name}")
        return True

    # ========================================================================
    # Version Management
    # ========================================================================

    def create_version(
        self,
        model_name: str,
        version: str,
        framework: ModelFramework,
        created_by: str = "system",
        description: str = "",
        tags: list[str] | None = None,
        parameters: dict[str, Any] | None = None,
        metrics: ModelMetrics | None = None,
        lineage: ModelLineage | None = None,
        model_bytes: bytes | None = None,
    ) -> ModelVersion:
        """
        Create a new model version.

        Args:
            model_name: Name of parent model
            version: Semantic version string
            framework: ML framework used
            created_by: User creating the version
            description: Version description
            tags: Optional tags
            parameters: Hyperparameters
            metrics: Performance metrics
            lineage: Training lineage
            model_bytes: Optional serialized model

        Returns:
            ModelVersion
        """
        if model_name not in self._models:
            raise ValueError(f"Model '{model_name}' not registered")

        if version in self._versions.get(model_name, {}):
            raise ValueError(f"Version '{version}' already exists for model '{model_name}'")

        # Store model artifact if provided
        model_path = None
        model_hash = None
        if model_bytes:
            model_hash = hashlib.sha256(model_bytes).hexdigest()
            model_path = str(self.storage_dir / f"{model_name}_{version}.model")
            with open(model_path, "wb") as f:
                f.write(model_bytes)
            logger.debug(f"Saved model artifact: {model_path}")

        model_version = ModelVersion(
            version_id=str(uuid4()),
            model_name=model_name,
            version=version,
            stage=ModelStage.DEVELOPMENT,
            framework=framework,
            created_at=datetime.utcnow(),
            created_by=created_by,
            model_path=model_path,
            model_hash=model_hash,
            description=description,
            tags=tags or [],
            parameters=parameters or {},
            metrics=metrics or ModelMetrics(),
            lineage=lineage or ModelLineage(),
        )

        self._versions[model_name][version] = model_version

        # Update parent model
        self._models[model_name].latest_version = version
        self._models[model_name].updated_at = datetime.utcnow()

        logger.info(f"Created model version: {model_name} v{version}")
        return model_version

    def get_version(self, model_name: str, version: str) -> ModelVersion | None:
        """Get a specific model version."""
        return self._versions.get(model_name, {}).get(version)

    def get_latest_version(self, model_name: str) -> ModelVersion | None:
        """Get the latest version of a model."""
        if model_name not in self._models:
            return None

        latest = self._models[model_name].latest_version
        if latest:
            return self._versions[model_name].get(latest)
        return None

    def get_production_version(self, model_name: str) -> ModelVersion | None:
        """Get the production version of a model."""
        if model_name not in self._models:
            return None

        prod = self._models[model_name].production_version
        if prod:
            return self._versions[model_name].get(prod)
        return None

    def list_versions(
        self,
        model_name: str,
        stage: ModelStage | None = None,
    ) -> list[ModelVersion]:
        """
        List all versions of a model.

        Args:
            model_name: Model name
            stage: Optional stage filter

        Returns:
            List of ModelVersion
        """
        versions = list(self._versions.get(model_name, {}).values())

        if stage:
            versions = [v for v in versions if v.stage == stage]

        return sorted(versions, key=lambda v: v.created_at, reverse=True)

    # ========================================================================
    # Lifecycle Management
    # ========================================================================

    def transition_stage(
        self,
        model_name: str,
        version: str,
        stage: ModelStage,
        archive_existing: bool = True,
    ) -> ModelVersion:
        """
        Transition a model version to a new stage.

        Args:
            model_name: Model name
            version: Version string
            stage: Target stage
            archive_existing: Archive existing version in same stage

        Returns:
            Updated ModelVersion
        """
        model_version = self.get_version(model_name, version)
        if not model_version:
            raise ValueError(f"Version '{version}' not found for model '{model_name}'")

        # Archive existing version in target stage if requested
        if archive_existing and stage in [ModelStage.STAGING, ModelStage.PRODUCTION]:
            for v in self._versions[model_name].values():
                if v.version != version and v.stage == stage:
                    v.stage = ModelStage.ARCHIVED
                    v.archived_at = datetime.utcnow()
                    logger.info(f"Archived {model_name} v{v.version}")

        # Update stage
        model_version.stage = stage

        if stage == ModelStage.PRODUCTION:
            model_version.deployed_at = datetime.utcnow()
            self._models[model_name].production_version = version
        elif stage == ModelStage.STAGING:
            self._models[model_name].staging_version = version
        elif stage == ModelStage.ARCHIVED:
            model_version.archived_at = datetime.utcnow()

        self._models[model_name].updated_at = datetime.utcnow()

        logger.info(f"Transitioned {model_name} v{version} to {stage.value}")
        return model_version

    def promote_to_staging(self, model_name: str, version: str) -> ModelVersion:
        """Promote a model version to staging."""
        return self.transition_stage(model_name, version, ModelStage.STAGING)

    def promote_to_production(self, model_name: str, version: str) -> ModelVersion:
        """Promote a model version to production."""
        return self.transition_stage(model_name, version, ModelStage.PRODUCTION)

    def archive_version(self, model_name: str, version: str) -> ModelVersion:
        """Archive a model version."""
        return self.transition_stage(model_name, version, ModelStage.ARCHIVED, archive_existing=False)

    # ========================================================================
    # Metrics Tracking
    # ========================================================================

    def update_metrics(
        self,
        model_name: str,
        version: str,
        metrics: dict[str, float],
    ) -> ModelVersion:
        """
        Update metrics for a model version.

        Args:
            model_name: Model name
            version: Version string
            metrics: Dictionary of metric values

        Returns:
            Updated ModelVersion
        """
        model_version = self.get_version(model_name, version)
        if not model_version:
            raise ValueError(f"Version not found")

        # Update standard metrics
        for metric in ["accuracy", "precision", "recall", "f1_score", "auc_roc", "rmse", "mae", "r2_score"]:
            if metric in metrics:
                setattr(model_version.metrics, metric, metrics[metric])

        # Update custom metrics
        for key, value in metrics.items():
            if key not in ["accuracy", "precision", "recall", "f1_score", "auc_roc", "rmse", "mae", "r2_score"]:
                model_version.metrics.custom_metrics[key] = value

        logger.info(f"Updated metrics for {model_name} v{version}")
        return model_version

    def record_serving(self, model_name: str, version: str, count: int = 1) -> None:
        """Record that a model version was used for serving."""
        model_version = self.get_version(model_name, version)
        if model_version:
            model_version.served_count += count

    # ========================================================================
    # Model Comparison
    # ========================================================================

    def compare_versions(
        self,
        model_name: str,
        version_a: str,
        version_b: str,
        metrics_to_compare: list[str] | None = None,
    ) -> ModelComparison:
        """
        Compare two model versions.

        Args:
            model_name: Model name
            version_a: First version
            version_b: Second version
            metrics_to_compare: Optional specific metrics to compare

        Returns:
            ModelComparison result
        """
        v_a = self.get_version(model_name, version_a)
        v_b = self.get_version(model_name, version_b)

        if not v_a or not v_b:
            raise ValueError("One or both versions not found")

        # Get all metrics
        metrics_a = v_a.metrics.to_dict()
        metrics_b = v_b.metrics.to_dict()

        # Calculate differences
        all_metrics = set(metrics_a.keys()) | set(metrics_b.keys())
        if metrics_to_compare:
            all_metrics = all_metrics & set(metrics_to_compare)

        differences = {}
        for metric in all_metrics:
            val_a = metrics_a.get(metric, 0)
            val_b = metrics_b.get(metric, 0)
            differences[metric] = val_b - val_a

        # Determine winner (higher is better for most metrics)
        winner = None
        if "accuracy" in differences:
            winner = v_b.version_id if differences["accuracy"] > 0 else v_a.version_id
        elif "f1_score" in differences:
            winner = v_b.version_id if differences["f1_score"] > 0 else v_a.version_id

        comparison = ModelComparison(
            model_a_id=v_a.version_id,
            model_b_id=v_b.version_id,
            compared_at=datetime.utcnow(),
            metric_differences=differences,
            winner=winner,
        )

        self._comparisons.append(comparison)

        logger.info(f"Compared {model_name}: v{version_a} vs v{version_b}")
        return comparison

    # ========================================================================
    # Export and Search
    # ========================================================================

    def export_model_metadata(self, model_name: str, version: str | None = None) -> dict[str, Any]:
        """
        Export model metadata as dictionary.

        Args:
            model_name: Model name
            version: Optional specific version (defaults to latest)

        Returns:
            Dictionary with full model metadata
        """
        model = self.get_model(model_name)
        if not model:
            raise ValueError(f"Model '{model_name}' not found")

        model_version = None
        if version:
            model_version = self.get_version(model_name, version)
        else:
            model_version = self.get_latest_version(model_name)

        return {
            "model": {
                "model_id": model.model_id,
                "name": model.name,
                "description": model.description,
                "tags": model.tags,
                "created_at": model.created_at.isoformat(),
                "created_by": model.created_by,
                "latest_version": model.latest_version,
                "production_version": model.production_version,
            },
            "version": {
                "version_id": model_version.version_id,
                "version": model_version.version,
                "stage": model_version.stage.value,
                "framework": model_version.framework.value,
                "description": model_version.description,
                "parameters": model_version.parameters,
                "metrics": model_version.metrics.to_dict(),
                "lineage": {
                    "feature_group": model_version.lineage.feature_group,
                    "feature_version": model_version.lineage.feature_version,
                    "training_dataset_id": model_version.lineage.training_dataset_id,
                    "features_used": model_version.lineage.features_used,
                },
                "created_at": model_version.created_at.isoformat(),
                "served_count": model_version.served_count,
            } if model_version else None,
        }

    def search_models(
        self,
        query: str | None = None,
        framework: ModelFramework | None = None,
        stage: ModelStage | None = None,
        min_accuracy: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search models with filters.

        Args:
            query: Search query (matches name, description)
            framework: Filter by framework
            stage: Filter by version stage
            min_accuracy: Minimum accuracy threshold

        Returns:
            List of matching model summaries
        """
        results = []

        for model in self._models.values():
            # Text search
            if query:
                query_lower = query.lower()
                if query_lower not in model.name.lower() and query_lower not in model.description.lower():
                    continue

            versions = self._versions.get(model.name, {}).values()

            # Filter versions
            if framework:
                versions = [v for v in versions if v.framework == framework]
            if stage:
                versions = [v for v in versions if v.stage == stage]
            if min_accuracy is not None:
                versions = [v for v in versions if v.metrics.accuracy and v.metrics.accuracy >= min_accuracy]

            if versions:
                best_version = max(versions, key=lambda v: v.metrics.accuracy or 0)
                results.append({
                    "model_name": model.name,
                    "description": model.description,
                    "tags": model.tags,
                    "best_version": best_version.version,
                    "best_accuracy": best_version.metrics.accuracy,
                    "framework": best_version.framework.value,
                    "stage": best_version.stage.value,
                })

        return results


# ============================================================================
# Singleton Instance
# ============================================================================

_model_registry: ModelRegistry | None = None


def get_model_registry() -> ModelRegistry:
    """
    Get or create global model registry instance.

    Returns:
        ModelRegistry instance
    """
    global _model_registry

    if _model_registry is None:
        _model_registry = ModelRegistry()

    return _model_registry
