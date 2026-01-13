"""
Role-Based Access Control (RBAC) System (Phase 6)
=================================================

Provides fine-grained permission management for Atlas Data Pipeline.

Features:
- User roles (Admin, DataEngineer, DataAnalyst, Viewer)
- Resource-level permissions
- API endpoint authorization
- Dataset-level access control
- Column-level masking support

Reference: NIST RBAC model, AWS IAM patterns
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable
from uuid import uuid4

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Constants
# ============================================================================


class Role(str, Enum):
    """User roles with hierarchical permissions."""

    ADMIN = "admin"  # Full access to everything
    DATA_ENGINEER = "data_engineer"  # Manage pipelines, connectors, data
    DATA_ANALYST = "data_analyst"  # Read data, run queries, view reports
    VIEWER = "viewer"  # Read-only access to dashboards


class Permission(str, Enum):
    """Individual permissions that can be assigned to roles."""

    # Pipeline permissions
    PIPELINE_CREATE = "pipeline:create"
    PIPELINE_READ = "pipeline:read"
    PIPELINE_UPDATE = "pipeline:update"
    PIPELINE_DELETE = "pipeline:delete"
    PIPELINE_RUN = "pipeline:run"

    # Connector permissions
    CONNECTOR_CREATE = "connector:create"
    CONNECTOR_READ = "connector:read"
    CONNECTOR_UPDATE = "connector:update"
    CONNECTOR_DELETE = "connector:delete"
    CONNECTOR_SYNC = "connector:sync"

    # Data permissions
    DATA_READ = "data:read"
    DATA_WRITE = "data:write"
    DATA_DELETE = "data:delete"
    DATA_EXPORT = "data:export"
    DATA_PROFILE = "data:profile"

    # Quality permissions
    QUALITY_READ = "quality:read"
    QUALITY_WRITE = "quality:write"

    # PII permissions
    PII_READ = "pii:read"
    PII_MANAGE = "pii:manage"

    # GDPR permissions
    GDPR_READ = "gdpr:read"
    GDPR_EXECUTE = "gdpr:execute"

    # Catalog permissions
    CATALOG_READ = "catalog:read"
    CATALOG_WRITE = "catalog:write"

    # Feature store permissions
    FEATURES_READ = "features:read"
    FEATURES_WRITE = "features:write"
    FEATURES_EXPORT = "features:export"

    # Admin permissions
    ADMIN_USERS = "admin:users"
    ADMIN_ROLES = "admin:roles"
    ADMIN_SETTINGS = "admin:settings"
    ADMIN_AUDIT = "admin:audit"


# Role-to-permissions mapping
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.ADMIN: set(Permission),  # All permissions
    Role.DATA_ENGINEER: {
        Permission.PIPELINE_CREATE,
        Permission.PIPELINE_READ,
        Permission.PIPELINE_UPDATE,
        Permission.PIPELINE_DELETE,
        Permission.PIPELINE_RUN,
        Permission.CONNECTOR_CREATE,
        Permission.CONNECTOR_READ,
        Permission.CONNECTOR_UPDATE,
        Permission.CONNECTOR_DELETE,
        Permission.CONNECTOR_SYNC,
        Permission.DATA_READ,
        Permission.DATA_WRITE,
        Permission.DATA_DELETE,
        Permission.DATA_EXPORT,
        Permission.DATA_PROFILE,
        Permission.QUALITY_READ,
        Permission.QUALITY_WRITE,
        Permission.PII_READ,
        Permission.PII_MANAGE,
        Permission.GDPR_READ,
        Permission.CATALOG_READ,
        Permission.CATALOG_WRITE,
        Permission.FEATURES_READ,
        Permission.FEATURES_WRITE,
        Permission.FEATURES_EXPORT,
    },
    Role.DATA_ANALYST: {
        Permission.PIPELINE_READ,
        Permission.CONNECTOR_READ,
        Permission.DATA_READ,
        Permission.DATA_EXPORT,
        Permission.DATA_PROFILE,
        Permission.QUALITY_READ,
        Permission.PII_READ,
        Permission.GDPR_READ,
        Permission.CATALOG_READ,
        Permission.FEATURES_READ,
        Permission.FEATURES_EXPORT,
    },
    Role.VIEWER: {
        Permission.PIPELINE_READ,
        Permission.CONNECTOR_READ,
        Permission.DATA_READ,
        Permission.QUALITY_READ,
        Permission.CATALOG_READ,
        Permission.FEATURES_READ,
    },
}


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class User:
    """User model with role assignments."""

    user_id: str
    username: str
    email: str
    roles: list[Role]
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: datetime | None = None

    # Dataset-level access control
    allowed_datasets: list[str] | None = None  # None = all datasets
    denied_datasets: list[str] = field(default_factory=list)

    # Column masking rules
    masked_columns: dict[str, list[str]] = field(default_factory=dict)  # dataset -> columns

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        for role in self.roles:
            if permission in ROLE_PERMISSIONS.get(role, set()):
                return True
        return False

    def has_any_permission(self, permissions: list[Permission]) -> bool:
        """Check if user has any of the given permissions."""
        return any(self.has_permission(p) for p in permissions)

    def has_all_permissions(self, permissions: list[Permission]) -> bool:
        """Check if user has all given permissions."""
        return all(self.has_permission(p) for p in permissions)

    def can_access_dataset(self, dataset_id: str) -> bool:
        """Check if user can access a specific dataset."""
        # Denied takes precedence
        if dataset_id in self.denied_datasets:
            return False

        # If allowed_datasets is set, check membership
        if self.allowed_datasets is not None:
            return dataset_id in self.allowed_datasets

        # Default: allow access
        return True

    def get_masked_columns(self, dataset_id: str) -> list[str]:
        """Get list of columns to mask for this dataset."""
        return self.masked_columns.get(dataset_id, [])


@dataclass
class AccessLog:
    """Audit log for access attempts."""

    log_id: str
    user_id: str
    resource: str
    action: str
    permission: Permission
    granted: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ip_address: str | None = None
    user_agent: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# RBAC Manager
# ============================================================================


class RBACManager:
    """
    Role-Based Access Control manager.

    Handles user authentication, authorization, and access logging.
    """

    def __init__(self):
        """Initialize RBAC manager."""
        # In-memory storage (replace with database in production)
        self._users: dict[str, User] = {}
        self._api_keys: dict[str, str] = {}  # api_key -> user_id
        self._access_logs: list[AccessLog] = []

        # Create default admin user
        self._create_default_users()

        logger.info("Initialized RBAC manager with default users")

    def _create_default_users(self):
        """Create default users for testing."""
        # Default admin
        admin = User(
            user_id="admin-001",
            username="admin",
            email="admin@atlas.local",
            roles=[Role.ADMIN],
        )
        self._users[admin.user_id] = admin
        self._api_keys["atlas-admin-key"] = admin.user_id

        # Default data engineer
        engineer = User(
            user_id="engineer-001",
            username="engineer",
            email="engineer@atlas.local",
            roles=[Role.DATA_ENGINEER],
        )
        self._users[engineer.user_id] = engineer
        self._api_keys["atlas-engineer-key"] = engineer.user_id

        # Default analyst
        analyst = User(
            user_id="analyst-001",
            username="analyst",
            email="analyst@atlas.local",
            roles=[Role.DATA_ANALYST],
        )
        self._users[analyst.user_id] = analyst
        self._api_keys["atlas-analyst-key"] = analyst.user_id

        # Default viewer
        viewer = User(
            user_id="viewer-001",
            username="viewer",
            email="viewer@atlas.local",
            roles=[Role.VIEWER],
        )
        self._users[viewer.user_id] = viewer
        self._api_keys["atlas-viewer-key"] = viewer.user_id

    def create_user(
        self,
        username: str,
        email: str,
        roles: list[Role],
        allowed_datasets: list[str] | None = None,
        denied_datasets: list[str] | None = None,
        masked_columns: dict[str, list[str]] | None = None,
    ) -> User:
        """
        Create a new user.

        Args:
            username: Username
            email: Email address
            roles: List of roles
            allowed_datasets: Optional list of allowed datasets
            denied_datasets: Optional list of denied datasets
            masked_columns: Optional column masking rules

        Returns:
            Created User
        """
        user = User(
            user_id=str(uuid4()),
            username=username,
            email=email,
            roles=roles,
            allowed_datasets=allowed_datasets,
            denied_datasets=denied_datasets or [],
            masked_columns=masked_columns or {},
        )

        self._users[user.user_id] = user

        # Generate API key
        api_key = f"atlas-{user.username}-{uuid4().hex[:8]}"
        self._api_keys[api_key] = user.user_id

        logger.info(f"Created user: {username} with roles {[r.value for r in roles]}")

        return user

    def get_user(self, user_id: str) -> User | None:
        """Get user by ID."""
        return self._users.get(user_id)

    def get_user_by_api_key(self, api_key: str) -> User | None:
        """Get user by API key."""
        user_id = self._api_keys.get(api_key)
        if user_id:
            return self._users.get(user_id)
        return None

    def list_users(self) -> list[User]:
        """List all users."""
        return list(self._users.values())

    def update_user_roles(self, user_id: str, roles: list[Role]) -> bool:
        """Update user roles."""
        user = self._users.get(user_id)
        if not user:
            return False

        user.roles = roles
        logger.info(f"Updated roles for user {user.username}: {[r.value for r in roles]}")
        return True

    def update_dataset_access(
        self,
        user_id: str,
        allowed_datasets: list[str] | None = None,
        denied_datasets: list[str] | None = None,
    ) -> bool:
        """Update user's dataset access rules."""
        user = self._users.get(user_id)
        if not user:
            return False

        if allowed_datasets is not None:
            user.allowed_datasets = allowed_datasets
        if denied_datasets is not None:
            user.denied_datasets = denied_datasets

        logger.info(f"Updated dataset access for user {user.username}")
        return True

    def update_column_masking(
        self,
        user_id: str,
        dataset_id: str,
        masked_columns: list[str],
    ) -> bool:
        """Update column masking rules for a user."""
        user = self._users.get(user_id)
        if not user:
            return False

        user.masked_columns[dataset_id] = masked_columns
        logger.info(
            f"Updated column masking for user {user.username}, "
            f"dataset {dataset_id}: {masked_columns}"
        )
        return True

    def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        if user_id not in self._users:
            return False

        user = self._users[user_id]

        # Remove API keys for this user
        keys_to_remove = [k for k, v in self._api_keys.items() if v == user_id]
        for key in keys_to_remove:
            del self._api_keys[key]

        del self._users[user_id]
        logger.info(f"Deleted user: {user.username}")
        return True

    def check_permission(
        self,
        user: User,
        permission: Permission,
        resource: str | None = None,
        log_access: bool = True,
    ) -> bool:
        """
        Check if user has permission.

        Args:
            user: User to check
            permission: Required permission
            resource: Optional resource identifier
            log_access: Whether to log this access check

        Returns:
            True if permitted, False otherwise
        """
        if not user.is_active:
            if log_access:
                self._log_access(user, resource or "unknown", permission, False)
            return False

        granted = user.has_permission(permission)

        if log_access:
            self._log_access(user, resource or "unknown", permission, granted)

        return granted

    def check_dataset_access(
        self,
        user: User,
        dataset_id: str,
        permission: Permission,
        log_access: bool = True,
    ) -> bool:
        """
        Check if user can access a specific dataset.

        Args:
            user: User to check
            dataset_id: Dataset ID
            permission: Required permission
            log_access: Whether to log this access check

        Returns:
            True if permitted, False otherwise
        """
        # Check permission first
        if not self.check_permission(user, permission, dataset_id, log_access=False):
            if log_access:
                self._log_access(user, dataset_id, permission, False)
            return False

        # Check dataset-level access
        granted = user.can_access_dataset(dataset_id)

        if log_access:
            self._log_access(user, dataset_id, permission, granted)

        return granted

    def _log_access(
        self,
        user: User,
        resource: str,
        permission: Permission,
        granted: bool,
    ):
        """Log an access attempt."""
        log_entry = AccessLog(
            log_id=str(uuid4()),
            user_id=user.user_id,
            resource=resource,
            action=permission.value,
            permission=permission,
            granted=granted,
        )

        self._access_logs.append(log_entry)

        # Keep only last 10000 logs
        if len(self._access_logs) > 10000:
            self._access_logs = self._access_logs[-10000:]

        level = "DEBUG" if granted else "WARNING"
        logger.log(
            level,
            f"Access {'granted' if granted else 'denied'}: "
            f"user={user.username}, resource={resource}, permission={permission.value}"
        )

    def get_access_logs(
        self,
        user_id: str | None = None,
        resource: str | None = None,
        granted: bool | None = None,
        limit: int = 100,
    ) -> list[AccessLog]:
        """
        Get access logs with optional filters.

        Args:
            user_id: Filter by user ID
            resource: Filter by resource
            granted: Filter by access result
            limit: Maximum logs to return

        Returns:
            List of AccessLog entries
        """
        logs = self._access_logs

        if user_id:
            logs = [l for l in logs if l.user_id == user_id]
        if resource:
            logs = [l for l in logs if l.resource == resource]
        if granted is not None:
            logs = [l for l in logs if l.granted == granted]

        return sorted(logs, key=lambda l: l.timestamp, reverse=True)[:limit]


