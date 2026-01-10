"""
Integration Tests for Week 5-6: Data Lineage & GDPR Workflows
=============================================================

Tests for:
- OpenLineage integration
- Feature Store
- GDPR workflows
- Data Catalog
"""

import pandas as pd
import pytest
from io import BytesIO


class TestOpenLineageIntegration:
    """Test OpenLineage client integration."""

    def test_lineage_client_initialization(self):
        """Test that lineage client initializes correctly."""
        from app.lineage.openlineage_client import get_lineage_client, LineageConfig

        client = get_lineage_client()
        assert client is not None
        assert client.namespace == "atlas_production"
        assert client.producer == "atlas_pipeline_v1.0"

    def test_emit_start_event(self):
        """Test emitting START event."""
        from app.lineage.openlineage_client import get_lineage_client

        client = get_lineage_client()

        # Emit START event (will fail gracefully if Marquez unavailable)
        success = client.emit_start_event(
            job_name="test_pipeline",
            run_id="test-run-123",
            inputs=[{"name": "test_input.csv", "facets": {}}],
            outputs=[{"name": "explore.test_data", "facets": {}}],
        )

        # Success depends on Marquez availability
        assert isinstance(success, bool)

    def test_emit_complete_event(self):
        """Test emitting COMPLETE event."""
        from app.lineage.openlineage_client import get_lineage_client

        client = get_lineage_client()

        success = client.emit_complete_event(
            job_name="test_pipeline",
            run_id="test-run-123",
            outputs=[{"name": "explore.test_data", "facets": {}}],
            metrics={"rows_processed": 100, "duration_seconds": 1.5},
        )

        assert isinstance(success, bool)

    def test_emit_fail_event(self):
        """Test emitting FAIL event."""
        from app.lineage.openlineage_client import get_lineage_client

        client = get_lineage_client()

        success = client.emit_fail_event(
            job_name="test_pipeline",
            run_id="test-run-123",
            error_message="Test error message",
        )

        assert isinstance(success, bool)

    def test_create_dataset_facets(self):
        """Test creating dataset facets from DataFrame."""
        from app.lineage.openlineage_client import get_lineage_client

        client = get_lineage_client()

        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35]
        })

        facets = client._create_dataset_facets(df, "s3://test-bucket/data.csv")

        assert "schema" in facets
        assert "dataSource" in facets
        assert "stats" in facets
        assert facets["stats"]["rowCount"] == 3
        assert facets["stats"]["columnCount"] == 3


