# Atlas Data Pipeline Platform - Setup Guide

**Version:** 1.0
**Last Updated:** January 2026

This guide covers the complete setup process for the Atlas Data Pipeline Platform, from initial environment configuration to running your first pipeline.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Configuration](#configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

| Software | Version | Purpose | Installation |
|----------|---------|---------|-------------|
| Docker | 24.0+ | Container runtime | [Install Docker](https://docs.docker.com/get-docker/) |
| Docker Compose | 2.20+ | Multi-container orchestration | Included with Docker Desktop |
| Python | 3.11+ | Development language | [Install Python](https://www.python.org/downloads/) |
| Git | 2.40+ | Version control | [Install Git](https://git-scm.com/downloads/) |
| uv | Latest | Fast Python package installer | `pip install uv` |

### System Requirements

- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 20GB free space
- **OS**: macOS, Linux, or Windows with WSL2

### Knowledge Requirements

- Basic Python programming
- Understanding of REST APIs
- Familiarity with Docker and containers
- Basic SQL knowledge
- Understanding of data pipelines (helpful)

## Quick Start

For experienced developers who want to get started immediately:

```bash
# 1. Clone repository (if not already cloned)
git clone <repository-url> atlas-pipeline
cd atlas-pipeline

# 2. Setup environment
cp .env.example .env
# Edit .env with your passwords

# 3. Start services
docker-compose up -d

# 4. Wait for services to be healthy
docker-compose ps

# 5. Run database migrations
docker-compose exec api alembic upgrade head

# 6. Create initial superuser
docker-compose exec api python -m app.initial_data

# 7. Access application
open http://localhost:8000/docs
```

## Detailed Setup

### Step 1: Environment Configuration

1. **Copy environment template**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env file** - Update these critical values:
   ```bash
   # Security - CHANGE THESE!
   SECRET_KEY=generate_a_secure_random_string_here
   FIRST_SUPERUSER_PASSWORD=your_secure_password
   POSTGRES_PASSWORD=your_postgres_password
   REDIS_PASSWORD=your_redis_password
   S3_SECRET_KEY=your_minio_password

   # Database
   POSTGRES_DB=atlas_pipeline
   POSTGRES_USER=atlas_user

   # API Configuration
   PROJECT_NAME="Atlas Data Pipeline Platform"
   DOMAIN=localhost
   ENVIRONMENT=local
   ```

3. **Generate secure keys** (recommended):
   ```bash
   # Generate SECRET_KEY
   python -c "import secrets; print(secrets.token_urlsafe(32))"

   # Generate ENCRYPTION_KEY (32 bytes)
   python -c "import secrets; print(secrets.token_urlsafe(32))"

   # Generate FERNET_KEY
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

### Step 2: Start Infrastructure Services

1. **Start all services**
   ```bash
   docker-compose up -d
   ```

2. **Verify services are running**
   ```bash
   docker-compose ps
   ```

   All services should show status "Up" and healthy:
   - `atlas-db` - PostgreSQL database
   - `atlas-redis` - Redis cache and message broker
   - `atlas-minio` - Object storage
   - `atlas-marquez-db` - Lineage database
   - `atlas-marquez` - Lineage API
   - `atlas-prefect` - Workflow orchestration
   - `atlas-api` - FastAPI backend
   - `atlas-worker` - Celery workers
   - `atlas-flower` - Celery monitoring

3. **Check service logs** (if needed):
   ```bash
   # All services
   docker-compose logs -f

   # Specific service
   docker-compose logs -f api
   ```

### Step 3: Database Setup

1. **Run database migrations**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

2. **Create initial superuser and sample data**
   ```bash
   docker-compose exec api python -m app.initial_data
   ```

3. **Verify database connection**
   ```bash
   # Connect to database
   docker-compose exec db psql -U atlas_user -d atlas_pipeline

   # List tables
   \dt

   # Exit
   \q
   ```

### Step 4: Object Storage Setup

1. **Access MinIO Console**
   - URL: http://localhost:9001
   - Username: `minioadmin` (or value from .env)
   - Password: From `S3_SECRET_KEY` in .env

2. **Verify buckets are created**
   - `atlas-bronze` - Raw data layer
   - `atlas-silver` - Cleaned data layer
   - `atlas-gold` - Curated data layer
   - `atlas-ai-ready` - AI-ready datasets

3. **Create buckets manually** (if not auto-created):
   ```bash
   docker-compose exec api python scripts/init_storage.py
   ```

### Step 5: Presidio Setup (PII Detection)

1. **Download spaCy language model**
   ```bash
   docker-compose exec api python -m spacy download en_core_web_lg
   docker-compose exec api python -m spacy download da_core_news_lg  # Danish
   ```

2. **Verify Presidio is working**
   ```bash
   docker-compose exec api python scripts/test_presidio.py
   ```

### Step 6: Verification

1. **API Health Check**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

   Expected response:
   ```json
   {
     "status": "healthy",
     "version": "0.1.0",
     "services": {
       "database": "connected",
       "redis": "connected",
       "storage": "connected"
     }
   }
   ```

2. **API Documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

3. **Web Interfaces**
   - API: http://localhost:8000
   - Prefect UI: http://localhost:4200
   - Marquez UI: http://localhost:5000
   - Flower (Celery): http://localhost:5555
   - MinIO Console: http://localhost:9001
   - Adminer (DB UI): http://localhost:8081

## Configuration

### Environment Variables

Key environment variables organized by category:

#### Core Configuration
```bash
DOMAIN=localhost
ENVIRONMENT=local
PROJECT_NAME="Atlas Data Pipeline Platform"
API_VERSION=v1
```

#### Database Settings
```bash
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=atlas_pipeline
POSTGRES_USER=atlas_user
POSTGRES_PASSWORD=changethis
```

#### Medallion Architecture Layers
```bash
BRONZE_DB=atlas_bronze      # Raw ingestion
SILVER_DB=atlas_silver      # Cleaned data
GOLD_DB=atlas_gold          # Curated data
```

#### PII Detection
```bash
PRESIDIO_ENABLED=true
PRESIDIO_LANGUAGES=en,da
PRESIDIO_SCORE_THRESHOLD=0.35
```

#### Data Quality
```bash
QUALITY_COMPLETENESS_THRESHOLD=0.95
QUALITY_VALIDITY_THRESHOLD=0.90
QUALITY_CONSISTENCY_THRESHOLD=0.85
```

#### Pipeline Settings
```bash
PIPELINE_BATCH_SIZE=1000
PIPELINE_MAX_RETRIES=3
PIPELINE_TIMEOUT=3600
```

### Docker Compose Profiles

The `docker-compose.yml` supports different profiles for various scenarios:

```bash
# Development (all services)
docker-compose --profile dev up -d

# Production (without dev tools)
docker-compose --profile prod up -d

# Minimal (API, DB, Redis only)
docker-compose --profile minimal up -d
```

### Custom Configuration

1. **Custom Presidio Patterns**
   - Edit: `app/config/presidio_patterns.yaml`
   - Add domain-specific PII patterns

2. **Custom Soda Checks**
   - Directory: `app/config/soda_checks/`
   - Add YAML files for custom quality checks

3. **Custom Business Rules**
   - Module: `app/pipeline/rules/`
   - Implement custom transformation logic

## Verification

### Automated Verification Script

```bash
# Run comprehensive verification
docker-compose exec api python scripts/verify_setup.py
```

This checks:
- All services are running
- Database migrations are applied
- Storage buckets exist
- PII detection is functional
- Data quality checks work
- Lineage tracking is operational

### Manual Verification Steps

1. **Test API Authentication**
   ```bash
   # Login
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username":"admin@atlas.local","password":"changethis"}'
   ```

2. **Test Pipeline Execution**
   ```bash
   # Trigger sample pipeline
   curl -X POST "http://localhost:8000/api/v1/pipelines/execute" \
     -H "Authorization: Bearer <your-token>" \
     -H "Content-Type: application/json" \
     -d '{"pipeline_name":"sample_pipeline","input_data":{}}'
   ```

3. **Check Celery Workers**
   ```bash
   docker-compose exec worker celery -A app.workers inspect active
   ```

4. **View Prefect Flows**
   - Open http://localhost:4200
   - Check for registered flows

5. **View Data Lineage**
   - Open http://localhost:5000
   - Verify lineage graph is displayed

## Troubleshooting

### Common Issues

#### Services Won't Start

**Symptom**: `docker-compose up` fails

**Solutions**:
1. Check Docker is running: `docker info`
2. Check port conflicts: `lsof -i :8000`
3. Check disk space: `df -h`
4. Review logs: `docker-compose logs`

#### Database Connection Errors

**Symptom**: "Connection refused" or "Authentication failed"

**Solutions**:
1. Verify PostgreSQL is running:
   ```bash
   docker-compose ps db
   ```

2. Check credentials in .env match:
   ```bash
   docker-compose exec db psql -U atlas_user -d atlas_pipeline
   ```

3. Reset database (if needed):
   ```bash
   docker-compose down -v
   docker-compose up -d db
   ```

#### Migration Failures

**Symptom**: Alembic migration errors

**Solutions**:
1. Check current migration state:
   ```bash
   docker-compose exec api alembic current
   ```

2. View migration history:
   ```bash
   docker-compose exec api alembic history
   ```

3. Downgrade and retry:
   ```bash
   docker-compose exec api alembic downgrade -1
   docker-compose exec api alembic upgrade head
   ```

#### MinIO Connection Issues

**Symptom**: "Connection refused" to S3

**Solutions**:
1. Verify MinIO is running:
   ```bash
   docker-compose ps minio
   ```

2. Test connection:
   ```bash
   curl http://localhost:9000/minio/health/live
   ```

3. Check credentials in .env

#### Presidio Not Detecting PII

**Symptom**: PII not detected in test data

**Solutions**:
1. Verify spaCy models installed:
   ```bash
   docker-compose exec api python -m spacy validate
   ```

2. Check Presidio configuration:
   ```bash
   docker-compose exec api python -c "from presidio_analyzer import AnalyzerEngine; print(AnalyzerEngine().get_supported_entities())"
   ```

3. Lower threshold in .env:
   ```bash
   PRESIDIO_SCORE_THRESHOLD=0.3
   ```

#### Celery Workers Not Processing Tasks

**Symptom**: Tasks stay in pending state

**Solutions**:
1. Check worker status:
   ```bash
   docker-compose logs worker
   ```

2. Restart workers:
   ```bash
   docker-compose restart worker
   ```

3. Check Redis connection:
   ```bash
   docker-compose exec redis redis-cli PING
   ```

#### Port Already in Use

**Symptom**: "Port is already allocated"

**Solutions**:
1. Find process using port:
   ```bash
   lsof -i :8000
   ```

2. Kill process or change port in docker-compose.yml:
   ```yaml
   ports:
     - "8001:8000"  # Use 8001 instead
   ```

### Getting Help

1. **Check logs**
   ```bash
   docker-compose logs -f [service-name]
   ```

2. **Review documentation**
   - See `docs/ARCHITECTURE.md` for system design
   - See `docs/API.md` for API reference
   - See integration examples in `examples/`

3. **Debug mode**
   - Set in .env: `DEBUG=true`
   - Set in .env: `LOG_LEVEL=DEBUG`
   - Restart services

4. **Contact support**
   - Create issue in repository
   - Include logs and configuration
   - Describe steps to reproduce

## Next Steps

After successful setup:

1. **Read Documentation**
   - [Architecture Guide](ARCHITECTURE.md)
   - [API Reference](API.md)
   - [Workflow Guide](WORKFLOW.md)

2. **Run Example Pipelines**
   ```bash
   cd examples
   python 01_adamiao_presidio_pii_detection.py
   ```

3. **Development Setup**
   - See "Development" section in README.md
   - Setup local Python environment
   - Install development tools

4. **Create Your First Pipeline**
   - Follow tutorial in `docs/tutorials/01_first_pipeline.md`
   - Implement custom business logic
   - Test with sample data

---

**Atlas Data Pipeline Platform** - Production-ready data infrastructure for AI initiatives
