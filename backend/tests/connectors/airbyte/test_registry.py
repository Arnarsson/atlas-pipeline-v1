"""
Tests for Airbyte Connector Registry
====================================

Tests the connector registry with 100+ Airbyte Docker images.
"""

import pytest

from app.connectors.airbyte.registry import (
    ConnectorCategory,
    ConnectorInfo,
    AIRBYTE_CONNECTORS,
    get_connector_image,
    get_connector_info,
    list_connectors,
    list_categories,
    search_connectors,
    get_connector_count,
    get_category_counts,
)


class TestConnectorRegistry:
    """Test connector registry contents."""

    def test_registry_has_connectors(self):
        """Test that registry contains connectors."""
        count = get_connector_count()
        assert count >= 100, f"Expected 100+ connectors, got {count}"

    def test_registry_has_all_categories(self):
        """Test that all categories have connectors."""
        counts = get_category_counts()

        # Check major categories have connectors
        assert counts.get("database", 0) >= 10
        assert counts.get("crm", 0) >= 5
        assert counts.get("marketing", 0) >= 5
        assert counts.get("analytics", 0) >= 5
        assert counts.get("ecommerce", 0) >= 5
        assert counts.get("development", 0) >= 5

    def test_all_connectors_have_required_fields(self):
        """Test that all connectors have required fields."""
        for name, connector in AIRBYTE_CONNECTORS.items():
            assert connector.name, f"Connector {name} missing name"
            assert connector.display_name, f"Connector {name} missing display_name"
            assert connector.docker_image, f"Connector {name} missing docker_image"
            assert connector.category, f"Connector {name} missing category"

    def test_docker_images_follow_pattern(self):
        """Test that Docker images follow airbyte/source-* pattern."""
        for name, connector in AIRBYTE_CONNECTORS.items():
            assert connector.docker_image.startswith("airbyte/"), \
                f"Connector {name} image should start with 'airbyte/'"
            assert ":latest" in connector.docker_image or ":" in connector.docker_image, \
                f"Connector {name} image should have a tag"


class TestGetConnectorImage:
    """Test get_connector_image function."""

    def test_get_postgres_image(self):
        """Test getting PostgreSQL connector image."""
        image = get_connector_image("source-postgres")
        assert image == "airbyte/source-postgres:latest"

    def test_get_mysql_image(self):
        """Test getting MySQL connector image."""
        image = get_connector_image("source-mysql")
        assert image == "airbyte/source-mysql:latest"

    def test_get_image_without_prefix(self):
        """Test getting image without 'source-' prefix."""
        image = get_connector_image("postgres")
        assert image == "airbyte/source-postgres:latest"

    def test_get_salesforce_image(self):
        """Test getting Salesforce connector image."""
        image = get_connector_image("source-salesforce")
        assert image == "airbyte/source-salesforce:latest"

    def test_get_unknown_connector_returns_default(self):
        """Test that unknown connectors return a default pattern."""
        image = get_connector_image("source-unknown-connector")
        assert image == "airbyte/source-unknown-connector:latest"


class TestGetConnectorInfo:
    """Test get_connector_info function."""

    def test_get_postgres_info(self):
        """Test getting PostgreSQL connector info."""
        info = get_connector_info("source-postgres")

        assert info is not None
        assert info.name == "source-postgres"
        assert info.display_name == "PostgreSQL"
        assert info.category == ConnectorCategory.DATABASE
        assert info.supports_incremental is True

    def test_get_info_without_prefix(self):
        """Test getting info without 'source-' prefix."""
        info = get_connector_info("postgres")

        assert info is not None
        assert info.name == "source-postgres"

    def test_get_unknown_connector_returns_none(self):
        """Test that unknown connectors return None."""
        info = get_connector_info("source-unknown-connector")
        assert info is None


class TestListConnectors:
    """Test list_connectors function."""

    def test_list_all_connectors(self):
        """Test listing all connectors."""
        connectors = list_connectors()

        assert len(connectors) >= 100
        # Should be sorted by display name
        names = [c.display_name for c in connectors]
        assert names == sorted(names)

    def test_list_database_connectors(self):
        """Test listing database connectors only."""
        connectors = list_connectors(category=ConnectorCategory.DATABASE)

        assert len(connectors) >= 10
        for c in connectors:
            assert c.category == ConnectorCategory.DATABASE

    def test_list_by_string_category(self):
        """Test listing by string category."""
        connectors = list_connectors(category="crm")

        assert len(connectors) >= 5
        for c in connectors:
            assert c.category == ConnectorCategory.CRM


class TestListCategories:
    """Test list_categories function."""

    def test_list_all_categories(self):
        """Test listing all categories."""
        categories = list_categories()

        assert ConnectorCategory.DATABASE in categories
        assert ConnectorCategory.CRM in categories
        assert ConnectorCategory.MARKETING in categories
        assert ConnectorCategory.ANALYTICS in categories
        assert ConnectorCategory.ECOMMERCE in categories


