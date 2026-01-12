"""
Tests for ML Model Registry (Phase 6)
=====================================

Tests model versioning and lifecycle management.
"""

import pytest

from app.ml.model_registry import (
    ModelFramework,
    ModelLineage,
    ModelMetrics,
    ModelRegistry,
    ModelStage,
    get_model_registry,
)


class TestModelRegistry:
    """Test cases for ModelRegistry."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ModelRegistry(storage_dir="/tmp/atlas_test_models")

    def test_register_model(self):
        """Test registering a new model."""
        model = self.registry.register_model(
            name="fraud_detector",
            description="Detects fraudulent transactions",
            tags=["finance", "classification"],
        )

        assert model is not None
        assert model.name == "fraud_detector"
        assert model.description == "Detects fraudulent transactions"
        assert "finance" in model.tags

    def test_register_duplicate_model_fails(self):
        """Test that registering duplicate model fails."""
        self.registry.register_model(name="duplicate_test")

        with pytest.raises(ValueError, match="already registered"):
            self.registry.register_model(name="duplicate_test")

    def test_get_model(self):
        """Test getting a registered model."""
        self.registry.register_model(name="get_test", description="Test model")

        model = self.registry.get_model("get_test")
        assert model is not None
        assert model.name == "get_test"

        # Non-existent
        assert self.registry.get_model("non_existent") is None

    def test_list_models(self):
        """Test listing models."""
        self.registry.register_model("list_model_1", tags=["tag_a"])
        self.registry.register_model("list_model_2", tags=["tag_b"])
        self.registry.register_model("list_model_3", tags=["tag_a", "tag_b"])

        # All models
        all_models = self.registry.list_models()
        assert len(all_models) >= 3

        # Filter by tag
        tag_a_models = self.registry.list_models(tags=["tag_a"])
        assert len(tag_a_models) >= 2

    def test_update_model(self):
        """Test updating model metadata."""
        self.registry.register_model(
            name="update_test",
            description="Original",
            tags=["old_tag"],
        )

        updated = self.registry.update_model(
            name="update_test",
            description="Updated description",
            tags=["new_tag"],
        )

        assert updated.description == "Updated description"
        assert "new_tag" in updated.tags
        assert "old_tag" not in updated.tags

    def test_delete_model(self):
        """Test deleting a model."""
        self.registry.register_model(name="delete_test")

        result = self.registry.delete_model("delete_test")
        assert result is True

        assert self.registry.get_model("delete_test") is None

        # Delete non-existent
        result = self.registry.delete_model("non_existent")
        assert result is False


class TestModelVersions:
    """Test model version management."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ModelRegistry(storage_dir="/tmp/atlas_test_models")
        self.registry.register_model(
            name="versioned_model",
            description="Model with versions",
        )

    def test_create_version(self):
        """Test creating a model version."""
        version = self.registry.create_version(
            model_name="versioned_model",
            version="1.0.0",
            framework=ModelFramework.SKLEARN,
            description="Initial version",
            tags=["baseline"],
            parameters={"n_estimators": 100, "max_depth": 10},
        )

        assert version is not None
        assert version.version == "1.0.0"
        assert version.framework == ModelFramework.SKLEARN
        assert version.stage == ModelStage.DEVELOPMENT
        assert version.parameters["n_estimators"] == 100

    def test_create_version_with_metrics(self):
        """Test creating version with metrics."""
        metrics = ModelMetrics(
            accuracy=0.95,
            precision=0.93,
            recall=0.92,
            f1_score=0.925,
        )

        version = self.registry.create_version(
            model_name="versioned_model",
            version="1.1.0",
            framework=ModelFramework.SKLEARN,
            metrics=metrics,
        )

        assert version.metrics.accuracy == 0.95
        assert version.metrics.precision == 0.93

    def test_create_version_with_lineage(self):
        """Test creating version with lineage."""
        lineage = ModelLineage(
            feature_group="customer_features",
            feature_version="2.0.0",
            training_dataset_id="ds_123",
            features_used=["age", "income", "credit_score"],
        )

        version = self.registry.create_version(
            model_name="versioned_model",
            version="1.2.0",
            framework=ModelFramework.SKLEARN,
            lineage=lineage,
        )

        assert version.lineage.feature_group == "customer_features"
        assert "age" in version.lineage.features_used

    def test_get_version(self):
        """Test getting a specific version."""
        self.registry.create_version(
            model_name="versioned_model",
            version="2.0.0",
            framework=ModelFramework.PYTORCH,
        )

        version = self.registry.get_version("versioned_model", "2.0.0")
        assert version is not None
        assert version.framework == ModelFramework.PYTORCH

    def test_get_latest_version(self):
        """Test getting latest version."""
        self.registry.create_version(
            model_name="versioned_model",
            version="3.0.0",
            framework=ModelFramework.SKLEARN,
        )
        self.registry.create_version(
            model_name="versioned_model",
            version="3.1.0",
            framework=ModelFramework.SKLEARN,
        )

        latest = self.registry.get_latest_version("versioned_model")
        assert latest is not None
        # Latest is the most recently created
        assert latest.version == "3.1.0"

    def test_list_versions(self):
        """Test listing all versions."""
        for i in range(3):
            self.registry.create_version(
                model_name="versioned_model",
                version=f"4.{i}.0",
                framework=ModelFramework.SKLEARN,
            )

        versions = self.registry.list_versions("versioned_model")
        assert len(versions) >= 3


