"""
Claims & Approvals Demo API

Pre-configured demo pipeline for showcasing Atlas Pipeline capabilities.
Demonstrates the complete flow: Inbox → Document Processing → HIL Decision → Audit.
"""

import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/demo", tags=["demo"])


class DemoScenario(str, Enum):
    """Available demo scenarios."""
    CLAIMS_APPROVAL = "claims_approval"
    INVOICE_PROCESSING = "invoice_processing"
    CONTRACT_REVIEW = "contract_review"


class ClaimType(str, Enum):
    """Types of claims in demo."""
    EXPENSE = "expense"
    TRAVEL = "travel"
    MEDICAL = "medical"
    EQUIPMENT = "equipment"


class ClaimStatus(str, Enum):
    """Claim processing status."""
    SUBMITTED = "submitted"
    DOCUMENT_PROCESSING = "document_processing"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class DemoClaim(BaseModel):
    """A demo claim for the Claims & Approvals flow."""
    claim_id: str = Field(default_factory=lambda: f"CLM-{uuid.uuid4().hex[:8].upper()}")
    claim_type: ClaimType
    status: ClaimStatus = ClaimStatus.SUBMITTED
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_by: str
    amount: float
    currency: str = "DKK"
    description: str
    category: str

    # Document info
    document_filename: Optional[str] = None
    document_hash: Optional[str] = None
    document_extracted: bool = False

    # Extracted data
    extracted_vendor: Optional[str] = None
    extracted_date: Optional[datetime] = None
    extracted_amount: Optional[float] = None
    extracted_items: List[str] = Field(default_factory=list)

    # PII detection
    pii_detected: bool = False
    pii_types: List[str] = Field(default_factory=list)
    pii_masked: bool = False

    # Quality check
    quality_score: Optional[float] = None
    quality_issues: List[str] = Field(default_factory=list)

    # Decision tracking
    decision_id: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # Audit
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)


class DemoClaimSubmission(BaseModel):
    """Request to submit a demo claim."""
    claim_type: ClaimType
    submitted_by: str = "demo_user@atlas-intelligence.com"
    amount: float
    description: str
    category: str = "General"


class DemoStats(BaseModel):
    """Statistics for the demo."""
    total_claims: int = 0
    by_status: Dict[str, int] = Field(default_factory=dict)
    by_type: Dict[str, int] = Field(default_factory=dict)
    avg_processing_time_seconds: float = 0.0
    approval_rate: float = 0.0
    total_amount_processed: float = 0.0


class DemoScenarioConfig(BaseModel):
    """Configuration for a demo scenario."""
    scenario: DemoScenario
    name: str
    description: str
    steps: List[str]
    estimated_duration_seconds: int
    features_demonstrated: List[str]


# In-memory demo data
_demo_claims: Dict[str, DemoClaim] = {}


def _add_audit_event(claim: DemoClaim, event_type: str, details: Dict[str, Any] = None):
    """Add an audit event to a claim."""
    claim.audit_trail.append({
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "details": details or {},
    })


