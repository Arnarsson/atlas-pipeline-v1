"""PostgreSQL connector with async support and incremental loading."""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

import asyncpg
import pandas as pd
from loguru import logger

from app.connectors.base import ConnectionConfig, SourceConnector


class PostgreSQLConnector(SourceConnector):
    """PostgreSQL data source connector with connection pooling."""

    def __init__(self, config: ConnectionConfig):
        """Initialize PostgreSQL connector.

        Args:
            config: Connection configuration
        """
        super().__init__(config)
        self._pool: Optional[asyncpg.Pool] = None
        self._max_retries = 3
        self._retry_delay = 1  # seconds

    async def _get_pool(self) -> asyncpg.Pool:
        """Get or create connection pool.

        Returns:
            Connection pool

        Raises:
            ConnectionError: If pool creation fails
        """
        if self._pool is None:
            try:
                # Build connection string
                if self.config.connection_string:
                    dsn = self.config.connection_string
                else:
                    dsn = (
                        f"postgresql://{self.config.username}:{self.config.password}"
                        f"@{self.config.host}:{self.config.port}/{self.config.database}"
                    )

                # Create pool
                self._pool = await asyncpg.create_pool(
                    dsn,
                    min_size=2,
                    max_size=10,
                    command_timeout=60,
                    **self.config.additional_params
                )
                logger.info(f"PostgreSQL pool created for {self.config.source_name}")

            except Exception as e:
                logger.error(f"Failed to create PostgreSQL pool: {e}")
                raise ConnectionError(f"PostgreSQL connection failed: {e}")

        return self._pool

    async def test_connection(self) -> bool:
        """Test PostgreSQL connection.

        Returns:
            True if connection successful

        Raises:
            ConnectionError: If connection test fails
        """
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            logger.info(f"PostgreSQL connection test successful: {self.config.source_name}")
            return True

        except Exception as e:
            logger.error(f"PostgreSQL connection test failed: {e}")
            raise ConnectionError(f"Connection test failed: {e}")

    async def get_data(
        self,
        query: Optional[str] = None,
        table: Optional[str] = None,
        incremental: bool = False,
        timestamp_column: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """Fetch data from PostgreSQL.

        Args:
            query: Custom SQL query
            table: Table name to fetch from
            incremental: Whether to fetch only new/updated records
            timestamp_column: Column to use for incremental loading
            filters: Additional filters as dict

        Returns:
            DataFrame with fetched data

        Raises:
            ValueError: If neither query nor table provided
            ConnectionError: If data fetch fails
        """
        if not query and not table:
            raise ValueError("Either 'query' or 'table' must be provided")

        # Build query
        if query:
            final_query = query
        else:
            final_query = f"SELECT * FROM {table}"

            # Add incremental filter
            if incremental and timestamp_column and self.last_sync_timestamp:
                final_query += f" WHERE {timestamp_column} > $1"

            # Add additional filters
            if filters:
                where_clause = " AND ".join([f"{k} = ${i+2}" for i, k in enumerate(filters.keys())])
                if "WHERE" in final_query:
                    final_query += f" AND {where_clause}"
                else:
                    final_query += f" WHERE {where_clause}"

        # Execute with retries
        for attempt in range(self._max_retries):
            try:
                pool = await self._get_pool()
                async with pool.acquire() as conn:
                    # Prepare query parameters
                    params = []
                    if incremental and timestamp_column and self.last_sync_timestamp:
                        params.append(self.last_sync_timestamp)
                    if filters:
                        params.extend(filters.values())

                    # Execute query
                    if params:
                        rows = await conn.fetch(final_query, *params)
                    else:
                        rows = await conn.fetch(final_query)

                    # Convert to DataFrame
                    if rows:
                        df = pd.DataFrame([dict(row) for row in rows])
                        logger.info(f"Fetched {len(df)} rows from PostgreSQL: {self.config.source_name}")

                        # Update last sync timestamp
                        if incremental and timestamp_column and timestamp_column in df.columns:
                            self.last_sync_timestamp = df[timestamp_column].max()

                        return df
                    else:
                        logger.info(f"No rows returned from PostgreSQL: {self.config.source_name}")
                        return pd.DataFrame()

            except Exception as e:
                logger.warning(f"PostgreSQL query attempt {attempt + 1} failed: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"PostgreSQL query failed after {self._max_retries} attempts")
                    raise ConnectionError(f"Data fetch failed: {e}")

    async def get_schema(self, table: str) -> Dict[str, str]:
        """Get PostgreSQL table schema.

        Args:
            table: Table name

        Returns:
            Dictionary mapping column names to data types

        Raises:
            ValueError: If table doesn't exist
        """
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                # Parse schema and table name
                if "." in table:
                    schema, table_name = table.split(".", 1)
                else:
                    schema = "public"
                    table_name = table

                # Query information_schema
                query = """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = $1 AND table_name = $2
                    ORDER BY ordinal_position
                """
                rows = await conn.fetch(query, schema, table_name)

                if not rows:
                    raise ValueError(f"Table '{table}' not found")

                schema_dict = {row["column_name"]: row["data_type"] for row in rows}
                logger.info(f"Retrieved schema for table {table}: {len(schema_dict)} columns")
                return schema_dict

        except Exception as e:
            logger.error(f"Failed to get schema for table {table}: {e}")
            raise

    async def get_row_count(
        self,
        table: str,
        where: Optional[str] = None
    ) -> int:
        """Get row count for PostgreSQL table.

        Args:
            table: Table name
            where: Optional WHERE clause

        Returns:
            Number of rows

        Raises:
            ValueError: If table doesn't exist
        """
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                query = f"SELECT COUNT(*) FROM {table}"
                if where:
                    query += f" WHERE {where}"

                count = await conn.fetchval(query)
                logger.info(f"Row count for {table}: {count}")
                return count

        except Exception as e:
            logger.error(f"Failed to get row count for {table}: {e}")
            raise ValueError(f"Table '{table}' not found or query failed: {e}")

    async def close(self) -> None:
        """Close PostgreSQL connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info(f"PostgreSQL pool closed for {self.config.source_name}")
            self._pool = None
