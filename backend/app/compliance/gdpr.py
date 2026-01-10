"""
Atlas GDPR Workflows
====================

GDPR compliance workflows for data subject rights.

Features:
- Right to Access (Article 15): Export all data for a subject
- Right to Deletion (Article 17): Delete all PII for a subject
- Right to Rectification (Article 16): Update PII across datasets
- Consent Management: Track consent status and purpose
- Audit Trail: Log all GDPR operations

Reference: GDPR Articles 15-17, 30 (Record of Processing Activities)
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


# ============================================================================
# Models
# ============================================================================


class GDPRRequestType(str, Enum):
    """GDPR request types."""

    ACCESS = "access"  # Article 15
    DELETION = "deletion"  # Article 17 (Right to be forgotten)
    RECTIFICATION = "rectification"  # Article 16
    PORTABILITY = "portability"  # Article 20
    RESTRICTION = "restriction"  # Article 18


class GDPRRequestStatus(str, Enum):
    """GDPR request processing status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConsentStatus(str, Enum):
    """Consent status for data subject."""

    GRANTED = "granted"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    NOT_REQUIRED = "not_required"


class IdentifierType(str, Enum):
    """Types of identifiers for data subjects."""

    EMAIL = "email"
    PHONE = "phone"
    CPR = "cpr"  # Danish CPR number
    SSN = "ssn"  # Social Security Number
    CUSTOMER_ID = "customer_id"
    USER_ID = "user_id"


@dataclass
class DataSubject:
    """Data subject information."""

    subject_id: str
    identifier_type: IdentifierType
    identifier_value: str
    consent_status: ConsentStatus
    consent_date: datetime | None = None
    consent_purpose: list[str] | None = None
    created_at: datetime | None = None


@dataclass
class GDPRRequest:
    """GDPR request information."""

    request_id: str
    subject_id: str
    request_type: GDPRRequestType
    status: GDPRRequestStatus
    requested_at: datetime
    completed_at: datetime | None = None
    processed_by: str | None = None
    result: dict[str, Any] | None = None
    error_message: str | None = None


@dataclass
class AuditLogEntry:
    """Audit log entry for GDPR operations."""

    log_id: str
    subject_id: str
    operation: str
    performed_by: str
    timestamp: datetime
    details: dict[str, Any]
    ip_address: str | None = None


# ============================================================================
# GDPR Workflow Manager
# ============================================================================


