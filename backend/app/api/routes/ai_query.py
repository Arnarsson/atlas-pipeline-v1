"""
Atlas AI Query API

Structured API endpoints for AI agents to access data.
All access is audit-logged for EU AI Act compliance.

Features:
- Structured JSON output for AI consumption
- Semantic search via vector embeddings
- Full audit trail of all AI data access
- Schema discovery for agent tool use

Author: Atlas Pipeline Team
Date: January 2026
"""

import time
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, Header
from pydantic import BaseModel, Field
from loguru import logger

router = APIRouter(prefix="/ai", tags=["AI Query API"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class DataQueryRequest(BaseModel):
    """Request model for AI data queries."""
    dataset_name: str = Field(..., description="Name of the dataset to query")
    layer: str = Field("navigate", description="Data layer: explore, chart, or navigate")
    filters: Optional[dict[str, Any]] = Field(None, description="JSONB filters")
    columns: Optional[list[str]] = Field(None, description="Specific columns to return")
    limit: int = Field(100, ge=1, le=10000, description="Max records to return")
    offset: int = Field(0, ge=0, description="Records to skip")


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search."""
    query: str = Field(..., description="Natural language search query")
    dataset_name: Optional[str] = Field(None, description="Optional dataset filter")
    limit: int = Field(10, ge=1, le=100, description="Max results")


class DataRecord(BaseModel):
    """Single data record with metadata."""
    data: dict[str, Any]
    run_id: str
    timestamp: str
    dataset_name: str


class DataQueryResponse(BaseModel):
    """Response model for data queries."""
    success: bool = True
    dataset_name: str
    layer: str
    record_count: int
    records: list[DataRecord]
    query_id: str  # Audit reference
    timestamp: str


class SemanticSearchResponse(BaseModel):
    """Response model for semantic search."""
    success: bool = True
    query: str
    result_count: int
    results: list[dict[str, Any]]
    query_id: str  # Audit reference
    timestamp: str


class DatasetSchema(BaseModel):
    """Dataset schema information."""
    dataset_name: str
    layer: str
    columns: list[dict[str, str]]
    record_count: int
    sample_record: Optional[dict[str, Any]]
    last_updated: Optional[str]


class AvailableDatasets(BaseModel):
    """List of available datasets."""
    datasets: list[dict[str, Any]]
    total_count: int


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.get("/health")
async def ai_api_health():
    """Health check for AI API."""
    return {
        "status": "healthy",
        "service": "atlas-ai-query-api",
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "structured_queries": True,
            "semantic_search": True,
            "audit_logging": True
        }
    }


@router.get("/datasets", response_model=AvailableDatasets)
async def list_available_datasets(
    request: Request,
    layer: Optional[str] = Query(None, description="Filter by layer"),
    x_api_key: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None)
):
    """
    List all available datasets for AI access.

    This endpoint is designed for AI agents to discover available data.

    Returns:
        List of datasets with metadata
    """
    from app.core.database import get_database, log_data_access

    start_time = time.time()
    db = await get_database()

    async with db.connection() as conn:
        # Query distinct datasets from all layers
        datasets = []

        layers = ["explore", "chart", "navigate"] if not layer else [layer]

        for l in layers:
            if l == "explore":
                rows = await conn.fetch("""
                    SELECT DISTINCT dataset_name, COUNT(*) as record_count,
                           MAX(ingested_at) as last_updated
                    FROM explore.raw_data
                    GROUP BY dataset_name
                """)
            elif l == "chart":
                rows = await conn.fetch("""
                    SELECT DISTINCT dataset_name, COUNT(*) as record_count,
                           MAX(validated_at) as last_updated,
                           AVG(quality_score) as avg_quality
                    FROM chart.validated_data
                    GROUP BY dataset_name
                """)
            elif l == "navigate":
                rows = await conn.fetch("""
                    SELECT DISTINCT dataset_name, COUNT(*) as record_count,
                           MAX(created_at) as last_updated
                    FROM navigate.business_data
                    WHERE is_current = TRUE
                    GROUP BY dataset_name
                """)
            else:
                continue

            for row in rows:
                datasets.append({
                    "dataset_name": row["dataset_name"],
                    "layer": l,
                    "record_count": row["record_count"],
                    "last_updated": row["last_updated"].isoformat() if row["last_updated"] else None,
                    "avg_quality": float(row.get("avg_quality", 0)) if row.get("avg_quality") else None
                })

    # Audit log this access
    duration_ms = int((time.time() - start_time) * 1000)
    await log_data_access(
        db=db,
        user_id=x_user_id,
        api_key=x_api_key[:8] + "..." if x_api_key else None,
        action="list_datasets",
        resource_type="catalog",
        query_params={"layer": layer},
        records_accessed=len(datasets),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        duration_ms=duration_ms
    )

    return AvailableDatasets(
        datasets=datasets,
        total_count=len(datasets)
    )


@router.get("/datasets/{dataset_name}/schema", response_model=DatasetSchema)
async def get_dataset_schema(
    dataset_name: str,
    request: Request,
    layer: str = Query("navigate", description="Data layer"),
    x_api_key: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None)
):
    """
    Get schema information for a dataset.

    Useful for AI agents to understand data structure before querying.

    Returns:
        Schema with column names, types, and sample data
    """
    from app.core.database import get_database, log_data_access
    import json

    start_time = time.time()
    db = await get_database()

    async with db.connection() as conn:
        # Get sample record to infer schema
        table_map = {
            "explore": "explore.raw_data",
            "chart": "chart.validated_data",
            "navigate": "navigate.business_data"
        }

        if layer not in table_map:
            raise HTTPException(400, f"Invalid layer: {layer}")

        table = table_map[layer]

        # Get a sample record
        sample = await conn.fetchrow(f"""
            SELECT record_data FROM {table}
            WHERE dataset_name = $1
            LIMIT 1
        """, dataset_name)

        if not sample:
            raise HTTPException(404, f"Dataset {dataset_name} not found in {layer}")

        record_data = json.loads(sample["record_data"])

        # Infer columns from sample
        columns = []
        for key, value in record_data.items():
            col_type = type(value).__name__ if value is not None else "unknown"
            columns.append({"name": key, "type": col_type})

        # Get count
        count_row = await conn.fetchrow(f"""
            SELECT COUNT(*) as count FROM {table}
            WHERE dataset_name = $1
        """, dataset_name)

        record_count = count_row["count"] if count_row else 0

    # Audit log
    duration_ms = int((time.time() - start_time) * 1000)
    await log_data_access(
        db=db,
        user_id=x_user_id,
        api_key=x_api_key[:8] + "..." if x_api_key else None,
        action="get_schema",
        resource_type="dataset",
        resource_id=dataset_name,
        query_params={"layer": layer},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        duration_ms=duration_ms
    )

    return DatasetSchema(
        dataset_name=dataset_name,
        layer=layer,
        columns=columns,
        record_count=record_count,
        sample_record=record_data,
        last_updated=None
    )


@router.post("/query", response_model=DataQueryResponse)
async def query_data(
    query_request: DataQueryRequest,
    request: Request,
    x_api_key: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None)
):
    """
    Query data from Atlas pipeline.

    This is the main endpoint for AI agents to retrieve structured data.
    All queries are logged for audit purposes.

    Args:
        query_request: Query parameters

    Returns:
        Structured data response with records and metadata
    """
    from app.core.database import get_database, log_data_access, query_data as db_query
    from uuid import uuid4

    start_time = time.time()
    query_id = str(uuid4())

    db = await get_database()

    try:
        # Execute query
        records = await db_query(
            db=db,
            dataset_name=query_request.dataset_name,
            layer=query_request.layer,
            filters=query_request.filters,
            limit=query_request.limit,
            offset=query_request.offset
        )

        # Filter columns if specified
        if query_request.columns:
            for record in records:
                record["data"] = {
                    k: v for k, v in record["data"].items()
                    if k in query_request.columns
                }

        # Format response
        formatted_records = [
            DataRecord(
                data=r["data"],
                run_id=r["run_id"],
                timestamp=r["timestamp"],
                dataset_name=query_request.dataset_name
            )
            for r in records
        ]

        # Audit log the query
        duration_ms = int((time.time() - start_time) * 1000)
        await log_data_access(
            db=db,
            user_id=x_user_id,
            api_key=x_api_key[:8] + "..." if x_api_key else None,
            action="ai_query",
            resource_type="dataset",
            resource_id=query_request.dataset_name,
            query_params={
                "layer": query_request.layer,
                "filters": query_request.filters,
                "columns": query_request.columns,
                "limit": query_request.limit,
                "offset": query_request.offset
            },
            records_accessed=len(records),
            data_accessed={"columns": query_request.columns or "all"},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            duration_ms=duration_ms
        )

        return DataQueryResponse(
            success=True,
            dataset_name=query_request.dataset_name,
            layer=query_request.layer,
            record_count=len(formatted_records),
            records=formatted_records,
            query_id=query_id,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        # Log failed query
        await log_data_access(
            db=db,
            user_id=x_user_id,
            api_key=x_api_key[:8] + "..." if x_api_key else None,
            action="ai_query",
            resource_type="dataset",
            resource_id=query_request.dataset_name,
            success=False,
            error_message=str(e),
            ip_address=request.client.host if request.client else None
        )
        raise HTTPException(500, f"Query failed: {str(e)}")


@router.post("/search", response_model=SemanticSearchResponse)
async def semantic_search_endpoint(
    search_request: SemanticSearchRequest,
    request: Request,
    x_api_key: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None)
):
    """
    Semantic search across all data using vector embeddings.

    Use natural language to find relevant data across all datasets.
    Requires vector embeddings to be enabled.

    Args:
        search_request: Search query and parameters

    Returns:
        Semantically similar results with similarity scores
    """
    from app.core.database import get_database, log_data_access
    from app.ai.embeddings import get_embedding_service, semantic_search
    from uuid import uuid4

    start_time = time.time()
    query_id = str(uuid4())

    db = await get_database()
    embedding_service = get_embedding_service()

    try:
        results = await semantic_search(
            db=db,
            query=search_request.query,
            dataset_name=search_request.dataset_name,
            limit=search_request.limit,
            embedding_service=embedding_service
        )

        # Audit log
        duration_ms = int((time.time() - start_time) * 1000)
        await log_data_access(
            db=db,
            user_id=x_user_id,
            api_key=x_api_key[:8] + "..." if x_api_key else None,
            action="semantic_search",
            resource_type="vectors",
            resource_id=search_request.dataset_name,
            query_params={
                "query": search_request.query,
                "limit": search_request.limit
            },
            records_accessed=len(results),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            duration_ms=duration_ms
        )

        return SemanticSearchResponse(
            success=True,
            query=search_request.query,
            result_count=len(results),
            results=results,
            query_id=query_id,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(500, f"Search failed: {str(e)}")


@router.get("/audit/{query_id}")
async def get_audit_entry(
    query_id: str,
    request: Request,
    x_api_key: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None)
):
    """
    Get audit log entry for a specific query.

    Allows tracing what data was accessed by a specific AI query.

    Returns:
        Audit log entry with full access details
    """
    from app.core.database import get_database

    db = await get_database()

    async with db.connection() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM audit.data_access_log
            WHERE log_id = $1::uuid
        """, query_id)

        if not row:
            raise HTTPException(404, f"Audit entry {query_id} not found")

        return dict(row)


@router.get("/audit")
async def list_audit_logs(
    request: Request,
    resource_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    x_api_key: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None)
):
    """
    List audit logs for data access.

    Filter by resource type, user, or date range.
    Required for EU AI Act Article 12 compliance.

    Returns:
        List of audit log entries
    """
    from app.core.database import get_database, get_audit_logs

    db = await get_database()

    logs = await get_audit_logs(
        db=db,
        resource_type=resource_type,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )

    return {
        "logs": logs,
        "count": len(logs),
        "filters": {
            "resource_type": resource_type,
            "user_id": user_id,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        }
    }


