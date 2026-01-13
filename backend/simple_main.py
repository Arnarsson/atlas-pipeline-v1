"""
Atlas Data Pipeline API

Production-ready data pipeline with:
- Real PostgreSQL persistence (Explore/Chart/Navigate layers)
- Vector embeddings for AI/RAG (pgvector)
- Structured AI query endpoints
- Full audit logging (EU AI Act Art. 12 compliance)

Author: Atlas Pipeline Team
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel

from app.connectors.base import ConnectionConfig
from app.connectors.registry import ConnectorRegistry
from app.monitoring.health import router as health_router
from app.monitoring.metrics import get_metrics, get_metrics_content_type, metrics_middleware
from app.api.routes.enhanced_catalog import router as enhanced_catalog_router
from app.api.routes.atlas_intelligence import router as atlas_intelligence_router
from app.api.routes.compliance_assessment import router as compliance_assessment_router
from app.api.routes.governance import router as governance_router
from app.api.routes.ai_query import router as ai_query_router
from app.api.routes.auth import router as auth_router
from app.pipeline.core.orchestrator import PipelineOrchestrator
from app.scheduler.tasks import (
    delete_connector,
    get_connector,
    get_run_history,
    list_connectors,
    register_connector,
    run_connector_pipeline,
    update_connector,
)

# Database imports (optional - graceful degradation if not available)
DB_AVAILABLE = False
try:
    from app.core.database import (
        get_database,
        persist_raw_data,
        persist_validated_data,
        persist_business_data,
        save_pipeline_run,
        log_data_access,
    )
    DB_AVAILABLE = True
    logger.info("✅ Database module loaded - persistence enabled")
except ImportError as e:
    logger.warning(f"⚠️ Database module not available: {e}")
    logger.warning("Running in memory-only mode (data lost on restart)")

# AI/RAG imports (optional)
RAG_AVAILABLE = False
try:
    from app.ai.embeddings import get_embedding_service, embed_and_store
    from app.connectors.airbyte.airbyte_rag import get_rag_pipeline, run_rag_sync
    RAG_AVAILABLE = True
    logger.info("✅ RAG pipeline loaded - vector embeddings enabled")
except ImportError as e:
    logger.warning(f"⚠️ RAG module not available: {e}")

# =============================================================================
# APPLICATION LIFECYCLE
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize/cleanup database."""
    # Startup
    if DB_AVAILABLE:
        try:
            db = await get_database()
            logger.info("✅ Database connected and schema initialized")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            logger.warning("Falling back to in-memory mode")

    yield  # Application runs here

    # Shutdown
    if DB_AVAILABLE:
        try:
            db = await get_database()
            await db.close()
            logger.info("Database connection closed")
        except Exception:
            pass


# Create FastAPI app
app = FastAPI(
    title="Atlas Data Pipeline",
    description="""
    Production-ready data pipeline with:
    - Real PostgreSQL persistence (Explore/Chart/Navigate layers)
    - Vector embeddings for AI/RAG (pgvector)
    - Structured AI query endpoints
    - Full audit logging (EU AI Act Art. 12 compliance)
    """,
    version="2.0.0",
    lifespan=lifespan,
)

# Add Prometheus metrics middleware
app.add_middleware(metrics_middleware())

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(enhanced_catalog_router)  # Phase 4: Enhanced Catalog
app.include_router(atlas_intelligence_router)  # Phase 5: Airbyte Integration
app.include_router(compliance_assessment_router)  # Phase 0: EU AI Act
app.include_router(governance_router)  # Phase 0: RBAC
app.include_router(ai_query_router)  # NEW: AI Query API for agents
app.include_router(auth_router)  # NEW: Client Authentication & API Keys

# In-memory storage (fallback when DB not available)
pipeline_runs: dict[str, dict[str, Any]] = {}


# ============================================================================
# Models
# ============================================================================


class PipelineRunResponse(BaseModel):
    """Response model for pipeline run."""
    run_id: str
    status: str
    message: str


class PipelineStatusResponse(BaseModel):
    """Response model for pipeline status."""
    run_id: str
    status: str
    current_step: str | None = None
    results: dict[str, Any] | None = None
    error: str | None = None


class QualityMetricsResponse(BaseModel):
    """Response model for quality metrics."""
    run_id: str
    dataset_name: str
    completeness_score: float
    validity_score: float
    consistency_score: float
    overall_score: float
    details: dict[str, Any]


class PIIReportResponse(BaseModel):
    """Response model for PII report."""
    run_id: str
    dataset_name: str
    pii_found: bool
    pii_count: int
    pii_types: list[str]
    pii_details: list[dict[str, Any]]


class ConnectorCreateRequest(BaseModel):
    """Request model for creating a connector."""
    source_type: str
    source_name: str
    config: dict[str, Any]
    schedule_cron: str | None = None
    enabled: bool = True
    incremental: bool = True
    timestamp_column: str | None = None
    table: str | None = None
    query: str | None = None
    description: str | None = None


class ConnectorUpdateRequest(BaseModel):
    """Request model for updating a connector."""
    config: dict[str, Any] | None = None
    schedule_cron: str | None = None
    enabled: bool | None = None
    incremental: bool | None = None
    timestamp_column: str | None = None
    table: str | None = None
    query: str | None = None
    description: str | None = None


class ConnectorResponse(BaseModel):
    """Response model for connector."""
    connector_id: str
    source_type: str
    source_name: str
    enabled: bool
    schedule_cron: str | None = None
    last_sync_at: str | None = None
    last_sync_status: str | None = None


class ConnectorTestResponse(BaseModel):
    """Response model for connector test."""
    connector_id: str
    source_name: str
    connection_status: str
    message: str


class ConnectorSyncResponse(BaseModel):
    """Response model for manual sync trigger."""
    connector_id: str
    run_id: str
    status: str
    message: str


