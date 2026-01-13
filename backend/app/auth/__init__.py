"""
Atlas Client Authentication Module

Multi-tenant API key system for client data isolation.
"""

from .api_keys import (
    ClientInfo,
    APIKeyCreate,
    APIKeyResponse,
    create_api_key,
    validate_api_key,
    revoke_api_key,
    list_clients,
    check_rate_limit,
    get_current_client,
    require_client,
    require_scope,
    check_dataset_access,
    persist_api_keys_to_db,
    load_api_keys_from_db,
)

__all__ = [
    "ClientInfo",
    "APIKeyCreate",
    "APIKeyResponse",
    "create_api_key",
    "validate_api_key",
    "revoke_api_key",
    "list_clients",
    "check_rate_limit",
    "get_current_client",
    "require_client",
    "require_scope",
    "check_dataset_access",
    "persist_api_keys_to_db",
    "load_api_keys_from_db",
]
