# Atlas Data Pipeline Platform - API Reference

**Version:** 1.0
**API Version:** v1
**Base URL:** `http://localhost:8000/api/v1`
**Last Updated:** January 2026

Complete API reference for the Atlas Data Pipeline Platform.

## Table of Contents

- [Authentication](#authentication)
- [Pipeline Management](#pipeline-management)
- [Data Quality](#data-quality)
- [PII Detection](#pii-detection)
- [Data Lineage](#data-lineage)
- [Monitoring](#monitoring)
- [Error Handling](#error-handling)

## Authentication

### POST /auth/login

Authenticate user and obtain access token.

**Request**:
```json
{
  "username": "admin@atlas.local",
  "password": "yourpassword"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### POST /auth/refresh

Refresh access token using refresh token.

**Request**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### POST /auth/logout

Invalidate current tokens.

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "message": "Successfully logged out"
}
```

## Pipeline Management

### GET /pipelines

List all available pipelines.

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Number of results (default: 100)
- `status` (string): Filter by status (active|inactive|archived)

**Response**:
```json
{
  "total": 5,
  "items": [
    {
      "pipeline_id": "bronze_to_silver",
      "name": "Bronze to Silver Pipeline",
      "description": "Clean and validate bronze layer data",
      "status": "active",
      "version": "1.0.0",
      "created_at": "2026-01-09T10:00:00Z"
    }
  ]
}
```

### GET /pipelines/{pipeline_id}

Get detailed information about a specific pipeline.

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "pipeline_id": "bronze_to_silver",
  "name": "Bronze to Silver Pipeline",
  "description": "Clean and validate bronze layer data",
  "status": "active",
  "version": "1.0.0",
  "configuration": {
    "batch_size": 1000,
    "max_retries": 3,
    "timeout": 3600
  },
  "steps": [
    {
      "step_id": "pii_detection",
      "name": "PII Detection",
      "order": 1
    },
    {
      "step_id": "data_cleaning",
      "name": "Data Cleaning",
      "order": 2
    }
  ],
  "created_at": "2026-01-09T10:00:00Z",
  "updated_at": "2026-01-09T15:30:00Z"
}
```

### POST /pipelines/execute

Execute a pipeline with provided input data.

**Headers**:
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request**:
```json
{
  "pipeline_id": "bronze_to_silver",
  "input_data": {
    "source_table": "bronze.customers",
    "target_table": "silver.customers"
  },
  "options": {
    "async": true,
    "notify_on_completion": true
  }
}
```

**Response**:
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "pipeline_id": "bronze_to_silver",
  "status": "running",
  "started_at": "2026-01-09T16:00:00Z",
  "estimated_completion": "2026-01-09T16:05:00Z"
}
```

### GET /pipelines/runs

List pipeline execution runs.

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
- `skip` (int): Pagination offset
- `limit` (int): Number of results
- `pipeline_id` (string): Filter by pipeline
- `status` (string): Filter by status (pending|running|completed|failed)
- `from_date` (datetime): Filter runs after this date
- `to_date` (datetime): Filter runs before this date

**Response**:
```json
{
  "total": 150,
  "items": [
    {
      "run_id": "550e8400-e29b-41d4-a716-446655440000",
      "pipeline_id": "bronze_to_silver",
      "status": "completed",
      "started_at": "2026-01-09T16:00:00Z",
      "completed_at": "2026-01-09T16:04:30Z",
      "duration_seconds": 270,
      "records_processed": 10000,
      "records_failed": 5
    }
  ]
}
```

### GET /pipelines/runs/{run_id}

Get detailed information about a specific pipeline run.

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "pipeline_id": "bronze_to_silver",
  "status": "completed",
  "started_at": "2026-01-09T16:00:00Z",
  "completed_at": "2026-01-09T16:04:30Z",
  "duration_seconds": 270,
  "input_params": {
    "source_table": "bronze.customers",
    "target_table": "silver.customers"
  },
  "result_data": {
    "records_processed": 10000,
    "records_failed": 5,
    "pii_detected": 2500,
    "quality_score": 0.98
  },
  "steps": [
    {
      "step_id": "pii_detection",
      "status": "completed",
      "duration_seconds": 45,
      "records_processed": 10000
    }
  ],
  "error_message": null
}
```

### POST /pipelines/runs/{run_id}/cancel

Cancel a running pipeline execution.

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled",
  "cancelled_at": "2026-01-09T16:02:00Z"
}
```

### POST /pipelines/runs/{run_id}/retry

Retry a failed pipeline run.

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "run_id": "660e8400-e29b-41d4-a716-446655440001",
  "original_run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "started_at": "2026-01-09T16:10:00Z"
}
```

## Data Quality

### GET /quality/metrics

Get data quality metrics for a table or pipeline run.

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
- `table_name` (string): Table to check (e.g., "silver.customers")
- `run_id` (string): Specific pipeline run
- `layer` (string): bronze|silver|gold|ai_ready

**Response**:
```json
{
  "table_name": "silver.customers",
  "layer": "silver",
  "measured_at": "2026-01-09T16:05:00Z",
  "overall_score": 0.95,
  "dimensions": {
    "completeness": {
      "score": 0.98,
      "threshold": 0.95,
      "passed": true,
      "details": {
        "total_rows": 10000,
        "complete_rows": 9800
      }
    },
    "validity": {
      "score": 0.92,
      "threshold": 0.90,
      "passed": true,
      "details": {
        "valid_emails": 9200,
        "total_emails": 10000
      }
    },
    "consistency": {
      "score": 0.95,
      "threshold": 0.85,
      "passed": true
    },
    "accuracy": {
      "score": 0.91,
      "threshold": 0.90,
      "passed": true
    },
    "timeliness": {
      "score": 0.99,
      "threshold": 0.95,
      "passed": true,
      "details": {
        "avg_age_hours": 2.5,
        "threshold_hours": 24
      }
    },
    "uniqueness": {
      "score": 0.998,
      "threshold": 0.99,
      "passed": true,
      "details": {
        "duplicate_rows": 20,
        "total_rows": 10000
      }
    }
  }
}
```

### POST /quality/checks/execute

Execute quality checks on a table.

**Headers**:
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request**:
```json
{
  "table_name": "silver.customers",
  "checks": [
    "completeness",
    "validity",
    "uniqueness"
  ]
}
```

**Response**:
```json
{
  "check_id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "running",
  "started_at": "2026-01-09T16:15:00Z"
}
```

### GET /quality/checks/{check_id}

Get results of a quality check execution.

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "check_id": "770e8400-e29b-41d4-a716-446655440002",
  "table_name": "silver.customers",
  "status": "completed",
  "started_at": "2026-01-09T16:15:00Z",
  "completed_at": "2026-01-09T16:15:30Z",
  "overall_passed": true,
  "results": [
    {
      "check_name": "completeness",
      "passed": true,
      "score": 0.98,
      "threshold": 0.95
    }
  ]
}
```

## PII Detection

### POST /pii/analyze

Analyze text or data for PII entities.

**Headers**:
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request**:
```json
{
  "text": "My name is John Doe and my email is john.doe@example.com",
  "language": "en",
  "entities": ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"],
  "score_threshold": 0.35
}
```

**Response**:
```json
{
  "analysis_id": "880e8400-e29b-41d4-a716-446655440003",
  "detected_entities": [
    {
      "entity_type": "PERSON",
      "start": 11,
      "end": 19,
      "score": 0.85,
      "text": "John Doe"
    },
    {
      "entity_type": "EMAIL_ADDRESS",
      "start": 37,
      "end": 58,
      "score": 1.0,
      "text": "john.doe@example.com"
    }
  ],
  "entity_count": 2,
  "analyzed_at": "2026-01-09T16:20:00Z"
}
```

### POST /pii/anonymize

Anonymize detected PII entities in text or data.

**Headers**:
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request**:
```json
{
  "text": "My name is John Doe and my email is john.doe@example.com",
  "anonymization_strategy": {
    "PERSON": "replace",
    "EMAIL_ADDRESS": "mask"
  },
  "language": "en"
}
```

**Response**:
```json
{
  "anonymized_text": "My name is <PERSON> and my email is ***@example.com",
  "entities_anonymized": 2,
  "strategy_applied": {
    "PERSON": "replace",
    "EMAIL_ADDRESS": "mask"
  }
}
```

### POST /pii/batch-analyze

Analyze a batch of records for PII.

**Headers**:
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request**:
```json
{
  "table_name": "bronze.customers",
  "columns": ["name", "email", "phone", "address"],
  "language": "en",
  "async": true
}
```

**Response**:
```json
{
  "job_id": "990e8400-e29b-41d4-a716-446655440004",
  "status": "running",
  "started_at": "2026-01-09T16:25:00Z",
  "estimated_completion": "2026-01-09T16:30:00Z"
}
```

## Data Lineage

### GET /lineage/datasets/{dataset_name}

Get lineage information for a specific dataset.

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "dataset_name": "silver.customers",
  "namespace": "atlas_pipeline",
  "upstream_datasets": [
    {
      "dataset_name": "bronze.customers_raw",
      "namespace": "atlas_pipeline",
      "relationship": "derived_from"
    }
  ],
  "downstream_datasets": [
    {
      "dataset_name": "gold.customer_analytics",
      "namespace": "atlas_pipeline",
      "relationship": "feeds_into"
    }
  ],
  "transformations": [
    {
      "job_name": "bronze_to_silver",
      "run_id": "550e8400-e29b-41d4-a716-446655440000",
      "executed_at": "2026-01-09T16:00:00Z"
    }
  ]
}
```

### GET /lineage/graph

Get full lineage graph.

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
- `namespace` (string): Filter by namespace
- `depth` (int): Graph depth (default: 3)

**Response**:
```json
{
  "nodes": [
    {
      "id": "bronze.customers_raw",
      "type": "dataset",
      "layer": "bronze"
    },
    {
      "id": "silver.customers",
      "type": "dataset",
      "layer": "silver"
    }
  ],
  "edges": [
    {
      "source": "bronze.customers_raw",
      "target": "silver.customers",
      "transformation": "bronze_to_silver",
      "created_at": "2026-01-09T16:00:00Z"
    }
  ]
}
```

### POST /lineage/events

Emit a lineage event.

**Headers**:
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request**:
```json
{
  "event_type": "COMPLETE",
  "event_time": "2026-01-09T16:30:00Z",
  "run": {
    "run_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "job": {
    "namespace": "atlas_pipeline",
    "name": "bronze_to_silver"
  },
  "inputs": [
    {
      "namespace": "atlas",
      "name": "bronze.customers"
    }
  ],
  "outputs": [
    {
      "namespace": "atlas",
      "name": "silver.customers"
    }
  ]
}
```

**Response**:
```json
{
  "event_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "status": "recorded",
  "recorded_at": "2026-01-09T16:30:01Z"
}
```

## Monitoring

### GET /health

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "storage": "connected",
    "celery": "3 workers active"
  },
  "timestamp": "2026-01-09T16:35:00Z"
}
```

### GET /metrics

Prometheus-compatible metrics.

**Response**: Prometheus text format
```
# HELP atlas_pipeline_runs_total Total number of pipeline runs
# TYPE atlas_pipeline_runs_total counter
atlas_pipeline_runs_total{pipeline="bronze_to_silver",status="completed"} 150

# HELP atlas_pipeline_duration_seconds Pipeline execution duration
# TYPE atlas_pipeline_duration_seconds histogram
atlas_pipeline_duration_seconds_bucket{pipeline="bronze_to_silver",le="60"} 120
```

### GET /monitoring/dashboard

Get monitoring dashboard data.

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "overview": {
    "total_pipelines": 5,
    "active_runs": 2,
    "completed_today": 45,
    "failed_today": 1
  },
  "recent_runs": [...],
  "quality_summary": {
    "avg_score": 0.95,
    "failing_tables": []
  },
  "system_health": {
    "cpu_usage": 45.2,
    "memory_usage": 62.8,
    "disk_usage": 38.5
  }
}
```

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "error": {
    "code": "PIPELINE_EXECUTION_FAILED",
    "message": "Pipeline execution failed due to quality check failure",
    "details": {
      "run_id": "550e8400-e29b-41d4-a716-446655440000",
      "failed_step": "quality_validation",
      "reason": "Completeness score 0.89 below threshold 0.95"
    },
    "timestamp": "2026-01-09T16:40:00Z",
    "request_id": "req_bb0e8400e29b41d4"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful request |
| 201 | Created | Resource created |
| 202 | Accepted | Async operation started |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily down |

### Common Error Codes

| Code | Description |
|------|-------------|
| `AUTHENTICATION_FAILED` | Invalid credentials |
| `TOKEN_EXPIRED` | Access token expired |
| `PIPELINE_NOT_FOUND` | Pipeline doesn't exist |
| `RUN_NOT_FOUND` | Pipeline run doesn't exist |
| `PIPELINE_EXECUTION_FAILED` | Pipeline failed during execution |
| `QUALITY_CHECK_FAILED` | Data quality below threshold |
| `PII_DETECTION_FAILED` | PII detection service error |
| `INSUFFICIENT_PERMISSIONS` | User lacks required permissions |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `VALIDATION_ERROR` | Input validation failed |

## Rate Limiting

**Default Limits**:
- Authenticated: 100 requests/minute
- Burst: 200 requests/minute
- Anonymous: 20 requests/minute

**Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1641736800
```

## Pagination

All list endpoints support pagination:

**Query Parameters**:
- `skip`: Offset (default: 0)
- `limit`: Page size (default: 100, max: 1000)

**Response**:
```json
{
  "total": 500,
  "skip": 0,
  "limit": 100,
  "items": [...]
}
```

## Webhooks (Optional)

Configure webhooks to receive notifications:

```json
{
  "webhook_url": "https://your-service.com/webhook",
  "events": [
    "pipeline.started",
    "pipeline.completed",
    "pipeline.failed",
    "quality.check_failed",
    "pii.detected"
  ],
  "secret": "your_webhook_secret"
}
```

---

**Atlas Data Pipeline Platform** - Complete API reference for production use

**Interactive Documentation**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
