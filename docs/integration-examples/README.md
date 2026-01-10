# Atlas Pipeline Integration Examples

This directory contains **copy-paste ready code examples** demonstrating how to integrate key open-source tools into the Atlas data pipeline platform.

## 📋 Overview

Each example is a **complete, runnable Python file** with:
- ✅ Detailed inline comments explaining **WHY** each piece is needed
- ✅ Production-ready error handling and retry logic
- ✅ Database models and configuration
- ✅ Example usage and testing instructions
- ✅ Dependencies list

## 🗂️ Integration Examples

### 1. [adamiao + Presidio PII Detection](./01_adamiao_presidio_pii_detection.py)

**What it does**: Adds robust PII detection and anonymization to the Silver layer transformation.

**Key integrations**:
- adamiao-style retry logic with exponential backoff (using `tenacity`)
- Microsoft Presidio for PII detection (names, emails, SSNs, phone numbers)
- Automatic PII masking before data reaches Gold/AI layers
- GDPR-compliant anonymization strategies (hash, mask, redact)

**Use cases**:
- Ensuring GDPR/CCPA compliance
- Protecting customer data in analytics pipelines
- Audit trail for PII handling

**Dependencies**:
```bash
pip install presidio-analyzer presidio-anonymizer tenacity pandas
```

**Key patterns**:
- Configuration-as-code for retry behavior
- Custom exception types for PII errors
- Metadata tracking for audit trails
- Retry-wrapped API calls for resilience

---

### 2. [Prefect + OpenLineage/Marquez Tracking](./02_prefect_openlineage_tracking.py)

**What it does**: Adds complete data lineage tracking from Bronze → Silver → Gold layers.

**Key integrations**:
- Prefect for workflow orchestration (tasks, flows, scheduling)
- OpenLineage for standardized lineage events (Linux Foundation standard)
- Marquez as lineage backend with visual graph UI
- Dataset facets for schema and metadata tracking

**Use cases**:
- Impact analysis ("What breaks if I change this table?")
- Root cause analysis for data quality issues
- Compliance and audit requirements
- Column-level lineage tracking

**Dependencies**:
```bash
pip install prefect openlineage-python openlineage-sql requests pandas
```

**Key patterns**:
- START/COMPLETE/FAIL event lifecycle
- Dataset facets for rich metadata
- Job facets for SQL queries and source code
- Downstream impact analysis via Marquez API

---

### 3. [FastAPI + Celery Pipeline Execution](./03_fastapi_celery_pipeline_execution.py)

**What it does**: Provides REST API for async pipeline execution with queuing and status tracking.

**Key integrations**:
- FastAPI for modern async REST API
- Celery for distributed task execution
- Redis/RabbitMQ as message broker
- PostgreSQL for persistent result storage

**Use cases**:
- Triggering pipelines from external systems
- Long-running pipeline jobs without blocking API
- Distributed pipeline execution across workers
- Retry and scheduling capabilities

**Dependencies**:
```bash
pip install fastapi celery redis uvicorn sqlalchemy psycopg2-binary pydantic
```

**Key patterns**:
- Immediate API response with run_id
- Background Celery workers process jobs
- Database tracking for status across restarts
- Custom Celery task classes for lifecycle hooks

**API endpoints**:
- `POST /pipelines/execute` - Queue pipeline
- `GET /pipelines/{run_id}` - Check status
- `GET /pipelines` - List recent runs
- `DELETE /pipelines/{run_id}/cancel` - Cancel job

---

### 4. [Soda Core Quality Checks](./04_soda_core_quality_checks.py)

**What it does**: Implements automated data quality validation at each pipeline layer.

**Key integrations**:
- Soda Core for declarative quality checks (SQL-based)
- YAML-based quality definitions (version-controlled)
- PostgreSQL for historical quality metrics
- Automated quality gates that stop bad data

**Use cases**:
- Preventing bad data from reaching Gold layer
- Historical quality trend analysis
- Automated alerting on quality degradation
- Compliance and SLA monitoring

