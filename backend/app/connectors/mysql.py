"""MySQL connector with async support and CDC capabilities."""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

import aiomysql
import pandas as pd
from loguru import logger

from app.connectors.base import ConnectionConfig, SourceConnector


class MySQLConnector(SourceConnector):
    """MySQL data source connector with connection pooling."""

    def __init__(self, config: ConnectionConfig):
        """Initialize MySQL connector.

        Args:
            config: Connection configuration
        """
        super().__init__(config)
        self._pool: Optional[aiomysql.Pool] = None
        self._max_retries = 3
        self._retry_delay = 1  # seconds

    async def _get_pool(self) -> aiomysql.Pool:
        """Get or create connection pool.

        Returns:
            Connection pool

        Raises:
            ConnectionError: If pool creation fails
        """
        if self._pool is None:
            try:
                # Create pool
                self._pool = await aiomysql.create_pool(
                    host=self.config.host,
                    port=self.config.port or 3306,
                    user=self.config.username,
                    password=self.config.password,
                    db=self.config.database,
                    minsize=2,
                    maxsize=10,
                    autocommit=True,
                    **self.config.additional_params
                )
                logger.info(f"MySQL pool created for {self.config.source_name}")

            except Exception as e:
                logger.error(f"Failed to create MySQL pool: {e}")
                raise ConnectionError(f"MySQL connection failed: {e}")

        return self._pool

    async def test_connection(self) -> bool:
        """Test MySQL connection.

        Returns:
            True if connection successful

        Raises:
            ConnectionError: If connection test fails
        """
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    await cursor.fetchone()
            logger.info(f"MySQL connection test successful: {self.config.source_name}")
            return True

        except Exception as e:
            logger.error(f"MySQL connection test failed: {e}")
            raise ConnectionError(f"Connection test failed: {e}")

    async def get_data(
        self,
        query: Optional[str] = None,
        table: Optional[str] = None,
        incremental: bool = False,
        timestamp_column: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """Fetch data from MySQL.

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
            params = []
        else:
            final_query = f"SELECT * FROM {table}"
            params = []

            # Add incremental filter
            if incremental and timestamp_column and self.last_sync_timestamp:
                final_query += f" WHERE {timestamp_column} > %s"
                params.append(self.last_sync_timestamp)

            # Add additional filters
            if filters:
                where_conditions = [f"{k} = %s" for k in filters.keys()]
                if "WHERE" in final_query:
                    final_query += " AND " + " AND ".join(where_conditions)
                else:
                    final_query += " WHERE " + " AND ".join(where_conditions)
                params.extend(filters.values())

        # Execute with retries
        for attempt in range(self._max_retries):
            try:
                pool = await self._get_pool()
                async with pool.acquire() as conn:
                    async with conn.cursor(aiomysql.DictCursor) as cursor:
                        await cursor.execute(final_query, params)
                        rows = await cursor.fetchall()

                        # Convert to DataFrame
                        if rows:
                            df = pd.DataFrame(rows)
                            logger.info(f"Fetched {len(df)} rows from MySQL: {self.config.source_name}")

                            # Update last sync timestamp
                            if incremental and timestamp_column and timestamp_column in df.columns:
                                self.last_sync_timestamp = df[timestamp_column].max()

                            return df
                        else:
                            logger.info(f"No rows returned from MySQL: {self.config.source_name}")
                            return pd.DataFrame()

            except Exception as e:
                logger.warning(f"MySQL query attempt {attempt + 1} failed: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"MySQL query failed after {self._max_retries} attempts")
                    raise ConnectionError(f"Data fetch failed: {e}")

    async def get_schema(self, table: str) -> Dict[str, str]:
        """Get MySQL table schema.

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
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Parse database and table name
                    if "." in table:
                        database, table_name = table.split(".", 1)
                    else:
                        database = self.config.database
                        table_name = table

                    # Query information_schema
                    query = """
                        SELECT COLUMN_NAME, DATA_TYPE
                        FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                        ORDER BY ORDINAL_POSITION
                    """
                    await cursor.execute(query, (database, table_name))
                    rows = await cursor.fetchall()

                    if not rows:
                        raise ValueError(f"Table '{table}' not found")

                    schema_dict = {row["COLUMN_NAME"]: row["DATA_TYPE"] for row in rows}
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
        """Get row count for MySQL table.

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
                async with conn.cursor() as cursor:
                    query = f"SELECT COUNT(*) FROM {table}"
                    if where:
                        query += f" WHERE {where}"

                    await cursor.execute(query)
                    result = await cursor.fetchone()
                    count = result[0] if result else 0
                    logger.info(f"Row count for {table}: {count}")
                    return count

        except Exception as e:
            logger.error(f"Failed to get row count for {table}: {e}")
            raise ValueError(f"Table '{table}' not found or query failed: {e}")

    async def close(self) -> None:
        """Close MySQL connection pool."""
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            logger.info(f"MySQL pool closed for {self.config.source_name}")
            self._pool = None