def _initialize_demo_claims():
    """Initialize demo claims with sample data."""
    if _demo_claims:
        return

    sample_claims = [
        DemoClaim(
            claim_type=ClaimType.EXPENSE,
            status=ClaimStatus.APPROVED,
            submitted_at=datetime.utcnow() - timedelta(days=5),
            submitted_by="alice@company.com",
            amount=1250.00,
            description="Office supplies for Q4",
            category="Office Supplies",
            document_filename="receipt_001.pdf",
            document_extracted=True,
            extracted_vendor="Staples Denmark",
            extracted_amount=1250.00,
            quality_score=0.95,
            reviewed_by="manager@company.com",
            reviewed_at=datetime.utcnow() - timedelta(days=4),
        ),
        DemoClaim(
            claim_type=ClaimType.TRAVEL,
            status=ClaimStatus.PENDING_REVIEW,
            submitted_at=datetime.utcnow() - timedelta(hours=3),
            submitted_by="bob@company.com",
            amount=3500.00,
            description="Client meeting in Stockholm",
            category="Business Travel",
            document_filename="travel_expenses.pdf",
            document_extracted=True,
            extracted_vendor="SAS Airlines",
            extracted_amount=3500.00,
            pii_detected=True,
            pii_types=["PERSON", "EMAIL_ADDRESS"],
            pii_masked=True,
            quality_score=0.88,
        ),
        DemoClaim(
            claim_type=ClaimType.EQUIPMENT,
            status=ClaimStatus.REJECTED,
            submitted_at=datetime.utcnow() - timedelta(days=2),
            submitted_by="charlie@company.com",
            amount=15000.00,
            description="New laptop for development",
            category="IT Equipment",
            document_filename="quote_laptop.pdf",
            document_extracted=True,
            extracted_vendor="Dell Technologies",
            extracted_amount=15000.00,
            quality_score=0.72,
            quality_issues=["Amount exceeds single-approval limit", "Missing manager pre-approval"],
            reviewed_by="finance@company.com",
            reviewed_at=datetime.utcnow() - timedelta(days=1),
            rejection_reason="Amount exceeds DKK 10,000 limit without executive approval",
        ),
        DemoClaim(
            claim_type=ClaimType.EXPENSE,
            status=ClaimStatus.DOCUMENT_PROCESSING,
            submitted_at=datetime.utcnow() - timedelta(minutes=15),
            submitted_by="diana@company.com",
            amount=450.00,
            description="Team lunch meeting",
            category="Meals & Entertainment",
            document_filename="receipt_team_lunch.jpg",
        ),
    ]

    for claim in sample_claims:
        _add_audit_event(claim, "claim.submitted", {"amount": claim.amount})
        if claim.document_extracted:
            _add_audit_event(claim, "document.processed", {"extracted_amount": claim.extracted_amount})
        if claim.pii_detected:
            _add_audit_event(claim, "pii.detected", {"types": claim.pii_types})
        if claim.reviewed_at:
            _add_audit_event(claim, f"claim.{claim.status.value}", {"reviewer": claim.reviewed_by})
        _demo_claims[claim.claim_id] = claim

    logger.info(f"Initialized {len(_demo_claims)} demo claims")


# Initialize on module load
_initialize_demo_claims()


@router.get("/scenarios", response_model=List[DemoScenarioConfig])
async def get_demo_scenarios():
    """
    Get available demo scenarios.
    """
    return [
        DemoScenarioConfig(
            scenario=DemoScenario.CLAIMS_APPROVAL,
            name="Claims & Approvals",
            description="Complete expense claim processing workflow with document extraction, PII detection, and human-in-the-loop approval.",
            steps=[
                "1. Upload claim document (PDF/image)",
                "2. Automatic document extraction (OCR if needed)",
                "3. PII detection and masking",
                "4. Quality validation",
                "5. AI recommendation",
                "6. Human review and decision",
                "7. Audit trail generation",
            ],
            estimated_duration_seconds=90,
            features_demonstrated=[
                "Document Processing (unstructured + Azure OCR)",
                "PII Detection (Presidio ML)",
                "Quality Validation (6 dimensions)",
                "Human-in-the-Loop (HIL) Decisions",
                "Audit Logging (EU AI Act Art. 12)",
                "Compliance Reporting",
            ],
        ),
        DemoScenarioConfig(
            scenario=DemoScenario.INVOICE_PROCESSING,
            name="Invoice Processing",
            description="Automated invoice processing with vendor matching and payment approval.",
            steps=[
                "1. Receive invoice from vendor",
                "2. Extract invoice data (amount, vendor, items)",
                "3. Match to purchase order",
                "4. Validate payment terms",
                "5. Route for approval based on amount",
                "6. Record in audit log",
            ],
            estimated_duration_seconds=60,
            features_demonstrated=[
                "Document Processing",
                "Data Extraction",
                "Business Rule Validation",
                "Automated Routing",
                "Audit Compliance",
            ],
        ),
        DemoScenarioConfig(
            scenario=DemoScenario.CONTRACT_REVIEW,
            name="Contract Review",
            description="AI-assisted contract review with risk assessment and compliance checking.",
            steps=[
                "1. Upload contract document",
                "2. Extract key terms and clauses",
                "3. Identify risk areas",
                "4. Check compliance requirements",
                "5. Generate review summary",
                "6. Human approval for signing",
            ],
            estimated_duration_seconds=120,
            features_demonstrated=[
                "Document Processing",
                "NLP Analysis",
                "Risk Assessment",
                "Compliance Checking",
                "HIL Decision",
            ],
        ),
    ]


@router.get("/claims", response_model=List[DemoClaim])
async def get_demo_claims(
    status: Optional[ClaimStatus] = Query(None, description="Filter by status"),
    claim_type: Optional[ClaimType] = Query(None, description="Filter by type"),
    limit: int = Query(50, ge=1, le=100),
):
    """
    Get demo claims with optional filtering.
    """
    claims = list(_demo_claims.values())

    if status:
        claims = [c for c in claims if c.status == status]
    if claim_type:
        claims = [c for c in claims if c.claim_type == claim_type]

    # Sort by submitted_at descending
    claims.sort(key=lambda c: c.submitted_at, reverse=True)

    return claims[:limit]


