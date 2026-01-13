"""
Atlas OpenLineage Integration
==============================

OpenLineage client for data lineage tracking and Marquez integration.

Features:
- Event emission (START, RUNNING, COMPLETE, FAIL, ABORT)
- Dataset lineage tracking (inputs → job → outputs)
- Schema tracking and metadata
- Integration with Marquez backend
- Lineage graph generation

Reference: docs/integration-examples/02_prefect_openlineage_tracking.py
"""

import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4

import httpx
import pandas as pd

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================


@dataclass
class LineageConfig:
    """
    Configuration for OpenLineage/Marquez integration.

    Attributes:
        marquez_url: Marquez backend URL (default: http://localhost:3000)
        namespace: Logical grouping for datasets/jobs (default: atlas_production)
        producer: Event producer identifier (default: atlas_pipeline_v1.0)
    """

    marquez_url: str = "http://localhost:3000"
    namespace: str = "atlas_production"
    producer: str = "atlas_pipeline_v1.0"


# ============================================================================
# OpenLineage Event Models
# ============================================================================


@dataclass
class Run:
    """OpenLineage Run identifier."""

    runId: str


@dataclass
class Job:
    """OpenLineage Job identifier."""

    namespace: str
    name: str
    facets: dict[str, Any] | None = None


@dataclass
class Dataset:
    """OpenLineage Dataset identifier."""

    namespace: str
    name: str
    facets: dict[str, Any] | None = None


@dataclass
class SchemaField:
    """Schema field definition."""

    name: str
    type: str
    description: str | None = None


@dataclass
class SchemaDatasetFacet:
    """Schema facet for dataset."""

    _producer: str
    _schemaURL: str = "https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json"
    fields: list[SchemaField] | None = None


@dataclass
class DataSourceDatasetFacet:
    """Data source facet for dataset."""

    _producer: str
    name: str
    uri: str
    _schemaURL: str = "https://openlineage.io/spec/facets/1-0-0/DatasourceDatasetFacet.json"


@dataclass
class RunEvent:
    """OpenLineage Run Event."""

    eventType: str  # START, RUNNING, COMPLETE, FAIL, ABORT
    eventTime: str  # ISO 8601 timestamp
    run: Run
    job: Job
    inputs: list[Dataset] | None = None
    outputs: list[Dataset] | None = None
    producer: str | None = None


# ============================================================================
# OpenLineage Client
# ============================================================================


