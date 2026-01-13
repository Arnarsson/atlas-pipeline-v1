"""
AtlasIntelligence Connectors API - Unified data connector platform.

Provides access to:
- 13+ MCP Connectors (lightweight, fast)
- 300+ PyAirbyte Sources (full Airbyte protocol)
- N8N Workflow integration
"""

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.connectors.airbyte.pyairbyte_executor import (
    PyAirbyteExecutor,
    PyAirbyteConfig,
    SyncMode,
    get_pyairbyte_executor,
)

router = APIRouter(prefix="/atlas-intelligence", tags=["AtlasIntelligence Connectors"])


# ============================================================================
# Pydantic Models
# ============================================================================


class ConnectorInfo(BaseModel):
    """Information about an available connector."""
    id: str
    name: str
    description: str
    category: str
    type: str  # "mcp", "pyairbyte", "n8n"
    status: str = "available"


class EntityInfo(BaseModel):
    """Information about a connector entity/stream."""
    name: str
    actions: List[str]
    description: Optional[str] = None


class ExecuteRequest(BaseModel):
    """Request to execute a connector operation."""
    connector_id: str
    entity: str
    action: str
    params: Dict[str, Any] = Field(default_factory=dict)


class PyAirbyteConfigRequest(BaseModel):
    """Request to configure a PyAirbyte source."""
    source_name: str = Field(..., description="Airbyte source name (e.g., 'source-postgres')")
    config: Dict[str, Any] = Field(..., description="Source configuration")
    streams: List[str] = Field(default_factory=list, description="Streams to sync")


class PyAirbyteReadRequest(BaseModel):
    """Request to read from a PyAirbyte stream."""
    source_name: str
    stream_name: str
    sync_mode: str = "full_refresh"
    state: Optional[Dict[str, Any]] = None


# ============================================================================
# MCP Connector Registry (Lightweight connectors)
# ============================================================================

MCP_CONNECTORS = {
    "github": {
        "id": "github",
        "name": "GitHub",
        "description": "Access repositories, issues, PRs, and more",
        "category": "development",
        "type": "mcp",
        "entities": ["repositories", "issues", "pull_requests", "commits", "users"]
    },
    "stripe": {
        "id": "stripe",
        "name": "Stripe",
        "description": "Payment processing and subscription data",
        "category": "ecommerce",
        "type": "mcp",
        "entities": ["customers", "subscriptions", "invoices", "payments", "products"]
    },
    "hubspot": {
        "id": "hubspot",
        "name": "HubSpot",
        "description": "CRM, marketing, and sales data",
        "category": "crm",
        "type": "mcp",
        "entities": ["contacts", "companies", "deals", "tickets", "emails"]
    },
    "salesforce": {
        "id": "salesforce",
        "name": "Salesforce",
        "description": "Enterprise CRM data",
        "category": "crm",
        "type": "mcp",
        "entities": ["accounts", "contacts", "opportunities", "leads", "cases"]
    },
    "jira": {
        "id": "jira",
        "name": "Jira",
        "description": "Issue tracking and project management",
        "category": "project",
        "type": "mcp",
        "entities": ["issues", "projects", "sprints", "boards", "users"]
    },
    "linear": {
        "id": "linear",
        "name": "Linear",
        "description": "Modern issue tracking",
        "category": "project",
        "type": "mcp",
        "entities": ["issues", "projects", "teams", "cycles", "labels"]
    },
    "intercom": {
        "id": "intercom",
        "name": "Intercom",
        "description": "Customer messaging platform",
        "category": "communication",
        "type": "mcp",
        "entities": ["contacts", "conversations", "companies", "tags", "segments"]
    },
    "google-drive": {
        "id": "google-drive",
        "name": "Google Drive",
        "description": "File storage and collaboration",
        "category": "storage",
        "type": "mcp",
        "entities": ["files", "folders", "permissions", "comments"]
    },
    "asana": {
        "id": "asana",
        "name": "Asana",
        "description": "Work management platform",
        "category": "project",
        "type": "mcp",
        "entities": ["tasks", "projects", "sections", "tags", "users"]
    },
    "zendesk": {
        "id": "zendesk",
        "name": "Zendesk",
        "description": "Customer service platform",
        "category": "communication",
        "type": "mcp",
        "entities": ["tickets", "users", "organizations", "groups", "macros"]
    },
    "greenhouse": {
        "id": "greenhouse",
        "name": "Greenhouse",
        "description": "Recruiting and hiring",
        "category": "hr",
        "type": "mcp",
        "entities": ["candidates", "applications", "jobs", "offers", "interviews"]
    },
    "gong": {
        "id": "gong",
        "name": "Gong",
        "description": "Revenue intelligence platform",
        "category": "sales",
        "type": "mcp",
        "entities": ["calls", "emails", "deals", "users", "scorecards"]
    },
    "notion": {
        "id": "notion",
        "name": "Notion",
        "description": "All-in-one workspace",
        "category": "project",
        "type": "mcp",
        "entities": ["pages", "databases", "blocks", "users", "comments"]
    },
}