class TestModelLifecycle:
    """Test model lifecycle transitions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ModelRegistry(storage_dir="/tmp/atlas_test_models")
        self.registry.register_model(name="lifecycle_model")
        self.registry.create_version(
            model_name="lifecycle_model",
            version="1.0.0",
            framework=ModelFramework.SKLEARN,
        )

    def test_transition_to_staging(self):
        """Test promoting to staging."""
        version = self.registry.promote_to_staging("lifecycle_model", "1.0.0")

        assert version.stage == ModelStage.STAGING

        model = self.registry.get_model("lifecycle_model")
        assert model.staging_version == "1.0.0"

    def test_transition_to_production(self):
        """Test promoting to production."""
        version = self.registry.promote_to_production("lifecycle_model", "1.0.0")

        assert version.stage == ModelStage.PRODUCTION
        assert version.deployed_at is not None

        model = self.registry.get_model("lifecycle_model")
        assert model.production_version == "1.0.0"

    def test_archive_version(self):
        """Test archiving a version."""
        version = self.registry.archive_version("lifecycle_model", "1.0.0")

        assert version.stage == ModelStage.ARCHIVED
        assert version.archived_at is not None

    def test_auto_archive_on_promotion(self):
        """Test that existing staging/production is archived on promotion."""
        # Create two versions
        self.registry.create_version(
            model_name="lifecycle_model",
            version="1.1.0",
            framework=ModelFramework.SKLEARN,
        )

        # Promote first to production
        self.registry.promote_to_production("lifecycle_model", "1.0.0")

        # Promote second to production (should archive first)
        self.registry.promote_to_production("lifecycle_model", "1.1.0")

        # Check first is archived
        v1 = self.registry.get_version("lifecycle_model", "1.0.0")
        assert v1.stage == ModelStage.ARCHIVED

    def test_cannot_delete_model_with_production(self):
        """Test that model with production version cannot be deleted."""
        self.registry.promote_to_production("lifecycle_model", "1.0.0")

        with pytest.raises(ValueError, match="production version"):
            self.registry.delete_model("lifecycle_model")


class TestModelMetrics:
    """Test metrics tracking."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ModelRegistry(storage_dir="/tmp/atlas_test_models")
        self.registry.register_model(name="metrics_model")
        self.registry.create_version(
            model_name="metrics_model",
            version="1.0.0",
            framework=ModelFramework.SKLEARN,
        )

    def test_update_metrics(self):
        """Test updating model metrics."""
        version = self.registry.update_metrics(
            model_name="metrics_model",
            version="1.0.0",
            metrics={
                "accuracy": 0.95,
                "custom_metric": 0.88,
            },
        )

        assert version.metrics.accuracy == 0.95
        assert version.metrics.custom_metrics["custom_metric"] == 0.88

    def test_record_serving(self):
        """Test recording serving counts."""
        self.registry.record_serving("metrics_model", "1.0.0", count=10)

        version = self.registry.get_version("metrics_model", "1.0.0")
        assert version.served_count == 10

        self.registry.record_serving("metrics_model", "1.0.0", count=5)
        version = self.registry.get_version("metrics_model", "1.0.0")
        assert version.served_count == 15


