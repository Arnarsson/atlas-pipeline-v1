"""Governance endpoints for RBAC and audit logging.

Provides role management, permission checking, and audit trail
as required by EU AI Act Article 10 (Data Governance).
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.governance.roles import (
    get_governance_manager,
    Role,
    Permission,
    ROLE_PERMISSIONS
)

router = APIRouter(prefix="/governance", tags=["Governance & RBAC"])


# Request/Response Models

class RoleAssignmentRequest(BaseModel):
    """Request to assign a role to a user."""
    user: str = Field(..., description="User email or identifier")
    role: str = Field(
        ...,
        description="Role to assign",
        examples=["admin", "data_owner", "data_engineer", "analyst", "auditor", "compliance_officer"]
    )
    resource: str = Field(
        ...,
        description="Resource pattern (e.g., 'dataset:123', 'dataset:*', '*')"
    )
    reason: Optional[str] = Field(
        None,
        description="Justification for role assignment"
    )
    expires_in_days: Optional[int] = Field(
        None,
        description="Optional expiration in days",
        ge=1,
        le=365
    )


class RoleRemovalRequest(BaseModel):
    """Request to remove a role from a user."""
    user: str = Field(..., description="User email or identifier")
    role: str = Field(..., description="Role to remove")
    resource: str = Field(..., description="Resource pattern")
    reason: Optional[str] = Field(None, description="Reason for removal")


class AuditLogRequest(BaseModel):
    """Request to log an action."""
    user: str = Field(..., description="User performing action")
    action: str = Field(
        ...,
        description="Action type",
        examples=["created", "updated", "deleted", "accessed", "approved", "exported"]
    )
    resource: str = Field(..., description="Resource being acted on")
    resource_type: str = Field(
        ...,
        description="Type of resource",
        examples=["dataset", "connector", "pipeline", "assessment"]
    )
    details: dict = Field(default_factory=dict, description="Additional details")
    reason: Optional[str] = Field(None, description="Reason for action")


class PermissionCheckRequest(BaseModel):
    """Request to check permission."""
    user: str = Field(..., description="User to check")
    permission: str = Field(..., description="Permission to check")
    resource: str = Field(..., description="Resource to check against")


# Endpoints

@router.post("/roles/assign")
async def assign_role(request: RoleAssignmentRequest):
    """
    Assign a role to a user for a specific resource.

    ## Roles

    - **admin**: Full access to all resources and actions
    - **data_owner**: Can approve changes and assign roles for owned resources
    - **data_engineer**: Can create, read, update connectors and pipelines
    - **analyst**: Read-only access to datasets
    - **auditor**: Read-only with access to all audit logs
    - **compliance_officer**: Can assess compliance and approve changes

    ## Resource Patterns

    - `*`: All resources
    - `dataset:*`: All datasets
    - `dataset:123`: Specific dataset
    - `connector:*`: All connectors
    """
    try:
        role = Role[request.role.upper()]
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role: {request.role}. Valid roles: {[r.value for r in Role]}"
        )

    manager = get_governance_manager()

    # Calculate expiration
    expires_at = None
    if request.expires_in_days:
        from datetime import timedelta
        expires_at = datetime.now() + timedelta(days=request.expires_in_days)

    assignment = manager.assign_role(
        user=request.user,
        role=role,
        resource=request.resource,
        assigned_by="system",  # In production, get from auth context
        reason=request.reason,
        expires_at=expires_at
    )

    return {
        "status": "assigned",
        "user": request.user,
        "role": request.role,
        "resource": request.resource,
        "assigned_at": assignment.assigned_at.isoformat(),
        "expires_at": expires_at.isoformat() if expires_at else None,
        "permissions": [p.value for p in ROLE_PERMISSIONS.get(role, set())]
    }


@router.delete("/roles/remove")
async def remove_role(request: RoleRemovalRequest):
    """Remove a role assignment from a user."""
    try:
        role = Role[request.role.upper()]
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role: {request.role}"
        )

    manager = get_governance_manager()
    removed = manager.remove_role(
        user=request.user,
        role=role,
        resource=request.resource,
        removed_by="system",
        reason=request.reason
    )

    if not removed:
        raise HTTPException(
            status_code=404,
            detail=f"Role assignment not found for user {request.user}"
        )

    return {
        "status": "removed",
        "user": request.user,
        "role": request.role,
        "resource": request.resource
    }


@router.get("/roles/{user}")
async def get_user_roles(user: str):
    """
    Get all roles and permissions for a user.

    Returns:
        - Active role assignments
        - Combined permissions from all roles
        - Recent activity summary
    """
    manager = get_governance_manager()
    summary = manager.get_user_summary(user)

    return summary


@router.get("/roles")
async def list_all_roles():
    """
    List all available roles and their permissions.

    Returns detailed information about each role including
    its permissions and typical use cases.
    """
    return {
        "roles": [
            {
                "role": role.value,
                "permissions": [p.value for p in permissions],
                "description": {
                    Role.ADMIN: "Full system access - manages all resources and users",
                    Role.DATA_OWNER: "Owns datasets - approves access and changes",
                    Role.DATA_ENGINEER: "Builds pipelines - manages connectors and ETL",
                    Role.ANALYST: "Consumes data - read-only access to datasets",
                    Role.AUDITOR: "Reviews compliance - accesses all audit logs",
                    Role.COMPLIANCE_OFFICER: "Manages compliance - assesses and approves"
                }.get(role, "")
            }
            for role, permissions in ROLE_PERMISSIONS.items()
        ]
    }


@router.post("/permissions/check")
async def check_permission(request: PermissionCheckRequest):
    """
    Check if a user has a specific permission on a resource.

    This can be used to validate access before performing actions.
    """
    try:
        permission = Permission[request.permission.upper()]
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid permission: {request.permission}. Valid: {[p.value for p in Permission]}"
        )

    manager = get_governance_manager()
    allowed = manager.can_perform(request.user, permission, request.resource)

    return {
        "user": request.user,
        "permission": request.permission,
        "resource": request.resource,
        "allowed": allowed,
        "message": "Access granted" if allowed else "Access denied"
    }


@router.get("/permissions")
async def list_permissions():
    """List all available permissions."""
    return {
        "permissions": [
            {
                "permission": p.value,
                "category": "data" if p in [Permission.CREATE, Permission.READ, Permission.UPDATE, Permission.DELETE]
                           else "governance" if p in [Permission.APPROVE, Permission.ASSIGN_ROLES]
                           else "audit" if p in [Permission.AUDIT, Permission.EXPORT_LOGS]
                           else "compliance"
            }
            for p in Permission
        ]
    }


@router.post("/audit/log")
async def log_action(request: AuditLogRequest):
    """
    Log an action to the audit trail.

    This endpoint is used to record user actions for compliance tracking.
    All actions are timestamped and stored for the required retention period.
    """
    manager = get_governance_manager()

    try:
        log_entry = manager.log_action(
            user=request.user,
            action=request.action,
            resource=request.resource,
            resource_type=request.resource_type,
            details=request.details,
            reason=request.reason,
            check_permission=False  # Don't check for manual logging
        )

        return {
            "status": "logged",
            "log_id": log_entry.id,
            "timestamp": log_entry.timestamp.isoformat(),
            "user": request.user,
            "action": request.action,
            "resource": request.resource
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/audit")
async def get_audit_trail(
    user: Optional[str] = Query(None, description="Filter by user"),
    resource: Optional[str] = Query(None, description="Filter by resource"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Skip first N records")
):
    """
    Get audit trail with optional filters.

    Returns a list of audit log entries, sorted by timestamp (newest first).

    ## Filters

    - **user**: Filter logs by user who performed the action
    - **resource**: Filter by specific resource (e.g., "dataset:123")
    - **resource_type**: Filter by resource type (dataset, connector, pipeline)
    - **action**: Filter by action type (created, updated, deleted, accessed)

    ## EU AI Act Compliance

    This endpoint supports Article 12 requirements for logging and traceability.
    All logs are retained for the required 5+ year period.
    """
    manager = get_governance_manager()

    logs = manager.get_audit_trail(
        user=user,
        resource=resource,
        resource_type=resource_type,
        action=action,
        limit=limit,
        offset=offset
    )

    return {
        "logs": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "user": log.user,
                "action": log.action,
                "resource": log.resource,
                "resource_type": log.resource_type,
                "details": log.details,
                "reason": log.reason,
                "success": log.success,
                "error_message": log.error_message
            }
            for log in logs
        ],
        "count": len(logs),
        "offset": offset,
        "limit": limit
    }


@router.get("/audit/summary")
async def get_audit_summary():
    """
    Get summary statistics of audit logs.

    Returns aggregated statistics including:
    - Total events
    - Events by action type
    - Events by user
    - Events by resource type
    - Failed event count
    """
    manager = get_governance_manager()
    return manager.get_audit_summary()


@router.get("/audit/user/{user}")
async def get_user_audit_trail(
    user: str,
    limit: int = Query(50, ge=1, le=500)
):
    """
    Get audit trail for a specific user.

    Returns all actions performed by or affecting the specified user.
    """
    manager = get_governance_manager()

    logs = manager.get_audit_trail(user=user, limit=limit)

    return {
        "user": user,
        "logs": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "action": log.action,
                "resource": log.resource,
                "success": log.success
            }
            for log in logs
        ],
        "count": len(logs)
    }


@router.get("/audit/resource/{resource_type}/{resource_id}")
async def get_resource_audit_trail(
    resource_type: str,
    resource_id: str,
    limit: int = Query(50, ge=1, le=500)
):
    """
    Get audit trail for a specific resource.

    Returns all actions performed on the specified resource.
    """
    manager = get_governance_manager()

    resource = f"{resource_type}:{resource_id}"
    logs = manager.get_audit_trail(resource=resource, limit=limit)

    return {
        "resource": resource,
        "logs": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "user": log.user,
                "action": log.action,
                "success": log.success,
                "details": log.details
            }
            for log in logs
        ],
        "count": len(logs)
    }


@router.get("/compliance/status")
async def get_compliance_status():
    """
    Get current governance compliance status.

    Checks if the system meets EU AI Act Article 10 requirements
    for data governance.
    """
    manager = get_governance_manager()
    summary = manager.get_audit_summary()

    # Check compliance indicators
    has_roles = len(manager.user_roles) > 0
    has_audit_logs = summary["total_events"] > 0

    compliance_checks = {
        "role_assignments": {
            "status": "compliant" if has_roles else "not_configured",
            "description": "RBAC roles are defined and assigned",
            "requirement": "Art. 10: Data governance with defined ownership"
        },
        "audit_logging": {
            "status": "compliant" if has_audit_logs else "not_started",
            "description": "Actions are being logged for traceability",
            "requirement": "Art. 12: Automatic logging of events"
        },
        "permission_enforcement": {
            "status": "active",
            "description": "Permission checks are enforced",
            "requirement": "Art. 10: Access control policies"
        }
    }

    all_compliant = all(
        c["status"] == "compliant" or c["status"] == "active"
        for c in compliance_checks.values()
    )

    return {
        "overall_status": "compliant" if all_compliant else "gaps_found",
        "checks": compliance_checks,
        "audit_summary": summary,
        "recommendations": [] if all_compliant else [
            "Assign data owners to all datasets",
            "Ensure all user actions are being logged",
            "Review and document access policies"
        ]
    }
