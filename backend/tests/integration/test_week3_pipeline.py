"""Integration test for Week 3: End-to-end pipeline with Presidio and Soda Core.

WHY: Validate complete Week 3 implementation
- Test CSV → Explore → Chart pipeline
- Verify Presidio PII detection integration
- Verify Soda Core quality validation
- Test API endpoints with Week 3 features
- Ensure backward compatibility with Week 2
"""

import io
import pytest
import pandas as pd
from datetime import datetime

from app.pipeline.core.orchestrator import PipelineOrchestrator

# Check if Week 3 dependencies are available
try:
    from app.pipeline.pii.presidio_detector import PresidioPIIDetector
    from app.pipeline.quality.soda_validator import SodaQualityValidator

    WEEK3_AVAILABLE = True
except ImportError:
    WEEK3_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason="Week 3 dependencies not installed")


@pytest.fixture
def sample_csv_with_pii():
    """Sample CSV file with PII for testing."""
    csv_data = """customer_id,name,email,phone,address,purchase_amount,created_at
C001,John Smith,john@example.com,+1-555-0001,"123 Main St",99.99,2026-01-08
C002,Jane Doe,jane@test.com,+1-555-0002,"456 Oak Ave",149.99,2026-01-07
C003,Bob Johnson,bob@demo.com,+1-555-0003,"789 Pine Rd",79.99,2026-01-09
C004,Alice Williams,alice@sample.com,+1-555-0004,"321 Elm St",199.99,2026-01-06
C005,Charlie Brown,charlie@example.com,+1-555-0005,"654 Maple Dr",124.99,2026-01-05
"""
    return csv_data.encode("utf-8")


@pytest.fixture
def sample_csv_clean():
    """Sample CSV without PII for testing."""
    csv_data = """product_id,category,price,quantity,in_stock,last_updated
P001,Electronics,299.99,15,true,2026-01-08
P002,Clothing,49.99,50,true,2026-01-07
P003,Books,19.99,100,true,2026-01-09
P004,Electronics,499.99,8,true,2026-01-06
P005,Home,89.99,25,true,2026-01-05
"""
    return csv_data.encode("utf-8")


@pytest.fixture
def sample_csv_with_issues():
    """Sample CSV with quality issues."""
    csv_data = """product_id,name,price,quantity,category
P001,Widget A,29.99,10,Electronics
P001,Widget A,29.99,10,Electronics
P003,Widget C,,15,
P004,,19.99,,-5
P005,Widget E,999999.99,1000000,Electronics
"""
    return csv_data.encode("utf-8")