class TestModelComparison:
    """Test model comparison functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ModelRegistry(storage_dir="/tmp/atlas_test_models")
        self.registry.register_model(name="compare_model")

        # Create two versions with different metrics
        metrics_a = ModelMetrics(accuracy=0.90, f1_score=0.88)
        metrics_b = ModelMetrics(accuracy=0.92, f1_score=0.91)

        self.registry.create_version(
            model_name="compare_model",
            version="1.0.0",
            framework=ModelFramework.SKLEARN,
            metrics=metrics_a,
        )
        self.registry.create_version(
            model_name="compare_model",
            version="2.0.0",
            framework=ModelFramework.SKLEARN,
            metrics=metrics_b,
        )

    def test_compare_versions(self):
        """Test comparing two versions."""
        comparison = self.registry.compare_versions(
            model_name="compare_model",
            version_a="1.0.0",
            version_b="2.0.0",
        )

        assert comparison is not None
        assert "accuracy" in comparison.metric_differences
        assert comparison.metric_differences["accuracy"] == 0.02  # 0.92 - 0.90

    def test_compare_with_specific_metrics(self):
        """Test comparing only specific metrics."""
        comparison = self.registry.compare_versions(
            model_name="compare_model",
            version_a="1.0.0",
            version_b="2.0.0",
            metrics_to_compare=["accuracy"],
        )

        assert "accuracy" in comparison.metric_differences
        assert "f1_score" not in comparison.metric_differences


class TestModelSearch:
    """Test model search functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ModelRegistry(storage_dir="/tmp/atlas_test_models")

        # Create models with different frameworks
        self.registry.register_model(name="sklearn_model", description="SKLearn classifier")
        self.registry.create_version(
            model_name="sklearn_model",
            version="1.0.0",
            framework=ModelFramework.SKLEARN,
            metrics=ModelMetrics(accuracy=0.85),
        )

        self.registry.register_model(name="pytorch_model", description="PyTorch neural net")
        self.registry.create_version(
            model_name="pytorch_model",
            version="1.0.0",
            framework=ModelFramework.PYTORCH,
            metrics=ModelMetrics(accuracy=0.92),
        )

    def test_search_by_query(self):
        """Test searching by text query."""
        results = self.registry.search_models(query="sklearn")
        assert len(results) >= 1
        assert any("sklearn" in r["model_name"] for r in results)

    def test_search_by_framework(self):
        """Test filtering by framework."""
        results = self.registry.search_models(framework=ModelFramework.PYTORCH)
        assert len(results) >= 1
        assert all(r["framework"] == "pytorch" for r in results)

    def test_search_by_min_accuracy(self):
        """Test filtering by minimum accuracy."""
        results = self.registry.search_models(min_accuracy=0.90)
        assert len(results) >= 1
        assert all(r.get("best_accuracy", 0) >= 0.90 for r in results)


class TestModelExport:
    """Test model export functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ModelRegistry(storage_dir="/tmp/atlas_test_models")
        self.registry.register_model(name="export_model", description="For export")
        self.registry.create_version(
            model_name="export_model",
            version="1.0.0",
            framework=ModelFramework.SKLEARN,
            parameters={"param1": "value1"},
            metrics=ModelMetrics(accuracy=0.95),
        )

    def test_export_metadata(self):
        """Test exporting model metadata."""
        metadata = self.registry.export_model_metadata("export_model", "1.0.0")

        assert "model" in metadata
        assert "version" in metadata
        assert metadata["model"]["name"] == "export_model"
        assert metadata["version"]["version"] == "1.0.0"
        assert metadata["version"]["parameters"]["param1"] == "value1"
        assert metadata["version"]["metrics"]["accuracy"] == 0.95

    def test_export_latest_when_no_version_specified(self):
        """Test that export uses latest when version not specified."""
        metadata = self.registry.export_model_metadata("export_model")

        assert metadata["version"] is not None
        assert metadata["version"]["version"] == "1.0.0"