# ============================================================================
# Routes
# ============================================================================


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint with feature status."""
    return {
        "message": "Atlas Data Pipeline API",
        "version": "2.0.0",
        "docs": "/docs",
        "features": {
            "database_persistence": DB_AVAILABLE,
            "vector_embeddings": RAG_AVAILABLE,
            "audit_logging": DB_AVAILABLE,
            "ai_query_api": True,
        },
        "endpoints": {
            "upload": "/pipeline/run",
            "ai_query": "/ai/query",
            "ai_search": "/ai/search",
            "audit_logs": "/ai/audit",
            "rag_sync": "/rag/sync",
        }
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/pipeline/run", response_model=PipelineRunResponse)
async def run_pipeline(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    dataset_name: str | None = None,
) -> PipelineRunResponse:
    """
    Trigger a data pipeline run.

    Uploads a CSV file and processes it through:
    1. Explore layer (bronze) - data ingestion
    2. Chart layer (silver) - PII scanning + quality checks
    """
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    run_id = str(uuid4())

    pipeline_runs[run_id] = {
        "run_id": run_id,
        "status": "queued",
        "filename": file.filename,
        "dataset_name": dataset_name or file.filename.replace('.csv', ''),
        "current_step": "queued",
        "results": {},
        "error": None,
    }

    content = await file.read()

    orchestrator = PipelineOrchestrator()
    background_tasks.add_task(
        orchestrator.run_pipeline,
        run_id=run_id,
        file_content=content,
        filename=file.filename,
        dataset_name=dataset_name or file.filename.replace('.csv', ''),
        storage=pipeline_runs,
    )

    return PipelineRunResponse(
        run_id=run_id,
        status="queued",
        message=f"Pipeline run {run_id} has been queued for processing",
    )


@app.get("/pipeline/status/{run_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(run_id: str) -> PipelineStatusResponse:
    """Check the status of a pipeline run."""
    if run_id not in pipeline_runs:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    run_data = pipeline_runs[run_id]

    return PipelineStatusResponse(
        run_id=run_data["run_id"],
        status=run_data["status"],
        current_step=run_data.get("current_step"),
        results=run_data.get("results"),
        error=run_data.get("error"),
    )


@app.get("/pipeline/runs")
async def list_pipeline_runs() -> list[dict[str, Any]]:
    """List all pipeline runs."""
    return [
        {
            "run_id": run["run_id"],
            "status": run["status"],
            "filename": run["filename"],
            "dataset_name": run["dataset_name"],
            "current_step": run.get("current_step"),
        }
        for run in pipeline_runs.values()
    ]


@app.delete("/pipeline/runs/{run_id}")
async def delete_pipeline_run(run_id: str) -> dict[str, str]:
    """Delete a pipeline run."""
    if run_id not in pipeline_runs:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    del pipeline_runs[run_id]

    return {"message": f"Pipeline run {run_id} deleted successfully"}


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint.

    Returns metrics in Prometheus exposition format for scraping.
    """
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type()
    )


@app.get("/dashboard/stats")
async def get_dashboard_stats() -> dict[str, Any]:
    """High-level dashboard statistics for the UI."""
    total_runs = len(pipeline_runs)

    def _quality_score(run: dict[str, Any]) -> float:
        results = run.get("results") or {}
        quality = results.get("quality") or {}
        return float(quality.get("overall_score") or 0.0)

    def _pii_count(run: dict[str, Any]) -> int:
        results = run.get("results") or {}
        pii = results.get("pii") or {}
        findings = pii.get("findings") or []
        return len(findings)

    completed = [run for run in pipeline_runs.values() if run.get("status") == "completed"]
    avg_quality_score = (
        sum(_quality_score(run) for run in completed) / len(completed)
        if completed else 0.0
    )
    total_pii_detections = sum(_pii_count(run) for run in completed)

    recent_runs = []
    for run_id, run in list(pipeline_runs.items())[-10:]:
        recent_runs.append({
            "run_id": run_id,
            "dataset_name": run.get("dataset_name"),
            "status": run.get("status"),
            "filename": run.get("filename"),
            "current_step": run.get("current_step"),
            "quality_score": _quality_score(run),
            "pii_detections": _pii_count(run),
            "created_at": run.get("created_at") or run.get("started_at") or "",
            "completed_at": run.get("completed_at") or "",
        })

    try:
        connectors = list_connectors()
        active_connectors = sum(1 for c in connectors if c.get("enabled", True))
    except Exception:
        active_connectors = 0

    return {
        "total_runs": total_runs,
        "avg_quality_score": avg_quality_score,
        "total_pii_detections": total_pii_detections,
        "recent_runs": recent_runs,
        "active_connectors": active_connectors,
    }


@app.get("/quality/metrics/{run_id}", response_model=QualityMetricsResponse)
async def get_quality_metrics(run_id: str) -> QualityMetricsResponse:
    """Get data quality metrics for a pipeline run.

    Week 3 Enhancement: Returns all 6 quality dimensions if Week 3 detectors are enabled.
    """
    if run_id not in pipeline_runs:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    run_data = pipeline_runs[run_id]

    if run_data["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Pipeline run {run_id} has not completed yet (status: {run_data['status']})"
        )

    results = run_data.get("results", {})
    quality_results = results.get("quality", {})

    return QualityMetricsResponse(
        run_id=run_id,
        dataset_name=run_data["dataset_name"],
        completeness_score=quality_results.get("completeness_score", 0.0),
        validity_score=quality_results.get("validity_score", 0.0),
        consistency_score=quality_results.get("consistency_score", 0.0),
        overall_score=quality_results.get("overall_score", 0.0),
        details=quality_results.get("details", {}),
    )


