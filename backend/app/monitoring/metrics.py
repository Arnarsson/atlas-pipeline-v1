"""Prometheus metrics for Atlas Data Pipeline Platform."""

import time
from typing import Callable

from fastapi import Request, Response
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
)
from starlette.middleware.base import BaseHTTPMiddleware


# Create a custom registry
registry = CollectorRegistry()

# ============================================================================
# HTTP Metrics
# ============================================================================

http_requests_total = Counter(
    "atlas_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=registry
)

http_request_duration_seconds = Histogram(
    "atlas_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=registry
)

http_requests_in_progress = Gauge(
    "atlas_http_requests_in_progress",
    "HTTP requests currently in progress",
    ["method", "endpoint"],
    registry=registry
)

# ============================================================================
# Pipeline Metrics
# ============================================================================

pipeline_runs_total = Counter(
    "atlas_pipeline_runs_total",
    "Total pipeline runs",
    ["status"],
    registry=registry
)

pipeline_run_duration_seconds = Histogram(
    "atlas_pipeline_run_duration_seconds",
    "Pipeline run duration in seconds",
    ["dataset_name"],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600),
    registry=registry
)

pipeline_runs_active = Gauge(
    "atlas_pipeline_runs_active",
    "Number of currently active pipeline runs",
    registry=registry
)

# ============================================================================
# Data Quality Metrics
# ============================================================================

quality_score = Gauge(
    "atlas_quality_score",
    "Data quality score (0-1)",
    ["dataset_name", "dimension"],
    registry=registry
)

quality_checks_total = Counter(
    "atlas_quality_checks_total",
    "Total quality checks performed",
    ["dimension", "status"],
    registry=registry
)

# ============================================================================
# PII Detection Metrics
# ============================================================================

pii_detections_total = Counter(
    "atlas_pii_detections_total",
    "Total PII detections",
    ["pii_type", "confidence_level"],
    registry=registry
)

pii_columns_detected = Gauge(
    "atlas_pii_columns_detected",
    "Number of columns with PII detected",
    ["dataset_name"],
    registry=registry
)

# ============================================================================
# Connector Metrics
# ============================================================================

connector_syncs_total = Counter(
    "atlas_connector_syncs_total",
    "Total connector sync operations",
    ["connector_type", "source_name", "status"],
    registry=registry
)

connector_sync_duration_seconds = Histogram(
    "atlas_connector_sync_duration_seconds",
    "Connector sync duration in seconds",
    ["connector_type", "source_name"],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600),
    registry=registry
)

connector_records_synced = Counter(
    "atlas_connector_records_synced",
    "Total records synced from connectors",
    ["connector_type", "source_name"],
    registry=registry
)

connector_active = Gauge(
    "atlas_connector_active",
    "Number of active connectors",
    ["connector_type"],
    registry=registry
)

# ============================================================================
# Database Metrics
# ============================================================================

database_connections_active = Gauge(
    "atlas_database_connections_active",
    "Number of active database connections",
    ["pool"],
    registry=registry
)

database_query_duration_seconds = Histogram(
    "atlas_database_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
    registry=registry
)

# ============================================================================
# GDPR Metrics
# ============================================================================

gdpr_requests_total = Counter(
    "atlas_gdpr_requests_total",
    "Total GDPR requests processed",
    ["request_type", "status"],
    registry=registry
)

gdpr_requests_pending = Gauge(
    "atlas_gdpr_requests_pending",
    "Number of pending GDPR requests",
    ["request_type"],
    registry=registry
)

# ============================================================================
# Cache Metrics
# ============================================================================

cache_hits_total = Counter(
    "atlas_cache_hits_total",
    "Total cache hits",
    ["cache_name"],
    registry=registry
)

cache_misses_total = Counter(
    "atlas_cache_misses_total",
    "Total cache misses",
    ["cache_name"],
    registry=registry
)

cache_size_bytes = Gauge(
    "atlas_cache_size_bytes",
    "Cache size in bytes",
    ["cache_name"],
    registry=registry
)

# ============================================================================
# Feature Store Metrics
# ============================================================================

feature_group_versions = Gauge(
    "atlas_feature_group_versions",
    "Number of versions for each feature group",
    ["feature_group"],
    registry=registry
)

feature_exports_total = Counter(
    "atlas_feature_exports_total",
    "Total feature exports",
    ["format", "status"],
    registry=registry
)

# ============================================================================
# System Metrics
# ============================================================================

system_errors_total = Counter(
    "atlas_system_errors_total",
    "Total system errors",
    ["error_type", "component"],
    registry=registry
)

tasks_queued = Gauge(
    "atlas_tasks_queued",
    "Number of tasks in queue",
    ["queue_name"],
    registry=registry
)


# ============================================================================
# Middleware for automatic HTTP metrics
# ============================================================================

class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically collect HTTP metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        # Extract endpoint pattern (remove path params)
        endpoint = request.url.path
        method = request.method

        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        # Track request duration
        start_time = time.time()
        status = 500  # Default to error status

        try:
            response = await call_next(request)
            status = response.status_code
            return response

        except Exception as e:
            # Track errors
            system_errors_total.labels(
                error_type=type(e).__name__,
                component="http_middleware"
            ).inc()
            raise

        finally:
            # Record metrics
            duration = time.time() - start_time

            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()

            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            http_requests_in_progress.labels(
                method=method,
                endpoint=endpoint
            ).dec()


def metrics_middleware():
    """Get the Prometheus middleware instance."""
    return PrometheusMiddleware


def get_metrics() -> bytes:
    """Get current metrics in Prometheus format.

    Returns:
        Metrics data in Prometheus exposition format
    """
    return generate_latest(registry)


def get_metrics_content_type() -> str:
    """Get the content type for Prometheus metrics.

    Returns:
        Content type string
    """
    return CONTENT_TYPE_LATEST
