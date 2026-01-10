# Quick Reference: Integration Examples

> **TL;DR**: Copy-paste these code snippets to integrate key tools into your Atlas pipeline.

## 🎯 Quick Start by Use Case

### "I need to detect and mask PII"
→ Use **Example 1**: adamiao + Presidio

```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# Detect PII
analyzer = AnalyzerEngine()
findings = analyzer.analyze(text="John's email is john@example.com", entities=["EMAIL_ADDRESS"], language="en")

# Anonymize
anonymizer = AnonymizerEngine()
result = anonymizer.anonymize(text="John's email is john@example.com", analyzer_results=findings)
# Output: "John's email is <EMAIL_ADDRESS>"
```

**File**: `01_adamiao_presidio_pii_detection.py`
**Key classes**: `PIIDetector`, `SilverLayerTransformer`

---

### "I need data lineage tracking"
→ Use **Example 2**: Prefect + OpenLineage

```python
from openlineage.client import OpenLineageClient
from openlineage.client.run import RunEvent, RunState, Run, Job, Dataset

# Emit lineage event
client = OpenLineageClient(url="http://localhost:5000/api/v1/lineage")
event = RunEvent(
    eventType=RunState.COMPLETE,
    eventTime=datetime.utcnow().isoformat(),
    run=Run(runId=str(uuid.uuid4())),
    job=Job(namespace="atlas", name="bronze_to_silver"),
    inputs=[Dataset(namespace="atlas", name="bronze.customers")],
    outputs=[Dataset(namespace="atlas", name="silver.customers")],
    producer="atlas_v1"
)
client.emit(event)
```

**File**: `02_prefect_openlineage_tracking.py`
**Key classes**: `LineageTracker`

---

### "I need async pipeline execution"
→ Use **Example 3**: FastAPI + Celery

```python
from fastapi import FastAPI
from celery import Celery

app = FastAPI()
celery_app = Celery("tasks", broker="redis://localhost:6379/0")

@celery_app.task
def run_pipeline(table_name: str):
    # Your pipeline logic here
    return {"status": "success", "rows": 1000}

@app.post("/pipeline/execute")
async def execute_pipeline(table_name: str):
    task = run_pipeline.apply_async(args=[table_name])
    return {"task_id": task.id, "status": "queued"}
```

**File**: `03_fastapi_celery_pipeline_execution.py`
**Key classes**: `AtlasPipelineTask`

---

### "I need data quality checks"
→ Use **Example 4**: Soda Core

```yaml
# checks.yml
checks for customers:
  - row_count:
      fail:
        when < 1
  - missing_count(email):
      warn:
        when > 5%
      fail:
        when > 10%
  - duplicate_count:
      fail:
        when > 0
```

```python
from soda.scan import Scan

scan = Scan()
scan.set_data_source_name("postgres_warehouse")
scan.add_configuration_yaml_file("config.yml")
scan.add_sodacl_yaml_file("checks.yml")
scan.execute()

# Check results
for check in scan.scan_results:
    print(f"{check.check.name}: {check.outcome}")
```

**File**: `04_soda_core_quality_checks.py`
**Key classes**: `QualityCheckExecutor`, `SodaCheckGenerator`

---

### "I need a chatbot for pipelines"
→ Use **Example 5**: Opsdroid

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

class PipelineBot(Skill):
    @match_regex(r"run pipeline (?P<name>\w+)")
    async def run_pipeline(self, message):
        pipeline = message.regex["name"]
        # Trigger pipeline via API
        await message.respond(f"✅ Starting pipeline: {pipeline}")
```

**File**: `05_opsdroid_bot_integration.py`
**Key classes**: `AtlasPipelineSkill`, `AtlasPipelineClient`

---

## 📦 Installation Commands

### All Dependencies at Once
```bash
# Install everything
pip install \
  presidio-analyzer presidio-anonymizer tenacity \
  prefect openlineage-python openlineage-sql \
  fastapi celery redis uvicorn sqlalchemy psycopg2-binary pydantic \
  soda-core-postgres soda-core-scientific pyyaml \
  opsdroid aiohttp requests pandas python-dateutil