# =============================================================================
# EXPORT ENDPOINTS (for AI model training / RAG)
# =============================================================================

@router.get("/export/{dataset_name}")
async def export_dataset(
    dataset_name: str,
    request: Request,
    layer: str = Query("navigate"),
    format: str = Query("json", description="Export format: json, jsonl, csv"),
    limit: int = Query(10000, ge=1, le=100000),
    x_api_key: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None)
):
    """
    Export dataset for AI model training or RAG ingestion.

    Returns data in formats suitable for:
    - Fine-tuning (JSONL)
    - RAG indexing (JSON with metadata)
    - Analysis (CSV)

    All exports are audit-logged.
    """
    from app.core.database import get_database, log_data_access, query_data as db_query
    from fastapi.responses import StreamingResponse
    import csv
    import io
    import json

    start_time = time.time()
    db = await get_database()

    records = await db_query(
        db=db,
        dataset_name=dataset_name,
        layer=layer,
        limit=limit
    )

    if not records:
        raise HTTPException(404, f"Dataset {dataset_name} not found or empty")

    # Audit log the export
    duration_ms = int((time.time() - start_time) * 1000)
    await log_data_access(
        db=db,
        user_id=x_user_id,
        api_key=x_api_key[:8] + "..." if x_api_key else None,
        action="ai_export",
        resource_type="dataset",
        resource_id=dataset_name,
        query_params={"layer": layer, "format": format, "limit": limit},
        records_accessed=len(records),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        duration_ms=duration_ms
    )

    if format == "jsonl":
        # JSONL format for fine-tuning
        def generate_jsonl():
            for record in records:
                yield json.dumps(record["data"]) + "\n"

        return StreamingResponse(
            generate_jsonl(),
            media_type="application/x-ndjson",
            headers={"Content-Disposition": f"attachment; filename={dataset_name}.jsonl"}
        )

    elif format == "csv":
        # CSV format
        output = io.StringIO()
        if records:
            fieldnames = list(records[0]["data"].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for record in records:
                writer.writerow(record["data"])

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={dataset_name}.csv"}
        )

    else:
        # JSON format (default)
        return {
            "dataset_name": dataset_name,
            "layer": layer,
            "record_count": len(records),
            "records": [r["data"] for r in records],
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "format": "json"
            }
        }
