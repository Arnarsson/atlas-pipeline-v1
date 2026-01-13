"""Governance role and permission model.

Implements RBAC (Role-Based Access Control) for data governance
as required by EU AI Act Article 10.
"""

from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
from typing import Set, Optional, List, Dict


class Role(str, Enum):
    """Governance roles per Art. 10 data governance requirements."""
    ADMIN = "admin"  # Full access, manages system
    DATA_OWNER = "data_owner"  # Owns datasets, approves access
    DATA_ENGINEER = "data_engineer"  # Configures pipelines, manages connectors
    ANALYST = "analyst"  # Read-only access, can export
    AUDITOR = "auditor"  # Read-only, can access all logs
    COMPLIANCE_OFFICER = "compliance_officer"  # Manages compliance, reviews assessments


class Permission(str, Enum):
    """Granular permissions for access control."""
    # Data permissions
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

    # Governance permissions
    APPROVE = "approve"
    ASSIGN_ROLES = "assign_roles"

    # Audit permissions
    AUDIT = "audit"
    EXPORT_LOGS = "export_logs"

    # Compliance permissions
    ASSESS = "assess"
    CONFIGURE_RULES = "configure_rules"


# Role -> Permission mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        Permission.CREATE, Permission.READ, Permission.UPDATE, Permission.DELETE,
        Permission.APPROVE, Permission.ASSIGN_ROLES,
        Permission.AUDIT, Permission.EXPORT_LOGS,
        Permission.ASSESS, Permission.CONFIGURE_RULES
    },
    Role.DATA_OWNER: {
        Permission.READ, Permission.APPROVE, Permission.ASSIGN_ROLES
    },
    Role.DATA_ENGINEER: {
        Permission.CREATE, Permission.READ, Permission.UPDATE,
        Permission.CONFIGURE_RULES
    },
    Role.ANALYST: {
        Permission.READ
    },
    Role.AUDITOR: {
        Permission.READ, Permission.AUDIT, Permission.EXPORT_LOGS
    },
    Role.COMPLIANCE_OFFICER: {
        Permission.READ, Permission.AUDIT, Permission.EXPORT_LOGS,
        Permission.ASSESS, Permission.APPROVE
    }
}


@dataclass
class RoleAssignment:
    """A role assignment to a user for a resource."""
    user: str
    role: Role
    resource: str  # "dataset:123", "connector:456", "*" for all
    assigned_by: str
    assigned_at: datetime
    reason: Optional[str] = None
    expires_at: Optional[datetime] = None


