# Integration Examples Index

Quick navigation for all integration examples and documentation.

## 📚 Documentation Files

| File | Description | Lines |
|------|-------------|-------|
| [README.md](./README.md) | Complete integration guide with architecture diagrams | 454 |
| [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) | Quick copy-paste code snippets and patterns | 495 |
| [../INTEGRATION_SUMMARY.md](../INTEGRATION_SUMMARY.md) | High-level summary and statistics | ~600 |

## 🐍 Python Integration Examples

### 1. PII Detection
**File**: [01_adamiao_presidio_pii_detection.py](./01_adamiao_presidio_pii_detection.py)
**Lines**: 417
**Deps**: `presidio-analyzer`, `presidio-anonymizer`, `tenacity`, `pandas`

**Classes**:
- `PIIDetectionConfig` - Configuration for PII detection
- `PIIDetector` - Main PII detection and anonymization engine
- `SilverLayerTransformer` - Bronze → Silver with PII handling

**Quick Start**:
```bash
pip install presidio-analyzer presidio-anonymizer tenacity pandas
python 01_adamiao_presidio_pii_detection.py
```

---

### 2. Data Lineage Tracking
**File**: [02_prefect_openlineage_tracking.py](./02_prefect_openlineage_tracking.py)
**Lines**: 590
**Deps**: `prefect`, `openlineage-python`, `openlineage-sql`, `requests`, `pandas`

**Classes**:
- `LineageConfig` - Configuration for OpenLineage/Marquez
- `LineageTracker` - Wrapper around OpenLineage client

**Prefect Tasks**:
- `extract_from_bronze` - Bronze extraction with lineage
- `transform_to_silver` - Silver transformation with lineage
- `load_to_gold` - Gold loading with lineage

**Quick Start**:
```bash
pip install prefect openlineage-python pandas
docker run -d -p 5000:5000 marquezproject/marquez
python 02_prefect_openlineage_tracking.py
```

---

### 3. Async API Execution
**File**: [03_fastapi_celery_pipeline_execution.py](./03_fastapi_celery_pipeline_execution.py)
**Lines**: 646
**Deps**: `fastapi`, `celery`, `redis`, `uvicorn`, `sqlalchemy`, `psycopg2-binary`, `pydantic`

**Classes**:
- `AppConfig` - Application configuration
- `PipelineRun` - Database model for pipeline runs
- `AtlasPipelineTask` - Custom Celery task base class

**API Endpoints**:
- `POST /pipelines/execute` - Queue pipeline
- `GET /pipelines/{run_id}` - Check status
- `GET /pipelines` - List recent runs
- `DELETE /pipelines/{run_id}/cancel` - Cancel pipeline

**Quick Start**:
```bash
pip install fastapi celery redis uvicorn sqlalchemy psycopg2-binary pydantic
docker run -d -p 6379:6379 redis
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres
celery -A 03_fastapi_celery_pipeline_execution worker --loglevel=info &
uvicorn 03_fastapi_celery_pipeline_execution:app --reload
```

---

### 4. Quality Validation
**File**: [04_soda_core_quality_checks.py](./04_soda_core_quality_checks.py)
**Lines**: 696
**Deps**: `soda-core-postgres`, `soda-core-scientific`, `pandas`, `sqlalchemy`, `psycopg2-binary`, `pyyaml`

**Classes**:
- `QualityConfig` - Quality check configuration
- `QualityCheckRun` - Database model for check runs
- `QualityMetric` - Database model for metrics
- `SodaCheckGenerator` - Generate YAML checks for Bronze/Silver/Gold
- `QualityCheckExecutor` - Execute checks and store results
- `PipelineWithQualityGates` - Integrated pipeline with quality gates

**Quick Start**:
```bash
pip install soda-core-postgres soda-core-scientific pandas sqlalchemy psycopg2-binary pyyaml
python 04_soda_core_quality_checks.py
```

---

### 5. Chat Bot Interface
**File**: [05_opsdroid_bot_integration.py](./05_opsdroid_bot_integration.py)
**Lines**: 667
**Deps**: `opsdroid`, `aiohttp`, `requests`, `pandas`, `python-dateutil`

**Classes**:
- `AtlasConfig` - Bot configuration
- `AtlasPipelineClient` - Async HTTP client for Atlas API
- `AtlasPipelineSkill` - Opsdroid skill with commands

**Commands**:
- `run pipeline <name> for <table>` - Execute pipeline
- `status <run-id>` - Check pipeline status
- `list pipelines` - Show recent runs
- `quality report for <run-id>` - Show quality metrics
- `cancel <run-id>` - Cancel pipeline
- `help` - Show commands

