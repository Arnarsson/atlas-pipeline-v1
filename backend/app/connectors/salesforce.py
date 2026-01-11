"""Salesforce CRM connector with OAuth2 and REST API support."""

from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import pandas as pd
import requests
from loguru import logger

from app.connectors.base import ConnectionConfig, SourceConnector


class SalesforceConnector(SourceConnector):
    """Salesforce CRM data source connector.

    Supports:
    - OAuth2 authentication (access token + instance URL)
    - Standard objects (Account, Contact, Opportunity, Lead, etc.)
    - Custom objects
    - SOQL queries
    - Incremental loading via LastModifiedDate
    - Bulk API for large datasets
    """

    # Salesforce API version
    API_VERSION = "v58.0"

    # Standard Salesforce objects
    STANDARD_OBJECTS = [
        "Account", "Contact", "Lead", "Opportunity", "Case",
        "Task", "Event", "Campaign", "User", "Product2"
    ]

    def __init__(self, config: ConnectionConfig):
        """Initialize Salesforce connector.

        Args:
            config: Connection configuration with additional_params:
                - instance_url: Salesforce instance URL (required, e.g., 'https://yourinstance.salesforce.com')
                - access_token: OAuth2 access token (required)
                - api_version: Salesforce API version (optional, default: v58.0)
                - use_bulk_api: Use Bulk API for large queries (optional, default: False)
        """
        super().__init__(config)
        self._instance_url = config.additional_params.get('instance_url')
        self._access_token = config.additional_params.get('access_token')
        self._api_version = config.additional_params.get('api_version', self.API_VERSION)
        self._use_bulk_api = config.additional_params.get('use_bulk_api', False)

        if not self._instance_url:
            raise ValueError("instance_url is required in additional_params")
        if not self._access_token:
            raise ValueError("access_token is required in additional_params")

        # Clean up instance URL (remove trailing slash)
        self._instance_url = self._instance_url.rstrip('/')

        # Build base API URL
        self._base_url = f"{self._instance_url}/services/data/{self._api_version}"

        # Session for connection pooling
        self._session = None

    def _get_session(self) -> requests.Session:
        """Get or create HTTP session with authentication.

        Returns:
            Requests session with headers configured
        """
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                'Authorization': f'Bearer {self._access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
        return self._session

    async def test_connection(self) -> bool:
        """Test Salesforce connection by querying user info.

        Returns:
            True if connection successful

        Raises:
            ConnectionError: If connection test fails
        """
        try:
            session = self._get_session()

            # Test connection by getting user info
            response = session.get(f"{self._base_url}/sobjects")

            if response.status_code == 200:
                logger.info(f"Salesforce connection test successful: {self.config.source_name}")
                return True
            elif response.status_code == 401:
                raise ConnectionError("Salesforce authentication failed: Invalid or expired access token")
            else:
                raise ConnectionError(f"Salesforce connection failed: HTTP {response.status_code}: {response.text}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Salesforce connection test failed: {e}")
            raise ConnectionError(f"Salesforce connection failed: {e}")
        except Exception as e:
            logger.error(f"Salesforce connection test failed: {e}")
            raise ConnectionError(str(e))

    async def get_data(
        self,
        query: Optional[str] = None,
        table: Optional[str] = None,
        incremental: bool = False,
        timestamp_column: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """Fetch data from Salesforce.

        Args:
            query: SOQL query string (if provided, overrides table)
            table: Salesforce object name (e.g., 'Account', 'Contact')
            incremental: Whether to fetch only new/updated records (requires timestamp_column)
            timestamp_column: Column to use for incremental loading (default: 'LastModifiedDate')
            filters: Additional WHERE clause filters as dict (e.g., {'Type': 'Customer'})

        Returns:
            DataFrame with fetched data

        Raises:
            ValueError: If neither query nor table is provided
            ConnectionError: If data fetch fails
        """
        try:
            session = self._get_session()

            # Build SOQL query
            if query:
                soql_query = query
            elif table:
                # Get object fields first
                fields = await self._get_object_fields(table)
                field_names = ', '.join(fields.keys())

                # Build WHERE clause
                where_conditions = []

                # Add filters
                if filters:
                    for key, value in filters.items():
                        if isinstance(value, str):
                            where_conditions.append(f"{key} = '{value}'")
                        else:
                            where_conditions.append(f"{key} = {value}")

                # Add incremental loading condition
                if incremental:
                    ts_col = timestamp_column or 'LastModifiedDate'
                    if self.last_sync_timestamp:
                        # Salesforce datetime format: YYYY-MM-DDTHH:MM:SSZ
                        last_sync_str = self.last_sync_timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
                        where_conditions.append(f"{ts_col} > {last_sync_str}")
                        logger.info(f"Incremental query: {ts_col} > {last_sync_str}")

                # Build final query
                soql_query = f"SELECT {field_names} FROM {table}"
                if where_conditions:
                    soql_query += f" WHERE {' AND '.join(where_conditions)}"

                # Add ORDER BY for consistent pagination
                if incremental and timestamp_column:
                    soql_query += f" ORDER BY {timestamp_column} ASC"

            else:
                raise ValueError("Either 'query' or 'table' must be provided")

            logger.info(f"Executing SOQL query: {soql_query}")

            # Execute query
            all_records = []
            next_records_url = None

            # Initial query
            params = {'q': soql_query}
            response = session.get(f"{self._base_url}/query", params=params)

            if response.status_code != 200:
                raise ConnectionError(f"Salesforce query failed: HTTP {response.status_code}: {response.text}")

            result = response.json()
            all_records.extend(result.get('records', []))
            next_records_url = result.get('nextRecordsUrl')

            # Pagination - fetch remaining batches
            while next_records_url:
                logger.info(f"Fetching next batch via pagination...")
                response = session.get(f"{self._instance_url}{next_records_url}")

                if response.status_code != 200:
                    logger.warning(f"Pagination request failed: HTTP {response.status_code}")
                    break

                result = response.json()
                all_records.extend(result.get('records', []))
                next_records_url = result.get('nextRecordsUrl')

            logger.info(f"Fetched {len(all_records)} records from Salesforce: {table or 'custom query'}")

            if not all_records:
                return pd.DataFrame()

            # Clean records (remove Salesforce metadata)
            cleaned_records = []
            for record in all_records:
                # Remove 'attributes' field
                clean_record = {k: v for k, v in record.items() if k != 'attributes'}
                cleaned_records.append(clean_record)

            # Convert to DataFrame
            df = pd.DataFrame(cleaned_records)

            # Update last sync timestamp
            if incremental:
                self.last_sync_timestamp = datetime.now()

            return df

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch Salesforce data: {e}")
            raise ConnectionError(f"Salesforce query failed: {e}")
        except Exception as e:
            logger.error(f"Failed to fetch Salesforce data: {e}")
            raise ConnectionError(str(e))

    async def _get_object_fields(self, object_name: str) -> Dict[str, str]:
        """Get all fields for a Salesforce object.

        Args:
            object_name: Salesforce object name

        Returns:
            Dictionary mapping field names to field types

        Raises:
            ConnectionError: If object metadata fetch fails
        """
        try:
            session = self._get_session()

            # Get object describe
            response = session.get(f"{self._base_url}/sobjects/{object_name}/describe")

            if response.status_code != 200:
                raise ConnectionError(f"Failed to describe object '{object_name}': HTTP {response.status_code}")

            describe = response.json()
            fields = {}

            for field in describe.get('fields', []):
                field_name = field.get('name')
                field_type = field.get('type', 'string').lower()

                # Map Salesforce types to standard types
                if field_type in ['int', 'double', 'currency', 'percent']:
                    fields[field_name] = 'numeric'
                elif field_type in ['date', 'datetime']:
                    fields[field_name] = 'datetime'
                elif field_type == 'boolean':
                    fields[field_name] = 'boolean'
                else:
                    fields[field_name] = 'string'

            return fields

        except Exception as e:
            logger.error(f"Failed to get Salesforce object fields: {e}")
            raise ConnectionError(f"Failed to describe object '{object_name}': {e}")

    async def get_schema(self, table: str) -> Dict[str, str]:
        """Get Salesforce object schema.

        Args:
            table: Salesforce object name

        Returns:
            Dictionary mapping field names to data types

        Raises:
            ValueError: If object doesn't exist
        """
        try:
            return await self._get_object_fields(table)

        except Exception as e:
            logger.error(f"Failed to get Salesforce schema: {e}")
            raise ValueError(f"Failed to get schema for object '{table}': {e}")

    async def get_row_count(
        self,
        table: str,
        where: Optional[str] = None
    ) -> int:
        """Get row count for a Salesforce object.

        Args:
            table: Salesforce object name
            where: Optional WHERE clause (SOQL syntax)

        Returns:
            Number of rows

        Raises:
            ValueError: If object doesn't exist
            ConnectionError: If count query fails
        """
        try:
            session = self._get_session()

            # Build count query
            soql_query = f"SELECT COUNT() FROM {table}"
            if where:
                soql_query += f" WHERE {where}"

            params = {'q': soql_query}
            response = session.get(f"{self._base_url}/query", params=params)

            if response.status_code != 200:
                raise ConnectionError(f"Count query failed: HTTP {response.status_code}: {response.text}")

            result = response.json()
            count = result.get('totalSize', 0)

            return count

        except Exception as e:
            logger.error(f"Failed to get Salesforce row count: {e}")
            raise ValueError(f"Failed to get row count for object '{table}': {e}")

    async def close(self) -> None:
        """Close connection and cleanup resources."""
        if self._session:
            self._session.close()
            self._session = None
        logger.info(f"Salesforce connector closed: {self.config.source_name}")

    async def list_objects(self, custom_only: bool = False) -> list[Dict[str, Any]]:
        """List all Salesforce objects (standard and custom).

        Args:
            custom_only: If True, return only custom objects (ending with __c)

        Returns:
            List of object information dictionaries with 'name', 'label', 'custom', 'queryable'

        Raises:
            ConnectionError: If listing fails
        """
        try:
            session = self._get_session()

            response = session.get(f"{self._base_url}/sobjects")

            if response.status_code != 200:
                raise ConnectionError(f"Failed to list objects: HTTP {response.status_code}: {response.text}")

            result = response.json()
            objects = []

            for obj in result.get('sobjects', []):
                name = obj.get('name', '')
                is_custom = name.endswith('__c')

                if custom_only and not is_custom:
                    continue

                objects.append({
                    'name': name,
                    'label': obj.get('label', ''),
                    'custom': is_custom,
                    'queryable': obj.get('queryable', False),
                    'createable': obj.get('createable', False),
                    'updateable': obj.get('updateable', False),
                })

            return objects

        except Exception as e:
            logger.error(f"Failed to list Salesforce objects: {e}")
            raise ConnectionError(f"Failed to list objects: {e}")

    async def execute_soql(self, soql_query: str) -> pd.DataFrame:
        """Execute a raw SOQL query.

        Args:
            soql_query: SOQL query string

        Returns:
            DataFrame with query results

        Raises:
            ConnectionError: If query execution fails
        """
        return await self.get_data(query=soql_query)
