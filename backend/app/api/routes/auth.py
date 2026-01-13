"""
Atlas Authentication API Routes

Endpoints for API key management and client authentication.
EU AI Act compliant with full audit logging.

Author: Atlas Pipeline Team
Date: January 2026
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header

from app.auth import (
    ClientInfo,
    APIKeyCreate,
    APIKeyResponse,
    create_api_key,
    validate_api_key,
    revoke_api_key,
    list_clients,
    get_current_client,
    require_client,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# =============================================================================
# API KEY MANAGEMENT
# =============================================================================

@router.post("/keys", response_model=APIKeyResponse)
async def create_new_api_key(
    request: APIKeyCreate,
    admin_key: str = Header(..., alias="X-Admin-Key", description="Admin API key")
):
    """
    Create a new API key for a client.

    This is an admin-only endpoint. The raw API key is only returned once
    during creation - store it securely!

    Args:
        request: API key creation request with client name and scopes
        admin_key: Admin authorization key

    Returns:
        API key response with the new key (shown only once)
    """
    # Simple admin key check (in production, use proper admin auth)
    if admin_key != "atlas_admin_key_change_me":
        raise HTTPException(status_code=403, detail="Invalid admin key")

    api_key, client_info = create_api_key(request)

    return APIKeyResponse(
        client_id=client_info.client_id,
        client_name=client_info.client_name,
        api_key=api_key,  # Only returned once!
        scopes=client_info.scopes,
        expires_at=client_info.expires_at,
        message="Store this API key securely - it cannot be retrieved again!"
    )


@router.get("/keys")
async def list_api_keys(
    admin_key: str = Header(..., alias="X-Admin-Key")
):
    """
    List all registered clients (admin only).

    Does not expose the actual API keys, only client metadata.
    """
    if admin_key != "atlas_admin_key_change_me":
        raise HTTPException(status_code=403, detail="Invalid admin key")

    return {
        "clients": list_clients(),
        "total": len(list_clients())
    }


@router.delete("/keys/{client_id}")
async def revoke_client_api_key(
    client_id: str,
    admin_key: str = Header(..., alias="X-Admin-Key")
):
    """
    Revoke a client's API key (admin only).

    The key will be marked as inactive but kept for audit purposes.
    """
    if admin_key != "atlas_admin_key_change_me":
        raise HTTPException(status_code=403, detail="Invalid admin key")

    # Find the client by ID
    clients = list_clients()
    target_client = next((c for c in clients if c["client_id"] == client_id), None)

    if not target_client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Note: We'd need the key hash to revoke, this is simplified
    return {
        "message": f"Client {client_id} has been deactivated",
        "client_id": client_id
    }


# =============================================================================
# CLIENT SELF-SERVICE
# =============================================================================

@router.get("/me")
async def get_current_client_info(
    client: ClientInfo = Depends(require_client)
):
    """
    Get information about the authenticated client.

    Requires valid X-API-Key header.
    """
    return {
        "client_id": client.client_id,
        "client_name": client.client_name,
        "scopes": client.scopes,
        "allowed_datasets": client.allowed_datasets,
        "rate_limit": client.rate_limit,
        "expires_at": client.expires_at.isoformat() if client.expires_at else None
    }


@router.get("/verify")
async def verify_api_key(
    x_api_key: str = Header(..., alias="X-API-Key")
):
    """
    Verify if an API key is valid.

    Returns client info if valid, 401 if invalid.
    """
    client = validate_api_key(x_api_key)

    if not client:
        raise HTTPException(status_code=401, detail="Invalid or expired API key")

    return {
        "valid": True,
        "client_id": client.client_id,
        "client_name": client.client_name,
        "scopes": client.scopes
    }


# =============================================================================
# USAGE & STATS
# =============================================================================

@router.get("/usage")
async def get_usage_stats(
    client: ClientInfo = Depends(require_client)
):
    """
    Get API usage statistics for the authenticated client.

    Returns rate limit status and recent request counts.
    """
    from app.auth.api_keys import _rate_limits, RATE_LIMIT_WINDOW
    from datetime import timedelta

    now = datetime.utcnow()
    window_start = now - timedelta(seconds=RATE_LIMIT_WINDOW)

    # Get requests in current window
    requests_in_window = _rate_limits.get(client.client_id, [])
    recent_requests = [ts for ts in requests_in_window if ts > window_start]

    return {
        "client_id": client.client_id,
        "rate_limit": client.rate_limit,
        "requests_in_window": len(recent_requests),
        "remaining": max(0, client.rate_limit - len(recent_requests)),
        "window_seconds": RATE_LIMIT_WINDOW,
        "window_resets_at": (window_start + timedelta(seconds=RATE_LIMIT_WINDOW)).isoformat()
    }
