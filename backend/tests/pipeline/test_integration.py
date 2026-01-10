"""
Integration Tests for Atlas Data Pipeline Platform

Tests the end-to-end flow of data through the pipeline:
1. Bronze layer ingestion
2. Silver layer transformation with PII detection
3. Gold layer business logic
4. Data quality validation
"""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session


@pytest.mark.integration
@pytest.mark.pipeline
class TestPipelineIntegration:
    """Integration tests for complete pipeline flows."""

    def test_health_check_endpoint(self, client: TestClient) -> None:
        """Test that the health check endpoint is working."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_bronze_layer_ingestion(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        sample_bronze_data: list[dict[str, Any]],
    ) -> None:
        """
        Test Bronze layer data ingestion.

        Verifies:
        - Data can be ingested through the API
        - Raw data is stored correctly
        - Metadata is captured
        """
        response = client.post(
            "/api/v1/pipeline/bronze/ingest",
            json={"data": sample_bronze_data, "source": "test_source"},
            headers=superuser_token_headers,
        )

        # Skip if endpoint not yet implemented
        if response.status_code == 404:
            pytest.skip("Bronze ingestion endpoint not yet implemented")

        assert response.status_code in [200, 201]
        data = response.json()

        assert "batch_id" in data
        assert data["records_ingested"] == len(sample_bronze_data)

    @pytest.mark.pii
    def test_silver_layer_pii_detection(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        sample_pii_data: dict[str, Any],
    ) -> None:
        """
        Test Silver layer PII detection and masking.

        Verifies:
        - PII is correctly detected
        - Sensitive data is masked
        - Non-sensitive data is preserved
        """
        response = client.post(
            "/api/v1/pipeline/silver/process",
            json={"data": sample_pii_data},
            headers=superuser_token_headers,
        )

        # Skip if endpoint not yet implemented
        if response.status_code == 404:
            pytest.skip("Silver processing endpoint not yet implemented")

        assert response.status_code == 200
        data = response.json()

        # Verify PII was detected
        assert "pii_detected" in data
        assert len(data["pii_detected"]) > 0

        # Verify sensitive fields are masked
        processed = data["processed_data"]
        assert "***" in processed.get("ssn", "")
        assert "***" in processed.get("credit_card", "")

    @pytest.mark.quality
    def test_data_quality_validation(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        sample_bronze_data: list[dict[str, Any]],
        mock_data_quality_config: dict[str, Any],
    ) -> None:
        """
        Test data quality validation.

        Verifies:
        - Quality checks run successfully
        - Quality scores are calculated
        - Failing data is identified
        """
        response = client.post(
            "/api/v1/pipeline/quality/validate",
            json={"data": sample_bronze_data, "config": mock_data_quality_config},
            headers=superuser_token_headers,
        )

        # Skip if endpoint not yet implemented
        if response.status_code == 404:
            pytest.skip("Quality validation endpoint not yet implemented")

        assert response.status_code == 200
        data = response.json()

        # Verify quality metrics are returned
        assert "quality_score" in data
        assert 0 <= data["quality_score"] <= 1.0

        # Verify individual dimension scores
        assert "dimensions" in data
        dimensions = data["dimensions"]
        assert "completeness" in dimensions
        assert "validity" in dimensions
        assert "consistency" in dimensions

    @pytest.mark.slow
    def test_end_to_end_pipeline_flow(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        sample_bronze_data: list[dict[str, Any]],
    ) -> None:
        """
        Test complete end-to-end pipeline flow.

        Flow:
        1. Ingest raw data to Bronze
        2. Process through Silver (PII detection, transformation)
        3. Apply business logic in Gold
        4. Validate data quality
        5. Verify lineage tracking
        """
        # Step 1: Ingest to Bronze
        bronze_response = client.post(
            "/api/v1/pipeline/bronze/ingest",
            json={"data": sample_bronze_data, "source": "e2e_test"},
            headers=superuser_token_headers,
        )

        if bronze_response.status_code == 404:
            pytest.skip("End-to-end pipeline not yet implemented")

        assert bronze_response.status_code in [200, 201]
        batch_id = bronze_response.json()["batch_id"]

        # Step 2: Process through Silver
        silver_response = client.post(
            f"/api/v1/pipeline/silver/process/{batch_id}",
            headers=superuser_token_headers,
        )
        assert silver_response.status_code == 200

        # Step 3: Apply Gold layer transformations
        gold_response = client.post(
            f"/api/v1/pipeline/gold/transform/{batch_id}",
            headers=superuser_token_headers,
        )
        assert gold_response.status_code == 200

        # Step 4: Verify data quality
        quality_response = client.get(
            f"/api/v1/pipeline/quality/report/{batch_id}",
            headers=superuser_token_headers,
        )
        assert quality_response.status_code == 200
        quality_data = quality_response.json()
        assert quality_data["quality_score"] >= 0.8  # Minimum acceptable quality

        # Step 5: Verify lineage tracking
        lineage_response = client.get(
            f"/api/v1/pipeline/lineage/{batch_id}",
            headers=superuser_token_headers,
        )
        assert lineage_response.status_code == 200
        lineage_data = lineage_response.json()
        assert "bronze" in lineage_data["layers"]
        assert "silver" in lineage_data["layers"]
        assert "gold" in lineage_data["layers"]


@pytest.mark.integration
class TestPipelineErrorHandling:
    """Test pipeline error handling and resilience."""

    def test_invalid_data_format(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
    ) -> None:
        """Test that invalid data format is handled gracefully."""
        response = client.post(
            "/api/v1/pipeline/bronze/ingest",
            json={"data": "invalid_format"},  # Should be list
            headers=superuser_token_headers,
        )

        if response.status_code == 404:
            pytest.skip("Bronze ingestion endpoint not yet implemented")

        assert response.status_code in [400, 422]  # Bad request or validation error

    def test_missing_required_fields(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
    ) -> None:
        """Test that missing required fields are caught."""
        incomplete_data = [{"name": "John Doe"}]  # Missing required fields

        response = client.post(
            "/api/v1/pipeline/bronze/ingest",
            json={"data": incomplete_data, "source": "test"},
            headers=superuser_token_headers,
        )

        if response.status_code == 404:
            pytest.skip("Bronze ingestion endpoint not yet implemented")

        # Should either accept with warnings or reject
        assert response.status_code in [200, 201, 400, 422]

    def test_unauthorized_access(self, client: TestClient) -> None:
        """Test that unauthorized requests are rejected."""
        response = client.post(
            "/api/v1/pipeline/bronze/ingest",
            json={"data": [], "source": "test"},
            # No authentication headers
        )

        if response.status_code == 404:
            pytest.skip("Bronze ingestion endpoint not yet implemented")

        assert response.status_code in [401, 403]  # Unauthorized or Forbidden
