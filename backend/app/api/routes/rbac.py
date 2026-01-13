"""
RBAC API Routes (Phase 6)
=========================

API endpoints for Role-Based Access Control management.

Endpoints:
- User management (CRUD)
- Role assignment
- Permission queries
- Access log viewing
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.rbac import (
    Permission,
    Role,
    User,
    get_current_user,
    get_rbac_manager,
    require_permission,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rbac", tags=["rbac"])


# ============================================================================
# Request/Response Models
# ============================================================================


class CreateUserRequest(BaseModel):
    """Request to create a new user."""

    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5)
    roles: list[str] = Field(..., min_items=1)
    allowed_datasets: list[str] | None = None
    denied_datasets: list[str] | None = None
    masked_columns: dict[str, list[str]] | None = None


class UpdateRolesRequest(BaseModel):
    """Request to update user roles."""

    roles: list[str] = Field(..., min_items=1)


class UpdateDatasetAccessRequest(BaseModel):
    """Request to update dataset access rules."""

    allowed_datasets: list[str] | None = None
    denied_datasets: list[str] | None = None


class UpdateColumnMaskingRequest(BaseModel):
    """Request to update column masking rules."""

    dataset_id: str
    masked_columns: list[str]


class UserResponse(BaseModel):
    """User response model."""

    user_id: str
    username: str
    email: str
    roles: list[str]
    is_active: bool
    created_at: str
    last_login: str | None
    allowed_datasets: list[str] | None
    denied_datasets: list[str]


# ============================================================================
# User Management Endpoints
# ============================================================================


@router.get("/roles")
async def list_roles():
    """
    List all available roles with their permissions.
    """
    from app.auth.rbac import ROLE_PERMISSIONS

    return {
        "roles": [
            {
                "role": role.value,
                "permissions": [p.value for p in permissions],
            }
            for role, permissions in ROLE_PERMISSIONS.items()
        ]
    }


@router.get("/permissions")
async def list_permissions():
    """
    List all available permissions.
    """
    return {
        "permissions": [
            {
                "permission": p.value,
                "category": p.value.split(":")[0],
                "action": p.value.split(":")[1],
            }
            for p in Permission
        ]
    }


@router.post("/users", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    user: User | None = Depends(get_current_user),
):
    """
    Create a new user.

    Requires: admin:users permission
    """
    # Check permission
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    rbac = get_rbac_manager()

    if not rbac.check_permission(user, Permission.ADMIN_USERS):
        raise HTTPException(status_code=403, detail="Permission denied: admin:users required")

    # Validate roles
    try:
        roles = [Role(r) for r in request.roles]
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role: {e}. Valid roles: {[r.value for r in Role]}"
        )

    # Create user
    new_user = rbac.create_user(
        username=request.username,
        email=request.email,
        roles=roles,
        allowed_datasets=request.allowed_datasets,
        denied_datasets=request.denied_datasets,
        masked_columns=request.masked_columns,
    )

    return UserResponse(
        user_id=new_user.user_id,
        username=new_user.username,
        email=new_user.email,
        roles=[r.value for r in new_user.roles],
        is_active=new_user.is_active,
        created_at=new_user.created_at.isoformat(),
        last_login=new_user.last_login.isoformat() if new_user.last_login else None,
        allowed_datasets=new_user.allowed_datasets,
        denied_datasets=new_user.denied_datasets,
    )


@router.get("/users")
async def list_users(
    user: User | None = Depends(get_current_user),
):
    """
    List all users.

    Requires: admin:users permission
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    rbac = get_rbac_manager()

    if not rbac.check_permission(user, Permission.ADMIN_USERS):
        raise HTTPException(status_code=403, detail="Permission denied")

    users = rbac.list_users()

    return {
        "total": len(users),
        "users": [
            {
                "user_id": u.user_id,
                "username": u.username,
                "email": u.email,
                "roles": [r.value for r in u.roles],
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ],
    }


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    user: User | None = Depends(get_current_user),
):
    """
    Get user details.

    Requires: admin:users permission OR accessing own profile
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    rbac = get_rbac_manager()

    # Allow users to access their own profile
    if user.user_id != user_id:
        if not rbac.check_permission(user, Permission.ADMIN_USERS):
            raise HTTPException(status_code=403, detail="Permission denied")

    target_user = rbac.get_user(user_id)

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": target_user.user_id,
        "username": target_user.username,
        "email": target_user.email,
        "roles": [r.value for r in target_user.roles],
        "is_active": target_user.is_active,
        "created_at": target_user.created_at.isoformat(),
        "last_login": target_user.last_login.isoformat() if target_user.last_login else None,
        "allowed_datasets": target_user.allowed_datasets,
        "denied_datasets": target_user.denied_datasets,
        "masked_columns": target_user.masked_columns,
    }


@router.put("/users/{user_id}/roles")
async def update_user_roles(
    user_id: str,
    request: UpdateRolesRequest,
    user: User | None = Depends(get_current_user),
):
    """
    Update user roles.

    Requires: admin:roles permission
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    rbac = get_rbac_manager()

    if not rbac.check_permission(user, Permission.ADMIN_ROLES):
        raise HTTPException(status_code=403, detail="Permission denied: admin:roles required")

    # Validate roles
    try:
        roles = [Role(r) for r in request.roles]
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role: {e}"
        )

    # Update roles
    success = rbac.update_user_roles(user_id, roles)

    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": f"Roles updated for user {user_id}"}


