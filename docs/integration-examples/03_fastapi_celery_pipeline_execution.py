"""
Atlas Pipeline Integration: FastAPI + Celery for Pipeline Execution
===================================================================

This example shows how to integrate:
1. FastAPI for REST API endpoints
2. Celery for asynchronous pipeline execution
3. Redis/RabbitMQ as message broker
4. PostgreSQL for result storage

WHY THIS INTEGRATION:
- FastAPI provides modern async API for triggering pipelines
- Celery handles long-running pipeline jobs asynchronously
- Users get immediate API response while pipeline runs in background
- Enables queuing, retries, scheduling, and distributed execution

DEPENDENCIES:
pip install fastapi celery redis uvicorn sqlalchemy psycopg2-binary pydantic
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid

# FastAPI for REST API
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Celery for async task execution
from celery import Celery, Task, states
from celery.result import AsyncResult

# Database
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

class AppConfig:
    """
    WHY: Centralized configuration for all components
    - DATABASE_URL: Where pipeline results are stored
    - CELERY_BROKER_URL: Message queue (Redis/RabbitMQ)
    - CELERY_RESULT_BACKEND: Where Celery stores task results
    """
    DATABASE_URL = "postgresql://user:password@localhost:5432/atlas_pipelines"
    CELERY_BROKER_URL = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/0"


# ============================================================================
# Database Models
# ============================================================================

Base = declarative_base()


class PipelineRunStatus(str, Enum):
    """
    WHY: Standardized status tracking across API and database
    - PENDING: Job queued but not started
    - RUNNING: Currently executing
    - SUCCESS: Completed successfully
    - FAILED: Completed with errors
    - CANCELLED: User cancelled the job
    """
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PipelineRun(Base):
    """
    WHY: Persistent storage of pipeline execution history
    - Enables status tracking across API restarts
    - Stores complete execution metadata
    - Supports auditing and compliance
    """
    __tablename__ = "pipeline_runs"

    run_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pipeline_name = Column(String, nullable=False, index=True)
    status = Column(SQLEnum(PipelineRunStatus), default=PipelineRunStatus.PENDING)

    # Task tracking
    celery_task_id = Column(String, nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Execution details
    input_params = Column(JSON, nullable=True)
    result_data = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)

    # Metrics
    rows_processed = Column(JSON, nullable=True)
    duration_seconds = Column(JSON, nullable=True)


# WHY: Create database engine and session factory
engine = create_engine(AppConfig.DATABASE_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def get_db():
    """
    WHY: Dependency injection for database sessions
    - FastAPI will automatically manage session lifecycle
    - Ensures proper cleanup even on errors
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Celery Application
# ============================================================================

# WHY: Initialize Celery with Redis as broker and backend
celery_app = Celery(
    "atlas_pipelines",
    broker=AppConfig.CELERY_BROKER_URL,
    backend=AppConfig.CELERY_RESULT_BACKEND
)

# WHY: Configure Celery for reliability and monitoring
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,  # Track when tasks actually start
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # Warning at 55 minutes
    task_acks_late=True,  # Only ack after task completes
    worker_prefetch_multiplier=1,  # Process one task at a time per worker
)


class AtlasPipelineTask(Task):
    """
    WHY: Custom Celery task base class for pipeline tasks
    - Automatic database updates on status changes
    - Standardized error handling
    - Metrics tracking
    """

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        logger.info(f"Task {task_id} succeeded")
        # Update database
        db = SessionLocal()
        try:
            run = db.query(PipelineRun).filter(
                PipelineRun.celery_task_id == task_id
            ).first()
            if run:
                run.status = PipelineRunStatus.SUCCESS
                run.completed_at = datetime.utcnow()
                run.result_data = retval
                run.duration_seconds = (
                    run.completed_at - run.started_at
                ).total_seconds() if run.started_at else None
                db.commit()
        finally:
            db.close()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        logger.error(f"Task {task_id} failed: {exc}")
        # Update database
        db = SessionLocal()
        try:
            run = db.query(PipelineRun).filter(
                PipelineRun.celery_task_id == task_id
            ).first()
            if run:
                run.status = PipelineRunStatus.FAILED
                run.completed_at = datetime.utcnow()
                run.error_message = str(exc)
                db.commit()
        finally:
            db.close()


