"""
Human-in-the-Loop (HIL) Decision API

Endpoints for managing decisions that require human approval.
Supports approve/reject with audit trail, assignment, and notifications.
"""

import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/decisions", tags=["decisions"])


class DecisionStatus(str, Enum):
    """Status of a decision."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REASSIGNED = "reassigned"
    EXPIRED = "expired"


class DecisionSeverity(str, Enum):
    """Severity level for decisions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionType(str, Enum):
    """Type of decision."""
    CLASSIFICATION = "classification"
    APPROVAL = "approval"
    VALIDATION = "validation"
    REVIEW = "review"


class AIRecommendation(BaseModel):
    """AI-generated recommendation for a decision."""
    action: str  # approve, reject, escalate
    confidence: float = Field(ge=0, le=1)
    reasoning: str
    model_id: str
    model_version: str
    generated_at: datetime


class Decision(BaseModel):
    """A decision requiring human approval."""
    id: str = Field(default_factory=lambda: f"dec_{uuid.uuid4().hex[:12]}")
    decision_type: DecisionType
    severity: DecisionSeverity
    status: DecisionStatus = DecisionStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    # Content
    title: str
    description: str
    source_document: Optional[str] = None
    source_document_hash: Optional[str] = None

    # Context
    context: Dict[str, Any] = Field(default_factory=dict)
    extracted_data: Dict[str, Any] = Field(default_factory=dict)

    # AI Recommendation
    ai_recommendation: Optional[AIRecommendation] = None

    # Assignment
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None

    # Resolution
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_comment: Optional[str] = None

    # Audit
    audit_id: str = Field(default_factory=lambda: f"aud_{uuid.uuid4().hex[:16]}")


class DecisionCreateRequest(BaseModel):
    """Request to create a new decision."""
    decision_type: DecisionType
    severity: DecisionSeverity
    title: str
    description: str
    source_document: Optional[str] = None
    source_document_hash: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    ai_recommendation: Optional[AIRecommendation] = None
    assigned_to: Optional[str] = None
    expires_in_hours: Optional[int] = 48  # Default 48 hour expiry


class DecisionApproveRequest(BaseModel):
    """Request to approve a decision."""
    user: str
    comment: Optional[str] = None


class DecisionRejectRequest(BaseModel):
    """Request to reject a decision."""
    user: str
    reason: str


class DecisionAssignRequest(BaseModel):
    """Request to assign/reassign a decision."""
    user: str
    assigned_to: str
    comment: Optional[str] = None


class DecisionListResponse(BaseModel):
    """Response for listing decisions."""
    total: int
    pending: int
    approved: int
    rejected: int
    decisions: List[Decision]


class AuditEvent(BaseModel):
    """Audit event for decision tracking."""
    id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    decision_id: str
    audit_id: str
    event_type: str  # created, viewed, approved, rejected, assigned, expired
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


# In-memory storage (replace with database in production)
_decisions: Dict[str, Decision] = {}
_audit_events: List[AuditEvent] = []