@dataclass
class AuditLog:
    """Single audit log entry for compliance tracking."""
    id: str
    timestamp: datetime
    user: str
    action: str  # "created", "updated", "deleted", "accessed", "approved", "exported"
    resource: str  # "dataset:123", "connector:456"
    resource_type: str  # "dataset", "connector", "pipeline", "assessment"
    details: dict
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class GovernanceManager:
    """
    Manage roles, permissions, and audit logging.

    Provides RBAC functionality for data governance compliance.
    """

    def __init__(self):
        # In production, these would be backed by database
        self.user_roles: Dict[str, List[RoleAssignment]] = {}
        self.audit_logs: List[AuditLog] = []
        self._log_counter = 0

    def assign_role(
        self,
        user: str,
        role: Role,
        resource: str,
        assigned_by: str,
        reason: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> RoleAssignment:
        """
        Assign a role to a user for a specific resource.

        Args:
            user: Email or user identifier
            role: Role to assign
            resource: Resource pattern (e.g., "dataset:*" for all datasets)
            assigned_by: Who is making the assignment
            reason: Justification for assignment
            expires_at: Optional expiration time

        Returns:
            RoleAssignment record
        """
        assignment = RoleAssignment(
            user=user,
            role=role,
            resource=resource,
            assigned_by=assigned_by,
            assigned_at=datetime.now(),
            reason=reason,
            expires_at=expires_at
        )

        if user not in self.user_roles:
            self.user_roles[user] = []

        # Remove existing same role on same resource
        self.user_roles[user] = [
            r for r in self.user_roles[user]
            if not (r.role == role and r.resource == resource)
        ]

        self.user_roles[user].append(assignment)

        # Log the assignment
        self._log_action(
            user=assigned_by,
            action="role_assigned",
            resource=f"user:{user}",
            resource_type="governance",
            details={
                "assigned_role": role.value,
                "target_user": user,
                "target_resource": resource,
                "expires_at": expires_at.isoformat() if expires_at else None
            },
            reason=reason
        )

        return assignment

    def remove_role(
        self,
        user: str,
        role: Role,
        resource: str,
        removed_by: str,
        reason: Optional[str] = None
    ) -> bool:
        """Remove a role assignment from a user."""
        if user not in self.user_roles:
            return False

        original_count = len(self.user_roles[user])
        self.user_roles[user] = [
            r for r in self.user_roles[user]
            if not (r.role == role and r.resource == resource)
        ]

        removed = len(self.user_roles[user]) < original_count

        if removed:
            self._log_action(
                user=removed_by,
                action="role_removed",
                resource=f"user:{user}",
                resource_type="governance",
                details={
                    "removed_role": role.value,
                    "from_user": user,
                    "from_resource": resource
                },
                reason=reason
            )

        return removed

    def get_user_roles(self, user: str) -> List[RoleAssignment]:
        """Get all role assignments for a user."""
        if user not in self.user_roles:
            return []

        # Filter out expired roles
        now = datetime.now()
        active_roles = [
            r for r in self.user_roles[user]
            if r.expires_at is None or r.expires_at > now
        ]

        return active_roles

    def get_user_permissions(self, user: str) -> Set[Permission]:
        """Get all permissions for a user across all their roles."""
        permissions = set()

        for assignment in self.get_user_roles(user):
            permissions.update(ROLE_PERMISSIONS.get(assignment.role, set()))

        return permissions

    def can_perform(
        self,
        user: str,
        permission: Permission,
        resource: str
    ) -> bool:
        """
        Check if user has permission to perform action on resource.

        Args:
            user: User identifier
            permission: Required permission
            resource: Target resource (e.g., "dataset:123")

        Returns:
            True if user has permission, False otherwise
        """
        roles = self.get_user_roles(user)

        for assignment in roles:
            # Check if role has the permission
            if permission not in ROLE_PERMISSIONS.get(assignment.role, set()):
                continue

            # Check if resource matches
            if self._resource_matches(assignment.resource, resource):
                return True

        return False

    def _resource_matches(self, pattern: str, resource: str) -> bool:
        """Check if a resource matches a pattern."""
        # Wildcard matches all
        if pattern == "*":
            return True

        # Exact match
        if pattern == resource:
            return True

        # Pattern matching (e.g., "dataset:*" matches "dataset:123")
        if pattern.endswith(":*"):
            prefix = pattern[:-1]  # Remove "*"
            return resource.startswith(prefix)

        # Type wildcard (e.g., "dataset" matches "dataset:123")
        if ":" not in pattern and resource.startswith(f"{pattern}:"):
            return True

        return False

    def log_action(
        self,
        user: str,
        action: str,
        resource: str,
        resource_type: str,
        details: dict,
        reason: Optional[str] = None,
        check_permission: bool = True,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> AuditLog:
        """
        Log a user action with optional permission checking.

        Args:
            user: User performing action
            action: Action type (created, updated, deleted, accessed, approved)
            resource: Resource being acted on
            resource_type: Type of resource
            details: Additional details
            reason: Reason for action
            check_permission: Whether to verify permission
            ip_address: Client IP
            session_id: Session identifier

        Returns:
            AuditLog entry

        Raises:
            PermissionError: If user lacks required permission
        """
        # Map actions to permissions
        permission_map = {
            "created": Permission.CREATE,
            "updated": Permission.UPDATE,
            "deleted": Permission.DELETE,
            "accessed": Permission.READ,
            "approved": Permission.APPROVE,
            "exported": Permission.EXPORT_LOGS,
            "assessed": Permission.ASSESS
        }

        success = True
        error_message = None

        if check_permission and action in permission_map:
            required_permission = permission_map[action]
            if not self.can_perform(user, required_permission, resource):
                success = False
                error_message = f"User {user} lacks permission {required_permission.value} on {resource}"

                # Log the failed attempt
                log = self._log_action(
                    user=user,
                    action=f"attempted_{action}",
                    resource=resource,
                    resource_type=resource_type,
                    details=details,
                    reason=reason,
                    success=False,
                    error_message=error_message,
                    ip_address=ip_address,
                    session_id=session_id
                )

                raise PermissionError(error_message)

        return self._log_action(
            user=user,
            action=action,
            resource=resource,
            resource_type=resource_type,
            details=details,
            reason=reason,
            success=success,
            error_message=error_message,
            ip_address=ip_address,
            session_id=session_id
        )

    def _log_action(
        self,
        user: str,
        action: str,
        resource: str,
        resource_type: str,
        details: dict,
        reason: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> AuditLog:
        """Internal method to create audit log entry."""
        self._log_counter += 1

        log = AuditLog(
            id=f"log_{self._log_counter:08d}",
            timestamp=datetime.now(),
            user=user,
            action=action,
            resource=resource,
            resource_type=resource_type,
            details=details,
            reason=reason,
            success=success,
            error_message=error_message,
            ip_address=ip_address,
            session_id=session_id
        )

        self.audit_logs.append(log)
        return log

    def get_audit_trail(
        self,
        user: Optional[str] = None,
        resource: Optional[str] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Get filtered audit trail.

        Args:
            user: Filter by user
            resource: Filter by resource
            resource_type: Filter by resource type
            action: Filter by action type
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum records to return
            offset: Skip first N records

        Returns:
            List of matching AuditLog entries
        """
        logs = self.audit_logs

        if user:
            logs = [log for log in logs if log.user == user]
        if resource:
            logs = [log for log in logs if log.resource == resource]
        if resource_type:
            logs = [log for log in logs if log.resource_type == resource_type]
        if action:
            logs = [log for log in logs if log.action == action]
        if start_time:
            logs = [log for log in logs if log.timestamp >= start_time]
        if end_time:
            logs = [log for log in logs if log.timestamp <= end_time]

        # Sort by timestamp descending (newest first)
        logs = sorted(logs, key=lambda x: x.timestamp, reverse=True)

        # Apply pagination
        return logs[offset:offset + limit]

    def get_audit_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> dict:
        """Get summary statistics of audit logs."""
        logs = self.audit_logs

        if start_time:
            logs = [log for log in logs if log.timestamp >= start_time]
        if end_time:
            logs = [log for log in logs if log.timestamp <= end_time]

        # Count by action
        actions: Dict[str, int] = {}
        users: Dict[str, int] = {}
        resources: Dict[str, int] = {}
        failed_count = 0

        for log in logs:
            actions[log.action] = actions.get(log.action, 0) + 1
            users[log.user] = users.get(log.user, 0) + 1
            resources[log.resource_type] = resources.get(log.resource_type, 0) + 1
            if not log.success:
                failed_count += 1

        return {
            "total_events": len(logs),
            "failed_events": failed_count,
            "events_by_action": actions,
            "events_by_user": users,
            "events_by_resource_type": resources,
            "period": {
                "start": start_time.isoformat() if start_time else None,
                "end": end_time.isoformat() if end_time else None
            },
            "latest_event": logs[0].timestamp.isoformat() if logs else None
        }

    def get_user_summary(self, user: str) -> dict:
        """Get summary of user's roles, permissions, and recent activity."""
        roles = self.get_user_roles(user)
        permissions = self.get_user_permissions(user)

        # Get recent activity
        recent_logs = self.get_audit_trail(user=user, limit=10)

        return {
            "user": user,
            "roles": [
                {
                    "role": r.role.value,
                    "resource": r.resource,
                    "assigned_by": r.assigned_by,
                    "assigned_at": r.assigned_at.isoformat(),
                    "expires_at": r.expires_at.isoformat() if r.expires_at else None
                }
                for r in roles
            ],
            "permissions": [p.value for p in permissions],
            "recent_activity": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "action": log.action,
                    "resource": log.resource,
                    "success": log.success
                }
                for log in recent_logs
            ],
            "is_admin": any(r.role == Role.ADMIN for r in roles)
        }


# Global singleton instance
_governance_manager: Optional[GovernanceManager] = None


def get_governance_manager() -> GovernanceManager:
    """Get or create the global governance manager."""
    global _governance_manager
    if _governance_manager is None:
        _governance_manager = GovernanceManager()
    return _governance_manager