# ============================================================================
# FastAPI Integration
# ============================================================================

# Global RBAC manager instance
_rbac_manager: RBACManager | None = None


def get_rbac_manager() -> RBACManager:
    """Get or create global RBAC manager instance."""
    global _rbac_manager
    if _rbac_manager is None:
        _rbac_manager = RBACManager()
    return _rbac_manager


# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User | None:
    """
    Extract current user from request.

    Supports:
    - Bearer token authentication
    - X-API-Key header
    - Anonymous access (returns None)
    """
    rbac = get_rbac_manager()

    # Try Bearer token
    if credentials:
        user = rbac.get_user_by_api_key(credentials.credentials)
        if user:
            return user

    # Try X-API-Key header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        user = rbac.get_user_by_api_key(api_key)
        if user:
            return user

    # Anonymous access
    return None


def require_permission(*permissions: Permission):
    """
    Decorator to require specific permissions for an endpoint.

    Usage:
        @router.get("/admin/users")
        @require_permission(Permission.ADMIN_USERS)
        async def list_users(user: User = Depends(get_current_user)):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from kwargs (injected by Depends)
            user = kwargs.get("user")

            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            rbac = get_rbac_manager()

            # Check all required permissions
            for permission in permissions:
                if not rbac.check_permission(user, permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: {permission.value}",
                    )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_dataset_access(permission: Permission):
    """
    Decorator to require dataset-level access.

    Expects 'dataset_id' in function parameters.

    Usage:
        @router.get("/data/{dataset_id}")
        @require_dataset_access(Permission.DATA_READ)
        async def get_data(dataset_id: str, user: User = Depends(get_current_user)):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get("user")
            dataset_id = kwargs.get("dataset_id")

            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            if dataset_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="dataset_id is required",
                )

            rbac = get_rbac_manager()

            if not rbac.check_dataset_access(user, dataset_id, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to dataset: {dataset_id}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def mask_sensitive_columns(data: dict[str, Any], user: User, dataset_id: str) -> dict[str, Any]:
    """
    Apply column masking based on user's masking rules.

    Args:
        data: Data dictionary with column values
        user: Current user
        dataset_id: Dataset ID

    Returns:
        Data with masked columns
    """
    masked_columns = user.get_masked_columns(dataset_id)

    if not masked_columns:
        return data

    masked_data = data.copy()

    for column in masked_columns:
        if column in masked_data:
            # Mask the value
            original = masked_data[column]
            if isinstance(original, str):
                masked_data[column] = "***MASKED***"
            elif isinstance(original, (int, float)):
                masked_data[column] = 0
            else:
                masked_data[column] = None

    return masked_data
