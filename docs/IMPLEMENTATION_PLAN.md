# Atlas Data Pipeline Platform - Implementation Plan

**Version:** 1.0
**Date:** January 2026
**Duration:** 8 Weeks
**Team Size:** 3-5 Developers

---

## Executive Summary

### Project Overview

The Atlas Data Pipeline Platform is a production-grade data infrastructure system designed to transform raw data from multiple sources into AI-ready, compliant datasets. The platform implements the medallion architecture (Bronze/Silver/Gold) with integrated PII detection, data quality validation, and comprehensive lineage tracking.

**Key Objectives:**
- Build automated data pipelines from source systems to AI-ready outputs
- Ensure GDPR compliance with automated PII detection and handling
- Implement comprehensive data quality framework (6 dimensions)
- Enable full data lineage tracking and impact analysis
- Provide REST API for pipeline orchestration and monitoring
- Create foundation for future AI/ML initiatives

### Success Criteria

1. **Functional:** Process 100K+ records through Bronze → Silver → Gold layers
2. **Quality:** Achieve >95% data quality score across all dimensions
3. **Compliance:** 100% PII detection rate with automated masking
4. **Performance:** <5 minute processing time for 10K record batches
5. **Reliability:** 99% pipeline success rate with automated retry logic
6. **Observability:** Real-time monitoring dashboard with lineage visualization

### Timeline Overview

```
Week 1-2: Foundation       ████████░░░░░░░░  Development Environment + Core Infrastructure
Week 3-4: Core Pipeline    ░░░░░░░░████████  Bronze/Silver/Gold + PII + Quality
Week 5-6: API & Services   ░░░░░░░░░░░░████  FastAPI + Celery + Lineage
Week 7-8: Dashboard & Bot  ░░░░░░░░░░░░░░██  UI + Bot + Testing + Docs
```

### Team Requirements

**Required Roles:**
- **Tech Lead / Architect** (1): System design, integration oversight, technical decisions
- **Backend Engineers** (2): Python/FastAPI development, pipeline implementation
- **DevOps Engineer** (1): Infrastructure, Docker, deployment, monitoring
- **QA Engineer** (0.5 FTE): Testing strategy, test automation, quality validation

**Skills Required:**
- Python 3.11+ (FastAPI, Pandas, SQLAlchemy)
- PostgreSQL and SQL optimization
- Docker and container orchestration
- REST API design and async processing
- Data pipeline patterns and ETL
- Testing frameworks (pytest, integration testing)

### Key Milestones

| Week | Milestone | Deliverable | Success Criteria |
|------|-----------|-------------|------------------|
| 2 | Foundation Complete | Running dev environment | All services up, sample data flows |
| 4 | Core Pipeline Live | Bronze→Silver→Gold | 1K records processed with PII masked |
| 6 | API Operational | REST endpoints functional | API can trigger/monitor pipelines |
| 8 | Production Ready | Full platform deployed | End-to-end pipeline with dashboard |

### Risk Assessment

**High Priority Risks:**
- **PII Detection Accuracy:** Presidio may miss custom PII patterns
  - *Mitigation:* Extensive testing, custom recognizers, manual review process
- **Data Quality Variability:** Source data quality may be inconsistent
  - *Mitigation:* Configurable quality thresholds, dead-letter queues
- **Performance at Scale:** Pipeline may not meet performance targets
  - *Mitigation:* Early load testing, horizontal scaling design

**Medium Priority Risks:**
- Integration complexity with multiple repos
- Learning curve for team on new technologies
- Scope creep from stakeholder requests

---

## Technology Stack

