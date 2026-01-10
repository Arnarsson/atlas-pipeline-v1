"""Pipeline API endpoints for Atlas Data Platform."""

from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel

from app.pipeline.core.orchestrator import PipelineOrchestrator

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

# In-memory storage for demo (replace with DB in production)
pipeline_runs: dict[str, dict[str, Any]] = {}


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


@router.post("/run", response_model=PipelineRunResponse)
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

    Args:
        file: CSV file to process
        dataset_name: Optional name for the dataset

    Returns:
        Run ID and status
    """
    # Validate file type
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    # Generate run ID
    run_id = str(uuid4())

    # Initialize run status
    pipeline_runs[run_id] = {
        "run_id": run_id,
        "status": "queued",
        "filename": file.filename,
        "dataset_name": dataset_name or file.filename.replace('.csv', ''),
        "current_step": "queued",
        "results": {},
        "error": None,
    }

    # Read file content
    content = await file.read()

    # Create orchestrator and run in background
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


@router.get("/status/{run_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(run_id: str) -> PipelineStatusResponse:
    """
    Check the status of a pipeline run.

    Args:
        run_id: The pipeline run ID

    Returns:
        Current status and results
    """
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


@router.get("/runs")
async def list_pipeline_runs() -> list[dict[str, Any]]:
    """
    List all pipeline runs.

    Returns:
        List of all pipeline runs with their status
    """
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


@router.delete("/runs/{run_id}")
async def delete_pipeline_run(run_id: str) -> dict[str, str]:
    """
    Delete a pipeline run.

    Args:
        run_id: The pipeline run ID

    Returns:
        Success message
    """
    if run_id not in pipeline_runs:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    del pipeline_runs[run_id]

    return {"message": f"Pipeline run {run_id} deleted successfully"}
