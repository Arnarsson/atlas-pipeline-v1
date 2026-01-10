# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Atlas Data Pipeline Platform**: Production-grade data infrastructure for transforming raw data into AI-ready, GDPR-compliant datasets using medallion architecture.

**Key Concept**: Explore → Chart → Navigate (renamed from Bronze → Silver → Gold)
- **Explore**: Raw data ingestion with source fidelity
- **Chart**: PII detection, quality validation, data standardization
- **Navigate**: Business aggregations and AI-ready feature engineering

**Implementation Status**:
- Week 1: ✅ Infrastructure (50 tables, 42/42 tests ✅)
- Week 2: ✅ **WORKING API** (CSV→Explore→Chart, PII detection, quality validation)
- Week 3-8: Planlagt (Presidio integration, Soda Core, dashboard)

**STATUS: BRUGBAR NU** ✅
```bash
cd /Users/sven/Desktop/MCP/.worktrees/atlas-api
python3 simple_main.py
# → http://localhost:8000/docs (Interactive API)
# Upload CSV → få quality + PII report på sekunder
```

---

## Architecture & Structure

### Multi-Location Codebase

This repository contains **three distinct workspaces**:

1. **Production Backend** (`/Users/sven/Desktop/MCP/.worktrees/atlas-api/`)
   - FastAPI application with 51-table database schema
   - Week 1+ production implementation
   - CI/CD, testing, monitoring configured

2. **Proof of Concept** (`atlas-poc/`)
   - Working Explore→Chart pipeline demo
   - Validates architecture before production build
   - Use for reference, not production code

3. **Documentation & Planning** (`docs/`)
   - `IMPLEMENTATION_PLAN.md` - 8-week roadmap
   - `integration-examples/` - Copy-paste integration patterns
   - Design decisions and use cases

**Always work in the production backend** (`atlas-api` worktree) unless explicitly testing POC concepts.

### Database Schema Architecture

**7 PostgreSQL Schemas** (not separate databases):
```
atlas_pipeline (main database)
├── explore.*        # Raw data layer (was "bronze")
├── chart.*          # Validated data layer (was "silver")
├── navigate.*       # Business-ready layer (was "gold")
├── pipeline.*       # Pipeline execution metadata
├── quality.*        # Data quality metrics
├── compliance.*     # PII detection, GDPR audit trails
└── archive.*        # Historical data retention
```

**Critical**: Always use Explore/Chart/Navigate terminology, never Bronze/Silver/Gold.

### Integration Pattern

Atlas integrates **8 external open-source projects**:
- **Presidio** (Microsoft): PII detection - see `docs/integration-examples/01_adamiao_presidio_pii_detection.py`
- **Soda Core**: Data quality validation - see `04_soda_core_quality_checks.py`
- **OpenLineage + Marquez**: Data lineage - see `02_prefect_openlineage_tracking.py`
- **Prefect**: Workflow orchestration
- **Celery**: Background task processing - see `03_fastapi_celery_pipeline_execution.py`
- **Tiangolo FastAPI Template**: Backend structure foundation
- **adamiao/data-pipeline**: Medallion architecture patterns
- **Opsdroid**: Multi-channel bot interface - see `05_opsdroid_bot_integration.py`

**Integration examples** in `docs/integration-examples/` show exact connection code - reference these when implementing features.

---

## Common Commands

### Quick Start (Brug Atlas NU)

```bash
# Start API serveren (Week 2 simple version)
cd /Users/sven/Desktop/MCP/.worktrees/atlas-api
python3 simple_main.py

# API kører nu på http://localhost:8000
# Docs: http://localhost:8000/docs

# Upload CSV (via Swagger UI eller curl):
curl -X POST http://localhost:8000/pipeline/run \
  -F "file=@your_file.csv" \
  -F "dataset_name=test"

# Få quality metrics:
curl http://localhost:8000/quality/metrics/{run_id}

# Få PII report:
curl http://localhost:8000/quality/pii-report/{run_id}

# Stop serveren:
# Ctrl+C i terminal hvor den kører
```

**Hvad den kan**:
- Upload CSV (enhver størrelse, auto-delimiter detection)
- Quality validation (completeness, validity, consistency scores)
- PII detection (email, phone, SSN, credit cards, zipcodes)
- Compliance reporting (GDPR-relevant findings)
- Results på sekunder (100 rækker = ~300ms)

### Working in Production Backend

