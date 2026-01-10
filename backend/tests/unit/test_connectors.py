"""Unit tests for data source connectors."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.connectors.base import ConnectionConfig
from app.connectors.postgresql import PostgreSQLConnector
from app.connectors.mysql import MySQLConnector
from app.connectors.rest_api import RESTAPIConnector
from app.connectors.registry import ConnectorRegistry


class TestConnectionConfig:
    """Test ConnectionConfig model."""

    def test_postgresql_config(self):
        """Test PostgreSQL configuration."""
        config = ConnectionConfig(
            source_type="postgresql",
            source_name="test_db",
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="password",
        )

        assert config.source_type == "postgresql"
        assert config.host == "localhost"
        assert config.port == 5432

    def test_mysql_config(self):
        """Test MySQL configuration."""
        config = ConnectionConfig(
            source_type="mysql",
            source_name="test_db",
            host="localhost",
            port=3306,
            database="testdb",
            username="user",
            password="password",
        )

        assert config.source_type == "mysql"
        assert config.port == 3306

    def test_rest_api_config(self):
        """Test REST API configuration."""
        config = ConnectionConfig(
            source_type="rest_api",
            source_name="test_api",
            base_url="https://api.example.com",
            auth_type="bearer",
            auth_token="test_token",
            additional_params={"pagination_type": "offset"}
        )

        assert config.source_type == "rest_api"
        assert config.base_url == "https://api.example.com"
        assert config.auth_type == "bearer"


class TestConnectorRegistry:
    """Test ConnectorRegistry."""

    def test_list_connectors(self):
        """Test listing all connector types."""
        types = ConnectorRegistry.list_connectors()

        assert "postgresql" in types
        assert "mysql" in types
        assert "rest_api" in types

    def test_get_connector(self):
        """Test getting connector class."""
        connector_class = ConnectorRegistry.get_connector("postgresql")
        assert connector_class == PostgreSQLConnector

        connector_class = ConnectorRegistry.get_connector("mysql")
        assert connector_class == MySQLConnector

        connector_class = ConnectorRegistry.get_connector("rest_api")
        assert connector_class == RESTAPIConnector

    def test_get_unknown_connector(self):
        """Test getting unknown connector raises error."""
        with pytest.raises(ValueError, match="Unknown connector type"):
            ConnectorRegistry.get_connector("unknown")

    def test_is_registered(self):
        """Test checking if connector is registered."""
        assert ConnectorRegistry.is_registered("postgresql") is True
        assert ConnectorRegistry.is_registered("unknown") is False


@pytest.mark.asyncio
class TestPostgreSQLConnector:
    """Test PostgreSQL connector."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return ConnectionConfig(
            source_type="postgresql",
            source_name="test_db",
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="password",
        )

    @pytest.fixture
    def connector(self, config):
        """Create connector instance."""
        return PostgreSQLConnector(config)

    async def test_init(self, connector, config):
        """Test connector initialization."""
        assert connector.config == config
        assert connector._pool is None
        assert connector._max_retries == 3

    @patch("asyncpg.create_pool")
    async def test_test_connection_success(self, mock_pool, connector):
        """Test successful connection test."""
        # Mock pool and connection
        mock_conn = AsyncMock()
        mock_conn.fetchval.return_value = 1

        mock_pool_instance = AsyncMock()
        mock_pool_instance.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        result = await connector.test_connection()

        assert result is True
        mock_pool.assert_called_once()

    @patch("asyncpg.create_pool")
    async def test_get_data_with_table(self, mock_pool, connector):
        """Test fetching data from table."""
        # Mock data
        mock_rows = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]

        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [MagicMock(**row) for row in mock_rows]

        mock_pool_instance = AsyncMock()
        mock_pool_instance.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        df = await connector.get_data(table="users")

        assert len(df) == 2
        assert "id" in df.columns
        assert "name" in df.columns


@pytest.mark.asyncio
class TestMySQLConnector:
    """Test MySQL connector."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return ConnectionConfig(
            source_type="mysql",
            source_name="test_db",
            host="localhost",
            port=3306,
            database="testdb",
            username="user",
            password="password",
        )

    @pytest.fixture
    def connector(self, config):
        """Create connector instance."""
        return MySQLConnector(config)

    async def test_init(self, connector, config):
        """Test connector initialization."""
        assert connector.config == config
        assert connector._pool is None


@pytest.mark.asyncio
class TestRESTAPIConnector:
    """Test REST API connector."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return ConnectionConfig(
            source_type="rest_api",
            source_name="test_api",
            base_url="https://api.example.com",
            auth_type="bearer",
            auth_token="test_token",
            additional_params={"pagination_type": "none"}
        )

    @pytest.fixture
    def connector(self, config):
        """Create connector instance."""
        return RESTAPIConnector(config)

    async def test_init(self, connector, config):
        """Test connector initialization."""
        assert connector.config == config
        assert connector._client is None

    def test_auth_headers_bearer(self, connector):
        """Test bearer authentication headers."""
        headers = connector._get_auth_headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_token"

    async def test_auth_headers_apikey(self):
        """Test API key authentication headers."""
        config = ConnectionConfig(
            source_type="rest_api",
            source_name="test_api",
            base_url="https://api.example.com",
            auth_type="apikey",
            api_key="test_key",
        )
        connector = RESTAPIConnector(config)
        headers = connector._get_auth_headers()

        assert "X-API-Key" in headers
        assert headers["X-API-Key"] == "test_key"