# Environment variable mappings for credentials
CREDENTIAL_ENV_VARS = {
    "github": "GITHUB_TOKEN",
    "stripe": "STRIPE_API_KEY",
    "hubspot": "HUBSPOT_API_KEY",
    "salesforce": "SALESFORCE_ACCESS_TOKEN",
    "jira": "JIRA_API_TOKEN",
    "linear": "LINEAR_API_KEY",
    "intercom": "INTERCOM_ACCESS_TOKEN",
    "google-drive": "GOOGLE_DRIVE_CREDENTIALS",
    "asana": "ASANA_ACCESS_TOKEN",
    "zendesk": "ZENDESK_API_TOKEN",
    "greenhouse": "GREENHOUSE_API_KEY",
    "gong": "GONG_ACCESS_KEY",
    "notion": "NOTION_API_KEY",
}


# ============================================================================
# Health & Status Endpoints
# ============================================================================


@router.get("/health")
async def get_health() -> Dict[str, Any]:
    """Get AtlasIntelligence platform health status."""
    executor = get_pyairbyte_executor()
    pyairbyte_health = executor.health_check()

    return {
        "status": "healthy",
        "platform": "AtlasIntelligence",
        "mcp_connectors": len(MCP_CONNECTORS),
        "pyairbyte_connectors": pyairbyte_health["total_available_connectors"],
        "pyairbyte_status": pyairbyte_health["status"],
        "total_connectors": len(MCP_CONNECTORS) + pyairbyte_health["total_available_connectors"],
        "message": f"Access to {len(MCP_CONNECTORS)} MCP + {pyairbyte_health['total_available_connectors']}+ PyAirbyte connectors"
    }


# ============================================================================
# MCP Connector Endpoints
# ============================================================================


@router.get("/connectors")
async def list_mcp_connectors() -> List[Dict[str, Any]]:
    """List all available MCP connectors."""
    connectors = []
    for connector_id, info in MCP_CONNECTORS.items():
        connectors.append({
            "id": info["id"],
            "description": info["description"],
            "type": info["type"],
            "category": info["category"],
            "path": None,
            "connector_name": info["name"]
        })
    return connectors


@router.get("/connectors/{connector_id}/entities")
async def get_connector_entities(connector_id: str) -> List[EntityInfo]:
    """Get available entities/streams for a connector."""
    if connector_id not in MCP_CONNECTORS:
        raise HTTPException(status_code=404, detail=f"Connector {connector_id} not found")

    connector = MCP_CONNECTORS[connector_id]
    entities = []

    for entity_name in connector.get("entities", []):
        entities.append(EntityInfo(
            name=entity_name,
            actions=["list", "get", "search"],
            description=f"{entity_name.replace('_', ' ').title()} from {connector['name']}"
        ))

    return entities


@router.post("/execute")
async def execute_mcp_operation(request: ExecuteRequest) -> Dict[str, Any]:
    """Execute an operation on an MCP connector."""
    if request.connector_id not in MCP_CONNECTORS:
        raise HTTPException(status_code=404, detail=f"Connector {request.connector_id} not found")

    connector = MCP_CONNECTORS[request.connector_id]

    # Check if credential is configured
    env_var = CREDENTIAL_ENV_VARS.get(request.connector_id)
    has_credential = bool(os.environ.get(env_var, "")) if env_var else False

    if not has_credential:
        return {
            "status": "error",
            "connector_id": request.connector_id,
            "entity": request.entity,
            "action": request.action,
            "error": f"Credentials not configured. Set {env_var} environment variable.",
            "message": "Configure API key to execute operations"
        }

    # Mock execution result (in production, would call actual MCP connector)
    return {
        "status": "success",
        "connector_id": request.connector_id,
        "connector_name": connector["name"],
        "entity": request.entity,
        "action": request.action,
        "params": request.params,
        "result": {
            "message": f"Operation {request.action} on {request.entity} executed successfully",
            "records": [],
            "count": 0
        }
    }


