# Atlas Data Pipeline Platform

**Version:** 0.1.0  
**Status:** Development  
**Python:** 3.11+

Production-grade data infrastructure system that transforms raw data from multiple sources into AI-ready, compliant datasets using the medallion architecture (Bronze/Silver/Gold) with integrated PII detection, data quality validation, and comprehensive lineage tracking.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Development](#development)
- [Documentation](#documentation)

## Features

### Core Capabilities
- **Medallion Architecture**: Bronze → Silver → Gold → AI-Ready data layers
- **PII Detection**: Automated detection and anonymization using Microsoft Presidio
- **Data Quality**: 6-dimension quality framework with Soda Core
- **Data Lineage**: OpenLineage integration with Marquez for full traceability
- **REST API**: FastAPI-based API for pipeline orchestration and monitoring
- **Async Processing**: Celery workers for distributed task execution
- **Workflow Orchestration**: Prefect for complex pipeline workflows

### Quality Standards
- GDPR compliance with automated PII handling
- 95%+ data quality score across all dimensions
- <5 minute processing for 10K record batches
- 99% pipeline success rate with retry logic
- Real-time monitoring and lineage visualization

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ FastAPI  │  │  Minimal │  │ Opsdroid │                  │
│  │   API    │  │Dashboard │  │   Bot    │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION LAYER                        │
│  ┌────────┐  ┌──────────┐  ┌────────────┐                 │
│  │ Celery │  │ Prefect  │  │OpenLineage │                 │
│  └────────┘  └──────────┘  └────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│                    PROCESSING LAYER                          │
│  ┌──────────────────────────────────────────────┐           │
│  │  PIPELINE (adamiao patterns)                 │           │
│  │  Bronze → Silver → Gold → AI Ready           │           │
│  └──────────────────────────────────────────────┘           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ Presidio │  │SodaCore  │  │ Business │                 │
│  │  (PII)   │  │(Quality) │  │  Rules   │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│                      STORAGE LAYER                           │
│  ┌────────────┐  ┌────────┐  ┌────────┐                    │
│  │ PostgreSQL │  │ Redis  │  │ MinIO  │                    │
│  └────────────┘  └────────┘  └────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose 24+
- Python 3.11+
- Git

### Installation

1. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start services**
   ```bash
   docker-compose up -d
   ```

3. **Verify installation**
   ```bash
   # Check all services are running
   docker-compose ps

   # API health check
   curl http://localhost:8000/api/v1/health
   ```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| API | http://localhost:8000 | FastAPI backend |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| Adminer | http://localhost:8081 | Database UI |
| Prefect UI | http://localhost:4200 | Workflow orchestration |
| Marquez UI | http://localhost:5000 | Data lineage visualization |
| Flower | http://localhost:5555 | Celery task monitoring |
| MinIO Console | http://localhost:9001 | Object storage UI |

### Default Credentials

- **Database**: `atlas_user` / `changethis`
- **MinIO**: `minioadmin` / `changethis`
- **API**: `admin@atlas.local` / `changethis`

> **Security Note**: Change all default passwords in production!

## Project Structure

```
atlas-api/
├── app/                          # Application code
│   ├── api/                      # API routes
│   ├── core/                     # Core configuration
│   ├── models.py                 # Database models
│   ├── pipeline/                 # Data pipeline components
│   │   ├── bronze/              # Raw data ingestion
│   │   ├── silver/              # Cleaned data
│   │   ├── gold/                # Curated data
│   │   ├── ai_ready/            # AI-ready datasets
│   │   ├── core/                # Pipeline core logic
│   │   ├── quality/             # Data quality checks
│   │   ├── pii/                 # PII detection/masking
│   │   └── lineage/             # Lineage tracking
│   ├── integrations/             # Third-party integrations
│   │   ├── presidio/            # PII detection
│   │   ├── soda/                # Data quality
│   │   ├── openlineage/         # Lineage tracking
│   │   └── prefect/             # Workflow orchestration
│   ├── tasks/                    # Celery tasks
│   ├── workers/                  # Worker configuration
│   └── config/                   # Configuration files
├── tests/                        # Test suite
├── scripts/                      # Utility scripts
├── examples/                     # Integration examples
├── docs/                         # Documentation
├── .env.example                  # Environment template
├── docker-compose.yml            # Docker services
├── Dockerfile                    # Container image
├── pyproject.toml               # Python dependencies
└── README.md                     # This file
```

## Development

### Local Development Setup

1. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

4. **Start development server**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test category
pytest -m unit
pytest -m integration
pytest -m pipeline
```

### Code Quality

```bash
# Format code
black app/ tests/
isort app/ tests/

# Lint code
ruff app/ tests/

# Type checking
mypy app/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Documentation

### Key Documents

See `/docs` directory for detailed documentation.

### Integration Examples

Check `/examples` directory for:
- PII detection with Presidio
- Data quality checks with Soda Core
- Lineage tracking with OpenLineage
- Pipeline execution with Celery
- Workflow orchestration with Prefect

## Technology Stack

| Category | Technology | Version |
|----------|-----------|---------|
| Language | Python | 3.11+ |
| Web Framework | FastAPI | 0.109+ |
| Database | PostgreSQL | 15+ |
| Cache/Queue | Redis | 7+ |
| Object Storage | MinIO | Latest |
| Task Queue | Celery | 5.3+ |
| Orchestration | Prefect | 2.14+ |
| PII Detection | Presidio | 2.2+ |
| Data Quality | Soda Core | 3.0+ |
| Lineage | OpenLineage | 1.0+ |

---

**Atlas Data Pipeline Platform** - Transforming data into AI-ready insights