# ============================================================================
# Celery Tasks (The Actual Pipeline Logic)
# ============================================================================

@celery_app.task(base=AtlasPipelineTask, name="atlas.pipeline.bronze_to_silver")
def run_bronze_to_silver_pipeline(
    run_id: str,
    table_name: str,
    **kwargs
) -> Dict[str, Any]:
    """
    WHY: Celery task that executes Bronze -> Silver transformation
    - Runs asynchronously in Celery worker
    - Updates database with progress
    - Returns metrics on completion

    Args:
        run_id: Unique pipeline run ID
        table_name: Table to transform
        **kwargs: Additional pipeline parameters

    Returns:
        Dict with execution results and metrics
    """
    logger.info(f"Starting Bronze->Silver pipeline for {table_name} (run: {run_id})")

    # Update run status to RUNNING
    db = SessionLocal()
    try:
        run = db.query(PipelineRun).filter(PipelineRun.run_id == run_id).first()
        if run:
            run.status = PipelineRunStatus.RUNNING
            run.started_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()

    # WHY: Simulate actual pipeline execution
    # In real implementation, this would:
    # 1. Read from Bronze layer
    # 2. Apply transformations
    # 3. Write to Silver layer
    # 4. Emit lineage events
    import time
    import pandas as pd

    start_time = datetime.utcnow()

    # Simulate data extraction
    logger.info(f"Extracting Bronze data for {table_name}...")
    time.sleep(2)  # Simulate I/O

    # Simulate transformation
    logger.info(f"Transforming to Silver...")
    time.sleep(3)  # Simulate processing

    # Simulate data loading
    logger.info(f"Loading Silver data...")
    time.sleep(1)  # Simulate I/O

    end_time = datetime.utcnow()

    # WHY: Return detailed metrics
    result = {
        "status": "SUCCESS",
        "table_name": table_name,
        "rows_processed": 1000,  # Would be actual count
        "duration_seconds": (end_time - start_time).total_seconds(),
        "layers": {
            "bronze": "s3://atlas-bronze/" + table_name,
            "silver": "s3://atlas-silver/" + table_name
        },
        "metadata": {
            "pipeline_version": "1.0.0",
            "transformations_applied": ["deduplicate", "standardize", "validate"]
        }
    }

    logger.info(f"Pipeline complete for {table_name}: {result['rows_processed']} rows")
    return result