@app.get("/quality/dimensions/{run_id}")
async def get_quality_dimensions(run_id: str) -> dict[str, Any]:
    """Get detailed quality metrics for all 6 dimensions (Week 3 feature).

    Returns:
        Dictionary with all 6 quality dimensions and their detailed metrics
    """
    if run_id not in pipeline_runs:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    run_data = pipeline_runs[run_id]

    if run_data["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Pipeline run {run_id} has not completed yet (status: {run_data['status']})"
        )

    results = run_data.get("results", {})
    quality_results = results.get("quality", {})
    metadata = results.get("metadata", {})

    # Check if Week 3 dimensions are available
    all_dimensions = quality_results.get("details", {}).get("all_dimensions")

    if all_dimensions:
        # Week 3 format with 6 dimensions
        return {
            "run_id": run_id,
            "dataset_name": run_data["dataset_name"],
            "overall_score": quality_results.get("overall_score", 0.0),
            "dimensions": all_dimensions,
            "quality_validator": metadata.get("quality_validator", "unknown"),
            "week3_enabled": metadata.get("week3_enabled", False),
        }
    else:
        # Week 2 format - convert to dimension format
        return {
            "run_id": run_id,
            "dataset_name": run_data["dataset_name"],
            "overall_score": quality_results.get("overall_score", 0.0),
            "dimensions": {
                "completeness": {
                    "score": quality_results.get("completeness_score", 0.0),
                    "passed": quality_results.get("completeness_score", 0.0) >= 0.95,
                    "threshold": 0.95,
                    "details": {},
                },
                "validity": {
                    "score": quality_results.get("validity_score", 0.0),
                    "passed": quality_results.get("validity_score", 0.0) >= 0.90,
                    "threshold": 0.90,
                    "details": {},
                },
                "consistency": {
                    "score": quality_results.get("consistency_score", 0.0),
                    "passed": quality_results.get("consistency_score", 0.0) >= 0.90,
                    "threshold": 0.90,
                    "details": {},
                },
            },
            "quality_validator": "basic",
            "week3_enabled": False,
        }


@app.get("/quality/pii-report/{run_id}", response_model=PIIReportResponse)
async def get_pii_report(run_id: str) -> PIIReportResponse:
    """Get PII detection report for a pipeline run.

    Week 3 Enhancement: Includes confidence scores if Presidio was used.
    """
    if run_id not in pipeline_runs:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    run_data = pipeline_runs[run_id]

    if run_data["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Pipeline run {run_id} has not completed yet (status: {run_data['status']})"
        )

    results = run_data.get("results", {})
    pii_results = results.get("pii", {})

    pii_details = pii_results.get("findings", [])
    pii_types = list(set([finding["type"] for finding in pii_details]))

    return PIIReportResponse(
        run_id=run_id,
        dataset_name=run_data["dataset_name"],
        pii_found=len(pii_details) > 0,
        pii_count=len(pii_details),
        pii_types=pii_types,
        pii_details=pii_details,
    )


@app.get("/compliance/pii-detailed/{run_id}")
async def get_pii_detailed(run_id: str) -> dict[str, Any]:
    """Get detailed PII detection results with confidence scores (Week 3 feature).

    Returns:
        Dictionary with detailed PII findings including confidence scores
    """
    if run_id not in pipeline_runs:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    run_data = pipeline_runs[run_id]

    if run_data["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Pipeline run {run_id} has not completed yet (status: {run_data['status']})"
        )

    results = run_data.get("results", {})
    pii_results = results.get("pii", {})
    metadata = results.get("metadata", {})

    pii_details = pii_results.get("findings", [])

    # Aggregate by PII type
    pii_by_type = {}
    for finding in pii_details:
        pii_type = finding["type"]
        if pii_type not in pii_by_type:
            pii_by_type[pii_type] = {
                "type": pii_type,
                "total_instances": 0,
                "affected_columns": [],
                "avg_confidence": 0.0,
                "min_confidence": 1.0,
                "max_confidence": 0.0,
            }

        pii_by_type[pii_type]["total_instances"] += finding.get("match_count", 0)
        pii_by_type[pii_type]["affected_columns"].append(finding["column"])

        # Add confidence if available (Week 3)
        confidence = finding.get("confidence")
        if confidence is not None:
            current_avg = pii_by_type[pii_type]["avg_confidence"]
            count = len(pii_by_type[pii_type]["affected_columns"])
            pii_by_type[pii_type]["avg_confidence"] = (
                (current_avg * (count - 1) + confidence) / count
            )
            pii_by_type[pii_type]["min_confidence"] = min(
                pii_by_type[pii_type]["min_confidence"], confidence
            )
            pii_by_type[pii_type]["max_confidence"] = max(
                pii_by_type[pii_type]["max_confidence"], confidence
            )

    return {
        "run_id": run_id,
        "dataset_name": run_data["dataset_name"],
        "pii_found": len(pii_details) > 0,
        "total_pii_types": len(pii_by_type),
        "total_pii_instances": sum(
            p["total_instances"] for p in pii_by_type.values()
        ),
        "pii_by_type": list(pii_by_type.values()),
        "detailed_findings": pii_details,
        "pii_detector": metadata.get("pii_detector", "unknown"),
        "week3_enabled": metadata.get("week3_enabled", False),
    }


@app.get("/compliance/report/{run_id}")
async def get_compliance_report(run_id: str) -> dict[str, Any]:
    """Get compliance report for a pipeline run."""
    if run_id not in pipeline_runs:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    run_data = pipeline_runs[run_id]

    if run_data["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Pipeline run {run_id} has not completed yet (status: {run_data['status']})"
        )

    results = run_data.get("results", {})
    quality_results = results.get("quality", {})
    pii_results = results.get("pii", {})

    pii_count = len(pii_results.get("findings", []))
    overall_quality = quality_results.get("overall_score", 0.0)

    compliance_status = "compliant"
    issues = []
    recommendations = []

    if pii_count > 0:
        compliance_status = "non_compliant"
        issues.append(f"Found {pii_count} PII fields that need anonymization")
        recommendations.append("Apply anonymization to detected PII fields")

    if overall_quality < 0.7:
        if compliance_status == "compliant":
            compliance_status = "warning"
        issues.append(f"Data quality score below threshold: {overall_quality:.2%}")
        recommendations.append("Review and improve data quality issues")

    return {
        "run_id": run_id,
        "dataset_name": run_data["dataset_name"],
        "compliance_status": compliance_status,
        "overall_quality_score": overall_quality,
        "pii_count": pii_count,
        "issues": issues,
        "recommendations": recommendations,
        "quality_details": quality_results,
        "pii_details": pii_results,
    }


