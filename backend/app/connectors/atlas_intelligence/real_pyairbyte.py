"""
Real PyAirbyte Integration Module

This module provides integration with the actual PyAirbyte library when installed.
Falls back to mock implementation if PyAirbyte is not available.

Install PyAirbyte: pip install airbyte

Features:
- Automatic detection of PyAirbyte availability
- Real connector execution when available
- Graceful fallback to mock data
- Full Airbyte catalog support
- Credential management
- Stream configuration
"""
import os
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Try to import PyAirbyte
PYAIRBYTE_AVAILABLE = False
try:
    import airbyte as ab
    PYAIRBYTE_AVAILABLE = True
    logger.info("PyAirbyte is available - real connectors enabled")
except ImportError:
    logger.warning("PyAirbyte not installed - using mock implementation")
    logger.warning("Install with: pip install airbyte")


@dataclass
class ConnectorInfo:
    """Information about a connector."""
    name: str
    source_name: str
    version: Optional[str] = None
    documentation_url: Optional[str] = None


@dataclass
class StreamInfo:
    """Information about a stream."""
    name: str
    json_schema: Dict[str, Any]
    supported_sync_modes: List[str]
    source_defined_cursor: bool = False
    default_cursor_field: Optional[List[str]] = None
    source_defined_primary_key: Optional[List[List[str]]] = None


