"""Google Sheets connector with service account and OAuth2 support."""

import json
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger

from app.connectors.base import ConnectionConfig, SourceConnector


class GoogleSheetsConnector(SourceConnector):
    """Google Sheets data source connector.

    Supports:
    - Service account authentication (recommended for automation)
    - Multiple sheets in a spreadsheet
    - Auto-detection of headers and data types
    - Incremental loading based on timestamp column
    """

    # Google Sheets API scopes
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    def __init__(self, config: ConnectionConfig):
        """Initialize Google Sheets connector.

        Args:
            config: Connection configuration with additional_params:
                - spreadsheet_id: Google Sheets spreadsheet ID (required)
                - service_account_json: Service account credentials JSON string (required)
                - sheet_name: Sheet name to read (optional, defaults to first sheet)
                - range: A1 notation range (optional, e.g., 'A1:Z1000')
                - value_render_option: How to render values ('FORMATTED_VALUE', 'UNFORMATTED_VALUE', 'FORMULA')
        """
        super().__init__(config)
        self._service = None
        self._spreadsheet_id = config.additional_params.get('spreadsheet_id')
        self._sheet_name = config.additional_params.get('sheet_name')
        self._range = config.additional_params.get('range')
        self._value_render_option = config.additional_params.get('value_render_option', 'FORMATTED_VALUE')

        if not self._spreadsheet_id:
            raise ValueError("spreadsheet_id is required in additional_params")

        # Parse service account credentials
        service_account_json = config.additional_params.get('service_account_json')
        if not service_account_json:
            raise ValueError("service_account_json is required in additional_params")

        try:
            if isinstance(service_account_json, str):
                self._credentials_info = json.loads(service_account_json)
            else:
                self._credentials_info = service_account_json
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid service account JSON: {e}")

    async def _get_service(self):
        """Get or create Google Sheets API service.

        Returns:
            Google Sheets API service instance

        Raises:
            ConnectionError: If service creation fails
        """
        if self._service is None:
            try:
                # Create credentials from service account info
                credentials = service_account.Credentials.from_service_account_info(
                    self._credentials_info,
                    scopes=self.SCOPES
                )

                # Build the service
                self._service = build('sheets', 'v4', credentials=credentials, cache_discovery=False)
                logger.info(f"Google Sheets service created for {self.config.source_name}")

            except Exception as e:
                logger.error(f"Failed to create Google Sheets service: {e}")
                raise ConnectionError(f"Google Sheets connection failed: {e}")

        return self._service

    async def test_connection(self) -> bool:
        """Test Google Sheets connection by fetching spreadsheet metadata.

        Returns:
            True if connection successful

        Raises:
            ConnectionError: If connection test fails
        """
        try:
            service = await self._get_service()

            # Try to get spreadsheet metadata
            spreadsheet = service.spreadsheets().get(
                spreadsheetId=self._spreadsheet_id
            ).execute()

            title = spreadsheet.get('properties', {}).get('title', 'Unknown')
            logger.info(f"Google Sheets connection test successful: {self.config.source_name} (Spreadsheet: {title})")
            return True

        except HttpError as e:
            error_msg = f"HTTP error {e.resp.status}: {e.error_details}"
            logger.error(f"Google Sheets connection test failed: {error_msg}")
            raise ConnectionError(error_msg)
        except Exception as e:
            logger.error(f"Google Sheets connection test failed: {e}")
            raise ConnectionError(str(e))

    async def get_data(
        self,
        query: Optional[str] = None,
        table: Optional[str] = None,
        incremental: bool = False,
        timestamp_column: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """Fetch data from Google Sheets.

        Args:
            query: Not used for Google Sheets (sheet_name comes from config)
            table: Sheet name (overrides config.additional_params.sheet_name)
            incremental: Whether to fetch only new/updated records (requires timestamp_column)
            timestamp_column: Column name to use for incremental loading
            filters: Not used for Google Sheets

        Returns:
            DataFrame with fetched data

        Raises:
            ValueError: If sheet name is not provided
            ConnectionError: If data fetch fails
        """
        try:
            service = await self._get_service()

            # Determine sheet name
            sheet_name = table or self._sheet_name

            # Get sheet metadata if no sheet name provided
            if not sheet_name:
                spreadsheet = service.spreadsheets().get(
                    spreadsheetId=self._spreadsheet_id
                ).execute()
                sheets = spreadsheet.get('sheets', [])
                if not sheets:
                    raise ValueError("No sheets found in spreadsheet")
                sheet_name = sheets[0].get('properties', {}).get('title', 'Sheet1')
                logger.info(f"Using first sheet: {sheet_name}")

            # Build range notation
            if self._range:
                range_notation = f"{sheet_name}!{self._range}"
            else:
                range_notation = sheet_name

            # Fetch data
            logger.info(f"Fetching data from {range_notation}")
            result = service.spreadsheets().values().get(
                spreadsheetId=self._spreadsheet_id,
                range=range_notation,
                valueRenderOption=self._value_render_option
            ).execute()

            values = result.get('values', [])
            if not values:
                logger.warning(f"No data found in {range_notation}")
                return pd.DataFrame()

            # Convert to DataFrame
            # First row is assumed to be headers
            if len(values) > 1:
                df = pd.DataFrame(values[1:], columns=values[0])
            else:
                df = pd.DataFrame(values)

            # Auto-detect and convert data types
            df = self._infer_dtypes(df)

            logger.info(f"Fetched {len(df)} rows from Google Sheets: {sheet_name}")

            # Handle incremental loading
            if incremental and timestamp_column:
                if timestamp_column not in df.columns:
                    logger.warning(f"Timestamp column '{timestamp_column}' not found, returning all data")
                elif self.last_sync_timestamp:
                    # Filter records after last sync
                    df[timestamp_column] = pd.to_datetime(df[timestamp_column], errors='coerce')
                    df = df[df[timestamp_column] > self.last_sync_timestamp]
                    logger.info(f"Incremental load: {len(df)} new records after {self.last_sync_timestamp}")

                # Update last sync timestamp
                self.last_sync_timestamp = datetime.now()

            return df

        except HttpError as e:
            error_msg = f"HTTP error {e.resp.status}: {e.error_details}"
            logger.error(f"Failed to fetch Google Sheets data: {error_msg}")
            raise ConnectionError(error_msg)
        except Exception as e:
            logger.error(f"Failed to fetch Google Sheets data: {e}")
            raise ConnectionError(str(e))

    def _infer_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Infer and convert DataFrame column types.

        Attempts to convert columns to appropriate types:
        - Numeric columns to int/float
        - Date/time strings to datetime
        - Booleans to bool
        - Everything else stays as string

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with inferred types
        """
        for col in df.columns:
            # Try numeric conversion
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except Exception:
                pass

            # Try datetime conversion if still object type
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_datetime(df[col], errors='ignore')
                except Exception:
                    pass

            # Try boolean conversion
            if df[col].dtype == 'object':
                unique_vals = df[col].dropna().unique()
                if len(unique_vals) <= 2 and all(str(v).lower() in ['true', 'false', 'yes', 'no', '1', '0'] for v in unique_vals):
                    df[col] = df[col].map(lambda x: str(x).lower() in ['true', 'yes', '1'])

        return df

    async def get_schema(self, table: str) -> Dict[str, str]:
        """Get sheet schema by reading first few rows and inferring types.

        Args:
            table: Sheet name

        Returns:
            Dictionary mapping column names to data types

        Raises:
            ValueError: If sheet doesn't exist or is empty
        """
        try:
            # Fetch a small sample to infer schema
            df = await self.get_data(table=table, incremental=False)

            if df.empty:
                raise ValueError(f"Sheet '{table}' is empty")

            # Build schema from DataFrame dtypes
            schema = {}
            for col, dtype in df.dtypes.items():
                if pd.api.types.is_integer_dtype(dtype):
                    schema[col] = 'integer'
                elif pd.api.types.is_float_dtype(dtype):
                    schema[col] = 'float'
                elif pd.api.types.is_bool_dtype(dtype):
                    schema[col] = 'boolean'
                elif pd.api.types.is_datetime64_any_dtype(dtype):
                    schema[col] = 'datetime'
                else:
                    schema[col] = 'string'

            return schema

        except Exception as e:
            logger.error(f"Failed to get Google Sheets schema: {e}")
            raise ValueError(f"Failed to get schema for sheet '{table}': {e}")

    async def get_row_count(
        self,
        table: str,
        where: Optional[str] = None
    ) -> int:
        """Get row count for a sheet.

        Args:
            table: Sheet name
            where: Not supported for Google Sheets

        Returns:
            Number of rows (excluding header)

        Raises:
            ValueError: If sheet doesn't exist
        """
        try:
            df = await self.get_data(table=table, incremental=False)
            return len(df)

        except Exception as e:
            logger.error(f"Failed to get Google Sheets row count: {e}")
            raise ValueError(f"Failed to get row count for sheet '{table}': {e}")

    async def close(self) -> None:
        """Close connection and cleanup resources."""
        # Google Sheets API doesn't require explicit connection closing
        # Just clear the service reference
        self._service = None
        logger.info(f"Google Sheets connector closed: {self.config.source_name}")

    async def list_sheets(self) -> list[Dict[str, Any]]:
        """List all sheets in the spreadsheet.

        Returns:
            List of sheet information dictionaries with 'title', 'sheetId', 'index', 'rowCount', 'columnCount'

        Raises:
            ConnectionError: If listing fails
        """
        try:
            service = await self._get_service()

            spreadsheet = service.spreadsheets().get(
                spreadsheetId=self._spreadsheet_id
            ).execute()

            sheets = []
            for sheet in spreadsheet.get('sheets', []):
                props = sheet.get('properties', {})
                grid_props = props.get('gridProperties', {})
                sheets.append({
                    'title': props.get('title', ''),
                    'sheetId': props.get('sheetId', 0),
                    'index': props.get('index', 0),
                    'rowCount': grid_props.get('rowCount', 0),
                    'columnCount': grid_props.get('columnCount', 0),
                })

            return sheets

        except Exception as e:
            logger.error(f"Failed to list Google Sheets: {e}")
            raise ConnectionError(f"Failed to list sheets: {e}")
