"""Connector registry for managing available data source connectors."""

from typing import Dict, List, Type
import logging

from app.connectors.base import SourceConnector

logger = logging.getLogger(__name__)

# Optional connectors with graceful fallback
MySQLConnector = None
PostgreSQLConnector = None
RESTAPIConnector = None
GoogleSheetsConnector = None
SalesforceConnector = None
KafkaConsumerConnector = None

try:
    from app.connectors.mysql import MySQLConnector
except (ImportError, Exception) as e:
    logger.warning(f"MySQL connector not available: {e}")

try:
    from app.connectors.postgresql import PostgreSQLConnector
except (ImportError, Exception) as e:
    logger.warning(f"PostgreSQL connector not available: {e}")

try:
    from app.connectors.rest_api import RESTAPIConnector
except (ImportError, Exception) as e:
    logger.warning(f"REST API connector not available: {e}")

try:
    from app.connectors.google_sheets import GoogleSheetsConnector
except (ImportError, Exception) as e:
    logger.warning(f"Google Sheets connector not available: {e}")

try:
    from app.connectors.salesforce import SalesforceConnector
except (ImportError, Exception) as e:
    logger.warning(f"Salesforce connector not available: {e}")

try:
    from app.connectors.kafka import KafkaConsumerConnector
except ImportError as e:
    logger.warning(f"Kafka connector not available: {e}")


class ConnectorRegistry:
    """Registry for all available data source connectors.

    Provides a centralized way to:
    - Discover available connector types
    - Instantiate connectors by type
    - Validate connector configurations
    """

    _connectors: Dict[str, Type[SourceConnector]] = {}

    # Add connectors if available
    if PostgreSQLConnector is not None:
        _connectors["postgresql"] = PostgreSQLConnector
    if MySQLConnector is not None:
        _connectors["mysql"] = MySQLConnector
    if RESTAPIConnector is not None:
        _connectors["rest_api"] = RESTAPIConnector
    if GoogleSheetsConnector is not None:
        _connectors["google_sheets"] = GoogleSheetsConnector
    if SalesforceConnector is not None:
        _connectors["salesforce"] = SalesforceConnector
    if KafkaConsumerConnector is not None:
        _connectors["kafka"] = KafkaConsumerConnector

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
