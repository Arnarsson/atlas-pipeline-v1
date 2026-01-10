"""Celery tasks for scheduled pipeline execution."""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from loguru import logger

from app.connectors.base import ConnectionConfig
from app.connectors.registry import ConnectorRegistry
from app.scheduler.celery_app import celery_app

# In-memory storage for connectors and runs
# TODO: Replace with database persistence in Week 5
CONNECTORS: Dict[str, Dict[str, Any]] = {}
SCHEDULED_RUNS: Dict[str, Dict[str, Any]] = {}


@celery_app.task(name="app.scheduler.tasks.run_connector_pipeline")
def run_connector_pipeline(
    connector_id: str,
    triggered_by: str = "schedule"
) -> Dict[str, Any]:
    """Execute pipeline for a single connector.

    Args:
        connector_id: UUID of the connector to run
        triggered_by: How this run was triggered (schedule, manual, api)

    Returns:
        Dictionary with run results

    Raises:
        ValueError: If connector not found
    """
    run_id = str(uuid4())
    started_at = datetime.utcnow()

    logger.info(f"Starting connector pipeline: {connector_id} (run_id={run_id})")

    # Record run start
    SCHEDULED_RUNS[run_id] = {
        "run_id": run_id,
        "connector_id": connector_id,
        "triggered_by": triggered_by,
        "started_at": started_at,
        "status": "running",
        "rows_processed": 0,
        "error_message": None,
    }

    try:
        # Get connector configuration
        if connector_id not in CONNECTORS:
            raise ValueError(f"Connector not found: {connector_id}")

        connector_config = CONNECTORS[connector_id]

        # Run async pipeline
        result = asyncio.run(_run_async_pipeline(connector_config))

        # Update run status
        completed_at = datetime.utcnow()
        duration_seconds = (completed_at - started_at).total_seconds()

        SCHEDULED_RUNS[run_id].update({
            "completed_at": completed_at,
            "status": "completed",
            "rows_processed": result["rows_processed"],
            "duration_seconds": duration_seconds,
            "metadata": result.get("metadata", {}),
        })

        # Update connector last sync
        CONNECTORS[connector_id]["last_sync_at"] = completed_at
        CONNECTORS[connector_id]["last_sync_status"] = "completed"

        logger.info(
            f"Connector pipeline completed: {connector_id} "
            f"({result['rows_processed']} rows in {duration_seconds:.2f}s)"
        )

        return SCHEDULED_RUNS[run_id]

    except Exception as e:
        logger.error(f"Connector pipeline failed: {connector_id} - {e}")

        completed_at = datetime.utcnow()
        duration_seconds = (completed_at - started_at).total_seconds()

        SCHEDULED_RUNS[run_id].update({
            "completed_at": completed_at,
            "status": "failed",
            "error_message": str(e),
            "duration_seconds": duration_seconds,
        })

        # Update connector status
        if connector_id in CONNECTORS:
            CONNECTORS[connector_id]["last_sync_at"] = completed_at
            CONNECTORS[connector_id]["last_sync_status"] = "failed"

        raise


async def _run_async_pipeline(connector_config: Dict[str, Any]) -> Dict[str, Any]:
    """Run async pipeline for a connector.

    Args:
        connector_config: Connector configuration dict

    Returns:
        Dictionary with pipeline results
    """
    # Build ConnectionConfig
    config = ConnectionConfig(**connector_config["config"])

    # Get connector class
    connector_class = ConnectorRegistry.get_connector(config.source_type)

    # Create connector instance
    async with connector_class(config) as connector:
        # Test connection
        await connector.test_connection()

        # Get data (use incremental if configured)
        incremental = connector_config.get("incremental", True)
        timestamp_column = connector_config.get("timestamp_column")
        table = connector_config.get("table")
        query = connector_config.get("query")

        df = await connector.get_data(
            query=query,
            table=table,
            incremental=incremental,
            timestamp_column=timestamp_column,
        )

        # TODO: Process data through Explore → Chart pipeline
        # For now, just return row count
        rows_processed = len(df)

        return {
            "rows_processed": rows_processed,
            "metadata": {
                "columns": list(df.columns) if not df.empty else [],
                "incremental": incremental,
            }
        }


