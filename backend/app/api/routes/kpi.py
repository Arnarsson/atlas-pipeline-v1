"""
KPI Dashboard API

Provides KPIs for measuring automation impact (before/after).
Tracks: Throughput, Lead Time, Approval Rate, Rejection Reasons.
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/kpi", tags=["kpi"])


class TimeRange(str, Enum):
    """Time range for KPI calculations."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class ThroughputMetric(BaseModel):
    """Throughput metrics - cases processed per time period."""
    period: str
    cases_submitted: int = 0
    cases_resolved: int = 0
    cases_pending: int = 0
    avg_daily_throughput: float = 0.0
    trend_percent: float = 0.0  # % change vs previous period


class LeadTimeMetric(BaseModel):
    """Lead time metrics - time from submission to resolution."""
    period: str
    avg_lead_time_hours: float = 0.0
    median_lead_time_hours: float = 0.0
    p95_lead_time_hours: float = 0.0  # 95th percentile
    min_lead_time_hours: float = 0.0
    max_lead_time_hours: float = 0.0
    trend_percent: float = 0.0  # % change vs previous (negative is good)


class ApprovalMetric(BaseModel):
    """Approval rate metrics."""
    period: str
    total_resolved: int = 0
    approved: int = 0
    rejected: int = 0
    approval_rate: float = 0.0
    trend_percent: float = 0.0


class RejectionReason(BaseModel):
    """Rejection reason breakdown."""
    reason: str
    count: int = 0
    percentage: float = 0.0


class RejectionMetric(BaseModel):
    """Rejection reasons breakdown."""
    period: str
    total_rejections: int = 0
    reasons: List[RejectionReason] = Field(default_factory=list)
    top_reason: Optional[str] = None


class KPISummary(BaseModel):
    """Complete KPI summary for a time period."""
    period: str
    period_start: datetime
    period_end: datetime
    throughput: ThroughputMetric
    lead_time: LeadTimeMetric
    approval: ApprovalMetric
    rejections: RejectionMetric


class BeforeAfterComparison(BaseModel):
    """Before/after comparison for demonstrating automation impact."""
    metric_name: str
    before_value: float
    after_value: float
    change_absolute: float
    change_percent: float
    improvement: bool  # True if change is positive impact


class KPIDashboardResponse(BaseModel):
    """Complete KPI dashboard response."""
    generated_at: datetime
    period: str
    current: KPISummary
    previous: Optional[KPISummary] = None
    before_after: List[BeforeAfterComparison] = Field(default_factory=list)


# In-memory storage for demo data
_kpi_data: Dict[str, Any] = {}


