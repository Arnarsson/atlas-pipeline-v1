"""Quality and compliance API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.routes.pipeline import pipeline_runs

router = APIRouter(prefix="/quality", tags=["quality"])


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


@router.get("/metrics/{run_id}", response_model=QualityMetricsResponse)
async def get_quality_metrics(run_id: str) -> QualityMetricsResponse:
    """
    Get data quality metrics for a pipeline run.

    Args:
        run_id: The pipeline run ID

    Returns:
        Quality scores and details
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


@router.get("/pii-report/{run_id}", response_model=PIIReportResponse)
async def get_pii_report(run_id: str) -> PIIReportResponse:
    """
    Get PII detection report for a pipeline run.

    Args:
        run_id: The pipeline run ID

    Returns:
        PII findings and details
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


@router.get("/compliance/{run_id}")
async def get_compliance_report(run_id: str) -> dict[str, Any]:
    """
    Get compliance report for a pipeline run.

    Combines quality and PII data into a compliance overview.

    Args:
        run_id: The pipeline run ID

    Returns:
        Compliance status and recommendations
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
    pii_results = results.get("pii", {})

    # Determine compliance status
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
