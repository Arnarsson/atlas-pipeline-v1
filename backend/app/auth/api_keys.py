"""
Atlas Client Authentication - API Key Management

Multi-tenant API key system for client data isolation.
Each client gets their own API key with access to their datasets only.

Features:
- API key generation and validation
- Client-scoped data access
- Rate limiting per client
- Full audit logging

Author: Atlas Pipeline Team
Date: January 2026
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

from fastapi import Depends, HTTPException, Header, Request
from fastapi.security import APIKeyHeader
from loguru import logger
from pydantic import BaseModel

# In-memory storage (replace with database in production)
# Structure: {api_key_hash: ClientInfo}
_api_keys: dict[str, "ClientInfo"] = {}
_rate_limits: dict[str, list[datetime]] = {}

# Configuration
API_KEY_PREFIX = "atlas_"
RATE_LIMIT_REQUESTS = 1000  # per hour
RATE_LIMIT_WINDOW = 3600  # seconds


class ClientInfo(BaseModel):
    """Client information associated with an API key."""
    client_id: str
    client_name: str
    api_key_hash: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    scopes: list[str] = ["read", "write"]
    allowed_datasets: list[str] = []  # Empty = all datasets
    rate_limit: int = RATE_LIMIT_REQUESTS
    metadata: dict[str, Any] = {}


class APIKeyCreate(BaseModel):
    """Request to create a new API key."""
    client_name: str
    scopes: list[str] = ["read", "write"]
    allowed_datasets: list[str] = []
    expires_in_days: Optional[int] = None
    rate_limit: int = RATE_LIMIT_REQUESTS


class APIKeyResponse(BaseModel):
    """Response after creating an API key."""
    client_id: str
    client_name: str
    api_key: str  # Only returned once on creation
    scopes: list[str]
    expires_at: Optional[datetime]
    message: str


# =============================================================================
# API KEY MANAGEMENT
# =============================================================================

def generate_api_key() -> str:
    """Generate a new API key with prefix."""
    random_part = secrets.token_urlsafe(32)
    return f"{API_KEY_PREFIX}{random_part}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def create_api_key(request: APIKeyCreate) -> tuple[str, ClientInfo]:
    """
    Create a new API key for a client.

    Args:
        request: API key creation request

    Returns:
        Tuple of (raw_api_key, client_info)
    """
    # Generate key
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)

    # Calculate expiration
    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)

    # Create client info
    client_info = ClientInfo(
        client_id=str(uuid4()),
        client_name=request.client_name,
        api_key_hash=api_key_hash,
        created_at=datetime.utcnow(),
        expires_at=expires_at,
        scopes=request.scopes,
        allowed_datasets=request.allowed_datasets,
        rate_limit=request.rate_limit
    )

    # Store
    _api_keys[api_key_hash] = client_info

    logger.info(f"Created API key for client: {request.client_name} (id={client_info.client_id})")

    return api_key, client_info


def validate_api_key(api_key: str) -> Optional[ClientInfo]:
    """
    Validate an API key and return client info.

    Args:
        api_key: The API key to validate

    Returns:
        ClientInfo if valid, None otherwise
    """
    if not api_key or not api_key.startswith(API_KEY_PREFIX):
        return None

    api_key_hash = hash_api_key(api_key)
    client_info = _api_keys.get(api_key_hash)

    if not client_info:
        return None

    if not client_info.is_active:
        return None

    if client_info.expires_at and client_info.expires_at < datetime.utcnow():
        return None

    return client_info


def revoke_api_key(api_key: str) -> bool:
    """Revoke an API key."""
    api_key_hash = hash_api_key(api_key)
    if api_key_hash in _api_keys:
        _api_keys[api_key_hash].is_active = False
        return True
    return False


def list_clients() -> list[dict[str, Any]]:
    """List all registered clients (without exposing keys)."""
    return [
        {
            "client_id": info.client_id,
            "client_name": info.client_name,
            "created_at": info.created_at.isoformat(),
            "expires_at": info.expires_at.isoformat() if info.expires_at else None,
            "is_active": info.is_active,
            "scopes": info.scopes,
            "allowed_datasets": info.allowed_datasets
        }
        for info in _api_keys.values()
    ]


# =============================================================================
# RATE LIMITING
# =============================================================================

def check_rate_limit(client_id: str, limit: int = RATE_LIMIT_REQUESTS) -> bool:
    """
    Check if client is within rate limit.

    Args:
        client_id: Client identifier
        limit: Max requests per hour

    Returns:
        True if within limit, False if exceeded
    """
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=RATE_LIMIT_WINDOW)

    # Get requests in window
    if client_id not in _rate_limits:
        _rate_limits[client_id] = []

    # Clean old entries
    _rate_limits[client_id] = [
        ts for ts in _rate_limits[client_id]
        if ts > window_start
    ]

    # Check limit
    if len(_rate_limits[client_id]) >= limit:
        return False

    # Record this request
    _rate_limits[client_id].append(now)
    return True


# =============================================================================
# FASTAPI DEPENDENCIES
# =============================================================================

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_client(
    request: Request,
    api_key: Optional[str] = Depends(api_key_header),
    x_api_key: Optional[str] = Header(None),
) -> Optional[ClientInfo]:
    """
    FastAPI dependency to get current authenticated client.

    Checks X-API-Key header for authentication.
    Returns None if no key provided (for public endpoints).
    """
    # Try both header formats
    key = api_key or x_api_key

    if not key:
        return None

    client = validate_api_key(key)

    if not client:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API key"
        )

    # Check rate limit
    if not check_rate_limit(client.client_id, client.rate_limit):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {client.rate_limit} requests per hour."
        )

    return client


async def require_client(
    client: Optional[ClientInfo] = Depends(get_current_client)
) -> ClientInfo:
    """
    FastAPI dependency that requires authentication.

    Use this for protected endpoints.
    """
    if not client:
        raise HTTPException(
            status_code=401,
            detail="API key required. Include X-API-Key header."
        )
    return client


def require_scope(required_scope: str):
    """
    FastAPI dependency factory for scope-based access control.

    Usage:
        @app.get("/data", dependencies=[Depends(require_scope("read"))])
    """
    async def check_scope(client: ClientInfo = Depends(require_client)) -> ClientInfo:
        if required_scope not in client.scopes:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required scope: {required_scope}"
            )
        return client
    return check_scope


def check_dataset_access(client: ClientInfo, dataset_name: str) -> bool:
    """
    Check if client has access to a specific dataset.

    Args:
        client: Client info
        dataset_name: Dataset to check

    Returns:
        True if allowed, False otherwise
    """
    # Empty allowed_datasets means access to all
    if not client.allowed_datasets:
        return True

    return dataset_name in client.allowed_datasets


# =============================================================================
# DATABASE PERSISTENCE (optional)
# =============================================================================

async def persist_api_keys_to_db(db) -> int:
    """
    Persist in-memory API keys to database.

    Args:
        db: Database instance

    Returns:
        Number of keys persisted
    """
    import json

    async with db.connection() as conn:
        # Create table if not exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS auth.api_keys (
                api_key_hash VARCHAR(64) PRIMARY KEY,
                client_id VARCHAR(100) NOT NULL,
                client_name VARCHAR(255) NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                expires_at TIMESTAMPTZ,
                is_active BOOLEAN DEFAULT TRUE,
                scopes TEXT[],
                allowed_datasets TEXT[],
                rate_limit INTEGER DEFAULT 1000,
                metadata JSONB
            );
            CREATE INDEX IF NOT EXISTS idx_api_keys_client ON auth.api_keys(client_id);
        """)

        count = 0
        for key_hash, info in _api_keys.items():
            try:
                await conn.execute("""
                    INSERT INTO auth.api_keys
                    (api_key_hash, client_id, client_name, created_at, expires_at,
                     is_active, scopes, allowed_datasets, rate_limit, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (api_key_hash) DO UPDATE SET
                        is_active = EXCLUDED.is_active,
                        expires_at = EXCLUDED.expires_at,
                        scopes = EXCLUDED.scopes,
                        allowed_datasets = EXCLUDED.allowed_datasets
                """,
                    key_hash, info.client_id, info.client_name,
                    info.created_at, info.expires_at, info.is_active,
                    info.scopes, info.allowed_datasets, info.rate_limit,
                    json.dumps(info.metadata)
                )
                count += 1
            except Exception as e:
                logger.error(f"Failed to persist API key: {e}")

    return count


async def load_api_keys_from_db(db) -> int:
    """
    Load API keys from database into memory.

    Args:
        db: Database instance

    Returns:
        Number of keys loaded
    """
    async with db.connection() as conn:
        try:
            rows = await conn.fetch("""
                SELECT * FROM auth.api_keys WHERE is_active = TRUE
            """)

            for row in rows:
                info = ClientInfo(
                    client_id=row["client_id"],
                    client_name=row["client_name"],
                    api_key_hash=row["api_key_hash"],
                    created_at=row["created_at"],
                    expires_at=row["expires_at"],
                    is_active=row["is_active"],
                    scopes=list(row["scopes"]) if row["scopes"] else [],
                    allowed_datasets=list(row["allowed_datasets"]) if row["allowed_datasets"] else [],
                    rate_limit=row["rate_limit"]
                )
                _api_keys[row["api_key_hash"]] = info

            return len(rows)
        except Exception as e:
            logger.warning(f"Failed to load API keys from DB: {e}")
            return 0