class GDPRWorkflowManager:
    """
    GDPR workflow manager for data subject rights.

    Handles:
    - Data subject registration
    - Consent management
    - Right to access (export)
    - Right to deletion
    - Right to rectification
    - Audit logging
    """

    def __init__(self):
        """Initialize GDPR workflow manager (in-memory for Week 5-6)."""
        # In-memory storage (Week 5-6 simple version)
        # Week 7+ will add database persistence
        self.data_subjects: dict[str, DataSubject] = {}
        self.gdpr_requests: dict[str, GDPRRequest] = {}
        self.audit_logs: list[AuditLogEntry] = []

        logger.info("Initialized GDPRWorkflowManager (in-memory mode)")

    def register_data_subject(
        self,
        identifier_type: IdentifierType,
        identifier_value: str,
        consent_status: ConsentStatus = ConsentStatus.NOT_REQUIRED,
        consent_purpose: list[str] | None = None,
    ) -> DataSubject:
        """
        Register a data subject.

        Args:
            identifier_type: Type of identifier
            identifier_value: Identifier value (email, phone, etc.)
            consent_status: Initial consent status
            consent_purpose: Purpose of data processing

        Returns:
            DataSubject instance
        """
        subject_id = str(uuid4())

        subject = DataSubject(
            subject_id=subject_id,
            identifier_type=identifier_type,
            identifier_value=identifier_value,
            consent_status=consent_status,
            consent_date=datetime.utcnow() if consent_status == ConsentStatus.GRANTED else None,
            consent_purpose=consent_purpose or [],
            created_at=datetime.utcnow(),
        )

        self.data_subjects[subject_id] = subject

        # Log registration
        self._log_audit_event(
            subject_id=subject_id,
            operation="register_subject",
            performed_by="system",
            details={
                "identifier_type": identifier_type,
                "consent_status": consent_status,
            },
        )

        logger.info(
            f"Registered data subject: {identifier_type}={identifier_value}, "
            f"subject_id={subject_id}"
        )

        return subject

    def find_data_subject(
        self, identifier_type: IdentifierType, identifier_value: str
    ) -> DataSubject | None:
        """
        Find data subject by identifier.

        Args:
            identifier_type: Type of identifier
            identifier_value: Identifier value

        Returns:
            DataSubject or None if not found
        """
        for subject in self.data_subjects.values():
            if (
                subject.identifier_type == identifier_type
                and subject.identifier_value == identifier_value
            ):
                return subject
        return None

    def update_consent(
        self,
        subject_id: str,
        consent_status: ConsentStatus,
        consent_purpose: list[str] | None = None,
        performed_by: str = "system",
    ):
        """
        Update consent status for a data subject.

        Args:
            subject_id: Data subject ID
            consent_status: New consent status
            consent_purpose: Purpose of data processing
            performed_by: User or system performing the update
        """
        subject = self.data_subjects.get(subject_id)
        if not subject:
            raise ValueError(f"Data subject {subject_id} not found")

        old_status = subject.consent_status
        subject.consent_status = consent_status
        subject.consent_date = (
            datetime.utcnow() if consent_status == ConsentStatus.GRANTED else None
        )

        if consent_purpose:
            subject.consent_purpose = consent_purpose

        # Log consent change
        self._log_audit_event(
            subject_id=subject_id,
            operation="update_consent",
            performed_by=performed_by,
            details={
                "old_status": old_status,
                "new_status": consent_status,
                "purpose": consent_purpose,
            },
        )

        logger.info(
            f"Updated consent for subject {subject_id}: {old_status} -> {consent_status}"
        )

    def request_data_access(
        self, subject_identifier: str, identifier_type: IdentifierType = IdentifierType.EMAIL
    ) -> dict[str, Any]:
        """
        Handle Right to Access (GDPR Article 15).

        Export all data for a data subject.

        Args:
            subject_identifier: Subject identifier (email, phone, etc.)
            identifier_type: Type of identifier

        Returns:
            Dictionary with all data for the subject
        """
        logger.info(
            f"Processing Right to Access request for {identifier_type}={subject_identifier}"
        )

        # Find or create data subject
        subject = self.find_data_subject(identifier_type, subject_identifier)
        if not subject:
            subject = self.register_data_subject(
                identifier_type=identifier_type,
                identifier_value=subject_identifier,
            )

        # Create GDPR request
        request_id = str(uuid4())
        gdpr_request = GDPRRequest(
            request_id=request_id,
            subject_id=subject.subject_id,
            request_type=GDPRRequestType.ACCESS,
            status=GDPRRequestStatus.IN_PROGRESS,
            requested_at=datetime.utcnow(),
        )
        self.gdpr_requests[request_id] = gdpr_request

        try:
            # In production, this would:
            # 1. Search all layers (explore, chart, navigate) for subject data
            # 2. Collect all records containing PII
            # 3. Include quality metrics and processing history
            # 4. Format as JSON with schema documentation

            # Simulated export data
            export_data = {
                "subject_id": subject.subject_id,
                "identifier": {
                    "type": identifier_type,
                    "value": subject_identifier,
                },
                "consent": {
                    "status": subject.consent_status,
                    "date": subject.consent_date.isoformat() if subject.consent_date else None,
                    "purpose": subject.consent_purpose,
                },
                "data": {
                    "explore_layer": {
                        "tables": ["raw_data"],
                        "records_found": 0,
                        "data": [],
                    },
                    "chart_layer": {
                        "tables": ["validated_data"],
                        "records_found": 0,
                        "data": [],
                    },
                    "navigate_layer": {
                        "tables": ["business_metrics"],
                        "records_found": 0,
                        "data": [],
                    },
                },
                "processing_history": {
                    "pipeline_runs": [],
                    "quality_checks": [],
                    "pii_detections": [],
                },
                "exported_at": datetime.utcnow().isoformat(),
            }

            # Update request status
            gdpr_request.status = GDPRRequestStatus.COMPLETED
            gdpr_request.completed_at = datetime.utcnow()
            gdpr_request.processed_by = "system"
            gdpr_request.result = export_data

            # Log access request
            self._log_audit_event(
                subject_id=subject.subject_id,
                operation="data_access",
                performed_by="system",
                details={
                    "request_id": request_id,
                    "records_exported": 0,
                },
            )

            logger.info(
                f"Right to Access completed for subject {subject.subject_id}, "
                f"request_id={request_id}"
            )

            return export_data

        except Exception as e:
            logger.error(f"Right to Access failed: {e}")
            gdpr_request.status = GDPRRequestStatus.FAILED
            gdpr_request.error_message = str(e)
            raise

    def request_data_deletion(
        self,
        subject_identifier: str,
        identifier_type: IdentifierType = IdentifierType.EMAIL,
        reason: str = "User request",
        performed_by: str = "system",
    ) -> dict[str, int]:
        """
        Handle Right to Deletion (GDPR Article 17 - Right to be forgotten).

        Delete all PII for a data subject across all layers.

        Args:
            subject_identifier: Subject identifier (email, phone, etc.)
            identifier_type: Type of identifier
            reason: Reason for deletion
            performed_by: User or system performing deletion

        Returns:
            Dictionary with deletion counts per layer
        """
        logger.info(
            f"Processing Right to Deletion request for {identifier_type}={subject_identifier}"
        )

        # Find data subject
        subject = self.find_data_subject(identifier_type, subject_identifier)
        if not subject:
            logger.warning(f"Data subject not found: {subject_identifier}")
            return {"error": "Data subject not found"}

        # Create GDPR request
        request_id = str(uuid4())
        gdpr_request = GDPRRequest(
            request_id=request_id,
            subject_id=subject.subject_id,
            request_type=GDPRRequestType.DELETION,
            status=GDPRRequestStatus.IN_PROGRESS,
            requested_at=datetime.utcnow(),
        )
        self.gdpr_requests[request_id] = gdpr_request

        try:
            # In production, this would:
            # 1. Find all records containing subject PII
            # 2. Delete from navigate layer (business data)
            # 3. Delete from chart layer (validated data)
            # 4. Mark as deleted in explore layer (retain for audit)
            # 5. Log deletion in audit trail

            # Simulated deletion counts
            deletion_counts = {
                "explore_layer": 0,
                "chart_layer": 0,
                "navigate_layer": 0,
                "total": 0,
            }

            # Update request status
            gdpr_request.status = GDPRRequestStatus.COMPLETED
            gdpr_request.completed_at = datetime.utcnow()
            gdpr_request.processed_by = performed_by
            gdpr_request.result = deletion_counts

            # Log deletion request
            self._log_audit_event(
                subject_id=subject.subject_id,
                operation="data_deletion",
                performed_by=performed_by,
                details={
                    "request_id": request_id,
                    "reason": reason,
                    "deletion_counts": deletion_counts,
                },
            )

            # Update subject consent to withdrawn
            subject.consent_status = ConsentStatus.WITHDRAWN

            logger.info(
                f"Right to Deletion completed for subject {subject.subject_id}, "
                f"request_id={request_id}, deleted={deletion_counts['total']} records"
            )

            return deletion_counts

        except Exception as e:
            logger.error(f"Right to Deletion failed: {e}")
            gdpr_request.status = GDPRRequestStatus.FAILED
            gdpr_request.error_message = str(e)
            raise

    def request_data_rectification(
        self,
        subject_identifier: str,
        updates: dict[str, Any],
        identifier_type: IdentifierType = IdentifierType.EMAIL,
        performed_by: str = "system",
    ) -> dict[str, int]:
        """
        Handle Right to Rectification (GDPR Article 16).

        Update PII across all datasets for a data subject.

        Args:
            subject_identifier: Subject identifier
            updates: Dictionary of fields to update
            identifier_type: Type of identifier
            performed_by: User or system performing update

        Returns:
            Dictionary with update counts per layer
        """
        logger.info(
            f"Processing Right to Rectification request for {identifier_type}={subject_identifier}"
        )

        # Find data subject
        subject = self.find_data_subject(identifier_type, subject_identifier)
        if not subject:
            logger.warning(f"Data subject not found: {subject_identifier}")
            return {"error": "Data subject not found"}

        # Create GDPR request
        request_id = str(uuid4())
        gdpr_request = GDPRRequest(
            request_id=request_id,
            subject_id=subject.subject_id,
            request_type=GDPRRequestType.RECTIFICATION,
            status=GDPRRequestStatus.IN_PROGRESS,
            requested_at=datetime.utcnow(),
        )
        self.gdpr_requests[request_id] = gdpr_request

        try:
            # In production, this would:
            # 1. Find all records containing subject PII
            # 2. Update fields in navigate layer
            # 3. Update fields in chart layer
            # 4. Update fields in explore layer
            # 5. Log updates in audit trail

            # Simulated update counts
            update_counts = {
                "explore_layer": 0,
                "chart_layer": 0,
                "navigate_layer": 0,
                "total": 0,
            }

            # Update request status
            gdpr_request.status = GDPRRequestStatus.COMPLETED
            gdpr_request.completed_at = datetime.utcnow()
            gdpr_request.processed_by = performed_by
            gdpr_request.result = update_counts

            # Log rectification request
            self._log_audit_event(
                subject_id=subject.subject_id,
                operation="data_rectification",
                performed_by=performed_by,
                details={
                    "request_id": request_id,
                    "updates": updates,
                    "update_counts": update_counts,
                },
            )

            logger.info(
                f"Right to Rectification completed for subject {subject.subject_id}, "
                f"request_id={request_id}, updated={update_counts['total']} records"
            )

            return update_counts

        except Exception as e:
            logger.error(f"Right to Rectification failed: {e}")
            gdpr_request.status = GDPRRequestStatus.FAILED
            gdpr_request.error_message = str(e)
            raise

    def get_request_status(self, request_id: str) -> GDPRRequest | None:
        """
        Get GDPR request status.

        Args:
            request_id: Request ID

        Returns:
            GDPRRequest or None if not found
        """
        return self.gdpr_requests.get(request_id)

    def list_requests(
        self,
        subject_id: str | None = None,
        request_type: GDPRRequestType | None = None,
        status: GDPRRequestStatus | None = None,
    ) -> list[GDPRRequest]:
        """
        List GDPR requests with optional filters.

        Args:
            subject_id: Optional filter by subject ID
            request_type: Optional filter by request type
            status: Optional filter by status

        Returns:
            List of GDPRRequest
        """
        requests = list(self.gdpr_requests.values())

        if subject_id:
            requests = [r for r in requests if r.subject_id == subject_id]

        if request_type:
            requests = [r for r in requests if r.request_type == request_type]

        if status:
            requests = [r for r in requests if r.status == status]

        return sorted(requests, key=lambda r: r.requested_at, reverse=True)

    def get_audit_trail(self, subject_id: str) -> list[AuditLogEntry]:
        """
        Get audit trail for a data subject.

        Args:
            subject_id: Data subject ID

        Returns:
            List of AuditLogEntry
        """
        entries = [e for e in self.audit_logs if e.subject_id == subject_id]
        return sorted(entries, key=lambda e: e.timestamp, reverse=True)

    def _log_audit_event(
        self,
        subject_id: str,
        operation: str,
        performed_by: str,
        details: dict[str, Any],
        ip_address: str | None = None,
    ):
        """
        Log an audit event.

        Args:
            subject_id: Data subject ID
            operation: Operation performed
            performed_by: User or system that performed operation
            details: Additional details
            ip_address: Optional IP address
        """
        log_entry = AuditLogEntry(
            log_id=str(uuid4()),
            subject_id=subject_id,
            operation=operation,
            performed_by=performed_by,
            timestamp=datetime.utcnow(),
            details=details,
            ip_address=ip_address,
        )

        self.audit_logs.append(log_entry)


# ============================================================================
# Singleton Instance
# ============================================================================

_gdpr_manager: GDPRWorkflowManager | None = None


def get_gdpr_manager() -> GDPRWorkflowManager:
    """
    Get or create global GDPR workflow manager instance.

    Returns:
        GDPRWorkflowManager instance
    """
    global _gdpr_manager

    if _gdpr_manager is None:
        _gdpr_manager = GDPRWorkflowManager()

    return _gdpr_manager
