"""
Compliance Report API

Endpoints for generating compliance reports in PDF and Excel formats.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.reports import (
    ComplianceReportGenerator,
    ReportData,
    ReportFormat,
    get_report_generator,
)
from app.reports.compliance_report import (
    PIISummary,
    QualitySummary,
    GDPRStatus,
    AuditSummary,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["reports"])


class GenerateReportRequest(BaseModel):
    """Request to generate a compliance report."""
    dataset_name: str = Field(..., description="Name of the dataset")
    organization: str = Field(default="Atlas Intelligence", description="Organization name")
    format: str = Field(default="pdf", description="Output format: pdf or excel")

    # Optional data overrides (will use mock data if not provided)
    pii: Optional[PIISummary] = None
    quality: Optional[QualitySummary] = None
    gdpr: Optional[GDPRStatus] = None
    audit: Optional[AuditSummary] = None


class ReportStatusResponse(BaseModel):
    """Response for report generation status."""
    pdf_available: bool
    excel_available: bool
    supported_formats: list[str]


@router.get("/status", response_model=ReportStatusResponse)
async def get_report_status():
    """
    Get report generation capabilities.

    Returns which formats are available based on installed dependencies.
    """
    generator = get_report_generator()

    formats = []
    if generator._pdf_available:
        formats.append("pdf")
    if generator._excel_available:
        formats.append("excel")

    return ReportStatusResponse(
        pdf_available=generator._pdf_available,
        excel_available=generator._excel_available,
        supported_formats=formats,
    )


@router.post("/generate")
async def generate_compliance_report(request: GenerateReportRequest):
    """
    Generate a compliance report.

    Args:
        request: Report generation parameters

    Returns:
        PDF or Excel file as response
    """
    generator = get_report_generator()

    # Parse format
    try:
        format_enum = ReportFormat(request.format.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format. Supported: pdf, excel"
        )

    # Check availability
    if format_enum == ReportFormat.PDF and not generator._pdf_available:
        raise HTTPException(
            status_code=503,
            detail="PDF generation not available. Install reportlab."
        )
    if format_enum == ReportFormat.EXCEL and not generator._excel_available:
        raise HTTPException(
            status_code=503,
            detail="Excel generation not available. Install openpyxl."
        )

    # Build report data
    data = ReportData(
        organization=request.organization,
        dataset_name=request.dataset_name,
        date_range_start=datetime.utcnow() - timedelta(days=30),
        date_range_end=datetime.utcnow(),
    )

    # Use provided data or generate demo data
    if request.pii:
        data.pii = request.pii
    else:
        data.pii = PIISummary(
            total_detections=42,
            by_type={
                "EMAIL_ADDRESS": 15,
                "PHONE_NUMBER": 12,
                "PERSON": 8,
                "CREDIT_CARD": 4,
                "DATE_TIME": 3,
            },
            high_risk_count=4,
            masked_count=38,
            avg_confidence=0.92,
        )

    if request.quality:
        data.quality = request.quality
    else:
        data.quality = QualitySummary(
            overall_score=0.94,
            completeness=0.97,
            uniqueness=0.99,
            validity=0.95,
            timeliness=0.92,
            accuracy=0.91,
            consistency=0.93,
            issues_found=12,
            records_processed=10542,
        )

    if request.gdpr:
        data.gdpr = request.gdpr
    else:
        data.gdpr = GDPRStatus(
            compliant=True,
            pending_requests=2,
            completed_requests=18,
            access_requests=8,
            deletion_requests=7,
            rectification_requests=5,
            retention_policy_days=365,
            data_processing_basis="consent",
        )

    if request.audit:
        data.audit = request.audit
    else:
        data.audit = AuditSummary(
            total_events=1247,
            by_type={
                "data_access": 520,
                "data_modification": 312,
                "user_login": 245,
                "report_generation": 98,
                "decision_approval": 45,
                "decision_rejection": 27,
            },
            last_24h_events=87,
            critical_events=3,
        )

    try:
        report_bytes = generator.generate(data, format_enum)

        # Set response headers
        if format_enum == ReportFormat.PDF:
            media_type = "application/pdf"
            filename = f"compliance_report_{data.report_id}.pdf"
        else:
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"compliance_report_{data.report_id}.xlsx"

        return Response(
            content=report_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )


@router.get("/generate/pdf")
async def generate_pdf_report(
    dataset_name: str = Query(..., description="Dataset name"),
    organization: str = Query("Atlas Intelligence", description="Organization"),
):
    """
    Generate a PDF compliance report (GET endpoint for simple downloads).
    """
    request = GenerateReportRequest(
        dataset_name=dataset_name,
        organization=organization,
        format="pdf",
    )
    return await generate_compliance_report(request)


@router.get("/generate/excel")
async def generate_excel_report(
    dataset_name: str = Query(..., description="Dataset name"),
    organization: str = Query("Atlas Intelligence", description="Organization"),
):
    """
    Generate an Excel compliance report (GET endpoint for simple downloads).
    """
    request = GenerateReportRequest(
        dataset_name=dataset_name,
        organization=organization,
        format="excel",
    )
    return await generate_compliance_report(request)
