"""
Pytest Configuration and Fixtures for Atlas Data Pipeline Platform

This module provides comprehensive test fixtures for:
- Database sessions with test isolation
- FastAPI test client
- Authentication and authorization
- Pipeline test data
- Mock external services
"""

from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete, create_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import Item, User
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine with isolated transactions."""
    # Use in-memory SQLite for fast tests, or PostgreSQL for integration tests
    if settings.ENVIRONMENT == "testing":
        # SQLite in-memory for unit tests
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        # Use existing PostgreSQL engine for integration tests
        engine = engine

    return engine


@pytest.fixture(scope="session", autouse=True)
def db(test_engine) -> Generator[Session, None, None]:
    """
    Session-wide database fixture with automatic cleanup.

    This fixture:
    - Initializes the database schema
    - Provides a database session for tests
    - Cleans up all data after tests complete
    """
    with Session(test_engine) as session:
        init_db(session)
        yield session
        # Cleanup after all tests
        statement = delete(Item)
        session.execute(statement)
        statement = delete(User)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="function")
def db_session(db: Session) -> Generator[Session, None, None]:
    """
    Function-scoped database session with transaction rollback.

    Use this for tests that modify the database.
    Each test gets a fresh transaction that's rolled back after completion.
    """
    db.begin_nested()
    yield db
    db.rollback()


# ============================================================================
# FastAPI Test Client Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """
    Module-scoped FastAPI test client.

    Provides an HTTP client for testing API endpoints without
    running the actual server.
    """
    with TestClient(app) as c:
        yield c


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    """
    Get authentication headers for superuser.

    Returns:
        dict: Headers with Bearer token for superuser authentication
    """
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    """
    Get authentication headers for normal user.

    Returns:
        dict: Headers with Bearer token for normal user authentication
    """
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )


# ============================================================================
# Pipeline Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_bronze_data() -> list[dict[str, Any]]:
    """
    Sample data for Bronze layer testing.

    Returns raw data as it would come from source systems.
    """
    return [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
            "ssn": "123-45-6789",
            "created_at": "2024-01-01T00:00:00Z",
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "phone": "+1-555-987-6543",
            "ssn": "987-65-4321",
            "created_at": "2024-01-02T00:00:00Z",
        },
    ]


@pytest.fixture
def sample_pii_data() -> dict[str, Any]:
    """
    Sample data containing various PII types for testing detection.

    Includes:
    - Names
    - Email addresses
    - Phone numbers
    - SSN
    - Credit card numbers
    - Addresses
    """
    return {
        "full_name": "John Michael Doe",
        "email": "john.doe@company.com",
        "phone": "+1 (555) 123-4567",
        "ssn": "123-45-6789",
        "credit_card": "4532-1234-5678-9010",
        "address": "123 Main St, Anytown, CA 12345",
        "date_of_birth": "1985-06-15",
        "passport": "X12345678",
    }


@pytest.fixture
def mock_data_quality_config() -> dict[str, Any]:
    """
    Mock configuration for data quality checks.

    Defines quality rules and thresholds for testing.
    """
    return {
        "completeness": {"threshold": 0.95, "critical_columns": ["id", "email"]},
        "validity": {"email_pattern": r"^[\w\.-]+@[\w\.-]+\.\w+$"},
        "consistency": {"date_format": "%Y-%m-%dT%H:%M:%SZ"},
        "accuracy": {"phone_country_code": "+1"},
        "timeliness": {"max_age_days": 30},
        "uniqueness": {"unique_columns": ["id", "email"]},
    }


# ============================================================================
# External Service Mocks
# ============================================================================

@pytest.fixture
def mock_redis_client(monkeypatch):
    """Mock Redis client for testing without Redis dependency."""

    class MockRedis:
        def __init__(self):
            self.data = {}

        def get(self, key: str) -> str | None:
            return self.data.get(key)

        def set(self, key: str, value: str, ex: int | None = None) -> bool:
            self.data[key] = value
            return True

        def delete(self, key: str) -> int:
            if key in self.data:
                del self.data[key]
                return 1
            return 0

    mock_redis = MockRedis()
    # Monkeypatch Redis client in app
    # monkeypatch.setattr("app.core.cache.redis_client", mock_redis)
    return mock_redis


@pytest.fixture
def mock_s3_client(monkeypatch):
    """Mock S3/MinIO client for testing without external storage."""

    class MockS3:
        def __init__(self):
            self.buckets = {}

        def upload_file(self, file_path: str, bucket: str, key: str) -> bool:
            if bucket not in self.buckets:
                self.buckets[bucket] = {}
            self.buckets[bucket][key] = file_path
            return True

        def download_file(self, bucket: str, key: str, file_path: str) -> bool:
            return bucket in self.buckets and key in self.buckets[bucket]

    mock_s3 = MockS3()
    return mock_s3


# ============================================================================
# Test Markers and Configuration
# ============================================================================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "pipeline: marks tests for pipeline components"
    )
    config.addinivalue_line(
        "markers", "pii: marks tests for PII detection"
    )
    config.addinivalue_line(
        "markers", "quality: marks tests for data quality"
    )
