"""EU AI Act Article Mapping Engine.

Provides compliance assessment for EU AI Act (Regulation 2024/1689).
Assesses AI systems against Articles 5, 6, 9, 10, 11, 12, and 30.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


class RiskLevel(str, Enum):
    """Risk levels per EU AI Act Art. 6."""
    PROHIBITED = "prohibited"
    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"


class AISystemArea(str, Enum):
    """Areas from Annex III (high-risk systems)."""
    EMPLOYMENT = "employment"
    EDUCATION = "education"
    CREDIT = "credit"
    LAW_ENFORCEMENT = "law_enforcement"
    MIGRATION = "migration_asylum"
    JUSTICE = "justice"
    HEALTHCARE = "healthcare"
    CRITICAL_INFRASTRUCTURE = "critical_infrastructure"
    OTHER = "other"


@dataclass
class ComplianceGap:
    """Single compliance gap."""
    article: str  # e.g., "Art. 10"
    requirement: str  # What the law requires
    finding: str  # What was found
    gaps: List[str] = field(default_factory=list)  # Specific gaps
    severity: str = "medium"  # "critical" | "high" | "medium" | "low"
    remediation: str = ""  # How to fix it


@dataclass
class ComplianceAssessment:
    """Full compliance assessment."""
    risk_level: RiskLevel
    compliance_status: str  # "compliant" | "gaps_found" | "non_compliant"
    articles: dict  # Per-article findings
    required_actions: List[str]
    timeline_weeks: int
    recommendations: List[str]
    assessment_date: datetime = field(default_factory=datetime.now)
    assessment_version: str = "1.0.0"


class EUAIActAssessor:
    """Assess compliance with EU AI Act (Regulation 2024/1689)."""

    def __init__(self):
        self.prohibited_practices = [
            "Real-time facial recognition in public spaces (without exemption)",
            "Subliminal manipulation techniques",
            "Exploiting vulnerabilities of specific groups",
            "Social credit scoring by public authorities",
            "Biometric categorization inferring sensitive characteristics",
            "Untargeted scraping for facial recognition databases",
            "Emotion recognition in workplace/education (without safety justification)",
            "Predictive policing based solely on profiling"
        ]

        self.high_risk_areas = {
            AISystemArea.EMPLOYMENT: [
                "recruitment", "dismissal", "promotion", "performance_monitoring",
                "task_allocation", "hr_analytics"
            ],
            AISystemArea.EDUCATION: [
                "student_assessment", "access_to_education", "learning_analytics",
                "proctoring", "adaptive_learning"
            ],
            AISystemArea.CREDIT: [
                "lending_decision", "loan_approval", "credit_scoring",
                "insurance_pricing", "risk_assessment"
            ],
            AISystemArea.LAW_ENFORCEMENT: [
                "detection", "assessment", "predictive_policing",
                "facial_recognition", "evidence_analysis"
            ],
            AISystemArea.MIGRATION: [
                "border_control", "asylum_processing", "visa_assessment",
                "identity_verification"
            ],
            AISystemArea.JUSTICE: [
                "criminal_sentencing", "pre_trial_assessment",
                "recidivism_prediction", "case_prioritization"
            ],
            AISystemArea.HEALTHCARE: [
                "diagnosis", "treatment_recommendation", "triage",
                "medical_device_control"
            ],
            AISystemArea.CRITICAL_INFRASTRUCTURE: [
                "energy_management", "water_supply", "transport_control",
                "digital_infrastructure"
            ]
        }

        # Article requirements for high-risk systems
        self.high_risk_requirements = {
            "article_9": "Risk management system throughout lifecycle",
            "article_10": "Data governance for training, validation, testing datasets",
            "article_11": "Technical documentation before market placement",
            "article_12": "Automatic logging of events during operation",
            "article_13": "Transparency and provision of information to users",
            "article_14": "Human oversight measures",
            "article_15": "Accuracy, robustness and cybersecurity"
        }

    def assess(
        self,
        system_name: str,
        system_type: str,  # "classification", "detection", "assessment", "generation"
        areas: List[AISystemArea],
        affected_persons: int,
        has_human_review: bool,
        decision_type: Optional[str] = None,
        data_quality_score: Optional[float] = None,
        has_quality_gates: bool = False,
        has_audit_logging: bool = False,
        has_data_governance: bool = False,
        has_technical_docs: bool = False,
        has_risk_management: bool = False
    ) -> ComplianceAssessment:
        """
        Assess EU AI Act compliance.

        Args:
            system_name: Name of the AI system
            system_type: Type of AI system
            areas: Application areas (employment, credit, etc.)
            affected_persons: Number of people affected
            has_human_review: Whether human oversight exists
            decision_type: Type of decisions made
            data_quality_score: Current data quality score (0-100)
            has_quality_gates: Whether quality gates are in place
            has_audit_logging: Whether audit logging is enabled
            has_data_governance: Whether data governance framework exists
            has_technical_docs: Whether technical documentation exists
            has_risk_management: Whether risk management system exists

        Returns:
            ComplianceAssessment with gaps and recommendations
        """
        # Step 1: Check for prohibited practices (Art. 5)
        article_5 = self._check_article_5(system_type, areas, decision_type)
        if article_5.get("status") == "prohibited":
            return ComplianceAssessment(
                risk_level=RiskLevel.PROHIBITED,
                compliance_status="prohibited",
                articles={"article_5": article_5},
                required_actions=["STOP: This AI system is prohibited under EU AI Act"],
                timeline_weeks=0,
                recommendations=["Cease development and deployment immediately",
                               "Seek legal counsel for alternative approaches"]
            )

        # Step 2: Determine risk level (Art. 6)
        risk_level = self._determine_risk_level(areas, affected_persons, decision_type)

        # Step 3: Check each article based on risk level
        articles = {
            "article_5": article_5,
            "article_6": self._check_article_6(risk_level, areas, affected_persons),
        }

        # For high/limited risk, check additional articles
        if risk_level in [RiskLevel.HIGH, RiskLevel.LIMITED]:
            articles.update({
                "article_9": self._check_article_9(has_risk_management),
                "article_10": self._check_article_10(has_data_governance, data_quality_score),
                "article_11": self._check_article_11(has_technical_docs),
                "article_12": self._check_article_12(has_audit_logging),
                "article_14": self._check_article_14(has_human_review),
                "article_30": self._check_article_30(risk_level),
            })

        # Step 4: Collect all gaps
        all_gaps = []
        critical_gaps = []
        high_gaps = []

        for article, finding in articles.items():
            if finding.get("status") not in ["compliant", "not_applicable"]:
                gaps = finding.get("gaps", [])
                all_gaps.extend(gaps)
                severity = finding.get("severity", "medium")
                if severity == "critical":
                    critical_gaps.extend(gaps)
                elif severity == "high":
                    high_gaps.extend(gaps)

        # Step 5: Determine overall compliance status
        if critical_gaps:
            compliance_status = "non_compliant"
        elif all_gaps:
            compliance_status = "gaps_found"
        else:
            compliance_status = "compliant"

        # Step 6: Calculate timeline
        timeline_weeks = self._calculate_timeline(all_gaps, critical_gaps, risk_level)

        # Step 7: Generate actions and recommendations
        required_actions = self._generate_actions(articles, all_gaps, critical_gaps)
        recommendations = self._generate_recommendations(risk_level, all_gaps, affected_persons)

        return ComplianceAssessment(
            risk_level=risk_level,
            compliance_status=compliance_status,
            articles=articles,
            required_actions=required_actions,
            timeline_weeks=timeline_weeks,
            recommendations=recommendations
        )

    def _determine_risk_level(
        self,
        areas: List[AISystemArea],
        affected_persons: int,
        decision_type: Optional[str]
    ) -> RiskLevel:
        """Determine risk level per Art. 6 and Annex III."""
        # High-risk areas from Annex III
        high_risk_areas = [
            AISystemArea.LAW_ENFORCEMENT,
            AISystemArea.JUSTICE,
            AISystemArea.MIGRATION,
            AISystemArea.CRITICAL_INFRASTRUCTURE
        ]

        for area in areas:
            if area in high_risk_areas:
                return RiskLevel.HIGH

        # Employment, education, credit with significant impact
        significant_impact_areas = [
            AISystemArea.EMPLOYMENT,
            AISystemArea.EDUCATION,
            AISystemArea.CREDIT,
            AISystemArea.HEALTHCARE
        ]

        for area in areas:
            if area in significant_impact_areas:
                # Scale triggers high-risk
                if affected_persons >= 1000:
                    return RiskLevel.HIGH
                return RiskLevel.LIMITED

        # Default to limited for any AI system with moderate scale
        if affected_persons >= 5000:
            return RiskLevel.LIMITED

        return RiskLevel.MINIMAL

    def _check_article_5(
        self,
        system_type: str,
        areas: List[AISystemArea],
        decision_type: Optional[str]
    ) -> dict:
        """Check prohibited practices (Art. 5)."""
        prohibited_indicators = []

        # Check for prohibited patterns
        if system_type == "biometric" and AISystemArea.LAW_ENFORCEMENT in areas:
            prohibited_indicators.append("Real-time biometric identification in public spaces")

        if decision_type in ["social_scoring", "social_credit"]:
            prohibited_indicators.append("Social credit scoring system")

        if decision_type == "emotion_recognition" and \
           (AISystemArea.EMPLOYMENT in areas or AISystemArea.EDUCATION in areas):
            prohibited_indicators.append("Emotion recognition in workplace/education")

        if prohibited_indicators:
            return {
                "article": "Art. 5",
                "requirement": "Prohibited AI practices",
                "status": "prohibited",
                "finding": "Potential prohibited practices detected",
                "gaps": prohibited_indicators,
                "severity": "critical",
                "remediation": "Immediately cease development and seek legal review"
            }

        return {
            "article": "Art. 5",
            "requirement": "Prohibited AI practices",
            "status": "compliant",
            "finding": "No prohibited practices detected",
            "severity": "none"
        }

    def _check_article_6(
        self,
        risk_level: RiskLevel,
        areas: List[AISystemArea],
        affected_persons: int
    ) -> dict:
        """Check high-risk AI classification (Art. 6)."""
        area_names = [a.value for a in areas]

        if risk_level == RiskLevel.HIGH:
            return {
                "article": "Art. 6",
                "requirement": "High-risk AI system classification",
                "status": "high_risk_identified",
                "finding": f"HIGH-RISK: Areas {area_names}, affects {affected_persons:,} persons",
                "gaps": [
                    "Must comply with Chapter 2 requirements (Art. 9-15)",
                    "Registration in EU database required (Art. 30)",
                    "Conformity assessment required before deployment"
                ],
                "severity": "critical"
            }
        elif risk_level == RiskLevel.LIMITED:
            return {
                "article": "Art. 6",
                "requirement": "Risk classification",
                "status": "limited_risk",
                "finding": f"LIMITED-RISK: Areas {area_names}",
                "gaps": ["Transparency requirements apply"],
                "severity": "medium"
            }
        else:
            return {
                "article": "Art. 6",
                "requirement": "Risk classification",
                "status": "minimal_risk",
                "finding": "MINIMAL-RISK: Standard obligations apply",
                "severity": "low"
            }

    def _check_article_9(self, has_risk_management: bool) -> dict:
        """Check risk management system (Art. 9)."""
        gaps = []
        if not has_risk_management:
            gaps = [
                "Establish risk management system",
                "Identify and analyze known/foreseeable risks",
                "Estimate and evaluate risks from intended use",
                "Evaluate risks from reasonably foreseeable misuse",
                "Adopt suitable risk management measures",
                "Test risk management measures"
            ]

        return {
            "article": "Art. 9",
            "requirement": "Risk management system",
            "status": "gaps_found" if gaps else "compliant",
            "finding": "Risk management system required throughout AI lifecycle",
            "gaps": gaps,
            "severity": "high" if gaps else "none",
            "remediation": "Implement continuous risk identification and mitigation process"
        }

    def _check_article_10(
        self,
        has_governance: bool,
        data_quality_score: Optional[float]
    ) -> dict:
        """Check data governance (Art. 10)."""
        gaps = []

        if not has_governance:
            gaps.extend([
                "Define data governance policies",
                "Assign data owners for all AI training data",
                "Implement access control policies",
                "Document data collection processes",
                "Establish data quality standards"
            ])

        if data_quality_score is not None and data_quality_score < 80:
            gaps.extend([
                f"Improve data quality (current: {data_quality_score}%, required: ≥80%)",
                "Implement bias detection and mitigation",
                "Ensure training data is relevant and representative"
            ])
        elif data_quality_score is None:
            gaps.append("Measure and document data quality metrics")

        return {
            "article": "Art. 10",
            "requirement": "Data and data governance",
            "status": "gaps_found" if gaps else "compliant",
            "finding": "Training, validation and testing data must meet quality criteria",
            "gaps": gaps,
            "severity": "high" if gaps else "none",
            "remediation": "Implement comprehensive data governance framework per Art. 10"
        }

    def _check_article_11(self, has_technical_docs: bool) -> dict:
        """Check technical documentation (Art. 11)."""
        gaps = []
        if not has_technical_docs:
            gaps = [
                "Document general description and intended purpose",
                "Document system architecture and design",
                "Document training data characteristics",
                "Document model evaluation methodology",
                "Document performance metrics and benchmarks",
                "Document known limitations and risks",
                "Document instructions for use"
            ]

        return {
            "article": "Art. 11",
            "requirement": "Technical documentation",
            "status": "gaps_found" if gaps else "compliant",
            "finding": "Technical documentation must be prepared before market placement",
            "gaps": gaps,
            "severity": "high" if gaps else "none",
            "remediation": "Generate comprehensive technical documentation per Annex IV"
        }

    def _check_article_12(self, has_logging: bool) -> dict:
        """Check logging requirements (Art. 12)."""
        gaps = []
        if not has_logging:
            gaps = [
                "Enable automatic event logging",
                "Log input data (or references)",
                "Log system outputs and decisions",
                "Log operating period start/stop",
                "Log human oversight actions",
                "Implement 5+ year retention policy",
                "Ensure logs are tamper-evident"
            ]

        return {
            "article": "Art. 12",
            "requirement": "Record-keeping (Logging)",
            "status": "gaps_found" if gaps else "compliant",
            "finding": "Automatic logging of events required for traceability",
            "gaps": gaps,
            "severity": "high" if gaps else "none",
            "remediation": "Implement comprehensive audit logging with 5+ year retention"
        }

    def _check_article_14(self, has_human_review: bool) -> dict:
        """Check human oversight (Art. 14)."""
        gaps = []
        if not has_human_review:
            gaps = [
                "Implement human oversight mechanism",
                "Enable operators to understand AI capabilities/limitations",
                "Allow operators to monitor AI operation",
                "Enable intervention/interruption capability",
                "Provide decision override mechanism"
            ]

        return {
            "article": "Art. 14",
            "requirement": "Human oversight",
            "status": "gaps_found" if gaps else "compliant",
            "finding": "Human oversight measures required for high-risk AI",
            "gaps": gaps,
            "severity": "critical" if gaps else "none",
            "remediation": "Implement human-in-the-loop or human-on-the-loop oversight"
        }

    def _check_article_30(self, risk_level: RiskLevel) -> dict:
        """Check registration requirements (Art. 30)."""
        if risk_level == RiskLevel.HIGH:
            return {
                "article": "Art. 30",
                "requirement": "EU database registration",
                "status": "action_required",
                "finding": "HIGH-RISK system must be registered in EU database",
                "gaps": [
                    "Prepare registration information",
                    "Register in EU AI database before deployment",
                    "Update registration for substantial modifications"
                ],
                "severity": "critical",
                "remediation": "Register system at https://ai-system-registration.ec.europa.eu"
            }
        return {
            "article": "Art. 30",
            "requirement": "EU database registration",
            "status": "not_applicable",
            "finding": "Registration not required for this risk level",
            "severity": "none"
        }

    def _calculate_timeline(
        self,
        all_gaps: List[str],
        critical_gaps: List[str],
        risk_level: RiskLevel
    ) -> int:
        """Calculate estimated timeline to compliance in weeks."""
        if not all_gaps:
            return 0

        # Base calculation
        base_weeks = len(all_gaps) // 2 + 1  # ~2 gaps per week

        # Critical gaps add more time
        base_weeks += len(critical_gaps)

        # Risk level multiplier
        if risk_level == RiskLevel.HIGH:
            base_weeks = int(base_weeks * 1.5)

        # Reasonable bounds
        return max(4, min(base_weeks, 24))

    def _generate_actions(
        self,
        articles: dict,
        all_gaps: List[str],
        critical_gaps: List[str]
    ) -> List[str]:
        """Generate prioritized required actions."""
        actions = []

        # Critical actions first
        if critical_gaps:
            actions.append("🔴 URGENT: Address critical compliance gaps immediately")

        # Per-article actions
        for article_id, finding in articles.items():
            if finding.get("status") not in ["compliant", "not_applicable"]:
                article_num = article_id.replace("article_", "Art. ")
                if finding.get("severity") == "critical":
                    actions.append(f"[CRITICAL] {article_num}: {finding.get('remediation', 'Address gaps')}")
                elif finding.get("severity") == "high":
                    actions.append(f"[HIGH] {article_num}: {finding.get('remediation', 'Address gaps')}")
                else:
                    actions.append(f"{article_num}: {finding.get('remediation', 'Address gaps')}")

        # Generic actions based on gaps
        if any("governance" in g.lower() for g in all_gaps):
            actions.append("Establish data governance framework with defined ownership")
        if any("logging" in g.lower() or "audit" in g.lower() for g in all_gaps):
            actions.append("Implement comprehensive audit logging system")
        if any("documentation" in g.lower() for g in all_gaps):
            actions.append("Generate technical documentation per Annex IV")

        return actions

    def _generate_recommendations(
        self,
        risk_level: RiskLevel,
        gaps: List[str],
        affected_persons: int
    ) -> List[str]:
        """Generate recommendations based on assessment."""
        recommendations = []

        if risk_level == RiskLevel.HIGH:
            recommendations.extend([
                "Engage legal counsel familiar with EU AI Act",
                "Appoint AI compliance officer or team",
                "Plan for conformity assessment before deployment",
                "Budget for ongoing compliance monitoring"
            ])
            if affected_persons >= 10000:
                recommendations.append("Consider impact assessment for large-scale deployment")

        elif risk_level == RiskLevel.LIMITED:
            recommendations.extend([
                "Document transparency measures",
                "Prepare user-facing disclosures about AI use",
                "Review regularly for potential high-risk classification"
            ])

        # Gap-specific recommendations
        if gaps:
            recommendations.append(f"Address {len(gaps)} identified gaps systematically")
            recommendations.append("Prioritize critical and high-severity gaps first")

        # Timeline-based
        if len(gaps) > 10:
            recommendations.append("Consider phased compliance approach over 2-3 months")
        elif len(gaps) > 5:
            recommendations.append("Plan 4-6 week compliance sprint")

        return recommendations