```

### Minimal Setup (API + Quality only)
```bash
pip install fastapi celery redis uvicorn sqlalchemy soda-core-postgres pandas
```

---

## 🔗 Integration Combinations

### Recommended Stack #1: Complete Data Platform
```
FastAPI + Celery → Async execution
Prefect + OpenLineage → Orchestration + Lineage
Presidio → PII protection
Soda Core → Quality validation
Opsdroid → Chat interface
```

### Recommended Stack #2: Quality-First
```
FastAPI + Celery → Async execution
Presidio → PII protection
Soda Core → Quality validation
```

### Recommended Stack #3: Observability-First
```
FastAPI + Celery → Async execution
Prefect + OpenLineage → Orchestration + Lineage
Soda Core → Quality validation
```

---

## 🚀 Common Code Patterns

### Pattern 1: Silver Layer with PII + Quality

```python
from pii_detection import PIIDetector, PIIDetectionConfig
from quality_checks import QualityCheckExecutor, QualityConfig

# Initialize
pii_detector = PIIDetector(PIIDetectionConfig(confidence_threshold=0.7))
quality_executor = QualityCheckExecutor(QualityConfig())

# Transform Bronze → Silver
def bronze_to_silver(bronze_df: pd.DataFrame, table_name: str):
    # Step 1: Quality check on Bronze
    bronze_checks = generate_bronze_checks(table_name, bronze_df.columns.tolist())
    bronze_quality = quality_executor.run_quality_checks(table_name, "bronze", bronze_checks)

    if bronze_quality["overall_status"] == "fail":
        raise ValueError("Bronze quality check failed")

    # Step 2: Detect and mask PII
    pii_findings = pii_detector.detect_pii_in_dataframe(bronze_df)
    silver_df = pii_detector.anonymize_dataframe(bronze_df, pii_findings)

    # Step 3: Quality check on Silver
    silver_checks = generate_silver_checks(table_name, pii_columns=["email", "phone"])
    silver_quality = quality_executor.run_quality_checks(table_name, "silver", silver_checks)

    return silver_df, {"bronze": bronze_quality, "silver": silver_quality}
```

---

### Pattern 2: API-Triggered Pipeline with Lineage

```python
from fastapi import FastAPI
from celery import Celery
from lineage_tracking import LineageTracker

app = FastAPI()
celery_app = Celery("pipeline", broker="redis://localhost:6379/0")

@celery_app.task
def run_pipeline_with_lineage(run_id: str, table_name: str):
    tracker = LineageTracker()

    # Emit START event
    tracker.emit_start_event(
        job_name=f"bronze_to_silver_{table_name}",
        run_id=run_id,
        inputs=[{"name": f"bronze.{table_name}", "facets": {}}],
        outputs=[{"name": f"silver.{table_name}", "facets": {}}]
    )

    try:
        # Execute pipeline
        result = transform_data(table_name)

        # Emit COMPLETE event
        tracker.emit_complete_event(
            job_name=f"bronze_to_silver_{table_name}",
            run_id=run_id,
            outputs=[{"name": f"silver.{table_name}", "facets": result["facets"]}],
            metrics={"rows_processed": result["rows"]}
        )

        return result

    except Exception as e:
        # Emit FAIL event
        tracker.emit_fail_event(
            job_name=f"bronze_to_silver_{table_name}",
            run_id=run_id,
            error_message=str(e)
        )
        raise

@app.post("/pipeline/execute")
async def execute(table_name: str):
    run_id = str(uuid.uuid4())
    task = run_pipeline_with_lineage.apply_async(args=[run_id, table_name])
    return {"run_id": run_id, "task_id": task.id}
```

---

### Pattern 3: Chatbot-Triggered Pipeline

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex
import aiohttp

class PipelineBot(Skill):
    @match_regex(r"run pipeline (?P<pipeline>\w+) for (?P<table>\w+)")
    async def run_pipeline(self, message):
        pipeline = message.regex["pipeline"]
        table = message.regex["table"]

        # Call Atlas API
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/pipelines/execute",
                json={"pipeline_name": pipeline, "table_name": table}
            ) as response:
                result = await response.json()

        # Respond
        await message.respond(
            f"✅ Pipeline queued!\n"
            f"Run ID: {result['run_id']}\n"
            f"Use 'status {result['run_id']}' to check progress."
        )
```

---

## 🎨 Architecture Diagrams

### Data Flow with All Integrations