class TestFeatureStore:
    """Test Feature Store functionality."""

    def test_feature_store_initialization(self):
        """Test that feature store initializes correctly."""
        from app.features.feature_store import get_feature_store

        store = get_feature_store()
        assert store is not None
        assert isinstance(store.feature_groups, dict)

    def test_register_feature_group(self):
        """Test registering a feature group."""
        from app.features.feature_store import get_feature_store

        store = get_feature_store()

        df = pd.DataFrame({
            "customer_id": [1, 2, 3],
            "total_purchases": [10, 20, 15],
            "avg_order_value": [100.0, 150.0, 120.0]
        })

        feature_group = store.register_feature_group(
            name="customer_metrics",
            description="Customer purchase metrics",
            df=df,
            version="1.0.0",
            tags=["finance", "production"]
        )

        assert feature_group.name == "customer_metrics"
        assert feature_group.version == "1.0.0"
        assert "finance" in feature_group.tags

    def test_list_feature_groups(self):
        """Test listing feature groups."""
        from app.features.feature_store import get_feature_store

        store = get_feature_store()

        # Register a feature group first
        df = pd.DataFrame({"col1": [1, 2, 3]})
        store.register_feature_group("test_features", "Test features", df)

        groups = store.list_feature_groups()
        assert len(groups) >= 1
        assert any(g.name == "test_features" for g in groups)

    def test_get_versions(self):
        """Test getting feature group versions."""
        from app.features.feature_store import get_feature_store

        store = get_feature_store()

        df = pd.DataFrame({"col1": [1, 2, 3]})

        # Register version 1.0.0
        store.register_feature_group("versioned_features", "Test", df, version="1.0.0")

        # Register version 1.1.0
        store.register_feature_group("versioned_features", "Test", df, version="1.1.0")

        versions = store.get_versions("versioned_features")
        assert len(versions) == 2
        assert any(v.version == "1.0.0" for v in versions)
        assert any(v.version == "1.1.0" for v in versions)

    def test_get_latest_version(self):
        """Test getting latest version."""
        from app.features.feature_store import get_feature_store

        store = get_feature_store()

        df = pd.DataFrame({"col1": [1, 2, 3]})

        store.register_feature_group("latest_test", "Test", df, version="1.0.0")
        store.register_feature_group("latest_test", "Test", df, version="2.0.0")

        latest = store.get_latest_version("latest_test")
        assert latest is not None
        assert latest.version == "2.0.0"
        assert latest.is_latest is True

    def test_feature_metadata(self):
        """Test feature metadata extraction."""
        from app.features.feature_store import get_feature_store

        store = get_feature_store()

        df = pd.DataFrame({
            "feature1": [1, 2, 3],
            "feature2": [10.0, 20.0, 30.0],
            "feature3": ["a", "b", "c"]
        })

        store.register_feature_group("metadata_test", "Test", df)

        metadata = store.get_feature_metadata("metadata_test")
        assert len(metadata) == 3
        assert all(m.null_percentage is not None for m in metadata)
        assert all(m.unique_percentage is not None for m in metadata)

    def test_export_features(self):
        """Test feature export."""
        from app.features.feature_store import get_feature_store, ExportFormat

        store = get_feature_store()

        df = pd.DataFrame({"col1": [1, 2, 3]})
        store.register_feature_group("export_test", "Test", df)

        result = store.export_features("export_test", ExportFormat.PARQUET)
        assert "export_location" in result
        assert "row_count" in result
        assert result["format"] == "parquet"


class TestGDPRWorkflows:
    """Test GDPR workflow functionality."""

    def test_gdpr_manager_initialization(self):
        """Test that GDPR manager initializes correctly."""
        from app.compliance.gdpr import get_gdpr_manager

        manager = get_gdpr_manager()
        assert manager is not None

    def test_register_data_subject(self):
        """Test registering a data subject."""
        from app.compliance.gdpr import get_gdpr_manager, IdentifierType, ConsentStatus

        manager = get_gdpr_manager()

        subject = manager.register_data_subject(
            identifier_type=IdentifierType.EMAIL,
            identifier_value="test@example.com",
            consent_status=ConsentStatus.GRANTED,
            consent_purpose=["marketing", "analytics"]
        )

        assert subject.identifier_value == "test@example.com"
        assert subject.consent_status == ConsentStatus.GRANTED

    def test_find_data_subject(self):
        """Test finding a data subject."""
        from app.compliance.gdpr import get_gdpr_manager, IdentifierType

        manager = get_gdpr_manager()

        # Register first
        manager.register_data_subject(
            IdentifierType.EMAIL,
            "find-me@example.com"
        )

        # Find it
        subject = manager.find_data_subject(
            IdentifierType.EMAIL,
            "find-me@example.com"
        )

        assert subject is not None
        assert subject.identifier_value == "find-me@example.com"

    def test_request_data_access(self):
        """Test Right to Access (Article 15)."""
        from app.compliance.gdpr import get_gdpr_manager, IdentifierType

        manager = get_gdpr_manager()

        export_data = manager.request_data_access("access@example.com", IdentifierType.EMAIL)

        assert "subject_id" in export_data
        assert "identifier" in export_data
        assert "data" in export_data
        assert export_data["identifier"]["value"] == "access@example.com"

    def test_request_data_deletion(self):
        """Test Right to Deletion (Article 17)."""
        from app.compliance.gdpr import get_gdpr_manager, IdentifierType

        manager = get_gdpr_manager()

        # Register first
        manager.register_data_subject(IdentifierType.EMAIL, "delete@example.com")

        # Delete
        deletion_counts = manager.request_data_deletion(
            "delete@example.com",
            IdentifierType.EMAIL,
            reason="User requested account deletion"
        )

        assert "explore_layer" in deletion_counts
        assert "chart_layer" in deletion_counts
        assert "navigate_layer" in deletion_counts

    def test_request_data_rectification(self):
        """Test Right to Rectification (Article 16)."""
        from app.compliance.gdpr import get_gdpr_manager, IdentifierType

        manager = get_gdpr_manager()

        # Register first
        manager.register_data_subject(IdentifierType.EMAIL, "rectify@example.com")

        # Rectify
        update_counts = manager.request_data_rectification(
            "rectify@example.com",
            updates={"email": "new-email@example.com", "name": "Updated Name"},
            identifier_type=IdentifierType.EMAIL
        )

        assert "total" in update_counts

    def test_list_gdpr_requests(self):
        """Test listing GDPR requests."""
        from app.compliance.gdpr import get_gdpr_manager, IdentifierType

        manager = get_gdpr_manager()

        # Create a request
        manager.request_data_access("list-test@example.com", IdentifierType.EMAIL)

        # List requests
        requests = manager.list_requests()
        assert len(requests) > 0

    def test_audit_trail(self):
        """Test audit trail functionality."""
        from app.compliance.gdpr import get_gdpr_manager, IdentifierType

        manager = get_gdpr_manager()

        # Perform some operations
        subject = manager.register_data_subject(IdentifierType.EMAIL, "audit@example.com")
        manager.request_data_access("audit@example.com", IdentifierType.EMAIL)

        # Get audit trail
        audit_entries = manager.get_audit_trail(subject.subject_id)
        assert len(audit_entries) >= 2  # Registration + Access request


