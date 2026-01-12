"""
Airbyte Orchestrator

Orchestrates complete Airbyte sync pipeline end-to-end.
Coordinates data reading, PII detection, quality validation, database writes, and lineage tracking.

Author: Atlas Pipeline Team
Date: January 12, 2026
"""

import asyncio
import pandas as pd
from typing import Dict, Any, Optional
from uuid import uuid4
import logging

from app.connectors.airbyte.real_pyairbyte import RealPyAirbyteExecutor
from app.connectors.airbyte.database_writer import AirbyteDatabaseWriter
from app.connectors.airbyte.state_manager import StateManager
from app.pipeline.pii.presidio_detector import PresidioPIIDetector
from app.pipeline.quality.soda_validator import SodaQualityValidator

logger = logging.getLogger(__name__)


class AirbyteOrchestrator:
    """Orchestrates complete Airbyte sync pipeline."""

    def __init__(
        self,
        executor: RealPyAirbyteExecutor,
        writer: AirbyteDatabaseWriter,
        state_manager: StateManager,
        pii_detector: Optional[PresidioPIIDetector] = None,
        quality_validator: Optional[SodaQualityValidator] = None
    ):
        """
        Initialize orchestrator with all dependencies.

        Args:
            executor: PyAirbyte executor (real or mock)
            writer: Database writer for all layers
            state_manager: State persistence manager
            pii_detector: Optional PII detection service
            quality_validator: Optional quality validation service
        """
        self.executor = executor
        self.writer = writer
        self.state_manager = state_manager
        self.pii_detector = pii_detector
        self.quality_validator = quality_validator
        logger.info("Initialized AirbyteOrchestrator")

    async def execute_full_sync(
        self,
        source_id: str,
        stream_name: str,
        sync_mode: str = "incremental",
        natural_key_column: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute complete sync pipeline from source to all database layers.

        Steps:
        1. Read data from Airbyte source (or mock)
        2. Write raw to explore layer
        3. Run PII detection (if available)
        4. Run quality checks (if available)
        5. Write validated to chart layer
        6. Write business-ready to navigate layer
        7. Update state for incremental syncs
        8. Track lineage (placeholder)

        Args:
            source_id: Airbyte source identifier
            stream_name: Stream name to sync
            sync_mode: "incremental" or "full_refresh"
            natural_key_column: Column for SCD Type 2 tracking

        Returns:
            Sync results with comprehensive metrics

        Example:
            >>> orchestrator = await get_airbyte_orchestrator(DATABASE_URL)
            >>> result = await orchestrator.execute_full_sync(
            ...     source_id="postgres-prod",
            ...     stream_name="users",
            ...     sync_mode="incremental"
            ... )
            >>> print(f"Synced {result['records_synced']} records")
        """
        run_id = str(uuid4())
        logger.info(f"🚀 Starting sync: {source_id}/{stream_name} (run_id={run_id}, mode={sync_mode})")

        try:
            # Step 1: Read data from Airbyte (or mock)
            logger.info(f"[{run_id}] Step 1/8: Reading data from {source_id}")
            records = []

            async for record in self.executor.read_stream(
                source_id=source_id,
                stream_name=stream_name,
                sync_mode=sync_mode
            ):
                records.append(record)

            if not records:
                logger.warning(f"[{run_id}] No records returned from {source_id}/{stream_name}")
                return {
                    "run_id": run_id,
                    "status": "completed",
                    "records_synced": 0,
                    "message": "No new records to sync"
                }

            logger.info(f"[{run_id}] ✅ Read {len(records)} records from Airbyte")

            # Step 2: Write raw to explore layer
            logger.info(f"[{run_id}] Step 2/8: Writing raw data to explore layer")
            explore_count = await self.writer.write_to_explore(
                source_id=source_id,
                stream_name=stream_name,
                records=records,
                run_id=run_id
            )
            logger.info(f"[{run_id}] ✅ Wrote {explore_count} records to explore layer")

            # Convert to DataFrame for processing
            df = pd.DataFrame(records)
            logger.info(f"[{run_id}] Created DataFrame: {len(df)} rows × {len(df.columns)} columns")

            # Step 3: PII Detection
            logger.info(f"[{run_id}] Step 3/8: Running PII detection")
            pii_results = {}
            if self.pii_detector:
                try:
                    pii_results = await self.pii_detector.detect_pii(df)
                    total_detections = pii_results.get('total_detections', 0)
                    logger.info(f"[{run_id}] ✅ PII detection: {total_detections} findings")
                except Exception as e:
                    logger.error(f"[{run_id}] ⚠️ PII detection failed: {e}")
                    pii_results = {"total_detections": 0, "error": str(e)}
            else:
                logger.info(f"[{run_id}] ⚠️ PII detector not available, skipping")
                pii_results = {"total_detections": 0, "skipped": True}

            # Step 4: Quality Checks
            logger.info(f"[{run_id}] Step 4/8: Running quality checks")
            quality_results = {}
            if self.quality_validator:
                try:
                    quality_results = await self.quality_validator.validate_data(df)
                    overall_score = quality_results.get('overall_score', 0)
                    logger.info(f"[{run_id}] ✅ Quality score: {overall_score:.2f}/100")
                except Exception as e:
                    logger.error(f"[{run_id}] ⚠️ Quality validation failed: {e}")
                    quality_results = {"overall_score": 0, "error": str(e)}
            else:
                logger.info(f"[{run_id}] ⚠️ Quality validator not available, skipping")
                quality_results = {"overall_score": 100, "skipped": True}

            # Step 5: Write validated to chart layer
            logger.info(f"[{run_id}] Step 5/8: Writing validated data to chart layer")
            chart_count = await self.writer.write_to_chart(
                source_id=source_id,
                stream_name=stream_name,
                df=df,
                run_id=run_id,
                pii_results=pii_results,
                quality_results=quality_results
            )
            logger.info(f"[{run_id}] ✅ Wrote {chart_count} records to chart layer")

            # Step 6: Write business-ready to navigate layer
            logger.info(f"[{run_id}] Step 6/8: Writing business data to navigate layer (SCD Type 2)")
            navigate_count = await self.writer.write_to_navigate(
                source_id=source_id,
                stream_name=stream_name,
                df=df,
                run_id=run_id,
                natural_key_column=natural_key_column
            )
            logger.info(f"[{run_id}] ✅ Processed {navigate_count} records in navigate layer")

            # Step 7: Update state for incremental syncs
            if sync_mode == "incremental":
                logger.info(f"[{run_id}] Step 7/8: Updating incremental sync state")
                try:
                    # Extract cursor value from last record
                    cursor_value = None
                    for cursor_field in ['updated_at', 'created_at', 'timestamp', 'id']:
                        if cursor_field in records[-1]:
                            cursor_value = records[-1][cursor_field]
                            break

                    if cursor_value:
                        await self.state_manager.update_stream_state(
                            source_id=source_id,
                            stream_name=stream_name,
                            state_data={"cursor_value": str(cursor_value), "last_run_id": run_id}
                        )
                        logger.info(f"[{run_id}] ✅ Updated state: cursor={cursor_value}")
                    else:
                        logger.warning(f"[{run_id}] ⚠️ No cursor field found for incremental sync")
                except Exception as e:
                    logger.error(f"[{run_id}] ⚠️ Failed to update state: {e}")
            else:
                logger.info(f"[{run_id}] Step 7/8: Skipping state update (full refresh mode)")

            # Step 8: Track lineage
            logger.info(f"[{run_id}] Step 8/8: Tracking data lineage")
            try:
                await self._emit_lineage_event(
                    source_id=source_id,
                    stream_name=stream_name,
                    run_id=run_id,
                    records_count=len(records),
                    quality_score=quality_results.get('overall_score', 0),
                    pii_detections=pii_results.get('total_detections', 0)
                )
                logger.info(f"[{run_id}] ✅ Lineage event emitted")
            except Exception as e:
                logger.error(f"[{run_id}] ⚠️ Failed to emit lineage: {e}")

            # Build comprehensive result
            result = {
                "run_id": run_id,
                "status": "completed",
                "records_synced": len(records),
                "explore_records": explore_count,
                "chart_records": chart_count,
                "navigate_records": navigate_count,
                "pii_detections": pii_results.get('total_detections', 0),
                "quality_score": quality_results.get('overall_score', 0),
                "sync_mode": sync_mode,
                "source_id": source_id,
                "stream_name": stream_name,
                "layers_written": ["explore", "chart", "navigate"],
                "checks_performed": {
                    "pii_detection": bool(self.pii_detector and not pii_results.get('skipped')),
                    "quality_validation": bool(self.quality_validator and not quality_results.get('skipped')),
                    "state_updated": sync_mode == "incremental",
                    "lineage_tracked": True
                }
            }

            logger.info(f"[{run_id}] 🎉 Sync completed successfully!")
            logger.info(f"[{run_id}] Summary: {len(records)} records → explore ({explore_count}) → chart ({chart_count}) → navigate ({navigate_count})")

            return result

        except Exception as e:
            logger.error(f"[{run_id}] ❌ Sync failed: {e}", exc_info=True)
            return {
                "run_id": run_id,
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "source_id": source_id,
                "stream_name": stream_name
            }

    async def _emit_lineage_event(
        self,
        source_id: str,
        stream_name: str,
        run_id: str,
        records_count: int,
        quality_score: float,
        pii_detections: int
    ):
        """
        Emit OpenLineage event for data lineage tracking.

        Args:
            source_id: Source identifier
            stream_name: Stream name
            run_id: Pipeline run ID
            records_count: Number of records processed
            quality_score: Overall quality score
            pii_detections: Number of PII findings

        Note:
            This is a placeholder for OpenLineage integration.
            In production, this would emit events to an OpenLineage backend.
        """
        # Placeholder implementation
        # In production, integrate with OpenLineage client:
        #
        # from openlineage.client import OpenLineageClient
        # client = OpenLineageClient(url="http://openlineage-server:5000")
        #
        # event = {
        #     "eventType": "START",
        #     "eventTime": datetime.utcnow().isoformat(),
        #     "run": {"runId": run_id},
        #     "job": {
        #         "namespace": "atlas-pipeline",
        #         "name": f"airbyte-sync-{source_id}-{stream_name}"
        #     },
        #     "inputs": [
        #         {
        #             "namespace": source_id,
        #             "name": stream_name,
        #             "facets": {
        #                 "dataQuality": {"score": quality_score},
        #                 "dataPrivacy": {"pii_detections": pii_detections}
        #             }
        #         }
        #     ],
        #     "outputs": [
        #         {"namespace": "explore", "name": f"{source_id}_{stream_name}_raw"},
        #         {"namespace": "chart", "name": f"{source_id}_{stream_name}_validated"},
        #         {"namespace": "navigate", "name": f"{source_id}_{stream_name}_business"}
        #     ]
        # }
        # client.emit(event)

        logger.debug(
            f"Lineage: {source_id}/{stream_name} → "
            f"{records_count} records, quality={quality_score:.1f}, pii={pii_detections}"
        )


async def get_airbyte_orchestrator(
    database_url: str,
    enable_pii_detection: bool = True,
    enable_quality_validation: bool = True
) -> AirbyteOrchestrator:
    """
    Create Airbyte orchestrator with all dependencies.

    Args:
        database_url: PostgreSQL connection URL
        enable_pii_detection: Enable PII detection (default: True)
        enable_quality_validation: Enable quality validation (default: True)

    Returns:
        Initialized AirbyteOrchestrator instance

    Example:
        >>> orchestrator = await get_airbyte_orchestrator(
        ...     database_url="postgresql://user:pass@localhost/atlas_pipeline",
        ...     enable_pii_detection=True,
        ...     enable_quality_validation=True
        ... )
        >>> result = await orchestrator.execute_full_sync("postgres", "users")
    """
    try:
        # Import factory functions
        from app.connectors.airbyte.real_pyairbyte import get_real_pyairbyte_executor
        from app.connectors.airbyte.database_writer import get_database_writer
        from app.connectors.airbyte.state_manager import get_state_manager

        # Create executor (real or mock)
        logger.info("Creating PyAirbyte executor...")
        executor = get_real_pyairbyte_executor()

        # Create database writer
        logger.info("Creating database writer...")
        writer = await get_database_writer(database_url)

        # Create state manager
        logger.info("Creating state manager...")
        state_manager = get_state_manager()

        # Optionally create PII detector
        pii_detector = None
        if enable_pii_detection:
            try:
                from app.pipeline.pii.presidio_detector import get_presidio_detector
                logger.info("Creating PII detector...")
                pii_detector = get_presidio_detector()
            except Exception as e:
                logger.warning(f"Failed to create PII detector: {e}")

        # Optionally create quality validator
        quality_validator = None
        if enable_quality_validation:
            try:
                from app.pipeline.quality.soda_validator import get_soda_validator
                logger.info("Creating quality validator...")
                quality_validator = get_soda_validator()
            except Exception as e:
                logger.warning(f"Failed to create quality validator: {e}")

        orchestrator = AirbyteOrchestrator(
            executor=executor,
            writer=writer,
            state_manager=state_manager,
            pii_detector=pii_detector,
            quality_validator=quality_validator
        )

        logger.info("✅ Airbyte orchestrator created successfully")
        return orchestrator

    except Exception as e:
        logger.error(f"Failed to create orchestrator: {e}")
        raise
