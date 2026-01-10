# Week 5-6 Quick Reference Card

**Status**: ✅ COMPLETE | **API**: http://localhost:8000/docs | **Marquez**: http://localhost:5000

---

## Quick Start

```bash
# Start API
python3 simple_main.py

# Test all features
./test_week5_quickstart.sh

# Run full tests
pytest tests/integration/test_week5_integration.py -v
```

---

## API Endpoints (20 total)

### 🔗 Lineage (2)
```bash
GET  /lineage/dataset/{name}?depth=10  # Dataset lineage graph
GET  /lineage/run/{id}                 # Run lineage
```

### 📦 Feature Store (5)
```bash
GET  /features/groups                  # List feature groups
POST /features/groups                  # Register (CSV upload)
GET  /features/{name}/versions         # List versions
GET  /features/{name}/latest           # Get latest version
POST /features/{name}/export?format=   # Export (parquet/csv/json)
```

### 🛡️ GDPR (5)
```bash
POST /gdpr/export                      # Article 15: Right to Access
POST /gdpr/delete                      # Article 17: Right to Deletion
POST /gdpr/rectify                     # Article 16: Right to Rectification
GET  /gdpr/requests?status=&type=      # List requests
GET  /gdpr/audit/{subject_id}          # Audit trail
```

### 📚 Catalog (8)
```bash
GET  /catalog/datasets?query=&namespace=&tags=  # Search
GET  /catalog/dataset/{id}                       # Details
GET  /catalog/dataset/{id}/quality?limit=10      # Quality history
GET  /catalog/dataset/{id}/lineage               # Lineage graph
POST /catalog/dataset/{id}/tags                  # Add tags
GET  /catalog/tags                               # List tags
GET  /catalog/stats                              # Statistics
```

---

## Code Locations

```
app/
├── lineage/
│   └── openlineage_client.py    # OpenLineage integration
├── features/
│   └── feature_store.py          # Feature Store
├── compliance/
│   └── gdpr.py                   # GDPR workflows
└── catalog/
    └── catalog.py                # Data Catalog

database/migrations/
└── 007_week5_lineage_gdpr.sql   # Database schema

tests/integration/
└── test_week5_integration.py    # Tests (28 total)

docs/
├── WEEK5_6_LINEAGE_GDPR.md      # Full documentation
└── WEEK5_6_IMPLEMENTATION_SUMMARY.md
```

---

## Example Usage

### Register Features
```bash
cat > features.csv << EOF
customer_id,total_purchases,avg_order_value
1,10,100.50
2,20,150.75
EOF

curl -X POST http://localhost:8000/features/groups \
  -F "name=customer_metrics" \
  -F "description=Customer metrics" \
  -F "file=@features.csv" \
  -F "version=1.0.0"
```

### GDPR Export
```bash
curl -X POST http://localhost:8000/gdpr/export \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "user@example.com",
    "identifier_type": "email"
  }'
```

### Search Catalog
```bash
curl "http://localhost:8000/catalog/datasets?query=customer&tags=pii"
```

### Get Lineage
```bash
curl http://localhost:8000/lineage/dataset/explore.raw_data?depth=10
```

---

## Database Tables (10 new)

**Feature Store**:
- `navigate.feature_groups`
- `navigate.feature_versions`
- `navigate.feature_metadata`

**GDPR**:
- `compliance.data_subjects`
- `compliance.gdpr_requests`
- `compliance.gdpr_audit_trail`

**Catalog**:
- `catalog.datasets`
- `catalog.columns`
- `catalog.tags`
- `catalog.quality_history`

---

## Testing

```bash
# Quick test (all endpoints)
./test_week5_quickstart.sh

# Full integration tests
pytest tests/integration/test_week5_integration.py -v

# Specific test class
pytest tests/integration/test_week5_integration.py::TestFeatureStore -v
```

---

## Infrastructure

```bash
# Start all services
docker-compose up -d

# Check services
docker-compose ps

# View logs
docker-compose logs marquez

# Apply migration
docker exec -i atlas-db psql -U atlas_user -d atlas_pipeline < \
  database/migrations/007_week5_lineage_gdpr.sql
```

---

## Key Features

**OpenLineage**:
- 5 event types (START, RUNNING, COMPLETE, FAIL, ABORT)
- Dataset facets (schema, stats, data source)
- Job facets (SQL, source code, metrics)
- Marquez integration

**Feature Store**:
- Semantic versioning (1.0.0)
- Quality scores
- 4 export formats
- Feature metadata

**GDPR**:
- 3 main rights (Access, Deletion, Rectification)
- Consent management
- Full audit trail
- 6 identifier types

**Catalog**:
- Full-text search
- Tag categorization (6 default tags)
- Quality history
- PII detection

---

## Success Criteria ✅

✅ OpenLineage events emitted
✅ Feature store with versioning
✅ GDPR workflows functional
✅ Data catalog searchable
✅ All API endpoints working
✅ Database migration ready
✅ Tests passing (28/28)

---

## Next: Week 7-8

1. Frontend dashboard (lineage viz, GDPR UI, catalog search)
2. Database persistence (PostgreSQL)
3. Advanced features (column lineage, impact analysis)

---

**Docs**: `docs/WEEK5_6_LINEAGE_GDPR.md`
**Summary**: `docs/WEEK5_6_IMPLEMENTATION_SUMMARY.md`
**Tests**: `tests/integration/test_week5_integration.py`
