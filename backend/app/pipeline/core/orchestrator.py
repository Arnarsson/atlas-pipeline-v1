"""Pipeline orchestrator for Atlas Data Platform."""

import io
import os
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

# Week 3: Import production-grade detectors
try:
    from app.pipeline.pii.presidio_detector import PresidioPIIDetector
    from app.pipeline.quality.soda_validator import SodaQualityValidator

    WEEK3_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Week 3 dependencies not available, falling back to Week 2: {e}")
    WEEK3_AVAILABLE = False
    from app.pipeline.pii.detector import SimplePIIDetector
    from app.pipeline.quality.checker import SimpleQualityChecker


def _convert_numpy_types(obj: Any) -> Any:
    """
    Recursively convert numpy types to Python native types for JSON serialization.

    Args:
        obj: Object to convert (can be dict, list, numpy type, or any value)

    Returns:
        Object with all numpy types converted to Python native types
    """
    if isinstance(obj, dict):
        return {key: _convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_convert_numpy_types(item) for item in obj]
    elif isinstance(obj, (np.bool_, np.bool8)):
        return bool(obj)
    elif isinstance(obj, (np.integer, np.int8, np.int16, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


class PipelineOrchestrator:
    """
    Pipeline orchestrator for Atlas Data Platform.

    Processes data through:
    1. Explore layer (Bronze) - CSV ingestion
    2. Chart layer (Silver) - PII scanning + quality checks

    Week 3 Enhancement:
    - Upgrades to Presidio PII detection (if spaCy models installed)
    - Upgrades to Soda Core quality validation (6 dimensions)
    - Falls back to Week 2 implementation if dependencies unavailable
    """

    def __init__(self, use_week3: bool = True):
        """Initialize the orchestrator.

        Args:
            use_week3: Whether to use Week 3 enhanced detectors (default: True)
        """
        self.use_week3 = use_week3 and WEEK3_AVAILABLE

        if self.use_week3:
            try:
                logger.info("Initializing Week 3 production-grade detectors")
                self.pii_detector = PresidioPIIDetector(
                    languages=["en", "da"], confidence_threshold=0.7
                )
                self.quality_checker = SodaQualityValidator(
                    completeness_threshold=0.95,
                    uniqueness_threshold=0.98,
                    validity_threshold=0.90,
                )
                logger.info("✅ Week 3 detectors initialized successfully")
            except Exception as e:
                logger.warning(
                    f"Failed to initialize Week 3 detectors, falling back to Week 2: {e}"
                )
                self.use_week3 = False
                self.pii_detector = SimplePIIDetector()
                self.quality_checker = SimpleQualityChecker()
        else:
            logger.info("Using Week 2 simple detectors")
            self.pii_detector = SimplePIIDetector()
            self.quality_checker = SimpleQualityChecker()

    def run_pipeline(
        self,
        run_id: str,
        file_content: bytes,
        filename: str,
        dataset_name: str,
        storage: dict[str, dict[str, Any]],
    ) -> None:
        """
        Run the data pipeline.

        Args:
            run_id: Pipeline run ID
            file_content: CSV file content
            filename: Original filename
            dataset_name: Dataset name
            storage: In-memory storage dict
        """
        try:
            logger.info(f"Starting pipeline run {run_id} for {dataset_name}")

            # Update status
            storage[run_id]["status"] = "running"
            storage[run_id]["current_step"] = "ingestion"

            # Step 1: Explore Layer - Ingest CSV
            logger.info(f"[{run_id}] Step 1: Ingesting CSV data")
            df = self._ingest_csv(file_content, filename)

            storage[run_id]["current_step"] = "exploration"
            logger.info(f"[{run_id}] Ingested {len(df)} rows, {len(df.columns)} columns")

            # Step 2: Chart Layer - PII Scanning
            storage[run_id]["current_step"] = "pii_scanning"
            logger.info(
                f"[{run_id}] Step 2: Scanning for PII "
                f"(using {'Week 3 Presidio' if self.use_week3 else 'Week 2 regex'})"
            )
            pii_results = self._scan_pii(df)

            pii_count = pii_results.get("total_pii_fields", 0)
            logger.info(f"[{run_id}] Found {pii_count} PII fields")

            # Step 3: Chart Layer - Quality Checks
            storage[run_id]["current_step"] = "quality_checks"
            logger.info(
                f"[{run_id}] Step 3: Running quality checks "
                f"(using {'Week 3 Soda Core' if self.use_week3 else 'Week 2 basic'})"
            )
            quality_results = self._check_quality(df)

            logger.info(
                f"[{run_id}] Quality score: {quality_results['overall_score']:.2%}"
            )

            # Add metadata about detector versions
            detector_metadata = {
                "pii_detector": "presidio" if self.use_week3 else "regex",
                "quality_validator": "soda-core" if self.use_week3 else "basic",
                "week3_enabled": self.use_week3,
            }

            # Complete - convert all numpy types to Python types for JSON serialization
            storage[run_id]["status"] = "completed"
            storage[run_id]["current_step"] = "completed"
            storage[run_id]["results"] = _convert_numpy_types(
                {
                    "explore": {
                        "rows": len(df),
                        "columns": len(df.columns),
                        "column_names": df.columns.tolist(),
                        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                    },
                    "pii": pii_results,
                    "quality": quality_results,
                    "metadata": detector_metadata,
                }
            )

            logger.info(
                f"[{run_id}] Pipeline completed successfully "
                f"(Week {'3' if self.use_week3 else '2'} detectors)"
            )

        except Exception as e:
            logger.error(f"[{run_id}] Pipeline failed: {str(e)}")
            storage[run_id]["status"] = "failed"
            storage[run_id]["error"] = str(e)

    def _ingest_csv(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """
        Ingest CSV file into a DataFrame.

        Args:
            file_content: CSV file content
            filename: Original filename

        Returns:
            Pandas DataFrame
        """
        try:
            # Read CSV with automatic type inference
            df = pd.read_csv(io.BytesIO(file_content))

            if df.empty:
                raise ValueError("CSV file is empty")

            return df

        except pd.errors.EmptyDataError:
            raise ValueError("CSV file is empty")
        except pd.errors.ParserError as e:
            raise ValueError(f"Failed to parse CSV: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to read CSV: {str(e)}")

    def _scan_pii(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Scan DataFrame for PII.

        Args:
            df: DataFrame to scan

        Returns:
            PII scan results
        """
        return self.pii_detector.scan_dataframe(df)

    def _check_quality(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Check data quality.

        Args:
            df: DataFrame to check

        Returns:
            Quality check results
        """
        return self.quality_checker.check_dataframe(df)