@celery_app.task(name="app.scheduler.tasks.sync_all_scheduled_sources")
def sync_all_scheduled_sources() -> Dict[str, Any]:
    """Run all enabled connectors that are scheduled.

    Returns:
        Dictionary with sync results
    """
    logger.info("Starting scheduled sync for all enabled connectors")

    results = {
        "total_connectors": 0,
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "run_ids": [],
    }

    for connector_id, connector in CONNECTORS.items():
        results["total_connectors"] += 1

        # Skip if not enabled
        if not connector.get("enabled", True):
            logger.info(f"Skipping disabled connector: {connector_id}")
            results["skipped"] += 1
            continue

        # Skip if no schedule
        if not connector.get("schedule_cron"):
            logger.info(f"Skipping connector without schedule: {connector_id}")
            results["skipped"] += 1
            continue

        try:
            # Queue connector pipeline
            task = run_connector_pipeline.delay(connector_id, triggered_by="schedule")
            results["run_ids"].append(task.id)
            results["successful"] += 1
            logger.info(f"Queued connector: {connector_id} (task_id={task.id})")

        except Exception as e:
            logger.error(f"Failed to queue connector {connector_id}: {e}")
            results["failed"] += 1

    logger.info(
        f"Scheduled sync completed: {results['successful']} queued, "
        f"{results['failed']} failed, {results['skipped']} skipped"
    )

    return results


@celery_app.task(name="app.scheduler.tasks.test_connector_health")
def test_connector_health() -> Dict[str, Any]:
    """Test health of all connectors.

    Returns:
        Dictionary with health check results
    """
    logger.info("Starting connector health checks")

    results = {
        "total_connectors": 0,
        "healthy": 0,
        "unhealthy": 0,
        "details": {},
    }

    for connector_id, connector in CONNECTORS.items():
        results["total_connectors"] += 1

        # Skip if not enabled
        if not connector.get("enabled", True):
            continue

        try:
            # Run async health check
            is_healthy = asyncio.run(_test_connector_async(connector))

            if is_healthy:
                results["healthy"] += 1
                results["details"][connector_id] = "healthy"
            else:
                results["unhealthy"] += 1
                results["details"][connector_id] = "unhealthy"

        except Exception as e:
            logger.error(f"Health check failed for {connector_id}: {e}")
            results["unhealthy"] += 1
            results["details"][connector_id] = f"error: {str(e)}"

    logger.info(
        f"Health check completed: {results['healthy']} healthy, "
        f"{results['unhealthy']} unhealthy"
    )

    return results


async def _test_connector_async(connector_config: Dict[str, Any]) -> bool:
    """Test connector health asynchronously.

    Args:
        connector_config: Connector configuration dict

    Returns:
        True if healthy, False otherwise
    """
    try:
        # Build ConnectionConfig
        config = ConnectionConfig(**connector_config["config"])

        # Get connector class
        connector_class = ConnectorRegistry.get_connector(config.source_type)

        # Create connector and test
        async with connector_class(config) as connector:
            return await connector.test_connection()

    except Exception as e:
        logger.error(f"Connector health check failed: {e}")
        return False


# Helper functions for connector management
def register_connector(connector_data: Dict[str, Any]) -> str:
    """Register a new connector.

    Args:
        connector_data: Connector configuration

    Returns:
        Connector ID
    """
    connector_id = str(uuid4())
    connector_data["connector_id"] = connector_id
    connector_data["created_at"] = datetime.utcnow()
    connector_data["updated_at"] = datetime.utcnow()
    CONNECTORS[connector_id] = connector_data
    logger.info(f"Registered connector: {connector_id}")
    return connector_id


def get_connector(connector_id: str) -> Optional[Dict[str, Any]]:
    """Get connector by ID.

    Args:
        connector_id: Connector UUID

    Returns:
        Connector data or None
    """
    return CONNECTORS.get(connector_id)


def list_connectors() -> list[Dict[str, Any]]:
    """List all connectors.

    Returns:
        List of connector configurations
    """
    return list(CONNECTORS.values())


def update_connector(connector_id: str, updates: Dict[str, Any]) -> bool:
    """Update connector configuration.

    Args:
        connector_id: Connector UUID
        updates: Fields to update

    Returns:
        True if updated, False if not found
    """
    if connector_id not in CONNECTORS:
        return False

    CONNECTORS[connector_id].update(updates)
    CONNECTORS[connector_id]["updated_at"] = datetime.utcnow()
    logger.info(f"Updated connector: {connector_id}")
    return True


def delete_connector(connector_id: str) -> bool:
    """Delete connector.

    Args:
        connector_id: Connector UUID

    Returns:
        True if deleted, False if not found
    """
    if connector_id not in CONNECTORS:
        return False

    del CONNECTORS[connector_id]
    logger.info(f"Deleted connector: {connector_id}")
    return True


def get_run_history(connector_id: Optional[str] = None) -> list[Dict[str, Any]]:
    """Get run history for connectors.

    Args:
        connector_id: Optional connector ID to filter by

    Returns:
        List of run records
    """
    if connector_id:
        return [
            run for run in SCHEDULED_RUNS.values()
            if run["connector_id"] == connector_id
        ]
    else:
        return list(SCHEDULED_RUNS.values())