# ============================================================================
# Connector Management Routes (Week 4)
# ============================================================================


@app.get("/connectors/types")
async def list_connector_types() -> dict[str, Any]:
    """List all available connector types."""
    return {
        "connector_types": ConnectorRegistry.list_connectors(),
        "total": len(ConnectorRegistry.list_connectors()),
    }


@app.post("/connectors/", response_model=ConnectorResponse)
async def create_connector(request: ConnectorCreateRequest) -> ConnectorResponse:
    """Register a new data source connector."""
    # Validate connector type
    if not ConnectorRegistry.is_registered(request.source_type):
        raise HTTPException(
            status_code=400,
            detail=f"Unknown connector type: {request.source_type}. "
                   f"Available types: {ConnectorRegistry.list_connectors()}"
        )

    # Validate config
    try:
        ConnectionConfig(**request.config)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid connector configuration: {e}"
        )

    # Register connector
    connector_data = {
        "source_type": request.source_type,
        "source_name": request.source_name,
        "config": request.config,
        "schedule_cron": request.schedule_cron,
        "enabled": request.enabled,
        "incremental": request.incremental,
        "timestamp_column": request.timestamp_column,
        "table": request.table,
        "query": request.query,
        "description": request.description,
    }

    connector_id = register_connector(connector_data)

    return ConnectorResponse(
        connector_id=connector_id,
        source_type=request.source_type,
        source_name=request.source_name,
        enabled=request.enabled,
        schedule_cron=request.schedule_cron,
    )


@app.get("/connectors/")
async def get_all_connectors() -> list[dict[str, Any]]:
    """List all registered connectors."""
    connectors = list_connectors()
    return [
        {
            "connector_id": c["connector_id"],
            "source_type": c["source_type"],
            "source_name": c["source_name"],
            "enabled": c.get("enabled", True),
            "schedule_cron": c.get("schedule_cron"),
            "last_sync_at": c.get("last_sync_at"),
            "last_sync_status": c.get("last_sync_status"),
        }
        for c in connectors
    ]


@app.get("/connectors/{connector_id}")
async def get_connector_details(connector_id: str) -> dict[str, Any]:
    """Get detailed connector configuration."""
    connector = get_connector(connector_id)

    if not connector:
        raise HTTPException(
            status_code=404,
            detail=f"Connector {connector_id} not found"
        )

    return connector


@app.put("/connectors/{connector_id}", response_model=ConnectorResponse)
async def update_connector_config(
    connector_id: str,
    request: ConnectorUpdateRequest
) -> ConnectorResponse:
    """Update connector configuration."""
    connector = get_connector(connector_id)

    if not connector:
        raise HTTPException(
            status_code=404,
            detail=f"Connector {connector_id} not found"
        )

    # Build updates dict
    updates = {}
    if request.config is not None:
        # Validate config
        try:
            ConnectionConfig(**request.config)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid connector configuration: {e}"
            )
        updates["config"] = request.config

    if request.schedule_cron is not None:
        updates["schedule_cron"] = request.schedule_cron
    if request.enabled is not None:
        updates["enabled"] = request.enabled
    if request.incremental is not None:
        updates["incremental"] = request.incremental
    if request.timestamp_column is not None:
        updates["timestamp_column"] = request.timestamp_column
    if request.table is not None:
        updates["table"] = request.table
    if request.query is not None:
        updates["query"] = request.query
    if request.description is not None:
        updates["description"] = request.description

    # Update connector
    success = update_connector(connector_id, updates)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to update connector"
        )

    # Get updated connector
    updated = get_connector(connector_id)

    return ConnectorResponse(
        connector_id=connector_id,
        source_type=updated["source_type"],
        source_name=updated["source_name"],
        enabled=updated.get("enabled", True),
        schedule_cron=updated.get("schedule_cron"),
        last_sync_at=updated.get("last_sync_at"),
        last_sync_status=updated.get("last_sync_status"),
    )


@app.delete("/connectors/{connector_id}")
async def delete_connector_endpoint(connector_id: str) -> dict[str, str]:
    """Delete a connector."""
    success = delete_connector(connector_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Connector {connector_id} not found"
        )

    return {"message": f"Connector {connector_id} deleted successfully"}


@app.post("/connectors/{connector_id}/test", response_model=ConnectorTestResponse)
async def test_connector_connection(connector_id: str) -> ConnectorTestResponse:
    """Test connector connection."""
    import asyncio

    connector_data = get_connector(connector_id)

    if not connector_data:
        raise HTTPException(
            status_code=404,
            detail=f"Connector {connector_id} not found"
        )

    try:
        # Build ConnectionConfig
        config = ConnectionConfig(**connector_data["config"])

        # Get connector class
        connector_class = ConnectorRegistry.get_connector(config.source_type)

        # Test connection
        async def test_async():
            async with connector_class(config) as connector:
                return await connector.test_connection()

        is_healthy = asyncio.run(test_async())

        if is_healthy:
            return ConnectorTestResponse(
                connector_id=connector_id,
                source_name=connector_data["source_name"],
                connection_status="success",
                message="Connection test successful"
            )
        else:
            return ConnectorTestResponse(
                connector_id=connector_id,
                source_name=connector_data["source_name"],
                connection_status="failed",
                message="Connection test failed"
            )

    except Exception as e:
        return ConnectorTestResponse(
            connector_id=connector_id,
            source_name=connector_data["source_name"],
            connection_status="error",
            message=f"Connection test error: {str(e)}"
        )


@app.post("/connectors/{connector_id}/sync", response_model=ConnectorSyncResponse)
async def trigger_manual_sync(connector_id: str) -> ConnectorSyncResponse:
    """Manually trigger a sync for a connector."""
    connector = get_connector(connector_id)

    if not connector:
        raise HTTPException(
            status_code=404,
            detail=f"Connector {connector_id} not found"
        )

    try:
        # Queue connector pipeline using Celery
        task = run_connector_pipeline.delay(connector_id, triggered_by="manual")

        return ConnectorSyncResponse(
            connector_id=connector_id,
            run_id=task.id,
            status="queued",
            message=f"Manual sync queued for connector {connector_id}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue sync: {str(e)}"
        )