**Quick Start**:
```bash
pip install opsdroid aiohttp requests pandas python-dateutil
# Configure ~/.opsdroid/configuration.yaml
opsdroid start
```

---

## 🎯 Use Case → Example Mapping

| Use Case | Example | Key Feature |
|----------|---------|-------------|
| Detect PII in data | #1 | Presidio + retry logic |
| Track data lineage | #2 | OpenLineage events |
| Async pipeline execution | #3 | FastAPI + Celery |
| Validate data quality | #4 | Soda Core YAML checks |
| Chat-based pipeline control | #5 | Opsdroid skills |

## 🔧 Technology Stack

### Core Technologies
- **Python 3.9+**: All examples
- **Pandas**: Data manipulation
- **SQLAlchemy**: Database ORM
- **PostgreSQL**: Data storage

### Integration Technologies
- **Presidio**: PII detection (Microsoft)
- **Prefect**: Workflow orchestration
- **OpenLineage**: Lineage standard (Linux Foundation)
- **Marquez**: Lineage backend/UI
- **FastAPI**: Modern async API framework
- **Celery**: Distributed task queue
- **Redis**: Message broker
- **Soda Core**: Data quality framework
- **Opsdroid**: Chatbot framework

## 📊 Statistics

### Code Metrics
- **Total Lines**: 3,965
- **Python Code**: 3,016 lines (76%)
- **Documentation**: 949 lines (24%)
- **Files**: 7 (5 Python, 2 Markdown)

### Complexity Metrics
- **Classes**: 20 total
- **Functions**: 79 total
- **API Endpoints**: 4 (FastAPI)
- **Bot Commands**: 6 (Opsdroid)
- **Database Models**: 3 (SQLAlchemy)

## 🚀 Recommended Reading Order

### For Beginners
1. [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - Start here
2. [README.md](./README.md) - Detailed guide
3. [01_adamiao_presidio_pii_detection.py](./01_adamiao_presidio_pii_detection.py) - Simplest example
4. [04_soda_core_quality_checks.py](./04_soda_core_quality_checks.py) - Next complexity
5. Other examples as needed

### For Advanced Users
1. [README.md](./README.md) - Architecture overview
2. [02_prefect_openlineage_tracking.py](./02_prefect_openlineage_tracking.py) - Lineage patterns
3. [03_fastapi_celery_pipeline_execution.py](./03_fastapi_celery_pipeline_execution.py) - Async patterns
4. [INTEGRATION_SUMMARY.md](../INTEGRATION_SUMMARY.md) - System design
5. Customize and combine patterns

## 🔗 External Links

### Official Documentation
- [Presidio Documentation](https://microsoft.github.io/presidio/)
- [Prefect Documentation](https://docs.prefect.io/)
- [OpenLineage Specification](https://openlineage.io/)
- [Marquez Documentation](https://marquezproject.ai/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Soda Core Documentation](https://docs.soda.io/soda-core/overview.html)
- [Opsdroid Documentation](https://docs.opsdroid.dev/)

### Related Atlas Documentation
- [Atlas POC README](../../atlas-poc/README.md)
- [API Documentation](../../atlas-poc/src/api/README.md)
- [Pipeline Documentation](../../atlas-poc/src/pipeline/README.md)

## 📝 Quick Commands Cheat Sheet

```bash
# Install all dependencies
pip install presidio-analyzer presidio-anonymizer tenacity \
  prefect openlineage-python fastapi celery redis uvicorn \
  sqlalchemy psycopg2-binary pydantic soda-core-postgres \
  opsdroid aiohttp requests pandas python-dateutil pyyaml

# Start infrastructure (Docker)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres
docker run -d -p 6379:6379 redis
docker run -d -p 5000:5000 marquezproject/marquez

# Run examples
python 01_adamiao_presidio_pii_detection.py
python 02_prefect_openlineage_tracking.py
python 04_soda_core_quality_checks.py

# Start API + workers
celery -A 03_fastapi_celery_pipeline_execution worker --loglevel=info &
uvicorn 03_fastapi_celery_pipeline_execution:app --reload &

# Start bot
opsdroid start
```

## ✅ Checklist for Integration

Before integrating into your pipeline:

- [ ] Read the specific integration example file
- [ ] Understand the WHY comments
- [ ] Install dependencies
- [ ] Test with provided sample data
- [ ] Configure connection strings
- [ ] Update error handling for your use case
- [ ] Add monitoring/alerting
- [ ] Set up proper secret management
- [ ] Run integration tests
- [ ] Deploy and monitor

---

**Navigate**: [README](./README.md) | [Quick Reference](./QUICK_REFERENCE.md) | [Summary](../INTEGRATION_SUMMARY.md)
