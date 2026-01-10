"""
Atlas Pipeline Integration: adamiao + Presidio PII Detection
=============================================================

This example shows how to integrate:
1. adamiao's robust retry logic and error handling
2. Microsoft Presidio for PII detection and anonymization
3. Silver layer transformation with PII masking

WHY THIS INTEGRATION:
- adamiao provides production-grade retry patterns for API failures
- Presidio detects PII (names, emails, SSNs, phone numbers, etc.)
- Silver layer needs PII handling before data reaches Gold/AI layers
- Ensures GDPR compliance and privacy protection

DEPENDENCIES:
pip install presidio-analyzer presidio-anonymizer tenacity pandas
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

# adamiao-inspired retry logic with exponential backoff
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

# Presidio for PII detection
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# adamiao-style Configuration and Error Handling
# ============================================================================

@dataclass
class PIIDetectionConfig:
    """
    WHY: Configuration as code pattern from adamiao
    - Separates configuration from logic
    - Makes retry behavior tunable
    - Enables different configs for dev/staging/prod
    """
    max_retry_attempts: int = 3
    initial_delay_seconds: int = 1
    max_delay_seconds: int = 60
    backoff_multiplier: int = 2

    # Presidio configuration
    pii_languages: List[str] = None
    pii_entities: List[str] = None
    confidence_threshold: float = 0.7

    def __post_init__(self):
        if self.pii_languages is None:
            self.pii_languages = ["da", "en"]  # Danish and English
        if self.pii_entities is None:
            # WHY: Define what PII to detect - aligns with GDPR requirements
            self.pii_entities = [
                "PERSON",           # Names
                "EMAIL_ADDRESS",    # Email
                "PHONE_NUMBER",     # Phone
                "CPR_NUMBER",       # Danish CPR (similar to SSN)
                "CREDIT_CARD",      # Credit card numbers
                "IBAN_CODE",        # Bank accounts
                "LOCATION",         # Addresses
                "DATE_TIME",        # Dates (quasi-identifier)
            ]


class PIIDetectionError(Exception):
    """
    WHY: Custom exception for PII detection failures
    - Allows specific error handling for PII issues
    - Can be caught and logged separately from other errors
    """
    pass


# ============================================================================
# Presidio-based PII Detector with adamiao retry logic
# ============================================================================

class PIIDetector:
    """
    WHY: Encapsulates PII detection logic with robust error handling
    - Combines Presidio's detection with adamiao's retry patterns
    - Provides both detection and anonymization capabilities
    - Logs all PII findings for audit trail
    """

    def __init__(self, config: PIIDetectionConfig):
        self.config = config

        # Initialize Presidio engines
        # WHY: AnalyzerEngine detects PII, AnonymizerEngine masks it
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

        logger.info(f"Initialized PII detector for entities: {config.pii_entities}")

    @retry(
        # WHY: adamiao pattern - retry on transient failures only
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=1, max=60),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    def _analyze_text_with_retry(self, text: str, language: str = "en") -> List:
        """
        WHY: Presidio API calls might fail due to:
        - Network issues
        - Service overload
        - Temporary unavailability

        adamiao retry pattern ensures resilience
        """
        try:
            results = self.analyzer.analyze(
                text=text,
                language=language,
                entities=self.config.pii_entities,
                score_threshold=self.config.confidence_threshold
            )
            return results
        except Exception as e:
            logger.error(f"PII analysis failed: {str(e)}")
            raise PIIDetectionError(f"Failed to analyze text: {str(e)}")

    def detect_pii_in_dataframe(
        self,
        df: pd.DataFrame,
        columns_to_scan: Optional[List[str]] = None
    ) -> Dict[str, List[Dict]]:
        """
        Scan DataFrame for PII across specified columns.

        WHY: Silver layer transformation needs to:
        1. Identify which columns contain PII
        2. Track exactly where PII appears
        3. Log findings for compliance

        Args:
            df: DataFrame to scan
            columns_to_scan: Specific columns to check (None = all text columns)

        Returns:
            Dict mapping column names to list of PII findings
        """
        if columns_to_scan is None:
            # WHY: Only scan text columns to avoid type errors
            columns_to_scan = df.select_dtypes(include=['object']).columns.tolist()

        pii_findings = {}

        for column in columns_to_scan:
            logger.info(f"Scanning column '{column}' for PII...")
            column_findings = []

            for idx, value in df[column].items():
                if pd.isna(value) or not isinstance(value, str):
                    continue

                # WHY: Use retry-wrapped method for resilience
                try:
                    results = self._analyze_text_with_retry(
                        text=value,
                        language="da"  # Danish as primary, falls back to EN patterns
                    )

                    if results:
                        # WHY: Store findings with context for audit trail
                        column_findings.append({
                            'row_index': idx,
                            'original_value': value,
                            'pii_types': [r.entity_type for r in results],
                            'confidence_scores': [r.score for r in results],
                            'detected_at': datetime.utcnow().isoformat()
                        })

                except PIIDetectionError as e:
                    logger.warning(f"Skipping row {idx} in {column}: {e}")
                    continue

            if column_findings:
                pii_findings[column] = column_findings
                logger.warning(
                    f"Found {len(column_findings)} PII instances in column '{column}'"
                )

        return pii_findings

    def anonymize_dataframe(
        self,
        df: pd.DataFrame,
        pii_findings: Dict[str, List[Dict]],
        anonymization_strategy: str = "hash"
    ) -> pd.DataFrame:
        """
        Anonymize PII in DataFrame based on detection findings.

        WHY: Silver layer must mask PII before data flows to Gold/AI
        - 'hash': One-way hash (irreversible, GDPR compliant)
        - 'mask': Replace with <MASKED>
        - 'redact': Remove entirely

        Args:
            df: Original DataFrame
            pii_findings: Output from detect_pii_in_dataframe
            anonymization_strategy: How to handle PII

        Returns:
            Anonymized DataFrame
        """
        anonymized_df = df.copy()

        # WHY: Define operator config based on strategy
        operator_configs = {
            "hash": OperatorConfig("hash", {"hash_type": "sha256"}),
            "mask": OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 100}),
            "redact": OperatorConfig("redact", {})
        }

        if anonymization_strategy not in operator_configs:
            raise ValueError(f"Unknown strategy: {anonymization_strategy}")

        operator = operator_configs[anonymization_strategy]

        for column, findings in pii_findings.items():
            for finding in findings:
                row_idx = finding['row_index']
                original_text = finding['original_value']

                # WHY: Use Presidio to anonymize with chosen strategy
                try:
                    # Re-analyze to get structured results for anonymization
                    analysis_results = self._analyze_text_with_retry(
                        text=original_text,
                        language="da"
                    )

                    # Anonymize the text
                    anonymized_result = self.anonymizer.anonymize(
                        text=original_text,
                        analyzer_results=analysis_results,
                        operators={"DEFAULT": operator}
                    )

                    # WHY: Update DataFrame with anonymized value
                    anonymized_df.at[row_idx, column] = anonymized_result.text

                    logger.debug(
                        f"Anonymized {column}[{row_idx}]: "
                        f"{original_text[:20]}... -> {anonymized_result.text[:20]}..."
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to anonymize {column}[{row_idx}]: {e}"
                    )
                    # WHY: On failure, redact entirely for safety
                    anonymized_df.at[row_idx, column] = "<REDACTED_DUE_TO_ERROR>"

        return anonymized_df


# ============================================================================
# Silver Layer Transformation with PII Detection
# ============================================================================

class SilverLayerTransformer:
    """
    WHY: Silver layer is where raw data becomes clean, standardized, and safe
    - Validates data quality
    - Detects and handles PII
    - Standardizes formats
    - Logs lineage
    """

    def __init__(self, config: PIIDetectionConfig):
        self.config = config
        self.pii_detector = PIIDetector(config)
        self.transformation_log = []

    def transform_bronze_to_silver(
        self,
        bronze_df: pd.DataFrame,
        table_name: str,
        pii_columns: Optional[List[str]] = None,
        pipeline_run_id: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Main transformation: Bronze (raw) -> Silver (clean + safe)

        WHY: This is the critical step where:
        1. Data is validated
        2. PII is detected and masked
        3. Lineage is tracked
        4. Quality is ensured

        Args:
            bronze_df: Raw data from source
            table_name: Name for logging/lineage
            pii_columns: Columns to scan (None = auto-detect)
            pipeline_run_id: For lineage tracking

        Returns:
            Silver layer DataFrame (clean, safe, standardized)
        """
        logger.info(f"Starting Silver transformation for {table_name}")
        transformation_start = datetime.utcnow()

        # Step 1: Detect PII
        # WHY: Must identify PII before masking
        logger.info("Step 1: Detecting PII...")
        pii_findings = self.pii_detector.detect_pii_in_dataframe(
            df=bronze_df,
            columns_to_scan=pii_columns
        )

        # Step 2: Anonymize PII
        # WHY: Mask PII before data goes downstream
        logger.info("Step 2: Anonymizing PII...")
        silver_df = self.pii_detector.anonymize_dataframe(
            df=bronze_df,
            pii_findings=pii_findings,
            anonymization_strategy="hash"  # GDPR-compliant one-way hash
        )

        # Step 3: Add metadata columns
        # WHY: Track lineage and enable auditing
        logger.info("Step 3: Adding metadata...")
        silver_df['_silver_processed_at'] = transformation_start
        silver_df['_pipeline_run_id'] = pipeline_run_id or "unknown"
        silver_df['_pii_detected'] = silver_df.index.isin(
            [f['row_index'] for findings in pii_findings.values() for f in findings]
        )

        # Step 4: Log transformation
        # WHY: Audit trail for compliance and debugging
        transformation_record = {
            'table_name': table_name,
            'pipeline_run_id': pipeline_run_id,
            'transformation_start': transformation_start,
            'transformation_end': datetime.utcnow(),
            'rows_processed': len(bronze_df),
            'pii_columns_found': list(pii_findings.keys()),
            'total_pii_instances': sum(len(f) for f in pii_findings.values()),
            'anonymization_strategy': 'hash'
        }
        self.transformation_log.append(transformation_record)

        logger.info(
            f"Silver transformation complete: {len(bronze_df)} rows, "
            f"{sum(len(f) for f in pii_findings.values())} PII instances masked"
        )

        return silver_df


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Sample data with PII
    sample_data = pd.DataFrame({
        'customer_id': ['C001', 'C002', 'C003'],
        'customer_name': ['Anders Jensen', 'Maria Nielsen', 'Peter Hansen'],
        'email': ['anders@example.dk', 'maria@test.dk', 'peter@demo.dk'],
        'phone': ['+4512345678', '+4587654321', '+4511223344'],
        'notes': [
            'Customer called on 2025-01-15',
            'Email sent to maria@test.dk',
            'Follow up with Peter Hansen at +4511223344'
        ]
    })

    # Configure PII detection
    config = PIIDetectionConfig(
        max_retry_attempts=3,
        confidence_threshold=0.7
    )

    # Transform Bronze -> Silver with PII handling
    transformer = SilverLayerTransformer(config)

    silver_data = transformer.transform_bronze_to_silver(
        bronze_df=sample_data,
        table_name='customers',
        pii_columns=['customer_name', 'email', 'phone', 'notes'],
        pipeline_run_id='run_20260107_001'
    )

    print("\n=== ORIGINAL (Bronze) ===")
    print(sample_data)

    print("\n=== TRANSFORMED (Silver) ===")
    print(silver_data)

    print("\n=== TRANSFORMATION LOG ===")
    import json
    print(json.dumps(transformer.transformation_log, indent=2, default=str))
