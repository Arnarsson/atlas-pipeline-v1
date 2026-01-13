"""EU AI Act compliance assessment endpoints.

Provides API endpoints for assessing AI systems against EU AI Act requirements.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.compliance.eu_ai_act_mapper import EUAIActAssessor, AISystemArea, RiskLevel

router = APIRouter(prefix="/compliance", tags=["EU AI Act Compliance"])


class ComplianceAssessmentRequest(BaseModel):
    """Request for EU AI Act compliance assessment."""
    ai_system_name: str = Field(..., description="Name of the AI system")
    system_type: str = Field(
        ...,
        description="Type of AI system",
        examples=["classification", "detection", "assessment", "generation", "recommendation"]
    )
    areas: List[str] = Field(
        ...,
        description="Application areas (employment, education, credit, law_enforcement, migration_asylum, justice, healthcare, critical_infrastructure, other)"
    )
    affected_persons: int = Field(
        ...,
        description="Estimated number of persons affected by the AI system",
        ge=0
    )
    decision_type: Optional[str] = Field(
        None,
        description="Type of decisions made (e.g., recruitment, credit_scoring, diagnosis)"
    )
    has_human_review: bool = Field(
        False,
        description="Whether human oversight/review mechanism exists"
    )
    data_quality_score: Optional[float] = Field(
        None,
        description="Current data quality score (0-100)",
        ge=0,
        le=100
    )
    has_quality_gates: bool = Field(
        False,
        description="Whether quality gates are implemented"
    )
    has_audit_logging: bool = Field(
        False,
        description="Whether audit logging is enabled"
    )
    has_data_governance: bool = Field(
        False,
        description="Whether data governance framework exists"
    )
    has_technical_docs: bool = Field(
        False,
        description="Whether technical documentation exists"
    )
    has_risk_management: bool = Field(
        False,
        description="Whether risk management system is in place"
    )


class ArticleFinding(BaseModel):
    """Finding for a specific EU AI Act article."""
    article: str
    requirement: str
    status: str
    finding: str
    gaps: List[str] = []
    severity: str = "none"
    remediation: Optional[str] = None


class ComplianceAssessmentResponse(BaseModel):
    """Response from EU AI Act compliance assessment."""
    system_name: str
    risk_level: str
    compliance_status: str
    articles: dict
    required_actions: List[str]
    timeline_weeks: int
    recommendations: List[str]
    assessment_date: str
    assessment_version: str


@router.post("/eu-ai-act/assess", response_model=ComplianceAssessmentResponse)
async def assess_compliance(request: ComplianceAssessmentRequest):
    """
    Assess EU AI Act compliance for an AI system.

    This endpoint evaluates an AI system against the requirements of the
    EU AI Act (Regulation 2024/1689) and returns:

    - **Risk level**: prohibited, high, limited, or minimal
    - **Per-article compliance status**: Art. 5, 6, 9, 10, 11, 12, 14, 30
    - **Specific gaps**: What's missing for compliance
    - **Required actions**: Prioritized steps to achieve compliance
    - **Timeline**: Estimated weeks to compliance

    ## Risk Levels (Art. 6)

    - **Prohibited**: AI practices banned under Art. 5
    - **High-risk**: Systems in Annex III areas (employment, credit, law enforcement, etc.)
    - **Limited**: Systems with transparency obligations
    - **Minimal**: Low-risk systems with minimal obligations

    ## Articles Checked

    - **Art. 5**: Prohibited practices
    - **Art. 6**: High-risk classification
    - **Art. 9**: Risk management system
    - **Art. 10**: Data governance
    - **Art. 11**: Technical documentation
    - **Art. 12**: Logging and record-keeping
    - **Art. 14**: Human oversight
    - **Art. 30**: EU database registration
    """
    try:
        # Map string areas to enum
        areas = []
        for area in request.areas:
            try:
                areas.append(AISystemArea[area.upper()])
            except KeyError:
                # Try with underscore conversion
                area_key = area.upper().replace("-", "_").replace(" ", "_")
                try:
                    areas.append(AISystemArea[area_key])
                except KeyError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid area: {area}. Valid areas: {[a.value for a in AISystemArea]}"
                    )
    except HTTPException:
        raise

    # Perform assessment
    assessor = EUAIActAssessor()
    assessment = assessor.assess(
        system_name=request.ai_system_name,
        system_type=request.system_type,
        areas=areas,
        affected_persons=request.affected_persons,
        has_human_review=request.has_human_review,
        decision_type=request.decision_type,
        data_quality_score=request.data_quality_score,
        has_quality_gates=request.has_quality_gates,
        has_audit_logging=request.has_audit_logging,
        has_data_governance=request.has_data_governance,
        has_technical_docs=request.has_technical_docs,
        has_risk_management=request.has_risk_management
    )

    return ComplianceAssessmentResponse(
        system_name=request.ai_system_name,
        risk_level=assessment.risk_level.value,
        compliance_status=assessment.compliance_status,
        articles=assessment.articles,
        required_actions=assessment.required_actions,
        timeline_weeks=assessment.timeline_weeks,
        recommendations=assessment.recommendations,
        assessment_date=assessment.assessment_date.isoformat(),
        assessment_version=assessment.assessment_version
    )


@router.get("/eu-ai-act/risk-levels")
async def get_risk_levels():
    """
    Get explanation of EU AI Act risk levels.

    Returns detailed information about each risk level including:
    - Description
    - Examples
    - Requirements
    - Whether allowed
    """
    return {
        "prohibited": {
            "level": "prohibited",
            "description": "AI systems that create unacceptable risk to safety, livelihoods, and rights",
            "examples": [
                "Real-time remote biometric identification in public spaces",
                "Subliminal manipulation techniques",
                "Exploitation of vulnerable groups",
                "Social credit scoring by public authorities",
                "Biometric categorization inferring sensitive characteristics",
                "Untargeted scraping for facial recognition",
                "Emotion recognition in workplace/education",
                "Predictive policing based solely on profiling"
            ],
            "allowed": False,
            "article": "Article 5"
        },
        "high": {
            "level": "high",
            "description": "AI systems with significant impact on health, safety, or fundamental rights",
            "examples": [
                "Employment decisions (hiring, firing, promotion)",
                "Educational assessment and access",
                "Credit and insurance decisions",
                "Law enforcement applications",
                "Migration and border control",
                "Justice system applications",
                "Critical infrastructure management",
                "Medical device AI"
            ],
            "requirements": [
                "Risk management system (Art. 9)",
                "Data governance (Art. 10)",
                "Technical documentation (Art. 11)",
                "Logging for 5+ years (Art. 12)",
                "Transparency to users (Art. 13)",
                "Human oversight (Art. 14)",
                "Accuracy and robustness (Art. 15)",
                "EU database registration (Art. 30)"
            ],
            "allowed": True,
            "article": "Article 6, Annex III"
        },
        "limited": {
            "level": "limited",
            "description": "AI systems with specific transparency obligations",
            "examples": [
                "Chatbots (must disclose AI nature)",
                "Emotion recognition systems",
                "Biometric categorization systems",
                "AI-generated content (deepfakes)"
            ],
            "requirements": [
                "Transparency: inform users they're interacting with AI",
                "Disclose AI-generated content"
            ],
            "allowed": True,
            "article": "Article 50"
        },
        "minimal": {
            "level": "minimal",
            "description": "AI systems with minimal or no specific obligations",
            "examples": [
                "Spam filters",
                "Recommendation systems",
                "AI in video games",
                "Inventory management"
            ],
            "requirements": [
                "Voluntary codes of conduct encouraged",
                "No mandatory compliance requirements"
            ],
            "allowed": True,
            "article": "Article 95"
        }
    }


@router.get("/eu-ai-act/areas")
async def get_application_areas():
    """
    Get list of valid application areas for assessment.

    These areas correspond to the high-risk categories in Annex III of the EU AI Act.
    """
    return {
        "areas": [
            {
                "id": "employment",
                "name": "Employment",
                "description": "AI for recruitment, HR analytics, worker management",
                "examples": ["CV screening", "Interview assessment", "Performance monitoring"],
                "risk_level": "high",
                "annex_section": "Annex III, Section 4"
            },
            {
                "id": "education",
                "name": "Education",
                "description": "AI for educational access and assessment",
                "examples": ["Student assessment", "Proctoring", "Adaptive learning"],
                "risk_level": "high",
                "annex_section": "Annex III, Section 3"
            },
            {
                "id": "credit",
                "name": "Credit & Finance",
                "description": "AI for creditworthiness and financial decisions",
                "examples": ["Credit scoring", "Loan approval", "Insurance pricing"],
                "risk_level": "high",
                "annex_section": "Annex III, Section 5"
            },
            {
                "id": "law_enforcement",
                "name": "Law Enforcement",
                "description": "AI for law enforcement purposes",
                "examples": ["Predictive policing", "Evidence analysis", "Facial recognition"],
                "risk_level": "high",
                "annex_section": "Annex III, Section 6"
            },
            {
                "id": "migration_asylum",
                "name": "Migration & Asylum",
                "description": "AI for border control and asylum processing",
                "examples": ["Border control", "Visa assessment", "Asylum application processing"],
                "risk_level": "high",
                "annex_section": "Annex III, Section 7"
            },
            {
                "id": "justice",
                "name": "Justice & Democracy",
                "description": "AI for judicial and democratic processes",
                "examples": ["Sentencing assistance", "Case prioritization", "Recidivism prediction"],
                "risk_level": "high",
                "annex_section": "Annex III, Section 8"
            },
            {
                "id": "healthcare",
                "name": "Healthcare",
                "description": "AI for medical diagnosis and treatment",
                "examples": ["Diagnostic AI", "Treatment recommendation", "Triage systems"],
                "risk_level": "high",
                "annex_section": "Annex III, Section 1 (as medical devices)"
            },
            {
                "id": "critical_infrastructure",
                "name": "Critical Infrastructure",
                "description": "AI for managing critical infrastructure",
                "examples": ["Energy grid management", "Water supply", "Transport control"],
                "risk_level": "high",
                "annex_section": "Annex III, Section 2"
            },
            {
                "id": "other",
                "name": "Other",
                "description": "Other AI applications",
                "examples": ["Recommendation systems", "Content moderation", "Customer service"],
                "risk_level": "minimal_to_limited",
                "annex_section": "N/A"
            }
        ]
    }


@router.get("/eu-ai-act/articles")
async def get_articles_overview():
    """
    Get overview of key EU AI Act articles.

    Returns summary of articles relevant to AI system compliance.
    """
    return {
        "articles": [
            {
                "article": "Art. 5",
                "title": "Prohibited AI Practices",
                "summary": "Lists AI practices that are completely prohibited",
                "applies_to": "All AI systems",
                "key_requirements": ["No subliminal manipulation", "No exploitation of vulnerabilities", "No social scoring"]
            },
            {
                "article": "Art. 6",
                "title": "Classification of High-Risk AI",
                "summary": "Defines which AI systems are high-risk based on Annex III",
                "applies_to": "AI in listed areas",
                "key_requirements": ["Determine risk classification", "Apply appropriate requirements"]
            },
            {
                "article": "Art. 9",
                "title": "Risk Management System",
                "summary": "Requires continuous risk identification and mitigation",
                "applies_to": "High-risk AI",
                "key_requirements": ["Identify risks", "Estimate risks", "Evaluate risks", "Adopt measures", "Test measures"]
            },
            {
                "article": "Art. 10",
                "title": "Data and Data Governance",
                "summary": "Requirements for training, validation, and testing data",
                "applies_to": "High-risk AI",
                "key_requirements": ["Data governance", "Data quality", "Bias examination", "Representative data"]
            },
            {
                "article": "Art. 11",
                "title": "Technical Documentation",
                "summary": "Documentation requirements before market placement",
                "applies_to": "High-risk AI",
                "key_requirements": ["System description", "Design specifications", "Performance metrics", "Limitations"]
            },
            {
                "article": "Art. 12",
                "title": "Record-Keeping",
                "summary": "Logging and traceability requirements",
                "applies_to": "High-risk AI",
                "key_requirements": ["Automatic logging", "Input/output recording", "5+ year retention"]
            },
            {
                "article": "Art. 14",
                "title": "Human Oversight",
                "summary": "Human oversight and intervention capability",
                "applies_to": "High-risk AI",
                "key_requirements": ["Oversight mechanism", "Intervention capability", "Override ability"]
            },
            {
                "article": "Art. 30",
                "title": "EU Database Registration",
                "summary": "Registration in public EU AI database",
                "applies_to": "High-risk AI",
                "key_requirements": ["Register before deployment", "Update for modifications"]
            }
        ],
        "enforcement_dates": {
            "prohibited_practices": "February 2, 2025",
            "gpai_codes": "August 2, 2025",
            "high_risk_full": "August 2, 2026",
            "annex_iii_updates": "August 2, 2027"
        }
    }


@router.get("/eu-ai-act/quick-check")
async def quick_compliance_check(
    area: str,
    affected_persons: int = 100,
    has_human_oversight: bool = False
):
    """
    Quick compliance check based on application area.

    This is a simplified check - use /assess for full assessment.
    """
    try:
        system_area = AISystemArea[area.upper().replace("-", "_").replace(" ", "_")]
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid area. Valid: {[a.value for a in AISystemArea]}"
        )

    # Quick risk determination
    high_risk_areas = [
        AISystemArea.LAW_ENFORCEMENT,
        AISystemArea.JUSTICE,
        AISystemArea.MIGRATION,
        AISystemArea.CRITICAL_INFRASTRUCTURE
    ]

    if system_area in high_risk_areas:
        risk = "high"
    elif system_area in [AISystemArea.EMPLOYMENT, AISystemArea.EDUCATION, AISystemArea.CREDIT, AISystemArea.HEALTHCARE]:
        risk = "high" if affected_persons >= 1000 else "limited"
    else:
        risk = "minimal"

    return {
        "area": area,
        "risk_level": risk,
        "affected_persons": affected_persons,
        "has_human_oversight": has_human_oversight,
        "quick_verdict": {
            "high": "⚠️ HIGH-RISK: Full compliance with Art. 9-15, 30 required",
            "limited": "📋 LIMITED-RISK: Transparency requirements apply",
            "minimal": "✅ MINIMAL-RISK: Voluntary compliance recommended"
        }[risk],
        "next_step": "Use POST /compliance/eu-ai-act/assess for full assessment"
    }
