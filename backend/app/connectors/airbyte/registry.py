"""
Airbyte Connector Registry
==========================

Registry of 100+ Airbyte connector Docker images organized by category.
This enables Atlas to use any Airbyte connector through Docker execution.

All images are from the official Airbyte Docker Hub:
https://hub.docker.com/u/airbyte

Usage:
    from registry import get_connector_image, list_connectors

    # Get Docker image for a connector
    image = get_connector_image("source-postgres")
    # Returns: "airbyte/source-postgres:latest"

    # List all available connectors
    connectors = list_connectors()

    # List by category
    databases = list_connectors(category="database")
"""

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ConnectorCategory(str, Enum):
    """Categories of Airbyte connectors."""

    DATABASE = "database"
    FILE = "file"
    API = "api"
    CRM = "crm"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    ECOMMERCE = "ecommerce"
    FINANCE = "finance"
    HR = "hr"
    PRODUCTIVITY = "productivity"
    COMMUNICATION = "communication"
    DEVELOPMENT = "development"
    STORAGE = "storage"
    OTHER = "other"


@dataclass
class ConnectorInfo:
    """Information about an Airbyte connector."""

    name: str  # Connector name (e.g., "source-postgres")
    display_name: str  # Human-readable name
    category: ConnectorCategory
    docker_image: str  # Full Docker image name
    documentation_url: str | None = None
    supports_incremental: bool = True
    supports_normalization: bool = False


# =============================================================================
# Connector Registry (100+ Connectors)
# =============================================================================

