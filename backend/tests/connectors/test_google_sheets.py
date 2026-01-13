"""Tests for Google Sheets connector."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from app.connectors.base import ConnectionConfig

# Skip all tests in this module if google library is not available
pytest.importorskip("google.oauth2.service_account", reason="Google API client not installed")

from app.connectors.google_sheets import GoogleSheetsConnector


@pytest.fixture
def mock_service_account_json():
    """Mock service account JSON credentials."""
    return json.dumps({
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "key123",
        "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    })


@pytest.fixture
def google_sheets_config(mock_service_account_json):
    """Google Sheets connector configuration."""
    return ConnectionConfig(
        source_type="google_sheets",
        source_name="test_sheets",
        additional_params={
            "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
            "service_account_json": mock_service_account_json,
            "sheet_name": "Sheet1",
        }
    )


@pytest.mark.asyncio
class TestGoogleSheetsConnector:
    """Test Google Sheets connector functionality."""

    async def test_init_success(self, google_sheets_config):
        """Test successful connector initialization."""
        connector = GoogleSheetsConnector(google_sheets_config)
        assert connector._spreadsheet_id == "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        assert connector._sheet_name == "Sheet1"

    async def test_init_missing_spreadsheet_id(self, mock_service_account_json):
        """Test initialization fails without spreadsheet_id."""
        config = ConnectionConfig(
            source_type="google_sheets",
            source_name="test",
            additional_params={
                "service_account_json": mock_service_account_json,
            }
        )
        with pytest.raises(ValueError, match="spreadsheet_id is required"):
            GoogleSheetsConnector(config)

    async def test_init_missing_credentials(self):
        """Test initialization fails without service account JSON."""
        config = ConnectionConfig(
            source_type="google_sheets",
            source_name="test",
            additional_params={
                "spreadsheet_id": "test123",
            }
        )
        with pytest.raises(ValueError, match="service_account_json is required"):
            GoogleSheetsConnector(config)

    @patch('app.connectors.google_sheets.build')
    @patch('app.connectors.google_sheets.service_account.Credentials.from_service_account_info')
    async def test_test_connection_success(self, mock_creds, mock_build, google_sheets_config):
        """Test successful connection test."""
        # Mock service and API calls
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.spreadsheets().get().execute.return_value = {
            'properties': {'title': 'Test Spreadsheet'}
        }

        connector = GoogleSheetsConnector(google_sheets_config)
        result = await connector.test_connection()

        assert result is True
        mock_build.assert_called_once()

    @patch('app.connectors.google_sheets.build')
    @patch('app.connectors.google_sheets.service_account.Credentials.from_service_account_info')
    async def test_get_data_success(self, mock_creds, mock_build, google_sheets_config):
        """Test successful data retrieval."""
        # Mock service and API response
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Mock sheet data
        mock_service.spreadsheets().values().get().execute.return_value = {
            'values': [
                ['Name', 'Age', 'Email'],
                ['Alice', '30', 'alice@example.com'],
                ['Bob', '25', 'bob@example.com'],
            ]
        }

        connector = GoogleSheetsConnector(google_sheets_config)
        df = await connector.get_data()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ['Name', 'Age', 'Email']
        assert df.iloc[0]['Name'] == 'Alice'

    @patch('app.connectors.google_sheets.build')
    @patch('app.connectors.google_sheets.service_account.Credentials.from_service_account_info')
    async def test_get_schema(self, mock_creds, mock_build, google_sheets_config):
        """Test schema inference."""
        # Mock service and API response
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_service.spreadsheets().values().get().execute.return_value = {
            'values': [
                ['Name', 'Age', 'Active'],
                ['Alice', '30', 'true'],
                ['Bob', '25', 'false'],
            ]
        }

        connector = GoogleSheetsConnector(google_sheets_config)
        schema = await connector.get_schema('Sheet1')

        assert isinstance(schema, dict)
        assert 'Name' in schema
        assert 'Age' in schema
        assert 'Active' in schema

    @patch('app.connectors.google_sheets.build')
    @patch('app.connectors.google_sheets.service_account.Credentials.from_service_account_info')
    async def test_list_sheets(self, mock_creds, mock_build, google_sheets_config):
        """Test listing all sheets in spreadsheet."""
        # Mock service and API response
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_service.spreadsheets().get().execute.return_value = {
            'sheets': [
                {
                    'properties': {
                        'title': 'Sheet1',
                        'sheetId': 0,
                        'index': 0,
                        'gridProperties': {
                            'rowCount': 100,
                            'columnCount': 26
                        }
                    }
                },
                {
                    'properties': {
                        'title': 'Sheet2',
                        'sheetId': 1,
                        'index': 1,
                        'gridProperties': {
                            'rowCount': 50,
                            'columnCount': 10
                        }
                    }
                }
            ]
        }

        connector = GoogleSheetsConnector(google_sheets_config)
        sheets = await connector.list_sheets()

        assert len(sheets) == 2
        assert sheets[0]['title'] == 'Sheet1'
        assert sheets[0]['rowCount'] == 100
        assert sheets[1]['title'] == 'Sheet2'

    async def test_close(self, google_sheets_config):
        """Test connection closing."""
        connector = GoogleSheetsConnector(google_sheets_config)
        await connector.close()
        assert connector._service is None