```bash
# Navigate to production workspace
cd /Users/sven/Desktop/MCP/.worktrees/atlas-api

# Start infrastructure (PostgreSQL + Redis)
docker-compose up -d db redis

# Verify infrastructure health (should show 27/27 ✅)
./scripts/verify-setup.sh

# Run integration tests (should show 15/15 ✅)
python3 tests/integration/test_week1_deployment.py

# Access database
docker exec -it atlas-db psql -U atlas_user -d atlas_pipeline

# Inside psql:
\dn+                    # List all 7 schemas
\dt explore.*           # Tables in Explore layer
\dt chart.*             # Tables in Chart layer
\dt navigate.*          # Tables in Navigate layer
\d+ tablename           # Describe specific table
```

### Database Management

```bash
# Run migrations
docker-compose run --rm backend alembic upgrade head

# Create new migration
docker-compose run --rm backend alembic revision --autogenerate -m "description"

# Rollback one migration
docker-compose run --rm backend alembic downgrade -1

# View migration history
docker-compose run --rm backend alembic history

# Reset database (WARNING: destructive)
docker-compose down -v
docker-compose up -d db
```

### Development (When Backend Builds)

```bash
# Using Makefile automation (40+ commands available)
make help              # Show all available commands

# Common commands:
make dev               # Start development server
make test              # Run all tests
make test-coverage     # Run tests with coverage report
make lint              # Run linting (ruff)
make format            # Format code (black)
make type-check        # Type checking (mypy)
make quality           # Run all quality checks
make db-upgrade        # Run database migrations
make db-reset          # Reset database

# Or manually:
uvicorn app.main:app --reload --port 8000
pytest tests/
ruff check .
black .
mypy app/
```

### Testing POC

```bash
# Test the proof-of-concept demo
cd atlas-poc
docker-compose up -d

# Access demo
open http://localhost:8000/static/demo.html

# Run pipeline test
curl -X POST "http://localhost:8000/pipeline/run" \
  -H "Content-Type: application/json" \
  -d '{"source_file": "customers.csv", "pipeline_type": "explore_to_chart"}'

# Stop POC
docker-compose down
```

---

## Data Pipeline Flow

### Processing Layers

**Explore Layer** (Raw Ingestion):
- Load data from sources (CSV, API, Database) without transformation
- Store in `explore.raw_data` table (partitioned by ingestion_date)
- Emit OpenLineage START event
- Preserve complete audit trail

**Chart Layer** (Validation & Cleaning):
1. Scan for PII using Presidio (`app/integrations/presidio/`)
2. Run Soda Core quality checks (`app/integrations/soda/`)
3. Standardize formats (dates, currencies, phone numbers)
4. Apply business rules and transformations
5. Store in `chart.*` tables
6. Log PII detections to `compliance.pii_detections`
7. Log quality metrics to `quality.check_results`

**Navigate Layer** (Business Ready):
- Aggregate by business dimensions
- Feature engineering for AI/ML models
- Denormalize for query performance
- Export to feature store or AI frameworks

### Key Integration Points

**PII Detection Flow**:
```
Data → Presidio Analyzer (detects EMAIL, PHONE, SSN, etc.)
     → Store in compliance.pii_detections
     → Apply masking strategy
     → Log to compliance.audit_trail
```

**Quality Validation Flow**:
```
Data → Soda Core checks (YAML-defined)
     → Validate 6 dimensions (completeness, uniqueness, validity, etc.)
     → Store results in quality.check_results
     → Fail pipeline if critical checks fail
```

**Lineage Tracking Flow**:
```
Pipeline Start → Emit OpenLineage START event → Marquez API
Pipeline Step  → Emit RUNNING events → Track transformations
Pipeline End   → Emit COMPLETE event → Full lineage graph available
```

---

## Critical Development Notes

### Schema Naming Convention

**ALWAYS use**:
- `explore.*` for raw data (not bronze)
- `chart.*` for validated data (not silver)
- `navigate.*` for business data (not gold)

**Migration files already renamed** - see `database/migrations/001_core_tables_explore_chart_navigate.sql`

### Testing Strategy

**Integration tests validate** (run before any PR):
```bash
python3 tests/integration/test_week1_deployment.py
```

Tests check:
- All 7 schemas exist
- 51 tables deployed correctly
- Partitions configured
- Seed data loaded
- Correct naming (Explore/Chart/Navigate, not Bronze/Silver/Gold)

### Current Infrastructure Status

**Working & Tested** ✅:
- PostgreSQL: 50 tables deployed (27/27 health checks ✅)
- Redis: Authentication configured (15/15 integration tests ✅)
- **FastAPI API**: BRUGBAR (simple_main.py kører på localhost:8000) ✅
- Pipeline: CSV → Explore → Chart med PII/quality ✅

