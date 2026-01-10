"""
Prometheus Metrics Configuration for Atlas Data Pipeline Platform

This module provides comprehensive metrics collection for:
- API request/response metrics
- Pipeline execution metrics
- Data quality metrics
- PII detection metrics
- System health metrics
"""

from prometheus_client import Counter, Gauge, Histogram, Info
from prometheus_fastapi_instrumentator import Instrumentator, metrics

# ============================================================================
# FastAPI Instrumentator Configuration
# ============================================================================

def create_instrumentator() -> Instrumentator:
    """
    Create and configure Prometheus instrumentator for FastAPI.

    Includes:
    - Default HTTP metrics (requests, duration, response size)
    - Custom business metrics
    - Error tracking
    - Performance monitoring
    """
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=[
            "/metrics",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ],
        env_var_name="ENABLE_METRICS",
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True,
    )

    # Add default metrics
    instrumentator.add(
        metrics.default(
            metric_namespace="atlas",
            metric_subsystem="api",
        )
    )

    # Add request/response metrics
    instrumentator.add(
        metrics.requests(
            metric_namespace="atlas",
            metric_subsystem="api",
        )
    )

    # Add latency metrics with custom buckets
    instrumentator.add(
        metrics.latency(
            buckets=(
                0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5,
                0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 30.0, 60.0
            ),
            metric_namespace="atlas",
            metric_subsystem="api",
        )
    )

    return instrumentator


# ============================================================================
# Custom Application Metrics
# ============================================================================

# Application info
application_info = Info(
    "atlas_application",
    "Atlas Data Pipeline Platform application information"
)

# ============================================================================
# Pipeline Metrics
# ============================================================================

# Pipeline execution counters
pipeline_executions_total = Counter(
    "atlas_pipeline_executions_total",
    "Total number of pipeline executions",
    ["layer", "status", "pipeline_type"]
)

pipeline_records_processed = Counter(
    "atlas_pipeline_records_processed_total",
    "Total number of records processed",
    ["layer", "pipeline_type"]
)

pipeline_errors_total = Counter(
    "atlas_pipeline_errors_total",
    "Total number of pipeline errors",
    ["layer", "error_type", "pipeline_type"]
)

# Pipeline execution duration
pipeline_duration_seconds = Histogram(
    "atlas_pipeline_duration_seconds",
    "Pipeline execution duration in seconds",
    ["layer", "pipeline_type"],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600)
)

# Active pipeline executions
pipeline_executions_active = Gauge(
    "atlas_pipeline_executions_active",
    "Number of currently active pipeline executions",
    ["layer", "pipeline_type"]
)

# ============================================================================
# Data Quality Metrics
# ============================================================================

# Quality score gauge
data_quality_score = Gauge(
    "atlas_data_quality_score",
    "Current data quality score (0-1)",
    ["layer", "dimension", "dataset"]
)

# Quality check results
data_quality_checks_total = Counter(
    "atlas_data_quality_checks_total",
    "Total number of quality checks performed",
    ["dimension", "status", "severity"]
)

# Quality violations
data_quality_violations_total = Counter(
    "atlas_data_quality_violations_total",
    "Total number of quality violations detected",
    ["dimension", "severity", "rule"]
)

# ============================================================================
# PII Detection Metrics
# ============================================================================

# PII entities detected
pii_entities_detected_total = Counter(
    "atlas_pii_entities_detected_total",
    "Total number of PII entities detected",
    ["entity_type", "detection_method"]
)

# PII masking operations
pii_masking_operations_total = Counter(
    "atlas_pii_masking_operations_total",
    "Total number of PII masking operations",
    ["entity_type", "masking_strategy"]
)