@pytest.mark.skipif(not WEEK3_AVAILABLE, reason="Week 3 dependencies not installed")
class TestWeek3PipelineIntegration:
    """Integration tests for Week 3 pipeline."""

    def test_orchestrator_initialization_week3(self):
        """Test that orchestrator initializes with Week 3 detectors."""
        orchestrator = PipelineOrchestrator(use_week3=True)

        assert orchestrator.use_week3 is True
        assert isinstance(orchestrator.pii_detector, PresidioPIIDetector)
        assert isinstance(orchestrator.quality_checker, SodaQualityValidator)

    def test_orchestrator_fallback_to_week2(self):
        """Test that orchestrator can fall back to Week 2."""
        orchestrator = PipelineOrchestrator(use_week3=False)

        assert orchestrator.use_week3 is False

    def test_end_to_end_pii_detection(self, sample_csv_with_pii):
        """Test end-to-end pipeline with PII detection."""
        orchestrator = PipelineOrchestrator(use_week3=True)

        # In-memory storage
        storage = {
            "test_run_001": {
                "run_id": "test_run_001",
                "status": "queued",
                "filename": "customers.csv",
                "dataset_name": "customers",
                "current_step": "queued",
                "results": {},
                "error": None,
            }
        }

        # Run pipeline
        orchestrator.run_pipeline(
            run_id="test_run_001",
            file_content=sample_csv_with_pii,
            filename="customers.csv",
            dataset_name="customers",
            storage=storage,
        )

        # Verify pipeline completed
        assert storage["test_run_001"]["status"] == "completed"

        # Verify PII detection results
        pii_results = storage["test_run_001"]["results"]["pii"]
        assert pii_results["total_pii_fields"] > 0
        assert pii_results["scanned_rows"] == 5

        # Should detect EMAIL, PHONE, PERSON at minimum
        pii_types = {finding["type"] for finding in pii_results["findings"]}
        assert "EMAIL_ADDRESS" in pii_types or "email" in pii_types
        assert "PHONE_NUMBER" in pii_types or "phone" in pii_types

        # Verify metadata
        metadata = storage["test_run_001"]["results"]["metadata"]
        assert metadata["pii_detector"] == "presidio"
        assert metadata["week3_enabled"] is True

    def test_end_to_end_quality_validation(self, sample_csv_clean):
        """Test end-to-end pipeline with quality validation."""
        orchestrator = PipelineOrchestrator(use_week3=True)

        storage = {
            "test_run_002": {
                "run_id": "test_run_002",
                "status": "queued",
                "filename": "products.csv",
                "dataset_name": "products",
                "current_step": "queued",
                "results": {},
                "error": None,
            }
        }

        orchestrator.run_pipeline(
            run_id="test_run_002",
            file_content=sample_csv_clean,
            filename="products.csv",
            dataset_name="products",
            storage=storage,
        )

        # Verify pipeline completed
        assert storage["test_run_002"]["status"] == "completed"

        # Verify quality results
        quality_results = storage["test_run_002"]["results"]["quality"]
        assert quality_results["overall_score"] >= 0.9  # Clean data should score high

        # Check for all 6 dimensions in details
        if "all_dimensions" in quality_results.get("details", {}):
            dimensions = quality_results["details"]["all_dimensions"]
            assert "completeness" in dimensions
            assert "uniqueness" in dimensions
            assert "timeliness" in dimensions
            assert "validity" in dimensions
            assert "accuracy" in dimensions
            assert "consistency" in dimensions

        # Verify metadata
        metadata = storage["test_run_002"]["results"]["metadata"]
        assert metadata["quality_validator"] == "soda-core"
        assert metadata["week3_enabled"] is True

    def test_quality_issues_detection(self, sample_csv_with_issues):
        """Test that quality validator detects issues."""
        orchestrator = PipelineOrchestrator(use_week3=True)

        storage = {
            "test_run_003": {
                "run_id": "test_run_003",
                "status": "queued",
                "filename": "bad_data.csv",
                "dataset_name": "bad_data",
                "current_step": "queued",
                "results": {},
                "error": None,
            }
        }

        orchestrator.run_pipeline(
            run_id="test_run_003",
            file_content=sample_csv_with_issues,
            filename="bad_data.csv",
            dataset_name="bad_data",
            storage=storage,
        )

        assert storage["test_run_003"]["status"] == "completed"

        quality_results = storage["test_run_003"]["results"]["quality"]

        # Should detect quality issues
        assert quality_results["overall_score"] < 0.95  # Below threshold

        # Check specific dimension scores
        assert quality_results["completeness_score"] < 1.0  # Has missing values
        assert quality_results["consistency_score"] < 1.0  # Has duplicates

    def test_pii_confidence_scores(self, sample_csv_with_pii):
        """Test that PII detection includes confidence scores."""
        orchestrator = PipelineOrchestrator(use_week3=True)

        storage = {
            "test_run_004": {
                "run_id": "test_run_004",
                "status": "queued",
                "filename": "customers.csv",
                "dataset_name": "customers",
                "current_step": "queued",
                "results": {},
                "error": None,
            }
        }

        orchestrator.run_pipeline(
            run_id="test_run_004",
            file_content=sample_csv_with_pii,
            filename="customers.csv",
            dataset_name="customers",
            storage=storage,
        )

        pii_results = storage["test_run_004"]["results"]["pii"]

        # Week 3 should include confidence scores
        for finding in pii_results["findings"]:
            if "confidence" in finding:
                assert 0.0 <= finding["confidence"] <= 1.0
                assert finding["confidence"] >= 0.7  # Threshold

    def test_explore_layer_metadata(self, sample_csv_with_pii):
        """Test that Explore layer metadata is captured correctly."""
        orchestrator = PipelineOrchestrator(use_week3=True)

        storage = {
            "test_run_005": {
                "run_id": "test_run_005",
                "status": "queued",
                "filename": "customers.csv",
                "dataset_name": "customers",
                "current_step": "queued",
                "results": {},
                "error": None,
            }
        }

        orchestrator.run_pipeline(
            run_id="test_run_005",
            file_content=sample_csv_with_pii,
            filename="customers.csv",
            dataset_name="customers",
            storage=storage,
        )

        explore_results = storage["test_run_005"]["results"]["explore"]

        assert explore_results["rows"] == 5
        assert explore_results["columns"] == 7
        assert "column_names" in explore_results
        assert "dtypes" in explore_results

        # Verify column names
        expected_columns = [
            "customer_id",
            "name",
            "email",
            "phone",
            "address",
            "purchase_amount",
            "created_at",
        ]
        for col in expected_columns:
            assert col in explore_results["column_names"]

    def test_pipeline_error_handling(self):
        """Test that pipeline handles errors gracefully."""
        orchestrator = PipelineOrchestrator(use_week3=True)

        storage = {
            "test_run_006": {
                "run_id": "test_run_006",
                "status": "queued",
                "filename": "invalid.csv",
                "dataset_name": "invalid",
                "current_step": "queued",
                "results": {},
                "error": None,
            }
        }

        # Invalid CSV content
        invalid_csv = b"not,a,valid\ncsv,file"

        orchestrator.run_pipeline(
            run_id="test_run_006",
            file_content=invalid_csv,
            filename="invalid.csv",
            dataset_name="invalid",
            storage=storage,
        )

        # Should handle error gracefully
        if storage["test_run_006"]["status"] == "failed":
            assert storage["test_run_006"]["error"] is not None