**Dependencies**:
```bash
pip install soda-core-postgres soda-core-scientific pandas sqlalchemy psycopg2-binary pyyaml
```

**Key patterns**:
- Layer-specific quality checks (Bronze/Silver/Gold)
- YAML generators for common check patterns
- Quality gate enforcement in pipelines
- Time-series quality metric storage

**Quality dimensions**:
- **Completeness**: Non-null values, required fields
- **Validity**: Format correctness (emails, phones)
- **Uniqueness**: Duplicate detection
- **Consistency**: Outlier detection, distribution checks
- **Freshness**: Data recency validation

---

### 5. [Opsdroid Bot Integration](./05_opsdroid_bot_integration.py)

**What it does**: Enables conversational pipeline management via Microsoft Teams or Slack.

**Key integrations**:
- Opsdroid chatbot framework for natural language commands
- Skills for pipeline triggering, status checks, quality reports
- Microsoft Teams and Slack connectors
- Background monitoring with proactive notifications

**Use cases**:
- Non-technical users triggering pipelines via chat
- Real-time pipeline status notifications
- Quality report delivery to stakeholders
- Democratizing data pipeline access

**Dependencies**:
```bash
pip install opsdroid aiohttp requests pandas python-dateutil
```

**Key patterns**:
- Regex-based natural language matching
- Async HTTP client for API communication
- Background task monitoring
- Rich formatted responses with emoji

**Chat commands**:
```
• "run pipeline bronze_to_silver for customers"
• "status abc-123"
• "list recent pipelines"
• "quality report for abc-123"
• "cancel abc-123"
• "help"
```

---

## 🚀 Quick Start

### Running Individual Examples

Each example is standalone and can be run directly:

```bash
# 1. Install dependencies for the example
pip install -r requirements.txt  # (create per-example)

# 2. Configure connection strings and API keys
# Edit the Config class in each file

# 3. Run the example
python 01_adamiao_presidio_pii_detection.py
```

### Integration into Atlas Pipeline

To integrate into your Atlas pipeline:

1. **Read the file** - Each example has extensive inline comments
2. **Copy relevant classes** - Extract the classes you need
3. **Update configuration** - Adjust connection strings and parameters
4. **Add to your pipeline** - Import and use in your pipeline code

Example:
```python
# In your pipeline code
from integration_examples.pii_detection import PIIDetector, PIIDetectionConfig

# Initialize
config = PIIDetectionConfig(confidence_threshold=0.7)
pii_detector = PIIDetector(config)

# Use in Silver layer
pii_findings = pii_detector.detect_pii_in_dataframe(bronze_df)
silver_df = pii_detector.anonymize_dataframe(bronze_df, pii_findings)
```

---

## 🎯 Integration Architecture

Here's how all integrations work together:

```
┌─────────────────────────────────────────────────────────────┐
│                     External Triggers                        │
│  • REST API (FastAPI)                                        │
│  • Chat Bot (Opsdroid)                                       │
│  • Scheduled Jobs (Prefect)                                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    Pipeline Orchestration                    │
│  • Prefect Flows (workflow management)                       │
│  • Celery Tasks (async execution)                            │
│  • OpenLineage Events (lineage tracking)                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                     Data Transformations                     │
│                                                              │
│  Bronze Layer (Raw)                                          │
│    └─> Soda Core: Basic quality checks                      │
│                                                              │
│  Silver Layer (Clean)                                        │
│    ├─> Presidio: PII detection & masking                    │
│    └─> Soda Core: Business rule validation                  │
│                                                              │
│  Gold Layer (Analytics)                                      │
│    └─> Soda Core: Aggregation validation                    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                      Observability                           │
│  • Marquez: Lineage visualization                            │
│  • PostgreSQL: Quality metrics history                       │
│  • Opsdroid: Proactive notifications                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Infrastructure Requirements

### Minimum Setup

```yaml
# Docker Compose example
version: '3.8'

