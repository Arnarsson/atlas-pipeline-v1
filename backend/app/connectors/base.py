"""Base connector interface for all data sources."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from pydantic import BaseModel, Field


class ConnectionConfig(BaseModel):
    """Base configuration for data source connections."""

    source_type: str = Field(..., description="Type of data source (postgresql, mysql, rest_api)")
    source_name: str = Field(..., description="Unique name for this connection")
    connection_string: Optional[str] = Field(None, description="Full connection string")

    # Database connection params
    host: Optional[str] = Field(None, description="Database host")
    port: Optional[int] = Field(None, description="Database port")
    database: Optional[str] = Field(None, description="Database name")
    username: Optional[str] = Field(None, description="Database username")
    password: Optional[str] = Field(None, description="Database password (encrypted)")

    # REST API params
    base_url: Optional[str] = Field(None, description="Base URL for REST API")
    auth_type: Optional[str] = Field(None, description="Authentication type (bearer, apikey, basic, oauth2)")
    auth_token: Optional[str] = Field(None, description="Authentication token")
    api_key: Optional[str] = Field(None, description="API key")

    # Additional configuration
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="Additional connector-specific params")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "source_type": "postgresql",
                "source_name": "production_db",
                "host": "localhost",
                "port": 5432,
                "database": "mydb",
                "username": "user",
                "password": "encrypted_password",
                "additional_params": {"sslmode": "require"}
            }
        }


class SourceConnector(ABC):
    """Base class for all data source connectors.

    All connectors must implement:
    - Connection testing
    - Data retrieval (full and incremental)
    - Schema inspection
    - Row counting
    """

    def __init__(self, config: ConnectionConfig):
        """Initialize connector with configuration.

        Args:
            config: Connection configuration
        """
        self.config = config
        self.last_sync_timestamp: Optional[datetime] = None
        self._connection = None

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if connection is valid and accessible.

        Returns:
            True if connection successful, False otherwise

        Raises:
            ConnectionError: If connection fails with details
        """
        pass

    @abstractmethod
    async def get_data(
        self,
        query: Optional[str] = None,
        table: Optional[str] = None,
        incremental: bool = False,
        timestamp_column: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """Fetch data from source.

        Args:
            query: Custom SQL query or API endpoint
            table: Table name to fetch from
            incremental: Whether to fetch only new/updated records
            timestamp_column: Column to use for incremental loading
            filters: Additional filters to apply

        Returns:
            DataFrame with fetched data

        Raises:
            ValueError: If neither query nor table is provided
            ConnectionError: If data fetch fails
        """
        pass

    @abstractmethod
    async def get_schema(self, table: str) -> Dict[str, str]:
        """Get table schema information.

        Args:
            table: Table name

        Returns:
            Dictionary mapping column names to data types

        Raises:
            ValueError: If table doesn't exist
        """
        pass

    @abstractmethod
    async def get_row_count(
        self,
        table: str,
        where: Optional[str] = None
    ) -> int:
        """Get row count for a table.

        Args:
            table: Table name
            where: Optional WHERE clause

        Returns:
            Number of rows

        Raises:
            ValueError: If table doesn't exist
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connection and cleanup resources."""
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