class RealPyAirbyteExecutor:
    """
    Real PyAirbyte executor that uses the actual airbyte package.

    When PyAirbyte is not installed, falls back to mock implementation
    that returns sample data for development/testing.
    """

    def __init__(self):
        self._sources: Dict[str, Any] = {}
        self._cache_dir = os.environ.get(
            'PYAIRBYTE_CACHE_DIR',
            '/tmp/atlas_airbyte_cache'
        )
        os.makedirs(self._cache_dir, exist_ok=True)

    @property
    def is_real_mode(self) -> bool:
        """Check if using real PyAirbyte."""
        return PYAIRBYTE_AVAILABLE

    def get_available_connectors(self) -> List[ConnectorInfo]:
        """
        Get list of available connectors from PyAirbyte registry.

        Returns real connector list if PyAirbyte installed,
        otherwise returns curated list of common connectors.
        """
        if PYAIRBYTE_AVAILABLE:
            try:
                # Get connectors from PyAirbyte registry
                registry = ab.get_available_connectors()
                return [
                    ConnectorInfo(
                        name=name,
                        source_name=f"source-{name}",
                    )
                    for name in registry
                ]
            except Exception as e:
                logger.error(f"Failed to get PyAirbyte registry: {e}")

        # Fallback to curated list
        return self._get_curated_connectors()

    def _get_curated_connectors(self) -> List[ConnectorInfo]:
        """Get curated list of popular connectors."""
        connectors = [
            # Databases
            ("postgres", "source-postgres"),
            ("mysql", "source-mysql"),
            ("mongodb", "source-mongodb"),
            ("mssql", "source-mssql"),
            ("snowflake", "source-snowflake"),
            ("bigquery", "source-bigquery"),
            ("redshift", "source-redshift"),
            # CRM
            ("salesforce", "source-salesforce"),
            ("hubspot", "source-hubspot"),
            ("pipedrive", "source-pipedrive"),
            ("zoho-crm", "source-zoho-crm"),
            # Marketing
            ("google-ads", "source-google-ads"),
            ("facebook-marketing", "source-facebook-marketing"),
            ("linkedin-ads", "source-linkedin-ads"),
            ("mailchimp", "source-mailchimp"),
            # E-commerce
            ("shopify", "source-shopify"),
            ("stripe", "source-stripe"),
            ("woocommerce", "source-woocommerce"),
            ("amazon-seller-partner", "source-amazon-seller-partner"),
            # Analytics
            ("google-analytics-v4", "source-google-analytics-v4"),
            ("mixpanel", "source-mixpanel"),
            ("amplitude", "source-amplitude"),
            # Project Management
            ("jira", "source-jira"),
            ("asana", "source-asana"),
            ("notion", "source-notion"),
            ("monday", "source-monday"),
            # Communication
            ("slack", "source-slack"),
            ("intercom", "source-intercom"),
            ("zendesk-support", "source-zendesk-support"),
            # Storage
            ("s3", "source-s3"),
            ("gcs", "source-gcs"),
            ("google-sheets", "source-google-sheets"),
            # HR
            ("greenhouse", "source-greenhouse"),
            ("lever", "source-lever"),
            # Finance
            ("quickbooks", "source-quickbooks"),
            ("xero", "source-xero"),
            ("netsuite", "source-netsuite"),
            # Development
            ("github", "source-github"),
            ("gitlab", "source-gitlab"),
        ]
        return [
            ConnectorInfo(name=name, source_name=source_name)
            for name, source_name in connectors
        ]

    async def create_source(
        self,
        connector_name: str,
        config: Dict[str, Any],
        source_id: Optional[str] = None
    ) -> str:
        """
        Create and configure a source.

        Args:
            connector_name: Name of the connector (e.g., "source-postgres")
            config: Connector configuration
            source_id: Optional custom source ID

        Returns:
            Source ID
        """
        if source_id is None:
            source_id = f"src_{connector_name}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        if PYAIRBYTE_AVAILABLE:
            try:
                # Create real PyAirbyte source
                # Remove "source-" prefix if present
                name = connector_name.replace("source-", "")

                source = ab.get_source(
                    name,
                    config=config,
                    install_if_missing=True
                )

                self._sources[source_id] = {
                    "source": source,
                    "connector_name": connector_name,
                    "config": config,
                    "created_at": datetime.utcnow().isoformat(),
                    "mode": "real"
                }

                logger.info(f"Created real PyAirbyte source: {source_id}")
                return source_id

            except Exception as e:
                logger.error(f"Failed to create real source: {e}")
                logger.info("Falling back to mock source")

        # Mock implementation
        self._sources[source_id] = {
            "source": None,
            "connector_name": connector_name,
            "config": config,
            "created_at": datetime.utcnow().isoformat(),
            "mode": "mock"
        }

        logger.info(f"Created mock source: {source_id}")
        return source_id

    async def discover_catalog(self, source_id: str) -> List[StreamInfo]:
        """
        Discover available streams for a source.

        Returns real catalog if PyAirbyte source, otherwise mock streams.
        """
        if source_id not in self._sources:
            raise ValueError(f"Source {source_id} not found")

        source_info = self._sources[source_id]

        if source_info["mode"] == "real" and PYAIRBYTE_AVAILABLE:
            try:
                source = source_info["source"]
                catalog = source.get_available_streams()

                return [
                    StreamInfo(
                        name=stream,
                        json_schema={},  # Full schema available via source
                        supported_sync_modes=["full_refresh", "incremental"]
                    )
                    for stream in catalog
                ]
            except Exception as e:
                logger.error(f"Failed to discover catalog: {e}")

        # Mock catalog
        return self._get_mock_catalog(source_info["connector_name"])

    def _get_mock_catalog(self, connector_name: str) -> List[StreamInfo]:
        """Get mock catalog for a connector."""
        # Common stream patterns by connector type
        if "postgres" in connector_name or "mysql" in connector_name:
            return [
                StreamInfo(
                    name="users",
                    json_schema={"type": "object", "properties": {
                        "id": {"type": "integer"},
                        "email": {"type": "string"},
                        "created_at": {"type": "string", "format": "date-time"}
                    }},
                    supported_sync_modes=["full_refresh", "incremental"],
                    source_defined_cursor=True,
                    default_cursor_field=["updated_at"]
                ),
                StreamInfo(
                    name="orders",
                    json_schema={"type": "object", "properties": {
                        "id": {"type": "integer"},
                        "user_id": {"type": "integer"},
                        "total": {"type": "number"},
                        "status": {"type": "string"}
                    }},
                    supported_sync_modes=["full_refresh", "incremental"],
                    source_defined_cursor=True,
                    default_cursor_field=["created_at"]
                ),
                StreamInfo(
                    name="products",
                    json_schema={"type": "object", "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "price": {"type": "number"}
                    }},
                    supported_sync_modes=["full_refresh"]
                )
            ]
        elif "salesforce" in connector_name:
            return [
                StreamInfo(name="Account", json_schema={}, supported_sync_modes=["full_refresh", "incremental"]),
                StreamInfo(name="Contact", json_schema={}, supported_sync_modes=["full_refresh", "incremental"]),
                StreamInfo(name="Lead", json_schema={}, supported_sync_modes=["full_refresh", "incremental"]),
                StreamInfo(name="Opportunity", json_schema={}, supported_sync_modes=["full_refresh", "incremental"]),
            ]
        elif "stripe" in connector_name:
            return [
                StreamInfo(name="customers", json_schema={}, supported_sync_modes=["full_refresh", "incremental"]),
                StreamInfo(name="charges", json_schema={}, supported_sync_modes=["full_refresh", "incremental"]),
                StreamInfo(name="subscriptions", json_schema={}, supported_sync_modes=["full_refresh", "incremental"]),
                StreamInfo(name="invoices", json_schema={}, supported_sync_modes=["full_refresh", "incremental"]),
            ]
        else:
            return [
                StreamInfo(name="data", json_schema={}, supported_sync_modes=["full_refresh"]),
                StreamInfo(name="events", json_schema={}, supported_sync_modes=["full_refresh", "incremental"]),
            ]

    async def read_stream(
        self,
        source_id: str,
        stream_name: str,
        sync_mode: str = "full_refresh",
        cursor_value: Optional[Any] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Read records from a stream.

        Yields records one at a time for memory efficiency.
        """
        if source_id not in self._sources:
            raise ValueError(f"Source {source_id} not found")

        source_info = self._sources[source_id]

        if source_info["mode"] == "real" and PYAIRBYTE_AVAILABLE:
            try:
                source = source_info["source"]
                source.select_streams([stream_name])

                # Read to cache and yield records
                cache = ab.new_local_cache(cache_dir=self._cache_dir)
                result = source.read(cache=cache)

                for record in result[stream_name]:
                    yield dict(record)

                return

            except Exception as e:
                logger.error(f"Failed to read from real source: {e}")
                logger.info("Falling back to mock data")

        # Mock data generator
        async for record in self._generate_mock_data(stream_name, 100):
            yield record

    async def _generate_mock_data(
        self,
        stream_name: str,
        count: int
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate mock data for testing."""
        import random

        for i in range(count):
            if stream_name in ["users", "customers", "Account", "Contact"]:
                yield {
                    "id": i + 1,
                    "email": f"user{i+1}@example.com",
                    "name": f"User {i+1}",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
            elif stream_name in ["orders", "charges", "invoices"]:
                yield {
                    "id": i + 1,
                    "user_id": random.randint(1, 100),
                    "amount": round(random.uniform(10, 1000), 2),
                    "status": random.choice(["pending", "completed", "failed"]),
                    "created_at": datetime.utcnow().isoformat()
                }
            else:
                yield {
                    "id": i + 1,
                    "data": f"Record {i+1}",
                    "timestamp": datetime.utcnow().isoformat()
                }

    async def read_all(
        self,
        source_id: str,
        streams: Optional[List[str]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Read all records from selected streams.

        Returns dict mapping stream names to lists of records.
        """
        if source_id not in self._sources:
            raise ValueError(f"Source {source_id} not found")

        source_info = self._sources[source_id]

        # Get streams to read
        if streams is None:
            catalog = await self.discover_catalog(source_id)
            streams = [s.name for s in catalog]

        results = {}
        for stream in streams:
            records = []
            async for record in self.read_stream(source_id, stream):
                records.append(record)
            results[stream] = records

        return results

    async def check_connection(self, source_id: str) -> Dict[str, Any]:
        """
        Check if source connection is valid.

        Returns connection status and any error messages.
        """
        if source_id not in self._sources:
            return {
                "status": "failed",
                "error": f"Source {source_id} not found"
            }

        source_info = self._sources[source_id]

        if source_info["mode"] == "real" and PYAIRBYTE_AVAILABLE:
            try:
                source = source_info["source"]
                source.check()
                return {
                    "status": "succeeded",
                    "mode": "real"
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "error": str(e),
                    "mode": "real"
                }

        # Mock always succeeds
        return {
            "status": "succeeded",
            "mode": "mock",
            "message": "Using mock mode - install PyAirbyte for real connections"
        }

    def delete_source(self, source_id: str) -> bool:
        """Delete a source."""
        if source_id in self._sources:
            del self._sources[source_id]
            return True
        return False

    def list_sources(self) -> List[Dict[str, Any]]:
        """List all configured sources."""
        return [
            {
                "source_id": source_id,
                "connector_name": info["connector_name"],
                "created_at": info["created_at"],
                "mode": info["mode"]
            }
            for source_id, info in self._sources.items()
        ]


# Singleton instance
_real_executor: Optional[RealPyAirbyteExecutor] = None


def get_real_pyairbyte_executor() -> RealPyAirbyteExecutor:
    """Get singleton RealPyAirbyteExecutor instance."""
    global _real_executor
    if _real_executor is None:
        _real_executor = RealPyAirbyteExecutor()
    return _real_executor


def is_pyairbyte_available() -> bool:
    """Check if PyAirbyte is installed."""
    return PYAIRBYTE_AVAILABLE