**Endpoints Available**:
- `/pipeline/run` - Upload CSV, trigger processing
- `/pipeline/status/{id}` - Check completion
- `/quality/metrics/{id}` - Quality scores (completeness, validity, consistency)
- `/quality/pii-report/{id}` - PII findings (email, phone, SSN, etc.)
- `/compliance/report/{id}` - Combined GDPR compliance status

**In Progress** (Week 3+ scope):
- Full Presidio integration (nu: regex-based PII detection)
- Soda Core integration (nu: basic SQL quality checks)
- Database persistence (nu: in-memory results)
- Celery workers, Prefect workflows, Dashboard

### Simplified Working API (Week 2 Deliverable)

**File**: `simple_main.py` (standalone FastAPI app)

**Why**: Complex Docker build skipped - simple Python app that works immediately.

**Dependencies**: Minimal (fastapi, uvicorn, pandas, sqlalchemy)
```bash
pip install fastapi uvicorn pandas sqlalchemy psycopg2-binary
```

**Start**:
```bash
python3 simple_main.py  # Kører på http://localhost:8000
```

**Features**:
- CSV upload & processing
- Regex-based PII detection (email, phone, SSN, credit cards)
- Quality validation (completeness, validity, consistency)
- Compliance reporting
- In-memory storage (Week 3 adds DB persistence)

**Test**: Se `QUICKSTART_API.md` eller kør `./test_api.sh`

---

## Reference Materials

### Integration Patterns

All integration examples in `docs/integration-examples/`:
1. `01_adamiao_presidio_pii_detection.py` - PII in Chart layer
2. `02_prefect_openlineage_tracking.py` - Lineage tracking
3. `03_fastapi_celery_pipeline_execution.py` - Async pipelines
4. `04_soda_core_quality_checks.py` - Quality framework
5. `05_opsdroid_bot_integration.py` - Conversational interface

**Copy-paste these patterns** when implementing features - they're production-ready.

### Implementation Plan

**Follow**: `docs/IMPLEMENTATION_PLAN.md` (106KB, 8-week roadmap)
- Phase 1 Week 1: ✅ Complete (infrastructure)
- Phase 1 Week 2: Backend features (in progress)
- Phase 2: Core pipeline (Weeks 3-4)
- Phase 3: API & services (Weeks 5-6)
- Phase 4: Dashboard & deployment (Weeks 7-8)

### Database Schema Reference

**Deployed migrations**: `database/migrations/*.sql` (1,869 lines total)
- 001: Core tables (Explore/Chart/Navigate schemas, 374 lines)
- 002: Pipeline metadata (442 lines)
- 003: Quality metrics (518 lines)
- 004: Compliance (535 lines)

**Original design**: `database/01_core_tables.sql` through `07_bot_logs.sql`

---

## Development Workflow

### Git Worktree Strategy

**Production work happens in worktrees**:
```
.worktrees/
├── atlas-api/       # Backend (current work - Week 1 done)
├── atlas-pipeline/  # Pipeline core (Week 3+)
├── atlas-dashboard/ # Frontend UI (Week 7+)
└── atlas-poc/       # POC validation (reference only)
```

**Never develop in main directory** - always use appropriate worktree.

### When Adding New Features

1. **Check integration examples first** - pattern probably exists
2. **Reference the implementation plan** - see which week it's planned for
3. **Test in POC first** if validating new concept
4. **Deploy to production worktree** once validated
5. **Run all integration tests** before committing
6. **Update migration** if schema changes needed

### Data Quality Standards

All data must meet:
- Completeness: >95%
- Uniqueness: >98%
- Validity: >90%
- Consistency: >90%

These are enforced by Soda Core checks in `chart` layer.

---

## Quick Reference

**Current Phase**: Phase 1 Week 1 ✅ (infrastructure complete)
**Next Phase**: Phase 1 Week 2 (backend features)
**Overall Progress**: 12.5% (Week 1 of 8)

**Working Services**:
- PostgreSQL (localhost:5432) ✅
- Redis (localhost:6379) ✅

**Documentation Locations**:
- Design Doc: `docs/plans/2026-01-09-atlas-platform-design.md`
- Implementation Plan: `docs/IMPLEMENTATION_PLAN.md`
- Use Cases: `docs/USE_CASES.md`
- Week 1 Status: `docs/WEEK1_FINAL_STATUS.md`

**For New Developers**: Start with `atlas-api/QUICKSTART.md` then `README.md`
