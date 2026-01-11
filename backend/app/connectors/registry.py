"""Connector registry for managing available data source connectors."""

from typing import Dict, List, Type

from app.connectors.base import SourceConnector
from app.connectors.google_sheets import GoogleSheetsConnector
from app.connectors.mysql import MySQLConnector
from app.connectors.postgresql import PostgreSQLConnector
from app.connectors.rest_api import RESTAPIConnector
from app.connectors.salesforce import SalesforceConnector


class ConnectorRegistry:
    """Registry for all available data source connectors.

    Provides a centralized way to:
    - Discover available connector types
    - Instantiate connectors by type
    - Validate connector configurations
    """

    _connectors: Dict[str, Type[SourceConnector]] = {
        "postgresql": PostgreSQLConnector,
        "mysql": MySQLConnector,
        "rest_api": RESTAPIConnector,
        "google_sheets": GoogleSheetsConnector,
        "salesforce": SalesforceConnector,
    }

    @classmethod
    def get_connector(cls, source_type: str) -> Type[SourceConnector]:
        """Get connector class by type.

        Args:
            source_type: Type of connector (postgresql, mysql, rest_api)

        Returns:
            Connector class

        Raises:
            ValueError: If connector type is not registered
        """
        if source_type not in cls._connectors:
            available = ", ".join(cls._connectors.keys())
            raise ValueError(
                f"Unknown connector type: '{source_type}'. "
                f"Available types: {available}"
            )
        return cls._connectors[source_type]

    @classmethod
    def list_connectors(cls) -> List[str]:
        """List all available connector types.

        Returns:
            List of connector type names
        """
        return list(cls._connectors.keys())

    @classmethod
    def register_connector(
        cls,
        source_type: str,
        connector_class: Type[SourceConnector]
    ) -> None:
        """Register a new connector type.

        Args:
            source_type: Unique identifier for connector type
            connector_class: Connector class implementation

        Raises:
            ValueError: If connector type already registered
        """
        if source_type in cls._connectors:
            raise ValueError(f"Connector type '{source_type}' already registered")

        cls._connectors[source_type] = connector_class

    @classmethod
    def is_registered(cls, source_type: str) -> bool:
        """Check if connector type is registered.

        Args:
            source_type: Connector type to check

        Returns:
            True if registered, False otherwise
        """
        return source_type in cls._connectors