@router.get("/claims/{claim_id}", response_model=DemoClaim)
async def get_demo_claim(claim_id: str):
    """
    Get a specific demo claim.
    """
    if claim_id not in _demo_claims:
        raise HTTPException(status_code=404, detail="Claim not found")
    return _demo_claims[claim_id]


@router.post("/claims", response_model=DemoClaim)
async def submit_demo_claim(submission: DemoClaimSubmission):
    """
    Submit a new demo claim.

    This simulates the complete claim submission process.
    """
    claim = DemoClaim(
        claim_type=submission.claim_type,
        submitted_by=submission.submitted_by,
        amount=submission.amount,
        description=submission.description,
        category=submission.category,
    )

    _add_audit_event(claim, "claim.submitted", {
        "amount": claim.amount,
        "type": claim.claim_type.value,
    })

    _demo_claims[claim.claim_id] = claim
    logger.info(f"Demo claim submitted: {claim.claim_id}")

    return claim


@router.post("/claims/{claim_id}/process")
async def process_demo_claim(claim_id: str):
    """
    Simulate document processing for a demo claim.

    This simulates:
    - Document extraction
    - PII detection
    - Quality validation
    - AI recommendation
    """
    if claim_id not in _demo_claims:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim = _demo_claims[claim_id]

    if claim.status != ClaimStatus.SUBMITTED and claim.status != ClaimStatus.DOCUMENT_PROCESSING:
        raise HTTPException(status_code=400, detail="Claim already processed")

    # Simulate document processing
    claim.status = ClaimStatus.DOCUMENT_PROCESSING
    _add_audit_event(claim, "processing.started")

    # Simulate extraction
    claim.document_extracted = True
    claim.extracted_vendor = "Demo Vendor ApS"
    claim.extracted_date = datetime.utcnow() - timedelta(days=1)
    claim.extracted_amount = claim.amount
    claim.extracted_items = ["Item 1", "Item 2"]
    _add_audit_event(claim, "document.extracted", {
        "vendor": claim.extracted_vendor,
        "amount": claim.extracted_amount,
    })

    # Simulate PII detection
    if claim.amount > 1000:
        claim.pii_detected = True
        claim.pii_types = ["PERSON", "EMAIL_ADDRESS"]
        claim.pii_masked = True
        _add_audit_event(claim, "pii.detected", {"types": claim.pii_types})

    # Simulate quality check
    claim.quality_score = 0.92
    if claim.amount > 10000:
        claim.quality_issues = ["Amount exceeds standard approval threshold"]
        claim.quality_score = 0.78
    _add_audit_event(claim, "quality.checked", {"score": claim.quality_score})

    # Move to pending review
    claim.status = ClaimStatus.PENDING_REVIEW
    claim.decision_id = f"dec_{uuid.uuid4().hex[:12]}"
    _add_audit_event(claim, "decision.created", {"decision_id": claim.decision_id})

    return {
        "claim_id": claim_id,
        "status": claim.status,
        "document_extracted": claim.document_extracted,
        "pii_detected": claim.pii_detected,
        "quality_score": claim.quality_score,
        "decision_id": claim.decision_id,
        "message": "Claim processed and ready for review",
    }


@router.post("/claims/{claim_id}/approve")
async def approve_demo_claim(
    claim_id: str,
    reviewer: str = Query("reviewer@atlas-intelligence.com"),
    comment: Optional[str] = Query(None),
):
    """
    Approve a demo claim.
    """
    if claim_id not in _demo_claims:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim = _demo_claims[claim_id]

    if claim.status != ClaimStatus.PENDING_REVIEW:
        raise HTTPException(status_code=400, detail=f"Claim not pending review (status: {claim.status})")

    claim.status = ClaimStatus.APPROVED
    claim.reviewed_by = reviewer
    claim.reviewed_at = datetime.utcnow()

    _add_audit_event(claim, "claim.approved", {
        "reviewer": reviewer,
        "comment": comment,
    })

    return {
        "claim_id": claim_id,
        "status": claim.status,
        "reviewed_by": claim.reviewed_by,
        "reviewed_at": claim.reviewed_at,
        "message": "Claim approved successfully",
    }