@router.put("/users/{user_id}/dataset-access")
async def update_user_dataset_access(
    user_id: str,
    request: UpdateDatasetAccessRequest,
    user: User | None = Depends(get_current_user),
):
    """
    Update user's dataset access rules.

    Requires: admin:users permission
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    rbac = get_rbac_manager()

    if not rbac.check_permission(user, Permission.ADMIN_USERS):
        raise HTTPException(status_code=403, detail="Permission denied")

    success = rbac.update_dataset_access(
        user_id,
        allowed_datasets=request.allowed_datasets,
        denied_datasets=request.denied_datasets,
    )

    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": f"Dataset access updated for user {user_id}"}


@router.put("/users/{user_id}/column-masking")
async def update_user_column_masking(
    user_id: str,
    request: UpdateColumnMaskingRequest,
    user: User | None = Depends(get_current_user),
):
    """
    Update column masking rules for a user.

    Requires: admin:users permission
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    rbac = get_rbac_manager()

    if not rbac.check_permission(user, Permission.ADMIN_USERS):
        raise HTTPException(status_code=403, detail="Permission denied")

    success = rbac.update_column_masking(
        user_id,
        request.dataset_id,
        request.masked_columns,
    )

    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": f"Column masking updated for user {user_id}"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    user: User | None = Depends(get_current_user),
):
    """
    Delete a user.

    Requires: admin:users permission
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    rbac = get_rbac_manager()

    if not rbac.check_permission(user, Permission.ADMIN_USERS):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Prevent self-deletion
    if user.user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    success = rbac.delete_user(user_id)

    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": f"User {user_id} deleted"}


# ============================================================================
# Permission Check Endpoints
# ============================================================================


@router.get("/check-permission/{permission}")
async def check_permission(
    permission: str,
    user: User | None = Depends(get_current_user),
):
    """
    Check if current user has a specific permission.
    """
    if user is None:
        return {"has_permission": False, "reason": "Not authenticated"}

    try:
        perm = Permission(permission)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid permission: {permission}"
        )

    rbac = get_rbac_manager()
    has_perm = rbac.check_permission(user, perm, log_access=False)

    return {
        "permission": permission,
        "has_permission": has_perm,
        "user": user.username,
        "roles": [r.value for r in user.roles],
    }


@router.get("/check-dataset-access/{dataset_id}")
async def check_dataset_access(
    dataset_id: str,
    permission: str = Query("data:read"),
    user: User | None = Depends(get_current_user),
):
    """
    Check if current user can access a specific dataset.
    """
    if user is None:
        return {"has_access": False, "reason": "Not authenticated"}

    try:
        perm = Permission(permission)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid permission: {permission}"
        )

    rbac = get_rbac_manager()
    has_access = rbac.check_dataset_access(user, dataset_id, perm, log_access=False)

    return {
        "dataset_id": dataset_id,
        "permission": permission,
        "has_access": has_access,
        "user": user.username,
        "masked_columns": user.get_masked_columns(dataset_id),
    }


@router.get("/my-permissions")
async def get_my_permissions(
    user: User | None = Depends(get_current_user),
):
    """
    Get all permissions for the current user.
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    from app.auth.rbac import ROLE_PERMISSIONS

    # Collect all permissions from user's roles
    all_permissions = set()
    for role in user.roles:
        all_permissions.update(ROLE_PERMISSIONS.get(role, set()))

    return {
        "user_id": user.user_id,
        "username": user.username,
        "roles": [r.value for r in user.roles],
        "permissions": sorted([p.value for p in all_permissions]),
        "total_permissions": len(all_permissions),
        "dataset_restrictions": {
            "allowed_datasets": user.allowed_datasets,
            "denied_datasets": user.denied_datasets,
            "masked_columns": user.masked_columns,
        },
    }


# ============================================================================
# Access Log Endpoints
# ============================================================================


@router.get("/access-logs")
async def get_access_logs(
    user_id: str | None = Query(None),
    resource: str | None = Query(None),
    granted: bool | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    user: User | None = Depends(get_current_user),
):
    """
    Get access logs.

    Requires: admin:audit permission
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    rbac = get_rbac_manager()

    if not rbac.check_permission(user, Permission.ADMIN_AUDIT):
        raise HTTPException(status_code=403, detail="Permission denied: admin:audit required")

    logs = rbac.get_access_logs(
        user_id=user_id,
        resource=resource,
        granted=granted,
        limit=limit,
    )

    return {
        "total": len(logs),
        "logs": [
            {
                "log_id": log.log_id,
                "user_id": log.user_id,
                "resource": log.resource,
                "permission": log.permission.value,
                "granted": log.granted,
                "timestamp": log.timestamp.isoformat(),
            }
            for log in logs
        ],
    }


@router.get("/access-logs/denied")
async def get_denied_access_logs(
    limit: int = Query(50, ge=1, le=500),
    user: User | None = Depends(get_current_user),
):
    """
    Get denied access logs (security monitoring).

    Requires: admin:audit permission
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    rbac = get_rbac_manager()

    if not rbac.check_permission(user, Permission.ADMIN_AUDIT):
        raise HTTPException(status_code=403, detail="Permission denied")

    logs = rbac.get_access_logs(granted=False, limit=limit)

    return {
        "total_denied": len(logs),
        "logs": [
            {
                "log_id": log.log_id,
                "user_id": log.user_id,
                "resource": log.resource,
                "permission": log.permission.value,
                "timestamp": log.timestamp.isoformat(),
            }
            for log in logs
        ],
    }
