"""
Tests for AtlasIntelligence API Endpoints

Tests the complete API surface for the connector platform.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Import the router
from app.api.routes.atlas_intelligence import router


@pytest.fixture
def app():
    """Create a test FastAPI app."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_endpoint(self, client):
        """Test the main health endpoint."""
        response = client.get("/atlas-intelligence/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]

    def test_pyairbyte_health(self, client):
        """Test PyAirbyte health endpoint."""
        response = client.get("/atlas-intelligence/pyairbyte/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "pyairbyte_installed" in data


class TestMCPConnectorEndpoints:
    """Tests for MCP connector endpoints."""

    def test_list_connectors(self, client):
        """Test listing MCP connectors."""
        response = client.get("/atlas-intelligence/connectors")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least some connectors
        assert len(data) > 0
        # Check structure
        if len(data) > 0:
            assert "id" in data[0]
            assert "description" in data[0]

    def test_get_connector_entities(self, client):
        """Test getting connector entities."""
        response = client.get("/atlas-intelligence/connectors/github/entities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestPyAirbyteEndpoints:
    """Tests for PyAirbyte connector endpoints."""

    def test_list_pyairbyte_connectors(self, client):
        """Test listing PyAirbyte connectors."""
        response = client.get("/atlas-intelligence/pyairbyte/connectors")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 70  # Should have 70+ connectors

    def test_list_connectors_by_category(self, client):
        """Test filtering connectors by category."""
        response = client.get("/atlas-intelligence/pyairbyte/connectors?category=database")
        assert response.status_code == 200
        data = response.json()
        assert all(c["category"] == "database" for c in data)

    def test_list_connectors_by_search(self, client):
        """Test searching connectors."""
        response = client.get("/atlas-intelligence/pyairbyte/connectors?search=postgres")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert any("postgres" in c["name"].lower() for c in data)

    def test_get_categories(self, client):
        """Test getting connector categories."""
        response = client.get("/atlas-intelligence/pyairbyte/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 11  # 11 categories
        # Check structure
        for cat in data:
            assert "category" in cat
            assert "count" in cat
            assert "label" in cat

    def test_get_connector_spec(self, client):
        """Test getting connector specification."""
        response = client.get("/atlas-intelligence/pyairbyte/spec/source-postgres")
        assert response.status_code == 200
        data = response.json()
        assert "connector_name" in data

    def test_get_connector_spec_not_found(self, client):
        """Test getting spec for non-existent connector."""
        response = client.get("/atlas-intelligence/pyairbyte/spec/source-nonexistent")
        assert response.status_code == 404

    def test_configure_connector(self, client):
        """Test configuring a connector."""
        payload = {
            "connector_id": "source-postgres",
            "config": {
                "host": "localhost",
                "port": 5432,
                "database": "test"
            }
        }
        response = client.post("/atlas-intelligence/pyairbyte/configure", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "source_id" in data
        assert data["source_id"].startswith("src_")

    def test_discover_streams(self, client):
        """Test discovering streams for a configured source."""
        # First configure a source
        config_response = client.post(
            "/atlas-intelligence/pyairbyte/configure",
            json={"connector_id": "source-postgres", "config": {"host": "localhost"}}
        )
        source_id = config_response.json()["source_id"]

        # Then discover streams
        response = client.get(f"/atlas-intelligence/pyairbyte/discover/{source_id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_read_stream(self, client):
        """Test reading data from a stream."""
        # First configure a source
        config_response = client.post(
            "/atlas-intelligence/pyairbyte/configure",
            json={"connector_id": "source-postgres", "config": {"host": "localhost"}}
        )
        source_id = config_response.json()["source_id"]

        # Then read a stream
        response = client.get(f"/atlas-intelligence/pyairbyte/read/{source_id}/users")
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert isinstance(data["records"], list)


class TestCredentialEndpoints:
    """Tests for credential management endpoints."""

    def test_get_credentials(self, client):
        """Test getting credential status."""
        response = client.get("/atlas-intelligence/credentials")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_set_credential(self, client):
        """Test setting a credential."""
        payload = {
            "connector_id": "github",
            "api_key": "test_api_key_12345"
        }
        response = client.post("/atlas-intelligence/credentials", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "saved"


class TestStateEndpoints:
    """Tests for state management endpoints."""

    def test_list_source_states(self, client):
        """Test listing source states."""
        response = client.get("/atlas-intelligence/state/sources")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_source_state(self, client):
        """Test creating a source state."""
        payload = {
            "source_id": "test_src_001",
            "source_name": "Test Source",
            "streams": ["users", "orders"]
        }
        response = client.post("/atlas-intelligence/state/sources", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["source_id"] == "test_src_001"

    def test_get_source_state(self, client):
        """Test getting a specific source state."""
        # Create first
        client.post(
            "/atlas-intelligence/state/sources",
            json={"source_id": "get_test", "source_name": "Get Test", "streams": ["data"]}
        )

        response = client.get("/atlas-intelligence/state/sources/get_test")
        assert response.status_code == 200
        data = response.json()
        assert data["source_id"] == "get_test"

    def test_get_source_state_not_found(self, client):
        """Test getting non-existent source state."""
        response = client.get("/atlas-intelligence/state/sources/nonexistent")
        assert response.status_code == 404

    def test_update_stream_state(self, client):
        """Test updating stream state."""
        # Create source first
        client.post(
            "/atlas-intelligence/state/sources",
            json={"source_id": "update_test", "source_name": "Update Test", "streams": ["events"]}
        )

        payload = {
            "stream_name": "events",
            "cursor_field": "timestamp",
            "cursor_value": "2024-01-15T00:00:00Z",
            "records_synced": 1000
        }
        response = client.put(
            "/atlas-intelligence/state/sources/update_test/streams",
            json=payload
        )
        assert response.status_code == 200

    def test_reset_source_state(self, client):
        """Test resetting source state."""
        # Create source first
        client.post(
            "/atlas-intelligence/state/sources",
            json={"source_id": "reset_test", "source_name": "Reset Test", "streams": ["data"]}
        )

        response = client.post("/atlas-intelligence/state/sources/reset_test/reset")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reset"

    def test_export_state(self, client):
        """Test exporting all state."""
        response = client.get("/atlas-intelligence/state/export")
        assert response.status_code == 200
        data = response.json()
        assert "sources" in data

    def test_import_state(self, client):
        """Test importing state."""
        payload = {
            "sources": {
                "import_test": {
                    "source_id": "import_test",
                    "source_name": "Imported",
                    "streams": {},
                    "total_records_synced": 0
                }
            }
        }
        response = client.post("/atlas-intelligence/state/import", json=payload)
        assert response.status_code == 200


class TestSyncEndpoints:
    """Tests for sync job endpoints."""

    def test_get_sync_stats(self, client):
        """Test getting sync statistics."""
        response = client.get("/atlas-intelligence/sync/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_jobs" in data
        assert "running_jobs" in data
        assert "completed_jobs" in data
        assert "failed_jobs" in data

    def test_create_sync_job(self, client):
        """Test creating a sync job."""
        payload = {
            "source_id": "src_001",
            "source_name": "Test Source",
            "streams": ["users", "orders"],
            "sync_mode": "full_refresh"
        }
        response = client.post("/atlas-intelligence/sync/jobs", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["job_id"].startswith("job_")
        assert data["status"] == "pending"

    def test_get_sync_job(self, client):
        """Test getting a specific sync job."""
        # Create first
        create_response = client.post(
            "/atlas-intelligence/sync/jobs",
            json={"source_id": "src", "source_name": "name", "streams": ["s"]}
        )
        job_id = create_response.json()["job_id"]

        response = client.get(f"/atlas-intelligence/sync/jobs/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id

    def test_get_sync_job_not_found(self, client):
        """Test getting non-existent job."""
        response = client.get("/atlas-intelligence/sync/jobs/nonexistent")
        assert response.status_code == 404

    def test_list_sync_jobs(self, client):
        """Test listing sync jobs."""
        response = client.get("/atlas-intelligence/sync/jobs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_sync_jobs_with_limit(self, client):
        """Test listing jobs with limit."""
        # Create multiple jobs
        for i in range(5):
            client.post(
                "/atlas-intelligence/sync/jobs",
                json={"source_id": f"src_{i}", "source_name": f"name_{i}", "streams": ["s"]}
            )

        response = client.get("/atlas-intelligence/sync/jobs?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3

    def test_get_running_jobs(self, client):
        """Test getting running jobs."""
        response = client.get("/atlas-intelligence/sync/running")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestScheduleEndpoints:
    """Tests for schedule management endpoints."""

    def test_create_schedule(self, client):
        """Test creating a schedule."""
        payload = {
            "source_id": "src_001",
            "source_name": "Scheduled Source",
            "streams": ["data"],
            "cron_expression": "0 * * * *",
            "sync_mode": "incremental"
        }
        response = client.post("/atlas-intelligence/sync/schedules", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "schedule_id" in data
        assert data["enabled"] is True

    def test_list_schedules(self, client):
        """Test listing schedules."""
        response = client.get("/atlas-intelligence/sync/schedules")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_schedule(self, client):
        """Test getting a specific schedule."""
        # Create first
        create_response = client.post(
            "/atlas-intelligence/sync/schedules",
            json={
                "source_id": "src",
                "source_name": "name",
                "streams": ["s"],
                "cron_expression": "0 * * * *"
            }
        )
        schedule_id = create_response.json()["schedule_id"]

        response = client.get(f"/atlas-intelligence/sync/schedules/{schedule_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["schedule_id"] == schedule_id

    def test_update_schedule(self, client):
        """Test updating a schedule."""
        # Create first
        create_response = client.post(
            "/atlas-intelligence/sync/schedules",
            json={
                "source_id": "src",
                "source_name": "name",
                "streams": ["s"],
                "cron_expression": "0 * * * *"
            }
        )
        schedule_id = create_response.json()["schedule_id"]

        response = client.put(
            f"/atlas-intelligence/sync/schedules/{schedule_id}",
            json={"enabled": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False

    def test_delete_schedule(self, client):
        """Test deleting a schedule."""
        # Create first
        create_response = client.post(
            "/atlas-intelligence/sync/schedules",
            json={
                "source_id": "src",
                "source_name": "name",
                "streams": ["s"],
                "cron_expression": "0 * * * *"
            }
        )
        schedule_id = create_response.json()["schedule_id"]

        response = client.delete(f"/atlas-intelligence/sync/schedules/{schedule_id}")
        assert response.status_code == 200

        # Verify deleted
        get_response = client.get(f"/atlas-intelligence/sync/schedules/{schedule_id}")
        assert get_response.status_code == 404


class TestStatsEndpoint:
    """Tests for platform statistics endpoint."""

    def test_get_platform_stats(self, client):
        """Test getting overall platform statistics."""
        response = client.get("/atlas-intelligence/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_available" in data
        assert "mcp_connectors" in data
        assert "pyairbyte_connectors" in data


class TestUnifiedSearch:
    """Tests for unified search across connector types."""

    def test_search_all_connectors(self, client):
        """Test searching across all connector types."""
        response = client.get("/atlas-intelligence/search?q=postgres")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
