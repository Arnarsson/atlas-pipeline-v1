"""
Atlas Database Module - REAL PostgreSQL Connection

This module provides actual database persistence with:
- Connection pooling via asyncpg
- pgvector for AI embeddings
- Audit logging for all data access
- Schema initialization

Author: Atlas Pipeline Team
Date: January 2026
"""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Optional
from uuid import uuid4
import json
import hashlib

import asyncpg
from loguru import logger

# Database URL from environment or default for local dev
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://atlas_user:atlas_password@localhost:5432/atlas_pipeline"
)


class AtlasDatabase:
    """
    Real PostgreSQL database connection with pgvector support.

    Features:
    - Async connection pooling
    - Automatic schema initialization
    - pgvector for embeddings
    - Audit logging
    """

    _instance: Optional["AtlasDatabase"] = None
    _pool: Optional[asyncpg.Pool] = None

    def __init__(self):
        self.database_url = DATABASE_URL
        self._initialized = False

    @classmethod
    async def get_instance(cls) -> "AtlasDatabase":
        """Get singleton database instance."""
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance.initialize()
        return cls._instance

    async def initialize(self):
        """Initialize database connection and schema."""
        if self._initialized:
            return

        try:
            logger.info(f"Connecting to PostgreSQL...")
            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60,
                statement_cache_size=0  # Disable for dynamic queries
            )

            # Initialize schema
            await self._init_schema()
            self._initialized = True
            logger.info("✅ Database connection established")

        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    async def _init_schema(self):
        """Create necessary schemas and tables."""
        async with self._pool.acquire() as conn:
            # Create schemas
            await conn.execute("""
                CREATE SCHEMA IF NOT EXISTS explore;
                CREATE SCHEMA IF NOT EXISTS chart;
                CREATE SCHEMA IF NOT EXISTS navigate;
                CREATE SCHEMA IF NOT EXISTS audit;
                CREATE SCHEMA IF NOT EXISTS vectors;
            """)

            # Enable pgvector extension if available
            try:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                logger.info("✅ pgvector extension enabled")
            except Exception as e:
                logger.warning(f"⚠️ pgvector not available: {e}")

            # Create core tables
            await conn.execute("""
                -- Source systems registry
                CREATE TABLE IF NOT EXISTS explore.source_systems (
                    source_id VARCHAR(100) PRIMARY KEY,
                    source_type VARCHAR(50) NOT NULL,
                    source_name VARCHAR(255) NOT NULL,
                    config JSONB,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );

                -- Raw data storage (Explore layer)
                CREATE TABLE IF NOT EXISTS explore.raw_data (
                    id BIGSERIAL PRIMARY KEY,
                    run_id UUID NOT NULL,
                    source_id VARCHAR(100) NOT NULL,
                    dataset_name VARCHAR(255) NOT NULL,
                    record_data JSONB NOT NULL,
                    checksum VARCHAR(64),
                    ingested_at TIMESTAMPTZ DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_raw_data_run ON explore.raw_data(run_id);
                CREATE INDEX IF NOT EXISTS idx_raw_data_source ON explore.raw_data(source_id);
                CREATE INDEX IF NOT EXISTS idx_raw_data_dataset ON explore.raw_data(dataset_name);
                CREATE INDEX IF NOT EXISTS idx_raw_data_jsonb ON explore.raw_data USING GIN(record_data);

                -- Validated data storage (Chart layer)
                CREATE TABLE IF NOT EXISTS chart.validated_data (
                    id BIGSERIAL PRIMARY KEY,
                    run_id UUID NOT NULL,
                    source_id VARCHAR(100) NOT NULL,
                    dataset_name VARCHAR(255) NOT NULL,
                    record_data JSONB NOT NULL,
                    quality_score NUMERIC(5,2),
                    pii_detected BOOLEAN DEFAULT FALSE,
                    pii_types TEXT[],
                    validated_at TIMESTAMPTZ DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_validated_run ON chart.validated_data(run_id);
                CREATE INDEX IF NOT EXISTS idx_validated_quality ON chart.validated_data(quality_score);

                -- Business-ready data (Navigate layer)
                CREATE TABLE IF NOT EXISTS navigate.business_data (
                    id BIGSERIAL PRIMARY KEY,
                    run_id UUID NOT NULL,
                    source_id VARCHAR(100) NOT NULL,
                    dataset_name VARCHAR(255) NOT NULL,
                    natural_key VARCHAR(255),
                    record_data JSONB NOT NULL,
                    valid_from TIMESTAMPTZ DEFAULT NOW(),
                    valid_to TIMESTAMPTZ DEFAULT '9999-12-31',
                    is_current BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_business_current ON navigate.business_data(natural_key) WHERE is_current = TRUE;

                -- Pipeline runs tracking
                CREATE TABLE IF NOT EXISTS explore.pipeline_runs (
                    run_id UUID PRIMARY KEY,
                    source_id VARCHAR(100),
                    dataset_name VARCHAR(255) NOT NULL,
                    filename VARCHAR(255),
                    status VARCHAR(50) NOT NULL,
                    record_count INTEGER,
                    quality_score NUMERIC(5,2),
                    pii_count INTEGER,
                    results JSONB,
                    error TEXT,
                    started_at TIMESTAMPTZ DEFAULT NOW(),
                    completed_at TIMESTAMPTZ
                );
                CREATE INDEX IF NOT EXISTS idx_runs_status ON explore.pipeline_runs(status);
                CREATE INDEX IF NOT EXISTS idx_runs_dataset ON explore.pipeline_runs(dataset_name);

                -- Audit log for ALL data access (EU AI Act Art. 12)
                CREATE TABLE IF NOT EXISTS audit.data_access_log (
                    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    user_id VARCHAR(255),
                    api_key VARCHAR(100),
                    action VARCHAR(50) NOT NULL,
                    resource_type VARCHAR(100) NOT NULL,
                    resource_id VARCHAR(255),
                    query_params JSONB,
                    records_accessed INTEGER,
                    data_accessed JSONB,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    duration_ms INTEGER,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit.data_access_log(timestamp);
                CREATE INDEX IF NOT EXISTS idx_audit_user ON audit.data_access_log(user_id);
                CREATE INDEX IF NOT EXISTS idx_audit_action ON audit.data_access_log(action);
                CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit.data_access_log(resource_type, resource_id);

                -- Retention: Keep audit logs for 5+ years (EU AI Act requirement)
                COMMENT ON TABLE audit.data_access_log IS
                    'Audit trail for all data access - 5+ year retention for EU AI Act Art. 12 compliance';
            """)

            # Create vector table if pgvector is available
            try:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS vectors.embeddings (
                        id BIGSERIAL PRIMARY KEY,
                        run_id UUID NOT NULL,
                        source_id VARCHAR(100) NOT NULL,
                        dataset_name VARCHAR(255) NOT NULL,
                        record_id BIGINT,
                        content TEXT NOT NULL,
                        embedding vector(1536),
                        metadata JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    CREATE INDEX IF NOT EXISTS idx_embeddings_run ON vectors.embeddings(run_id);
                    CREATE INDEX IF NOT EXISTS idx_embeddings_dataset ON vectors.embeddings(dataset_name);
                """)
                logger.info("✅ Vector embeddings table created")
            except Exception as e:
                logger.warning(f"⚠️ Vector table not created (pgvector may not be available): {e}")

            logger.info("✅ Database schema initialized")

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get a database connection from the pool."""
        if not self._pool:
            raise RuntimeError("Database not initialized")
        async with self._pool.acquire() as conn:
            yield conn

    async def close(self):
        """Close database connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._initialized = False
            logger.info("Database connection closed")


# =============================================================================
# DATA PERSISTENCE FUNCTIONS
# =============================================================================

async def persist_raw_data(
    db: AtlasDatabase,
    run_id: str,
    source_id: str,
    dataset_name: str,
    records: list[dict[str, Any]]
) -> int:
    """
    Persist raw data to Explore layer.

    Args:
        db: Database instance
        run_id: Pipeline run ID
        source_id: Source identifier
        dataset_name: Dataset name
        records: List of record dictionaries

    Returns:
        Number of records inserted
    """
    if not records:
        return 0

    async with db.connection() as conn:
        count = 0
        for record in records:
            checksum = hashlib.sha256(
                json.dumps(record, sort_keys=True).encode()
            ).hexdigest()

            await conn.execute("""
                INSERT INTO explore.raw_data (run_id, source_id, dataset_name, record_data, checksum)
                VALUES ($1, $2, $3, $4, $5)
            """, run_id, source_id, dataset_name, json.dumps(record), checksum)
            count += 1

        logger.info(f"✅ Persisted {count} raw records to explore.raw_data")
        return count


async def persist_validated_data(
    db: AtlasDatabase,
    run_id: str,
    source_id: str,
    dataset_name: str,
    records: list[dict[str, Any]],
    quality_score: float,
    pii_types: list[str]
) -> int:
    """
    Persist validated data to Chart layer.

    Args:
        db: Database instance
        run_id: Pipeline run ID
        source_id: Source identifier
        dataset_name: Dataset name
        records: List of record dictionaries
        quality_score: Overall quality score
        pii_types: List of detected PII types

    Returns:
        Number of records inserted
    """
    if not records:
        return 0

    async with db.connection() as conn:
        count = 0
        pii_detected = len(pii_types) > 0

        for record in records:
            await conn.execute("""
                INSERT INTO chart.validated_data
                (run_id, source_id, dataset_name, record_data, quality_score, pii_detected, pii_types)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, run_id, source_id, dataset_name, json.dumps(record),
                quality_score, pii_detected, pii_types)
            count += 1

        logger.info(f"✅ Persisted {count} validated records to chart.validated_data")
        return count