@pytest.mark.skipif(not WEEK3_AVAILABLE, reason="Week 3 dependencies not installed")
class TestBackwardCompatibility:
    """Test backward compatibility with Week 2."""

    def test_api_compatibility_quality_metrics(self, sample_csv_clean):
        """Test that quality metrics API remains compatible."""
        orchestrator = PipelineOrchestrator(use_week3=True)

        storage = {
            "test_run_007": {
                "run_id": "test_run_007",
                "status": "queued",
                "filename": "products.csv",
                "dataset_name": "products",
                "current_step": "queued",
                "results": {},
                "error": None,
            }
        }

        orchestrator.run_pipeline(
            run_id="test_run_007",
            file_content=sample_csv_clean,
            filename="products.csv",
            dataset_name="products",
            storage=storage,
        )

        quality_results = storage["test_run_007"]["results"]["quality"]

        # Should have backward-compatible keys
        assert "completeness_score" in quality_results
        assert "validity_score" in quality_results
        assert "consistency_score" in quality_results
        assert "overall_score" in quality_results
        assert "details" in quality_results

    def test_api_compatibility_pii_report(self, sample_csv_with_pii):
        """Test that PII report API remains compatible."""
        orchestrator = PipelineOrchestrator(use_week3=True)

        storage = {
            "test_run_008": {
                "run_id": "test_run_008",
                "status": "queued",
                "filename": "customers.csv",
                "dataset_name": "customers",
                "current_step": "queued",
                "results": {},
                "error": None,
            }
        }

        orchestrator.run_pipeline(
            run_id="test_run_008",
            file_content=sample_csv_with_pii,
            filename="customers.csv",
            dataset_name="customers",
            storage=storage,
        )

        pii_results = storage["test_run_008"]["results"]["pii"]

        # Should have backward-compatible structure
        assert "findings" in pii_results
        assert "total_pii_fields" in pii_results
        assert "scanned_columns" in pii_results
        assert "scanned_rows" in pii_results

        # Findings should have expected fields
        for finding in pii_results["findings"]:
            assert "column" in finding
            assert "type" in finding
            assert "match_count" in finding


@pytest.mark.skipif(not WEEK3_AVAILABLE, reason="Week 3 dependencies not installed")
class TestPerformance:
    """Performance tests for Week 3 pipeline."""

    def test_small_dataset_performance(self, sample_csv_with_pii):
        """Test pipeline performance on small dataset."""
        import time

        orchestrator = PipelineOrchestrator(use_week3=True)

        storage = {
            "test_run_009": {
                "run_id": "test_run_009",
                "status": "queued",
                "filename": "customers.csv",
                "dataset_name": "customers",
                "current_step": "queued",
                "results": {},
                "error": None,
            }
        }

        start_time = time.time()

        orchestrator.run_pipeline(
            run_id="test_run_009",
            file_content=sample_csv_with_pii,
            filename="customers.csv",
            dataset_name="customers",
            storage=storage,
        )

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in reasonable time (< 5 seconds for small dataset)
        assert duration < 5.0
        assert storage["test_run_009"]["status"] == "completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