# PII detection latency
pii_detection_duration_seconds = Histogram(
    "atlas_pii_detection_duration_seconds",
    "PII detection duration in seconds",
    ["entity_type"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

# ============================================================================
# Data Lineage Metrics
# ============================================================================

# Lineage events recorded
lineage_events_total = Counter(
    "atlas_lineage_events_total",
    "Total number of lineage events recorded",
    ["event_type", "layer"]
)

# Lineage graph nodes
lineage_graph_nodes = Gauge(
    "atlas_lineage_graph_nodes_total",
    "Total number of nodes in lineage graph",
    ["node_type"]
)

# Lineage graph edges
lineage_graph_edges = Gauge(
    "atlas_lineage_graph_edges_total",
    "Total number of edges in lineage graph",
    ["edge_type"]
)

# ============================================================================
# Database Metrics
# ============================================================================

# Database connection pool
database_connections_active = Gauge(
    "atlas_database_connections_active",
    "Number of active database connections",
    ["pool_name"]
)

database_connections_idle = Gauge(
    "atlas_database_connections_idle",
    "Number of idle database connections",
    ["pool_name"]
)

# Database query metrics
database_queries_total = Counter(
    "atlas_database_queries_total",
    "Total number of database queries",
    ["operation", "table"]
)

database_query_duration_seconds = Histogram(
    "atlas_database_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

# ============================================================================
# Cache Metrics
# ============================================================================

# Cache operations
cache_operations_total = Counter(
    "atlas_cache_operations_total",
    "Total number of cache operations",
    ["operation", "status"]
)

# Cache hit rate
cache_hit_rate = Gauge(
    "atlas_cache_hit_rate",
    "Cache hit rate (0-1)",
    ["cache_type"]
)

# Cache size
cache_size_bytes = Gauge(
    "atlas_cache_size_bytes",
    "Cache size in bytes",
    ["cache_type"]
)

# ============================================================================
# Task Queue Metrics
# ============================================================================

# Task queue size
task_queue_size = Gauge(
    "atlas_task_queue_size",
    "Number of tasks in queue",
    ["queue_name", "status"]
)

# Task execution metrics
task_executions_total = Counter(
    "atlas_task_executions_total",
    "Total number of task executions",
    ["task_name", "status"]
)

task_duration_seconds = Histogram(
    "atlas_task_duration_seconds",
    "Task execution duration in seconds",
    ["task_name"],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600)
)

# ============================================================================
# Storage Metrics
# ============================================================================

# Storage usage
storage_bytes_used = Gauge(
    "atlas_storage_bytes_used",
    "Storage space used in bytes",
    ["storage_type", "layer"]
)

storage_bytes_total = Gauge(
    "atlas_storage_bytes_total",
    "Total storage space in bytes",
    ["storage_type"]
)

# File operations
file_operations_total = Counter(
    "atlas_file_operations_total",
    "Total number of file operations",
    ["operation", "storage_type", "status"]
)

# ============================================================================
# Business Metrics
# ============================================================================

# Total datasets
datasets_total = Gauge(
    "atlas_datasets_total",
    "Total number of datasets",
    ["layer", "status"]
)

# Total records
records_total = Gauge(
    "atlas_records_total",
    "Total number of records",
    ["layer", "dataset"]
)

# Data freshness
data_freshness_seconds = Gauge(
    "atlas_data_freshness_seconds",
    "Age of most recent data in seconds",
    ["layer", "dataset"]
)

# ============================================================================
# System Health Metrics
# ============================================================================

# System health status
system_health_status = Gauge(
    "atlas_system_health_status",
    "System health status (1=healthy, 0=unhealthy)",
    ["component"]
)

# Uptime
system_uptime_seconds = Gauge(
    "atlas_system_uptime_seconds",
    "System uptime in seconds"
)

# ============================================================================
# Helper Functions
# ============================================================================

def initialize_application_info(version: str, environment: str) -> None:
    """Initialize application information metrics."""
    application_info.info({
        "version": version,
        "environment": environment,
        "name": "Atlas Data Pipeline Platform",
    })


def record_pipeline_execution(
    layer: str,
    pipeline_type: str,
    duration: float,
    records: int,
    status: str = "success"
) -> None:
    """
    Record metrics for a pipeline execution.

    Args:
        layer: Pipeline layer (bronze, silver, gold)
        pipeline_type: Type of pipeline
        duration: Execution duration in seconds
        records: Number of records processed
        status: Execution status (success, error, timeout)
    """
    pipeline_executions_total.labels(
        layer=layer,
        status=status,
        pipeline_type=pipeline_type
    ).inc()

    pipeline_records_processed.labels(
        layer=layer,
        pipeline_type=pipeline_type
    ).inc(records)

    pipeline_duration_seconds.labels(
        layer=layer,
        pipeline_type=pipeline_type
    ).observe(duration)


def record_quality_check(
    dimension: str,
    score: float,
    dataset: str,
    layer: str = "silver"
) -> None:
    """
    Record data quality check metrics.

    Args:
        dimension: Quality dimension (completeness, validity, etc.)
        score: Quality score (0-1)
        dataset: Dataset name
        layer: Data layer
    """
    data_quality_score.labels(
        layer=layer,
        dimension=dimension,
        dataset=dataset
    ).set(score)


def record_pii_detection(
    entity_type: str,
    count: int,
    detection_method: str = "presidio"
) -> None:
    """
    Record PII detection metrics.

    Args:
        entity_type: Type of PII entity (email, ssn, etc.)
        count: Number of entities detected
        detection_method: Detection method used
    """
    pii_entities_detected_total.labels(
        entity_type=entity_type,
        detection_method=detection_method
    ).inc(count)