async def persist_business_data(
    db: AtlasDatabase,
    run_id: str,
    source_id: str,
    dataset_name: str,
    records: list[dict[str, Any]],
    natural_key_column: Optional[str] = None
) -> int:
    """
    Persist business-ready data to Navigate layer with SCD Type 2.

    Args:
        db: Database instance
        run_id: Pipeline run ID
        source_id: Source identifier
        dataset_name: Dataset name
        records: List of record dictionaries
        natural_key_column: Column to use as natural key

    Returns:
        Number of records processed
    """
    if not records:
        return 0

    async with db.connection() as conn:
        count = 0

        for record in records:
            # Determine natural key
            natural_key = None
            if natural_key_column and natural_key_column in record:
                natural_key = str(record[natural_key_column])
            elif records and len(record) > 0:
                # Use first column as natural key
                first_key = list(record.keys())[0]
                natural_key = str(record[first_key])

            if natural_key:
                # Check if record exists (SCD Type 2)
                existing = await conn.fetchrow("""
                    SELECT id FROM navigate.business_data
                    WHERE dataset_name = $1 AND natural_key = $2 AND is_current = TRUE
                """, dataset_name, natural_key)

                if existing:
                    # Close existing record
                    await conn.execute("""
                        UPDATE navigate.business_data
                        SET valid_to = NOW(), is_current = FALSE
                        WHERE id = $1
                    """, existing['id'])

            # Insert new record
            await conn.execute("""
                INSERT INTO navigate.business_data
                (run_id, source_id, dataset_name, natural_key, record_data)
                VALUES ($1, $2, $3, $4, $5)
            """, run_id, source_id, dataset_name, natural_key, json.dumps(record))
            count += 1

        logger.info(f"✅ Persisted {count} business records to navigate.business_data")
        return count