@celery_app.task(base=AtlasPipelineTask, name="atlas.pipeline.silver_to_gold")
def run_silver_to_gold_pipeline(
    run_id: str,
    table_name: str,
    aggregations: Optional[List[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    WHY: Celery task for Silver -> Gold transformation
    - Business logic and aggregations
    - Feature engineering for AI
    - Final quality validation
    """
    logger.info(f"Starting Silver->Gold pipeline for {table_name} (run: {run_id})")

    db = SessionLocal()
    try:
        run = db.query(PipelineRun).filter(PipelineRun.run_id == run_id).first()
        if run:
            run.status = PipelineRunStatus.RUNNING
            run.started_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()

    import time
    start_time = datetime.utcnow()

    # Simulate aggregation and enrichment
    logger.info(f"Applying aggregations: {aggregations or ['default']}")
    time.sleep(4)

    end_time = datetime.utcnow()

    result = {
        "status": "SUCCESS",
        "table_name": table_name,
        "rows_processed": 500,  # Typically fewer after aggregation
        "duration_seconds": (end_time - start_time).total_seconds(),
        "layers": {
            "silver": "s3://atlas-silver/" + table_name,
            "gold": "s3://atlas-gold/" + table_name
        },
        "aggregations_applied": aggregations or ["default"],
        "ai_features_created": 15
    }

    logger.info(f"Gold pipeline complete: {result['ai_features_created']} features")
    return result


# ============================================================================
# Pydantic Models (API Request/Response schemas)
# ============================================================================

class PipelineRequest(BaseModel):
    """
    WHY: Validates API request for pipeline execution
    - Ensures required fields are present
    - Provides API documentation via FastAPI
    - Type validation for safety
    """
    pipeline_name: str = Field(..., description="Name of pipeline to execute")
    table_name: str = Field(..., description="Table to process")
    parameters: Optional[Dict[str, Any]] = Field(
        default={},
        description="Additional pipeline parameters"
    )

    class Config:
        schema_extra = {
            "example": {
                "pipeline_name": "bronze_to_silver",
                "table_name": "customers",
                "parameters": {"validate_pii": True}
            }
        }


class PipelineResponse(BaseModel):
    """API response after queueing pipeline"""
    run_id: str
    pipeline_name: str
    status: PipelineRunStatus
    celery_task_id: str
    created_at: datetime
    message: str


class PipelineStatusResponse(BaseModel):
    """API response for status queries"""
    run_id: str
    pipeline_name: str
    status: PipelineRunStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    result_data: Optional[Dict[str, Any]]
    error_message: Optional[str]


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Atlas Data Pipeline API",
    description="REST API for executing and monitoring Atlas data pipelines",
    version="1.0.0"
)


@app.post("/pipelines/execute", response_model=PipelineResponse)
async def execute_pipeline(
    request: PipelineRequest,
    db: Session = Depends(get_db)
) -> PipelineResponse:
    """
    WHY: Execute a data pipeline asynchronously
    - Immediately returns run_id (doesn't wait for completion)
    - Pipeline executes in Celery worker
    - Client polls /pipelines/{run_id} for status

    Returns:
        Pipeline run details with run_id for tracking
    """
    logger.info(f"Received request to execute {request.pipeline_name}")

    # WHY: Create database record BEFORE queuing Celery task
    run_id = str(uuid.uuid4())
    pipeline_run = PipelineRun(
        run_id=run_id,
        pipeline_name=request.pipeline_name,
        status=PipelineRunStatus.PENDING,
        input_params=request.parameters
    )
    db.add(pipeline_run)
    db.commit()

    # WHY: Queue Celery task based on pipeline name
    try:
        if request.pipeline_name == "bronze_to_silver":
            task = run_bronze_to_silver_pipeline.apply_async(
                kwargs={
                    "run_id": run_id,
                    "table_name": request.table_name,
                    **request.parameters
                }
            )
        elif request.pipeline_name == "silver_to_gold":
            task = run_silver_to_gold_pipeline.apply_async(
                kwargs={
                    "run_id": run_id,
                    "table_name": request.table_name,
                    **request.parameters
                }
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown pipeline: {request.pipeline_name}"
            )

        # WHY: Store Celery task ID for later status queries
        pipeline_run.celery_task_id = task.id
        db.commit()

        logger.info(f"Queued pipeline {request.pipeline_name} with task_id: {task.id}")

        return PipelineResponse(
            run_id=run_id,
            pipeline_name=request.pipeline_name,
            status=PipelineRunStatus.PENDING,
            celery_task_id=task.id,
            created_at=pipeline_run.created_at,
            message=f"Pipeline queued successfully. Use run_id to check status."
        )

    except Exception as e:
        logger.error(f"Failed to queue pipeline: {e}")
        pipeline_run.status = PipelineRunStatus.FAILED
        pipeline_run.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pipelines/{run_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    run_id: str,
    db: Session = Depends(get_db)
) -> PipelineStatusResponse:
    """
    WHY: Check status and results of a pipeline run
    - Returns current status (PENDING/RUNNING/SUCCESS/FAILED)
    - Includes results when complete
    - Enables polling for async completion

    Args:
        run_id: Pipeline run ID from /pipelines/execute

    Returns:
        Current status and results
    """
    logger.info(f"Status query for run: {run_id}")

    # WHY: Query database for run details
    pipeline_run = db.query(PipelineRun).filter(
        PipelineRun.run_id == run_id
    ).first()

    if not pipeline_run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    # WHY: If task is still running, check Celery for real-time status
    if pipeline_run.status in [PipelineRunStatus.PENDING, PipelineRunStatus.RUNNING]:
        if pipeline_run.celery_task_id:
            celery_result = AsyncResult(pipeline_run.celery_task_id, app=celery_app)

            # Update status from Celery if changed
            if celery_result.state == states.SUCCESS:
                pipeline_run.status = PipelineRunStatus.SUCCESS
                pipeline_run.completed_at = datetime.utcnow()
                db.commit()
            elif celery_result.state == states.FAILURE:
                pipeline_run.status = PipelineRunStatus.FAILED
                pipeline_run.error_message = str(celery_result.info)
                db.commit()

    return PipelineStatusResponse(
        run_id=pipeline_run.run_id,
        pipeline_name=pipeline_run.pipeline_name,
        status=pipeline_run.status,
        created_at=pipeline_run.created_at,
        started_at=pipeline_run.started_at,
        completed_at=pipeline_run.completed_at,
        duration_seconds=pipeline_run.duration_seconds,
        result_data=pipeline_run.result_data,
        error_message=pipeline_run.error_message
    )


@app.get("/pipelines", response_model=List[PipelineStatusResponse])
async def list_pipeline_runs(
    pipeline_name: Optional[str] = None,
    status: Optional[PipelineRunStatus] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
) -> List[PipelineStatusResponse]:
    """
    WHY: List recent pipeline runs with optional filtering
    - Enables monitoring dashboard
    - Filter by pipeline name or status
    - Paginated results

    Args:
        pipeline_name: Filter by specific pipeline (optional)
        status: Filter by status (optional)
        limit: Max results to return

    Returns:
        List of pipeline runs
    """
    query = db.query(PipelineRun)

    if pipeline_name:
        query = query.filter(PipelineRun.pipeline_name == pipeline_name)

    if status:
        query = query.filter(PipelineRun.status == status)

    runs = query.order_by(PipelineRun.created_at.desc()).limit(limit).all()

    return [
        PipelineStatusResponse(
            run_id=run.run_id,
            pipeline_name=run.pipeline_name,
            status=run.status,
            created_at=run.created_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            duration_seconds=run.duration_seconds,
            result_data=run.result_data,
            error_message=run.error_message
        )
        for run in runs
    ]


@app.delete("/pipelines/{run_id}/cancel")
async def cancel_pipeline(
    run_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    WHY: Cancel a running pipeline
    - Stops Celery task execution
    - Updates status to CANCELLED
    - Enables user control over long-running jobs
    """
    pipeline_run = db.query(PipelineRun).filter(
        PipelineRun.run_id == run_id
    ).first()

    if not pipeline_run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    if pipeline_run.status not in [PipelineRunStatus.PENDING, PipelineRunStatus.RUNNING]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel pipeline with status {pipeline_run.status}"
        )

    # WHY: Revoke Celery task
    if pipeline_run.celery_task_id:
        celery_app.control.revoke(pipeline_run.celery_task_id, terminate=True)

    pipeline_run.status = PipelineRunStatus.CANCELLED
    pipeline_run.completed_at = datetime.utcnow()
    db.commit()

    return {"message": f"Pipeline {run_id} cancelled successfully"}


# ============================================================================
# Example Usage / Testing
# ============================================================================

if __name__ == "__main__":
    """
    To run this example:

    1. Start Redis:
       docker run -d -p 6379:6379 redis

    2. Start PostgreSQL:
       docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres

    3. Start Celery worker:
       celery -A 03_fastapi_celery_pipeline_execution worker --loglevel=info

    4. Start FastAPI:
       uvicorn 03_fastapi_celery_pipeline_execution:app --reload

    5. Execute pipeline via API:
       curl -X POST http://localhost:8000/pipelines/execute \
         -H "Content-Type: application/json" \
         -d '{
           "pipeline_name": "bronze_to_silver",
           "table_name": "customers",
           "parameters": {"validate_pii": true}
         }'

    6. Check status:
       curl http://localhost:8000/pipelines/{run_id}
    """
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