AIRBYTE_CONNECTORS: dict[str, ConnectorInfo] = {
    # =========================================================================
    # DATABASE CONNECTORS (20+)
    # =========================================================================
    "source-postgres": ConnectorInfo(
        name="source-postgres",
        display_name="PostgreSQL",
        category=ConnectorCategory.DATABASE,
        docker_image="airbyte/source-postgres:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/postgres",
        supports_incremental=True,
    ),
    "source-mysql": ConnectorInfo(
        name="source-mysql",
        display_name="MySQL",
        category=ConnectorCategory.DATABASE,
        docker_image="airbyte/source-mysql:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/mysql",
        supports_incremental=True,
    ),
    "source-mssql": ConnectorInfo(
        name="source-mssql",
        display_name="Microsoft SQL Server",
        category=ConnectorCategory.DATABASE,
        docker_image="airbyte/source-mssql:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/mssql",
        supports_incremental=True,
    ),
    "source-mongodb-v2": ConnectorInfo(
        name="source-mongodb-v2",
        display_name="MongoDB",
        category=ConnectorCategory.DATABASE,
        docker_image="airbyte/source-mongodb-v2:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/mongodb-v2",
        supports_incremental=True,
    ),
    "source-oracle": ConnectorInfo(
        name="source-oracle",
        display_name="Oracle Database",
        category=ConnectorCategory.DATABASE,
        docker_image="airbyte/source-oracle:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/oracle",
        supports_incremental=True,
    ),
    "source-cockroachdb": ConnectorInfo(
        name="source-cockroachdb",
        display_name="CockroachDB",
        category=ConnectorCategory.DATABASE,
        docker_image="airbyte/source-cockroachdb:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/cockroachdb",
        supports_incremental=True,
    ),
    "source-clickhouse": ConnectorInfo(
        name="source-clickhouse",
        display_name="ClickHouse",
        category=ConnectorCategory.DATABASE,
        docker_image="airbyte/source-clickhouse:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/clickhouse",
        supports_incremental=True,
    ),
    "source-redshift": ConnectorInfo(
        name="source-redshift",
        display_name="Amazon Redshift",
        category=ConnectorCategory.DATABASE,
        docker_image="airbyte/source-redshift:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/redshift",
        supports_incremental=True,
    ),
    "source-bigquery": ConnectorInfo(
        name="source-bigquery",
        display_name="Google BigQuery",
        category=ConnectorCategory.DATABASE,
        docker_image="airbyte/source-bigquery:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/bigquery",
        supports_incremental=True,
    ),
    "source-snowflake": ConnectorInfo(
        name="source-snowflake",
        display_name="Snowflake",
        category=ConnectorCategory.DATABASE,
        docker_image="airbyte/source-snowflake:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/snowflake",
        supports_incremental=True,
    ),
    "source-mariadb-columnstore": ConnectorInfo(
        name="source-mariadb-columnstore",
        display_name="MariaDB ColumnStore",
        category=ConnectorCategory.DATABASE,
        docker_image="airbyte/source-mariadb-columnstore:latest",
        supports_incremental=True,
    ),
    "source-tidb": ConnectorInfo(
        name="source-tidb",
        display_name="TiDB",
        category=ConnectorCategory.DATABASE,
        docker_image="airbyte/source-tidb:latest",
        supports_incremental=True,
    ),
    "source-db2": ConnectorInfo(
        name="source-db2",
        display_name="IBM DB2",
        category=ConnectorCategory.DATABASE,
        docker_image="airbyte/source-db2:latest",
        supports_incremental=True,
    ),
    "source-elasticsearch": ConnectorInfo(
        name="source-elasticsearch",
        display_name="Elasticsearch",
        category=ConnectorCategory.DATABASE,
        docker_image="airbyte/source-elasticsearch:latest",
        supports_incremental=False,
    ),
    "source-dynamodb": ConnectorInfo(
        name="source-dynamodb",
        display_name="Amazon DynamoDB",
        category=ConnectorCategory.DATABASE,
        docker_image="airbyte/source-dynamodb:latest",
        supports_incremental=True,
    ),
    "source-firebase-realtime-database": ConnectorInfo(
        name="source-firebase-realtime-database",
        display_name="Firebase Realtime Database",
        category=ConnectorCategory.DATABASE,
        docker_image="airbyte/source-firebase-realtime-database:latest",
        supports_incremental=False,
    ),
    "source-couchbase": ConnectorInfo(
        name="source-couchbase",
        display_name="Couchbase",
        category=ConnectorCategory.DATABASE,
        docker_image="airbyte/source-couchbase:latest",
        supports_incremental=True,
    ),
    "source-neo4j": ConnectorInfo(
        name="source-neo4j",
        display_name="Neo4j",
        category=ConnectorCategory.DATABASE,
        docker_image="airbyte/source-neo4j:latest",
        supports_incremental=False,
    ),
    "source-timescaledb": ConnectorInfo(
        name="source-timescaledb",
        display_name="TimescaleDB",
        category=ConnectorCategory.DATABASE,
        docker_image="airbyte/source-timescaledb:latest",
        supports_incremental=True,
    ),
    "source-yugabytedb": ConnectorInfo(
        name="source-yugabytedb",
        display_name="YugabyteDB",
        category=ConnectorCategory.DATABASE,
        docker_image="airbyte/source-yugabytedb:latest",
        supports_incremental=True,
    ),

    # =========================================================================
    # CRM CONNECTORS (10+)
    # =========================================================================
    "source-salesforce": ConnectorInfo(
        name="source-salesforce",
        display_name="Salesforce",
        category=ConnectorCategory.CRM,
        docker_image="airbyte/source-salesforce:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/salesforce",
        supports_incremental=True,
    ),
    "source-hubspot": ConnectorInfo(
        name="source-hubspot",
        display_name="HubSpot",
        category=ConnectorCategory.CRM,
        docker_image="airbyte/source-hubspot:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/hubspot",
        supports_incremental=True,
    ),
    "source-pipedrive": ConnectorInfo(
        name="source-pipedrive",
        display_name="Pipedrive",
        category=ConnectorCategory.CRM,
        docker_image="airbyte/source-pipedrive:latest",
        supports_incremental=True,
    ),
    "source-zoho-crm": ConnectorInfo(
        name="source-zoho-crm",
        display_name="Zoho CRM",
        category=ConnectorCategory.CRM,
        docker_image="airbyte/source-zoho-crm:latest",
        supports_incremental=True,
    ),
    "source-freshsales": ConnectorInfo(
        name="source-freshsales",
        display_name="Freshsales",
        category=ConnectorCategory.CRM,
        docker_image="airbyte/source-freshsales:latest",
        supports_incremental=True,
    ),
    "source-close-com": ConnectorInfo(
        name="source-close-com",
        display_name="Close.com",
        category=ConnectorCategory.CRM,
        docker_image="airbyte/source-close-com:latest",
        supports_incremental=True,
    ),
    "source-intercom": ConnectorInfo(
        name="source-intercom",
        display_name="Intercom",
        category=ConnectorCategory.CRM,
        docker_image="airbyte/source-intercom:latest",
        supports_incremental=True,
    ),
    "source-zendesk-support": ConnectorInfo(
        name="source-zendesk-support",
        display_name="Zendesk Support",
        category=ConnectorCategory.CRM,
        docker_image="airbyte/source-zendesk-support:latest",
        supports_incremental=True,
    ),
    "source-zendesk-chat": ConnectorInfo(
        name="source-zendesk-chat",
        display_name="Zendesk Chat",
        category=ConnectorCategory.CRM,
        docker_image="airbyte/source-zendesk-chat:latest",
        supports_incremental=True,
    ),
    "source-drift": ConnectorInfo(
        name="source-drift",
        display_name="Drift",
        category=ConnectorCategory.CRM,
        docker_image="airbyte/source-drift:latest",
        supports_incremental=True,
    ),

    # =========================================================================
    # MARKETING CONNECTORS (15+)
    # =========================================================================
    "source-google-ads": ConnectorInfo(
        name="source-google-ads",
        display_name="Google Ads",
        category=ConnectorCategory.MARKETING,
        docker_image="airbyte/source-google-ads:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/google-ads",
        supports_incremental=True,
    ),
    "source-facebook-marketing": ConnectorInfo(
        name="source-facebook-marketing",
        display_name="Facebook Marketing",
        category=ConnectorCategory.MARKETING,
        docker_image="airbyte/source-facebook-marketing:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/facebook-marketing",
        supports_incremental=True,
    ),
    "source-linkedin-ads": ConnectorInfo(
        name="source-linkedin-ads",
        display_name="LinkedIn Ads",
        category=ConnectorCategory.MARKETING,
        docker_image="airbyte/source-linkedin-ads:latest",
        supports_incremental=True,
    ),
    "source-twitter-ads": ConnectorInfo(
        name="source-twitter-ads",
        display_name="Twitter Ads",
        category=ConnectorCategory.MARKETING,
        docker_image="airbyte/source-twitter-ads:latest",
        supports_incremental=True,
    ),
    "source-tiktok-marketing": ConnectorInfo(
        name="source-tiktok-marketing",
        display_name="TikTok Marketing",
        category=ConnectorCategory.MARKETING,
        docker_image="airbyte/source-tiktok-marketing:latest",
        supports_incremental=True,
    ),
    "source-snapchat-marketing": ConnectorInfo(
        name="source-snapchat-marketing",
        display_name="Snapchat Marketing",
        category=ConnectorCategory.MARKETING,
        docker_image="airbyte/source-snapchat-marketing:latest",
        supports_incremental=True,
    ),
    "source-mailchimp": ConnectorInfo(
        name="source-mailchimp",
        display_name="Mailchimp",
        category=ConnectorCategory.MARKETING,
        docker_image="airbyte/source-mailchimp:latest",
        supports_incremental=True,
    ),
    "source-sendgrid": ConnectorInfo(
        name="source-sendgrid",
        display_name="SendGrid",
        category=ConnectorCategory.MARKETING,
        docker_image="airbyte/source-sendgrid:latest",
        supports_incremental=True,
    ),
    "source-klaviyo": ConnectorInfo(
        name="source-klaviyo",
        display_name="Klaviyo",
        category=ConnectorCategory.MARKETING,
        docker_image="airbyte/source-klaviyo:latest",
        supports_incremental=True,
    ),
    "source-braze": ConnectorInfo(
        name="source-braze",
        display_name="Braze",
        category=ConnectorCategory.MARKETING,
        docker_image="airbyte/source-braze:latest",
        supports_incremental=True,
    ),
    "source-iterable": ConnectorInfo(
        name="source-iterable",
        display_name="Iterable",
        category=ConnectorCategory.MARKETING,
        docker_image="airbyte/source-iterable:latest",
        supports_incremental=True,
    ),
    "source-marketo": ConnectorInfo(
        name="source-marketo",
        display_name="Marketo",
        category=ConnectorCategory.MARKETING,
        docker_image="airbyte/source-marketo:latest",
        supports_incremental=True,
    ),
    "source-google-search-console": ConnectorInfo(
        name="source-google-search-console",
        display_name="Google Search Console",
        category=ConnectorCategory.MARKETING,
        docker_image="airbyte/source-google-search-console:latest",
        supports_incremental=True,
    ),
    "source-bing-ads": ConnectorInfo(
        name="source-bing-ads",
        display_name="Bing Ads",
        category=ConnectorCategory.MARKETING,
        docker_image="airbyte/source-bing-ads:latest",
        supports_incremental=True,
    ),
    "source-pinterest": ConnectorInfo(
        name="source-pinterest",
        display_name="Pinterest Ads",
        category=ConnectorCategory.MARKETING,
        docker_image="airbyte/source-pinterest:latest",
        supports_incremental=True,
    ),

    # =========================================================================
    # ANALYTICS CONNECTORS (10+)
    # =========================================================================
    "source-google-analytics-v4": ConnectorInfo(
        name="source-google-analytics-v4",
        display_name="Google Analytics (UA)",
        category=ConnectorCategory.ANALYTICS,
        docker_image="airbyte/source-google-analytics-v4:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/google-analytics-v4",
        supports_incremental=True,
    ),
    "source-google-analytics-data-api": ConnectorInfo(
        name="source-google-analytics-data-api",
        display_name="Google Analytics 4 (GA4)",
        category=ConnectorCategory.ANALYTICS,
        docker_image="airbyte/source-google-analytics-data-api:latest",
        supports_incremental=True,
    ),
    "source-mixpanel": ConnectorInfo(
        name="source-mixpanel",
        display_name="Mixpanel",
        category=ConnectorCategory.ANALYTICS,
        docker_image="airbyte/source-mixpanel:latest",
        supports_incremental=True,
    ),
    "source-amplitude": ConnectorInfo(
        name="source-amplitude",
        display_name="Amplitude",
        category=ConnectorCategory.ANALYTICS,
        docker_image="airbyte/source-amplitude:latest",
        supports_incremental=True,
    ),
    "source-segment": ConnectorInfo(
        name="source-segment",
        display_name="Segment",
        category=ConnectorCategory.ANALYTICS,
        docker_image="airbyte/source-segment:latest",
        supports_incremental=True,
    ),
    "source-heap": ConnectorInfo(
        name="source-heap",
        display_name="Heap",
        category=ConnectorCategory.ANALYTICS,
        docker_image="airbyte/source-heap:latest",
        supports_incremental=True,
    ),
    "source-posthog": ConnectorInfo(
        name="source-posthog",
        display_name="PostHog",
        category=ConnectorCategory.ANALYTICS,
        docker_image="airbyte/source-posthog:latest",
        supports_incremental=True,
    ),
    "source-pendo": ConnectorInfo(
        name="source-pendo",
        display_name="Pendo",
        category=ConnectorCategory.ANALYTICS,
        docker_image="airbyte/source-pendo:latest",
        supports_incremental=True,
    ),
    "source-hotjar": ConnectorInfo(
        name="source-hotjar",
        display_name="Hotjar",
        category=ConnectorCategory.ANALYTICS,
        docker_image="airbyte/source-hotjar:latest",
        supports_incremental=False,
    ),
    "source-fullstory": ConnectorInfo(
        name="source-fullstory",
        display_name="FullStory",
        category=ConnectorCategory.ANALYTICS,
        docker_image="airbyte/source-fullstory:latest",
        supports_incremental=True,
    ),

    # =========================================================================
    # E-COMMERCE CONNECTORS (10+)
    # =========================================================================
    "source-shopify": ConnectorInfo(
        name="source-shopify",
        display_name="Shopify",
        category=ConnectorCategory.ECOMMERCE,
        docker_image="airbyte/source-shopify:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/shopify",
        supports_incremental=True,
    ),
    "source-stripe": ConnectorInfo(
        name="source-stripe",
        display_name="Stripe",
        category=ConnectorCategory.ECOMMERCE,
        docker_image="airbyte/source-stripe:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/stripe",
        supports_incremental=True,
    ),
    "source-woocommerce": ConnectorInfo(
        name="source-woocommerce",
        display_name="WooCommerce",
        category=ConnectorCategory.ECOMMERCE,
        docker_image="airbyte/source-woocommerce:latest",
        supports_incremental=True,
    ),
    "source-amazon-seller-partner": ConnectorInfo(
        name="source-amazon-seller-partner",
        display_name="Amazon Seller Partner",
        category=ConnectorCategory.ECOMMERCE,
        docker_image="airbyte/source-amazon-seller-partner:latest",
        supports_incremental=True,
    ),
    "source-magento": ConnectorInfo(
        name="source-magento",
        display_name="Magento",
        category=ConnectorCategory.ECOMMERCE,
        docker_image="airbyte/source-magento:latest",
        supports_incremental=True,
    ),
    "source-bigcommerce": ConnectorInfo(
        name="source-bigcommerce",
        display_name="BigCommerce",
        category=ConnectorCategory.ECOMMERCE,
        docker_image="airbyte/source-bigcommerce:latest",
        supports_incremental=True,
    ),
    "source-square": ConnectorInfo(
        name="source-square",
        display_name="Square",
        category=ConnectorCategory.ECOMMERCE,
        docker_image="airbyte/source-square:latest",
        supports_incremental=True,
    ),
    "source-paypal-transaction": ConnectorInfo(
        name="source-paypal-transaction",
        display_name="PayPal Transactions",
        category=ConnectorCategory.ECOMMERCE,
        docker_image="airbyte/source-paypal-transaction:latest",
        supports_incremental=True,
    ),
    "source-recharge": ConnectorInfo(
        name="source-recharge",
        display_name="Recharge",
        category=ConnectorCategory.ECOMMERCE,
        docker_image="airbyte/source-recharge:latest",
        supports_incremental=True,
    ),
    "source-chargebee": ConnectorInfo(
        name="source-chargebee",
        display_name="Chargebee",
        category=ConnectorCategory.ECOMMERCE,
        docker_image="airbyte/source-chargebee:latest",
        supports_incremental=True,
    ),

    # =========================================================================
    # FINANCE CONNECTORS (10+)
    # =========================================================================
    "source-quickbooks": ConnectorInfo(
        name="source-quickbooks",
        display_name="QuickBooks",
        category=ConnectorCategory.FINANCE,
        docker_image="airbyte/source-quickbooks:latest",
        supports_incremental=True,
    ),
    "source-xero": ConnectorInfo(
        name="source-xero",
        display_name="Xero",
        category=ConnectorCategory.FINANCE,
        docker_image="airbyte/source-xero:latest",
        supports_incremental=True,
    ),
    "source-netsuite": ConnectorInfo(
        name="source-netsuite",
        display_name="NetSuite",
        category=ConnectorCategory.FINANCE,
        docker_image="airbyte/source-netsuite:latest",
        supports_incremental=True,
    ),
    "source-freshbooks": ConnectorInfo(
        name="source-freshbooks",
        display_name="FreshBooks",
        category=ConnectorCategory.FINANCE,
        docker_image="airbyte/source-freshbooks:latest",
        supports_incremental=True,
    ),
    "source-recurly": ConnectorInfo(
        name="source-recurly",
        display_name="Recurly",
        category=ConnectorCategory.FINANCE,
        docker_image="airbyte/source-recurly:latest",
        supports_incremental=True,
    ),
    "source-zuora": ConnectorInfo(
        name="source-zuora",
        display_name="Zuora",
        category=ConnectorCategory.FINANCE,
        docker_image="airbyte/source-zuora:latest",
        supports_incremental=True,
    ),
    "source-harvest": ConnectorInfo(
        name="source-harvest",
        display_name="Harvest",
        category=ConnectorCategory.FINANCE,
        docker_image="airbyte/source-harvest:latest",
        supports_incremental=True,
    ),
    "source-plaid": ConnectorInfo(
        name="source-plaid",
        display_name="Plaid",
        category=ConnectorCategory.FINANCE,
        docker_image="airbyte/source-plaid:latest",
        supports_incremental=False,
    ),
    "source-braintree": ConnectorInfo(
        name="source-braintree",
        display_name="Braintree",
        category=ConnectorCategory.FINANCE,
        docker_image="airbyte/source-braintree:latest",
        supports_incremental=True,
    ),
    "source-sage-intacct": ConnectorInfo(
        name="source-sage-intacct",
        display_name="Sage Intacct",
        category=ConnectorCategory.FINANCE,
        docker_image="airbyte/source-sage-intacct:latest",
        supports_incremental=True,
    ),

    # =========================================================================
    # PRODUCTIVITY / PROJECT MANAGEMENT (10+)
    # =========================================================================
    "source-jira": ConnectorInfo(
        name="source-jira",
        display_name="Jira",
        category=ConnectorCategory.PRODUCTIVITY,
        docker_image="airbyte/source-jira:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/jira",
        supports_incremental=True,
    ),
    "source-asana": ConnectorInfo(
        name="source-asana",
        display_name="Asana",
        category=ConnectorCategory.PRODUCTIVITY,
        docker_image="airbyte/source-asana:latest",
        supports_incremental=True,
    ),
    "source-trello": ConnectorInfo(
        name="source-trello",
        display_name="Trello",
        category=ConnectorCategory.PRODUCTIVITY,
        docker_image="airbyte/source-trello:latest",
        supports_incremental=False,
    ),
    "source-monday": ConnectorInfo(
        name="source-monday",
        display_name="Monday.com",
        category=ConnectorCategory.PRODUCTIVITY,
        docker_image="airbyte/source-monday:latest",
        supports_incremental=True,
    ),
    "source-notion": ConnectorInfo(
        name="source-notion",
        display_name="Notion",
        category=ConnectorCategory.PRODUCTIVITY,
        docker_image="airbyte/source-notion:latest",
        supports_incremental=True,
    ),
    "source-airtable": ConnectorInfo(
        name="source-airtable",
        display_name="Airtable",
        category=ConnectorCategory.PRODUCTIVITY,
        docker_image="airbyte/source-airtable:latest",
        supports_incremental=False,
    ),
    "source-clickup-api": ConnectorInfo(
        name="source-clickup-api",
        display_name="ClickUp",
        category=ConnectorCategory.PRODUCTIVITY,
        docker_image="airbyte/source-clickup-api:latest",
        supports_incremental=True,
    ),
    "source-smartsheets": ConnectorInfo(
        name="source-smartsheets",
        display_name="Smartsheet",
        category=ConnectorCategory.PRODUCTIVITY,
        docker_image="airbyte/source-smartsheets:latest",
        supports_incremental=False,
    ),
    "source-basecamp": ConnectorInfo(
        name="source-basecamp",
        display_name="Basecamp",
        category=ConnectorCategory.PRODUCTIVITY,
        docker_image="airbyte/source-basecamp:latest",
        supports_incremental=False,
    ),
    "source-todoist": ConnectorInfo(
        name="source-todoist",
        display_name="Todoist",
        category=ConnectorCategory.PRODUCTIVITY,
        docker_image="airbyte/source-todoist:latest",
        supports_incremental=False,
    ),

    # =========================================================================
    # HR / RECRUITING (8+)
    # =========================================================================
    "source-greenhouse": ConnectorInfo(
        name="source-greenhouse",
        display_name="Greenhouse",
        category=ConnectorCategory.HR,
        docker_image="airbyte/source-greenhouse:latest",
        supports_incremental=True,
    ),
    "source-lever-hiring": ConnectorInfo(
        name="source-lever-hiring",
        display_name="Lever",
        category=ConnectorCategory.HR,
        docker_image="airbyte/source-lever-hiring:latest",
        supports_incremental=True,
    ),
    "source-bamboo-hr": ConnectorInfo(
        name="source-bamboo-hr",
        display_name="BambooHR",
        category=ConnectorCategory.HR,
        docker_image="airbyte/source-bamboo-hr:latest",
        supports_incremental=True,
    ),
    "source-workday": ConnectorInfo(
        name="source-workday",
        display_name="Workday",
        category=ConnectorCategory.HR,
        docker_image="airbyte/source-workday:latest",
        supports_incremental=True,
    ),
    "source-personio": ConnectorInfo(
        name="source-personio",
        display_name="Personio",
        category=ConnectorCategory.HR,
        docker_image="airbyte/source-personio:latest",
        supports_incremental=True,
    ),
    "source-recruitee": ConnectorInfo(
        name="source-recruitee",
        display_name="Recruitee",
        category=ConnectorCategory.HR,
        docker_image="airbyte/source-recruitee:latest",
        supports_incremental=True,
    ),
    "source-gusto": ConnectorInfo(
        name="source-gusto",
        display_name="Gusto",
        category=ConnectorCategory.HR,
        docker_image="airbyte/source-gusto:latest",
        supports_incremental=True,
    ),
    "source-namely": ConnectorInfo(
        name="source-namely",
        display_name="Namely",
        category=ConnectorCategory.HR,
        docker_image="airbyte/source-namely:latest",
        supports_incremental=True,
    ),

    # =========================================================================
    # COMMUNICATION (8+)
    # =========================================================================
    "source-slack": ConnectorInfo(
        name="source-slack",
        display_name="Slack",
        category=ConnectorCategory.COMMUNICATION,
        docker_image="airbyte/source-slack:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/slack",
        supports_incremental=True,
    ),
    "source-microsoft-teams": ConnectorInfo(
        name="source-microsoft-teams",
        display_name="Microsoft Teams",
        category=ConnectorCategory.COMMUNICATION,
        docker_image="airbyte/source-microsoft-teams:latest",
        supports_incremental=True,
    ),
    "source-twilio": ConnectorInfo(
        name="source-twilio",
        display_name="Twilio",
        category=ConnectorCategory.COMMUNICATION,
        docker_image="airbyte/source-twilio:latest",
        supports_incremental=True,
    ),
    "source-mailgun": ConnectorInfo(
        name="source-mailgun",
        display_name="Mailgun",
        category=ConnectorCategory.COMMUNICATION,
        docker_image="airbyte/source-mailgun:latest",
        supports_incremental=True,
    ),
    "source-zendesk-talk": ConnectorInfo(
        name="source-zendesk-talk",
        display_name="Zendesk Talk",
        category=ConnectorCategory.COMMUNICATION,
        docker_image="airbyte/source-zendesk-talk:latest",
        supports_incremental=True,
    ),
    "source-dixa": ConnectorInfo(
        name="source-dixa",
        display_name="Dixa",
        category=ConnectorCategory.COMMUNICATION,
        docker_image="airbyte/source-dixa:latest",
        supports_incremental=True,
    ),
    "source-front": ConnectorInfo(
        name="source-front",
        display_name="Front",
        category=ConnectorCategory.COMMUNICATION,
        docker_image="airbyte/source-front:latest",
        supports_incremental=True,
    ),
    "source-lemlist": ConnectorInfo(
        name="source-lemlist",
        display_name="Lemlist",
        category=ConnectorCategory.COMMUNICATION,
        docker_image="airbyte/source-lemlist:latest",
        supports_incremental=False,
    ),

    # =========================================================================
    # DEVELOPMENT / DEVOPS (10+)
    # =========================================================================
    "source-github": ConnectorInfo(
        name="source-github",
        display_name="GitHub",
        category=ConnectorCategory.DEVELOPMENT,
        docker_image="airbyte/source-github:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/github",
        supports_incremental=True,
    ),
    "source-gitlab": ConnectorInfo(
        name="source-gitlab",
        display_name="GitLab",
        category=ConnectorCategory.DEVELOPMENT,
        docker_image="airbyte/source-gitlab:latest",
        supports_incremental=True,
    ),
    "source-bitbucket": ConnectorInfo(
        name="source-bitbucket",
        display_name="Bitbucket",
        category=ConnectorCategory.DEVELOPMENT,
        docker_image="airbyte/source-bitbucket:latest",
        supports_incremental=True,
    ),
    "source-datadog": ConnectorInfo(
        name="source-datadog",
        display_name="Datadog",
        category=ConnectorCategory.DEVELOPMENT,
        docker_image="airbyte/source-datadog:latest",
        supports_incremental=True,
    ),
    "source-pagerduty": ConnectorInfo(
        name="source-pagerduty",
        display_name="PagerDuty",
        category=ConnectorCategory.DEVELOPMENT,
        docker_image="airbyte/source-pagerduty:latest",
        supports_incremental=True,
    ),
    "source-sentry": ConnectorInfo(
        name="source-sentry",
        display_name="Sentry",
        category=ConnectorCategory.DEVELOPMENT,
        docker_image="airbyte/source-sentry:latest",
        supports_incremental=True,
    ),
    "source-sonar-cloud": ConnectorInfo(
        name="source-sonar-cloud",
        display_name="SonarCloud",
        category=ConnectorCategory.DEVELOPMENT,
        docker_image="airbyte/source-sonar-cloud:latest",
        supports_incremental=False,
    ),
    "source-circleci": ConnectorInfo(
        name="source-circleci",
        display_name="CircleCI",
        category=ConnectorCategory.DEVELOPMENT,
        docker_image="airbyte/source-circleci:latest",
        supports_incremental=True,
    ),
    "source-jenkins": ConnectorInfo(
        name="source-jenkins",
        display_name="Jenkins",
        category=ConnectorCategory.DEVELOPMENT,
        docker_image="airbyte/source-jenkins:latest",
        supports_incremental=False,
    ),
    "source-linear": ConnectorInfo(
        name="source-linear",
        display_name="Linear",
        category=ConnectorCategory.DEVELOPMENT,
        docker_image="airbyte/source-linear:latest",
        supports_incremental=True,
    ),

    # =========================================================================
    # FILE / STORAGE (8+)
    # =========================================================================
    "source-s3": ConnectorInfo(
        name="source-s3",
        display_name="Amazon S3",
        category=ConnectorCategory.STORAGE,
        docker_image="airbyte/source-s3:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/s3",
        supports_incremental=True,
    ),
    "source-gcs": ConnectorInfo(
        name="source-gcs",
        display_name="Google Cloud Storage",
        category=ConnectorCategory.STORAGE,
        docker_image="airbyte/source-gcs:latest",
        supports_incremental=True,
    ),
    "source-azure-blob-storage": ConnectorInfo(
        name="source-azure-blob-storage",
        display_name="Azure Blob Storage",
        category=ConnectorCategory.STORAGE,
        docker_image="airbyte/source-azure-blob-storage:latest",
        supports_incremental=True,
    ),
    "source-sftp": ConnectorInfo(
        name="source-sftp",
        display_name="SFTP",
        category=ConnectorCategory.STORAGE,
        docker_image="airbyte/source-sftp:latest",
        supports_incremental=True,
    ),
    "source-google-drive": ConnectorInfo(
        name="source-google-drive",
        display_name="Google Drive",
        category=ConnectorCategory.STORAGE,
        docker_image="airbyte/source-google-drive:latest",
        supports_incremental=False,
    ),
    "source-dropbox": ConnectorInfo(
        name="source-dropbox",
        display_name="Dropbox",
        category=ConnectorCategory.STORAGE,
        docker_image="airbyte/source-dropbox:latest",
        supports_incremental=False,
    ),
    "source-onedrive": ConnectorInfo(
        name="source-onedrive",
        display_name="OneDrive",
        category=ConnectorCategory.STORAGE,
        docker_image="airbyte/source-onedrive:latest",
        supports_incremental=False,
    ),
    "source-google-sheets": ConnectorInfo(
        name="source-google-sheets",
        display_name="Google Sheets",
        category=ConnectorCategory.FILE,
        docker_image="airbyte/source-google-sheets:latest",
        documentation_url="https://docs.airbyte.com/integrations/sources/google-sheets",
        supports_incremental=False,
    ),

    # =========================================================================
    # API / GENERIC (5+)
    # =========================================================================
    "source-http-request": ConnectorInfo(
        name="source-http-request",
        display_name="HTTP Request",
        category=ConnectorCategory.API,
        docker_image="airbyte/source-http-request:latest",
        supports_incremental=False,
    ),
    "source-graphql": ConnectorInfo(
        name="source-graphql",
        display_name="GraphQL",
        category=ConnectorCategory.API,
        docker_image="airbyte/source-graphql:latest",
        supports_incremental=False,
    ),
    "source-faker": ConnectorInfo(
        name="source-faker",
        display_name="Faker (Sample Data)",
        category=ConnectorCategory.OTHER,
        docker_image="airbyte/source-faker:latest",
        supports_incremental=False,
    ),
    "source-file": ConnectorInfo(
        name="source-file",
        display_name="File (CSV, JSON, etc.)",
        category=ConnectorCategory.FILE,
        docker_image="airbyte/source-file:latest",
        supports_incremental=False,
    ),
    "source-pokeapi": ConnectorInfo(
        name="source-pokeapi",
        display_name="PokeAPI (Sample)",
        category=ConnectorCategory.OTHER,
        docker_image="airbyte/source-pokeapi:latest",
        supports_incremental=False,
    ),
}