```
┌─────────────┐
│  Opsdroid   │  Chat: "run pipeline bronze_to_silver for customers"
│   (Chat)    │
└──────┬──────┘
       │ HTTP Request
       ▼
┌─────────────────────┐
│  FastAPI            │  POST /pipelines/execute
│  (API Gateway)      │  → Returns run_id immediately
└──────┬──────────────┘
       │ Queue Task
       ▼
┌─────────────────────┐
│  Celery             │  Async execution
│  (Task Queue)       │  → run_pipeline(run_id, table)
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Prefect            │  Workflow orchestration
│  (Orchestrator)     │  → @flow bronze_to_silver()
└──────┬──────────────┘
       │
       ├─> OpenLineage: Emit START event
       │
       ▼
┌─────────────────────┐
│  Bronze Layer       │
│  (Raw Data)         │
└──────┬──────────────┘
       │
       ├─> Soda Core: Run quality checks
       │
       ▼
┌─────────────────────┐
│  Silver Layer       │
│  (Clean Data)       │
└──────┬──────────────┘
       │
       ├─> Presidio: Detect & mask PII
       ├─> Soda Core: Validate quality
       │
       ▼
┌─────────────────────┐
│  Gold Layer         │
│  (Analytics Data)   │
└──────┬──────────────┘
       │
       ├─> OpenLineage: Emit COMPLETE event
       ├─> Store metrics in PostgreSQL
       │
       ▼
┌─────────────────────┐
│  Marquez            │  View lineage graph
│  (Lineage UI)       │  Impact analysis
└─────────────────────┘
```

---

## 📊 Performance Benchmarks

### Typical Performance (1M rows)

| Operation                  | Time     | Notes                           |
|----------------------------|----------|---------------------------------|
| Bronze → Silver (no PII)   | ~30s     | Data cleaning + validation      |
| Bronze → Silver (with PII) | ~45s     | Adds Presidio scanning          |
| Soda Core quality checks   | ~10s     | 10 checks across 5 columns      |
| OpenLineage event emission | <100ms   | Async, non-blocking             |
| API response time          | <50ms    | Return immediately, queue task  |

### Scalability

- **Celery workers**: Add workers to process more pipelines in parallel
- **Presidio**: Cache analyzer initialization (saves ~2s per run)
- **Soda Core**: Run checks on sample for large datasets
- **OpenLineage**: Batch events for high-throughput scenarios

---

## 🔒 Security Checklist

### Before Production

- [ ] Replace hardcoded credentials with environment variables
- [ ] Enable authentication on FastAPI endpoints
- [ ] Use HTTPS for all API communication
- [ ] Encrypt sensitive data at rest (PII, API keys)
- [ ] Set up proper RBAC for bot commands
- [ ] Enable audit logging for all pipeline operations
- [ ] Configure network security groups / firewalls
- [ ] Implement rate limiting on API endpoints
- [ ] Use secret rotation for database credentials
- [ ] Enable SSL/TLS for database connections

---

## 🆘 Troubleshooting Guide

### Problem: Presidio not detecting PII
**Solution**:
```python
# Load larger spaCy model
python -m spacy download en_core_web_lg

# Lower confidence threshold
config = PIIDetectionConfig(confidence_threshold=0.5)
```

### Problem: Celery tasks not executing
**Solution**:
```bash
# Check Redis connection
redis-cli ping

# Check Celery worker logs
celery -A app worker --loglevel=debug

# Verify task routing
celery -A app inspect active
```

### Problem: Soda checks always failing
**Solution**:
```python
# Run with verbose output
scan = Scan()
scan.set_verbose(True)
scan.execute()

# Check actual data
print(scan.scan_results[0].check)
print(scan.scan_results[0].metric_value)
```

### Problem: OpenLineage events not appearing in Marquez
**Solution**:
```bash
# Check Marquez is running
curl http://localhost:5000/api/v1/namespaces

# Verify event structure
print(event.to_json())

# Check Marquez logs
docker logs marquez
```

### Problem: Opsdroid not responding
**Solution**:
```bash
# Check configuration
opsdroid config check

# View logs
opsdroid logs

# Test skill directly
opsdroid test -s atlas_pipeline
```

---

## 📚 Next Steps

1. **Start with one integration** - Don't implement everything at once
2. **Test with sample data** - Use the examples' test data
3. **Monitor performance** - Measure before optimizing
4. **Iterate** - Add integrations as needs grow
5. **Document** - Keep track of your specific configuration

---

## 🔗 Links to Full Examples

- [01_adamiao_presidio_pii_detection.py](./01_adamiao_presidio_pii_detection.py) - PII detection with retry logic
- [02_prefect_openlineage_tracking.py](./02_prefect_openlineage_tracking.py) - Data lineage tracking
- [03_fastapi_celery_pipeline_execution.py](./03_fastapi_celery_pipeline_execution.py) - Async API execution
- [04_soda_core_quality_checks.py](./04_soda_core_quality_checks.py) - Quality validation
- [05_opsdroid_bot_integration.py](./05_opsdroid_bot_integration.py) - Chatbot interface
- [README.md](./README.md) - Detailed documentation

---

**Ready to integrate? Pick an example and start coding! 🚀**
