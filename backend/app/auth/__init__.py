"""
Authentication and Authorization module for Atlas Data Pipeline.

Provides:
- Role-Based Access Control (RBAC)
- API key authentication
- Permission management
- Access logging
"""

from .rbac import (
    AccessLog,
    Permission,
    RBACManager,
    Role,
    User,
    get_current_user,
    get_rbac_manager,
    mask_sensitive_columns,
    require_dataset_access,
    require_permission,
)

__all__ = [
    "AccessLog",
    "Permission",
    "RBACManager",
    "Role",
    "User",
    "get_current_user",
    "get_rbac_manager",
    "mask_sensitive_columns",
    "require_dataset_access",
    "require_permission",
]
