"""Tests for Salesforce connector."""

from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest
import requests

from app.connectors.base import ConnectionConfig
from app.connectors.salesforce import SalesforceConnector


@pytest.fixture
def salesforce_config():
    """Salesforce connector configuration."""
    return ConnectionConfig(
        source_type="salesforce",
        source_name="test_salesforce",
        additional_params={
            "instance_url": "https://test.salesforce.com",
            "access_token": "test_access_token_123",
            "api_version": "v58.0",
        }
    )


@pytest.mark.asyncio
class TestSalesforceConnector:
    """Test Salesforce connector functionality."""

    async def test_init_success(self, salesforce_config):
        """Test successful connector initialization."""
        connector = SalesforceConnector(salesforce_config)
        assert connector._instance_url == "https://test.salesforce.com"
        assert connector._access_token == "test_access_token_123"
        assert connector._api_version == "v58.0"

    async def test_init_missing_instance_url(self):
        """Test initialization fails without instance_url."""
        config = ConnectionConfig(
            source_type="salesforce",
            source_name="test",
            additional_params={
                "access_token": "test123",
            }
        )
        with pytest.raises(ValueError, match="instance_url is required"):
            SalesforceConnector(config)

    async def test_init_missing_access_token(self):
        """Test initialization fails without access_token."""
        config = ConnectionConfig(
            source_type="salesforce",
            source_name="test",
            additional_params={
                "instance_url": "https://test.salesforce.com",
            }
        )
        with pytest.raises(ValueError, match="access_token is required"):
            SalesforceConnector(config)

    @patch('app.connectors.salesforce.requests.Session')
    async def test_test_connection_success(self, mock_session_class, salesforce_config):
        """Test successful connection test."""
        # Mock session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response

        connector = SalesforceConnector(salesforce_config)
        result = await connector.test_connection()

        assert result is True
        mock_session.get.assert_called_once()

    @patch('app.connectors.salesforce.requests.Session')
    async def test_test_connection_auth_failure(self, mock_session_class, salesforce_config):
        """Test connection failure with 401."""
        # Mock session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_session.get.return_value = mock_response

        connector = SalesforceConnector(salesforce_config)
        with pytest.raises(ConnectionError, match="authentication failed"):
            await connector.test_connection()

    @patch('app.connectors.salesforce.requests.Session')
    async def test_get_data_with_table(self, mock_session_class, salesforce_config):
        """Test data retrieval with table name."""
        # Mock session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock describe response (for getting fields)
        describe_response = Mock()
        describe_response.status_code = 200
        describe_response.json.return_value = {
            'fields': [
                {'name': 'Id', 'type': 'id'},
                {'name': 'Name', 'type': 'string'},
                {'name': 'Industry', 'type': 'string'},
            ]
        }

        # Mock query response
        query_response = Mock()
        query_response.status_code = 200
        query_response.json.return_value = {
            'totalSize': 2,
            'done': True,
            'records': [
                {
                    'attributes': {'type': 'Account'},
                    'Id': '001',
                    'Name': 'Acme Corp',
                    'Industry': 'Technology'
                },
                {
                    'attributes': {'type': 'Account'},
                    'Id': '002',
                    'Name': 'Global Inc',
                    'Industry': 'Finance'
                },
            ]
        }

        # Configure mock to return different responses
        mock_session.get.side_effect = [describe_response, query_response]

        connector = SalesforceConnector(salesforce_config)
        df = await connector.get_data(table='Account')

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'Name' in df.columns
        assert df.iloc[0]['Name'] == 'Acme Corp'
        # Attributes field should be removed
        assert 'attributes' not in df.columns

    @patch('app.connectors.salesforce.requests.Session')
    async def test_get_data_with_soql_query(self, mock_session_class, salesforce_config):
        """Test data retrieval with custom SOQL query."""
        # Mock session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock query response
        query_response = Mock()
        query_response.status_code = 200
        query_response.json.return_value = {
            'totalSize': 1,
            'done': True,
            'records': [
                {
                    'attributes': {'type': 'Contact'},
                    'Id': '003',
                    'FirstName': 'John',
                    'LastName': 'Doe',
                },
            ]
        }

        mock_session.get.return_value = query_response

        connector = SalesforceConnector(salesforce_config)
        df = await connector.get_data(query="SELECT Id, FirstName, LastName FROM Contact")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]['FirstName'] == 'John'

    @patch('app.connectors.salesforce.requests.Session')
    async def test_get_schema(self, mock_session_class, salesforce_config):
        """Test schema retrieval."""
        # Mock session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock describe response
        describe_response = Mock()
        describe_response.status_code = 200
        describe_response.json.return_value = {
            'fields': [
                {'name': 'Id', 'type': 'id'},
                {'name': 'Name', 'type': 'string'},
                {'name': 'AnnualRevenue', 'type': 'currency'},
                {'name': 'CreatedDate', 'type': 'datetime'},
                {'name': 'IsDeleted', 'type': 'boolean'},
            ]
        }

        mock_session.get.return_value = describe_response

        connector = SalesforceConnector(salesforce_config)
        schema = await connector.get_schema('Account')

        assert isinstance(schema, dict)
        assert schema['Id'] == 'string'
        assert schema['Name'] == 'string'
        assert schema['AnnualRevenue'] == 'numeric'
        assert schema['CreatedDate'] == 'datetime'
        assert schema['IsDeleted'] == 'boolean'

    @patch('app.connectors.salesforce.requests.Session')
    async def test_get_row_count(self, mock_session_class, salesforce_config):
        """Test row count retrieval."""
        # Mock session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock count response
        count_response = Mock()
        count_response.status_code = 200
        count_response.json.return_value = {
            'totalSize': 500,
            'done': True,
        }

        mock_session.get.return_value = count_response

        connector = SalesforceConnector(salesforce_config)
        count = await connector.get_row_count('Account')

        assert count == 500

    @patch('app.connectors.salesforce.requests.Session')
    async def test_list_objects(self, mock_session_class, salesforce_config):
        """Test listing Salesforce objects."""
        # Mock session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock sobjects response
        sobjects_response = Mock()
        sobjects_response.status_code = 200
        sobjects_response.json.return_value = {
            'sobjects': [
                {
                    'name': 'Account',
                    'label': 'Account',
                    'queryable': True,
                    'createable': True,
                    'updateable': True,
                },
                {
                    'name': 'CustomObject__c',
                    'label': 'Custom Object',
                    'queryable': True,
                    'createable': True,
                    'updateable': True,
                },
            ]
        }

        mock_session.get.return_value = sobjects_response

        connector = SalesforceConnector(salesforce_config)
        objects = await connector.list_objects()

        assert len(objects) == 2
        assert objects[0]['name'] == 'Account'
        assert objects[0]['custom'] is False
        assert objects[1]['name'] == 'CustomObject__c'
        assert objects[1]['custom'] is True

    @patch('app.connectors.salesforce.requests.Session')
    async def test_pagination(self, mock_session_class, salesforce_config):
        """Test query pagination handling."""
        # Mock session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock describe response
        describe_response = Mock()
        describe_response.status_code = 200
        describe_response.json.return_value = {
            'fields': [
                {'name': 'Id', 'type': 'id'},
                {'name': 'Name', 'type': 'string'},
            ]
        }

        # Mock first query response (with pagination)
        first_response = Mock()
        first_response.status_code = 200
        first_response.json.return_value = {
            'totalSize': 3,
            'done': False,
            'nextRecordsUrl': '/services/data/v58.0/query/next-batch',
            'records': [
                {'attributes': {'type': 'Account'}, 'Id': '001', 'Name': 'First'},
            ]
        }

        # Mock second query response (final)
        second_response = Mock()
        second_response.status_code = 200
        second_response.json.return_value = {
            'totalSize': 3,
            'done': True,
            'records': [
                {'attributes': {'type': 'Account'}, 'Id': '002', 'Name': 'Second'},
                {'attributes': {'type': 'Account'}, 'Id': '003', 'Name': 'Third'},
            ]
        }

        # Configure mock to return different responses
        mock_session.get.side_effect = [describe_response, first_response, second_response]

        connector = SalesforceConnector(salesforce_config)
        df = await connector.get_data(table='Account')

        assert len(df) == 3
        assert list(df['Name']) == ['First', 'Second', 'Third']

    async def test_close(self, salesforce_config):
        """Test connection closing."""
        connector = SalesforceConnector(salesforce_config)
        connector._session = MagicMock()
        await connector.close()
        connector._session.close.assert_called_once()
        assert connector._session is None