### Core Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   FastAPI    │  │   Minimal    │  │   Opsdroid   │          │
│  │     API      │  │     Web      │  │     Bot      │          │
│  │  (REST/Docs) │  │  Dashboard   │  │  (Optional)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │    Celery    │  │   Prefect    │  │ OpenLineage  │          │
│  │   Workers    │  │    (Flow     │  │   (Lineage   │          │
│  │  (Async)     │  │  Orchestr.)  │  │   Tracking)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      PROCESSING LAYER                           │
│  ┌──────────────────────────────────────────────────────┐      │
│  │            PIPELINE CORE (adamiao patterns)           │      │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐     │      │
│  │  │ Bronze │─▶│ Silver │─▶│  Gold  │─▶│   AI   │     │      │
│  │  │  (Raw) │  │(Clean) │  │(Curated│  │ Ready  │     │      │
│  │  └────────┘  └────────┘  └────────┘  └────────┘     │      │
│  └──────────────────────────────────────────────────────┘      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │  Presidio  │  │ Soda Core  │  │  Custom    │               │
│  │   (PII)    │  │ (Quality)  │  │  Business  │               │
│  │            │  │            │  │   Rules    │               │
│  └────────────┘  └────────────┘  └────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                        STORAGE LAYER                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │PostgreSQL  │  │   Redis    │  │  S3/Minio  │               │
│  │ (Metadata) │  │  (Cache/   │  │ (Data Lake)│               │
│  │            │  │   Queue)   │  │            │               │
│  └────────────┘  └────────────┘  └────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

### Repository Sources

| Component | Source Repository | Version | Purpose | License |
|-----------|------------------|---------|---------|---------|
| **Pipeline Patterns** | adamiao/data-pipeline-patterns | Latest | Retry logic, error handling | MIT |
| **API Template** | tiangolo/full-stack-fastapi-template | Latest | FastAPI + PostgreSQL + Docker | MIT |
| **PII Detection** | microsoft/presidio | 2.2+ | PII detection/anonymization | MIT |
| **Quality Checks** | sodadata/soda-core | 3.0+ | Data quality validation | Apache 2.0 |
| **Lineage** | OpenLineage/OpenLineage | 1.0+ | Data lineage standard | Apache 2.0 |
| **Lineage Backend** | MarquezProject/marquez | Latest | Lineage storage/visualization | Apache 2.0 |
| **Orchestration** | PrefectHQ/prefect | 2.0+ | Workflow orchestration | Apache 2.0 |
| **Web UI** | testdrivenio/flask-spa-same-origin | Latest | Minimal dashboard pattern | MIT |

### Why Each Was Chosen

**adamiao/data-pipeline-patterns:**
- Production-tested retry patterns with exponential backoff
- Robust error handling for transient failures
- Configuration-as-code approach
- Real-world patterns from AI/ML projects

**tiangolo/full-stack-fastapi-template:**
- Modern FastAPI + PostgreSQL + Docker setup
- Alembic migrations for schema management
- Authentication patterns (JWT)
- Production-ready project structure
- Created by FastAPI author (best practices)

**microsoft/presidio:**
- Industry standard for PII detection
- Supports 20+ PII entity types (names, emails, SSN, credit cards)
- Customizable recognizers for domain-specific PII
- GDPR-compliant anonymization strategies
- Multi-language support (English, Danish, etc.)
- Active development and strong community

**sodadata/soda-core:**
- Declarative data quality checks (YAML)
- 6 dimensions of quality (completeness, validity, etc.)
- Integration with data catalogs
- SQL-based for database compatibility
- Built-in anomaly detection
- Open source with enterprise support

**OpenLineage/OpenLineage:**
- Linux Foundation standard for data lineage
- Vendor-neutral specification
- Column-level lineage tracking
- Integration with major orchestrators
- Growing ecosystem of tools
- Future-proof choice

**MarquezProject/marquez:**
- Reference implementation of OpenLineage
- Visual lineage graph UI
- Impact analysis capabilities
- REST API for programmatic access
- Active community support
- Open source

**PrefectHQ/prefect:**
- Modern Python-native orchestration
- Dynamic DAGs (no compilation needed)
- Built-in retry and error handling
- Real-time monitoring
- Easy integration with FastAPI
- Free tier for development

**testdrivenio/flask-spa-same-origin:**
- Minimal viable dashboard pattern
- Single-page app with REST backend
- Easy to extend with React/Vue
- Same-origin for simplified security
- Focus on functionality over complexity

### Version Compatibility Matrix

| Component | Version | Python | PostgreSQL | Notes |
|-----------|---------|--------|------------|-------|
| Python | 3.11+ | - | - | Use 3.11 for performance |
| FastAPI | 0.109+ | 3.11+ | - | Latest stable |
| SQLAlchemy | 2.0+ | 3.11+ | 12+ | Use 2.0 syntax |
| Alembic | 1.13+ | 3.11+ | 12+ | Database migrations |
| Pandas | 2.2+ | 3.11+ | - | Arrow backend |
| Presidio | 2.2+ | 3.8+ | - | Latest stable |
| Soda Core | 3.0+ | 3.8+ | 12+ | Latest major version |
| Celery | 5.3+ | 3.8+ | - | With Redis 7+ |
| Prefect | 2.14+ | 3.8+ | - | Latest 2.x |
| PostgreSQL | 15+ | - | - | Use latest stable |
| Redis | 7+ | - | - | For caching + Celery |
| Docker | 24+ | - | - | Use Docker Compose v2 |

**Critical Compatibility Notes:**
- Python 3.11+ required for performance (up to 25% faster than 3.10)
- SQLAlchemy 2.0+ uses new syntax (breaking changes from 1.4)
- Pandas 2.2+ has PyArrow backend for better performance
- PostgreSQL 15+ for JSONB performance improvements
- Use `presidio-analyzer` and `presidio-anonymizer` separately

---

## Phase 1: Foundation (Weeks 1-2)

**Objective:** Establish development environment, project structure, and core infrastructure

### Week 1: Development Environment Setup

#### Day 1-2: Project Initialization

**Tasks:**
1. Clone and configure tiangolo/full-stack-fastapi-template
2. Adapt project structure for Atlas requirements
3. Setup version control (Git repository)
4. Configure VS Code / IDE with Python extensions
5. Create initial documentation structure

**Deliverables:**
- [ ] Git repository initialized with `.gitignore`
- [ ] Project structure adapted from tiangolo template
- [ ] Development branch strategy defined (main, develop, feature/*)
- [ ] README.md with setup instructions
- [ ] Team onboarding document

**Acceptance Criteria:**
- All team members can clone repository
- Development environment documented
- Project structure follows FastAPI best practices
- Git workflow established (feature branches, PR process)

**Estimated Hours:** 12h (Tech Lead: 8h, Backend: 4h)

**Files to Create:**
```
atlas-pipeline/
├── README.md                 # Project overview, setup
├── .gitignore               # Python, Docker, IDE exclusions
├── .env.example             # Environment variable template
├── pyproject.toml           # Python project config (Poetry/PDM)
├── docker-compose.yml       # Multi-service orchestration
├── Dockerfile               # API service container
└── docs/
    ├── SETUP.md            # Detailed setup instructions
    ├── ARCHITECTURE.md     # System architecture
    └── API.md              # API documentation
```

---

#### Day 3-4: Core Infrastructure Deployment

**Tasks:**
1. Setup PostgreSQL database (Docker container)
2. Configure Redis for caching and Celery
3. Setup MinIO for local S3-compatible storage
4. Create initial database schema (Alembic migrations)
5. Verify all services communicate

**Deliverables:**
- [ ] `docker-compose.yml` with PostgreSQL, Redis, MinIO
- [ ] Database initialization script
- [ ] Alembic migration for core tables
- [ ] Connection verification script
- [ ] Service health check endpoints

**Acceptance Criteria:**
- `docker-compose up` starts all services
- PostgreSQL accessible with test connection
- Redis accessible and responds to PING
- MinIO accessible with test bucket created
- All services pass health checks

**Estimated Hours:** 16h (DevOps: 12h, Backend: 4h)

**Docker Compose Structure:**
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: atlas_pipelines
      POSTGRES_USER: atlas
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U atlas"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

volumes:
  postgres_data:
  minio_data:
```

**Database Schema (Alembic Migration):**
```python
# alembic/versions/001_initial_schema.py
"""Initial schema

Revision ID: 001
Create Date: 2026-01-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Core pipeline runs table
    op.create_table(
        'pipeline_runs',
        sa.Column('run_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('pipeline_name', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('input_params', postgresql.JSONB),
        sa.Column('result_data', postgresql.JSONB),
        sa.Column('error_message', sa.Text),
        sa.Index('ix_pipeline_runs_status', 'status'),
        sa.Index('ix_pipeline_runs_created', 'created_at'),
    )

    # Data quality metrics table
    op.create_table(
        'quality_metrics',
        sa.Column('metric_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('table_name', sa.String(200), nullable=False),
        sa.Column('layer', sa.String(20), nullable=False),  # bronze/silver/gold
        sa.Column('metric_type', sa.String(50), nullable=False),
        sa.Column('metric_value', sa.Float),
        sa.Column('threshold', sa.Float),
        sa.Column('passed', sa.Boolean),
        sa.Column('measured_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['run_id'], ['pipeline_runs.run_id']),
    )

    # PII detection results table
    op.create_table(
        'pii_detections',
        sa.Column('detection_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('table_name', sa.String(200), nullable=False),
        sa.Column('column_name', sa.String(200), nullable=False),
        sa.Column('pii_type', sa.String(50), nullable=False),
        sa.Column('instances_found', sa.Integer),
        sa.Column('anonymization_strategy', sa.String(50)),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['run_id'], ['pipeline_runs.run_id']),
    )

    # Data lineage table
    op.create_table(
        'data_lineage',
        sa.Column('lineage_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_dataset', sa.String(200), nullable=False),
        sa.Column('target_dataset', sa.String(200), nullable=False),
        sa.Column('transformation_type', sa.String(100)),
        sa.Column('columns_affected', postgresql.ARRAY(sa.String)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['run_id'], ['pipeline_runs.run_id']),
        sa.Index('ix_lineage_source', 'source_dataset'),
        sa.Index('ix_lineage_target', 'target_dataset'),
    )

def downgrade():
    op.drop_table('data_lineage')
    op.drop_table('pii_detections')
    op.drop_table('quality_metrics')
    op.drop_table('pipeline_runs')
```

**Verification Script:**
```python
# scripts/verify_infrastructure.py
"""Verify all infrastructure services are operational"""

import asyncio
import asyncpg
import redis
from minio import Minio
from typing import Dict, Any

async def check_postgres() -> Dict[str, Any]:
    """Verify PostgreSQL connection"""
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            database='atlas_pipelines',
            user='atlas',
            password='atlas_password'
        )
        version = await conn.fetchval('SELECT version()')
        await conn.close()
        return {"status": "ok", "version": version}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def check_redis() -> Dict[str, Any]:
    """Verify Redis connection"""
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        info = r.info('server')
        return {"status": "ok", "version": info['redis_version']}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def check_minio() -> Dict[str, Any]:
    """Verify MinIO connection"""
    try:
        client = Minio(
            "localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False
        )
        # Create test bucket
        bucket_name = "atlas-bronze"
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
        return {"status": "ok", "bucket": bucket_name}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def main():
    """Run all verification checks"""
    print("🔍 Verifying Atlas Infrastructure...\n")

    print("PostgreSQL:", await check_postgres())
    print("Redis:", check_redis())
    print("MinIO:", check_minio())

    print("\n✅ All services verified!")

if __name__ == "__main__":
    asyncio.run(main())
```

---

#### Day 5: Project Structure and Configuration

**Tasks:**
1. Create Python package structure following tiangolo patterns
2. Setup configuration management (Pydantic settings)
3. Implement logging framework
4. Create base classes and utilities
5. Setup pytest and test structure

**Deliverables:**
- [ ] Python package structure with proper `__init__.py` files
- [ ] `config/settings.py` with environment-based configuration
- [ ] Logging configuration with structured logging
- [ ] Base models and schemas
- [ ] Test framework configured with fixtures

**Acceptance Criteria:**
- Configuration loads from environment variables
- Logging outputs structured JSON logs
- Base classes provide common functionality
- Tests run with `pytest` command
- Code coverage reporting enabled

**Estimated Hours:** 12h (Backend: 12h)

**Project Structure:**
```
atlas-pipeline/
├── src/
│   ├── atlas/
│   │   ├── __init__.py
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   └── settings.py          # Pydantic settings
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── database.py          # DB session management
│   │   │   ├── logging.py           # Structured logging
│   │   │   └── exceptions.py        # Custom exceptions
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py          # SQLAlchemy models
│   │   │   └── quality.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py          # Pydantic schemas
│   │   │   └── quality.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── main.py              # FastAPI app
│   │   │   ├── dependencies.py      # DI functions
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── pipelines.py
│   │   │       └── quality.py
│   │   ├── pipeline/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py      # Main pipeline logic
│   │   │   ├── bronze_layer.py
│   │   │   ├── silver_layer.py
│   │   │   ├── gold_layer.py
│   │   │   ├── pii_detector.py      # Presidio integration
│   │   │   └── quality_validator.py # Soda integration
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── lineage_tracker.py   # OpenLineage
│   │   │   └── storage.py           # MinIO integration
│   │   └── tasks/
│   │       ├── __init__.py
│   │       └── celery_tasks.py      # Async tasks
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   ├── unit/
│   │   ├── test_pii_detector.py
│   │   └── test_quality_validator.py
│   └── integration/
│       ├── test_pipeline_flow.py
│       └── test_api_endpoints.py
└── scripts/
    ├── seed_data.py                 # Sample data generator
    └── run_tests.sh                 # Test runner
```

**Configuration Management:**
```python
# src/atlas/config/settings.py
"""Configuration management using Pydantic"""

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    WHY: Pydantic Settings for type-safe configuration
    - Loads from environment variables
    - Provides validation
    - Supports multiple environments (dev/staging/prod)
    """

    # Application
    APP_NAME: str = "Atlas Data Pipeline"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # development, staging, production

    # Database
    POSTGRES_USER: str = "atlas"
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "atlas_pipelines"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # MinIO (S3-compatible storage)
    MINIO_HOST: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = False

    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    @property
    def CELERY_BROKER(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL

    # Prefect (optional)
    PREFECT_API_URL: Optional[str] = None

    # OpenLineage / Marquez
    MARQUEZ_URL: str = "http://localhost:5000"
    LINEAGE_NAMESPACE: str = "atlas_production"

    # PII Detection (Presidio)
    PII_LANGUAGES: list[str] = ["da", "en"]
    PII_CONFIDENCE_THRESHOLD: float = 0.7
    PII_ANONYMIZATION_STRATEGY: str = "hash"  # hash, mask, redact

    # Data Quality (Soda)
    SODA_CONFIG_PATH: str = "config/soda/"
    QUALITY_THRESHOLD_COMPLETENESS: float = 0.95
    QUALITY_THRESHOLD_UNIQUENESS: float = 0.99
    QUALITY_THRESHOLD_VALIDITY: float = 0.95

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**Structured Logging:**
```python
# src/atlas/core/logging.py
"""Structured logging configuration"""

import logging
import sys
from typing import Any
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """
    WHY: JSON logging for structured log analysis
    - Easy parsing for log aggregation (ELK, Datadog)
    - Includes context (run_id, pipeline_name, etc.)
    - Machine-readable format
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "run_id"):
            log_data["run_id"] = record.run_id
        if hasattr(record, "pipeline_name"):
            log_data["pipeline_name"] = record.pipeline_name

        return json.dumps(log_data)

def setup_logging(log_level: str = "INFO", log_format: str = "json"):
    """
    Configure application logging

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Output format (json or text)
    """
    handler = logging.StreamHandler(sys.stdout)

    if log_format == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(handler)

    # Quiet noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
```

---

### Week 2: Sample Data and Initial Pipeline

#### Day 6-7: Sample Data Generation

**Tasks:**
1. Create sample data generator for customer data
2. Generate Bronze layer test data (CSV files)
3. Setup data fixtures for testing
4. Create data quality issues intentionally (for testing)
5. Document data schema and formats

**Deliverables:**
- [ ] Sample data generator script
- [ ] 1000 customer records with PII
- [ ] 100 order records with quality issues
- [ ] Data schema documentation
- [ ] Test data fixtures for pytest

**Acceptance Criteria:**
- Sample data includes realistic PII (names, emails, phones)
- Data includes intentional quality issues (nulls, duplicates)
- Data fixtures load in <1 second
- Schema documentation matches generated data

**Estimated Hours:** 10h (Backend: 10h)

**Sample Data Generator:**
```python
# scripts/generate_sample_data.py
"""Generate realistic sample data for testing"""

import pandas as pd
import random
from faker import Faker
from datetime import datetime, timedelta
import uuid

fake = Faker(['da_DK', 'en_US'])  # Danish and English

def generate_customers(num_records: int = 1000) -> pd.DataFrame:
    """
    Generate customer data with PII and quality issues

    WHY: Need realistic test data with:
    - Valid PII for Presidio testing
    - Quality issues for Soda testing
    - Realistic distributions
    """

    customers = []

    for i in range(num_records):
        # WHY: 5% of records have missing email (completeness test)
        email = fake.email() if random.random() > 0.05 else None

        # WHY: 2% have invalid phone format (validity test)
        if random.random() > 0.02:
            phone = fake.phone_number()
        else:
            phone = "invalid_phone"

        # WHY: 1% are duplicates (uniqueness test)
        if random.random() < 0.01 and i > 0:
            customer_id = customers[-1]['customer_id']
        else:
            customer_id = f"C{i:06d}"

        customer = {
            'customer_id': customer_id,
            'customer_name': fake.name(),
            'email_address': email,
            'phone_number': phone,
            'address': fake.address(),
            'city': fake.city(),
            'postal_code': fake.postcode(),
            'country': 'Denmark',
            'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=90),
            'created_at': datetime.now() - timedelta(days=random.randint(1, 365)),
            'is_active': random.choice([True, False]),
            'customer_tier': random.choice(['bronze', 'silver', 'gold', 'platinum']),
            'notes': fake.text(max_nb_chars=200) if random.random() > 0.3 else None
        }

        customers.append(customer)

    df = pd.DataFrame(customers)
    return df

def generate_orders(num_records: int = 500) -> pd.DataFrame:
    """Generate order data with relationships to customers"""

    orders = []

    for i in range(num_records):
        # WHY: 3% missing customer_id (referential integrity test)
        customer_id = f"C{random.randint(0, 999):06d}" if random.random() > 0.03 else None

        # WHY: 2% have negative amounts (validity test)
        amount = random.uniform(10, 5000) if random.random() > 0.02 else random.uniform(-100, -10)

        order = {
            'order_id': f"O{i:08d}",
            'customer_id': customer_id,
            'order_date': datetime.now() - timedelta(days=random.randint(1, 365)),
            'order_amount': round(amount, 2),
            'currency': 'DKK',
            'status': random.choice(['pending', 'completed', 'cancelled', 'refunded']),
            'payment_method': random.choice(['credit_card', 'invoice', 'mobile_pay', None]),
            'shipping_address': fake.address() if random.random() > 0.1 else None
        }

        orders.append(order)

    df = pd.DataFrame(orders)
    return df

if __name__ == "__main__":
    print("Generating sample data...")

    # Generate data
    customers = generate_customers(1000)
    orders = generate_orders(500)

    # Save to Bronze layer
    customers.to_csv('data/bronze/customers.csv', index=False)
    orders.to_csv('data/bronze/orders.csv', index=False)

    print(f"✅ Generated {len(customers)} customers")
    print(f"✅ Generated {len(orders)} orders")
    print(f"📊 Quality issues intentionally included:")
    print(f"   - {customers['email_address'].isna().sum()} missing emails")
    print(f"   - {customers.duplicated('customer_id').sum()} duplicate customer IDs")
    print(f"   - {orders['customer_id'].isna().sum()} orders with missing customer_id")
    print(f"   - {(orders['order_amount'] < 0).sum()} orders with negative amounts")
```

---

#### Day 8-10: Initial Pipeline Implementation

**Tasks:**
1. Implement Bronze layer ingestion (CSV → Database/MinIO)
2. Create basic Silver layer transformation
3. Implement simple Gold layer aggregation
4. Add basic error handling and logging
5. Write unit tests for each layer

**Deliverables:**
- [ ] Bronze layer ingestion module
- [ ] Silver layer transformation module
- [ ] Gold layer aggregation module
- [ ] Pipeline orchestrator class
- [ ] Unit tests with >80% coverage

**Acceptance Criteria:**
- Bronze layer successfully ingests CSV files
- Silver layer applies basic transformations
- Gold layer produces aggregated output
- All tests pass
- End-to-end pipeline completes in <30 seconds for 1K records

**Estimated Hours:** 24h (Backend: 24h)

**Bronze Layer Implementation:**
```python
# src/atlas/pipeline/bronze_layer.py
"""Bronze layer: Raw data ingestion"""

import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import uuid

from atlas.config.settings import settings
from atlas.core.database import get_db_session
from atlas.models.pipeline import PipelineRun

logger = logging.getLogger(__name__)

class BronzeLayerIngestion:
    """
    WHY: Bronze layer stores raw data exactly as received
    - No transformations applied
    - Preserves original format
    - Append-only for audit trail
    - Basis for all downstream processing
    """

    def __init__(self, run_id: Optional[str] = None):
        self.run_id = run_id or str(uuid.uuid4())

    async def ingest_csv(
        self,
        file_path: Path,
        table_name: str,
        source_system: str = "unknown"
    ) -> pd.DataFrame:
        """
        Ingest CSV file into Bronze layer

        Args:
            file_path: Path to CSV file
            table_name: Target table name (e.g., 'customers')
            source_system: Name of source system (e.g., 'CRM')

        Returns:
            DataFrame with ingested data
        """
        logger.info(
            f"Ingesting Bronze data",
            extra={
                "run_id": self.run_id,
                "table_name": table_name,
                "source": str(file_path)
            }
        )

        try:
            # WHY: Read CSV with pandas for flexibility
            df = pd.read_csv(file_path)

            # WHY: Add metadata columns for lineage tracking
            df['_bronze_ingested_at'] = datetime.utcnow()
            df['_bronze_run_id'] = self.run_id
            df['_bronze_source_file'] = str(file_path)
            df['_bronze_source_system'] = source_system

            # WHY: Store in MinIO for durability (not implemented here)
            # bronze_path = f"s3://atlas-bronze/{table_name}/{self.run_id}.parquet"
            # df.to_parquet(bronze_path)

            # WHY: For now, store in local database
            # In production, Bronze should be in data lake (S3/MinIO)
            logger.info(
                f"Bronze ingestion complete",
                extra={
                    "run_id": self.run_id,
                    "rows": len(df),
                    "columns": len(df.columns)
                }
            )

            return df

        except Exception as e:
            logger.error(
                f"Bronze ingestion failed",
                extra={
                    "run_id": self.run_id,
                    "error": str(e)
                }
            )
            raise
```

**Silver Layer Implementation:**
```python
# src/atlas/pipeline/silver_layer.py
"""Silver layer: Cleaned and standardized data"""

import pandas as pd
import logging
from datetime import datetime
from typing import Optional
import uuid

logger = logging.getLogger(__name__)

class SilverLayerTransformation:
    """
    WHY: Silver layer applies data quality and standardization
    - Deduplication
    - Data type standardization
    - Null handling
    - Format validation
    - Basic business rules
    """

    def __init__(self, run_id: Optional[str] = None):
        self.run_id = run_id or str(uuid.uuid4())

    async def transform_customers(
        self,
        bronze_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Transform customer data: Bronze → Silver

        Transformations:
        1. Remove duplicates based on customer_id
        2. Standardize column names (lowercase, underscores)
        3. Validate email format
        4. Standardize phone numbers
        5. Handle null values
        """
        logger.info(
            f"Transforming customers to Silver",
            extra={"run_id": self.run_id, "rows": len(bronze_df)}
        )

        df = bronze_df.copy()

        # 1. Remove duplicates
        # WHY: Keep first occurrence, log duplicates
        duplicates = df.duplicated(subset='customer_id', keep='first')
        if duplicates.any():
            logger.warning(
                f"Removing {duplicates.sum()} duplicate customers",
                extra={"run_id": self.run_id}
            )
            df = df[~duplicates]

        # 2. Standardize phone numbers
        # WHY: Convert to E.164 format (+45XXXXXXXX)
        df['phone_number'] = df['phone_number'].apply(self._standardize_phone)

        # 3. Validate email format
        # WHY: Mark invalid emails for review
        df['email_valid'] = df['email_address'].apply(self._is_valid_email)

        # 4. Add metadata
        df['_silver_processed_at'] = datetime.utcnow()
        df['_silver_run_id'] = self.run_id

        logger.info(
            f"Silver transformation complete",
            extra={
                "run_id": self.run_id,
                "rows_output": len(df),
                "rows_dropped": len(bronze_df) - len(df)
            }
        )

        return df

    @staticmethod
    def _standardize_phone(phone: Optional[str]) -> Optional[str]:
        """Standardize phone number to E.164 format"""
        if pd.isna(phone) or not isinstance(phone, str):
            return None

        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone))

        # Add Danish country code if missing
        if len(digits) == 8:
            return f"+45{digits}"
        elif len(digits) == 10 and digits.startswith("45"):
            return f"+{digits}"

        return phone  # Return original if format unclear

    @staticmethod
    def _is_valid_email(email: Optional[str]) -> bool:
        """Basic email validation"""
        if pd.isna(email):
            return False
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
```

---

### Phase 1 Deliverables Summary

**Week 1 Deliverables:**
- ✅ Development environment fully configured
- ✅ Docker Compose with PostgreSQL, Redis, MinIO
- ✅ Initial database schema with Alembic migrations
- ✅ Project structure following best practices
- ✅ Configuration management and logging

**Week 2 Deliverables:**
- ✅ Sample data generator (1000 customers, 500 orders)
- ✅ Bronze layer ingestion module
- ✅ Silver layer transformation module
- ✅ Gold layer aggregation module (basic)
- ✅ Unit tests with >80% coverage

**Success Criteria:**
- [ ] All team members can run `docker-compose up` successfully
- [ ] Sample data generates with realistic PII and quality issues
- [ ] Simple pipeline (Bronze → Silver → Gold) completes end-to-end
- [ ] Unit tests pass with >80% code coverage
- [ ] Documentation complete for setup and architecture

**Risks Identified:**
- Learning curve for tiangolo template patterns
- MinIO setup complexity (fallback: local filesystem)
- Test data realism (mitigate with Faker library)

---

## Phase 2: Core Pipeline (Weeks 3-4)

**Objective:** Implement production-grade pipeline with PII detection, quality validation, and retry logic

### Week 3: PII Detection and Quality Framework

#### Day 11-12: Presidio PII Detection Integration

**Tasks:**
1. Install and configure Microsoft Presidio
2. Implement PII detector class with adamiao retry patterns
3. Create custom PII recognizers for Danish data
4. Integrate with Silver layer transformation
5. Write comprehensive PII detection tests

**Deliverables:**
- [ ] Presidio integration module
- [ ] Custom Danish CPR recognizer
- [ ] PII anonymization strategies (hash, mask, redact)
- [ ] PII detection results storage (database table)
- [ ] Unit tests for PII detection

**Acceptance Criteria:**
- Presidio detects standard PII types (email, phone, name)
- Custom recognizer detects Danish CPR numbers
- PII anonymization works for all strategies
- Detection results stored in database with lineage
- Tests achieve >90% PII detection rate

**Estimated Hours:** 16h (Backend: 16h)

**Implementation Plan:**

```python
# src/atlas/pipeline/pii_detector.py
"""PII Detection using Microsoft Presidio with adamiao patterns"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
import pandas as pd
from datetime import datetime

# Presidio imports
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Retry logic (adamiao pattern)
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from atlas.config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class PIIDetectionResult:
    """Result of PII detection for a column"""
    column_name: str
    pii_type: str
    instances_found: int
    confidence_scores: List[float]
    sample_values: List[str]  # First 3 for verification
    detected_at: datetime

class PIIDetector:
    """
    WHY: Detect and anonymize PII using Presidio
    - GDPR compliance requirement
    - Supports multiple PII types and languages
    - Integrates with Silver layer transformation
    - Provides audit trail of PII findings
    """

    def __init__(self):
        self.analyzer = self._setup_analyzer()
        self.anonymizer = AnonymizerEngine()

        logger.info("Initialized PII detector with custom recognizers")

    def _setup_analyzer(self) -> AnalyzerEngine:
        """
        Setup Presidio analyzer with custom recognizers

        WHY: Add Danish-specific PII patterns
        - CPR number (Danish social security)
        - Danish phone format
        - Danish address patterns
        """

        # Initialize NLP engine
        nlp_configuration = {
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": "en", "model_name": "en_core_web_sm"},
                {"lang_code": "da", "model_name": "da_core_news_sm"}
            ]
        }
        provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
        nlp_engine = provider.create_engine()

        # Create registry with custom recognizers
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers(nlp_engine=nlp_engine)

        # Add Danish CPR recognizer
        # WHY: CPR format: DDMMYY-XXXX or DDMMYYXXXX
        cpr_recognizer = PatternRecognizer(
            supported_entity="DK_CPR",
            name="Danish CPR Number Recognizer",
            supported_language="da",
            patterns=[
                {
                    "name": "cpr_pattern",
                    "regex": r"\b\d{6}[-\s]?\d{4}\b",
                    "score": 0.9
                }
            ],
            context=["cpr", "personnummer", "social", "sikringsnummer"]
        )
        registry.add_recognizer(cpr_recognizer)

        # Create analyzer with custom registry
        analyzer = AnalyzerEngine(
            registry=registry,
            nlp_engine=nlp_engine
        )

        return analyzer

    @retry(
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=1, max=60),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    async def detect_pii_in_dataframe(
        self,
        df: pd.DataFrame,
        columns_to_scan: Optional[List[str]] = None
    ) -> List[PIIDetectionResult]:
        """
        Scan DataFrame columns for PII

        WHY: Identify all PII before anonymization
        - Required for GDPR compliance
        - Informs anonymization strategy
        - Creates audit trail

        Args:
            df: DataFrame to scan
            columns_to_scan: Specific columns (None = all text columns)

        Returns:
            List of PII detection results
        """

        if columns_to_scan is None:
            # Only scan text/object columns
            columns_to_scan = df.select_dtypes(include=['object']).columns.tolist()

        results = []

        for column in columns_to_scan:
            logger.info(f"Scanning column '{column}' for PII")

            # Collect all non-null values
            values = df[column].dropna().astype(str).tolist()

            if not values:
                continue

            # WHY: Analyze sample of values (performance optimization)
            sample_size = min(100, len(values))
            sample_values = values[:sample_size]

            pii_findings = {}  # entity_type -> list of scores

            for value in sample_values:
                # WHY: Use Presidio to analyze each value
                analyzer_results = self.analyzer.analyze(
                    text=value,
                    language=settings.PII_LANGUAGES[0],  # Primary language
                    entities=None,  # Detect all entity types
                    score_threshold=settings.PII_CONFIDENCE_THRESHOLD
                )

                # Group findings by entity type
                for result in analyzer_results:
                    if result.entity_type not in pii_findings:
                        pii_findings[result.entity_type] = []
                    pii_findings[result.entity_type].append(result.score)

            # WHY: Create detection result for each PII type found
            for pii_type, scores in pii_findings.items():
                # Extrapolate to full column
                instances_found = int(len(scores) / sample_size * len(values))

                result = PIIDetectionResult(
                    column_name=column,
                    pii_type=pii_type,
                    instances_found=instances_found,
                    confidence_scores=scores,
                    sample_values=sample_values[:3],
                    detected_at=datetime.utcnow()
                )
                results.append(result)

                logger.warning(
                    f"Found PII in column '{column}': {pii_type} "
                    f"({instances_found} instances, "
                    f"avg confidence: {sum(scores)/len(scores):.2f})"
                )

        return results

    async def anonymize_dataframe(
        self,
        df: pd.DataFrame,
        detection_results: List[PIIDetectionResult],
        strategy: str = None
    ) -> pd.DataFrame:
        """
        Anonymize PII in DataFrame based on detection results

        WHY: GDPR compliance - mask PII before downstream processing
        - hash: One-way hash (irreversible)
        - mask: Replace with <MASKED>
        - redact: Remove entirely

        Args:
            df: Original DataFrame
            detection_results: PII detection results
            strategy: Anonymization strategy (defaults to settings)

        Returns:
            Anonymized DataFrame
        """

        strategy = strategy or settings.PII_ANONYMIZATION_STRATEGY
        anonymized_df = df.copy()

        # WHY: Define operator for anonymization strategy
        operators = {
            "hash": OperatorConfig("hash", {"hash_type": "sha256"}),
            "mask": OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 100}),
            "redact": OperatorConfig("redact", {})
        }

        if strategy not in operators:
            raise ValueError(f"Unknown anonymization strategy: {strategy}")

        operator = operators[strategy]

        # WHY: Anonymize each column that contains PII
        pii_columns = {result.column_name for result in detection_results}

        for column in pii_columns:
            logger.info(f"Anonymizing column '{column}' using strategy '{strategy}'")

            # Apply anonymization to each value
            anonymized_df[column] = anonymized_df[column].apply(
                lambda x: self._anonymize_value(x, operator) if pd.notna(x) else x
            )

        return anonymized_df

    def _anonymize_value(self, value: str, operator: OperatorConfig) -> str:
        """Anonymize a single value using Presidio"""

        try:
            # Re-analyze value to get structured results
            analysis_results = self.analyzer.analyze(
                text=str(value),
                language=settings.PII_LANGUAGES[0],
                score_threshold=settings.PII_CONFIDENCE_THRESHOLD
            )

            if not analysis_results:
                return value  # No PII detected, return original

            # Anonymize using Presidio
            anonymized_result = self.anonymizer.anonymize(
                text=str(value),
                analyzer_results=analysis_results,
                operators={"DEFAULT": operator}
            )

            return anonymized_result.text

        except Exception as e:
            logger.error(f"Failed to anonymize value: {e}")
            return "<REDACTED_ERROR>"  # Safe fallback
```

**Unit Tests:**

```python
# tests/unit/test_pii_detector.py
"""Unit tests for PII detection"""

import pytest
import pandas as pd
from atlas.pipeline.pii_detector import PIIDetector

@pytest.fixture
def pii_detector():
    """Fixture for PII detector instance"""
    return PIIDetector()

@pytest.fixture
def sample_data_with_pii():
    """Sample data containing various PII types"""
    return pd.DataFrame({
        'customer_id': ['C001', 'C002', 'C003'],
        'name': ['Anders Jensen', 'Maria Nielsen', 'Peter Hansen'],
        'email': ['anders@example.dk', 'maria@test.dk', 'peter@demo.dk'],
        'phone': ['+4512345678', '+4587654321', '+4511223344'],
        'cpr': ['010190-1234', '150585-5678', '220375-9012'],
        'notes': ['Normal text without PII', 'Email: anders@example.dk', None]
    })

@pytest.mark.asyncio
async def test_detect_email_pii(pii_detector, sample_data_with_pii):
    """Test detection of email addresses"""

    results = await pii_detector.detect_pii_in_dataframe(
        sample_data_with_pii,
        columns_to_scan=['email']
    )

    # Should detect EMAIL_ADDRESS entity
    email_results = [r for r in results if r.pii_type == 'EMAIL_ADDRESS']
    assert len(email_results) > 0
    assert email_results[0].instances_found == 3

@pytest.mark.asyncio
async def test_detect_phone_pii(pii_detector, sample_data_with_pii):
    """Test detection of phone numbers"""

    results = await pii_detector.detect_pii_in_dataframe(
        sample_data_with_pii,
        columns_to_scan=['phone']
    )

    # Should detect PHONE_NUMBER entity
    phone_results = [r for r in results if r.pii_type == 'PHONE_NUMBER']
    assert len(phone_results) > 0
    assert phone_results[0].instances_found == 3

@pytest.mark.asyncio
async def test_detect_danish_cpr(pii_detector, sample_data_with_pii):
    """Test detection of Danish CPR numbers"""

    results = await pii_detector.detect_pii_in_dataframe(
        sample_data_with_pii,
        columns_to_scan=['cpr']
    )

    # Should detect DK_CPR entity
    cpr_results = [r for r in results if r.pii_type == 'DK_CPR']
    assert len(cpr_results) > 0
    assert cpr_results[0].instances_found == 3

@pytest.mark.asyncio
async def test_anonymize_with_hash(pii_detector, sample_data_with_pii):
    """Test anonymization with hash strategy"""

    # First detect PII
    detection_results = await pii_detector.detect_pii_in_dataframe(
        sample_data_with_pii,
        columns_to_scan=['email']
    )

    # Then anonymize
    anonymized_df = await pii_detector.anonymize_dataframe(
        sample_data_with_pii,
        detection_results,
        strategy='hash'
    )

    # Original values should be changed
    assert not anonymized_df['email'].equals(sample_data_with_pii['email'])

    # But structure should be preserved
    assert len(anonymized_df) == len(sample_data_with_pii)
    assert list(anonymized_df.columns) == list(sample_data_with_pii.columns)

@pytest.mark.asyncio
async def test_no_pii_in_normal_text(pii_detector):
    """Test that normal text doesn't trigger false positives"""

    df = pd.DataFrame({
        'description': [
            'This is a normal product description',
            'Another regular text without PII',
            'Product specifications and features'
        ]
    })

    results = await pii_detector.detect_pii_in_dataframe(df)

    # Should not detect any PII
    assert len(results) == 0
```

---

#### Day 13-14: Soda Core Quality Framework Integration

**Tasks:**
1. Install and configure Soda Core
2. Create data quality check definitions (YAML)
3. Implement quality validator class
4. Integrate with Silver layer transformation
5. Store quality metrics in database

**Deliverables:**
- [ ] Soda Core integration module
- [ ] Quality check definitions for 6 dimensions
- [ ] Quality metrics storage (database table)
- [ ] Quality dashboard data API
- [ ] Unit tests for quality validation

**Acceptance Criteria:**
- Soda Core executes checks on Silver layer data
- All 6 quality dimensions measured (completeness, uniqueness, etc.)
- Quality scores stored in database with timestamps
- Failed checks trigger alerts
- Tests verify quality validation logic

**Estimated Hours:** 16h (Backend: 16h)

**Implementation:**

```python
# src/atlas/pipeline/quality_validator.py
"""Data quality validation using Soda Core"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

# Soda Core imports
from soda.scan import Scan
from soda.sampler.sampler import Sampler

from atlas.config.settings import settings
from atlas.models.quality import QualityMetric
from atlas.core.database import get_db_session

logger = logging.getLogger(__name__)

@dataclass
class QualityCheckResult:
    """Result of a single quality check"""
    check_name: str
    dimension: str  # completeness, uniqueness, validity, consistency, timeliness, accuracy
    metric_value: float
    threshold: float
    passed: bool
    measured_at: datetime
    details: Optional[str] = None

class QualityValidator:
    """
    WHY: Validate data quality using Soda Core
    - 6 dimensions of data quality
    - Automated quality checks
    - Threshold-based pass/fail
    - Integration with pipeline
    """

    QUALITY_DIMENSIONS = [
        "completeness",
        "uniqueness",
        "validity",
        "consistency",
        "timeliness",
        "accuracy"
    ]

    def __init__(self, run_id: str):
        self.run_id = run_id

    async def validate_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        layer: str,
        checks_file: Optional[str] = None
    ) -> List[QualityCheckResult]:
        """
        Run quality checks on DataFrame

        Args:
            df: DataFrame to validate
            table_name: Name for logging/reporting
            layer: Data layer (bronze/silver/gold)
            checks_file: Path to Soda checks YAML (optional)

        Returns:
            List of quality check results
        """

        logger.info(
            f"Running quality validation on {layer}.{table_name}",
            extra={"run_id": self.run_id, "rows": len(df)}
        )

        # WHY: Use Soda Scan to execute checks
        scan = Scan()
        scan.set_data_source_name("atlas_pipeline")

        # WHY: Add DataFrame as scan target
        scan.add_pandas_dataframe(
            dataset_name=table_name,
            pandas_df=df,
            data_source_name="atlas_pipeline"
        )

        # WHY: Load check definitions
        if checks_file:
            scan.add_sodacl_yaml_file(checks_file)
        else:
            # Use default checks
            scan.add_sodacl_yaml_str(self._get_default_checks(table_name))

        # Execute scan
        scan.execute()

        # WHY: Parse results into standardized format
        results = self._parse_scan_results(scan, table_name, layer)

        # Store results in database
        await self._store_quality_metrics(results, table_name, layer)

        # Log summary
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed

        logger.info(
            f"Quality validation complete: {passed} passed, {failed} failed",
            extra={"run_id": self.run_id}
        )

        return results

    def _get_default_checks(self, table_name: str) -> str:
        """
        Generate default Soda checks for a table

        WHY: Provide sensible defaults for common quality checks
        - Completeness: Required fields not null
        - Uniqueness: Primary keys are unique
        - Validity: Values within expected ranges
        """

        # WHY: Define checks in Soda YAML format
        checks_yaml = f"""
checks for {table_name}:

  # COMPLETENESS CHECKS
  - row_count > 0:
      name: Table not empty
      dimension: completeness

  - missing_count(customer_id) = 0:
      name: customer_id is required
      dimension: completeness

  - missing_percent(email_address) < 10:
      name: Email present in >90% rows
      dimension: completeness

  # UNIQUENESS CHECKS
  - duplicate_count(customer_id) = 0:
      name: customer_id is unique
      dimension: uniqueness

  # VALIDITY CHECKS
  - invalid_percent(email_address) < 5:
      name: Email format valid
      format: email
      dimension: validity

  - values_in_set(customer_tier) in ['bronze', 'silver', 'gold', 'platinum']:
      name: Valid customer tiers
      dimension: validity

  # TIMELINESS CHECKS
  - freshness(created_at) < 24h:
      name: Data is recent
      dimension: timeliness
"""

        return checks_yaml

    def _parse_scan_results(
        self,
        scan: Scan,
        table_name: str,
        layer: str
    ) -> List[QualityCheckResult]:
        """
        Parse Soda scan results into standardized format

        WHY: Convert Soda output to our internal format
        - Enables consistent storage and reporting
        - Normalizes across different check types
        """

        results = []

        for check in scan.get_checks():
            # Extract dimension from check metadata
            dimension = check.metrics.get('dimension', 'unknown')

            # Determine pass/fail
            passed = check.outcome == 'pass'

            # Extract metric value and threshold
            metric_value = check.metrics.get('value', 0.0)
            threshold = check.metrics.get('threshold', 0.0)

            result = QualityCheckResult(
                check_name=check.name,
                dimension=dimension,
                metric_value=float(metric_value),
                threshold=float(threshold),
                passed=passed,
                measured_at=datetime.utcnow(),
                details=check.get_log_diagnostic_lines() if not passed else None
            )

            results.append(result)

        return results

    async def _store_quality_metrics(
        self,
        results: List[QualityCheckResult],
        table_name: str,
        layer: str
    ):
        """Store quality metrics in database"""

        async with get_db_session() as session:
            for result in results:
                metric = QualityMetric(
                    run_id=self.run_id,
                    table_name=table_name,
                    layer=layer,
                    metric_type=result.check_name,
                    dimension=result.dimension,
                    metric_value=result.metric_value,
                    threshold=result.threshold,
                    passed=result.passed,
                    details=result.details
                )
                session.add(metric)

            await session.commit()

        logger.debug(
            f"Stored {len(results)} quality metrics",
            extra={"run_id": self.run_id}
        )

    async def get_quality_score(
        self,
        results: List[QualityCheckResult]
    ) -> Dict[str, float]:
        """
        Calculate overall quality score and per-dimension scores

        WHY: Provide high-level quality metrics
        - Overall score (0-1)
        - Score per dimension
        - Enables tracking quality over time

        Returns:
            Dict with overall and per-dimension scores
        """

        if not results:
            return {"overall": 0.0}

        # Calculate overall score (% of checks passed)
        overall_score = sum(1 for r in results if r.passed) / len(results)

        # Calculate per-dimension scores
        dimension_scores = {}
        for dimension in self.QUALITY_DIMENSIONS:
            dimension_checks = [r for r in results if r.dimension == dimension]
            if dimension_checks:
                score = sum(1 for r in dimension_checks if r.passed) / len(dimension_checks)
                dimension_scores[dimension] = score

        return {
            "overall": overall_score,
            **dimension_scores
        }
```

**Soda Checks Configuration:**

```yaml
# config/soda/checks/customers.yml
# WHY: Declarative quality checks for customers table
# - Covers all 6 quality dimensions
# - Thresholds based on business requirements
# - Easy to maintain and version control

checks for customers:

  # ========================================
  # COMPLETENESS (>95%)
  # ========================================

  - row_count > 0:
      name: customers_not_empty
      dimension: completeness
      severity: critical

  - missing_count(customer_id) = 0:
      name: customer_id_required
      dimension: completeness
      severity: critical

  - missing_percent(customer_name) < 5:
      name: customer_name_completeness
      dimension: completeness
      severity: warning

  - missing_percent(email_address) < 10:
      name: email_completeness
      dimension: completeness
      severity: warning

  # ========================================
  # UNIQUENESS (>99%)
  # ========================================

  - duplicate_count(customer_id) = 0:
      name: customer_id_unique
      dimension: uniqueness
      severity: critical

  - duplicate_percent(email_address) < 1:
      name: email_mostly_unique
      dimension: uniqueness
      severity: warning

  # ========================================
  # VALIDITY (>95%)
  # ========================================

  - invalid_percent(email_address) < 5:
      name: email_format_valid
      valid_format: email
      dimension: validity
      severity: warning

  - invalid_percent(phone_number) < 5:
      name: phone_format_valid
      valid_regex: '^\+45\d{8}$'  # Danish E.164 format
      dimension: validity
      severity: warning

  - values_in_set(customer_tier):
      name: valid_customer_tiers
      valid_values: ['bronze', 'silver', 'gold', 'platinum']
      dimension: validity
      severity: error

  - values_in_set(country):
      name: valid_countries
      valid_values: ['Denmark', 'Sweden', 'Norway', 'Germany', 'UK']
      dimension: validity
      severity: warning

  # ========================================
  # CONSISTENCY (>99%)
  # ========================================

  - schema:
      name: schema_matches_silver_standard
      dimension: consistency
      warn:
        when schema changes:
          - column add
          - column delete
          - column type change
      fail:
        when required columns missing:
          - customer_id
          - customer_name
          - created_at

  # ========================================
  # TIMELINESS (<24h)
  # ========================================

  - freshness(created_at) < 24h:
      name: data_is_recent
      dimension: timeliness
      severity: warning

  # ========================================
  # ACCURACY (sample-based)
  # ========================================

  - avg(customer_tier_score) between 0 and 100:
      name: tier_scores_in_range
      dimension: accuracy
      severity: error
```

---

#### Day 15: Integration and End-to-End Testing

**Tasks:**
1. Integrate PII detection into Silver layer
2. Integrate quality validation into Silver layer
3. Update pipeline orchestrator
4. Write end-to-end integration tests
5. Performance testing with 10K records

**Deliverables:**
- [ ] Updated Silver layer with PII + quality integration
- [ ] Pipeline orchestrator handles errors and retries
- [ ] End-to-end integration tests
- [ ] Performance benchmark results
- [ ] Integration documentation

**Acceptance Criteria:**
- Complete pipeline (Bronze → Silver with PII + Quality → Gold) works
- PII detection and anonymization automatic in Silver layer
- Quality validation automatic in Silver layer
- Pipeline completes 10K records in <5 minutes
- All integration tests pass

**Estimated Hours:** 8h (Backend: 8h)

**Updated Pipeline Orchestrator:**

```python
# src/atlas/pipeline/orchestrator.py
"""Main pipeline orchestrator"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime
import pandas as pd
import uuid

from atlas.pipeline.bronze_layer import BronzeLayerIngestion
from atlas.pipeline.silver_layer import SilverLayerTransformation
from atlas.pipeline.gold_layer import GoldLayerAggregation
from atlas.pipeline.pii_detector import PIIDetector
from atlas.pipeline.quality_validator import QualityValidator

logger = logging.getLogger(__name__)

class PipelineOrchestrator:
    """
    WHY: Orchestrate end-to-end data pipeline
    - Coordinates all pipeline layers
    - Handles errors and retries
    - Tracks lineage and metrics
    - Provides single entry point for pipeline execution
    """

    def __init__(self, run_id: Optional[str] = None):
        self.run_id = run_id or str(uuid.uuid4())

        # Initialize pipeline components
        self.bronze = BronzeLayerIngestion(run_id=self.run_id)
        self.silver = SilverLayerTransformation(run_id=self.run_id)
        self.gold = GoldLayerAggregation(run_id=self.run_id)
        self.pii_detector = PIIDetector()
        self.quality_validator = QualityValidator(run_id=self.run_id)

    async def run_bronze_to_silver(
        self,
        source_file: str,
        table_name: str,
        enable_pii_detection: bool = True,
        enable_quality_checks: bool = True
    ) -> Dict[str, Any]:
        """
        Execute Bronze → Silver pipeline

        WHY: Core transformation with PII and quality
        - Ingest raw data (Bronze)
        - Detect and mask PII
        - Validate data quality
        - Transform to Silver layer

        Args:
            source_file: Path to source CSV file
            table_name: Target table name
            enable_pii_detection: Run PII detection
            enable_quality_checks: Run quality validation

        Returns:
            Pipeline execution metrics
        """

        logger.info(
            f"Starting Bronze → Silver pipeline",
            extra={
                "run_id": self.run_id,
                "table_name": table_name,
                "source_file": source_file
            }
        )

        start_time = datetime.utcnow()
        metrics = {}

        try:
            # STEP 1: Bronze Layer Ingestion
            logger.info("Step 1/5: Bronze layer ingestion")
            bronze_df = await self.bronze.ingest_csv(
                file_path=source_file,
                table_name=table_name
            )
            metrics['bronze_rows'] = len(bronze_df)

            # STEP 2: PII Detection
            pii_results = []
            if enable_pii_detection:
                logger.info("Step 2/5: PII detection")
                pii_results = await self.pii_detector.detect_pii_in_dataframe(
                    bronze_df
                )
                metrics['pii_types_found'] = len(set(r.pii_type for r in pii_results))
                metrics['pii_instances_total'] = sum(r.instances_found for r in pii_results)

            # STEP 3: Silver Transformation
            logger.info("Step 3/5: Silver layer transformation")
            silver_df = await self.silver.transform_customers(bronze_df)
            metrics['silver_rows'] = len(silver_df)
            metrics['rows_dropped'] = len(bronze_df) - len(silver_df)

            # STEP 4: PII Anonymization
            if enable_pii_detection and pii_results:
                logger.info("Step 4/5: PII anonymization")
                silver_df = await self.pii_detector.anonymize_dataframe(
                    silver_df,
                    pii_results
                )
                metrics['pii_anonymized'] = True

            # STEP 5: Quality Validation
            quality_results = []
            if enable_quality_checks:
                logger.info("Step 5/5: Quality validation")
                quality_results = await self.quality_validator.validate_dataframe(
                    silver_df,
                    table_name=table_name,
                    layer="silver"
                )

                quality_scores = await self.quality_validator.get_quality_score(
                    quality_results
                )
                metrics['quality_score'] = quality_scores['overall']
                metrics['quality_checks_passed'] = sum(1 for r in quality_results if r.passed)
                metrics['quality_checks_failed'] = sum(1 for r in quality_results if not r.passed)

            # Calculate duration
            end_time = datetime.utcnow()
            metrics['duration_seconds'] = (end_time - start_time).total_seconds()
            metrics['status'] = 'SUCCESS'

            logger.info(
                f"Pipeline complete",
                extra={
                    "run_id": self.run_id,
                    "duration": metrics['duration_seconds'],
                    "quality_score": metrics.get('quality_score', 'N/A')
                }
            )

            return {
                "run_id": self.run_id,
                "table_name": table_name,
                "metrics": metrics,
                "silver_dataframe": silver_df
            }

        except Exception as e:
            logger.error(
                f"Pipeline failed: {str(e)}",
                extra={"run_id": self.run_id},
                exc_info=True
            )

            end_time = datetime.utcnow()
            metrics['duration_seconds'] = (end_time - start_time).total_seconds()
            metrics['status'] = 'FAILED'
            metrics['error_message'] = str(e)

            raise
```

**Integration Tests:**

```python
# tests/integration/test_pipeline_flow.py
"""End-to-end pipeline integration tests"""

import pytest
import pandas as pd
from pathlib import Path

from atlas.pipeline.orchestrator import PipelineOrchestrator

@pytest.fixture
async def sample_csv_file(tmp_path):
    """Create sample CSV file for testing"""

    data = pd.DataFrame({
        'customer_id': [f'C{i:04d}' for i in range(100)],
        'customer_name': [f'Customer {i}' for i in range(100)],
        'email_address': [f'customer{i}@example.com' for i in range(100)],
        'phone_number': [f'+451234{i:04d}' for i in range(100)],
        'created_at': [pd.Timestamp.now()] * 100
    })

    file_path = tmp_path / "customers.csv"
    data.to_csv(file_path, index=False)

    return file_path

@pytest.mark.asyncio
async def test_end_to_end_bronze_to_silver(sample_csv_file):
    """Test complete Bronze → Silver pipeline"""

    orchestrator = PipelineOrchestrator()

    result = await orchestrator.run_bronze_to_silver(
        source_file=str(sample_csv_file),
        table_name="customers",
        enable_pii_detection=True,
        enable_quality_checks=True
    )

    # Verify metrics
    assert result['metrics']['status'] == 'SUCCESS'
    assert result['metrics']['bronze_rows'] == 100
    assert result['metrics']['silver_rows'] > 0
    assert result['metrics']['quality_score'] > 0.8  # At least 80% quality

    # Verify PII was detected
    assert result['metrics']['pii_types_found'] > 0
    assert result['metrics']['pii_instances_total'] > 0

    # Verify quality checks ran
    assert result['metrics']['quality_checks_passed'] >= 0

@pytest.mark.asyncio
async def test_pipeline_handles_missing_data(tmp_path):
    """Test pipeline handles missing/null data"""

    # Create CSV with missing data
    data = pd.DataFrame({
        'customer_id': ['C001', 'C002', 'C003'],
        'customer_name': ['Customer 1', None, 'Customer 3'],
        'email_address': ['c1@example.com', None, 'c3@example.com'],
        'phone_number': ['+4512345678', '+4587654321', None]
    })

    file_path = tmp_path / "customers_with_nulls.csv"
    data.to_csv(file_path, index=False)

    orchestrator = PipelineOrchestrator()

    result = await orchestrator.run_bronze_to_silver(
        source_file=str(file_path),
        table_name="customers"
    )

    # Should complete despite missing data
    assert result['metrics']['status'] == 'SUCCESS'

    # Quality score should reflect completeness issues
    assert result['metrics']['quality_score'] < 1.0

@pytest.mark.asyncio
async def test_pipeline_performance_10k_records(tmp_path):
    """Test pipeline performance with 10K records"""

    # Generate 10K records
    data = pd.DataFrame({
        'customer_id': [f'C{i:06d}' for i in range(10000)],
        'customer_name': [f'Customer {i}' for i in range(10000)],
        'email_address': [f'customer{i}@example.com' for i in range(10000)],
        'phone_number': [f'+451234{i:06d}' for i in range(10000)],
        'created_at': [pd.Timestamp.now()] * 10000
    })

    file_path = tmp_path / "customers_10k.csv"
    data.to_csv(file_path, index=False)

    orchestrator = PipelineOrchestrator()

    result = await orchestrator.run_bronze_to_silver(
        source_file=str(file_path),
        table_name="customers"
    )

    # Verify completion
    assert result['metrics']['status'] == 'SUCCESS'
    assert result['metrics']['bronze_rows'] == 10000

    # Verify performance target (<5 minutes)
    assert result['metrics']['duration_seconds'] < 300
```

---

### Week 4: Retry Logic and Gold Layer

#### Day 16-17: Adamiao Retry Patterns Integration

**Tasks:**
1. Study adamiao retry patterns and error handling
2. Implement retry decorators for pipeline tasks
3. Add circuit breaker pattern for external services
4. Implement dead-letter queue for failed records
5. Write tests for retry logic

**Deliverables:**
- [ ] Retry decorator with exponential backoff
- [ ] Circuit breaker implementation
- [ ] Dead-letter queue for failed records
- [ ] Retry logic tests
- [ ] Error handling documentation

**Acceptance Criteria:**
- Transient failures automatically retry (up to 3 attempts)
- Circuit breaker prevents cascade failures
- Failed records stored in dead-letter queue
- Retry logic tested with simulated failures
- Error handling documented

**Estimated Hours:** 16h (Backend: 16h)

**Implementation:**

```python
# src/atlas/core/retry.py
"""Retry patterns inspired by adamiao"""

import logging
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps
from datetime import datetime, timedelta
import asyncio

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
    RetryError
)

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """
    WHY: Circuit breaker pattern prevents cascade failures
    - Fails fast when service is down
    - Automatically recovers when service returns
    - Reduces load on failing services

    States:
    - CLOSED: Normal operation
    - OPEN: Failing fast
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        name: str = "circuit_breaker"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name

        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""

        # Check circuit state
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                logger.info(f"Circuit {self.name}: HALF_OPEN (attempting recovery)")
            else:
                raise CircuitBreakerError(
                    f"Circuit {self.name} is OPEN (will retry after {self.recovery_timeout}s)"
                )

        try:
            # Execute function
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) \
                     else func(*args, **kwargs)

            # Success - reset circuit if needed
            if self.state == "HALF_OPEN":
                self._record_success()

            return result

        except Exception as e:
            self._record_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return True

        time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return time_since_failure >= self.recovery_timeout

    def _record_failure(self):
        """Record failure and update circuit state"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(
                f"Circuit {self.name}: OPEN after {self.failure_count} failures"
            )

    def _record_success(self):
        """Record success and close circuit"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
        logger.info(f"Circuit {self.name}: CLOSED (recovered)")

class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass

class DeadLetterQueue:
    """
    WHY: Store failed records for later reprocessing
    - Prevents data loss
    - Enables manual review of failures
    - Supports batch reprocessing
    """

    def __init__(self, storage_path: str = "data/dead_letter"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def enqueue(
        self,
        record: Dict[str, Any],
        error_message: str,
        pipeline_name: str,
        run_id: str
    ):
        """Add failed record to dead-letter queue"""

        entry = {
            "record": record,
            "error_message": error_message,
            "pipeline_name": pipeline_name,
            "run_id": run_id,
            "failed_at": datetime.utcnow().isoformat(),
            "retry_count": record.get("_retry_count", 0)
        }

        # Store as JSON file
        filename = f"{run_id}_{datetime.utcnow().timestamp()}.json"
        file_path = self.storage_path / pipeline_name / filename

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w') as f:
            json.dump(entry, f, indent=2)

        logger.warning(
            f"Record added to dead-letter queue",
            extra={
                "run_id": run_id,
                "pipeline": pipeline_name,
                "error": error_message
            }
        )

    async def dequeue_batch(
        self,
        pipeline_name: str,
        batch_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve batch of records for reprocessing"""

        pipeline_path = self.storage_path / pipeline_name

        if not pipeline_path.exists():
            return []

        files = list(pipeline_path.glob("*.json"))[:batch_size]
        records = []

        for file_path in files:
            with open(file_path, 'r') as f:
                entry = json.load(f)
                records.append(entry)

        return records

# Retry decorator with adamiao patterns
def retry_on_transient_errors(
    max_attempts: int = 3,
    initial_wait: int = 1,
    max_wait: int = 60,
    transient_exceptions: Tuple[Type[Exception], ...] = (
        ConnectionError,
        TimeoutError,
        TemporaryDatabaseError
    )
):
    """
    WHY: Retry decorator for transient failures
    - Exponential backoff with jitter
    - Only retries transient errors
    - Logs retry attempts
    - Gives up after max attempts

    Args:
        max_attempts: Maximum retry attempts
        initial_wait: Initial wait time (seconds)
        max_wait: Maximum wait time (seconds)
        transient_exceptions: Tuple of exceptions to retry
    """

    def decorator(func):
        @retry(
            retry=retry_if_exception_type(transient_exceptions),
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=1,
                min=initial_wait,
                max=max_wait
            ),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.INFO),
            reraise=True
        )
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper

    return decorator
```

**Usage Example:**

```python
# Example: Using retry patterns in pipeline

from atlas.core.retry import (
    retry_on_transient_errors,
    CircuitBreaker,
    DeadLetterQueue,
    CircuitBreakerError
)

# Initialize circuit breaker for external service
presidio_circuit = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    name="presidio_api"
)

# Initialize dead-letter queue
dlq = DeadLetterQueue(storage_path="data/dead_letter")

class ResilientPIIDetector:
    """PII Detector with retry logic and circuit breaker"""

    @retry_on_transient_errors(max_attempts=3)
    async def detect_pii_with_retry(
        self,
        text: str,
        run_id: str
    ):
        """
        WHY: Detect PII with automatic retry on transient failures
        - Retries on connection errors
        - Fails fast if circuit is open
        - Stores failed records in DLQ
        """

        try:
            # Use circuit breaker for external API call
            result = await presidio_circuit.call(
                self._call_presidio_api,
                text=text
            )

            return result

        except CircuitBreakerError as e:
            # Circuit is open - add to dead-letter queue
            await dlq.enqueue(
                record={"text": text},
                error_message=str(e),
                pipeline_name="pii_detection",
                run_id=run_id
            )
            raise

        except Exception as e:
            logger.error(f"PII detection failed after retries: {e}")
            raise

    async def _call_presidio_api(self, text: str):
        """Call Presidio API (placeholder)"""
        # Actual Presidio call here
        pass
```

---

#### Day 18-19: Gold Layer Implementation

**Tasks:**
1. Implement Gold layer aggregation logic
2. Create business metrics and KPIs
3. Add feature engineering for AI
4. Integrate with Silver layer pipeline
5. Write Gold layer tests

**Deliverables:**
- [ ] Gold layer module with aggregations
- [ ] Business metrics calculation
- [ ] Feature engineering functions
- [ ] Gold layer tests
- [ ] Documentation of metrics and features

**Acceptance Criteria:**
- Gold layer produces aggregated datasets
- Business metrics calculated correctly
- AI features created with proper data types
- Gold layer integrates with pipeline orchestrator
- Tests verify aggregation logic

**Estimated Hours:** 16h (Backend: 16h)

**Gold Layer Implementation:**

```python
# src/atlas/pipeline/gold_layer.py
"""Gold layer: Business-ready aggregated data"""

import logging
from typing import Dict, Optional, List
import pandas as pd
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class GoldLayerAggregation:
    """
    WHY: Gold layer provides business-ready, aggregated data
    - Aggregations for analytics
    - Business metrics and KPIs
    - AI-ready features
    - Optimized for consumption
    """

    def __init__(self, run_id: str):
        self.run_id = run_id

    async def create_customer_360(
        self,
        customers_silver: pd.DataFrame,
        orders_silver: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Create customer 360 view (Gold layer)

        WHY: Unified customer view for analytics and AI
        - Combines customer + order data
        - Calculates business metrics
        - Creates AI features
        - Single source of truth for customer analysis

        Args:
            customers_silver: Silver layer customer data
            orders_silver: Silver layer order data

        Returns:
            Gold layer customer 360 DataFrame
        """

        logger.info(
            f"Creating customer 360 view",
            extra={"run_id": self.run_id}
        )

        # Start with customer base
        gold_df = customers_silver.copy()

        # Calculate order metrics per customer
        order_metrics = self._calculate_order_metrics(orders_silver)

        # Join order metrics to customers
        gold_df = gold_df.merge(
            order_metrics,
            on='customer_id',
            how='left'
        )

        # Calculate RFM scores (Recency, Frequency, Monetary)
        gold_df = self._calculate_rfm_scores(gold_df)

        # Calculate customer lifetime value
        gold_df = self._calculate_customer_lifetime_value(gold_df)

        # Create AI features
        gold_df = self._create_ai_features(gold_df)

        # Add Gold layer metadata
        gold_df['_gold_created_at'] = datetime.utcnow()
        gold_df['_gold_run_id'] = self.run_id

        logger.info(
            f"Customer 360 view created",
            extra={
                "run_id": self.run_id,
                "customers": len(gold_df),
                "features": len(gold_df.columns)
            }
        )

        return gold_df

    def _calculate_order_metrics(
        self,
        orders_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate order metrics per customer

        WHY: Aggregate order data for customer-level analysis
        - Total orders
        - Total revenue
        - Average order value
        - First/last order dates
        """

        metrics = orders_df.groupby('customer_id').agg({
            'order_id': 'count',  # Total orders
            'order_amount': ['sum', 'mean', 'max'],  # Revenue metrics
            'order_date': ['min', 'max']  # First/last order
        })

        # Flatten column names
        metrics.columns = [
            'total_orders',
            'total_revenue',
            'avg_order_value',
            'max_order_value',
            'first_order_date',
            'last_order_date'
        ]

        # Calculate days since last order
        metrics['days_since_last_order'] = (
            datetime.utcnow() - metrics['last_order_date']
        ).dt.days

        # Calculate customer tenure (days)
        metrics['customer_tenure_days'] = (
            datetime.utcnow() - metrics['first_order_date']
        ).dt.days

        return metrics.reset_index()

    def _calculate_rfm_scores(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate RFM scores (Recency, Frequency, Monetary)

        WHY: RFM is fundamental for customer segmentation
        - Recency: How recently did customer purchase?
        - Frequency: How often do they purchase?
        - Monetary: How much do they spend?

        Scores 1-5 for each dimension (5 = best)
        """

        # Recency score (inverse - lower days = higher score)
        df['rfm_recency'] = pd.qcut(
            df['days_since_last_order'],
            q=5,
            labels=[5, 4, 3, 2, 1],
            duplicates='drop'
        ).astype(int)

        # Frequency score
        df['rfm_frequency'] = pd.qcut(
            df['total_orders'],
            q=5,
            labels=[1, 2, 3, 4, 5],
            duplicates='drop'
        ).astype(int)

        # Monetary score
        df['rfm_monetary'] = pd.qcut(
            df['total_revenue'],
            q=5,
            labels=[1, 2, 3, 4, 5],
            duplicates='drop'
        ).astype(int)

        # Combined RFM score (weighted average)
        df['rfm_score'] = (
            df['rfm_recency'] * 0.4 +
            df['rfm_frequency'] * 0.3 +
            df['rfm_monetary'] * 0.3
        )

        # RFM segment
        df['rfm_segment'] = df['rfm_score'].apply(self._assign_rfm_segment)

        return df

    @staticmethod
    def _assign_rfm_segment(score: float) -> str:
        """Assign customer segment based on RFM score"""

        if score >= 4.5:
            return 'champions'
        elif score >= 4.0:
            return 'loyal_customers'
        elif score >= 3.5:
            return 'potential_loyalists'
        elif score >= 3.0:
            return 'at_risk'
        elif score >= 2.5:
            return 'hibernating'
        else:
            return 'lost'

    def _calculate_customer_lifetime_value(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate Customer Lifetime Value (CLV)

        WHY: CLV predicts future revenue from customer
        - Critical for marketing ROI
        - Informs customer acquisition cost
        - Enables value-based segmentation

        Formula: CLV = (Avg Order Value) × (Purchase Frequency) × (Customer Lifespan)
        """

        # Average order value (already calculated)
        avg_order_value = df['avg_order_value']

        # Purchase frequency (orders per year)
        purchase_frequency = (
            df['total_orders'] / (df['customer_tenure_days'] / 365)
        ).fillna(0)

        # Predicted customer lifespan (years)
        # WHY: Use historical data or industry average (3 years)
        predicted_lifespan = 3

        # Calculate CLV
        df['customer_lifetime_value'] = (
            avg_order_value * purchase_frequency * predicted_lifespan
        )

        return df

    def _create_ai_features(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Create features for AI/ML models

        WHY: Feature engineering for churn prediction, recommendations, etc.
        - Behavioral features
        - Temporal features
        - Engagement features
        """

        # Behavioral features
        df['orders_per_month'] = df['total_orders'] / (df['customer_tenure_days'] / 30)
        df['revenue_per_month'] = df['total_revenue'] / (df['customer_tenure_days'] / 30)

        # Engagement features
        df['is_active'] = (df['days_since_last_order'] <= 90).astype(int)
        df['is_at_risk'] = (
            (df['days_since_last_order'] > 90) &
            (df['days_since_last_order'] <= 180)
        ).astype(int)

        # Temporal features
        df['recency_ratio'] = (
            df['days_since_last_order'] / df['customer_tenure_days']
        ).fillna(0)

        # Order consistency (coefficient of variation)
        # Lower = more consistent ordering pattern
        df['order_consistency'] = np.where(
            df['total_orders'] > 1,
            df['avg_order_value'] / df['max_order_value'],
            0
        )

        return df
```

---

#### Day 20: Phase 2 Integration and Testing

**Tasks:**
1. Full pipeline integration (Bronze → Silver → Gold)
2. End-to-end testing with realistic data
3. Performance optimization
4. Documentation updates
5. Phase 2 demo preparation

**Deliverables:**
- [ ] Complete pipeline (Bronze → Silver → Gold) operational
- [ ] End-to-end integration tests passing
- [ ] Performance benchmarks documented
- [ ] Phase 2 documentation complete
- [ ] Demo environment prepared

**Acceptance Criteria:**
- Full pipeline processes 10K customers + 50K orders in <10 minutes
- All quality and PII checks functional
- RFM scores and CLV calculated correctly
- Integration tests pass with >85% coverage
- Documentation updated with Phase 2 features

**Estimated Hours:** 8h (Team: 8h)

---

### Phase 2 Deliverables Summary

**Week 3 Deliverables:**
- ✅ Presidio PII detection integrated
- ✅ Custom Danish CPR recognizer
- ✅ Soda Core quality framework integrated
- ✅ 6 dimensions of quality validated
- ✅ PII + quality integrated in Silver layer

**Week 4 Deliverables:**
- ✅ Retry logic with exponential backoff
- ✅ Circuit breaker pattern implemented
- ✅ Dead-letter queue for failed records
- ✅ Gold layer with customer 360 view
- ✅ RFM scores and CLV calculation
- ✅ AI feature engineering

**Success Criteria:**
- [ ] PII detection rate >90% (verified with test data)
- [ ] Quality validation covers all 6 dimensions
- [ ] Retry logic handles transient failures
- [ ] Gold layer produces business-ready datasets
- [ ] Full pipeline (Bronze → Silver → Gold) operational
- [ ] Performance targets met (<10 min for 10K customers)

**Risks Identified:**
- Presidio model download time (first run)
- Soda Core learning curve
- Performance bottlenecks in aggregations
- Test data realism for PII/quality testing

---

## Phase 3: API & Services (Weeks 5-6)

**Objective:** Build FastAPI endpoints, Celery workers, and lineage tracking

### Week 5: FastAPI REST API

#### Day 21-23: Core API Endpoints

**Tasks:**
1. Implement FastAPI application structure
2. Create pipeline execution endpoints
3. Add pipeline status and monitoring endpoints
4. Implement authentication (JWT)
5. Write API tests

**Deliverables:**
- [ ] FastAPI application with OpenAPI docs
- [ ] `/pipelines/execute` endpoint
- [ ] `/pipelines/{run_id}` status endpoint
- [ ] `/pipelines` listing endpoint
- [ ] JWT authentication middleware
- [ ] API integration tests

**Acceptance Criteria:**
- API starts on port 8000 with auto-reload
- OpenAPI docs accessible at `/docs`
- Authentication protects all endpoints
- API tests achieve >80% coverage
- Response times <200ms for status queries

**Estimated Hours:** 24h (Backend: 24h)

**FastAPI Implementation:**

```python
# src/atlas/api/main.py
"""FastAPI application for Atlas Data Pipeline"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging

from atlas.config.settings import settings
from atlas.api.routes import pipelines, quality, compliance
from atlas.api.dependencies import get_current_user
from atlas.core.logging import setup_logging

# Setup logging
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_format=settings.LOG_FORMAT
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Atlas Data Pipeline API",
    description=(
        "Production-grade data pipeline platform with PII detection, "
        "quality validation, and lineage tracking"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    pipelines.router,
    prefix="/api/v1/pipelines",
    tags=["pipelines"]
)
app.include_router(
    quality.router,
    prefix="/api/v1/quality",
    tags=["quality"]
)
app.include_router(
    compliance.router,
    prefix="/api/v1/compliance",
    tags=["compliance"]
)

@app.get("/health")
async def health_check():
    """
    Health check endpoint

    WHY: Required for load balancers and monitoring
    - Returns 200 if service is healthy
    - Includes version and status
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Atlas Data Pipeline API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with consistent format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500
        }
    )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "atlas.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True if settings.ENVIRONMENT == "development" else False,
        workers=settings.API_WORKERS if settings.ENVIRONMENT != "development" else 1
    )
```

**Pipeline Routes:**

```python
# src/atlas/api/routes/pipelines.py
"""Pipeline execution and monitoring endpoints"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
from datetime import datetime

from atlas.api.dependencies import get_db, get_current_user
from atlas.schemas.pipeline import (
    PipelineRequest,
    PipelineResponse,
    PipelineStatusResponse
)
from atlas.pipeline.orchestrator import PipelineOrchestrator
from atlas.models.pipeline import PipelineRun, PipelineRunStatus

router = APIRouter()

@router.post("/execute", response_model=PipelineResponse)
async def execute_pipeline(
    request: PipelineRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Execute a data pipeline

    WHY: Main API endpoint for triggering pipelines
    - Queues pipeline for async execution
    - Returns immediately with run_id
    - User polls for status updates

    Args:
        request: Pipeline execution request
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Authenticated user

    Returns:
        Pipeline response with run_id
    """

    # Generate run ID
    run_id = str(uuid.uuid4())

    # Create database record
    pipeline_run = PipelineRun(
        run_id=run_id,
        pipeline_name=request.pipeline_name,
        status=PipelineRunStatus.PENDING,
        created_by=current_user.user_id,
        input_params=request.parameters
    )

    db.add(pipeline_run)
    await db.commit()

    # Queue pipeline execution as background task
    # WHY: FastAPI background task for simple async execution
    # (For production, use Celery instead)
    background_tasks.add_task(
        execute_pipeline_background,
        run_id=run_id,
        pipeline_name=request.pipeline_name,
        parameters=request.parameters
    )

    return PipelineResponse(
        run_id=run_id,
        pipeline_name=request.pipeline_name,
        status=PipelineRunStatus.PENDING,
        created_at=pipeline_run.created_at,
        message="Pipeline queued successfully"
    )

async def execute_pipeline_background(
    run_id: str,
    pipeline_name: str,
    parameters: dict
):
    """
    Execute pipeline in background

    WHY: Actual pipeline execution logic
    - Runs asynchronously
    - Updates database with progress
    - Handles errors
    """

    orchestrator = PipelineOrchestrator(run_id=run_id)

    try:
        if pipeline_name == "bronze_to_silver":
            await orchestrator.run_bronze_to_silver(
                source_file=parameters['source_file'],
                table_name=parameters['table_name']
            )
        elif pipeline_name == "bronze_to_gold":
            # Full pipeline
            pass
        else:
            raise ValueError(f"Unknown pipeline: {pipeline_name}")

    except Exception as e:
        logger.error(f"Pipeline {run_id} failed: {e}")
        # Update database with error
        # (Error handling would update DB here)

@router.get("/{run_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get pipeline execution status

    WHY: Poll endpoint for pipeline status
    - Returns current status
    - Includes metrics when complete
    - Enables UI progress tracking

    Args:
        run_id: Pipeline run ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Pipeline status and results
    """

    # Query database
    result = await db.execute(
        select(PipelineRun).where(PipelineRun.run_id == run_id)
    )
    pipeline_run = result.scalar_one_or_none()

    if not pipeline_run:
        raise HTTPException(
            status_code=404,
            detail=f"Pipeline run {run_id} not found"
        )

    return PipelineStatusResponse(
        run_id=pipeline_run.run_id,
        pipeline_name=pipeline_run.pipeline_name,
        status=pipeline_run.status,
        created_at=pipeline_run.created_at,
        started_at=pipeline_run.started_at,
        completed_at=pipeline_run.completed_at,
        duration_seconds=pipeline_run.duration_seconds,
        result_data=pipeline_run.result_data,
        error_message=pipeline_run.error_message
    )

@router.get("/", response_model=List[PipelineStatusResponse])
async def list_pipeline_runs(
    pipeline_name: Optional[str] = None,
    status: Optional[PipelineRunStatus] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List pipeline runs with filtering

    WHY: Enable monitoring dashboard
    - Filter by pipeline name or status
    - Paginated results
    - Recent runs first

    Args:
        pipeline_name: Filter by pipeline (optional)
        status: Filter by status (optional)
        limit: Max results
        offset: Pagination offset
        db: Database session
        current_user: Authenticated user

    Returns:
        List of pipeline runs
    """

    query = select(PipelineRun)

    if pipeline_name:
        query = query.where(PipelineRun.pipeline_name == pipeline_name)

    if status:
        query = query.where(PipelineRun.status == status)

    query = query.order_by(PipelineRun.created_at.desc())
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    runs = result.scalars().all()

    return [
        PipelineStatusResponse(
            run_id=run.run_id,
            pipeline_name=run.pipeline_name,
            status=run.status,
            created_at=run.created_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            duration_seconds=run.duration_seconds,
            result_data=run.result_data,
            error_message=run.error_message
        )
        for run in runs
    ]

@router.delete("/{run_id}/cancel")
async def cancel_pipeline(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Cancel a running pipeline

    WHY: Allow users to stop long-running jobs
    - Updates status to CANCELLED
    - Stops background task (if possible)
    """

    result = await db.execute(
        select(PipelineRun).where(PipelineRun.run_id == run_id)
    )
    pipeline_run = result.scalar_one_or_none()

    if not pipeline_run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")

    if pipeline_run.status not in [PipelineRunStatus.PENDING, PipelineRunStatus.RUNNING]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel pipeline with status {pipeline_run.status}"
        )

    pipeline_run.status = PipelineRunStatus.CANCELLED
    pipeline_run.completed_at = datetime.utcnow()

    await db.commit()

    return {"message": f"Pipeline {run_id} cancelled successfully"}
```

*(Continuing in next artifact due to length...)*

---

*This implementation plan continues with detailed sections for:*

- **Phase 3 (Weeks 5-6)**: Complete API implementation, Celery integration, OpenLineage tracking
- **Phase 4 (Weeks 7-8)**: Dashboard UI, bot integration, comprehensive testing
- **Testing Strategy**: Unit, integration, load, and security testing
- **Deployment Guide**: Docker Compose, Kubernetes, CI/CD pipelines
- **Risks & Mitigation**: Detailed risk analysis with mitigation strategies
- **Appendices**: File structure, configuration templates, troubleshooting guide

Would you like me to continue with the remaining sections of the implementation plan?
