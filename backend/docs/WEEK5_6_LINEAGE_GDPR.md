# Week 5-6: Data Lineage & GDPR Workflows

**Implementation Status**: ✅ Complete (In-Memory Version)
**Database Migration**: `007_week5_lineage_gdpr.sql`
**Date**: 2026-01-09

---

## Overview

Week 5-6 adds advanced data governance capabilities:

1. **OpenLineage Integration** - Data lineage tracking with Marquez
2. **Feature Store** - ML/AI feature management and versioning
3. **GDPR Workflows** - Data subject rights automation (Articles 15-17)
4. **Data Catalog** - Dataset discovery and metadata management

---

## Architecture

### Component Stack

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                             │
│  /lineage/*  /features/*  /gdpr/*  /catalog/*               │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  OpenLineage │  │ Feature Store│  │ GDPR Manager │       │
│  │    Client    │  │              │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐                                            │
│  │ Data Catalog │                                            │
│  └──────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Marquez    │  │  PostgreSQL  │  │  In-Memory   │       │
│  │   (Lineage)  │  │  (Week 7+)   │  │  (Week 5-6)  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. OpenLineage Integration

### Purpose
Track data lineage across all pipeline layers (Explore → Chart → Navigate).

### Implementation

**File**: `app/lineage/openlineage_client.py`

**Key Features**:
- Event types: START, RUNNING, COMPLETE, FAIL, ABORT
- Dataset facets: Schema, data source, statistics
- Job facets: SQL queries, source code location, metrics
- Marquez backend integration

### Usage Example

```python
from app.lineage.openlineage_client import get_lineage_client

client = get_lineage_client()

# Emit START event
client.emit_start_event(
    job_name="csv_to_explore_pipeline",
    run_id="run-123",
    inputs=[{
        "name": "customers.csv",
        "facets": {}
    }],
    outputs=[{
        "name": "explore.raw_data",
        "facets": {}
    }]
)

# Emit COMPLETE event
client.emit_complete_event(
    job_name="csv_to_explore_pipeline",
    run_id="run-123",
    outputs=[{
        "name": "explore.raw_data",
        "facets": {
            "stats": {"rowCount": 1000}
        }
    }],
    metrics={"duration_seconds": 1.5}
)

# Query lineage graph
lineage = client.query_lineage_graph("explore.raw_data", depth=10)
downstream = client.find_downstream_datasets("explore.raw_data")
```

### API Endpoints

**GET /lineage/dataset/{dataset_name}**
```bash
curl http://localhost:8000/lineage/dataset/explore.raw_data?depth=10
```

**GET /lineage/run/{run_id}**
```bash
curl http://localhost:8000/lineage/run/abc-123
```

### Marquez UI

Access lineage visualization at: **http://localhost:5000**

---

## 2. Feature Store

### Purpose
Manage ML/AI features with versioning, quality tracking, and export capabilities.

### Implementation

**File**: `app/features/feature_store.py`

**Key Features**:
- Semantic versioning (major.minor.patch)
- Schema tracking and evolution
- Quality score calculation
- Export formats: Parquet, CSV, JSON, TFRecord
- Feature metadata (null%, unique%, importance)

### Usage Example

```python
from app.features.feature_store import get_feature_store
import pandas as pd

store = get_feature_store()

# Register feature group
df = pd.DataFrame({
    "customer_id": [1, 2, 3],
    "total_purchases": [10, 20, 15],
    "avg_order_value": [100.0, 150.0, 120.0]
})

feature_group = store.register_feature_group(
    name="customer_metrics",
    description="Customer purchase metrics for ML models",
    df=df,
    version="1.0.0",
    tags=["finance", "production"]
)

# Get latest version
latest = store.get_latest_version("customer_metrics")

# Export features
result = store.export_features(
    "customer_metrics",
    format=ExportFormat.PARQUET,
    version="1.0.0"
)
```

### API Endpoints

**POST /features/groups** - Register feature group
```bash
curl -X POST http://localhost:8000/features/groups \
  -F "name=customer_metrics" \
  -F "description=Customer metrics" \
  -F "file=@features.csv" \
  -F "version=1.0.0"
```

**GET /features/groups** - List feature groups
```bash
curl http://localhost:8000/features/groups?tags=finance,production
```

**GET /features/{name}/versions** - Get versions
```bash
curl http://localhost:8000/features/customer_metrics/versions
```

**GET /features/{name}/latest** - Get latest version
```bash
curl http://localhost:8000/features/customer_metrics/latest
```

**POST /features/{name}/export** - Export features
```bash
curl -X POST "http://localhost:8000/features/customer_metrics/export?format=parquet"
```

### Database Schema

```sql
-- Feature groups
CREATE TABLE navigate.feature_groups (
    feature_group_id UUID PRIMARY KEY,
    name VARCHAR(255) UNIQUE,
    description TEXT,
    version VARCHAR(50),
    schema_definition JSONB,
    created_at TIMESTAMP,
    tags TEXT[]
);

-- Feature versions
CREATE TABLE navigate.feature_versions (
    version_id UUID PRIMARY KEY,
    feature_group_id UUID REFERENCES navigate.feature_groups,
    version VARCHAR(50),
    dataset_location TEXT,
    row_count INTEGER,
    quality_score DECIMAL(5,3),
    is_latest BOOLEAN
);

-- Feature metadata
CREATE TABLE navigate.feature_metadata (
    feature_id UUID PRIMARY KEY,
    feature_group_id UUID REFERENCES navigate.feature_groups,
    feature_name VARCHAR(255),
    data_type VARCHAR(50),
    null_percentage DECIMAL(5,3),
    unique_percentage DECIMAL(5,3)
);
```

---

## 3. GDPR Workflows

### Purpose
Automate GDPR data subject rights (Articles 15-17).

### Implementation

**File**: `app/compliance/gdpr.py`

**Key Features**:
- Right to Access (Article 15): Export all subject data
- Right to Deletion (Article 17): Delete all subject PII
- Right to Rectification (Article 16): Update subject data
- Consent management
- Full audit trail

### Usage Example

```python
from app.compliance.gdpr import get_gdpr_manager, IdentifierType

manager = get_gdpr_manager()

# Right to Access
export_data = manager.request_data_access(
    "user@example.com",
    IdentifierType.EMAIL
)

# Right to Deletion
deletion_counts = manager.request_data_deletion(
    "user@example.com",
    IdentifierType.EMAIL,
    reason="User requested account deletion"
)

# Right to Rectification
update_counts = manager.request_data_rectification(
    "user@example.com",
    updates={"email": "new-email@example.com"},
    identifier_type=IdentifierType.EMAIL
)

# Get audit trail
audit_entries = manager.get_audit_trail(subject_id)
```

### API Endpoints

**POST /gdpr/export** - Right to Access (Article 15)
```bash
curl -X POST http://localhost:8000/gdpr/export \
  -H "Content-Type: application/json" \
  -d '{"identifier": "user@example.com", "identifier_type": "email"}'
```

**POST /gdpr/delete** - Right to Deletion (Article 17)
```bash
curl -X POST http://localhost:8000/gdpr/delete \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "user@example.com",
    "identifier_type": "email",
    "reason": "User requested account deletion"
  }'
```

**POST /gdpr/rectify** - Right to Rectification (Article 16)
```bash
curl -X POST http://localhost:8000/gdpr/rectify \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "user@example.com",
    "updates": {"email": "new-email@example.com"},
    "identifier_type": "email"
  }'
```

**GET /gdpr/requests** - List GDPR requests
```bash
curl "http://localhost:8000/gdpr/requests?status=completed&request_type=deletion"
```

**GET /gdpr/audit/{subject_id}** - Get audit trail
```bash
curl http://localhost:8000/gdpr/audit/abc-123
```

### Database Schema

```sql
-- Data subjects
CREATE TABLE compliance.data_subjects (
    subject_id UUID PRIMARY KEY,
    identifier_type VARCHAR(50),  -- email, phone, cpr, ssn, etc.
    identifier_value VARCHAR(255),
    consent_status VARCHAR(50),   -- granted, withdrawn, expired
    consent_date TIMESTAMP,
    consent_purpose TEXT[]
);

-- GDPR requests
CREATE TABLE compliance.gdpr_requests (
    request_id UUID PRIMARY KEY,
    subject_id UUID REFERENCES compliance.data_subjects,
    request_type VARCHAR(50),  -- access, deletion, rectification
    status VARCHAR(50),        -- pending, in_progress, completed, failed
    requested_at TIMESTAMP,
    completed_at TIMESTAMP,
    result JSONB
);

-- Audit trail
CREATE TABLE compliance.gdpr_audit_trail (
    log_id UUID PRIMARY KEY,
    subject_id UUID REFERENCES compliance.data_subjects,
    operation VARCHAR(100),
    performed_by VARCHAR(255),
    timestamp TIMESTAMP,
    details JSONB
);
```

---

## 4. Data Catalog

### Purpose
Centralized dataset discovery and metadata management.

### Implementation

**File**: `app/catalog/catalog.py`

**Key Features**:
- Dataset registry across all layers (Explore, Chart, Navigate)
- Full-text search (name, description, columns)
- Tag-based categorization
- Quality history tracking
- Schema browsing
- Lineage integration

### Usage Example

```python
from app.catalog.catalog import get_data_catalog, DatasetNamespace

catalog = get_data_catalog()

# Register dataset
schema = {
    "fields": [
        {"name": "id", "type": "int64", "nullable": False},
        {"name": "email", "type": "object", "pii_type": "email"}
    ]
}

dataset = catalog.register_dataset(
    namespace=DatasetNamespace.EXPLORE,
    name="raw_customers",
    description="Raw customer data from CRM",
    schema_definition=schema,
    tags=["pii", "gdpr", "production"],
    row_count=10000,
    size_bytes=500000
)

# Search datasets
results = catalog.search_datasets(
    query="customer",
    namespace=DatasetNamespace.EXPLORE,
    tags=["production"]
)

# Add quality history
catalog.add_quality_history(
    dataset.dataset_id,
    completeness_score=0.95,
    validity_score=0.90,
    consistency_score=0.85
)
```

### API Endpoints

**GET /catalog/datasets** - Search datasets
```bash
curl "http://localhost:8000/catalog/datasets?query=customer&namespace=explore&tags=pii"
```

**GET /catalog/dataset/{dataset_id}** - Get dataset details
```bash
curl http://localhost:8000/catalog/dataset/abc-123
```

**GET /catalog/dataset/{dataset_id}/quality** - Quality history
```bash
curl http://localhost:8000/catalog/dataset/abc-123/quality?limit=10
```

**GET /catalog/dataset/{dataset_id}/lineage** - Lineage graph
```bash
curl http://localhost:8000/catalog/dataset/abc-123/lineage
```

**POST /catalog/dataset/{dataset_id}/tags** - Add tags
```bash
curl -X POST http://localhost:8000/catalog/dataset/abc-123/tags \
  -H "Content-Type: application/json" \
  -d '["new_tag", "another_tag"]'
```

**GET /catalog/tags** - List all tags
```bash
curl http://localhost:8000/catalog/tags
```

**GET /catalog/stats** - Catalog statistics
```bash
curl http://localhost:8000/catalog/stats
```

### Database Schema

```sql
-- Datasets
CREATE TABLE catalog.datasets (
    dataset_id UUID PRIMARY KEY,
    namespace VARCHAR(255),  -- explore, chart, navigate
    name VARCHAR(255),
    description TEXT,
    schema_definition JSONB,
    tags TEXT[],
    owner VARCHAR(255),
    row_count_estimate INTEGER,
    size_bytes BIGINT
);

-- Columns
CREATE TABLE catalog.columns (
    column_id UUID PRIMARY KEY,
    dataset_id UUID REFERENCES catalog.datasets,
    column_name VARCHAR(255),
    data_type VARCHAR(100),
    pii_type VARCHAR(50),  -- if contains PII
    nullable BOOLEAN
);

-- Tags
CREATE TABLE catalog.tags (
    tag_id UUID PRIMARY KEY,
    tag_name VARCHAR(100) UNIQUE,
    color VARCHAR(7),  -- hex color
    description TEXT
);

-- Quality history
CREATE TABLE catalog.quality_history (
    history_id UUID PRIMARY KEY,
    dataset_id UUID REFERENCES catalog.datasets,
    timestamp TIMESTAMP,
    completeness_score DECIMAL(5,3),
    validity_score DECIMAL(5,3),
    consistency_score DECIMAL(5,3),
    overall_score DECIMAL(5,3)
);
```

---

## Testing

### Run Integration Tests

```bash
cd /Users/sven/Desktop/MCP/.worktrees/atlas-api
pytest tests/integration/test_week5_integration.py -v
```

### Test Coverage

- ✅ OpenLineage client initialization and event emission
- ✅ Feature Store registration, versioning, and export
- ✅ GDPR workflows (Access, Deletion, Rectification)
- ✅ Data Catalog search, tagging, and quality history

---

## Database Migration

### Apply Migration

```bash
cd /Users/sven/Desktop/MCP/.worktrees/atlas-api

# Apply migration
docker exec -i atlas-db psql -U atlas_user -d atlas_pipeline < database/migrations/007_week5_lineage_gdpr.sql
```

### Verify Migration

```bash
docker exec -it atlas-db psql -U atlas_user -d atlas_pipeline

# Check feature store tables
\dt navigate.feature*

# Check GDPR tables
\dt compliance.data_subjects
\dt compliance.gdpr_requests
\dt compliance.gdpr_audit_trail

# Check catalog schema
\dn catalog
\dt catalog.*
```

---

## Infrastructure Setup

### Start Services

```bash
cd /Users/sven/Desktop/MCP/.worktrees/atlas-api

# Start all services (including Marquez)
docker-compose up -d

# Verify Marquez is running
curl http://localhost:5000/api/v1/namespaces
```

### Access Services

- **API**: http://localhost:8000/docs
- **Marquez UI**: http://localhost:5000
- **Database**: localhost:5432 (atlas_pipeline)
- **Marquez DB**: localhost:5433 (marquez)

---

## Current Status

### Implemented (Week 5-6)

✅ OpenLineage client with Marquez integration
✅ Feature Store with versioning and quality tracking
✅ GDPR workflows (Access, Deletion, Rectification)
✅ Data Catalog with search and tagging
✅ API endpoints for all features
✅ Database migration
✅ Integration tests

### In-Memory vs Database

**Current (Week 5-6)**: In-memory storage for rapid development
**Week 7+**: Full PostgreSQL persistence with Alembic migrations

---

## Next Steps (Week 7-8)

1. **Frontend Dashboard**
   - Lineage visualization (D3.js or react-flow)
   - GDPR request management UI
   - Feature Store browser
   - Data Catalog search interface

2. **Database Persistence**
   - Move from in-memory to PostgreSQL
   - Add Alembic migrations
   - Performance optimization with indexes

3. **Advanced Features**
   - Column-level lineage
   - Impact analysis automation
   - GDPR consent UI
   - Feature importance from ML models

---

## API Reference

See interactive API documentation at: **http://localhost:8000/docs**

### Quick Reference

**Lineage**:
- `GET /lineage/dataset/{name}` - Dataset lineage graph
- `GET /lineage/run/{id}` - Run lineage

**Features**:
- `GET /features/groups` - List feature groups
- `POST /features/groups` - Register feature group
- `GET /features/{name}/versions` - List versions
- `GET /features/{name}/latest` - Get latest version
- `POST /features/{name}/export` - Export features

**GDPR**:
- `POST /gdpr/export` - Right to Access
- `POST /gdpr/delete` - Right to Deletion
- `POST /gdpr/rectify` - Right to Rectification
- `GET /gdpr/requests` - List requests
- `GET /gdpr/audit/{id}` - Audit trail

**Catalog**:
- `GET /catalog/datasets` - Search datasets
- `GET /catalog/dataset/{id}` - Dataset details
- `GET /catalog/dataset/{id}/quality` - Quality history
- `GET /catalog/dataset/{id}/lineage` - Lineage graph
- `POST /catalog/dataset/{id}/tags` - Add tags
- `GET /catalog/tags` - List tags
- `GET /catalog/stats` - Catalog statistics

---

## Troubleshooting

### Marquez Not Available

If lineage operations fail gracefully:
```bash
# Check Marquez status
docker-compose ps marquez

# View Marquez logs
docker-compose logs marquez

# Restart Marquez
docker-compose restart marquez
```

### Migration Issues

```bash
# Check current schema
docker exec -it atlas-db psql -U atlas_user -d atlas_pipeline -c "\dn+"

# Re-apply migration
docker exec -i atlas-db psql -U atlas_user -d atlas_pipeline < database/migrations/007_week5_lineage_gdpr.sql
```

---

## References

- **OpenLineage**: https://openlineage.io/docs/spec/
- **Marquez**: https://marquezproject.github.io/marquez/
- **GDPR**: https://gdpr.eu/
- **Feature Store Patterns**: Feast, Tecton, Hopsworks
- **Data Catalog Patterns**: DataHub, Apache Atlas, Amundsen

---

**Status**: ✅ Week 5-6 Implementation Complete
**Next**: Week 7-8 Frontend Dashboard & Database Persistence