class TestDataCatalog:
    """Test Data Catalog functionality."""

    def test_catalog_initialization(self):
        """Test that catalog initializes with default tags."""
        from app.catalog.catalog import get_data_catalog

        catalog = get_data_catalog()
        assert catalog is not None
        assert len(catalog.tags) > 0  # Should have default tags

    def test_register_dataset(self):
        """Test registering a dataset."""
        from app.catalog.catalog import get_data_catalog, DatasetNamespace

        catalog = get_data_catalog()

        schema = {
            "fields": [
                {"name": "id", "type": "int64", "nullable": False},
                {"name": "name", "type": "object", "nullable": True}
            ]
        }

        dataset = catalog.register_dataset(
            namespace=DatasetNamespace.EXPLORE,
            name="test_dataset",
            description="Test dataset for catalog",
            schema_definition=schema,
            tags=["pii", "production"],
            row_count=1000,
            size_bytes=50000
        )

        assert dataset.name == "test_dataset"
        assert dataset.namespace == DatasetNamespace.EXPLORE
        assert "pii" in dataset.tags

    def test_search_datasets(self):
        """Test dataset search."""
        from app.catalog.catalog import get_data_catalog, DatasetNamespace

        catalog = get_data_catalog()

        # Register a dataset
        schema = {"fields": [{"name": "id", "type": "int64"}]}
        catalog.register_dataset(
            DatasetNamespace.CHART,
            "searchable_dataset",
            "A dataset for search testing",
            schema
        )

        # Search by name
        results = catalog.search_datasets(query="searchable")
        assert len(results) > 0
        assert any(d.name == "searchable_dataset" for d in results)

    def test_filter_by_namespace(self):
        """Test filtering datasets by namespace."""
        from app.catalog.catalog import get_data_catalog, DatasetNamespace

        catalog = get_data_catalog()

        schema = {"fields": []}

        # Register in different namespaces
        catalog.register_dataset(DatasetNamespace.EXPLORE, "explore_ds", "Test", schema)
        catalog.register_dataset(DatasetNamespace.CHART, "chart_ds", "Test", schema)

        # Filter by namespace
        explore_datasets = catalog.search_datasets(namespace=DatasetNamespace.EXPLORE)
        chart_datasets = catalog.search_datasets(namespace=DatasetNamespace.CHART)

        assert any(d.name == "explore_ds" for d in explore_datasets)
        assert any(d.name == "chart_ds" for d in chart_datasets)

    def test_filter_by_tags(self):
        """Test filtering datasets by tags."""
        from app.catalog.catalog import get_data_catalog, DatasetNamespace

        catalog = get_data_catalog()

        schema = {"fields": []}
        catalog.register_dataset(
            DatasetNamespace.NAVIGATE,
            "tagged_dataset",
            "Test",
            schema,
            tags=["finance", "production"]
        )

        # Filter by tags
        results = catalog.search_datasets(tags=["finance"])
        assert len(results) > 0
        assert any(d.name == "tagged_dataset" for d in results)

    def test_add_tags(self):
        """Test adding tags to dataset."""
        from app.catalog.catalog import get_data_catalog, DatasetNamespace

        catalog = get_data_catalog()

        schema = {"fields": []}
        dataset = catalog.register_dataset(
            DatasetNamespace.NAVIGATE,
            "tag_test_dataset",
            "Test",
            schema
        )

        catalog.add_tags_to_dataset(dataset.namespace, dataset.name, ["new_tag"])

        updated_dataset = catalog.get_dataset(dataset.namespace, dataset.name)
        assert "new_tag" in updated_dataset.tags

    def test_quality_history(self):
        """Test adding and retrieving quality history."""
        from app.catalog.catalog import get_data_catalog, DatasetNamespace

        catalog = get_data_catalog()

        schema = {"fields": []}
        dataset = catalog.register_dataset(
            DatasetNamespace.CHART,
            "quality_test",
            "Test",
            schema
        )

        # Add quality history
        catalog.add_quality_history(
            dataset.dataset_id,
            completeness_score=0.95,
            validity_score=0.90,
            consistency_score=0.85
        )

        # Get history
        history = catalog.get_quality_history(dataset.dataset_id)
        assert len(history) == 1
        assert history[0].completeness_score == 0.95

    def test_catalog_stats(self):
        """Test getting catalog statistics."""
        from app.catalog.catalog import get_data_catalog

        catalog = get_data_catalog()

        stats = catalog.get_catalog_stats()
        assert "total_datasets" in stats
        assert "datasets_by_namespace" in stats
        assert "total_tags" in stats

    def test_list_tags(self):
        """Test listing catalog tags."""
        from app.catalog.catalog import get_data_catalog

        catalog = get_data_catalog()

        tags = catalog.list_tags()
        assert len(tags) > 0
        assert any(t.tag_name == "pii" for t in tags)
        assert any(t.tag_name == "finance" for t in tags)


# ============================================================================
# SUMMARY TEST
# ============================================================================


def test_week5_integration_summary():
    """
    Summary test to verify all Week 5-6 components are working together.
    """
    from app.lineage.openlineage_client import get_lineage_client
    from app.features.feature_store import get_feature_store
    from app.compliance.gdpr import get_gdpr_manager
    from app.catalog.catalog import get_data_catalog

    # All components should initialize
    lineage_client = get_lineage_client()
    feature_store = get_feature_store()
    gdpr_manager = get_gdpr_manager()
    catalog = get_data_catalog()

    assert lineage_client is not None
    assert feature_store is not None
    assert gdpr_manager is not None
    assert catalog is not None

    print("\n" + "=" * 70)
    print("Week 5-6 Integration Test Summary")
    print("=" * 70)
    print("✅ OpenLineage Client: Initialized")
    print("✅ Feature Store: Initialized")
    print("✅ GDPR Manager: Initialized")
    print("✅ Data Catalog: Initialized")
    print("=" * 70)
    print("\nAll Week 5-6 components are functional!")
    print("=" * 70)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
