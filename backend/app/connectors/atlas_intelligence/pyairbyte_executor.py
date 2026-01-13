"""
PyAirbyte Executor - Access 300+ data sources via PyAirbyte.

This module provides a unified interface to Airbyte's connector ecosystem,
enabling access to databases, APIs, files, and more through a consistent API.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ConnectorStatus(str, Enum):
    """Status of a PyAirbyte connector."""
    AVAILABLE = "available"
    INSTALLED = "installed"
    CONFIGURED = "configured"
    CONNECTED = "connected"
    ERROR = "error"


class SyncMode(str, Enum):
    """Sync modes supported by Airbyte connectors."""
    FULL_REFRESH = "full_refresh"
    INCREMENTAL = "incremental"


@dataclass
class AirbyteStream:
    """Represents a stream (table/entity) in an Airbyte source."""
    name: str
    json_schema: Dict[str, Any]
    supported_sync_modes: List[str]
    source_defined_cursor: bool = False
    default_cursor_field: Optional[List[str]] = None
    source_defined_primary_key: Optional[List[List[str]]] = None


@dataclass
class AirbyteCatalog:
    """Catalog of available streams from a source."""
    streams: List[AirbyteStream] = field(default_factory=list)


class PyAirbyteConfig(BaseModel):
    """Configuration for a PyAirbyte connector."""
    source_name: str = Field(..., description="Airbyte source name (e.g., 'source-postgres')")
    config: Dict[str, Any] = Field(default_factory=dict, description="Source-specific configuration")
    streams: List[str] = Field(default_factory=list, description="Streams to sync (empty = all)")
    sync_mode: SyncMode = Field(default=SyncMode.FULL_REFRESH, description="Sync mode")


class PyAirbyteExecutor:
    """
    Executor for PyAirbyte connectors.

    Provides access to 300+ data sources through Airbyte's connector ecosystem.
    Uses PyAirbyte for Python-native integration without Docker overhead.
    """

    # Popular connectors with their categories
    CONNECTOR_CATALOG = {
        # Databases
        "source-postgres": {"category": "database", "name": "PostgreSQL"},
        "source-mysql": {"category": "database", "name": "MySQL"},
        "source-mssql": {"category": "database", "name": "Microsoft SQL Server"},
        "source-mongodb-v2": {"category": "database", "name": "MongoDB"},
        "source-oracle": {"category": "database", "name": "Oracle DB"},
        "source-snowflake": {"category": "database", "name": "Snowflake"},
        "source-bigquery": {"category": "database", "name": "BigQuery"},
        "source-redshift": {"category": "database", "name": "Amazon Redshift"},
        "source-clickhouse": {"category": "database", "name": "ClickHouse"},
        "source-cockroachdb": {"category": "database", "name": "CockroachDB"},

        # CRM / Sales
        "source-salesforce": {"category": "crm", "name": "Salesforce"},
        "source-hubspot": {"category": "crm", "name": "HubSpot"},
        "source-pipedrive": {"category": "crm", "name": "Pipedrive"},
        "source-zoho-crm": {"category": "crm", "name": "Zoho CRM"},
        "source-close-com": {"category": "crm", "name": "Close"},
        "source-copper": {"category": "crm", "name": "Copper"},
        "source-freshsales": {"category": "crm", "name": "Freshsales"},

        # Marketing
        "source-google-ads": {"category": "marketing", "name": "Google Ads"},
        "source-facebook-marketing": {"category": "marketing", "name": "Facebook Ads"},
        "source-linkedin-ads": {"category": "marketing", "name": "LinkedIn Ads"},
        "source-mailchimp": {"category": "marketing", "name": "Mailchimp"},
        "source-klaviyo": {"category": "marketing", "name": "Klaviyo"},
        "source-sendgrid": {"category": "marketing", "name": "SendGrid"},
        "source-braze": {"category": "marketing", "name": "Braze"},
        "source-iterable": {"category": "marketing", "name": "Iterable"},

        # E-commerce
        "source-shopify": {"category": "ecommerce", "name": "Shopify"},
        "source-stripe": {"category": "ecommerce", "name": "Stripe"},
        "source-woocommerce": {"category": "ecommerce", "name": "WooCommerce"},
        "source-amazon-seller-partner": {"category": "ecommerce", "name": "Amazon Seller"},
        "source-square": {"category": "ecommerce", "name": "Square"},
        "source-chargebee": {"category": "ecommerce", "name": "Chargebee"},
        "source-recurly": {"category": "ecommerce", "name": "Recurly"},

        # Analytics
        "source-google-analytics-v4": {"category": "analytics", "name": "Google Analytics 4"},
        "source-mixpanel": {"category": "analytics", "name": "Mixpanel"},
        "source-amplitude": {"category": "analytics", "name": "Amplitude"},
        "source-segment": {"category": "analytics", "name": "Segment"},
        "source-heap": {"category": "analytics", "name": "Heap"},
        "source-pendo": {"category": "analytics", "name": "Pendo"},

        # Project Management
        "source-jira": {"category": "project", "name": "Jira"},
        "source-asana": {"category": "project", "name": "Asana"},
        "source-monday": {"category": "project", "name": "Monday.com"},
        "source-notion": {"category": "project", "name": "Notion"},
        "source-linear": {"category": "project", "name": "Linear"},
        "source-clickup-api": {"category": "project", "name": "ClickUp"},
        "source-trello": {"category": "project", "name": "Trello"},

        # Communication
        "source-slack": {"category": "communication", "name": "Slack"},
        "source-intercom": {"category": "communication", "name": "Intercom"},
        "source-zendesk-support": {"category": "communication", "name": "Zendesk"},
        "source-freshdesk": {"category": "communication", "name": "Freshdesk"},
        "source-drift": {"category": "communication", "name": "Drift"},
        "source-front": {"category": "communication", "name": "Front"},

        # Files / Storage
        "source-s3": {"category": "storage", "name": "Amazon S3"},
        "source-gcs": {"category": "storage", "name": "Google Cloud Storage"},
        "source-azure-blob-storage": {"category": "storage", "name": "Azure Blob"},
        "source-sftp": {"category": "storage", "name": "SFTP"},
        "source-google-drive": {"category": "storage", "name": "Google Drive"},
        "source-google-sheets": {"category": "storage", "name": "Google Sheets"},

        # HR / Recruiting
        "source-greenhouse": {"category": "hr", "name": "Greenhouse"},
        "source-lever-hiring": {"category": "hr", "name": "Lever"},
        "source-workday": {"category": "hr", "name": "Workday"},
        "source-bamboohr": {"category": "hr", "name": "BambooHR"},

        # Finance
        "source-quickbooks": {"category": "finance", "name": "QuickBooks"},
        "source-xero": {"category": "finance", "name": "Xero"},
        "source-netsuite": {"category": "finance", "name": "NetSuite"},
        "source-plaid": {"category": "finance", "name": "Plaid"},

        # Development
        "source-github": {"category": "development", "name": "GitHub"},
        "source-gitlab": {"category": "development", "name": "GitLab"},
        "source-bitbucket": {"category": "development", "name": "Bitbucket"},
        "source-datadog": {"category": "development", "name": "Datadog"},
        "source-sentry": {"category": "development", "name": "Sentry"},
        "source-circleci": {"category": "development", "name": "CircleCI"},
        "source-jenkins": {"category": "development", "name": "Jenkins"},
        "source-sonarqube": {"category": "development", "name": "SonarQube"},
        "source-launchdarkly": {"category": "development", "name": "LaunchDarkly"},

        # Social Media
        "source-instagram": {"category": "social", "name": "Instagram"},
        "source-tiktok-marketing": {"category": "social", "name": "TikTok Ads"},
        "source-twitter": {"category": "social", "name": "Twitter/X"},
        "source-youtube-analytics": {"category": "social", "name": "YouTube Analytics"},
        "source-pinterest": {"category": "social", "name": "Pinterest"},
        "source-snapchat-marketing": {"category": "social", "name": "Snapchat Ads"},
        "source-reddit": {"category": "social", "name": "Reddit"},
        "source-twitch": {"category": "social", "name": "Twitch"},

        # Cloud Infrastructure
        "source-aws-cloudtrail": {"category": "cloud", "name": "AWS CloudTrail"},
        "source-amazon-sqs": {"category": "cloud", "name": "Amazon SQS"},
        "source-amazon-kinesis": {"category": "cloud", "name": "Amazon Kinesis"},
        "source-azure-table": {"category": "cloud", "name": "Azure Table Storage"},
        "source-google-pubsub": {"category": "cloud", "name": "Google Pub/Sub"},
        "source-firebase-realtime-database": {"category": "cloud", "name": "Firebase Realtime DB"},
        "source-dynamodb": {"category": "cloud", "name": "Amazon DynamoDB"},
        "source-elasticsearch": {"category": "cloud", "name": "Elasticsearch"},

        # Business Intelligence
        "source-metabase": {"category": "bi", "name": "Metabase"},
        "source-looker": {"category": "bi", "name": "Looker"},
        "source-tableau": {"category": "bi", "name": "Tableau"},
        "source-dbt-cloud": {"category": "bi", "name": "dbt Cloud"},
        "source-mode": {"category": "bi", "name": "Mode Analytics"},
        "source-sigma": {"category": "bi", "name": "Sigma Computing"},

        # DevOps & Monitoring
        "source-pagerduty": {"category": "devops", "name": "PagerDuty"},
        "source-newrelic": {"category": "devops", "name": "New Relic"},
        "source-opsgenie": {"category": "devops", "name": "Opsgenie"},
        "source-statuspage": {"category": "devops", "name": "Statuspage"},
        "source-victorops": {"category": "devops", "name": "VictorOps"},
        "source-instatus": {"category": "devops", "name": "Instatus"},

        # Customer Data Platforms
        "source-customerio": {"category": "cdp", "name": "Customer.io"},
        "source-rudderstack": {"category": "cdp", "name": "RudderStack"},
        "source-appsflyer": {"category": "cdp", "name": "AppsFlyer"},
        "source-adjust": {"category": "cdp", "name": "Adjust"},
        "source-branch": {"category": "cdp", "name": "Branch"},
        "source-mparticle": {"category": "cdp", "name": "mParticle"},

        # Forms & Surveys
        "source-typeform": {"category": "forms", "name": "Typeform"},
        "source-surveymonkey": {"category": "forms", "name": "SurveyMonkey"},
        "source-jotform": {"category": "forms", "name": "JotForm"},
        "source-google-forms": {"category": "forms", "name": "Google Forms"},
        "source-airtable": {"category": "forms", "name": "Airtable"},

        # Legal & Contracts
        "source-docusign": {"category": "legal", "name": "DocuSign"},
        "source-hellosign": {"category": "legal", "name": "HelloSign"},
        "source-pandadoc": {"category": "legal", "name": "PandaDoc"},
        "source-clio": {"category": "legal", "name": "Clio"},

        # Event & Ticketing
        "source-eventbrite": {"category": "events", "name": "Eventbrite"},
        "source-ticketmaster": {"category": "events", "name": "Ticketmaster"},
        "source-calendly": {"category": "events", "name": "Calendly"},
        "source-zoom": {"category": "events", "name": "Zoom"},

        # Education
        "source-canvas": {"category": "education", "name": "Canvas LMS"},
        "source-blackboard": {"category": "education", "name": "Blackboard"},
        "source-google-classroom": {"category": "education", "name": "Google Classroom"},
        "source-coursera": {"category": "education", "name": "Coursera"},

        # Real Estate & Property
        "source-yardi": {"category": "realestate", "name": "Yardi"},
        "source-appfolio": {"category": "realestate", "name": "AppFolio"},
        "source-buildium": {"category": "realestate", "name": "Buildium"},

        # Healthcare
        "source-athenahealth": {"category": "healthcare", "name": "athenahealth"},
        "source-epic-fhir": {"category": "healthcare", "name": "Epic FHIR"},
        "source-allscripts": {"category": "healthcare", "name": "Allscripts"},
        "source-cerner-fhir": {"category": "healthcare", "name": "Cerner FHIR"},

        # Logistics & Shipping
        "source-shipstation": {"category": "logistics", "name": "ShipStation"},
        "source-shippo": {"category": "logistics", "name": "Shippo"},
        "source-easypost": {"category": "logistics", "name": "EasyPost"},
        "source-aftership": {"category": "logistics", "name": "AfterShip"},

        # Productivity & Office
        "source-microsoft-teams": {"category": "productivity", "name": "Microsoft Teams"},
        "source-office365": {"category": "productivity", "name": "Office 365"},
        "source-outlook": {"category": "productivity", "name": "Outlook"},
        "source-onenote": {"category": "productivity", "name": "OneNote"},
        "source-sharepoint": {"category": "productivity", "name": "SharePoint"},
        "source-confluence": {"category": "productivity", "name": "Confluence"},

        # Advertising Networks
        "source-amazon-ads": {"category": "advertising", "name": "Amazon Ads"},
        "source-bing-ads": {"category": "advertising", "name": "Microsoft Ads"},
        "source-outbrain": {"category": "advertising", "name": "Outbrain"},
        "source-taboola": {"category": "advertising", "name": "Taboola"},
        "source-criteo": {"category": "advertising", "name": "Criteo"},
        "source-applovin": {"category": "advertising", "name": "AppLovin"},

        # Government & Public Data
        "source-us-census": {"category": "government", "name": "US Census"},
        "source-open-exchange-rates": {"category": "government", "name": "Exchange Rates"},
        "source-currencylayer": {"category": "government", "name": "Currency Layer"},

        # Weather & Location
        "source-openweathermap": {"category": "weather", "name": "OpenWeatherMap"},
        "source-weatherstack": {"category": "weather", "name": "Weatherstack"},
        "source-ip-info": {"category": "weather", "name": "IP Info"},
    }

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize PyAirbyte executor.

        Args:
            cache_dir: Directory for caching connector state
        """
        self.cache_dir = cache_dir or Path("/tmp/pyairbyte_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._sources: Dict[str, Any] = {}
        self._installed_connectors: set = set()
        self._pyairbyte_available = self._check_pyairbyte()

    def _check_pyairbyte(self) -> bool:
        """Check if PyAirbyte is available."""
        try:
            import airbyte as ab
            return True
        except ImportError:
            logger.warning("PyAirbyte not installed. Install with: pip install airbyte")
            return False

    def list_available_connectors(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List available Airbyte connectors.

        Args:
            category: Filter by category (database, crm, marketing, etc.)
            search: Search in connector names

        Returns:
            List of connector metadata
        """
        connectors = []

        for source_id, info in self.CONNECTOR_CATALOG.items():
            if category and info["category"] != category:
                continue
            if search and search.lower() not in info["name"].lower():
                continue

            connectors.append({
                "id": source_id,
                "name": info["name"],
                "category": info["category"],
                "status": (
                    ConnectorStatus.INSTALLED.value
                    if source_id in self._installed_connectors
                    else ConnectorStatus.AVAILABLE.value
                ),
                "pyairbyte_available": self._pyairbyte_available
            })

        return sorted(connectors, key=lambda x: x["name"])

    def get_connector_spec(self, source_name: str) -> Dict[str, Any]:
        """
        Get configuration specification for a connector.

        Args:
            source_name: Airbyte source name (e.g., 'source-postgres')

        Returns:
            JSON Schema for connector configuration
        """
        if not self._pyairbyte_available:
            return self._get_fallback_spec(source_name)

        try:
            import airbyte as ab
            source = ab.get_source(source_name)
            return source.spec
        except Exception as e:
            logger.error(f"Failed to get spec for {source_name}: {e}")
            return self._get_fallback_spec(source_name)

    def _get_fallback_spec(self, source_name: str) -> Dict[str, Any]:
        """Get fallback spec when PyAirbyte is not available."""
        # Common specs for popular connectors
        specs = {
            "source-postgres": {
                "type": "object",
                "required": ["host", "port", "database", "username", "password"],
                "properties": {
                    "host": {"type": "string", "description": "Database host"},
                    "port": {"type": "integer", "default": 5432},
                    "database": {"type": "string", "description": "Database name"},
                    "username": {"type": "string", "description": "Username"},
                    "password": {"type": "string", "description": "Password", "airbyte_secret": True},
                    "ssl": {"type": "boolean", "default": False}
                }
            },
            "source-mysql": {
                "type": "object",
                "required": ["host", "port", "database", "username", "password"],
                "properties": {
                    "host": {"type": "string", "description": "Database host"},
                    "port": {"type": "integer", "default": 3306},
                    "database": {"type": "string", "description": "Database name"},
                    "username": {"type": "string", "description": "Username"},
                    "password": {"type": "string", "description": "Password", "airbyte_secret": True}
                }
            },
            "source-stripe": {
                "type": "object",
                "required": ["account_id", "client_secret"],
                "properties": {
                    "account_id": {"type": "string", "description": "Stripe Account ID"},
                    "client_secret": {"type": "string", "description": "API Secret Key", "airbyte_secret": True},
                    "start_date": {"type": "string", "format": "date", "description": "Replication start date"}
                }
            },
            "source-github": {
                "type": "object",
                "required": ["credentials", "repositories"],
                "properties": {
                    "credentials": {
                        "type": "object",
                        "properties": {
                            "personal_access_token": {"type": "string", "airbyte_secret": True}
                        }
                    },
                    "repositories": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
        return specs.get(source_name, {"type": "object", "properties": {}})

    async def configure_source(
        self,
        source_name: str,
        config: Dict[str, Any],
        streams: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Configure and validate a source connector.

        Args:
            source_name: Airbyte source name
            config: Source configuration
            streams: Streams to sync (None = all)

        Returns:
            Configuration result with status
        """
        if not self._pyairbyte_available:
            return {
                "status": "simulated",
                "message": "PyAirbyte not installed - configuration simulated",
                "source_name": source_name,
                "streams": streams or ["all"]
            }

        try:
            import airbyte as ab

            # Get and configure source
            source = ab.get_source(
                source_name,
                config=config,
                streams=streams
            )

            # Validate configuration
            source.check()

            # Store configured source
            self._sources[source_name] = source
            self._installed_connectors.add(source_name)

            return {
                "status": "configured",
                "source_name": source_name,
                "streams": [s.stream_name for s in source.get_available_streams()],
                "message": "Source configured and validated successfully"
            }

        except Exception as e:
            logger.error(f"Failed to configure {source_name}: {e}")
            return {
                "status": "error",
                "source_name": source_name,
                "error": str(e)
            }

    async def discover_streams(self, source_name: str) -> AirbyteCatalog:
        """
        Discover available streams from a configured source.

        Args:
            source_name: Configured source name

        Returns:
            Catalog of available streams
        """
        if not self._pyairbyte_available or source_name not in self._sources:
            # Return mock catalog for demo
            return AirbyteCatalog(streams=[
                AirbyteStream(
                    name="mock_stream",
                    json_schema={"type": "object", "properties": {}},
                    supported_sync_modes=["full_refresh", "incremental"]
                )
            ])

        source = self._sources[source_name]
        streams = []

        for stream_info in source.get_available_streams():
            streams.append(AirbyteStream(
                name=stream_info.stream_name,
                json_schema=stream_info.stream.json_schema,
                supported_sync_modes=[str(m) for m in stream_info.stream.supported_sync_modes],
                source_defined_cursor=stream_info.stream.source_defined_cursor,
                default_cursor_field=stream_info.stream.default_cursor_field,
                source_defined_primary_key=stream_info.stream.source_defined_primary_key
            ))

        return AirbyteCatalog(streams=streams)

    async def read_stream(
        self,
        source_name: str,
        stream_name: str,
        sync_mode: SyncMode = SyncMode.FULL_REFRESH,
        state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Read data from a stream.

        Args:
            source_name: Configured source name
            stream_name: Stream to read
            sync_mode: Full refresh or incremental
            state: State for incremental syncs

        Returns:
            Data and sync state
        """
        if not self._pyairbyte_available or source_name not in self._sources:
            # Return mock data for demo
            return {
                "status": "simulated",
                "stream": stream_name,
                "records": [],
                "record_count": 0,
                "state": {},
                "message": "PyAirbyte not available - returning mock data"
            }

        try:
            source = self._sources[source_name]

            # Select the stream
            source.select_streams([stream_name])

            # Read data
            result = source.read()

            # Convert to DataFrame
            records = []
            for stream_data in result.streams.values():
                df = stream_data.to_pandas()
                records = df.to_dict(orient="records")
                break  # Only read first stream

            return {
                "status": "success",
                "stream": stream_name,
                "records": records[:1000],  # Limit for API response
                "record_count": len(records),
                "state": result.state or {},
                "synced_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to read {stream_name} from {source_name}: {e}")
            return {
                "status": "error",
                "stream": stream_name,
                "error": str(e)
            }

    async def sync_to_dataframe(
        self,
        source_name: str,
        streams: Optional[List[str]] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Sync data from source to pandas DataFrames.

        Args:
            source_name: Configured source name
            streams: Streams to sync (None = all selected)

        Returns:
            Dictionary mapping stream names to DataFrames
        """
        if not self._pyairbyte_available or source_name not in self._sources:
            # Return empty DataFrames for demo
            return {
                "mock_stream": pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})
            }

        try:
            source = self._sources[source_name]

            if streams:
                source.select_streams(streams)

            result = source.read()

            dataframes = {}
            for stream_name, stream_data in result.streams.items():
                dataframes[stream_name] = stream_data.to_pandas()

            return dataframes

        except Exception as e:
            logger.error(f"Failed to sync from {source_name}: {e}")
            return {}

    def get_categories(self) -> List[Dict[str, Any]]:
        """Get list of connector categories with counts."""
        category_counts: Dict[str, int] = {}

        for info in self.CONNECTOR_CATALOG.values():
            cat = info["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return [
            {"category": cat, "count": count, "label": cat.replace("_", " ").title()}
            for cat, count in sorted(category_counts.items())
        ]

    def health_check(self) -> Dict[str, Any]:
        """Check health status of PyAirbyte integration."""
        return {
            "status": "healthy" if self._pyairbyte_available else "degraded",
            "pyairbyte_installed": self._pyairbyte_available,
            "configured_sources": len(self._sources),
            "installed_connectors": len(self._installed_connectors),
            "total_available_connectors": len(self.CONNECTOR_CATALOG),
            "cache_dir": str(self.cache_dir),
            "message": (
                "PyAirbyte ready for 300+ data sources"
                if self._pyairbyte_available
                else "Install PyAirbyte for full connector support: pip install airbyte"
            )
        }


# Global executor instance
_executor: Optional[PyAirbyteExecutor] = None


def get_pyairbyte_executor() -> PyAirbyteExecutor:
    """Get or create PyAirbyte executor instance."""
    global _executor
    if _executor is None:
        _executor = PyAirbyteExecutor()
    return _executor
