"""Quality and compliance API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.routes.pipeline import pipeline_runs

router = APIRouter(prefix="/quality", tags=["quality"])

# Module load indicator
print("=" * 80)
print("QUALITY.PY MODULE LOADED - TRANSFORMERS ARE ACTIVE")
print("=" * 80)


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


# Transformer functions to align backend responses with frontend TypeScript interfaces
def transform_quality_metrics(quality_results: dict, run_id: str) -> dict:
    """
    Transform backend quality results to match frontend QualityMetrics interface.

    Frontend expects:
    - dimensions: { completeness: {score, threshold, passed, details}, ... } for 6 dimensions
    - column_metrics: Record<string, ColumnMetrics>
    """
    return {
        "run_id": run_id,
        "overall_score": quality_results.get("overall_score", 0.0),
        "dimensions": {
            "completeness": {
                "score": quality_results.get("completeness_score", 0.0),
                "threshold": 0.95,
                "passed": quality_results.get("completeness_score", 0.0) >= 0.95,
                "details": quality_results.get("details", {}).get("completeness", {})
            },
            "uniqueness": {
                "score": quality_results.get("uniqueness_score", 0.0),
                "threshold": 0.98,
                "passed": quality_results.get("uniqueness_score", 0.0) >= 0.98,
                "details": quality_results.get("details", {}).get("uniqueness", {})
            },
            "validity": {
                "score": quality_results.get("validity_score", 0.0),
                "threshold": 0.90,
                "passed": quality_results.get("validity_score", 0.0) >= 0.90,
                "details": quality_results.get("details", {}).get("validity", {})
            },
            "consistency": {
                "score": quality_results.get("consistency_score", 0.0),
                "threshold": 0.90,
                "passed": quality_results.get("consistency_score", 0.0) >= 0.90,
                "details": quality_results.get("details", {}).get("consistency", {})
            },
            "accuracy": {
                "score": quality_results.get("accuracy_score", 0.0),
                "threshold": 0.90,
                "passed": quality_results.get("accuracy_score", 0.0) >= 0.90,
                "details": quality_results.get("details", {}).get("accuracy", {})
            },
            "timeliness": {
                "score": quality_results.get("timeliness_score", 0.0),
                "threshold": 0.80,
                "passed": quality_results.get("timeliness_score", 0.0) >= 0.80,
                "details": quality_results.get("details", {}).get("timeliness", {})
            }
        },
        "column_metrics": extract_column_metrics(quality_results.get("details", {}))
    }


def extract_column_metrics(details: dict) -> dict:
    """
    Extract column-level metrics from details dict.

    Frontend expects: Record<string, ColumnMetrics> where ColumnMetrics has:
    - completeness: number
    - uniqueness: number
    - validity: number
    - data_type: string
    - null_count: number
    - unique_count: number
    """
    column_details = details.get("all_dimensions", {})
    column_metrics = {}

    for dimension in ["completeness", "uniqueness", "validity"]:
        dim_data = column_details.get(dimension, {}).get("details", {})
        if f"column_{dimension}" in dim_data:
            for col_name, col_data in dim_data[f"column_{dimension}"].items():
                if col_name not in column_metrics:
                    column_metrics[col_name] = {
                        "completeness": 1.0,
                        "uniqueness": 1.0,
                        "validity": 1.0,
                        "data_type": "unknown",
                        "null_count": 0,
                        "unique_count": 0
                    }

                if dimension == "completeness":
                    column_metrics[col_name]["completeness"] = col_data.get("completeness", 1.0)
                    column_metrics[col_name]["null_count"] = col_data.get("missing_count", 0)
                elif dimension == "uniqueness":
                    column_metrics[col_name]["uniqueness"] = col_data.get("uniqueness", 1.0)
                    column_metrics[col_name]["unique_count"] = col_data.get("unique_count", 0)
                elif dimension == "validity":
                    column_metrics[col_name]["validity"] = col_data.get("validity", 1.0)

    return column_metrics


def transform_pii_report(pii_results: dict, run_id: str, dataset_name: str) -> dict:
    """
    Transform backend PII results to match frontend PIIReport interface.

    Frontend expects:
    - total_detections: number
    - detections_by_type: Record<string, number>
    - detections: Array of {entity_type, location: {row, column}, confidence, matched_text, start, end}
    - compliance_status: 'compliant' | 'warning' | 'violation'
    - recommendations: string[]
    """
    findings = pii_results.get("findings", [])

    # Build detections_by_type
    detections_by_type = {}
    for finding in findings:
        entity_type = finding.get("type", "UNKNOWN")
        detections_by_type[entity_type] = detections_by_type.get(entity_type, 0) + finding.get("match_count", 0)

    # Build individual detections with location structure
    detections = []
    for finding in findings:
        column = finding.get("column", "")
        entity_type = finding.get("type", "UNKNOWN")
        sample_values = finding.get("sample_values", [])

        # Create a detection for each sample (up to 3 per type)
        for idx, value in enumerate(sample_values[:3]):
            detections.append({
                "entity_type": entity_type,
                "location": {
                    "row": idx,  # Approximate row number (samples don't have exact row)
                    "column": column
                },
                "confidence": finding.get("confidence", 0.85),
                "matched_text": value,
                "start": 0,
                "end": len(str(value))
            })

    # Calculate compliance status based on total detections
    total_detections = sum(detections_by_type.values())
    if total_detections == 0:
        compliance_status = "compliant"
    elif total_detections < 5:
        compliance_status = "warning"
    else:
        compliance_status = "violation"

    # Generate recommendations
    recommendations = []
    if total_detections > 0:
        recommendations.append(f"Found {total_detections} PII detections across {len(detections_by_type)} types")
        recommendations.append("Consider encrypting or masking sensitive fields")
        if compliance_status == "violation":
            recommendations.append("High volume of PII detected - implement data minimization")

    return {
        "run_id": run_id,
        "dataset_name": dataset_name,
        "total_detections": total_detections,
        "detections_by_type": detections_by_type,
        "detections": detections,
        "compliance_status": compliance_status,
        "recommendations": recommendations
    }


@router.get("/metrics-test/{run_id}")
async def get_quality_metrics_test(run_id: str):
    """Test endpoint to verify transformation works"""
    if run_id not in pipeline_runs:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    run_data = pipeline_runs[run_id]
    if run_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="Not completed")

    results = run_data.get("results", {})
    quality_results = results.get("quality", {})
    transformed = transform_quality_metrics(quality_results, run_id)

    return transformed


@router.get("/metrics/{run_id}")
async def get_quality_metrics(run_id: str) -> dict:
    """
    Get data quality metrics for a pipeline run.

    Returns frontend-compatible structure with all 6 dimensions.

    Args:
        run_id: The pipeline run ID

    Returns:
        Quality scores with dimensions structure matching frontend TypeScript interface
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

    # Transform to frontend format
    transformed = transform_quality_metrics(quality_results, run_id)

    # Debug logging
    print(f"DEBUG: Transformed keys: {list(transformed.keys())}")
    print(f"DEBUG: Has dimensions: {'dimensions' in transformed}")
    print(f"DEBUG: Has column_metrics: {'column_metrics' in transformed}")

    return transformed


@router.get("/pii-report/{run_id}")
async def get_pii_report(run_id: str) -> dict:
    """
    Get PII detection report for a pipeline run.

    Returns frontend-compatible structure with compliance status and recommendations.

    Args:
        run_id: The pipeline run ID

    Returns:
        PII report with detections, compliance status, and recommendations
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

    # Transform to frontend format
    transformed = transform_pii_report(
        pii_results,
        run_id,
        run_data.get("dataset_name", "unknown")
    )

    return transformed


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