@router.post("/claims/{claim_id}/reject")
async def reject_demo_claim(
    claim_id: str,
    reviewer: str = Query("reviewer@atlas-intelligence.com"),
    reason: str = Query(...),
):
    """
    Reject a demo claim.
    """
    if claim_id not in _demo_claims:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim = _demo_claims[claim_id]

    if claim.status != ClaimStatus.PENDING_REVIEW:
        raise HTTPException(status_code=400, detail=f"Claim not pending review (status: {claim.status})")

    claim.status = ClaimStatus.REJECTED
    claim.reviewed_by = reviewer
    claim.reviewed_at = datetime.utcnow()
    claim.rejection_reason = reason

    _add_audit_event(claim, "claim.rejected", {
        "reviewer": reviewer,
        "reason": reason,
    })

    return {
        "claim_id": claim_id,
        "status": claim.status,
        "reviewed_by": claim.reviewed_by,
        "rejection_reason": claim.rejection_reason,
        "message": "Claim rejected",
    }


@router.get("/stats", response_model=DemoStats)
async def get_demo_stats():
    """
    Get demo statistics.
    """
    claims = list(_demo_claims.values())

    by_status: Dict[str, int] = {}
    by_type: Dict[str, int] = {}
    total_amount = 0.0
    approved_count = 0
    resolved_count = 0
    processing_times = []

    for claim in claims:
        by_status[claim.status.value] = by_status.get(claim.status.value, 0) + 1
        by_type[claim.claim_type.value] = by_type.get(claim.claim_type.value, 0) + 1
        total_amount += claim.amount

        if claim.status in [ClaimStatus.APPROVED, ClaimStatus.REJECTED]:
            resolved_count += 1
            if claim.status == ClaimStatus.APPROVED:
                approved_count += 1
            if claim.reviewed_at:
                delta = (claim.reviewed_at - claim.submitted_at).total_seconds()
                processing_times.append(delta)

    return DemoStats(
        total_claims=len(claims),
        by_status=by_status,
        by_type=by_type,
        avg_processing_time_seconds=sum(processing_times) / len(processing_times) if processing_times else 0,
        approval_rate=approved_count / resolved_count if resolved_count > 0 else 0,
        total_amount_processed=total_amount,
    )


@router.post("/reset")
async def reset_demo():
    """
    Reset demo data to initial state.
    """
    global _demo_claims
    _demo_claims = {}
    _initialize_demo_claims()

    return {
        "message": "Demo data reset successfully",
        "claims_count": len(_demo_claims),
    }


@router.get("/walkthrough")
async def get_demo_walkthrough():
    """
    Get step-by-step walkthrough for the Claims & Approvals demo.

    Returns a script for a 90-second demo.
    """
    return {
        "title": "Claims & Approvals Demo",
        "duration_seconds": 90,
        "talking_points": [
            {
                "time": "0:00-0:15",
                "action": "Introduction",
                "script": "Welcome to Atlas Pipeline. Today I'll show you how we automate claims processing with AI-powered document extraction and human-in-the-loop decisions.",
                "screen": "Dashboard overview",
            },
            {
                "time": "0:15-0:30",
                "action": "Upload Document",
                "script": "Let's submit a new expense claim. I'll drag this receipt into the inbox. Notice how it's immediately queued for processing.",
                "screen": "Inbox Dropzone",
                "api_call": "POST /demo/claims",
            },
            {
                "time": "0:30-0:45",
                "action": "Document Processing",
                "script": "The system extracts text using OCR, identifies the vendor, amount, and date. It also detects any PII like names or email addresses.",
                "screen": "Processing status",
                "api_call": "POST /demo/claims/{id}/process",
            },
            {
                "time": "0:45-1:00",
                "action": "Quality & PII Check",
                "script": "Our 6-dimension quality check runs automatically. Any PII is masked for compliance. See the quality score here - 92% means it's ready for review.",
                "screen": "Quality dashboard",
            },
            {
                "time": "1:00-1:15",
                "action": "Human Decision",
                "script": "Now a human reviewer sees the claim with AI recommendations. They can approve, reject, or request more information. Full audit trail is maintained.",
                "screen": "Decisions page",
                "api_call": "POST /demo/claims/{id}/approve",
            },
            {
                "time": "1:15-1:30",
                "action": "Results & Audit",
                "script": "Done! The claim is approved. Every step is logged for EU AI Act compliance. You can export the full audit trail anytime.",
                "screen": "Audit export",
                "api_call": "GET /audit/export",
            },
        ],
        "key_features": [
            "Document extraction (PDF, images, scanned)",
            "PII detection with 99% accuracy",
            "6-dimension quality validation",
            "Human-in-the-loop decisions",
            "EU AI Act compliant audit logging",
            "Before/after KPI tracking",
        ],
    }