async def save_pipeline_run(
    db: AtlasDatabase,
    run_id: str,
    source_id: str,
    dataset_name: str,
    filename: str,
    status: str,
    record_count: int = 0,
    quality_score: float = 0.0,
    pii_count: int = 0,
    results: Optional[dict] = None,
    error: Optional[str] = None
) -> None:
    """Save pipeline run metadata."""
    async with db.connection() as conn:
        await conn.execute("""
            INSERT INTO explore.pipeline_runs
            (run_id, source_id, dataset_name, filename, status, record_count,
             quality_score, pii_count, results, error, completed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    CASE WHEN $5 IN ('completed', 'failed') THEN NOW() ELSE NULL END)
            ON CONFLICT (run_id) DO UPDATE SET
                status = EXCLUDED.status,
                record_count = EXCLUDED.record_count,
                quality_score = EXCLUDED.quality_score,
                pii_count = EXCLUDED.pii_count,
                results = EXCLUDED.results,
                error = EXCLUDED.error,
                completed_at = CASE WHEN EXCLUDED.status IN ('completed', 'failed') THEN NOW()
                               ELSE explore.pipeline_runs.completed_at END
        """, run_id, source_id, dataset_name, filename, status,
            record_count, quality_score, pii_count,
            json.dumps(results) if results else None, error)


# =============================================================================
# AUDIT LOGGING
# =============================================================================

