# Atlas Data Pipeline Platform - Architecture Guide

**Version:** 1.0
**Last Updated:** January 2026

This document provides a comprehensive overview of the Atlas Data Pipeline Platform architecture, design decisions, and technical implementation details.

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Layers](#architecture-layers)
- [Medallion Architecture](#medallion-architecture)
- [Data Flow](#data-flow)
- [Component Details](#component-details)
- [Integration Patterns](#integration-patterns)
- [Security Architecture](#security-architecture)
- [Scalability & Performance](#scalability--performance)

## System Overview

### High-Level Architecture

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

### Design Principles

1. **Separation of Concerns**: Clear layer boundaries with well-defined interfaces
2. **Scalability by Design**: Horizontal scaling for workers and vertical for database
3. **Observability First**: Comprehensive logging, metrics, and lineage tracking
4. **Security by Default**: PII detection, encryption, and access control
5. **Fault Tolerance**: Retry logic, dead letter queues, and error handling

## Architecture Layers

### Layer 1: Presentation

**Purpose**: User interaction and external integrations

**Components**:
- **FastAPI API**: RESTful API with OpenAPI documentation
- **Web Dashboard**: Minimal UI for monitoring and control (optional)
- **Bot Integration**: Opsdroid-based chatbot for pipeline management (optional)

**Key Features**:
- OpenAPI/Swagger documentation
- JWT-based authentication
- Rate limiting and throttling
- CORS configuration
- API versioning

### Layer 2: Orchestration

**Purpose**: Workflow coordination and task distribution

**Components**:
- **Celery**: Distributed task queue for async processing
- **Prefect**: Workflow orchestration for complex pipelines
- **OpenLineage**: Data lineage tracking standard

**Key Features**:
- Async task execution
- Task scheduling and retry logic
- Workflow state management
- Lineage event emission
- Worker health monitoring

### Layer 3: Processing

**Purpose**: Data transformation and validation

**Components**:
- **Pipeline Core**: Bronze → Silver → Gold → AI-Ready transformations
- **Presidio**: PII detection and anonymization
- **Soda Core**: Data quality validation
- **Business Rules**: Custom transformation logic

**Key Features**:
- Medallion architecture implementation
- Automated PII detection and masking
- 6-dimension quality framework
- Custom business rule engine
- Error handling with dead letter queue

### Layer 4: Storage

**Purpose**: Data persistence and caching

**Components**:
- **PostgreSQL**: Metadata, pipeline runs, quality metrics
- **Redis**: Caching and message broker
- **MinIO/S3**: Object storage for data files

**Key Features**:
- ACID transactions for metadata
- High-performance caching
- Scalable object storage
- Backup and recovery
- Data retention policies

## Medallion Architecture

### Overview

The Atlas platform implements the medallion architecture pattern for data refinement:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   SOURCE    │────▶│   BRONZE    │────▶│   SILVER    │────▶│    GOLD     │────▶│  AI READY   │
│             │     │   (Raw)     │     │  (Cleaned)  │     │  (Curated)  │     │  (Optimized)│
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                          │                   │                   │                     │
                          ▼                   ▼                   ▼                     ▼
                    ┌──────────────────────────────────────────────────────┐
                    │              Data Quality Validation                 │
                    │  PII Detection │ Quality Checks │ Lineage Tracking  │
                    └──────────────────────────────────────────────────────┘
```

### Bronze Layer (Explore)

**Purpose**: Raw data ingestion with minimal transformation

**Characteristics**:
- Exact copy of source data
- Preserves original structure and types
- Appends-only (no updates/deletes)
- Includes ingestion metadata

**Implementation**:
- Storage: MinIO bucket `atlas-bronze`
- Database: PostgreSQL schema `atlas_bronze`
- Format: Parquet or CSV
- Retention: 90 days

**Metadata Captured**:
```python
{
    "source_system": "crm",
    "ingestion_timestamp": "2026-01-09T10:30:00Z",
    "source_file": "customers_2026-01-09.csv",
    "record_count": 10000,
    "checksum": "abc123...",
    "schema_version": "1.0"
}
```

### Silver Layer (Chart)

**Purpose**: Cleaned, validated, and standardized data

**Transformations**:
- Data type standardization
- PII detection and anonymization
- Data quality validation
- Deduplication
- Schema enforcement

**Implementation**:
- Storage: MinIO bucket `atlas-silver`
- Database: PostgreSQL schema `atlas_silver`
- Format: Parquet (optimized)
- Retention: 365 days

**Quality Checks**:
```yaml
# Soda Core checks
checks:
  - completeness: 95%
  - validity: 90%
  - consistency: 85%
  - accuracy: 90%
  - timeliness: 95%
  - uniqueness: 99%
```

### Gold Layer (Navigate)

**Purpose**: Business-ready, aggregated data

**Transformations**:
- Business logic application
- Aggregations and calculations
- Dimensional modeling
- Performance optimization
- Access control

**Implementation**:
- Storage: MinIO bucket `atlas-gold`
- Database: PostgreSQL schema `atlas_gold`
- Format: Parquet (partitioned)
- Retention: 730 days (2 years)

**Features**:
- Star schema / snowflake schema
- Pre-calculated metrics
- Role-based access control
- Optimized for analytics

### AI-Ready Layer (Optimize)

**Purpose**: ML-optimized datasets for AI/ML workflows

**Transformations**:
- Feature engineering
- Normalization/standardization
- Train/test/validation splits
- Data augmentation (if needed)
- Format optimization

**Implementation**:
- Storage: MinIO bucket `atlas-ai-ready`
- Database: PostgreSQL schema `atlas_ai_ready`
- Format: Parquet, TFRecord, or Arrow
- Retention: 365 days

**Features**:
- Feature store compatible
- Version control for datasets
- Reproducible transformations
- ML framework compatibility

## Data Flow

### End-to-End Pipeline Flow

```
1. INGESTION
   Source System ──▶ Bronze Layer
   - API pull / File upload / Database sync
   - Raw data stored as-is
   - Metadata captured

2. CLEANING
   Bronze ──▶ Silver Layer
   - PII Detection (Presidio)
   - Data type standardization
   - Quality validation (Soda Core)
   - Schema enforcement
   - Deduplication

3. CURATION
   Silver ──▶ Gold Layer
   - Business rule application
   - Aggregations and calculations
   - Dimensional modeling
   - Access control application

4. OPTIMIZATION
   Gold ──▶ AI-Ready Layer
   - Feature engineering
   - ML-specific transformations
   - Format optimization
   - Version control

5. CONSUMPTION
   AI-Ready ──▶ ML Models / Analytics
   - Model training
   - Inference
   - Analytics dashboards
   - Reporting
```

### Typical Pipeline Execution

```python
# Simplified pipeline flow
async def execute_pipeline(source_data: DataFrame):
    # 1. Bronze: Ingest raw data
    bronze_df = await ingest_to_bronze(source_data)

    # 2. Detect and anonymize PII
    pii_results = await detect_pii(bronze_df)
    anonymized_df = await anonymize_pii(bronze_df, pii_results)

    # 3. Silver: Clean and validate
    cleaned_df = await clean_data(anonymized_df)
    quality_results = await validate_quality(cleaned_df)

    if not quality_results.passed:
        await send_to_dlq(cleaned_df, quality_results)
        raise QualityCheckFailure()

    silver_df = await write_to_silver(cleaned_df)

    # 4. Gold: Apply business rules
    curated_df = await apply_business_rules(silver_df)
    gold_df = await write_to_gold(curated_df)

    # 5. AI-Ready: Optimize for ML
    ml_df = await engineer_features(gold_df)
    ai_ready_df = await write_to_ai_ready(ml_df)

    # 6. Track lineage
    await emit_lineage_event(
        inputs=[bronze_df],
        outputs=[ai_ready_df],
        transformation="full_pipeline"
    )

    return ai_ready_df
```

## Component Details

### FastAPI Backend

**Technology**: FastAPI 0.109+, Python 3.11+

**Structure**:
```
app/
├── api/             # API routes
│   └── v1/
│       ├── auth.py
│       ├── pipelines.py
│       ├── quality.py
│       └── lineage.py
├── core/            # Core configuration
│   ├── config.py
│   ├── security.py
│   └── database.py
├── models.py        # Database models
├── schemas/         # Pydantic schemas
├── crud/            # Database operations
└── main.py          # Application entry point
```

**Key Features**:
- Async/await for high concurrency
- Dependency injection
- Background tasks
- WebSocket support
- Middleware for logging, CORS, auth

### Celery Workers

**Configuration**:
```python
# Celery settings
broker_url = "redis://localhost:6379/1"
result_backend = "redis://localhost:6379/2"
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "UTC"
enable_utc = True

# Task routing
task_routes = {
    "app.tasks.pipeline.*": {"queue": "pipeline"},
    "app.tasks.pii.*": {"queue": "pii"},
    "app.tasks.quality.*": {"queue": "quality"},
}

# Performance tuning
worker_prefetch_multiplier = 4
worker_max_tasks_per_child = 1000
task_time_limit = 3600  # 1 hour
task_soft_time_limit = 3300  # 55 minutes
```

**Task Types**:
- `pipeline.*`: Data transformation tasks
- `pii.*`: PII detection and anonymization
- `quality.*`: Data quality validation
- `lineage.*`: Lineage tracking

### Presidio Integration

**Components**:
- **Analyzer**: Detects PII entities in text
- **Anonymizer**: Applies anonymization strategies

**Supported PII Types**:
- Personal: NAME, EMAIL, PHONE, SSN
- Financial: CREDIT_CARD, IBAN, CRYPTO
- Location: ADDRESS, GPS_COORDINATES
- Identity: PASSPORT, DRIVER_LICENSE
- Custom: Domain-specific patterns

**Anonymization Strategies**:
```python
{
    "replace": "Replace with placeholder",
    "redact": "Remove completely",
    "mask": "Show only last 4 characters",
    "hash": "One-way hash",
    "encrypt": "Reversible encryption"
}
```

### Soda Core Integration

**Quality Dimensions**:

1. **Completeness**: No missing values where required
2. **Validity**: Data conforms to defined formats
3. **Consistency**: Data relationships are maintained
4. **Accuracy**: Data matches reality
5. **Timeliness**: Data is current and fresh
6. **Uniqueness**: No duplicates where unique expected

**Check Example**:
```yaml
# soda_checks/customer_silver.yml
checks for customer_silver:
  - row_count > 100
  - missing_count(email) = 0
  - invalid_count(email) = 0
  - duplicate_count(customer_id) = 0
  - freshness(updated_at) < 1d
  - avg(age) between 18 and 120
```

### OpenLineage Integration

**Event Types**:
- `START`: Pipeline execution begins
- `RUNNING`: In-progress updates
- `COMPLETE`: Successful completion
- `FAIL`: Execution failed
- `ABORT`: Manually stopped

**Event Structure**:
```json
{
  "eventType": "COMPLETE",
  "eventTime": "2026-01-09T10:30:00.000Z",
  "run": {
    "runId": "550e8400-e29b-41d4-a716-446655440000"
  },
  "job": {
    "namespace": "atlas_pipeline",
    "name": "bronze_to_silver"
  },
  "inputs": [{
    "namespace": "atlas",
    "name": "bronze.customers"
  }],
  "outputs": [{
    "namespace": "atlas",
    "name": "silver.customers"
  }]
}
```

## Integration Patterns

### Retry Pattern (adamiao)

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
async def resilient_operation():
    # Your operation here
    pass
```

### Circuit Breaker Pattern

```python
from pybreaker import CircuitBreaker

db_breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=60,
    reset_timeout=120
)

@db_breaker
async def db_operation():
    # Database operation
    pass
```

### Event-Driven Pattern

```python
# Emit events for pipeline lifecycle
await event_bus.emit("pipeline.started", {
    "run_id": run_id,
    "pipeline_name": "bronze_to_silver"
})

await event_bus.emit("pipeline.completed", {
    "run_id": run_id,
    "records_processed": 10000
})
```

## Security Architecture

### Authentication & Authorization

**Authentication**:
- JWT tokens (access + refresh)
- Token expiry: 60 minutes (access), 7 days (refresh)
- Secure token storage
- Token revocation support

**Authorization**:
- Role-based access control (RBAC)
- Resource-level permissions
- API key support for service accounts

**Roles**:
- `admin`: Full system access
- `data_engineer`: Pipeline management
- `data_analyst`: Read-only access to Gold/AI-Ready
- `ml_engineer`: Access to AI-Ready layer
- `viewer`: Read-only dashboard access

### Data Security

**At Rest**:
- PostgreSQL: Encrypted tablespaces
- MinIO: Server-side encryption (SSE)
- Redis: RDB encryption
- Secrets: Encrypted with Fernet

**In Transit**:
- TLS 1.3 for all external connections
- mTLS for inter-service communication
- Encrypted message queue

**PII Handling**:
- Automatic detection with Presidio
- Configurable anonymization
- Audit logging for PII access
- Consent management

### Network Security

```
┌────────────────────────────────────┐
│         External Network           │
│  (Internet / VPN)                  │
└───────────────┬────────────────────┘
                │
         ┌──────▼──────┐
         │  Firewall   │
         │  (WAF)      │
         └──────┬──────┘
                │
┌───────────────▼────────────────────┐
│       DMZ Network                  │
│  ┌──────┐  ┌──────┐                │
│  │ API  │  │  UI  │                │
│  └──────┘  └──────┘                │
└───────────────┬────────────────────┘
                │
┌───────────────▼────────────────────┐
│     Internal Network               │
│  ┌────┐ ┌─────┐ ┌──────┐           │
│  │ DB │ │Redis│ │MinIO │           │
│  └────┘ └─────┘ └──────┘           │
└────────────────────────────────────┘
```

## Scalability & Performance

### Horizontal Scaling

**Celery Workers**:
- Scale workers per queue type
- Auto-scaling based on queue depth
- Worker specialization (CPU vs I/O bound)

```bash
# Scale pipeline workers
docker-compose up -d --scale worker-pipeline=5

# Scale PII workers
docker-compose up -d --scale worker-pii=3
```

**API Instances**:
- Stateless design enables horizontal scaling
- Load balancer (nginx/HAProxy)
- Session affinity not required

### Vertical Scaling

**Database**:
- Connection pooling (20-50 connections)
- Read replicas for analytics queries
- Partitioning for large tables

**Redis**:
- Increase memory allocation
- Redis Cluster for distribution
- Separate instances per use case

### Performance Optimization

**Database**:
- Indexes on frequently queried columns
- Materialized views for analytics
- Query optimization and EXPLAIN analysis
- Connection pooling

**Caching Strategy**:
```python
# 3-tier caching
1. Application cache (in-memory)
2. Redis cache (distributed)
3. Database query cache
```

**Batch Processing**:
- Process data in configurable batch sizes (default: 1000)
- Parallel processing with worker pool
- Streaming for large datasets

### Monitoring & Observability

**Metrics**:
- Prometheus metrics export
- Custom business metrics
- Performance counters
- Resource utilization

**Logging**:
```python
{
    "timestamp": "2026-01-09T10:30:00Z",
    "level": "INFO",
    "service": "atlas-api",
    "trace_id": "abc123",
    "user_id": "user@example.com",
    "message": "Pipeline completed successfully",
    "duration_ms": 1250,
    "records_processed": 10000
}
```

**Tracing**:
- Distributed tracing with OpenTelemetry
- End-to-end request tracking
- Performance bottleneck identification

**Alerting**:
- Pipeline failures
- Quality check failures
- PII detection anomalies
- Performance degradation
- Resource exhaustion

---

**Atlas Data Pipeline Platform** - Scalable, secure, and observable data infrastructure