class OpenLineageClient:
    """
    OpenLineage client for emitting lineage events to Marquez.

    Handles:
    - Event emission to Marquez API
    - Dataset metadata extraction
    - Schema tracking
    - Lineage graph generation
    """

    def __init__(self, config: LineageConfig):
        """
        Initialize OpenLineage client.

        Args:
            config: LineageConfig with Marquez URL and namespace
        """
        self.config = config
        self.namespace = config.namespace
        self.producer = config.producer
        self.marquez_url = config.marquez_url.rstrip("/")
        self.lineage_endpoint = f"{self.marquez_url}/api/v1/lineage"

        logger.info(
            f"Initialized OpenLineageClient for namespace: {self.namespace}, "
            f"Marquez: {self.marquez_url}"
        )

    def _create_dataset_facets(
        self, df: pd.DataFrame, source_location: str | None = None
    ) -> dict[str, Any]:
        """
        Create dataset facets from DataFrame.

        Generates:
        - Schema facet (column names and types)
        - Data source facet (location)
        - Stats facet (row count, column count, size)

        Args:
            df: Pandas DataFrame
            source_location: Optional source location URI

        Returns:
            Dictionary of facets
        """
        facets = {}

        # Schema facet
        schema_fields = [
            {
                "name": str(col),
                "type": str(df[col].dtype),
                "description": f"Column {col} of type {df[col].dtype}",
            }
            for col in df.columns
        ]

        facets["schema"] = {
            "_producer": self.producer,
            "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json",
            "fields": schema_fields,
        }

        # Data source facet
        if source_location:
            facets["dataSource"] = {
                "_producer": self.producer,
                "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/DatasourceDatasetFacet.json",
                "name": source_location,
                "uri": source_location,
            }

        # Stats facet
        facets["stats"] = {
            "_producer": self.producer,
            "_schemaURL": "custom/stats",
            "rowCount": len(df),
            "columnCount": len(df.columns),
            "sizeBytes": int(df.memory_usage(deep=True).sum()),
        }

        return facets

    def emit_event(self, event: RunEvent) -> bool:
        """
        Emit OpenLineage event to Marquez.

        Args:
            event: RunEvent to emit

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert event to dict
            event_dict = asdict(event)

            # Remove None values
            event_dict = {k: v for k, v in event_dict.items() if v is not None}

            # Send to Marquez
            logger.debug(f"Emitting {event.eventType} event to {self.lineage_endpoint}")

            with httpx.Client(timeout=10.0) as client:
                response = client.post(self.lineage_endpoint, json=event_dict)
                response.raise_for_status()

            logger.info(
                f"{event.eventType} event emitted for job: {event.job.name}, "
                f"run: {event.run.runId}"
            )
            return True

        except httpx.HTTPError as e:
            logger.warning(f"Failed to emit lineage event to Marquez: {e}")
            logger.warning(
                "Continuing without lineage tracking (Marquez may be unavailable)"
            )
            return False
        except Exception as e:
            logger.error(f"Unexpected error emitting lineage event: {e}")
            return False

    def emit_start_event(
        self,
        job_name: str,
        run_id: str,
        inputs: list[dict[str, Any]],
        outputs: list[dict[str, Any]],
        job_metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Emit START event for pipeline job.

        Args:
            job_name: Name of the job (e.g., "csv_to_explore_pipeline")
            run_id: Unique run identifier
            inputs: List of input datasets with name and facets
            outputs: List of output datasets with name and facets
            job_metadata: Optional job metadata (sql, source_code_location, etc.)

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Emitting START event for job: {job_name}, run: {run_id}")

        # Convert inputs to Dataset objects
        input_datasets = [
            Dataset(
                namespace=self.namespace,
                name=inp["name"],
                facets=inp.get("facets", {}),
            )
            for inp in inputs
        ]

        # Convert outputs to Dataset objects
        output_datasets = [
            Dataset(
                namespace=self.namespace,
                name=out["name"],
                facets=out.get("facets", {}),
            )
            for out in outputs
        ]

        # Build job facets
        job_facets = {}
        if job_metadata:
            if "sql" in job_metadata:
                job_facets["sql"] = {
                    "_producer": self.producer,
                    "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SqlJobFacet.json",
                    "query": job_metadata["sql"],
                }
            if "source_code_location" in job_metadata:
                job_facets["sourceCodeLocation"] = {
                    "_producer": self.producer,
                    "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SourceCodeLocationJobFacet.json",
                    "type": "git",
                    "url": job_metadata["source_code_location"],
                }

        # Create and emit event
        event = RunEvent(
            eventType="START",
            eventTime=datetime.utcnow().isoformat() + "Z",
            run=Run(runId=run_id),
            job=Job(namespace=self.namespace, name=job_name, facets=job_facets or None),
            inputs=input_datasets if input_datasets else None,
            outputs=output_datasets if output_datasets else None,
            producer=self.producer,
        )

        return self.emit_event(event)

    def emit_running_event(
        self, job_name: str, run_id: str, progress: dict[str, Any] | None = None
    ) -> bool:
        """
        Emit RUNNING event for in-progress pipeline job.

        Args:
            job_name: Name of the job
            run_id: Unique run identifier
            progress: Optional progress metadata (percent_complete, current_step, etc.)

        Returns:
            True if successful, False otherwise
        """
        logger.debug(f"Emitting RUNNING event for job: {job_name}, run: {run_id}")

        job_facets = {}
        if progress:
            job_facets["progress"] = {
                "_producer": self.producer,
                "_schemaURL": "custom/progress",
                **progress,
            }

        event = RunEvent(
            eventType="RUNNING",
            eventTime=datetime.utcnow().isoformat() + "Z",
            run=Run(runId=run_id),
            job=Job(namespace=self.namespace, name=job_name, facets=job_facets or None),
            producer=self.producer,
        )

        return self.emit_event(event)

    def emit_complete_event(
        self,
        job_name: str,
        run_id: str,
        outputs: list[dict[str, Any]],
        metrics: dict[str, Any] | None = None,
    ) -> bool:
        """
        Emit COMPLETE event for successful pipeline job.

        Args:
            job_name: Name of the job
            run_id: Unique run identifier
            outputs: List of output datasets with name and facets
            metrics: Optional job metrics (rows_processed, duration_seconds, etc.)

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Emitting COMPLETE event for job: {job_name}, run: {run_id}")

        output_datasets = [
            Dataset(
                namespace=self.namespace,
                name=out["name"],
                facets=out.get("facets", {}),
            )
            for out in outputs
        ]

        # Add metrics to job facets
        job_facets = {}
        if metrics:
            job_facets["metrics"] = {
                "_producer": self.producer,
                "_schemaURL": "custom/metrics",
                **metrics,
            }

        event = RunEvent(
            eventType="COMPLETE",
            eventTime=datetime.utcnow().isoformat() + "Z",
            run=Run(runId=run_id),
            job=Job(namespace=self.namespace, name=job_name, facets=job_facets or None),
            outputs=output_datasets if output_datasets else None,
            producer=self.producer,
        )

        return self.emit_event(event)

    def emit_fail_event(
        self, job_name: str, run_id: str, error_message: str
    ) -> bool:
        """
        Emit FAIL event for failed pipeline job.

        Args:
            job_name: Name of the job
            run_id: Unique run identifier
            error_message: Error message or exception details

        Returns:
            True if successful, False otherwise
        """
        logger.error(f"Emitting FAIL event for job: {job_name}, run: {run_id}")

        job_facets = {
            "errorMessage": {
                "_producer": self.producer,
                "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/ErrorMessageRunFacet.json",
                "message": error_message,
                "programmingLanguage": "python",
            }
        }

        event = RunEvent(
            eventType="FAIL",
            eventTime=datetime.utcnow().isoformat() + "Z",
            run=Run(runId=run_id),
            job=Job(namespace=self.namespace, name=job_name, facets=job_facets),
            producer=self.producer,
        )

        return self.emit_event(event)

    def emit_abort_event(self, job_name: str, run_id: str, reason: str) -> bool:
        """
        Emit ABORT event for aborted pipeline job.

        Args:
            job_name: Name of the job
            run_id: Unique run identifier
            reason: Reason for abortion

        Returns:
            True if successful, False otherwise
        """
        logger.warning(f"Emitting ABORT event for job: {job_name}, run: {run_id}")

        job_facets = {
            "abortReason": {
                "_producer": self.producer,
                "_schemaURL": "custom/abortReason",
                "reason": reason,
            }
        }

        event = RunEvent(
            eventType="ABORT",
            eventTime=datetime.utcnow().isoformat() + "Z",
            run=Run(runId=run_id),
            job=Job(namespace=self.namespace, name=job_name, facets=job_facets),
            producer=self.producer,
        )

        return self.emit_event(event)

    def query_lineage_graph(
        self, dataset_name: str, depth: int = 10
    ) -> dict[str, Any] | None:
        """
        Query lineage graph for a dataset from Marquez.

        Args:
            dataset_name: Name of the dataset (e.g., "explore.raw_data")
            depth: How far to traverse the lineage graph

        Returns:
            Lineage graph dict or None if failed
        """
        try:
            url = f"{self.marquez_url}/api/v1/namespaces/{self.namespace}/datasets/{dataset_name}/lineage"

            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params={"depth": depth})
                response.raise_for_status()

            lineage_graph = response.json()
            logger.info(
                f"Retrieved lineage graph for {dataset_name}, "
                f"nodes: {len(lineage_graph.get('graph', []))}"
            )

            return lineage_graph

        except httpx.HTTPError as e:
            logger.warning(f"Failed to query lineage graph from Marquez: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error querying lineage: {e}")
            return None

    def find_downstream_datasets(self, dataset_name: str) -> list[str]:
        """
        Find all downstream datasets affected by changes to given dataset.

        Args:
            dataset_name: Name of the dataset (e.g., "explore.raw_data")

        Returns:
            List of downstream dataset names
        """
        lineage_graph = self.query_lineage_graph(dataset_name)

        if not lineage_graph:
            return []

        downstream = []
        for node in lineage_graph.get("graph", []):
            if node.get("type") == "DATASET" and node.get("name") != dataset_name:
                downstream.append(node["name"])

        logger.info(
            f"Found {len(downstream)} downstream datasets for {dataset_name}"
        )
        return downstream

    def find_upstream_datasets(self, dataset_name: str) -> list[str]:
        """
        Find all upstream datasets that contribute to given dataset.

        Args:
            dataset_name: Name of the dataset (e.g., "navigate.business_metrics")

        Returns:
            List of upstream dataset names
        """
        lineage_graph = self.query_lineage_graph(dataset_name)

        if not lineage_graph:
            return []

        # In lineage graph, upstream datasets have edges pointing to the target
        upstream = []
        for node in lineage_graph.get("graph", []):
            if node.get("type") == "DATASET" and node.get("name") != dataset_name:
                # Check if this node has an edge to our target dataset
                for edge in lineage_graph.get("edges", []):
                    if (
                        edge.get("destination") == dataset_name
                        and edge.get("origin") == node.get("name")
                    ):
                        upstream.append(node["name"])
                        break

        logger.info(f"Found {len(upstream)} upstream datasets for {dataset_name}")
        return upstream


# ============================================================================
# Singleton Instance
# ============================================================================

# Global lineage client instance (initialized on first use)
_lineage_client: OpenLineageClient | None = None


def get_lineage_client() -> OpenLineageClient:
    """
    Get or create global lineage client instance.

    Returns:
        OpenLineageClient instance
    """
    global _lineage_client

    if _lineage_client is None:
        config = LineageConfig()
        _lineage_client = OpenLineageClient(config)

    return _lineage_client