def _generate_demo_kpi(period: TimeRange, include_before_after: bool = True) -> KPIDashboardResponse:
    """Generate demo KPI data for the specified period."""
    now = datetime.utcnow()

    if period == TimeRange.DAY:
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = now
        prev_start = period_start - timedelta(days=1)
        prev_end = period_start
        period_label = "Today"
    elif period == TimeRange.WEEK:
        period_start = now - timedelta(days=now.weekday())
        period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = now
        prev_start = period_start - timedelta(weeks=1)
        prev_end = period_start
        period_label = "This Week"
    elif period == TimeRange.MONTH:
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = now
        prev_start = (period_start - timedelta(days=1)).replace(day=1)
        prev_end = period_start
        period_label = "This Month"
    elif period == TimeRange.QUARTER:
        quarter = (now.month - 1) // 3
        period_start = now.replace(month=quarter * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = now
        prev_start = period_start - timedelta(days=90)
        prev_end = period_start
        period_label = "This Quarter"
    else:  # YEAR
        period_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = now
        prev_start = period_start.replace(year=now.year - 1)
        prev_end = period_start
        period_label = "This Year"

    # Current period KPIs (after automation)
    current = KPISummary(
        period=period_label,
        period_start=period_start,
        period_end=period_end,
        throughput=ThroughputMetric(
            period=period_label,
            cases_submitted=156,
            cases_resolved=142,
            cases_pending=14,
            avg_daily_throughput=28.4,
            trend_percent=35.0,
        ),
        lead_time=LeadTimeMetric(
            period=period_label,
            avg_lead_time_hours=2.3,
            median_lead_time_hours=1.8,
            p95_lead_time_hours=6.5,
            min_lead_time_hours=0.2,
            max_lead_time_hours=12.0,
            trend_percent=-65.0,  # Negative is good for lead time
        ),
        approval=ApprovalMetric(
            period=period_label,
            total_resolved=142,
            approved=128,
            rejected=14,
            approval_rate=0.90,
            trend_percent=8.0,
        ),
        rejections=RejectionMetric(
            period=period_label,
            total_rejections=14,
            reasons=[
                RejectionReason(reason="Missing Documentation", count=5, percentage=35.7),
                RejectionReason(reason="Invalid Amount", count=4, percentage=28.6),
                RejectionReason(reason="Policy Violation", count=3, percentage=21.4),
                RejectionReason(reason="Duplicate Claim", count=2, percentage=14.3),
            ],
            top_reason="Missing Documentation",
        ),
    )

    # Previous period KPIs (before automation, or just previous period)
    previous = KPISummary(
        period=f"Previous {period.value}",
        period_start=prev_start,
        period_end=prev_end,
        throughput=ThroughputMetric(
            period=f"Previous {period.value}",
            cases_submitted=115,
            cases_resolved=98,
            cases_pending=17,
            avg_daily_throughput=21.0,
            trend_percent=0.0,
        ),
        lead_time=LeadTimeMetric(
            period=f"Previous {period.value}",
            avg_lead_time_hours=6.5,
            median_lead_time_hours=5.2,
            p95_lead_time_hours=18.0,
            min_lead_time_hours=1.0,
            max_lead_time_hours=48.0,
            trend_percent=0.0,
        ),
        approval=ApprovalMetric(
            period=f"Previous {period.value}",
            total_resolved=98,
            approved=82,
            rejected=16,
            approval_rate=0.84,
            trend_percent=0.0,
        ),
        rejections=RejectionMetric(
            period=f"Previous {period.value}",
            total_rejections=16,
            reasons=[
                RejectionReason(reason="Missing Documentation", count=8, percentage=50.0),
                RejectionReason(reason="Invalid Amount", count=4, percentage=25.0),
                RejectionReason(reason="Policy Violation", count=3, percentage=18.75),
                RejectionReason(reason="Other", count=1, percentage=6.25),
            ],
            top_reason="Missing Documentation",
        ),
    )

    # Before/after comparison (before Atlas vs after Atlas)
    before_after = []
    if include_before_after:
        # Manual process (before)
        before_throughput = 21.0
        before_lead_time = 6.5
        before_approval = 0.84
        before_errors = 18  # % error rate

        # Automated process (after)
        after_throughput = 28.4
        after_lead_time = 2.3
        after_approval = 0.90
        after_errors = 5  # % error rate

        before_after = [
            BeforeAfterComparison(
                metric_name="Daily Throughput",
                before_value=before_throughput,
                after_value=after_throughput,
                change_absolute=after_throughput - before_throughput,
                change_percent=((after_throughput - before_throughput) / before_throughput) * 100,
                improvement=True,
            ),
            BeforeAfterComparison(
                metric_name="Avg Lead Time (hours)",
                before_value=before_lead_time,
                after_value=after_lead_time,
                change_absolute=after_lead_time - before_lead_time,
                change_percent=((after_lead_time - before_lead_time) / before_lead_time) * 100,
                improvement=True,  # Decrease is improvement
            ),
            BeforeAfterComparison(
                metric_name="Approval Rate",
                before_value=before_approval * 100,
                after_value=after_approval * 100,
                change_absolute=(after_approval - before_approval) * 100,
                change_percent=((after_approval - before_approval) / before_approval) * 100,
                improvement=True,
            ),
            BeforeAfterComparison(
                metric_name="Error Rate (%)",
                before_value=before_errors,
                after_value=after_errors,
                change_absolute=after_errors - before_errors,
                change_percent=((after_errors - before_errors) / before_errors) * 100,
                improvement=True,  # Decrease is improvement
            ),
        ]

    return KPIDashboardResponse(
        generated_at=now,
        period=period_label,
        current=current,
        previous=previous,
        before_after=before_after,
    )


@router.get("/dashboard", response_model=KPIDashboardResponse)
async def get_kpi_dashboard(
    period: TimeRange = Query(TimeRange.WEEK, description="Time period for KPIs"),
    include_comparison: bool = Query(True, description="Include before/after comparison"),
):
    """
    Get KPI dashboard data.

    Returns throughput, lead time, approval rate, and rejection reasons
    for the specified time period with optional before/after comparison.
    """
    return _generate_demo_kpi(period, include_comparison)


@router.get("/throughput", response_model=ThroughputMetric)
async def get_throughput(
    period: TimeRange = Query(TimeRange.WEEK, description="Time period"),
):
    """Get throughput metrics."""
    dashboard = _generate_demo_kpi(period, False)
    return dashboard.current.throughput


@router.get("/lead-time", response_model=LeadTimeMetric)
async def get_lead_time(
    period: TimeRange = Query(TimeRange.WEEK, description="Time period"),
):
    """Get lead time metrics."""
    dashboard = _generate_demo_kpi(period, False)
    return dashboard.current.lead_time


@router.get("/approval-rate", response_model=ApprovalMetric)
async def get_approval_rate(
    period: TimeRange = Query(TimeRange.WEEK, description="Time period"),
):
    """Get approval rate metrics."""
    dashboard = _generate_demo_kpi(period, False)
    return dashboard.current.approval


@router.get("/rejections", response_model=RejectionMetric)
async def get_rejections(
    period: TimeRange = Query(TimeRange.WEEK, description="Time period"),
):
    """Get rejection reasons breakdown."""
    dashboard = _generate_demo_kpi(period, False)
    return dashboard.current.rejections


@router.get("/before-after", response_model=List[BeforeAfterComparison])
async def get_before_after_comparison():
    """
    Get before/after comparison for demonstrating automation impact.

    Shows key metrics comparing manual process vs automated process.
    """
    dashboard = _generate_demo_kpi(TimeRange.MONTH, True)
    return dashboard.before_after


@router.get("/trends")
async def get_kpi_trends(
    metric: str = Query(..., description="Metric: throughput, lead_time, approval_rate"),
    periods: int = Query(7, ge=1, le=90, description="Number of periods"),
):
    """
    Get trend data for a specific metric over multiple periods.

    Returns daily data points for charting.
    """
    now = datetime.utcnow()
    data_points = []

    for i in range(periods - 1, -1, -1):
        date = now - timedelta(days=i)

        if metric == "throughput":
            # Simulate daily throughput (with some variance and upward trend)
            base = 25 + (periods - i) * 0.3  # Gradual improvement
            variance = (hash(str(date.date())) % 10) - 5  # Random-ish variance
            value = max(15, base + variance)
        elif metric == "lead_time":
            # Simulate lead time (with downward trend = improvement)
            base = 4.5 - (periods - i) * 0.1  # Gradual improvement
            variance = ((hash(str(date.date())) % 6) - 3) * 0.3
            value = max(1.0, base + variance)
        elif metric == "approval_rate":
            # Simulate approval rate (with upward trend)
            base = 0.82 + (periods - i) * 0.005
            variance = ((hash(str(date.date())) % 6) - 3) * 0.02
            value = min(0.98, max(0.75, base + variance))
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown metric: {metric}. Use: throughput, lead_time, approval_rate"
            )

        data_points.append({
            "date": date.strftime("%Y-%m-%d"),
            "value": round(value, 2),
        })

    return {
        "metric": metric,
        "periods": periods,
        "data": data_points,
    }