# =============================================================================
# Registry Functions
# =============================================================================


def get_connector_image(connector_name: str) -> str:
    """
    Get Docker image for a connector.

    Args:
        connector_name: Connector name (e.g., "source-postgres" or "postgres")

    Returns:
        Full Docker image name (e.g., "airbyte/source-postgres:latest")

    Raises:
        ValueError: If connector not found
    """
    # Normalize name
    if not connector_name.startswith("source-"):
        connector_name = f"source-{connector_name}"

    connector = AIRBYTE_CONNECTORS.get(connector_name)
    if connector:
        return connector.docker_image

    # Fallback: construct default image name
    logger.warning(
        f"Connector '{connector_name}' not in registry, using default image pattern"
    )
    return f"airbyte/{connector_name}:latest"


def get_connector_info(connector_name: str) -> ConnectorInfo | None:
    """
    Get full information about a connector.

    Args:
        connector_name: Connector name

    Returns:
        ConnectorInfo or None if not found
    """
    if not connector_name.startswith("source-"):
        connector_name = f"source-{connector_name}"

    return AIRBYTE_CONNECTORS.get(connector_name)


def list_connectors(
    category: ConnectorCategory | str | None = None,
) -> list[ConnectorInfo]:
    """
    List all available connectors.

    Args:
        category: Optional category filter

    Returns:
        List of ConnectorInfo objects
    """
    connectors = list(AIRBYTE_CONNECTORS.values())

    if category:
        if isinstance(category, str):
            category = ConnectorCategory(category)
        connectors = [c for c in connectors if c.category == category]

    return sorted(connectors, key=lambda c: c.display_name)