@app.get("/connectors/{connector_id}/history")
async def get_connector_sync_history(connector_id: str) -> dict[str, Any]:
    """Get sync history for a connector."""
    connector = get_connector(connector_id)

    if not connector:
        raise HTTPException(
            status_code=404,
            detail=f"Connector {connector_id} not found"
        )

    history = get_run_history(connector_id)

    return {
        "connector_id": connector_id,
        "source_name": connector["source_name"],
        "total_runs": len(history),
        "runs": sorted(
            history,
            key=lambda x: x.get("started_at", ""),
            reverse=True
        )
    }


# ============================================================================
# WEEK 5-6: DATA LINEAGE API
# ============================================================================


@app.get("/lineage/dataset/{dataset_name}")
async def get_dataset_lineage(dataset_name: str, depth: int = 10) -> dict[str, Any]:
    """
    Get lineage graph for a dataset.

    Args:
        dataset_name: Dataset name (e.g., "explore.raw_data")
        depth: Lineage graph depth (default: 10)

    Returns:
        Lineage graph with upstream and downstream datasets
    """
    from app.lineage.openlineage_client import get_lineage_client

    client = get_lineage_client()
    lineage_graph = client.query_lineage_graph(dataset_name, depth)

    if not lineage_graph:
        return {
            "dataset": dataset_name,
            "lineage_available": False,
            "message": "Lineage data not available (Marquez may be unavailable)"
        }

    return {
        "dataset": dataset_name,
        "lineage_available": True,
        "graph": lineage_graph
    }


@app.get("/lineage/run/{run_id}")
async def get_run_lineage(run_id: str) -> dict[str, Any]:
    """Get lineage for a specific pipeline run."""
    if run_id not in pipeline_runs:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    run_data = pipeline_runs[run_id]

    # In production, this would query Marquez for the run's lineage
    return {
        "run_id": run_id,
        "dataset_name": run_data["dataset_name"],
        "inputs": [{"name": run_data["filename"], "type": "file"}],
        "outputs": [
            {"name": "explore.raw_data", "type": "table"},
            {"name": "chart.validated_data", "type": "table"}
        ],
        "lineage_available": True
    }


# ============================================================================
# WEEK 5-6: FEATURE STORE API
# ============================================================================


@app.get("/features/groups")
async def list_feature_groups(tags: list[str] | None = None) -> list[dict[str, Any]]:
    """List all feature groups, optionally filtered by tags."""
    from app.features.feature_store import get_feature_store

    store = get_feature_store()
    groups = store.list_feature_groups(tags=tags)

    return [
        {
            "feature_group_id": g.feature_group_id,
            "name": g.name,
            "description": g.description,
            "version": g.version,
            "created_at": g.created_at.isoformat(),
            "created_by": g.created_by,
            "tags": g.tags
        }
        for g in groups
    ]


@app.post("/features/groups")
async def register_feature_group(
    name: str,
    description: str,
    file: UploadFile = File(...),
    version: str = "1.0.0",
    tags: list[str] | None = None
) -> dict[str, Any]:
    """
    Register a new feature group from CSV file.

    Args:
        name: Feature group name (e.g., "customer_demographics")
        description: Description of features
        file: CSV file containing features
        version: Semantic version (default: 1.0.0)
        tags: Optional tags

    Returns:
        Feature group metadata
    """
    from app.features.feature_store import get_feature_store
    import pandas as pd
    from io import BytesIO

    # Read CSV
    contents = await file.read()
    df = pd.read_csv(BytesIO(contents))

    store = get_feature_store()
    feature_group = store.register_feature_group(
        name=name,
        description=description,
        df=df,
        version=version,
        tags=tags or []
    )

    return {
        "feature_group_id": feature_group.feature_group_id,
        "name": feature_group.name,
        "version": feature_group.version,
        "row_count": len(df),
        "feature_count": len(df.columns),
        "message": f"Feature group {name} v{version} registered successfully"
    }


@app.get("/features/{name}/versions")
async def get_feature_versions(name: str) -> list[dict[str, Any]]:
    """Get all versions for a feature group."""
    from app.features.feature_store import get_feature_store

    store = get_feature_store()
    versions = store.get_versions(name)

    if not versions:
        raise HTTPException(status_code=404, detail=f"Feature group {name} not found")

    return [
        {
            "version_id": v.version_id,
            "version": v.version,
            "row_count": v.row_count,
            "quality_score": float(v.quality_score),
            "created_at": v.created_at.isoformat(),
            "is_latest": v.is_latest
        }
        for v in versions
    ]


@app.get("/features/{name}/latest")
async def get_latest_features(name: str) -> dict[str, Any]:
    """Get latest version of a feature group."""
    from app.features.feature_store import get_feature_store

    store = get_feature_store()
    version = store.get_latest_version(name)

    if not version:
        raise HTTPException(status_code=404, detail=f"Feature group {name} not found")

    metadata = store.get_feature_metadata(name)

    return {
        "version_id": version.version_id,
        "version": version.version,
        "dataset_location": version.dataset_location,
        "row_count": version.row_count,
        "quality_score": float(version.quality_score),
        "features": [
            {
                "feature_name": m.feature_name,
                "data_type": m.data_type,
                "null_percentage": float(m.null_percentage) if m.null_percentage else None,
                "unique_percentage": float(m.unique_percentage) if m.unique_percentage else None
            }
            for m in metadata
        ]
    }


@app.post("/features/{name}/export")
async def export_features(
    name: str,
    format: str = "parquet",
    version: str | None = None
) -> dict[str, Any]:
    """
    Export features in specified format.

    Args:
        name: Feature group name
        format: Export format (parquet, csv, json)
        version: Optional specific version
    """
    from app.features.feature_store import get_feature_store, ExportFormat

    store = get_feature_store()

    try:
        export_format = ExportFormat(format)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format: {format}. Must be one of: parquet, csv, json, tfrecord"
        )

    result = store.export_features(name, export_format, version)
    return result


