"""
Airbyte Database Writer

Writes data from Airbyte syncs to Atlas medallion architecture layers.
Integrates with Explore/Chart/Navigate database schema.

Author: Atlas Pipeline Team
Date: January 12, 2026
"""

import asyncpg
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


class AirbyteDatabaseWriter:
    """Writes data from Airbyte syncs to Atlas database layers."""

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize database writer.

        Args:
            db_pool: AsyncPG connection pool
        """
        self.db_pool = db_pool
        logger.info("Initialized AirbyteDatabaseWriter")

    async def write_to_explore(
        self,
        source_id: str,
        stream_name: str,
        records: List[Dict[str, Any]],
        run_id: str
    ) -> int:
        """
        Write raw data to explore layer.

        Args:
            source_id: Airbyte source identifier (e.g., "source-postgres")
            stream_name: Stream name (e.g., "users", "orders")
            records: List of record dictionaries
            run_id: Pipeline run identifier (UUID)

        Returns:
            Number of records written

        Example:
            >>> records = [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
            >>> count = await writer.write_to_explore("postgres-source", "users", records, run_id)
            >>> print(f"Wrote {count} records")
        """
        if not records:
            logger.warning(f"No records to write for {source_id}/{stream_name}")
            return 0

        # Sanitize table name (remove hyphens, lowercase)
        table_name = self._sanitize_table_name(f"{source_id}_{stream_name}_raw")

        logger.info(f"Writing {len(records)} records to explore.{table_name}")

        # Create table if not exists
        await self._ensure_explore_table(table_name)

        # Write to database
        async with self.db_pool.acquire() as conn:
            # Prepare insert query
            insert_query = f"""
                INSERT INTO explore.{table_name}
                (run_id, source_system, raw_data, ingested_at)
                VALUES ($1, $2, $3, $4)
            """

            records_inserted = 0
            for record in records:
                try:
                    await conn.execute(
                        insert_query,
                        UUID(run_id) if isinstance(run_id, str) else run_id,
                        source_id,
                        json.dumps(record),
                        datetime.utcnow()
                    )
                    records_inserted += 1
                except Exception as e:
                    logger.error(f"Failed to insert record: {e}")
                    continue

        logger.info(f"✅ Wrote {records_inserted} records to explore.{table_name}")
        return records_inserted

    async def _ensure_explore_table(self, table_name: str):
        """
        Create explore table if doesn't exist.

        Args:
            table_name: Table name (without schema prefix)
        """
        async with self.db_pool.acquire() as conn:
            try:
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS explore.{table_name} (
                        id BIGSERIAL PRIMARY KEY,
                        run_id UUID NOT NULL,
                        source_system VARCHAR(255) NOT NULL,
                        raw_data JSONB NOT NULL,
                        ingested_at TIMESTAMP DEFAULT NOW(),
                        partition_date DATE GENERATED ALWAYS AS (DATE(ingested_at)) STORED,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)

                # Create index on run_id for fast lookups
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_run_id
                    ON explore.{table_name}(run_id)
                """)

                # Create index on partition_date for partition management
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_partition
                    ON explore.{table_name}(partition_date)
                """)

                logger.debug(f"Ensured explore.{table_name} exists")
            except Exception as e:
                logger.error(f"Failed to create explore table: {e}")
                raise

    async def write_to_chart(
        self,
        source_id: str,
        stream_name: str,
        df: pd.DataFrame,
        run_id: str,
        pii_results: Dict[str, Any],
        quality_results: Dict[str, Any]
    ) -> int:
        """
        Write validated data to chart layer.

        Args:
            source_id: Source identifier
            stream_name: Stream name
            df: Validated DataFrame with typed columns
            run_id: Pipeline run ID
            pii_results: PII detection results
            quality_results: Quality check results

        Returns:
            Number of records written

        Example:
            >>> df = pd.DataFrame({"id": [1, 2], "name": ["John", "Jane"]})
            >>> pii_results = {"total_detections": 0}
            >>> quality_results = {"overall_score": 95}
            >>> count = await writer.write_to_chart("postgres", "users", df, run_id, pii_results, quality_results)
        """
        if df.empty:
            logger.warning(f"Empty DataFrame for {source_id}/{stream_name}")
            return 0

        table_name = self._sanitize_table_name(f"{source_id}_{stream_name}_validated")

        logger.info(f"Writing {len(df)} records to chart.{table_name}")

        # Ensure table exists with inferred schema
        await self._ensure_chart_table(table_name, df)

        # Write DataFrame to chart layer
        async with self.db_pool.acquire() as conn:
            # Build insert query dynamically based on DataFrame columns
            columns = list(df.columns)
            placeholders = ', '.join([f'${i+1}' for i in range(len(columns) + 4)])
            column_names = ', '.join(columns) + ', run_id, validated_at, pii_checked, quality_score'

            insert_query = f"""
                INSERT INTO chart.{table_name}
                ({column_names})
                VALUES ({placeholders})
            """

            records_written = 0
            for _, row in df.iterrows():
                try:
                    values = [self._convert_value(row[col]) for col in columns]
                    values.extend([
                        UUID(run_id) if isinstance(run_id, str) else run_id,
                        datetime.utcnow(),
                        True,  # pii_checked
                        float(quality_results.get('overall_score', 0))
                    ])
                    await conn.execute(insert_query, *values)
                    records_written += 1
                except Exception as e:
                    logger.error(f"Failed to insert chart record: {e}")
                    continue

        logger.info(f"✅ Wrote {records_written} records to chart.{table_name}")
        return records_written

    async def _ensure_chart_table(self, table_name: str, df: pd.DataFrame):
        """
        Create chart table with inferred schema from DataFrame.

        Args:
            table_name: Table name (without schema prefix)
            df: Sample DataFrame for schema inference
        """
        async with self.db_pool.acquire() as conn:
            try:
                # Infer column types from DataFrame
                column_defs = []
                for col in df.columns:
                    dtype = df[col].dtype
                    sql_type = self._infer_sql_type(dtype)
                    # Use text to avoid issues with complex types
                    column_defs.append(f'"{col}" {sql_type}')

                # Add metadata columns
                metadata_columns = [
                    "run_id UUID NOT NULL",
                    "validated_at TIMESTAMP DEFAULT NOW()",
                    "pii_checked BOOLEAN DEFAULT FALSE",
                    "quality_score NUMERIC(5,2)",
                    "created_at TIMESTAMP DEFAULT NOW()"
                ]

                all_columns = column_defs + metadata_columns

                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS chart.{table_name} (
                        id BIGSERIAL PRIMARY KEY,
                        {', '.join(all_columns)}
                    )
                """)

                # Create index on run_id
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_run_id
                    ON chart.{table_name}(run_id)
                """)

                # Create index on quality_score for filtering
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_quality
                    ON chart.{table_name}(quality_score)
                    WHERE quality_score < 80
                """)

                logger.debug(f"Ensured chart.{table_name} exists")
            except Exception as e:
                logger.error(f"Failed to create chart table: {e}")
                raise

    async def write_to_navigate(
        self,
        source_id: str,
        stream_name: str,
        df: pd.DataFrame,
        run_id: str,
        natural_key_column: Optional[str] = None
    ) -> int:
        """
        Write business-ready data to navigate layer with SCD Type 2.

        Args:
            source_id: Source identifier
            stream_name: Stream name
            df: Business-ready DataFrame
            run_id: Pipeline run ID
            natural_key_column: Column to use as natural key (default: first column)

        Returns:
            Number of records written/updated

        Example:
            >>> df = pd.DataFrame({"user_id": [1, 2], "name": ["John Updated", "Jane"]})
            >>> count = await writer.write_to_navigate("postgres", "users", df, run_id, "user_id")
        """
        if df.empty:
            logger.warning(f"Empty DataFrame for {source_id}/{stream_name}")
            return 0

        table_name = self._sanitize_table_name(f"{source_id}_{stream_name}_business")

        # Use first column as natural key if not specified
        if natural_key_column is None:
            natural_key_column = df.columns[0]

        if natural_key_column not in df.columns:
            logger.error(f"Natural key column '{natural_key_column}' not found in DataFrame")
            return 0

        logger.info(f"Writing {len(df)} records to navigate.{table_name} (SCD Type 2)")

        # Ensure SCD Type 2 table exists
        await self._ensure_navigate_table(table_name, df)

        # Implement SCD Type 2 logic
        async with self.db_pool.acquire() as conn:
            records_processed = 0

            for _, row in df.iterrows():
                try:
                    natural_key = str(row[natural_key_column])

                    # Check if current record exists
                    existing = await conn.fetchrow(f"""
                        SELECT *
                        FROM navigate.{table_name}
                        WHERE natural_key = $1 AND is_current = TRUE
                    """, natural_key)

                    # Convert row to dict for comparison
                    row_dict = {col: self._convert_value(row[col]) for col in df.columns}
                    row_json = json.dumps(row_dict, sort_keys=True)

                    if existing:
                        # Check if data changed
                        existing_dict = {col: existing[col] for col in df.columns if col in existing}
                        existing_json = json.dumps(existing_dict, sort_keys=True)

                        if row_json != existing_json:
                            # Data changed - close old record
                            await conn.execute(f"""
                                UPDATE navigate.{table_name}
                                SET valid_to = NOW(), is_current = FALSE
                                WHERE natural_key = $1 AND is_current = TRUE
                            """, natural_key)

                            # Insert new record
                            await self._insert_navigate_record(
                                conn, table_name, df.columns, row_dict, natural_key, run_id
                            )
                            records_processed += 1
                        else:
                            # Data unchanged - just update run_id
                            await conn.execute(f"""
                                UPDATE navigate.{table_name}
                                SET run_id = $1
                                WHERE natural_key = $2 AND is_current = TRUE
                            """, UUID(run_id) if isinstance(run_id, str) else run_id, natural_key)
                            records_processed += 1
                    else:
                        # New record
                        await self._insert_navigate_record(
                            conn, table_name, df.columns, row_dict, natural_key, run_id
                        )
                        records_processed += 1

                except Exception as e:
                    logger.error(f"Failed to process navigate record: {e}")
                    continue

        logger.info(f"✅ Processed {records_processed} records in navigate.{table_name}")
        return records_processed

    async def _insert_navigate_record(
        self,
        conn: asyncpg.Connection,
        table_name: str,
        columns: List[str],
        row_dict: Dict[str, Any],
        natural_key: str,
        run_id: str
    ):
        """Insert a new record into navigate table."""
        values = [row_dict[col] for col in columns]
        values.extend([
            natural_key,
            datetime.utcnow(),  # valid_from
            UUID(run_id) if isinstance(run_id, str) else run_id
        ])

        placeholders = ', '.join([f'${i+1}' for i in range(len(values))])
        column_names = ', '.join([f'"{col}"' for col in columns]) + ', natural_key, valid_from, run_id'

        await conn.execute(f"""
            INSERT INTO navigate.{table_name}
            ({column_names})
            VALUES ({placeholders})
        """, *values)

    async def _ensure_navigate_table(self, table_name: str, df: pd.DataFrame):
        """
        Create navigate table with SCD Type 2 structure.

        Args:
            table_name: Table name (without schema prefix)
            df: Sample DataFrame for schema inference
        """
        async with self.db_pool.acquire() as conn:
            try:
                column_defs = []
                for col in df.columns:
                    dtype = df[col].dtype
                    sql_type = self._infer_sql_type(dtype)
                    column_defs.append(f'"{col}" {sql_type}')

                # Add SCD Type 2 columns
                scd_columns = [
                    "surrogate_key BIGSERIAL PRIMARY KEY",
                    "natural_key VARCHAR(255) NOT NULL",
                    "valid_from TIMESTAMP DEFAULT NOW()",
                    "valid_to TIMESTAMP DEFAULT '9999-12-31'",
                    "is_current BOOLEAN DEFAULT TRUE",
                    "run_id UUID NOT NULL",
                    "created_at TIMESTAMP DEFAULT NOW()"
                ]

                all_columns = column_defs + scd_columns

                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS navigate.{table_name} (
                        {', '.join(all_columns)}
                    )
                """)

                # Create unique index on natural_key where is_current = true
                await conn.execute(f"""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_{table_name}_current
                    ON navigate.{table_name}(natural_key)
                    WHERE is_current = TRUE
                """)

                # Create index on valid_from/valid_to for time-travel queries
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_validity
                    ON navigate.{table_name}(valid_from, valid_to)
                """)

                logger.debug(f"Ensured navigate.{table_name} exists")
            except Exception as e:
                logger.error(f"Failed to create navigate table: {e}")
                raise

    def _infer_sql_type(self, dtype) -> str:
        """
        Infer SQL type from pandas dtype.

        Args:
            dtype: pandas dtype

        Returns:
            PostgreSQL type string
        """
        dtype_str = str(dtype)

        if dtype_str.startswith('int'):
            return 'BIGINT'
        elif dtype_str.startswith('float'):
            return 'DOUBLE PRECISION'
        elif dtype_str == 'bool':
            return 'BOOLEAN'
        elif dtype_str.startswith('datetime'):
            return 'TIMESTAMP'
        elif dtype_str.startswith('date'):
            return 'DATE'
        else:
            return 'TEXT'

    def _convert_value(self, value: Any) -> Any:
        """
        Convert pandas value to Python type for PostgreSQL.

        Args:
            value: pandas value

        Returns:
            Python native type
        """
        # Handle NaN/None
        if pd.isna(value):
            return None

        # Handle numpy types
        if hasattr(value, 'item'):
            return value.item()

        # Handle datetime
        if isinstance(value, pd.Timestamp):
            return value.to_pydatetime()

        return value

    def _sanitize_table_name(self, name: str) -> str:
        """
        Sanitize table name for PostgreSQL.

        Args:
            name: Raw table name

        Returns:
            Sanitized table name (lowercase, underscores only)
        """
        # Replace hyphens with underscores
        name = name.replace('-', '_')
        # Remove special characters
        name = ''.join(c if c.isalnum() or c == '_' else '_' for c in name)
        # Lowercase
        name = name.lower()
        # Ensure doesn't start with number
        if name and name[0].isdigit():
            name = f'_{name}'
        return name


async def get_database_writer(database_url: str) -> AirbyteDatabaseWriter:
    """
    Create database writer with connection pool.

    Args:
        database_url: PostgreSQL connection URL

    Returns:
        Initialized AirbyteDatabaseWriter instance

    Example:
        >>> writer = await get_database_writer("postgresql://user:pass@localhost/dbname")
        >>> count = await writer.write_to_explore("source", "stream", records, run_id)
    """
    try:
        pool = await asyncpg.create_pool(
            database_url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        logger.info("Created database connection pool (5-20 connections)")
        return AirbyteDatabaseWriter(pool)
    except Exception as e:
        logger.error(f"Failed to create database writer: {e}")
        raise