def _log_audit_event(
    decision_id: str,
    audit_id: str,
    event_type: str,
    user: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> AuditEvent:
    """Log an audit event."""
    event = AuditEvent(
        decision_id=decision_id,
        audit_id=audit_id,
        event_type=event_type,
        user=user,
        details=details or {},
    )
    _audit_events.append(event)
    logger.info(f"Audit event: {event_type} for {decision_id} by {user}")
    return event


@router.post("/", response_model=Decision)
async def create_decision(request: DecisionCreateRequest):
    """
    Create a new decision requiring human approval.

    Returns the created decision with audit ID for tracking.
    """
    # Calculate expiry
    expires_at = None
    if request.expires_in_hours:
        expires_at = datetime.utcnow() + timedelta(hours=request.expires_in_hours)

    decision = Decision(
        decision_type=request.decision_type,
        severity=request.severity,
        title=request.title,
        description=request.description,
        source_document=request.source_document,
        source_document_hash=request.source_document_hash,
        context=request.context,
        extracted_data=request.extracted_data,
        ai_recommendation=request.ai_recommendation,
        assigned_to=request.assigned_to,
        assigned_at=datetime.utcnow() if request.assigned_to else None,
        expires_at=expires_at,
    )

    _decisions[decision.id] = decision

    # Log audit event
    _log_audit_event(
        decision_id=decision.id,
        audit_id=decision.audit_id,
        event_type="created",
        user="system",
        details={
            "severity": request.severity.value,
            "assigned_to": request.assigned_to,
            "expires_at": expires_at.isoformat() if expires_at else None,
        },
    )

    logger.info(f"Created decision {decision.id} ({request.severity.value})")
    return decision


@router.get("/pending", response_model=DecisionListResponse)
async def get_pending_decisions(
    severity: Optional[DecisionSeverity] = Query(None, description="Filter by severity"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee"),
    decision_type: Optional[DecisionType] = Query(None, description="Filter by type"),
    max_age_hours: Optional[int] = Query(None, description="Max age in hours"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    Get pending decisions requiring approval.

    Supports filtering by severity, assignee, type, and age.
    """
    # Filter decisions
    filtered = []
    cutoff_time = None
    if max_age_hours:
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

    for decision in _decisions.values():
        if decision.status != DecisionStatus.PENDING:
            continue
        if severity and decision.severity != severity:
            continue
        if assigned_to and decision.assigned_to != assigned_to:
            continue
        if decision_type and decision.decision_type != decision_type:
            continue
        if cutoff_time and decision.created_at < cutoff_time:
            continue
        filtered.append(decision)

    # Sort by severity (critical first) then by creation time
    severity_order = {
        DecisionSeverity.CRITICAL: 0,
        DecisionSeverity.HIGH: 1,
        DecisionSeverity.MEDIUM: 2,
        DecisionSeverity.LOW: 3,
    }
    filtered.sort(key=lambda d: (severity_order[d.severity], d.created_at))

    # Paginate
    total = len(filtered)
    paginated = filtered[offset:offset + limit]

    # Count by status
    all_decisions = list(_decisions.values())
    pending = sum(1 for d in all_decisions if d.status == DecisionStatus.PENDING)
    approved = sum(1 for d in all_decisions if d.status == DecisionStatus.APPROVED)
    rejected = sum(1 for d in all_decisions if d.status == DecisionStatus.REJECTED)

    return DecisionListResponse(
        total=total,
        pending=pending,
        approved=approved,
        rejected=rejected,
        decisions=paginated,
    )


@router.get("/{decision_id}", response_model=Decision)
async def get_decision(decision_id: str):
    """
    Get a specific decision by ID.

    Returns decision with full context and audit trail link.
    """
    if decision_id not in _decisions:
        raise HTTPException(status_code=404, detail="Decision not found")

    decision = _decisions[decision_id]

    # Log view event
    _log_audit_event(
        decision_id=decision_id,
        audit_id=decision.audit_id,
        event_type="viewed",
    )

    return decision


@router.post("/{decision_id}/approve", response_model=Decision)
async def approve_decision(decision_id: str, request: DecisionApproveRequest):
    """
    Approve a decision.

    Records the approving user and optional comment.
    Creates audit trail entry.
    """
    if decision_id not in _decisions:
        raise HTTPException(status_code=404, detail="Decision not found")

    decision = _decisions[decision_id]

    if decision.status != DecisionStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Decision already {decision.status.value}"
        )

    # Update decision
    decision.status = DecisionStatus.APPROVED
    decision.resolved_by = request.user
    decision.resolved_at = datetime.utcnow()
    decision.resolution_comment = request.comment
    decision.updated_at = datetime.utcnow()

    # Log audit event
    _log_audit_event(
        decision_id=decision_id,
        audit_id=decision.audit_id,
        event_type="approved",
        user=request.user,
        details={
            "comment": request.comment,
            "source_document_hash": decision.source_document_hash,
            "ai_recommendation": decision.ai_recommendation.action if decision.ai_recommendation else None,
        },
    )

    logger.info(f"Decision {decision_id} approved by {request.user}")
    return decision


@router.post("/{decision_id}/reject", response_model=Decision)
async def reject_decision(decision_id: str, request: DecisionRejectRequest):
    """
    Reject a decision.

    Records the rejecting user and required reason.
    Creates audit trail entry.
    """
    if decision_id not in _decisions:
        raise HTTPException(status_code=404, detail="Decision not found")

    decision = _decisions[decision_id]

    if decision.status != DecisionStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Decision already {decision.status.value}"
        )

    # Update decision
    decision.status = DecisionStatus.REJECTED
    decision.resolved_by = request.user
    decision.resolved_at = datetime.utcnow()
    decision.resolution_comment = request.reason
    decision.updated_at = datetime.utcnow()

    # Log audit event
    _log_audit_event(
        decision_id=decision_id,
        audit_id=decision.audit_id,
        event_type="rejected",
        user=request.user,
        details={
            "reason": request.reason,
            "source_document_hash": decision.source_document_hash,
        },
    )

    logger.info(f"Decision {decision_id} rejected by {request.user}: {request.reason}")
    return decision


@router.post("/{decision_id}/assign", response_model=Decision)
async def assign_decision(decision_id: str, request: DecisionAssignRequest):
    """
    Assign or reassign a decision to a user.

    Creates audit trail entry.
    """
    if decision_id not in _decisions:
        raise HTTPException(status_code=404, detail="Decision not found")

    decision = _decisions[decision_id]

    if decision.status != DecisionStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reassign {decision.status.value} decision"
        )

    previous_assignee = decision.assigned_to

    # Update decision
    decision.assigned_to = request.assigned_to
    decision.assigned_at = datetime.utcnow()
    decision.updated_at = datetime.utcnow()

    # Log audit event
    _log_audit_event(
        decision_id=decision_id,
        audit_id=decision.audit_id,
        event_type="assigned",
        user=request.user,
        details={
            "assigned_to": request.assigned_to,
            "previous_assignee": previous_assignee,
            "comment": request.comment,
        },
    )

    logger.info(f"Decision {decision_id} assigned to {request.assigned_to} by {request.user}")
    return decision


@router.get("/{decision_id}/audit", response_model=List[AuditEvent])
async def get_decision_audit_trail(decision_id: str):
    """
    Get the complete audit trail for a decision.

    Returns all events: created, viewed, approved, rejected, assigned.
    """
    if decision_id not in _decisions:
        raise HTTPException(status_code=404, detail="Decision not found")

    events = [e for e in _audit_events if e.decision_id == decision_id]
    events.sort(key=lambda e: e.timestamp)

    return events


@router.get("/stats/summary")
async def get_decision_stats():
    """
    Get summary statistics for decisions.

    Returns counts by status, severity, and response times.
    """
    all_decisions = list(_decisions.values())

    # Count by status
    by_status = {}
    for status in DecisionStatus:
        by_status[status.value] = sum(1 for d in all_decisions if d.status == status)

    # Count by severity
    by_severity = {}
    for severity in DecisionSeverity:
        by_severity[severity.value] = sum(1 for d in all_decisions if d.severity == severity)

    # Calculate response times for resolved decisions
    response_times = []
    for d in all_decisions:
        if d.resolved_at and d.created_at:
            delta = (d.resolved_at - d.created_at).total_seconds()
            response_times.append(delta)

    avg_response_time = sum(response_times) / len(response_times) if response_times else 0

    # Approval rate
    resolved = [d for d in all_decisions if d.status in [DecisionStatus.APPROVED, DecisionStatus.REJECTED]]
    approval_rate = 0
    if resolved:
        approval_rate = sum(1 for d in resolved if d.status == DecisionStatus.APPROVED) / len(resolved)

    # AI recommendation accuracy
    ai_recommended = [
        d for d in resolved
        if d.ai_recommendation
    ]
    ai_accuracy = 0
    if ai_recommended:
        correct = sum(
            1 for d in ai_recommended
            if (d.ai_recommendation.action == "approve" and d.status == DecisionStatus.APPROVED)
            or (d.ai_recommendation.action == "reject" and d.status == DecisionStatus.REJECTED)
        )
        ai_accuracy = correct / len(ai_recommended)

    return {
        "total_decisions": len(all_decisions),
        "by_status": by_status,
        "by_severity": by_severity,
        "avg_response_time_seconds": avg_response_time,
        "approval_rate": approval_rate,
        "ai_recommendation_accuracy": ai_accuracy,
        "pending_critical": sum(
            1 for d in all_decisions
            if d.status == DecisionStatus.PENDING and d.severity == DecisionSeverity.CRITICAL
        ),
        "pending_over_24h": sum(
            1 for d in all_decisions
            if d.status == DecisionStatus.PENDING
            and (datetime.utcnow() - d.created_at).total_seconds() > 86400
        ),
    }