# ============================================================================
# WEEK 5-6: GDPR API
# ============================================================================


@app.post("/gdpr/export")
async def gdpr_export_data(
    identifier: str,
    identifier_type: str = "email"
) -> dict[str, Any]:
    """
    GDPR Right to Access (Article 15): Export all data for a subject.

    Args:
        identifier: Subject identifier (email, phone, etc.)
        identifier_type: Type of identifier
    """
    from app.compliance.gdpr import get_gdpr_manager, IdentifierType

    try:
        id_type = IdentifierType(identifier_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid identifier type: {identifier_type}"
        )

    manager = get_gdpr_manager()
    export_data = manager.request_data_access(identifier, id_type)

    return export_data


@app.post("/gdpr/delete")
async def gdpr_delete_data(
    identifier: str,
    identifier_type: str = "email",
    reason: str = "User request"
) -> dict[str, Any]:
    """
    GDPR Right to Deletion (Article 17): Delete all data for a subject.

    Args:
        identifier: Subject identifier
        identifier_type: Type of identifier
        reason: Reason for deletion
    """
    from app.compliance.gdpr import get_gdpr_manager, IdentifierType

    try:
        id_type = IdentifierType(identifier_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid identifier type: {identifier_type}"
        )

    manager = get_gdpr_manager()
    deletion_counts = manager.request_data_deletion(identifier, id_type, reason)

    return {
        "identifier": identifier,
        "deletion_counts": deletion_counts,
        "message": f"Deleted {deletion_counts.get('total', 0)} records"
    }


@app.post("/gdpr/rectify")
async def gdpr_rectify_data(
    identifier: str,
    updates: dict[str, Any],
    identifier_type: str = "email"
) -> dict[str, Any]:
    """
    GDPR Right to Rectification (Article 16): Update data for a subject.

    Args:
        identifier: Subject identifier
        updates: Dictionary of fields to update
        identifier_type: Type of identifier
    """
    from app.compliance.gdpr import get_gdpr_manager, IdentifierType

    try:
        id_type = IdentifierType(identifier_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid identifier type: {identifier_type}"
        )

    manager = get_gdpr_manager()
    update_counts = manager.request_data_rectification(identifier, updates, id_type)

    return {
        "identifier": identifier,
        "update_counts": update_counts,
        "message": f"Updated {update_counts.get('total', 0)} records"
    }


