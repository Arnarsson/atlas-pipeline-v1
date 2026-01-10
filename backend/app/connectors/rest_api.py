"""REST API connector with authentication and pagination support."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
import pandas as pd
from loguru import logger

from app.connectors.base import ConnectionConfig, SourceConnector


class RESTAPIConnector(SourceConnector):
    """REST API data source connector with authentication and pagination."""

    def __init__(self, config: ConnectionConfig):
        """Initialize REST API connector.

        Args:
            config: Connection configuration
        """
        super().__init__(config)
        self._client: Optional[httpx.AsyncClient] = None
        self._max_retries = 3
        self._retry_delay = 1  # seconds
        self._rate_limit_delay = 1  # seconds between requests

    def _get_auth_headers(self) -> Dict[str, str]:
        """Build authentication headers.

        Returns:
            Dictionary of headers
        """
        headers = {"Content-Type": "application/json"}

        if self.config.auth_type == "bearer":
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        elif self.config.auth_type == "apikey":
            # API key can be in header or query param
            if "header_name" in self.config.additional_params:
                header_name = self.config.additional_params["header_name"]
                headers[header_name] = self.config.api_key
            else:
                headers["X-API-Key"] = self.config.api_key
        elif self.config.auth_type == "basic":
            # httpx will handle basic auth if we pass auth param
            pass

        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client.

        Returns:
            HTTP client
        """
        if self._client is None:
            auth = None
            if self.config.auth_type == "basic":
                auth = httpx.BasicAuth(
                    self.config.username,
                    self.config.password
                )

            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                auth=auth,
                timeout=30.0,
                follow_redirects=True,
            )
            logger.info(f"HTTP client created for {self.config.source_name}")

        return self._client

    async def test_connection(self) -> bool:
        """Test REST API connection.

        Returns:
            True if connection successful

        Raises:
            ConnectionError: If connection test fails
        """
        try:
            client = await self._get_client()
            headers = self._get_auth_headers()

            # Try to fetch from health endpoint or root
            health_endpoint = self.config.additional_params.get("health_endpoint", "/")
            response = await client.get(health_endpoint, headers=headers)
            response.raise_for_status()

            logger.info(f"REST API connection test successful: {self.config.source_name}")
            return True

        except Exception as e:
            logger.error(f"REST API connection test failed: {e}")
            raise ConnectionError(f"Connection test failed: {e}")

    async def get_data(
        self,
        query: Optional[str] = None,
        table: Optional[str] = None,
        incremental: bool = False,
        timestamp_column: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """Fetch data from REST API.

        Args:
            query: API endpoint path (relative to base_url)
            table: Alternative to query (used as endpoint)
            incremental: Whether to fetch only new/updated records
            timestamp_column: Column to use for incremental loading
            filters: Additional query parameters

        Returns:
            DataFrame with fetched data

        Raises:
            ValueError: If neither query nor table provided
            ConnectionError: If data fetch fails
        """
        endpoint = query or table
        if not endpoint:
            raise ValueError("Either 'query' or 'table' must be provided")

        # Build query parameters
        params = filters.copy() if filters else {}

        # Add incremental filter
        if incremental and timestamp_column and self.last_sync_timestamp:
            params[timestamp_column] = self.last_sync_timestamp.isoformat()

        # Determine pagination strategy
        pagination_type = self.config.additional_params.get("pagination_type", "offset")

        all_data: List[Dict[str, Any]] = []

        if pagination_type == "none":
            # Single request, no pagination
            data = await self._fetch_page(endpoint, params)
            all_data.extend(data)

        elif pagination_type == "offset":
            # Offset/limit pagination
            all_data = await self._fetch_with_offset_pagination(endpoint, params)

        elif pagination_type == "cursor":
            # Cursor-based pagination
            all_data = await self._fetch_with_cursor_pagination(endpoint, params)

        elif pagination_type == "page":
            # Page-based pagination
            all_data = await self._fetch_with_page_pagination(endpoint, params)

        # Convert to DataFrame
        if all_data:
            df = pd.DataFrame(all_data)
            logger.info(f"Fetched {len(df)} rows from REST API: {self.config.source_name}")

            # Update last sync timestamp
            if incremental and timestamp_column and timestamp_column in df.columns:
                self.last_sync_timestamp = pd.to_datetime(df[timestamp_column]).max()

            return df
        else:
            logger.info(f"No data returned from REST API: {self.config.source_name}")
            return pd.DataFrame()

    async def _fetch_page(
        self,
        endpoint: str,
        params: Dict[str, Any],
        retry_count: int = 0
    ) -> List[Dict[str, Any]]:
        """Fetch a single page of data.

        Args:
            endpoint: API endpoint
            params: Query parameters
            retry_count: Current retry attempt

        Returns:
            List of records

        Raises:
            ConnectionError: If fetch fails after retries
        """
        try:
            client = await self._get_client()
            headers = self._get_auth_headers()

            # Make request
            response = await client.get(endpoint, params=params, headers=headers)

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", self._rate_limit_delay))
                logger.warning(f"Rate limited, waiting {retry_after}s")
                await asyncio.sleep(retry_after)
                return await self._fetch_page(endpoint, params, retry_count)

            response.raise_for_status()

            # Parse response
            data = response.json()

            # Extract data from response
            data_key = self.config.additional_params.get("data_key", None)
            if data_key and isinstance(data, dict):
                data = data.get(data_key, [])

            # Ensure data is a list
            if not isinstance(data, list):
                data = [data]

            # Rate limiting between requests
            await asyncio.sleep(self._rate_limit_delay)

            return data

        except httpx.HTTPStatusError as e:
            if retry_count < self._max_retries:
                wait_time = self._retry_delay * (2 ** retry_count)  # Exponential backoff
                logger.warning(f"HTTP error {e.response.status_code}, retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
                return await self._fetch_page(endpoint, params, retry_count + 1)
            else:
                logger.error(f"HTTP request failed after {self._max_retries} retries")
                raise ConnectionError(f"Data fetch failed: {e}")

        except Exception as e:
            logger.error(f"Failed to fetch data from API: {e}")
            raise ConnectionError(f"Data fetch failed: {e}")

    async def _fetch_with_offset_pagination(
        self,
        endpoint: str,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fetch data with offset/limit pagination.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            All records from all pages
        """
        all_data: List[Dict[str, Any]] = []
        offset = 0
        limit = self.config.additional_params.get("page_size", 100)

        while True:
            page_params = params.copy()
            page_params["offset"] = offset
            page_params["limit"] = limit

            data = await self._fetch_page(endpoint, page_params)

            if not data:
                break

            all_data.extend(data)
            offset += limit

            # Check if we got fewer records than limit (last page)
            if len(data) < limit:
                break

        return all_data

    async def _fetch_with_cursor_pagination(
        self,
        endpoint: str,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fetch data with cursor-based pagination.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            All records from all pages
        """
        all_data: List[Dict[str, Any]] = []
        cursor = None
        cursor_key = self.config.additional_params.get("cursor_key", "cursor")

        while True:
            page_params = params.copy()
            if cursor:
                page_params[cursor_key] = cursor

            response_data = await self._fetch_page(endpoint, page_params)

            if not response_data:
                break

            # Extract data and next cursor
            if isinstance(response_data, dict):
                data = response_data.get("data", [])
                cursor = response_data.get("next_cursor")
            else:
                data = response_data
                cursor = None

            all_data.extend(data)

            if not cursor:
                break

        return all_data

    async def _fetch_with_page_pagination(
        self,
        endpoint: str,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fetch data with page-based pagination.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            All records from all pages
        """
        all_data: List[Dict[str, Any]] = []
        page = 1
        page_size = self.config.additional_params.get("page_size", 100)

        while True:
            page_params = params.copy()
            page_params["page"] = page
            page_params["page_size"] = page_size

            data = await self._fetch_page(endpoint, page_params)

            if not data:
                break

            all_data.extend(data)
            page += 1

            # Check if we got fewer records than page_size (last page)
            if len(data) < page_size:
                break

        return all_data

    async def get_schema(self, table: str) -> Dict[str, str]:
        """Get API schema (not typically available for REST APIs).

        Args:
            table: Endpoint name

        Returns:
            Dictionary mapping field names to inferred types

        Raises:
            NotImplementedError: Schema inspection not available for REST APIs
        """
        # For REST APIs, we can try to infer schema from a sample response
        try:
            data = await self.get_data(query=table)
            if not data.empty:
                schema = {col: str(data[col].dtype) for col in data.columns}
                logger.info(f"Inferred schema from sample data: {len(schema)} fields")
                return schema
            else:
                return {}

        except Exception as e:
            logger.warning(f"Could not infer schema: {e}")
            raise NotImplementedError("Schema inspection not available for REST APIs")

    async def get_row_count(
        self,
        table: str,
        where: Optional[str] = None
    ) -> int:
        """Get row count (requires fetching all data for REST APIs).

        Args:
            table: Endpoint name
            where: Not supported for REST APIs

        Returns:
            Number of rows

        Note:
            This will fetch all data to count rows
        """
        try:
            data = await self.get_data(query=table)
            count = len(data)
            logger.info(f"Row count for {table}: {count}")
            return count

        except Exception as e:
            logger.error(f"Failed to get row count: {e}")
            raise ValueError(f"Could not count rows: {e}")

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            logger.info(f"HTTP client closed for {self.config.source_name}")
            self._client = None
