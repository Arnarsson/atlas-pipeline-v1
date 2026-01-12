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

    def test_catalog_has_expected_categories(self):
        """Test that catalog contains all expected categories."""
        categories = set(c["category"] for c in CONNECTOR_CATALOG.values())
        expected = {"database", "crm", "marketing", "ecommerce", "analytics",
                   "project", "communication", "storage", "hr", "finance", "development"}
        assert categories == expected

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
        db_connectors = ["source-postgres", "source-mysql", "source-mongodb",
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
        assert "connector_name" in spec
        assert spec["connector_name"] == "PostgreSQL"

    def test_get_connector_spec_unknown_connector(self, executor):
        """Test getting spec for unknown connector returns None."""
        spec = executor.get_connector_spec("source-nonexistent")
        assert spec is None

    def test_get_categories(self, executor):
        """Test getting category list with counts."""
        categories = executor.get_categories()
        assert len(categories) == 11
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
    async def test_configure_source_creates_source_id(self, executor):
        """Test that configure_source returns a source ID."""
        config = {
            "host": "localhost",
            "port": 5432,
            "database": "test",
            "username": "user",
            "password": "pass"
        }
        source_id = await executor.configure_source("source-postgres", config)
        assert source_id is not None
        assert isinstance(source_id, str)
        assert source_id.startswith("src_")

    @pytest.mark.asyncio
    async def test_configure_source_stores_config(self, executor):
        """Test that configuration is stored."""
        config = {"host": "localhost", "database": "test"}
        source_id = await executor.configure_source("source-postgres", config)

        assert source_id in executor._configured_sources
        stored = executor._configured_sources[source_id]
        assert stored["connector_id"] == "source-postgres"
        assert stored["config"] == config

    @pytest.mark.asyncio
    async def test_discover_streams_returns_mock_streams(self, executor):
        """Test stream discovery returns expected structure."""
        config = {"host": "localhost"}
        source_id = await executor.configure_source("source-postgres", config)
        streams = await executor.discover_streams(source_id)

        assert isinstance(streams, list)
        assert len(streams) > 0
        for stream in streams:
            assert "name" in stream
            assert "json_schema" in stream

    @pytest.mark.asyncio
    async def test_discover_streams_invalid_source(self, executor):
        """Test discovery with invalid source raises error."""
        with pytest.raises(ValueError, match="Source .* not found"):
            await executor.discover_streams("invalid_source_id")

    @pytest.mark.asyncio
    async def test_read_stream_returns_data(self, executor):
        """Test reading stream returns data records."""
        config = {"host": "localhost"}
        source_id = await executor.configure_source("source-postgres", config)

        records = await executor.read_stream(source_id, "users")
        assert isinstance(records, list)
        assert len(records) > 0
        for record in records:
            assert isinstance(record, dict)

    @pytest.mark.asyncio
    async def test_read_stream_respects_limit(self, executor):
        """Test that limit parameter is respected."""
        config = {"host": "localhost"}
        source_id = await executor.configure_source("source-postgres", config)

        records = await executor.read_stream(source_id, "users", limit=5)
        assert len(records) <= 5

    @pytest.mark.asyncio
    async def test_read_stream_invalid_source(self, executor):
        """Test reading from invalid source raises error."""
        with pytest.raises(ValueError, match="Source .* not found"):
            await executor.read_stream("invalid_id", "users")


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
