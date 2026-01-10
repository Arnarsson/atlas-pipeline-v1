"""
Atlas Pipeline Integration: Prefect + OpenLineage/Marquez Data Lineage
=======================================================================

This example shows how to integrate:
1. Prefect for workflow orchestration
2. OpenLineage for standardized lineage tracking
3. Marquez as lineage backend/UI

WHY THIS INTEGRATION:
- Prefect provides modern workflow orchestration (tasks, flows, scheduling)
- OpenLineage is the standard for data lineage (backed by Linux Foundation)
- Marquez gives visual lineage graphs and impact analysis
- Enables full Bronze -> Silver -> Gold lineage tracking

DEPENDENCIES:
pip install prefect openlineage-python openlineage-sql requests pandas
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import pandas as pd

# Prefect for orchestration
from prefect import flow, task, get_run_logger
from prefect.context import get_run_context

# OpenLineage for standardized lineage events
from openlineage.client import OpenLineageClient
from openlineage.client.run import (
    RunEvent,
    RunState,
    Run,
    Job,
    Dataset,
    DatasetFacet,
    InputDataset,
    OutputDataset
)
from openlineage.client.facet import (
    SchemaDatasetFacet,
    SchemaField,
    DataSourceDatasetFacet,
    SqlJobFacet,
    SourceCodeLocationJobFacet
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class LineageConfig:
    """
    WHY: Configuration for OpenLineage/Marquez integration
    - marquez_url: Where lineage events are sent
    - namespace: Logical grouping (e.g., 'atlas_production')
    - producer: Who generated the event (e.g., 'atlas_pipeline_v1')
    """
    marquez_url: str = "http://localhost:5000"
    namespace: str = "atlas_production"
    producer: str = "atlas_pipeline_v1.0"


# ============================================================================
# OpenLineage Client Wrapper
# ============================================================================

class LineageTracker:
    """
    WHY: Wrapper around OpenLineage client for easier lineage tracking
    - Automatically generates events with proper structure
    - Handles START, COMPLETE, FAIL events
    - Captures dataset schemas and metadata
    """

    def __init__(self, config: LineageConfig):
        self.config = config
        # WHY: OpenLineageClient sends events to Marquez backend
        self.client = OpenLineageClient(url=f"{config.marquez_url}/api/v1/lineage")
        self.namespace = config.namespace
        self.producer = config.producer

        logger.info(f"Initialized LineageTracker for namespace: {self.namespace}")

    def _create_dataset_facets(
        self,
        df: pd.DataFrame,
        source_location: Optional[str] = None
    ) -> Dict[str, DatasetFacet]:
        """
        WHY: Dataset facets provide rich metadata about datasets
        - Schema: Column names and types
        - DataSource: Where the data came from
        - Custom facets: Size, row count, quality metrics
        """
        facets = {}

        # Schema facet
        # WHY: Tracks column-level lineage and schema evolution
        schema_fields = [
            SchemaField(
                name=str(col),
                type=str(df[col].dtype),
                description=f"Column {col} of type {df[col].dtype}"
            )
            for col in df.columns
        ]
        facets["schema"] = SchemaDatasetFacet(fields=schema_fields)

        # DataSource facet
        # WHY: Tracks original source location (file, database, API)
        if source_location:
            facets["dataSource"] = DataSourceDatasetFacet(
                name=source_location,
                uri=source_location
            )

        # Custom facet for row count
        # WHY: Track data volume for impact analysis
        facets["stats"] = {
            "_producer": self.producer,
            "_schemaURL": "custom/stats",
            "rowCount": len(df),
            "columnCount": len(df.columns),
            "sizeBytes": df.memory_usage(deep=True).sum()
        }

        return facets

    def emit_start_event(
        self,
        job_name: str,
        run_id: str,
        inputs: List[Dict[str, Any]],
        outputs: List[Dict[str, Any]],
        job_metadata: Optional[Dict] = None
    ):
        """
        WHY: START event marks beginning of data transformation
        - Establishes lineage graph edges (inputs -> job -> outputs)
        - Captures job metadata (SQL query, source code location)
        - Enables real-time monitoring in Marquez
        """
        logger.info(f"Emitting START event for job: {job_name}")

        # WHY: Convert input/output dicts to OpenLineage Dataset objects
        input_datasets = [
            InputDataset(
                namespace=self.namespace,
                name=inp["name"],
                facets=inp.get("facets", {})
            )
            for inp in inputs
        ]

        output_datasets = [
            OutputDataset(
                namespace=self.namespace,
                name=out["name"],
                facets=out.get("facets", {})
            )
            for out in outputs
        ]

        # Build job facets
        # WHY: Job facets capture HOW the transformation happens
        job_facets = {}
        if job_metadata:
            if "sql" in job_metadata:
                job_facets["sql"] = SqlJobFacet(query=job_metadata["sql"])
            if "source_code_location" in job_metadata:
                job_facets["sourceCodeLocation"] = SourceCodeLocationJobFacet(
                    type="git",
                    url=job_metadata["source_code_location"]
                )

        # Create and emit event
        event = RunEvent(
            eventType=RunState.START,
            eventTime=datetime.utcnow().isoformat(),
            run=Run(runId=run_id),
            job=Job(
                namespace=self.namespace,
                name=job_name,
                facets=job_facets
            ),
            inputs=input_datasets,
            outputs=output_datasets,
            producer=self.producer
        )

        self.client.emit(event)
        logger.info(f"START event emitted for run: {run_id}")

    def emit_complete_event(
        self,
        job_name: str,
        run_id: str,
        outputs: List[Dict[str, Any]],
        metrics: Optional[Dict] = None
    ):
        """
        WHY: COMPLETE event marks successful transformation
        - Updates output dataset metadata with final stats
        - Records performance metrics
        - Marks lineage edge as validated
        """
        logger.info(f"Emitting COMPLETE event for job: {job_name}")

        output_datasets = [
            OutputDataset(
                namespace=self.namespace,
                name=out["name"],
                facets=out.get("facets", {})
            )
            for out in outputs
        ]

        # WHY: Add execution metrics to job facets
        job_facets = {}
        if metrics:
            job_facets["metrics"] = {
                "_producer": self.producer,
                "_schemaURL": "custom/metrics",
                **metrics
            }

        event = RunEvent(
            eventType=RunState.COMPLETE,
            eventTime=datetime.utcnow().isoformat(),
            run=Run(runId=run_id),
            job=Job(
                namespace=self.namespace,
                name=job_name,
                facets=job_facets
            ),
            outputs=output_datasets,
            producer=self.producer
        )

        self.client.emit(event)
        logger.info(f"COMPLETE event emitted for run: {run_id}")

    def emit_fail_event(
        self,
        job_name: str,
        run_id: str,
        error_message: str
    ):
        """
        WHY: FAIL event captures pipeline failures
        - Enables failure analysis in Marquez
        - Tracks error patterns over time
        - Critical for debugging and monitoring
        """
        logger.error(f"Emitting FAIL event for job: {job_name} - {error_message}")

        event = RunEvent(
            eventType=RunState.FAIL,
            eventTime=datetime.utcnow().isoformat(),
            run=Run(runId=run_id),
            job=Job(
                namespace=self.namespace,
                name=job_name
            ),
            producer=self.producer
        )

        self.client.emit(event)


# ============================================================================
# Prefect Tasks with Lineage Tracking
# ============================================================================

@task(name="extract_from_bronze")
def extract_from_bronze(
    table_name: str,
    lineage_tracker: LineageTracker
) -> pd.DataFrame:
    """
    WHY: Extract task reads from Bronze layer
    - Simulates reading from data lake / warehouse
    - Emits lineage for the extraction
    - Returns DataFrame for next task
    """
    logger = get_run_logger()
    logger.info(f"Extracting from Bronze: {table_name}")

    # WHY: In real implementation, this would read from S3/GCS/database
    # For demo, create sample data
    df = pd.DataFrame({
        'customer_id': ['C001', 'C002', 'C003'],
        'raw_name': ['Anders Jensen', 'Maria Nielsen', 'Peter Hansen'],
        'raw_email': ['anders@example.dk', 'maria@test.dk', 'peter@demo.dk'],
        'source_timestamp': [datetime.utcnow()] * 3
    })

    # WHY: Emit lineage - this extraction creates a dataset
    # Note: In bronze extraction, inputs are external (e.g., CRM system)
    # We track them as input datasets for complete lineage
    run_id = str(uuid.uuid4())
    lineage_tracker.emit_complete_event(
        job_name=f"extract_{table_name}",
        run_id=run_id,
        outputs=[{
            "name": f"bronze.{table_name}",
            "facets": lineage_tracker._create_dataset_facets(
                df,
                source_location=f"s3://atlas-bronze/{table_name}"
            )
        }],
        metrics={
            "rows_extracted": len(df),
            "duration_seconds": 1.2
        }
    )

    return df


@task(name="transform_to_silver")
def transform_to_silver(
    bronze_df: pd.DataFrame,
    table_name: str,
    lineage_tracker: LineageTracker
) -> pd.DataFrame:
    """
    WHY: Transform task performs Silver layer transformations
    - Applies business logic (cleaning, standardization)
    - Emits START and COMPLETE lineage events
    - Tracks column-level transformations
    """
    logger = get_run_logger()
    run_id = str(uuid.uuid4())

    logger.info(f"Transforming to Silver: {table_name}")

    # WHY: Emit START event before transformation
    lineage_tracker.emit_start_event(
        job_name=f"transform_to_silver_{table_name}",
        run_id=run_id,
        inputs=[{
            "name": f"bronze.{table_name}",
            "facets": lineage_tracker._create_dataset_facets(bronze_df)
        }],
        outputs=[{
            "name": f"silver.{table_name}",
            "facets": {}  # Will be filled in COMPLETE event
        }],
        job_metadata={
            "source_code_location": "https://github.com/atlas/pipelines/silver_transform.py"
        }
    )

    try:
        # WHY: Perform actual transformation
        silver_df = bronze_df.copy()
        silver_df.rename(columns={
            'raw_name': 'customer_name',
            'raw_email': 'email_address'
        }, inplace=True)

        # Add metadata columns
        # WHY: Track lineage metadata in the data itself
        silver_df['_processed_at'] = datetime.utcnow()
        silver_df['_pipeline_run_id'] = run_id

        # WHY: Emit COMPLETE event with output dataset metadata
        lineage_tracker.emit_complete_event(
            job_name=f"transform_to_silver_{table_name}",
            run_id=run_id,
            outputs=[{
                "name": f"silver.{table_name}",
                "facets": lineage_tracker._create_dataset_facets(
                    silver_df,
                    source_location=f"s3://atlas-silver/{table_name}"
                )
            }],
            metrics={
                "rows_transformed": len(silver_df),
                "columns_added": 2,
                "duration_seconds": 0.5
            }
        )

        logger.info(f"Silver transformation complete: {len(silver_df)} rows")
        return silver_df

    except Exception as e:
        # WHY: Emit FAIL event on errors
        lineage_tracker.emit_fail_event(
            job_name=f"transform_to_silver_{table_name}",
            run_id=run_id,
            error_message=str(e)
        )
        raise


@task(name="load_to_gold")
def load_to_gold(
    silver_df: pd.DataFrame,
    table_name: str,
    lineage_tracker: LineageTracker
) -> pd.DataFrame:
    """
    WHY: Load task creates Gold layer (analytics-ready data)
    - Applies aggregations and business metrics
    - Final lineage emission for end-to-end tracking
    - Creates AI-ready features
    """
    logger = get_run_logger()
    run_id = str(uuid.uuid4())

    logger.info(f"Loading to Gold: {table_name}")

    # WHY: Emit START event
    lineage_tracker.emit_start_event(
        job_name=f"load_to_gold_{table_name}",
        run_id=run_id,
        inputs=[{
            "name": f"silver.{table_name}",
            "facets": lineage_tracker._create_dataset_facets(silver_df)
        }],
        outputs=[{
            "name": f"gold.{table_name}",
            "facets": {}
        }]
    )

    try:
        # WHY: Gold layer transformations (aggregations, enrichment)
        gold_df = silver_df.copy()
        gold_df['customer_tier'] = 'standard'  # Business logic
        gold_df['_gold_created_at'] = datetime.utcnow()

        # WHY: Emit COMPLETE with final dataset
        lineage_tracker.emit_complete_event(
            job_name=f"load_to_gold_{table_name}",
            run_id=run_id,
            outputs=[{
                "name": f"gold.{table_name}",
                "facets": lineage_tracker._create_dataset_facets(
                    gold_df,
                    source_location=f"s3://atlas-gold/{table_name}"
                )
            }],
            metrics={
                "rows_loaded": len(gold_df),
                "duration_seconds": 0.3
            }
        )

        logger.info(f"Gold layer load complete: {len(gold_df)} rows")
        return gold_df

    except Exception as e:
        lineage_tracker.emit_fail_event(
            job_name=f"load_to_gold_{table_name}",
            run_id=run_id,
            error_message=str(e)
        )
        raise


# ============================================================================
# Prefect Flow: Bronze -> Silver -> Gold with Full Lineage
# ============================================================================

@flow(name="bronze_to_gold_pipeline")
def bronze_to_gold_pipeline(table_name: str = "customers"):
    """
    WHY: Prefect Flow orchestrates the entire pipeline
    - Manages task dependencies automatically
    - Handles retries and error handling
    - Integrates lineage tracking at each step

    This creates the full lineage chain:
    bronze.customers -> transform -> silver.customers -> load -> gold.customers
    """
    logger = get_run_logger()
    logger.info(f"Starting Bronze -> Gold pipeline for {table_name}")

    # Initialize lineage tracker
    # WHY: Single tracker instance across all tasks
    lineage_config = LineageConfig(
        marquez_url="http://localhost:5000",
        namespace="atlas_production"
    )
    lineage_tracker = LineageTracker(lineage_config)

    # WHY: Prefect automatically manages dependencies based on data flow
    bronze_data = extract_from_bronze(table_name, lineage_tracker)
    silver_data = transform_to_silver(bronze_data, table_name, lineage_tracker)
    gold_data = load_to_gold(silver_data, table_name, lineage_tracker)

    logger.info(
        f"Pipeline complete: {len(gold_data)} rows in gold.{table_name}"
    )

    return gold_data


# ============================================================================
# Impact Analysis Helper
# ============================================================================

def query_downstream_datasets(
    marquez_url: str,
    namespace: str,
    dataset_name: str
) -> List[str]:
    """
    WHY: Impact analysis - find all datasets affected by upstream changes
    - Critical for change management
    - Enables "what if" analysis before schema changes
    - Uses Marquez API to traverse lineage graph

    Args:
        marquez_url: Marquez instance URL
        namespace: Dataset namespace
        dataset_name: Starting dataset (e.g., "bronze.customers")

    Returns:
        List of downstream dataset names
    """
    import requests

    logger.info(f"Querying downstream datasets for {dataset_name}")

    try:
        # WHY: Marquez API provides lineage graph traversal
        response = requests.get(
            f"{marquez_url}/api/v1/namespaces/{namespace}/datasets/{dataset_name}/lineage",
            params={"depth": 10}  # How far to traverse
        )
        response.raise_for_status()

        lineage_graph = response.json()

        # WHY: Extract all downstream nodes from graph
        downstream = []
        for node in lineage_graph.get("graph", []):
            if node["type"] == "DATASET" and node["name"] != dataset_name:
                downstream.append(node["name"])

        logger.info(f"Found {len(downstream)} downstream datasets")
        return downstream

    except Exception as e:
        logger.error(f"Failed to query lineage: {e}")
        return []


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Run the pipeline
    # WHY: This will create complete lineage in Marquez:
    # bronze.customers -> silver.customers -> gold.customers
    result = bronze_to_gold_pipeline(table_name="customers")

    print("\n=== FINAL GOLD DATA ===")
    print(result)

    # Query impact analysis
    # WHY: Show what would be affected if bronze.customers changed
    print("\n=== IMPACT ANALYSIS ===")
    downstream = query_downstream_datasets(
        marquez_url="http://localhost:5000",
        namespace="atlas_production",
        dataset_name="bronze.customers"
    )
    print(f"Datasets affected by changes to bronze.customers:")
    for ds in downstream:
        print(f"  - {ds}")

    print("\n✅ Pipeline complete with full lineage tracking!")
    print("View lineage graph at: http://localhost:5000")
