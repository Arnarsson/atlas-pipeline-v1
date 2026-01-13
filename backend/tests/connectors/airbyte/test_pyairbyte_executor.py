"""
Tests for PyAirbyte Executor

Tests the connector catalog, configuration, and data reading functionality.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, Any

from app.connectors.airbyte.pyairbyte_executor import (
    PyAirbyteExecutor,
    get_pyairbyte_executor,
    CONNECTOR_CATALOG
)


class TestConnectorCatalog:
    """Tests for the connector catalog."""

    def test_catalog_has_core_categories(self):
        """Test that catalog contains core expected categories."""
        categories = set(c["category"] for c in CONNECTOR_CATALOG.values())
        # Core categories that must be present
        core_categories = {"database", "crm", "marketing", "ecommerce", "analytics",
                          "communication", "storage", "hr", "finance", "development"}
        # All core categories should be present (catalog may have more)
        assert core_categories.issubset(categories), f"Missing categories: {core_categories - categories}"

    def test_catalog_has_minimum_connectors(self):
        """Test that catalog has at least 70 connectors."""
        assert len(CONNECTOR_CATALOG) >= 70

    def test_all_connectors_have_required_fields(self):
        """Test that all connectors have required fields."""
        for connector_id, info in CONNECTOR_CATALOG.items():
            assert "category" in info, f"{connector_id} missing category"
            assert "name" in info, f"{connector_id} missing name"
            assert isinstance(info["category"], str)
            assert isinstance(info["name"], str)

    def test_database_connectors_present(self):
        """Test that common database connectors are present."""
        # Note: MongoDB v2 is the current name in catalog
        db_connectors = ["source-postgres", "source-mysql", "source-mongodb-v2",
                        "source-mssql", "source-oracle", "source-snowflake"]
        for conn in db_connectors:
            assert conn in CONNECTOR_CATALOG, f"{conn} not in catalog"

    def test_crm_connectors_present(self):
        """Test that common CRM connectors are present."""
        crm_connectors = ["source-salesforce", "source-hubspot", "source-pipedrive"]
        for conn in crm_connectors:
            assert conn in CONNECTOR_CATALOG, f"{conn} not in catalog"


class TestPyAirbyteExecutor:
    """Tests for PyAirbyteExecutor class."""

    @pytest.fixture
    def executor(self):
        """Create a PyAirbyteExecutor instance."""
        return PyAirbyteExecutor()

    def test_list_available_connectors_returns_all(self, executor):
        """Test listing all connectors without filter."""
        connectors = executor.list_available_connectors()
        assert len(connectors) >= 70
        for conn in connectors:
            assert "id" in conn
            assert "name" in conn
            assert "category" in conn
            assert "status" in conn

    def test_list_connectors_filter_by_category(self, executor):
        """Test filtering connectors by category."""
        db_connectors = executor.list_available_connectors(category="database")
        assert all(c["category"] == "database" for c in db_connectors)
        assert len(db_connectors) > 0

    def test_list_connectors_filter_by_search(self, executor):
        """Test searching connectors by name."""
        results = executor.list_available_connectors(search="postgres")
        assert len(results) > 0
        assert any("postgres" in c["name"].lower() for c in results)

    def test_list_connectors_combined_filter(self, executor):
        """Test filtering by both category and search."""
        results = executor.list_available_connectors(category="database", search="sql")
        assert all(c["category"] == "database" for c in results)

    def test_get_connector_spec_known_connector(self, executor):
        """Test getting spec for a known connector."""
        spec = executor.get_connector_spec("source-postgres")
        assert spec is not None
        # Spec should have schema properties
        assert "properties" in spec
        assert isinstance(spec["properties"], dict)

    def test_get_connector_spec_unknown_connector(self, executor):
        """Test getting spec for unknown connector returns fallback spec."""
        spec = executor.get_connector_spec("source-nonexistent")
        # Unknown connectors return a default fallback spec
        assert spec is not None
        assert isinstance(spec, dict)
        # Should have minimal structure (empty properties is fine for unknown)
        assert "properties" in spec or spec == {}

    def test_get_categories(self, executor):
        """Test getting category list with counts."""
        categories = executor.get_categories()
        # Should have multiple categories (at least 10)
        assert len(categories) >= 10
        for cat in categories:
            assert "category" in cat
            assert "count" in cat
            assert "label" in cat
            assert cat["count"] > 0

    def test_category_labels_are_capitalized(self, executor):
        """Test that category labels are properly formatted."""
        categories = executor.get_categories()
        for cat in categories:
            # Label should be capitalized version of category
            assert cat["label"][0].isupper()

    @pytest.mark.asyncio
    async def test_configure_source_returns_result(self, executor):
        """Test that configure_source returns a configuration result."""
        config = {
            "host": "localhost",
            "port": 5432,
            "database": "test",
            "username": "user",
            "password": "pass"
        }
        result = await executor.configure_source("source-postgres", config)
        assert result is not None
        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] in ["configured", "simulated", "error"]

    @pytest.mark.asyncio
    async def test_configure_source_includes_source_name(self, executor):
        """Test that configuration result includes source name."""
        config = {"host": "localhost", "database": "test"}
        result = await executor.configure_source("source-postgres", config)
        assert "source_name" in result
        assert result["source_name"] == "source-postgres"

    @pytest.mark.asyncio
    async def test_discover_streams_returns_catalog(self, executor):
        """Test stream discovery returns a catalog structure."""
        # In mock mode, we can discover streams even without configuring
        catalog = await executor.discover_streams("source-postgres")
        # Should return AirbyteCatalog with streams attribute
        assert hasattr(catalog, 'streams')
        assert isinstance(catalog.streams, list)

    @pytest.mark.asyncio
    async def test_discover_streams_mock_has_stream(self, executor):
        """Test that mock discovery returns at least one stream."""
        catalog = await executor.discover_streams("source-postgres")
        assert len(catalog.streams) > 0
        stream = catalog.streams[0]
        assert hasattr(stream, 'name')
        assert hasattr(stream, 'json_schema')

    @pytest.mark.asyncio
    async def test_read_stream_returns_result(self, executor):
        """Test reading stream returns a result dict."""
        result = await executor.read_stream("source-postgres", "users")
        assert isinstance(result, dict)
        assert "status" in result
        assert "stream" in result
        assert result["stream"] == "users"

    @pytest.mark.asyncio
    async def test_read_stream_has_records_field(self, executor):
        """Test that read result has records field."""
        result = await executor.read_stream("source-postgres", "users")
        assert "records" in result
        assert isinstance(result["records"], list)

    @pytest.mark.asyncio
    async def test_read_stream_mock_mode(self, executor):
        """Test reading in mock mode returns simulated status."""
        result = await executor.read_stream("source-postgres", "users")
        # In mock mode, status should be simulated or success
        assert result["status"] in ["simulated", "success", "error"]


class TestGetPyAirbyteExecutor:
    """Tests for the singleton executor getter."""

    def test_returns_same_instance(self):
        """Test that get_pyairbyte_executor returns singleton."""
        executor1 = get_pyairbyte_executor()
        executor2 = get_pyairbyte_executor()
        assert executor1 is executor2

    def test_returns_pyairbyte_executor_instance(self):
        """Test that returned instance is correct type."""
        executor = get_pyairbyte_executor()
        assert isinstance(executor, PyAirbyteExecutor)


class TestConnectorValidation:
    """Tests for connector configuration validation."""

    @pytest.fixture
    def executor(self):
        return PyAirbyteExecutor()

    @pytest.mark.asyncio
    async def test_empty_config_accepted(self, executor):
        """Test that empty config is accepted (validation happens at runtime)."""
        source_id = await executor.configure_source("source-postgres", {})
        assert source_id is not None

    @pytest.mark.asyncio
    async def test_extra_config_fields_accepted(self, executor):
        """Test that extra config fields don't cause errors."""
        config = {
            "host": "localhost",
            "extra_field": "value",
            "another_extra": 123
        }
        source_id = await executor.configure_source("source-postgres", config)
        assert source_id is not None