# ============================================================================
# Credential Management
# ============================================================================


@router.get("/credentials")
async def get_credentials_status() -> Dict[str, Dict[str, Any]]:
    """Get status of configured credentials for all connectors."""
    credentials = {}

    for connector_id, env_var in CREDENTIAL_ENV_VARS.items():
        value = os.environ.get(env_var, "")
        configured = bool(value)

        credentials[connector_id] = {
            "configured": configured,
            "env_var": env_var,
            "masked": f"{value[:4]}...{value[-4:]}" if len(value) > 8 else ("*" * len(value) if value else "not_set")
        }

    return credentials


@router.post("/credentials")
async def update_credential(data: Dict[str, str]) -> Dict[str, Any]:
    """Update a connector credential (sets environment variable for session)."""
    connector_id = data.get("connector_id")
    api_key = data.get("api_key")

    if not connector_id or not api_key:
        raise HTTPException(status_code=400, detail="connector_id and api_key required")

    if connector_id not in CREDENTIAL_ENV_VARS:
        raise HTTPException(status_code=404, detail=f"Unknown connector: {connector_id}")

    env_var = CREDENTIAL_ENV_VARS[connector_id]
    os.environ[env_var] = api_key

    return {
        "status": "success",
        "connector_id": connector_id,
        "env_var": env_var,
        "message": f"Credential set for {connector_id}"
    }


# ============================================================================
# PyAirbyte Endpoints (300+ Sources)
# ============================================================================


@router.get("/pyairbyte/health")
async def get_pyairbyte_health() -> Dict[str, Any]:
    """Get PyAirbyte integration health status."""
    executor = get_pyairbyte_executor()
    return executor.health_check()


@router.get("/pyairbyte/connectors")
async def list_pyairbyte_connectors(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search connectors")
) -> List[Dict[str, Any]]:
    """List all available PyAirbyte connectors (300+)."""
    executor = get_pyairbyte_executor()
    return executor.list_available_connectors(category=category, search=search)


@router.get("/pyairbyte/categories")
async def get_pyairbyte_categories() -> List[Dict[str, Any]]:
    """Get list of connector categories with counts."""
    executor = get_pyairbyte_executor()
    return executor.get_categories()


@router.get("/pyairbyte/connectors/{source_name}/spec")
async def get_connector_spec(source_name: str) -> Dict[str, Any]:
    """Get configuration specification for a connector."""
    executor = get_pyairbyte_executor()
    spec = executor.get_connector_spec(source_name)
    return {
        "source_name": source_name,
        "spec": spec
    }


@router.post("/pyairbyte/configure")
async def configure_pyairbyte_source(request: PyAirbyteConfigRequest) -> Dict[str, Any]:
    """Configure and validate a PyAirbyte source connector."""
    executor = get_pyairbyte_executor()
    result = await executor.configure_source(
        source_name=request.source_name,
        config=request.config,
        streams=request.streams if request.streams else None
    )
    return result


@router.get("/pyairbyte/sources/{source_name}/streams")
async def discover_streams(source_name: str) -> Dict[str, Any]:
    """Discover available streams from a configured source."""
    executor = get_pyairbyte_executor()
    catalog = await executor.discover_streams(source_name)
    return {
        "source_name": source_name,
        "streams": [
            {
                "name": s.name,
                "supported_sync_modes": s.supported_sync_modes,
                "source_defined_cursor": s.source_defined_cursor
            }
            for s in catalog.streams
        ],
        "total_streams": len(catalog.streams)
    }


@router.post("/pyairbyte/read")
async def read_pyairbyte_stream(request: PyAirbyteReadRequest) -> Dict[str, Any]:
    """Read data from a PyAirbyte stream."""
    executor = get_pyairbyte_executor()

    sync_mode = SyncMode.INCREMENTAL if request.sync_mode == "incremental" else SyncMode.FULL_REFRESH

    result = await executor.read_stream(
        source_name=request.source_name,
        stream_name=request.stream_name,
        sync_mode=sync_mode,
        state=request.state
    )
    return result


# ============================================================================
# Unified Search Across All Connectors
# ============================================================================