def list_categories() -> list[ConnectorCategory]:
    """List all connector categories."""
    return list(ConnectorCategory)


def search_connectors(query: str) -> list[ConnectorInfo]:
    """
    Search connectors by name or display name.

    Args:
        query: Search query (case-insensitive)

    Returns:
        List of matching ConnectorInfo objects
    """
    query = query.lower()
    return [
        c
        for c in AIRBYTE_CONNECTORS.values()
        if query in c.name.lower() or query in c.display_name.lower()
    ]


def get_connector_count() -> int:
    """Get total number of registered connectors."""
    return len(AIRBYTE_CONNECTORS)


def get_category_counts() -> dict[str, int]:
    """Get connector counts by category."""
    counts: dict[str, int] = {}
    for connector in AIRBYTE_CONNECTORS.values():
        cat = connector.category.value
        counts[cat] = counts.get(cat, 0) + 1
    return counts


# =============================================================================
# Registry Summary
# =============================================================================

REGISTRY_SUMMARY = f"""
Airbyte Connector Registry
==========================
Total Connectors: {get_connector_count()}

Categories:
{chr(10).join(f'  - {cat.value}: {get_category_counts().get(cat.value, 0)}' for cat in ConnectorCategory)}

Popular Connectors:
  - Database: PostgreSQL, MySQL, MongoDB, Snowflake, BigQuery
  - CRM: Salesforce, HubSpot, Zendesk
  - Marketing: Google Ads, Facebook Ads, Mailchimp
  - Analytics: Google Analytics, Mixpanel, Amplitude
  - E-Commerce: Shopify, Stripe, WooCommerce
  - Development: GitHub, GitLab, Jira
"""

if __name__ == "__main__":
    print(REGISTRY_SUMMARY)