@app.get("/gdpr/requests")
async def list_gdpr_requests(
    status: str | None = None,
    request_type: str | None = None
) -> list[dict[str, Any]]:
    """List GDPR requests with optional filters."""
    from app.compliance.gdpr import get_gdpr_manager, GDPRRequestStatus, GDPRRequestType

    manager = get_gdpr_manager()

    status_filter = None
    if status:
        try:
            status_filter = GDPRRequestStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    type_filter = None
    if request_type:
        try:
            type_filter = GDPRRequestType(request_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid request type: {request_type}")

    requests = manager.list_requests(status=status_filter, request_type=type_filter)

    return [
        {
            "request_id": r.request_id,
            "subject_id": r.subject_id,
            "request_type": r.request_type,
            "status": r.status,
            "requested_at": r.requested_at.isoformat(),
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "processed_by": r.processed_by
        }
        for r in requests
    ]


@app.get("/gdpr/audit/{subject_id}")
async def get_gdpr_audit_trail(subject_id: str) -> list[dict[str, Any]]:
    """Get audit trail for a data subject."""
    from app.compliance.gdpr import get_gdpr_manager

    manager = get_gdpr_manager()
    audit_entries = manager.get_audit_trail(subject_id)

    return [
        {
            "log_id": e.log_id,
            "operation": e.operation,
            "performed_by": e.performed_by,
            "timestamp": e.timestamp.isoformat(),
            "details": e.details
        }
        for e in audit_entries
    ]


# ============================================================================
# WEEK 5-6: DATA CATALOG API
# ============================================================================


@app.get("/catalog/datasets")
async def search_catalog_datasets(
    query: str | None = None,
    namespace: str | None = None,
    tags: list[str] | None = None
) -> list[dict[str, Any]]:
    """
    Search datasets in the catalog.

    Args:
        query: Search query (searches name, description, columns)
        namespace: Filter by namespace (explore, chart, navigate)
        tags: Filter by tags
    """
    from app.catalog.catalog import get_data_catalog, DatasetNamespace

    catalog = get_data_catalog()

    namespace_filter = None
    if namespace:
        try:
            namespace_filter = DatasetNamespace(namespace)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid namespace: {namespace}")

    datasets = catalog.search_datasets(
        query=query,
        namespace=namespace_filter,
        tags=tags
    )

    return [
        {
            "dataset_id": d.dataset_id,
            "namespace": d.namespace,
            "name": d.name,
            "description": d.description,
            "owner": d.owner,
            "tags": d.tags,
            "row_count": d.row_count_estimate,
            "column_count": len(d.columns) if d.columns else 0,
            "last_updated": d.last_updated.isoformat()
        }
        for d in datasets
    ]


@app.get("/catalog/dataset/{dataset_id}")
async def get_catalog_dataset(dataset_id: str) -> dict[str, Any]:
    """Get detailed metadata for a dataset."""
    from app.catalog.catalog import get_data_catalog

    catalog = get_data_catalog()
    dataset = catalog.get_dataset_by_id(dataset_id)

    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")

    return {
        "dataset_id": dataset.dataset_id,
        "namespace": dataset.namespace,
        "name": dataset.name,
        "description": dataset.description,
        "owner": dataset.owner,
        "tags": dataset.tags,
        "created_at": dataset.created_at.isoformat(),
        "last_updated": dataset.last_updated.isoformat(),
        "row_count": dataset.row_count_estimate,
        "size_bytes": dataset.size_bytes,
        "columns": [
            {
                "column_name": c.column_name,
                "data_type": c.data_type,
                "nullable": c.nullable,
                "pii_type": c.pii_type,
                "description": c.description
            }
            for c in dataset.columns
        ] if dataset.columns else []
    }


@app.get("/catalog/dataset/{dataset_id}/quality")
async def get_catalog_quality_history(dataset_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """Get quality history for a dataset."""
    from app.catalog.catalog import get_data_catalog

    catalog = get_data_catalog()
    history = catalog.get_quality_history(dataset_id, limit)

    return [
        {
            "timestamp": h.timestamp.isoformat(),
            "completeness_score": float(h.completeness_score),
            "validity_score": float(h.validity_score),
            "consistency_score": float(h.consistency_score),
            "overall_score": float(h.overall_score)
        }
        for h in history
    ]


@app.get("/catalog/dataset/{dataset_id}/lineage")
async def get_catalog_dataset_lineage(dataset_id: str) -> dict[str, Any]:
    """Get lineage graph for a dataset from catalog."""
    from app.catalog.catalog import get_data_catalog

    catalog = get_data_catalog()
    lineage = catalog.get_dataset_lineage(dataset_id)

    if not lineage:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")

    return lineage


@app.post("/catalog/dataset/{dataset_id}/tags")
async def add_catalog_dataset_tags(dataset_id: str, tags: list[str]) -> dict[str, Any]:
    """Add tags to a dataset."""
    from app.catalog.catalog import get_data_catalog

    catalog = get_data_catalog()
    dataset = catalog.get_dataset_by_id(dataset_id)

    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")

    catalog.add_tags_to_dataset(dataset.namespace, dataset.name, tags)

    return {
        "dataset_id": dataset_id,
        "tags_added": tags,
        "message": f"Tags added to dataset {dataset.name}"
    }


@app.get("/catalog/tags")
async def list_catalog_tags() -> list[dict[str, Any]]:
    """List all available tags."""
    from app.catalog.catalog import get_data_catalog

    catalog = get_data_catalog()
    tags = catalog.list_tags()

    return [
        {
            "tag_id": t.tag_id,
            "tag_name": t.tag_name,
            "color": t.color,
            "description": t.description
        }
        for t in tags
    ]


@app.get("/catalog/stats")
async def get_catalog_stats() -> dict[str, Any]:
    """Get catalog statistics."""
    from app.catalog.catalog import get_data_catalog

    catalog = get_data_catalog()
    return catalog.get_catalog_stats()


# =============================================================================
# RAG SYNC ENDPOINTS (Airbyte + Vector Embeddings)
# =============================================================================


class RAGSyncRequest(BaseModel):
    """Request model for RAG sync."""
    source_name: str
    config: dict[str, Any]
    dataset_name: str
    streams: list[str] | None = None
    use_chroma: bool = False


class RAGSyncResponse(BaseModel):
    """Response model for RAG sync."""
    run_id: str
    source: str
    dataset_name: str
    records_processed: int
    chunks_created: int
    chunks_embedded: int
    chunks_stored: int
    status: str


@app.get("/rag/sources")
async def list_rag_sources() -> dict[str, Any]:
    """
    List available data sources for RAG sync.

    Returns Airbyte connectors available for data extraction.
    """
    if RAG_AVAILABLE:
        pipeline = get_rag_pipeline()
        sources = pipeline.list_available_sources()
    else:
        sources = [
            {"name": "source-postgres", "type": "database"},
            {"name": "source-mysql", "type": "database"},
            {"name": "source-salesforce", "type": "crm"},
            {"name": "source-hubspot", "type": "crm"},
            {"name": "source-stripe", "type": "payments"},
            {"name": "source-github", "type": "devtools"},
        ]

    return {
        "sources": sources,
        "total": len(sources),
        "rag_enabled": RAG_AVAILABLE,
        "message": "Use /rag/sync to sync data from any source to vector store"
    }


@app.post("/rag/sync", response_model=RAGSyncResponse)
async def sync_to_rag(request: RAGSyncRequest) -> RAGSyncResponse:
    """
    Sync data from an Airbyte source to vector store.

    Extracts data, chunks it, generates embeddings, and stores in pgvector/Chroma.
    This makes data available for AI semantic search.

    Args:
        request: Source configuration and sync options

    Returns:
        Sync results with statistics
    """
    if not RAG_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not available. Install: pip install sentence-transformers"
        )

    try:
        if DB_AVAILABLE:
            db = await get_database()
            result = await run_rag_sync(
                db=db,
                source_name=request.source_name,
                config=request.config,
                dataset_name=request.dataset_name,
                streams=request.streams,
                use_chroma=request.use_chroma
            )
        else:
            # Mock result for development
            result = {
                "run_id": str(uuid4()),
                "source": request.source_name,
                "dataset_name": request.dataset_name,
                "records_processed": 0,
                "chunks_created": 0,
                "chunks_embedded": 0,
                "chunks_stored": 0
            }

        return RAGSyncResponse(
            **result,
            status="completed"
        )

    except Exception as e:
        logger.error(f"RAG sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# PERSISTENT PIPELINE (Database-backed)
# =============================================================================


@app.post("/pipeline/run/persistent")
async def run_persistent_pipeline(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    dataset_name: str | None = None,
    embed_for_rag: bool = False,
) -> dict[str, Any]:
    """
    Run pipeline with REAL database persistence.

    Unlike /pipeline/run, this endpoint:
    1. Persists raw data to PostgreSQL (explore layer)
    2. Persists validated data with PII/quality metadata (chart layer)
    3. Persists business-ready data with SCD Type 2 (navigate layer)
    4. Optionally generates vector embeddings for RAG
    5. Logs all operations to audit trail

    Args:
        file: CSV file to process
        dataset_name: Name for the dataset
        embed_for_rag: Generate vector embeddings for AI search

    Returns:
        Run ID and status
    """
    if not DB_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Database not available. Start PostgreSQL and set DATABASE_URL"
        )

    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    run_id = str(uuid4())
    ds_name = dataset_name or file.filename.replace('.csv', '')
    source_id = "csv_upload"

    content = await file.read()

    # Run persistent pipeline in background
    background_tasks.add_task(
        _run_persistent_pipeline_task,
        run_id=run_id,
        source_id=source_id,
        dataset_name=ds_name,
        filename=file.filename,
        content=content,
        embed_for_rag=embed_for_rag,
    )

    return {
        "run_id": run_id,
        "status": "queued",
        "dataset_name": ds_name,
        "persist_to_db": True,
        "embed_for_rag": embed_for_rag,
        "message": f"Persistent pipeline run {run_id} queued. Data will be stored in PostgreSQL."
    }


async def _run_persistent_pipeline_task(
    run_id: str,
    source_id: str,
    dataset_name: str,
    filename: str,
    content: bytes,
    embed_for_rag: bool,
):
    """Background task for persistent pipeline."""
    import io
    import pandas as pd

    db = await get_database()

    try:
        # Save initial run status
        await save_pipeline_run(
            db=db,
            run_id=run_id,
            source_id=source_id,
            dataset_name=dataset_name,
            filename=filename,
            status="running"
        )

        # Step 1: Parse CSV
        logger.info(f"[{run_id}] Step 1: Parsing CSV")
        df = pd.read_csv(io.BytesIO(content))
        records = df.to_dict(orient='records')
        logger.info(f"[{run_id}] Parsed {len(records)} records")

        # Step 2: Persist to Explore layer (raw)
        logger.info(f"[{run_id}] Step 2: Writing to explore layer")
        await persist_raw_data(
            db=db,
            run_id=run_id,
            source_id=source_id,
            dataset_name=dataset_name,
            records=records
        )

        # Step 3: Run PII detection
        logger.info(f"[{run_id}] Step 3: Running PII detection")
        pii_types = []
        pii_count = 0
        try:
            orchestrator = PipelineOrchestrator()
            pii_results = orchestrator._scan_pii(df)
            pii_count = pii_results.get("total_pii_fields", 0)
            pii_types = list(set(
                f["type"] for f in pii_results.get("findings", [])
            ))
            logger.info(f"[{run_id}] Found {pii_count} PII fields: {pii_types}")
        except Exception as e:
            logger.warning(f"[{run_id}] PII detection failed: {e}")

        # Step 4: Run quality checks
        logger.info(f"[{run_id}] Step 4: Running quality checks")
        quality_score = 0.0
        try:
            orchestrator = PipelineOrchestrator()
            quality_results = orchestrator._check_quality(df)
            quality_score = float(quality_results.get("overall_score", 0))
            logger.info(f"[{run_id}] Quality score: {quality_score:.1f}%")
        except Exception as e:
            logger.warning(f"[{run_id}] Quality check failed: {e}")

        # Step 5: Persist to Chart layer (validated)
        logger.info(f"[{run_id}] Step 5: Writing to chart layer")
        await persist_validated_data(
            db=db,
            run_id=run_id,
            source_id=source_id,
            dataset_name=dataset_name,
            records=records,
            quality_score=quality_score,
            pii_types=pii_types
        )

        # Step 6: Persist to Navigate layer (business-ready)
        logger.info(f"[{run_id}] Step 6: Writing to navigate layer (SCD Type 2)")
        await persist_business_data(
            db=db,
            run_id=run_id,
            source_id=source_id,
            dataset_name=dataset_name,
            records=records
        )

        # Step 7: Generate embeddings for RAG (optional)
        chunks_stored = 0
        if embed_for_rag and RAG_AVAILABLE:
            logger.info(f"[{run_id}] Step 7: Generating embeddings for RAG")
            try:
                embedding_service = get_embedding_service()
                chunks_stored = await embed_and_store(
                    db=db,
                    run_id=run_id,
                    source_id=source_id,
                    dataset_name=dataset_name,
                    records=records,
                    embedding_service=embedding_service
                )
                logger.info(f"[{run_id}] Stored {chunks_stored} embeddings")
            except Exception as e:
                logger.warning(f"[{run_id}] Embedding failed: {e}")

        # Step 8: Log audit trail
        logger.info(f"[{run_id}] Step 8: Logging to audit trail")
        await log_data_access(
            db=db,
            user_id="system",
            api_key=None,
            action="pipeline_run",
            resource_type="dataset",
            resource_id=dataset_name,
            records_accessed=len(records),
            data_accessed={
                "columns": list(df.columns),
                "pii_types": pii_types,
                "quality_score": quality_score,
                "embeddings_stored": chunks_stored
            }
        )

        # Update run status
        await save_pipeline_run(
            db=db,
            run_id=run_id,
            source_id=source_id,
            dataset_name=dataset_name,
            filename=filename,
            status="completed",
            record_count=len(records),
            quality_score=quality_score,
            pii_count=pii_count,
            results={
                "records": len(records),
                "pii_count": pii_count,
                "pii_types": pii_types,
                "quality_score": quality_score,
                "embeddings_stored": chunks_stored,
                "layers": ["explore", "chart", "navigate"]
            }
        )

        logger.info(f"[{run_id}] ✅ Persistent pipeline completed successfully!")

    except Exception as e:
        logger.error(f"[{run_id}] ❌ Pipeline failed: {e}")
        await save_pipeline_run(
            db=db,
            run_id=run_id,
            source_id=source_id,
            dataset_name=dataset_name,
            filename=filename,
            status="failed",
            error=str(e)
        )


@app.get("/pipeline/runs/db")
async def list_pipeline_runs_from_db(
    dataset_name: str | None = None,
    status: str | None = None,
    limit: int = 50
) -> dict[str, Any]:
    """
    List pipeline runs from database.

    Unlike /pipeline/runs, this returns persisted runs that survive restarts.
    """
    if not DB_AVAILABLE:
        return {
            "runs": [],
            "total": 0,
            "db_available": False,
            "message": "Database not available"
        }

    from app.core.database import get_pipeline_runs

    db = await get_database()
    runs = await get_pipeline_runs(db, dataset_name, status, limit)

    return {
        "runs": runs,
        "total": len(runs),
        "db_available": True
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