services:
  # Data warehouse
  postgres:
    image: postgres:14
    ports: ["5432:5432"]
    environment:
      POSTGRES_PASSWORD: password

  # Message broker for Celery
  redis:
    image: redis:7
    ports: ["6379:6379"]

  # Lineage backend
  marquez:
    image: marquezproject/marquez:latest
    ports: ["5000:5000"]

  # Atlas API
  atlas-api:
    build: .
    ports: ["8000:8000"]
    depends_on: [postgres, redis]

  # Celery worker
  celery-worker:
    build: .
    command: celery -A app worker --loglevel=info
    depends_on: [redis, postgres]

  # Opsdroid bot
  opsdroid:
    image: opsdroid/opsdroid:latest
    volumes:
      - ./opsdroid:/root/.opsdroid
    depends_on: [atlas-api]
```

---

## 📊 Monitoring & Observability

### Key Metrics to Track

1. **Pipeline Execution**
   - Success/failure rate
   - Execution duration
   - Queue depth (Celery)
   - Throughput (rows/second)

2. **Data Quality**
   - Quality score trends
   - Failed check frequency
   - PII detection rate
   - Schema changes

3. **Data Lineage**
   - Dataset dependencies
   - Job execution patterns
   - Impact analysis queries
   - Lineage graph complexity

4. **Bot Usage**
   - Command frequency
   - User engagement
   - Response time
   - Error rate

### Dashboards

Recommended tools:
- **Grafana** for metrics visualization
- **Marquez** for lineage graphs
- **Prefect Cloud/Server** for workflow monitoring
- **Flower** for Celery task monitoring

---

## 🤝 Contributing

To add more integration examples:

1. **Follow the template**:
   - Start with module docstring explaining WHAT and WHY
   - Include inline comments for every significant block
   - Add example usage at the bottom
   - Provide setup instructions

2. **Code standards**:
   - Type hints for all functions
   - Docstrings with Args/Returns
   - Error handling with logging
   - Configuration via dataclasses

3. **Documentation**:
   - Update this README with new example
   - Add to architecture diagram
   - Include in quick start guide

---

## 📚 Additional Resources

### Related Documentation
- [Atlas POC README](../../atlas-poc/README.md)
- [API Documentation](../../atlas-poc/src/api/README.md)
- [Pipeline Architecture](../../architecture.md)

### External Resources
- [Presidio Documentation](https://microsoft.github.io/presidio/)
- [Prefect Documentation](https://docs.prefect.io/)
- [OpenLineage Specification](https://openlineage.io/)
- [Soda Core Documentation](https://docs.soda.io/soda-core/overview.html)
- [Opsdroid Documentation](https://docs.opsdroid.dev/)

---

## ❓ FAQ

### Q: Can I use these examples in production?

A: These examples provide production-ready patterns but require:
- Proper secret management (not hardcoded)
- Monitoring and alerting setup
- High availability configuration
- Security hardening (authentication, authorization)
- Load testing and capacity planning

### Q: Do I need all integrations?

A: No! Start with the integrations that solve your immediate needs:
- **Critical**: FastAPI + Celery (async execution)
- **Important**: Soda Core (quality), Presidio (PII)
- **Nice-to-have**: OpenLineage (lineage), Opsdroid (bot)

### Q: How do I handle secrets?

A: Use environment variables or secret management:
```python
import os
from dotenv import load_dotenv

load_dotenv()

config = Config(
    database_url=os.getenv("DATABASE_URL"),
    api_key=os.getenv("API_KEY")
)
```

### Q: Can I mix and match integrations?

A: Yes! Each integration is designed to be:
- **Independent**: Works standalone
- **Composable**: Can be combined
- **Configurable**: Easy to customize

---

## 📝 License

These examples are provided as part of the Atlas platform under [LICENSE](../../LICENSE).

---

## 🆘 Support

For questions or issues:
1. Check inline comments in each example file
2. Review the WHY comments for design decisions
3. Open an issue in the repository
4. Consult the external documentation links

---

**Happy integrating! 🚀**
