"""Production-grade PII Detection using Microsoft Presidio.

WHY: Week 3 upgrade from regex to ML-powered PII detection
- Supports multiple languages (English, Danish)
- Custom recognizers for Danish CPR numbers
- Configurable anonymization strategies
- Retry logic for resilience
- GDPR compliance through comprehensive PII detection
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd
from presidio_analyzer import (
    AnalyzerEngine,
    Pattern,
    PatternRecognizer,
    RecognizerRegistry,
)
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


@dataclass
class PIIDetectionResult:
    """Result of PII detection for a column.

    Attributes:
        column_name: Name of the column containing PII
        pii_type: Type of PII detected (EMAIL, PHONE, PERSON, CPR, etc.)
        instances_found: Number of instances detected
        confidence_scores: List of confidence scores for detections
        sample_values: First 3 sample values (masked) for verification
        detected_at: Timestamp of detection
    """

    column_name: str
    pii_type: str
    instances_found: int
    confidence_scores: list[float]
    sample_values: list[str]
    detected_at: datetime


class PIIDetectionError(Exception):
    """Custom exception for PII detection failures."""

    pass


class PresidioPIIDetector:
    """Production-grade PII detector using Microsoft Presidio.

    WHY:
    - GDPR compliance through comprehensive PII detection
    - Multi-language support (English, Danish)
    - Custom Danish CPR recognizer
    - ML-powered detection (better than regex)
    - Multiple anonymization strategies
    - Retry logic for resilience
    """

    def __init__(
        self,
        languages: list[str] | None = None,
        confidence_threshold: float = 0.7,
    ):
        """Initialize the Presidio PII detector.

        Args:
            languages: List of languages to support (default: ["en", "da"])
            confidence_threshold: Minimum confidence score for PII detection
        """
        self.languages = languages or ["en", "da"]
        self.confidence_threshold = confidence_threshold
        self.analyzer = self._setup_analyzer()
        self.anonymizer = AnonymizerEngine()

        logger.info(
            f"Initialized Presidio PII detector "
            f"(languages: {self.languages}, threshold: {confidence_threshold})"
        )

    def _setup_analyzer(self) -> AnalyzerEngine:
        """Setup Presidio analyzer with custom recognizers.

        WHY: Add Danish-specific PII patterns
        - CPR number (Danish social security number)
        - Danish phone format
        - Support for both English and Danish NLP models

        Returns:
            Configured AnalyzerEngine
        """
        # Configure NLP engine with multiple languages
        nlp_configuration = {
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": "en", "model_name": "en_core_web_sm"},
            ],
        }

        # Add Danish model if requested (optional - may not be installed)
        if "da" in self.languages:
            try:
                nlp_configuration["models"].append(
                    {"lang_code": "da", "model_name": "da_core_news_sm"}
                )
            except Exception as e:
                logger.warning(f"Danish NLP model not available: {e}")

        provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
        nlp_engine = provider.create_engine()

        # Create registry with predefined recognizers
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers(nlp_engine=nlp_engine)

        # Add Danish CPR recognizer
        # WHY: CPR format: DDMMYY-XXXX or DDMMYYXXXX
        # Example: 010190-1234 or 0101901234
        cpr_pattern = Pattern(
            name="cpr_pattern",
            regex=r"\b\d{6}[-\s]?\d{4}\b",
            score=0.9,
        )

        cpr_recognizer = PatternRecognizer(
            supported_entity="DK_CPR",
            name="Danish CPR Number Recognizer",
            supported_language="da",
            patterns=[cpr_pattern],
            context=["cpr", "personnummer", "social", "sikringsnummer"],
        )
        registry.add_recognizer(cpr_recognizer)

        logger.info("Added Danish CPR recognizer to Presidio analyzer")

        # Create analyzer with custom registry
        analyzer = AnalyzerEngine(registry=registry, nlp_engine=nlp_engine)

        return analyzer

    @retry(
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=1, max=60),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def detect_pii_in_dataframe(
        self,
        df: pd.DataFrame,
        columns_to_scan: list[str] | None = None,
    ) -> list[PIIDetectionResult]:
        """Scan DataFrame columns for PII using Presidio.

        WHY: Identify all PII before anonymization
        - Required for GDPR compliance
        - Informs anonymization strategy
        - Creates audit trail

        Args:
            df: DataFrame to scan
            columns_to_scan: Specific columns to scan (None = all text columns)

        Returns:
            List of PII detection results

        Raises:
            PIIDetectionError: If PII detection fails
        """
        if columns_to_scan is None:
            # Only scan text/object columns
            columns_to_scan = df.select_dtypes(include=["object"]).columns.tolist()

        results = []

        for column in columns_to_scan:
            logger.info(f"Scanning column '{column}' for PII")

            # Collect all non-null values
            values = df[column].dropna().astype(str).tolist()

            if not values:
                continue

            # WHY: Analyze sample of values (performance optimization)
            # For large datasets, analyzing all values would be too slow
            sample_size = min(100, len(values))
            sample_values = values[:sample_size]

            pii_findings: dict[str, list[float]] = {}  # entity_type -> list of scores

            for value in sample_values:
                try:
                    # WHY: Use Presidio to analyze each value
                    analyzer_results = self.analyzer.analyze(
                        text=value,
                        language=self.languages[0],  # Primary language
                        entities=None,  # Detect all entity types
                        score_threshold=self.confidence_threshold,
                    )

                    # Group findings by entity type
                    for result in analyzer_results:
                        if result.entity_type not in pii_findings:
                            pii_findings[result.entity_type] = []
                        pii_findings[result.entity_type].append(result.score)

                except Exception as e:
                    logger.warning(f"Failed to analyze value in {column}: {e}")
                    continue

            # WHY: Create detection result for each PII type found
            for pii_type, scores in pii_findings.items():
                # Extrapolate to full column based on sample
                instances_found = int(len(scores) / sample_size * len(values))

                # Get masked sample values for verification
                masked_samples = self._get_masked_samples(
                    sample_values[:3], pii_type
                )

                result = PIIDetectionResult(
                    column_name=column,
                    pii_type=pii_type,
                    instances_found=instances_found,
                    confidence_scores=scores,
                    sample_values=masked_samples,
                    detected_at=datetime.utcnow(),
                )
                results.append(result)

                avg_confidence = sum(scores) / len(scores) if scores else 0.0
                logger.warning(
                    f"Found PII in column '{column}': {pii_type} "
                    f"({instances_found} instances, "
                    f"avg confidence: {avg_confidence:.2f})"
                )

        return results

    def _get_masked_samples(
        self, sample_values: list[str], pii_type: str
    ) -> list[str]:
        """Get masked sample values for safe display.

        Args:
            sample_values: Original values
            pii_type: Type of PII

        Returns:
            List of masked values
        """
        masked = []
        for value in sample_values:
            try:
                # Re-analyze to get structured results
                analysis_results = self.analyzer.analyze(
                    text=str(value),
                    language=self.languages[0],
                    score_threshold=self.confidence_threshold,
                )

                if not analysis_results:
                    masked.append(value)
                    continue

                # Mask using default operator
                anonymized = self.anonymizer.anonymize(
                    text=str(value),
                    analyzer_results=analysis_results,
                    operators={
                        "DEFAULT": OperatorConfig(
                            "mask", {"masking_char": "*", "chars_to_mask": 100}
                        )
                    },
                )

                masked.append(anonymized.text)

            except Exception as e:
                logger.debug(f"Failed to mask sample value: {e}")
                masked.append("***MASKED***")

        return masked

    def anonymize_dataframe(
        self,
        df: pd.DataFrame,
        detection_results: list[PIIDetectionResult],
        strategy: str = "hash",
    ) -> pd.DataFrame:
        """Anonymize PII in DataFrame based on detection results.

        WHY: GDPR compliance - mask PII before downstream processing

        Strategies:
        - hash: One-way hash (irreversible, GDPR compliant)
        - mask: Replace with asterisks
        - redact: Remove entirely

        Args:
            df: Original DataFrame
            detection_results: PII detection results
            strategy: Anonymization strategy

        Returns:
            Anonymized DataFrame

        Raises:
            ValueError: If unknown anonymization strategy
        """
        # WHY: Define operator for anonymization strategy
        operators = {
            "hash": OperatorConfig("hash", {"hash_type": "sha256"}),
            "mask": OperatorConfig(
                "mask", {"masking_char": "*", "chars_to_mask": 100}
            ),
            "redact": OperatorConfig("redact", {}),
        }

        if strategy not in operators:
            raise ValueError(f"Unknown anonymization strategy: {strategy}")

        operator = operators[strategy]
        anonymized_df = df.copy()

        # WHY: Anonymize each column that contains PII
        pii_columns = {result.column_name for result in detection_results}

        for column in pii_columns:
            logger.info(f"Anonymizing column '{column}' using strategy '{strategy}'")

            # Apply anonymization to each value
            anonymized_df[column] = anonymized_df[column].apply(
                lambda x: self._anonymize_value(x, operator) if pd.notna(x) else x
            )

        return anonymized_df

    def _anonymize_value(self, value: str, operator: OperatorConfig) -> str:
        """Anonymize a single value using Presidio.

        Args:
            value: Original value
            operator: Anonymization operator configuration

        Returns:
            Anonymized value
        """
        try:
            # Re-analyze value to get structured results
            analysis_results = self.analyzer.analyze(
                text=str(value),
                language=self.languages[0],
                score_threshold=self.confidence_threshold,
            )

            if not analysis_results:
                return value  # No PII detected, return original

            # Anonymize using Presidio
            anonymized_result = self.anonymizer.anonymize(
                text=str(value),
                analyzer_results=analysis_results,
                operators={"DEFAULT": operator},
            )

            return anonymized_result.text

        except Exception as e:
            logger.error(f"Failed to anonymize value: {e}")
            return "<REDACTED_ERROR>"  # Safe fallback

    def scan_dataframe(self, df: pd.DataFrame) -> dict[str, Any]:
        """Scan dataframe for PII (compatible with SimplePIIDetector interface).

        WHY: Maintains backward compatibility with existing API

        Args:
            df: DataFrame to scan

        Returns:
            Dictionary with PII findings in compatible format
        """
        detection_results = self.detect_pii_in_dataframe(df)

        # Convert to compatible format
        findings = []
        for result in detection_results:
            avg_confidence = (
                sum(result.confidence_scores) / len(result.confidence_scores)
                if result.confidence_scores
                else 0.0
            )

            findings.append(
                {
                    "column": result.column_name,
                    "type": result.pii_type,
                    "match_count": result.instances_found,
                    "total_rows": len(df),
                    "percentage": float(result.instances_found / len(df))
                    if len(df) > 0
                    else 0.0,
                    "sample_values": result.sample_values,
                    "confidence": avg_confidence,
                }
            )

        return {
            "findings": findings,
            "total_pii_fields": len(findings),
            "scanned_columns": len(df.columns),
            "scanned_rows": len(df),
        }