@router.get("/search")
async def search_all_connectors(
    query: str = Query(..., description="Search query"),
    type: Optional[str] = Query(None, description="Filter by type: mcp, pyairbyte")
) -> List[Dict[str, Any]]:
    """Search across all available connectors (MCP + PyAirbyte)."""
    results = []
    query_lower = query.lower()

    # Search MCP connectors
    if type is None or type == "mcp":
        for connector_id, info in MCP_CONNECTORS.items():
            if query_lower in info["name"].lower() or query_lower in info["description"].lower():
                results.append({
                    "id": connector_id,
                    "name": info["name"],
                    "description": info["description"],
                    "category": info["category"],
                    "type": "mcp",
                    "match_score": 1.0 if query_lower in info["name"].lower() else 0.5
                })

    # Search PyAirbyte connectors
    if type is None or type == "pyairbyte":
        executor = get_pyairbyte_executor()
        pyairbyte_results = executor.list_available_connectors(search=query)
        for connector in pyairbyte_results:
            results.append({
                "id": connector["id"],
                "name": connector["name"],
                "description": f"PyAirbyte: {connector['name']} connector",
                "category": connector["category"],
                "type": "pyairbyte",
                "match_score": 0.8
            })

    # Sort by match score
    results.sort(key=lambda x: x["match_score"], reverse=True)

    return results[:50]  # Limit results


# ============================================================================
# Statistics
# ============================================================================


@router.get("/stats")
async def get_platform_stats() -> Dict[str, Any]:
    """Get platform statistics."""
    executor = get_pyairbyte_executor()
    pyairbyte_health = executor.health_check()
    categories = executor.get_categories()

    # Count configured credentials
    configured_count = sum(
        1 for env_var in CREDENTIAL_ENV_VARS.values()
        if os.environ.get(env_var, "")
    )

    return {
        "platform": "AtlasIntelligence",
        "mcp_connectors": {
            "total": len(MCP_CONNECTORS),
            "configured": configured_count,
            "categories": list(set(c["category"] for c in MCP_CONNECTORS.values()))
        },
        "pyairbyte_connectors": {
            "total": pyairbyte_health["total_available_connectors"],
            "installed": pyairbyte_health.get("installed_connectors", 0),
            "configured": pyairbyte_health.get("configured_sources", 0),
            "categories": categories
        },
        "total_available": len(MCP_CONNECTORS) + pyairbyte_health["total_available_connectors"],
        "pyairbyte_ready": pyairbyte_health["pyairbyte_installed"]
    }


# ============================================================================
# State Management (Incremental Syncs)
# ============================================================================


from app.connectors.airbyte.state_manager import get_state_manager


class CreateStateRequest(BaseModel):
    """Request to create a new state for a source."""
    source_name: str
    source_id: str
    streams: List[str] = Field(default_factory=list)
    global_state: Dict[str, Any] = Field(default_factory=dict)


class UpdateStreamStateRequest(BaseModel):
    """Request to update stream state."""
    stream_name: str
    cursor_field: Optional[str] = None
    cursor_value: Optional[Any] = None
    sync_mode: str = "incremental"
    records_synced: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.get("/state/sources")
async def list_source_states() -> List[Dict[str, Any]]:
    """List all sources with saved state."""
    manager = get_state_manager()
    return manager.list_sources()


@router.post("/state/sources")
async def create_source_state(request: CreateStateRequest) -> Dict[str, Any]:
    """Create a new state for a source connector."""
    manager = get_state_manager()
    state = manager.create_state(
        source_name=request.source_name,
        source_id=request.source_id,
        streams=request.streams if request.streams else None,
        global_state=request.global_state if request.global_state else None
    )
    return {
        "status": "created",
        "source_id": state.source_id,
        "source_name": state.source_name,
        "stream_count": len(state.streams),
        "message": f"State created for {request.source_name}"
    }


@router.get("/state/sources/{source_id}")
async def get_source_state(source_id: str) -> Dict[str, Any]:
    """Get complete state for a source."""
    manager = get_state_manager()
    state = manager.get_state(source_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"State not found for source {source_id}")
    return state.to_dict()


@router.get("/state/sources/{source_id}/summary")
async def get_sync_summary(source_id: str) -> Dict[str, Any]:
    """Get sync summary for a source."""
    manager = get_state_manager()
    summary = manager.get_sync_summary(source_id)
    if not summary:
        raise HTTPException(status_code=404, detail=f"State not found for source {source_id}")
    return summary


@router.put("/state/sources/{source_id}/streams")
async def update_stream_state(
    source_id: str,
    request: UpdateStreamStateRequest
) -> Dict[str, Any]:
    """Update state for a specific stream after sync."""
    manager = get_state_manager()
    stream_state = manager.update_stream_state(
        source_id=source_id,
        stream_name=request.stream_name,
        cursor_field=request.cursor_field,
        cursor_value=request.cursor_value,
        sync_mode=request.sync_mode,
        records_synced=request.records_synced,
        metadata=request.metadata if request.metadata else None
    )
    if not stream_state:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    return {
        "status": "updated",
        "source_id": source_id,
        "stream": stream_state.to_dict()
    }


