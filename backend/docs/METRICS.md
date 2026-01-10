# Atlas Data Pipeline Platform - Metrics Documentation

## Overview

The Atlas Data Pipeline Platform exposes comprehensive Prometheus metrics for monitoring pipeline performance, data quality, system health, and business KPIs.

**Metrics Endpoint**: `http://localhost:8000/metrics`

---

## Quick Start

### Viewing Metrics

```bash
# View all metrics
curl http://localhost:8000/metrics

# View specific metric
curl http://localhost:8000/metrics | grep atlas_pipeline_executions_total
```

### Prometheus Configuration

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'atlas-pipeline'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
```

---

## Metric Categories

### 1. API Metrics

**HTTP Request Metrics**

- `atlas_api_http_requests_total` - Total HTTP requests
  - Labels: `method`, `handler`, `status`
- `atlas_api_http_request_duration_seconds` - HTTP request latency
  - Labels: `method`, `handler`, `le` (bucket)
- `atlas_api_http_requests_inprogress` - Active HTTP requests
  - Labels: `method`, `handler`

**Example Queries**:
```promql
# Request rate per endpoint
rate(atlas_api_http_requests_total[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(atlas_api_http_request_duration_seconds_bucket[5m]))

# Error rate
rate(atlas_api_http_requests_total{status=~"5.."}[5m]) /
rate(atlas_api_http_requests_total[5m])
```

---

### 2. Pipeline Metrics

**Execution Metrics**

- `atlas_pipeline_executions_total` - Total pipeline executions
  - Labels: `layer` (bronze/silver/gold), `status`, `pipeline_type`
- `atlas_pipeline_records_processed_total` - Total records processed
  - Labels: `layer`, `pipeline_type`
- `atlas_pipeline_errors_total` - Total pipeline errors
  - Labels: `layer`, `error_type`, `pipeline_type`

**Performance Metrics**

- `atlas_pipeline_duration_seconds` - Pipeline execution duration
  - Labels: `layer`, `pipeline_type`
  - Buckets: 1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600 seconds
- `atlas_pipeline_executions_active` - Active pipeline executions
  - Labels: `layer`, `pipeline_type`

**Example Queries**:
```promql
# Pipeline success rate
rate(atlas_pipeline_executions_total{status="success"}[5m]) /
rate(atlas_pipeline_executions_total[5m])

# Average pipeline duration by layer
avg(atlas_pipeline_duration_seconds) by (layer)

# Records processed per second
rate(atlas_pipeline_records_processed_total[5m])
```

---

### 3. Data Quality Metrics

**Quality Scores**

- `atlas_data_quality_score` - Current quality score (0-1)
  - Labels: `layer`, `dimension`, `dataset`
  - Dimensions: completeness, validity, consistency, accuracy, timeliness, uniqueness

**Quality Checks**

- `atlas_data_quality_checks_total` - Total quality checks
  - Labels: `dimension`, `status`, `severity`
- `atlas_data_quality_violations_total` - Quality violations detected
  - Labels: `dimension`, `severity`, `rule`

**Example Queries**:
```promql
# Average quality score by dimension
avg(atlas_data_quality_score) by (dimension)

# Quality violations by severity
sum(atlas_data_quality_violations_total) by (severity)

# Quality score below threshold
atlas_data_quality_score < 0.8
```

**Alerting Rules**:
```yaml
- alert: LowDataQuality
  expr: atlas_data_quality_score{dimension="completeness"} < 0.95
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Data quality below threshold"
```

---

### 4. PII Detection Metrics

**Detection Metrics**

- `atlas_pii_entities_detected_total` - PII entities detected
  - Labels: `entity_type` (email, ssn, phone, credit_card), `detection_method`
- `atlas_pii_masking_operations_total` - PII masking operations
  - Labels: `entity_type`, `masking_strategy`
- `atlas_pii_detection_duration_seconds` - PII detection latency
  - Labels: `entity_type`

**Example Queries**:
```promql
# PII detection rate by type
rate(atlas_pii_entities_detected_total[5m]) by (entity_type)

# Average PII detection latency
avg(atlas_pii_detection_duration_seconds) by (entity_type)

# Total PII entities by type
sum(atlas_pii_entities_detected_total) by (entity_type)
```

---

### 5. Data Lineage Metrics

**Lineage Tracking**

- `atlas_lineage_events_total` - Lineage events recorded
  - Labels: `event_type`, `layer`
- `atlas_lineage_graph_nodes_total` - Nodes in lineage graph
  - Labels: `node_type`
- `atlas_lineage_graph_edges_total` - Edges in lineage graph
  - Labels: `edge_type`

**Example Queries**:
```promql
# Lineage graph size
atlas_lineage_graph_nodes_total + atlas_lineage_graph_edges_total

# Lineage events per minute
rate(atlas_lineage_events_total[1m])
```

---

### 6. Database Metrics

**Connection Pool**

- `atlas_database_connections_active` - Active connections
  - Labels: `pool_name`
- `atlas_database_connections_idle` - Idle connections
  - Labels: `pool_name`

**Query Performance**

- `atlas_database_queries_total` - Total queries
  - Labels: `operation`, `table`
- `atlas_database_query_duration_seconds` - Query duration
  - Labels: `operation`, `table`

**Example Queries**:
```promql
# Connection pool utilization
atlas_database_connections_active /
(atlas_database_connections_active + atlas_database_connections_idle)

# Slow queries (>100ms)
histogram_quantile(0.99, rate(atlas_database_query_duration_seconds_bucket[5m])) > 0.1

# Query rate by table
rate(atlas_database_queries_total[5m]) by (table)
```

---

### 7. Cache Metrics

**Cache Operations**

- `atlas_cache_operations_total` - Cache operations
  - Labels: `operation` (get, set, delete), `status` (hit, miss)
- `atlas_cache_hit_rate` - Cache hit rate (0-1)
  - Labels: `cache_type`
- `atlas_cache_size_bytes` - Cache size
  - Labels: `cache_type`

**Example Queries**:
```promql
# Cache hit rate
atlas_cache_hit_rate

# Cache operations per second
rate(atlas_cache_operations_total[5m])
```

---

### 8. Task Queue Metrics

**Queue Metrics**

- `atlas_task_queue_size` - Tasks in queue
  - Labels: `queue_name`, `status`
- `atlas_task_executions_total` - Task executions
  - Labels: `task_name`, `status`
- `atlas_task_duration_seconds` - Task duration
  - Labels: `task_name`

**Example Queries**:
```promql
# Queue depth
sum(atlas_task_queue_size) by (queue_name)

# Task success rate
rate(atlas_task_executions_total{status="success"}[5m]) /
rate(atlas_task_executions_total[5m])

# Average task duration
avg(atlas_task_duration_seconds) by (task_name)
```

---

### 9. Storage Metrics

**Storage Usage**

- `atlas_storage_bytes_used` - Storage used
  - Labels: `storage_type`, `layer`
- `atlas_storage_bytes_total` - Total storage
  - Labels: `storage_type`
- `atlas_file_operations_total` - File operations
  - Labels: `operation`, `storage_type`, `status`

**Example Queries**:
```promql
# Storage utilization
atlas_storage_bytes_used / atlas_storage_bytes_total

# Storage by layer
sum(atlas_storage_bytes_used) by (layer)
```

---

### 10. Business Metrics

**Datasets & Records**

- `atlas_datasets_total` - Total datasets
  - Labels: `layer`, `status`
- `atlas_records_total` - Total records
  - Labels: `layer`, `dataset`
- `atlas_data_freshness_seconds` - Data age
  - Labels: `layer`, `dataset`

**Example Queries**:
```promql
# Total datasets by layer
sum(atlas_datasets_total) by (layer)

# Data freshness (hours)
atlas_data_freshness_seconds / 3600

# Records by layer
sum(atlas_records_total) by (layer)
```

---

### 11. System Health Metrics

**Health Status**

- `atlas_system_health_status` - Component health (1=healthy, 0=unhealthy)
  - Labels: `component`
- `atlas_system_uptime_seconds` - System uptime
- `atlas_application_info` - Application info
  - Labels: `version`, `environment`, `name`

**Example Queries**:
```promql
# Unhealthy components
atlas_system_health_status == 0

# System uptime (days)
atlas_system_uptime_seconds / 86400
```

---

## Dashboard Examples

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Atlas Pipeline Overview",
    "panels": [
      {
        "title": "Pipeline Success Rate",
        "targets": [
          {
            "expr": "rate(atlas_pipeline_executions_total{status=\"success\"}[5m]) / rate(atlas_pipeline_executions_total[5m])"
          }
        ]
      },
      {
        "title": "Data Quality Score",
        "targets": [
          {
            "expr": "avg(atlas_data_quality_score) by (dimension)"
          }
        ]
      },
      {
        "title": "PII Detection Rate",
        "targets": [
          {
            "expr": "rate(atlas_pii_entities_detected_total[5m])"
          }
        ]
      }
    ]
  }
}
```

---

## Alerting Rules

### Recommended Alerts

```yaml
groups:
  - name: atlas_pipeline
    rules:
      # Pipeline failures
      - alert: HighPipelineFailureRate
        expr: |
          rate(atlas_pipeline_executions_total{status="error"}[5m]) /
          rate(atlas_pipeline_executions_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High pipeline failure rate"

      # Data quality
      - alert: LowDataQualityScore
        expr: atlas_data_quality_score < 0.8
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Data quality below threshold"

      # Performance
      - alert: SlowPipelineExecution
        expr: |
          histogram_quantile(0.95,
            rate(atlas_pipeline_duration_seconds_bucket[5m])
          ) > 300
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Pipeline execution is slow"

      # System health
      - alert: ComponentUnhealthy
        expr: atlas_system_health_status == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Component {{ $labels.component }} is unhealthy"
```

---

## Integration

### Python Code Examples

```python
from app.core.metrics import (
    record_pipeline_execution,
    record_quality_check,
    record_pii_detection,
)

# Record pipeline execution
record_pipeline_execution(
    layer="silver",
    pipeline_type="pii_detection",
    duration=15.5,
    records=1000,
    status="success"
)

# Record quality check
record_quality_check(
    dimension="completeness",
    score=0.98,
    dataset="customers",
    layer="silver"
)

# Record PII detection
record_pii_detection(
    entity_type="email",
    count=150,
    detection_method="presidio"
)
```

---

## Best Practices

1. **Scrape Interval**: Use 15-30 second intervals for most metrics
2. **Retention**: Keep metrics for at least 30 days
3. **Aggregation**: Use recording rules for frequently queried metrics
4. **Labels**: Keep label cardinality low (<1000 unique combinations)
5. **Dashboards**: Create role-specific dashboards (ops, data, business)

---

## Troubleshooting

### Metrics Not Appearing

1. Check metrics endpoint: `curl http://localhost:8000/metrics`
2. Verify Prometheus is scraping: Check targets page
3. Check application logs for instrumentation errors

### High Cardinality

If metrics have too many labels:
1. Review label usage in code
2. Use label aggregation in Prometheus
3. Implement recording rules

### Performance Impact

Metrics collection overhead:
- **CPU**: <1% typical
- **Memory**: ~10MB per million time series
- **Network**: ~1KB per scrape

---

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [prometheus-fastapi-instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator)