class TestSearchConnectors:
    """Test search_connectors function."""

    def test_search_by_name(self):
        """Test searching by connector name."""
        results = search_connectors("postgres")

        assert len(results) >= 1
        assert any(c.name == "source-postgres" for c in results)

    def test_search_by_display_name(self):
        """Test searching by display name."""
        results = search_connectors("PostgreSQL")

        assert len(results) >= 1
        assert any(c.display_name == "PostgreSQL" for c in results)

    def test_search_case_insensitive(self):
        """Test that search is case-insensitive."""
        results_lower = search_connectors("mysql")
        results_upper = search_connectors("MySQL")

        assert len(results_lower) == len(results_upper)

    def test_search_partial_match(self):
        """Test partial matching."""
        results = search_connectors("google")

        # Should match Google Ads, Google Analytics, Google Sheets, etc.
        assert len(results) >= 3

    def test_search_no_results(self):
        """Test search with no results."""
        results = search_connectors("nonexistentconnector123")
        assert len(results) == 0


class TestGetCategoryCounts:
    """Test get_category_counts function."""

    def test_category_counts(self):
        """Test getting category counts."""
        counts = get_category_counts()

        # Verify structure
        assert isinstance(counts, dict)

        # Verify major categories
        assert "database" in counts
        assert "crm" in counts
        assert "marketing" in counts

        # Verify counts are positive
        for category, count in counts.items():
            assert count > 0, f"Category {category} should have connectors"


class TestConnectorInfo:
    """Test ConnectorInfo dataclass."""

    def test_connector_info_fields(self):
        """Test ConnectorInfo has all expected fields."""
        info = ConnectorInfo(
            name="source-test",
            display_name="Test Connector",
            category=ConnectorCategory.DATABASE,
            docker_image="airbyte/source-test:latest",
            documentation_url="https://docs.example.com",
            supports_incremental=True,
            supports_normalization=False,
        )

        assert info.name == "source-test"
        assert info.display_name == "Test Connector"
        assert info.category == ConnectorCategory.DATABASE
        assert info.docker_image == "airbyte/source-test:latest"
        assert info.documentation_url == "https://docs.example.com"
        assert info.supports_incremental is True
        assert info.supports_normalization is False


class TestPopularConnectors:
    """Test that popular connectors are properly registered."""

    @pytest.mark.parametrize("connector_name,expected_display", [
        ("source-postgres", "PostgreSQL"),
        ("source-mysql", "MySQL"),
        ("source-mongodb-v2", "MongoDB"),
        ("source-snowflake", "Snowflake"),
        ("source-bigquery", "Google BigQuery"),
        ("source-salesforce", "Salesforce"),
        ("source-hubspot", "HubSpot"),
        ("source-stripe", "Stripe"),
        ("source-shopify", "Shopify"),
        ("source-github", "GitHub"),
        ("source-slack", "Slack"),
        ("source-jira", "Jira"),
        ("source-google-ads", "Google Ads"),
        ("source-facebook-marketing", "Facebook Marketing"),
        ("source-mixpanel", "Mixpanel"),
        ("source-amplitude", "Amplitude"),
        ("source-s3", "Amazon S3"),
        ("source-google-sheets", "Google Sheets"),
        ("source-notion", "Notion"),
        ("source-airtable", "Airtable"),
    ])
    def test_popular_connector_exists(self, connector_name, expected_display):
        """Test that popular connectors are registered."""
        info = get_connector_info(connector_name)

        assert info is not None, f"Connector {connector_name} not found"
        assert info.display_name == expected_display


class TestConnectorCategories:
    """Test connector categorization."""

    def test_database_connectors(self):
        """Test database connectors are properly categorized."""
        db_connectors = list_connectors(category=ConnectorCategory.DATABASE)

        expected_names = [
            "source-postgres", "source-mysql", "source-mssql",
            "source-mongodb-v2", "source-snowflake", "source-bigquery"
        ]

        connector_names = [c.name for c in db_connectors]
        for name in expected_names:
            assert name in connector_names, f"{name} should be in database category"

    def test_crm_connectors(self):
        """Test CRM connectors are properly categorized."""
        crm_connectors = list_connectors(category=ConnectorCategory.CRM)

        expected_names = ["source-salesforce", "source-hubspot", "source-pipedrive"]

        connector_names = [c.name for c in crm_connectors]
        for name in expected_names:
            assert name in connector_names, f"{name} should be in CRM category"

    def test_marketing_connectors(self):
        """Test marketing connectors are properly categorized."""
        marketing_connectors = list_connectors(category=ConnectorCategory.MARKETING)

        expected_names = ["source-google-ads", "source-facebook-marketing", "source-mailchimp"]

        connector_names = [c.name for c in marketing_connectors]
        for name in expected_names:
            assert name in connector_names, f"{name} should be in marketing category"