@router.get("/state/sources/{source_id}/streams/{stream_name}/cursor")
async def get_cursor_value(source_id: str, stream_name: str) -> Dict[str, Any]:
    """Get current cursor value for incremental sync."""
    manager = get_state_manager()
    cursor_value = manager.get_cursor_value(source_id, stream_name)
    return {
        "source_id": source_id,
        "stream_name": stream_name,
        "cursor_value": cursor_value,
        "has_cursor": cursor_value is not None
    }


@router.post("/state/sources/{source_id}/streams/{stream_name}/reset")
async def reset_stream_state(source_id: str, stream_name: str) -> Dict[str, Any]:
    """Reset state for a stream (force full refresh on next sync)."""
    manager = get_state_manager()
    success = manager.reset_stream_state(source_id, stream_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Source or stream not found")
    return {
        "status": "reset",
        "source_id": source_id,
        "stream_name": stream_name,
        "message": f"State reset for stream {stream_name}"
    }


@router.post("/state/sources/{source_id}/reset")
async def reset_source_state(source_id: str) -> Dict[str, Any]:
    """Reset all state for a source (force full refresh on all streams)."""
    manager = get_state_manager()
    success = manager.reset_source_state(source_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    return {
        "status": "reset",
        "source_id": source_id,
        "message": "All stream states reset"
    }


@router.delete("/state/sources/{source_id}")
async def delete_source_state(source_id: str) -> Dict[str, Any]:
    """Delete all state for a source."""
    manager = get_state_manager()
    success = manager.delete_state(source_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    return {
        "status": "deleted",
        "source_id": source_id,
        "message": "State deleted"
    }


@router.get("/state/sources/{source_id}/export")
async def export_state(source_id: str) -> Dict[str, Any]:
    """Export complete state for backup/migration."""
    manager = get_state_manager()
    state_data = manager.export_state(source_id)
    if not state_data:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    return {
        "status": "exported",
        "source_id": source_id,
        "state": state_data
    }


@router.post("/state/import")
async def import_state(state_data: Dict[str, Any]) -> Dict[str, Any]:
    """Import state from backup/migration."""
    manager = get_state_manager()
    state = manager.import_state(state_data)
    return {
        "status": "imported",
        "source_id": state.source_id,
        "source_name": state.source_name,
        "stream_count": len(state.streams),
        "message": "State imported successfully"
    }


# ============================================================================
# Sync Jobs & Scheduling
# ============================================================================


from app.connectors.airbyte.sync_scheduler import (
    get_sync_scheduler,
    SyncMode as SchedulerSyncMode,
)


class CreateSyncJobRequest(BaseModel):
    """Request to create a sync job."""
    source_id: str
    source_name: str
    streams: List[str]
    sync_mode: str = "full_refresh"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreateScheduleRequest(BaseModel):
    """Request to create a scheduled sync."""
    source_id: str
    source_name: str
    streams: List[str]
    cron_expression: str = Field(..., description="Cron expression (e.g., '0 * * * *' for hourly)")
    sync_mode: str = "incremental"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UpdateScheduleRequest(BaseModel):
    """Request to update a schedule."""
    enabled: Optional[bool] = None
    cron_expression: Optional[str] = None
    streams: Optional[List[str]] = None


@router.get("/sync/stats")
async def get_sync_stats() -> Dict[str, Any]:
    """Get sync scheduler statistics."""
    scheduler = get_sync_scheduler()
    return scheduler.get_stats()


@router.post("/sync/jobs")
async def create_sync_job(request: CreateSyncJobRequest) -> Dict[str, Any]:
    """Create a new sync job."""
    scheduler = get_sync_scheduler()

    sync_mode = (
        SchedulerSyncMode.INCREMENTAL
        if request.sync_mode == "incremental"
        else SchedulerSyncMode.FULL_REFRESH
    )

    job = scheduler.create_sync_job(
        source_id=request.source_id,
        source_name=request.source_name,
        streams=request.streams,
        sync_mode=sync_mode,
        metadata=request.metadata
    )

    return {
        "status": "created",
        "job": job.to_dict()
    }


@router.post("/sync/jobs/{job_id}/run")
async def run_sync_job(job_id: str) -> Dict[str, Any]:
    """Run a sync job."""
    scheduler = get_sync_scheduler()

    try:
        job = await scheduler.run_sync_job(job_id)
        return {
            "status": "completed" if job.status.value == "completed" else job.status.value,
            "job": job.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sync/jobs/{job_id}")
async def get_sync_job(job_id: str) -> Dict[str, Any]:
    """Get a sync job by ID."""
    scheduler = get_sync_scheduler()
    job = scheduler.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return job.to_dict()


@router.post("/sync/jobs/{job_id}/cancel")
async def cancel_sync_job(job_id: str) -> Dict[str, Any]:
    """Cancel a sync job."""
    scheduler = get_sync_scheduler()

    if scheduler.cancel_job(job_id):
        return {"status": "cancelled", "job_id": job_id}
    else:
        raise HTTPException(status_code=400, detail=f"Cannot cancel job {job_id}")


@router.get("/sync/jobs")
async def list_sync_jobs(
    source_id: Optional[str] = Query(None, description="Filter by source"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, description="Maximum jobs to return")
) -> List[Dict[str, Any]]:
    """List sync jobs and history."""
    scheduler = get_sync_scheduler()

    # Get running jobs
    running = scheduler.get_running_jobs()

    # Get history
    history = scheduler.get_job_history(source_id=source_id, limit=limit)

    # Combine and filter
    all_jobs = running + history

    if status:
        all_jobs = [j for j in all_jobs if j.status.value == status]

    return [j.to_dict() for j in all_jobs[:limit]]


@router.get("/sync/running")
async def get_running_jobs() -> List[Dict[str, Any]]:
    """Get all currently running sync jobs."""
    scheduler = get_sync_scheduler()
    jobs = scheduler.get_running_jobs()
    return [j.to_dict() for j in jobs]


# ============================================================================
# Scheduled Syncs
# ============================================================================


@router.post("/sync/schedules")
async def create_schedule(request: CreateScheduleRequest) -> Dict[str, Any]:
    """Create a scheduled recurring sync."""
    scheduler = get_sync_scheduler()

    sync_mode = (
        SchedulerSyncMode.INCREMENTAL
        if request.sync_mode == "incremental"
        else SchedulerSyncMode.FULL_REFRESH
    )

    schedule = scheduler.create_schedule(
        source_id=request.source_id,
        source_name=request.source_name,
        streams=request.streams,
        cron_expression=request.cron_expression,
        sync_mode=sync_mode,
        metadata=request.metadata
    )

    return {
        "status": "created",
        "schedule": schedule.to_dict()
    }


@router.get("/sync/schedules")
async def list_schedules(
    source_id: Optional[str] = Query(None, description="Filter by source")
) -> List[Dict[str, Any]]:
    """List all scheduled syncs."""
    scheduler = get_sync_scheduler()
    schedules = scheduler.list_schedules(source_id=source_id)
    return [s.to_dict() for s in schedules]


@router.get("/sync/schedules/{schedule_id}")
async def get_schedule(schedule_id: str) -> Dict[str, Any]:
    """Get a schedule by ID."""
    scheduler = get_sync_scheduler()
    schedule = scheduler.get_schedule(schedule_id)

    if not schedule:
        raise HTTPException(status_code=404, detail=f"Schedule {schedule_id} not found")

    return schedule.to_dict()


@router.put("/sync/schedules/{schedule_id}")
async def update_schedule(schedule_id: str, request: UpdateScheduleRequest) -> Dict[str, Any]:
    """Update a scheduled sync."""
    scheduler = get_sync_scheduler()

    schedule = scheduler.update_schedule(
        schedule_id=schedule_id,
        enabled=request.enabled,
        cron_expression=request.cron_expression,
        streams=request.streams
    )

    if not schedule:
        raise HTTPException(status_code=404, detail=f"Schedule {schedule_id} not found")

    return {
        "status": "updated",
        "schedule": schedule.to_dict()
    }


@router.delete("/sync/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str) -> Dict[str, Any]:
    """Delete a scheduled sync."""
    scheduler = get_sync_scheduler()

    if scheduler.delete_schedule(schedule_id):
        return {"status": "deleted", "schedule_id": schedule_id}
    else:
        raise HTTPException(status_code=404, detail=f"Schedule {schedule_id} not found")


@router.post("/sync/schedules/{schedule_id}/run")
async def trigger_scheduled_sync(schedule_id: str) -> Dict[str, Any]:
    """Manually trigger a scheduled sync."""
    scheduler = get_sync_scheduler()

    job = await scheduler.run_scheduled_sync(schedule_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Schedule {schedule_id} not found")

    return {
        "status": "triggered",
        "job": job.to_dict()
    }


# ============================================================================
# Docker-based Airbyte Execution (Production Mode)
# ============================================================================
# These endpoints use official Airbyte Docker images for connector execution.
# Requires Docker to be installed and running.

from app.connectors.airbyte import (
    # Registry
    list_connectors as list_docker_connectors,
    search_connectors as search_docker_connectors,
    get_connector_info,
    get_connector_count,
    get_category_counts,
    ConnectorCategory,
    # Docker execution
    AirbyteDockerExecutor,
    get_docker_executor,
    check_docker_available,
    pull_image,
    ExecutorConfig,
    # Adapter
    AirbyteSourceAdapter,
    create_airbyte_adapter,
)
from app.connectors.base import ConnectionConfig


class DockerConnectorConfigRequest(BaseModel):
    """Request to configure a Docker-based Airbyte connector."""
    connector_name: str = Field(..., description="Connector name (e.g., 'source-postgres')")
    config: Dict[str, Any] = Field(..., description="Connector configuration")
    source_name: Optional[str] = Field(None, description="Optional display name")


class DockerReadRequest(BaseModel):
    """Request to read data from a Docker-based connector."""
    connector_name: str
    config: Dict[str, Any]
    stream_name: str
    incremental: bool = False
    cursor_field: Optional[str] = None
    state: Optional[Dict[str, Any]] = None


@router.get("/docker/health")
async def get_docker_health() -> Dict[str, Any]:
    """Check if Docker is available for Airbyte connector execution."""
    is_available = await check_docker_available()

    return {
        "docker_available": is_available,
        "status": "healthy" if is_available else "docker_not_running",
        "message": "Docker is ready for Airbyte connector execution" if is_available
                   else "Docker is not available. Install and start Docker to use 100+ Airbyte connectors.",
        "total_connectors": get_connector_count(),
        "execution_mode": "docker"
    }


@router.get("/docker/connectors")
async def list_docker_airbyte_connectors(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search connectors by name")
) -> Dict[str, Any]:
    """List all available Docker-based Airbyte connectors (100+)."""
    if search:
        connectors = search_docker_connectors(search)
    elif category:
        try:
            cat = ConnectorCategory(category)
            connectors = list_docker_connectors(category=cat)
        except ValueError:
            connectors = list_docker_connectors()
    else:
        connectors = list_docker_connectors()

    return {
        "connectors": [
            {
                "id": c.name,
                "name": c.display_name,
                "category": c.category.value,
                "docker_image": c.docker_image,
                "supports_incremental": c.supports_incremental,
                "documentation_url": c.documentation_url,
                "type": "docker"
            }
            for c in connectors
        ],
        "total": len(connectors),
        "execution_mode": "docker"
    }


@router.get("/docker/connectors/{connector_name}")
async def get_docker_connector_info(connector_name: str) -> Dict[str, Any]:
    """Get detailed information about a Docker-based connector."""
    info = get_connector_info(connector_name)

    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Connector '{connector_name}' not found in registry"
        )

    return {
        "id": info.name,
        "name": info.display_name,
        "category": info.category.value,
        "docker_image": info.docker_image,
        "supports_incremental": info.supports_incremental,
        "supports_normalization": info.supports_normalization,
        "documentation_url": info.documentation_url,
        "type": "docker"
    }


@router.get("/docker/categories")
async def get_docker_connector_categories() -> Dict[str, Any]:
    """Get available connector categories with counts."""
    counts = get_category_counts()

    return {
        "categories": [
            {
                "id": cat,
                "name": cat.replace("_", " ").title(),
                "count": count
            }
            for cat, count in sorted(counts.items(), key=lambda x: -x[1])
        ],
        "total_connectors": get_connector_count()
    }


@router.post("/docker/connectors/{connector_name}/pull")
async def pull_connector_image(connector_name: str, force: bool = False) -> Dict[str, Any]:
    """Pull the Docker image for a connector."""
    info = get_connector_info(connector_name)

    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Connector '{connector_name}' not found"
        )

    # Check Docker availability first
    if not await check_docker_available():
        raise HTTPException(
            status_code=503,
            detail="Docker is not available. Please start Docker."
        )

    success = await pull_image(info.docker_image, force=force)

    return {
        "status": "pulled" if success else "failed",
        "connector_name": connector_name,
        "docker_image": info.docker_image,
        "message": f"Image {info.docker_image} pulled successfully" if success
                   else f"Failed to pull image {info.docker_image}"
    }


@router.get("/docker/connectors/{connector_name}/spec")
async def get_docker_connector_spec(connector_name: str) -> Dict[str, Any]:
    """Get the configuration specification for a connector via Docker SPEC command."""
    info = get_connector_info(connector_name)

    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Connector '{connector_name}' not found"
        )

    if not await check_docker_available():
        raise HTTPException(
            status_code=503,
            detail="Docker is not available"
        )

    try:
        executor = get_docker_executor()
        spec = await executor.spec(info.docker_image)

        return {
            "connector_name": connector_name,
            "docker_image": info.docker_image,
            "spec": {
                "documentation_url": spec.documentationUrl,
                "connection_specification": spec.connectionSpecification,
                "supports_incremental": spec.supportsIncremental,
                "supports_normalization": spec.supportsNormalization,
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get spec: {str(e)}"
        )


@router.post("/docker/check")
async def check_docker_connection(request: DockerConnectorConfigRequest) -> Dict[str, Any]:
    """Test a connection using Docker CHECK command."""
    info = get_connector_info(request.connector_name)

    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Connector '{request.connector_name}' not found"
        )

    if not await check_docker_available():
        raise HTTPException(
            status_code=503,
            detail="Docker is not available"
        )

    try:
        executor = get_docker_executor()
        status = await executor.check(info.docker_image, request.config)

        return {
            "status": status.status.value.lower(),
            "message": status.message,
            "connector_name": request.connector_name,
            "docker_image": info.docker_image,
            "success": status.status.value == "SUCCEEDED"
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": str(e),
            "connector_name": request.connector_name,
            "success": False
        }


@router.post("/docker/discover")
async def discover_docker_streams(request: DockerConnectorConfigRequest) -> Dict[str, Any]:
    """Discover available streams using Docker DISCOVER command."""
    info = get_connector_info(request.connector_name)

    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Connector '{request.connector_name}' not found"
        )

    if not await check_docker_available():
        raise HTTPException(
            status_code=503,
            detail="Docker is not available"
        )

    try:
        executor = get_docker_executor()
        catalog = await executor.discover(info.docker_image, request.config)

        return {
            "connector_name": request.connector_name,
            "streams": [
                {
                    "name": stream.name,
                    "namespace": stream.namespace,
                    "supported_sync_modes": [m.value for m in stream.supported_sync_modes],
                    "source_defined_cursor": stream.source_defined_cursor,
                    "default_cursor_field": stream.default_cursor_field,
                    "primary_key": stream.source_defined_primary_key,
                    "json_schema": stream.json_schema
                }
                for stream in catalog.streams
            ],
            "total_streams": len(catalog.streams)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Discovery failed: {str(e)}"
        )


@router.post("/docker/read")
async def read_docker_stream(request: DockerReadRequest) -> Dict[str, Any]:
    """Read data from a connector using Docker READ command."""
    if not await check_docker_available():
        raise HTTPException(
            status_code=503,
            detail="Docker is not available"
        )

    try:
        adapter = create_airbyte_adapter(
            request.connector_name,
            request.config,
            source_name=request.connector_name
        )

        # Set state if provided
        if request.state:
            adapter.set_state(request.stream_name, request.state)

        df = await adapter.get_data(
            table=request.stream_name,
            incremental=request.incremental,
            timestamp_column=request.cursor_field
        )

        # Get new state after sync
        new_state = adapter.get_state(request.stream_name)

        await adapter.close()

        return {
            "status": "success",
            "connector_name": request.connector_name,
            "stream_name": request.stream_name,
            "records_count": len(df),
            "columns": list(df.columns),
            "data": df.head(100).to_dict(orient="records"),  # Return first 100 records
            "state": new_state,
            "message": f"Read {len(df)} records from {request.stream_name}"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Read failed: {str(e)}"
        )


@router.get("/docker/stats")
async def get_docker_connector_stats() -> Dict[str, Any]:
    """Get statistics about Docker-based connectors."""
    is_docker_available = await check_docker_available()
    counts = get_category_counts()

    return {
        "docker_available": is_docker_available,
        "total_connectors": get_connector_count(),
        "categories": counts,
        "top_categories": sorted(
            [{"name": k, "count": v} for k, v in counts.items()],
            key=lambda x: -x["count"]
        )[:5],
        "execution_mode": "docker",
        "status": "ready" if is_docker_available else "docker_required"
    }