async def log_data_access(
    db: AtlasDatabase,
    user_id: Optional[str],
    api_key: Optional[str],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    query_params: Optional[dict] = None,
    records_accessed: int = 0,
    data_accessed: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    duration_ms: Optional[int] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> str:
    """
    Log data access for audit trail (EU AI Act Art. 12 compliance).

    Args:
        user_id: User identifier (if authenticated)
        api_key: API key used (masked)
        action: Action performed (query, export, ai_access, etc.)
        resource_type: Type of resource accessed (dataset, run, connector)
        resource_id: Specific resource ID
        query_params: Query parameters used
        records_accessed: Number of records accessed
        data_accessed: Summary of data fields accessed
        ip_address: Client IP address
        user_agent: Client user agent
        duration_ms: Request duration in milliseconds
        success: Whether the access was successful
        error_message: Error message if failed

    Returns:
        Log entry ID
    """
    log_id = str(uuid4())

    async with db.connection() as conn:
        await conn.execute("""
            INSERT INTO audit.data_access_log
            (log_id, user_id, api_key, action, resource_type, resource_id,
             query_params, records_accessed, data_accessed, ip_address,
             user_agent, duration_ms, success, error_message)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        """, log_id, user_id, api_key, action, resource_type, resource_id,
            json.dumps(query_params) if query_params else None,
            records_accessed,
            json.dumps(data_accessed) if data_accessed else None,
            ip_address, user_agent, duration_ms, success, error_message)

    logger.debug(f"Audit logged: {action} on {resource_type}/{resource_id}")
    return log_id


# =============================================================================
# QUERY FUNCTIONS (for AI and reporting)
# =============================================================================

async def query_data(
    db: AtlasDatabase,
    dataset_name: str,
    layer: str = "navigate",
    filters: Optional[dict] = None,
    limit: int = 1000,
    offset: int = 0
) -> list[dict[str, Any]]:
    """
    Query data from specified layer.

    Args:
        db: Database instance
        dataset_name: Dataset to query
        layer: Data layer (explore, chart, navigate)
        filters: Optional JSONB filters
        limit: Max records to return
        offset: Records to skip

    Returns:
        List of records
    """
    table_map = {
        "explore": "explore.raw_data",
        "chart": "chart.validated_data",
        "navigate": "navigate.business_data"
    }

    if layer not in table_map:
        raise ValueError(f"Invalid layer: {layer}")

    table = table_map[layer]

    async with db.connection() as conn:
        query = f"""
            SELECT record_data, run_id, created_at
            FROM {table}
            WHERE dataset_name = $1
        """
        params = [dataset_name]

        if layer == "navigate":
            query += " AND is_current = TRUE"

        query += f" ORDER BY created_at DESC LIMIT $2 OFFSET $3"
        params.extend([limit, offset])

        rows = await conn.fetch(query, *params)

        return [
            {
                "data": json.loads(row["record_data"]),
                "run_id": str(row["run_id"]),
                "timestamp": row["created_at"].isoformat()
            }
            for row in rows
        ]


async def get_pipeline_runs(
    db: AtlasDatabase,
    dataset_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
) -> list[dict[str, Any]]:
    """Get pipeline run history."""
    async with db.connection() as conn:
        query = "SELECT * FROM explore.pipeline_runs WHERE 1=1"
        params = []

        if dataset_name:
            params.append(dataset_name)
            query += f" AND dataset_name = ${len(params)}"

        if status:
            params.append(status)
            query += f" AND status = ${len(params)}"

        params.append(limit)
        query += f" ORDER BY started_at DESC LIMIT ${len(params)}"

        rows = await conn.fetch(query, *params)

        return [dict(row) for row in rows]


async def get_audit_logs(
    db: AtlasDatabase,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100
) -> list[dict[str, Any]]:
    """
    Query audit logs.

    Args:
        db: Database instance
        resource_type: Filter by resource type
        resource_id: Filter by resource ID
        user_id: Filter by user
        start_date: Filter from date
        end_date: Filter to date
        limit: Max records

    Returns:
        List of audit log entries
    """
    async with db.connection() as conn:
        query = "SELECT * FROM audit.data_access_log WHERE 1=1"
        params = []

        if resource_type:
            params.append(resource_type)
            query += f" AND resource_type = ${len(params)}"

        if resource_id:
            params.append(resource_id)
            query += f" AND resource_id = ${len(params)}"

        if user_id:
            params.append(user_id)
            query += f" AND user_id = ${len(params)}"

        if start_date:
            params.append(start_date)
            query += f" AND timestamp >= ${len(params)}"

        if end_date:
            params.append(end_date)
            query += f" AND timestamp <= ${len(params)}"

        params.append(limit)
        query += f" ORDER BY timestamp DESC LIMIT ${len(params)}"

        rows = await conn.fetch(query, *params)

        return [dict(row) for row in rows]


# Singleton accessor
_db_instance: Optional[AtlasDatabase] = None

async def get_database() -> AtlasDatabase:
    """Get the singleton database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = await AtlasDatabase.get_instance()
    return _db_instance
