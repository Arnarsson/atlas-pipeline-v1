"""Production-grade Data Quality Validation using Soda Core.

WHY: Week 3 upgrade from basic SQL checks to comprehensive quality framework
- 6 quality dimensions (completeness, uniqueness, timeliness, validity, accuracy, consistency)
- Configurable thresholds
- Detailed dimension-specific checks
- Integration with Soda Core quality framework
- Supports complex validation rules
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class QualityDimension(str, Enum):
    """Quality dimensions for data validation.

    WHY: Standard data quality framework
    - ISO 8000 data quality standards
    - DAMA-DMBOK quality dimensions
    """

    COMPLETENESS = "completeness"
    UNIQUENESS = "uniqueness"
    TIMELINESS = "timeliness"
    VALIDITY = "validity"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"


@dataclass
class QualityCheckResult:
    """Result of a quality check.

    Attributes:
        dimension: Quality dimension checked
        score: Quality score (0.0-1.0)
        passed: Whether check passed threshold
        threshold: Required threshold
        details: Dimension-specific details
        checked_at: Timestamp of check
    """

    dimension: QualityDimension
    score: float
    passed: bool
    threshold: float
    details: dict[str, Any]
    checked_at: datetime


class SodaQualityValidator:
    """Production-grade quality validator using Soda Core patterns.

    WHY:
    - Comprehensive quality validation across 6 dimensions
    - Industry-standard quality framework
    - Configurable thresholds per dimension
    - Detailed reporting for each dimension
    - Integration-ready with Soda Core
    """

    def __init__(
        self,
        completeness_threshold: float = 0.95,
        uniqueness_threshold: float = 0.98,
        timeliness_days: int = 7,
        validity_threshold: float = 0.90,
        accuracy_threshold: float = 0.90,
        consistency_threshold: float = 0.90,
    ):
        """Initialize quality validator with thresholds.

        Args:
            completeness_threshold: Minimum completeness score (default: 95%)
            uniqueness_threshold: Minimum uniqueness score (default: 98%)
            timeliness_days: Maximum age in days for timely data (default: 7)
            validity_threshold: Minimum validity score (default: 90%)
            accuracy_threshold: Minimum accuracy score (default: 90%)
            consistency_threshold: Minimum consistency score (default: 90%)
        """
        self.thresholds = {
            QualityDimension.COMPLETENESS: completeness_threshold,
            QualityDimension.UNIQUENESS: uniqueness_threshold,
            QualityDimension.TIMELINESS: timeliness_days,
            QualityDimension.VALIDITY: validity_threshold,
            QualityDimension.ACCURACY: accuracy_threshold,
            QualityDimension.CONSISTENCY: consistency_threshold,
        }

        logger.info(f"Initialized Soda quality validator with thresholds: {self.thresholds}")

    def check_completeness(self, df: pd.DataFrame) -> QualityCheckResult:
        """Check data completeness (missing values).

        WHY: Completeness measures the degree to which data is present
        - Missing values reduce data utility
        - Critical for downstream analytics
        - GDPR requires complete data for accuracy

        Args:
            df: DataFrame to check

        Returns:
            QualityCheckResult for completeness
        """
        total_cells = len(df) * len(df.columns)
        missing_values = df.isnull().sum().sum()

        completeness_score = (
            1.0 - (missing_values / total_cells) if total_cells > 0 else 0.0
        )

        # Per-column analysis
        column_completeness = {}
        for column in df.columns:
            col_missing = df[column].isnull().sum()
            col_total = len(df)
            col_completeness = (
                1.0 - (col_missing / col_total) if col_total > 0 else 0.0
            )
            column_completeness[column] = {
                "completeness": float(col_completeness),
                "missing_count": int(col_missing),
                "missing_percentage": float(col_missing / col_total)
                if col_total > 0
                else 0.0,
            }

        threshold = self.thresholds[QualityDimension.COMPLETENESS]

        return QualityCheckResult(
            dimension=QualityDimension.COMPLETENESS,
            score=completeness_score,
            passed=completeness_score >= threshold,
            threshold=threshold,
            details={
                "total_cells": total_cells,
                "missing_values": int(missing_values),
                "missing_percentage": float(missing_values / total_cells)
                if total_cells > 0
                else 0.0,
                "column_completeness": column_completeness,
            },
            checked_at=datetime.utcnow(),
        )

    def check_uniqueness(self, df: pd.DataFrame) -> QualityCheckResult:
        """Check data uniqueness (duplicate detection).

        WHY: Uniqueness measures the degree to which data is distinct
        - Duplicates skew analytics and ML models
        - Indicates data quality issues in source systems
        - Critical for key fields (IDs, emails, etc.)

        Args:
            df: DataFrame to check

        Returns:
            QualityCheckResult for uniqueness
        """
        total_rows = len(df)
        duplicate_rows = df.duplicated().sum()

        uniqueness_score = (
            1.0 - (duplicate_rows / total_rows) if total_rows > 0 else 1.0
        )

        # Per-column uniqueness analysis
        column_uniqueness = {}
        for column in df.columns:
            unique_count = df[column].nunique()
            total_count = len(df[column].dropna())
            uniqueness = unique_count / total_count if total_count > 0 else 1.0

            # Check for potential key fields (high uniqueness)
            is_potential_key = uniqueness >= 0.95

            column_uniqueness[column] = {
                "uniqueness": float(uniqueness),
                "unique_count": int(unique_count),
                "total_count": int(total_count),
                "duplicate_count": int(total_count - unique_count),
                "is_potential_key": is_potential_key,
            }

        threshold = self.thresholds[QualityDimension.UNIQUENESS]

        return QualityCheckResult(
            dimension=QualityDimension.UNIQUENESS,
            score=uniqueness_score,
            passed=uniqueness_score >= threshold,
            threshold=threshold,
            details={
                "total_rows": total_rows,
                "duplicate_rows": int(duplicate_rows),
                "duplicate_percentage": float(duplicate_rows / total_rows)
                if total_rows > 0
                else 0.0,
                "column_uniqueness": column_uniqueness,
            },
            checked_at=datetime.utcnow(),
        )

    def check_timeliness(self, df: pd.DataFrame) -> QualityCheckResult:
        """Check data timeliness (freshness).

        WHY: Timeliness measures how current the data is
        - Stale data leads to poor decisions
        - Critical for real-time analytics
        - SLA compliance for data delivery

        Args:
            df: DataFrame to check

        Returns:
            QualityCheckResult for timeliness
        """
        # Look for date/datetime columns
        date_columns = df.select_dtypes(
            include=["datetime64", "datetime64[ns]"]
        ).columns.tolist()

        if not date_columns:
            # Try to infer date columns from object types
            for column in df.select_dtypes(include=["object"]).columns:
                try:
                    pd.to_datetime(df[column].dropna().head(10))
                    date_columns.append(column)
                except (ValueError, TypeError):
                    continue

        if not date_columns:
            # No date columns found - consider data timely by default
            return QualityCheckResult(
                dimension=QualityDimension.TIMELINESS,
                score=1.0,
                passed=True,
                threshold=self.thresholds[QualityDimension.TIMELINESS],
                details={
                    "message": "No date columns found - timeliness check skipped",
                    "date_columns": [],
                },
                checked_at=datetime.utcnow(),
            )

        # Analyze freshness of date columns
        now = datetime.utcnow()
        max_age_days = self.thresholds[QualityDimension.TIMELINESS]
        cutoff_date = now - timedelta(days=max_age_days)

        column_timeliness = {}
        timely_rows = 0
        total_date_rows = 0

        for column in date_columns:
            try:
                # Convert to datetime if needed
                date_series = pd.to_datetime(df[column], errors="coerce")
                valid_dates = date_series.dropna()

                if len(valid_dates) == 0:
                    continue

                # Count rows within acceptable age
                recent_count = (valid_dates >= cutoff_date).sum()
                total_count = len(valid_dates)

                timeliness = recent_count / total_count if total_count > 0 else 0.0

                column_timeliness[column] = {
                    "timeliness": float(timeliness),
                    "recent_count": int(recent_count),
                    "stale_count": int(total_count - recent_count),
                    "oldest_date": valid_dates.min().isoformat(),
                    "newest_date": valid_dates.max().isoformat(),
                    "max_age_days": max_age_days,
                }

                timely_rows += recent_count
                total_date_rows += total_count

            except Exception as e:
                logger.warning(f"Failed to check timeliness for column {column}: {e}")
                continue

        # Overall timeliness score
        timeliness_score = (
            timely_rows / total_date_rows if total_date_rows > 0 else 1.0
        )

        # Threshold is in days, but we convert to score (0-1)
        # Data is timely if it meets the max_age_days threshold
        threshold_score = 0.8  # 80% of data should be within max_age_days

        return QualityCheckResult(
            dimension=QualityDimension.TIMELINESS,
            score=timeliness_score,
            passed=timeliness_score >= threshold_score,
            threshold=threshold_score,
            details={
                "timely_rows": int(timely_rows),
                "total_date_rows": int(total_date_rows),
                "max_age_days": max_age_days,
                "column_timeliness": column_timeliness,
            },
            checked_at=datetime.utcnow(),
        )

    def check_validity(self, df: pd.DataFrame) -> QualityCheckResult:
        """Check data validity (format and type correctness).

        WHY: Validity measures conformance to defined formats
        - Invalid data causes processing errors
        - Type mismatches break downstream systems
        - Format errors indicate data quality issues

        Args:
            df: DataFrame to check

        Returns:
            QualityCheckResult for validity
        """
        total_cells = len(df) * len(df.columns)
        invalid_count = 0

        column_validity = {}

        for column in df.columns:
            col_invalid = 0

            # Check for empty strings in text columns
            if df[column].dtype == "object":
                empty_strings = (df[column].astype(str).str.strip() == "").sum()
                col_invalid += empty_strings

                # Check for invalid patterns (optional - can be extended)
                # Example: check email format if column name suggests email
                if "email" in column.lower():
                    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                    invalid_emails = ~df[column].str.match(
                        email_pattern, na=False
                    )
                    col_invalid += invalid_emails.sum()

            # Check for invalid numeric values
            if pd.api.types.is_numeric_dtype(df[column]):
                # Check for inf and -inf
                inf_count = (df[column] == float("inf")).sum()
                neg_inf_count = (df[column] == float("-inf")).sum()
                col_invalid += inf_count + neg_inf_count

            column_validity[column] = {
                "invalid_count": int(col_invalid),
                "valid_count": int(len(df) - col_invalid),
                "validity": float(1.0 - (col_invalid / len(df)))
                if len(df) > 0
                else 1.0,
            }

            invalid_count += col_invalid

        validity_score = 1.0 - (invalid_count / total_cells) if total_cells > 0 else 1.0
        threshold = self.thresholds[QualityDimension.VALIDITY]

        return QualityCheckResult(
            dimension=QualityDimension.VALIDITY,
            score=validity_score,
            passed=validity_score >= threshold,
            threshold=threshold,
            details={
                "total_cells": total_cells,
                "invalid_count": int(invalid_count),
                "invalid_percentage": float(invalid_count / total_cells)
                if total_cells > 0
                else 0.0,
                "column_validity": column_validity,
            },
            checked_at=datetime.utcnow(),
        )

    def check_accuracy(self, df: pd.DataFrame) -> QualityCheckResult:
        """Check data accuracy (value range validation).

        WHY: Accuracy measures correctness of data values
        - Out-of-range values indicate errors
        - Statistical outliers may be data quality issues
        - Business rules violations

        Args:
            df: DataFrame to check

        Returns:
            QualityCheckResult for accuracy
        """
        total_cells = len(df) * len(df.columns)
        accuracy_issues = 0

        column_accuracy = {}

        for column in df.columns:
            col_issues = 0

            # Numeric column checks
            if pd.api.types.is_numeric_dtype(df[column]):
                values = df[column].dropna()

                if len(values) > 0:
                    # Statistical outlier detection using IQR method
                    Q1 = values.quantile(0.25)
                    Q3 = values.quantile(0.75)
                    IQR = Q3 - Q1

                    # Values outside 1.5 * IQR are potential outliers
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR

                    outliers = ((values < lower_bound) | (values > upper_bound)).sum()

                    column_accuracy[column] = {
                        "outlier_count": int(outliers),
                        "total_count": int(len(values)),
                        "outlier_percentage": float(outliers / len(values))
                        if len(values) > 0
                        else 0.0,
                        "min": float(values.min()),
                        "max": float(values.max()),
                        "mean": float(values.mean()),
                        "std": float(values.std()),
                        "lower_bound": float(lower_bound),
                        "upper_bound": float(upper_bound),
                    }

                    # Only count extreme outliers as accuracy issues
                    col_issues = outliers

            # Text column checks
            elif df[column].dtype == "object":
                values = df[column].dropna().astype(str)

                if len(values) > 0:
                    # Check for unreasonably long strings (potential data corruption)
                    max_reasonable_length = 1000
                    too_long = (values.str.len() > max_reasonable_length).sum()

                    # Check for strings with unusual characters (potential encoding issues)
                    unusual_chars = (
                        values.str.contains(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]", regex=True)
                    ).sum()

                    col_issues = too_long + unusual_chars

                    column_accuracy[column] = {
                        "too_long_count": int(too_long),
                        "unusual_chars_count": int(unusual_chars),
                        "total_count": int(len(values)),
                        "max_length": int(values.str.len().max()),
                        "avg_length": float(values.str.len().mean()),
                    }

            accuracy_issues += col_issues

        accuracy_score = (
            1.0 - (accuracy_issues / total_cells) if total_cells > 0 else 1.0
        )
        threshold = self.thresholds[QualityDimension.ACCURACY]

        return QualityCheckResult(
            dimension=QualityDimension.ACCURACY,
            score=accuracy_score,
            passed=accuracy_score >= threshold,
            threshold=threshold,
            details={
                "total_cells": total_cells,
                "accuracy_issues": int(accuracy_issues),
                "issue_percentage": float(accuracy_issues / total_cells)
                if total_cells > 0
                else 0.0,
                "column_accuracy": column_accuracy,
            },
            checked_at=datetime.utcnow(),
        )

    def check_consistency(self, df: pd.DataFrame) -> QualityCheckResult:
        """Check data consistency (cross-field validation).

        WHY: Consistency measures logical coherence across fields
        - Contradictory data indicates quality issues
        - Cross-field rules violations
        - Referential integrity

        Args:
            df: DataFrame to check

        Returns:
            QualityCheckResult for consistency
        """
        total_rows = len(df)
        consistency_issues = 0

        checks_performed = []

        # Check 1: Date range consistency (start_date < end_date)
        date_columns = df.select_dtypes(
            include=["datetime64", "datetime64[ns]"]
        ).columns.tolist()

        if len(date_columns) >= 2:
            # Look for common date pairs
            for i, col1 in enumerate(date_columns):
                for col2 in date_columns[i + 1 :]:
                    if "start" in col1.lower() and "end" in col2.lower():
                        inconsistent = (df[col1] > df[col2]).sum()
                        consistency_issues += inconsistent
                        checks_performed.append(
                            {
                                "check": f"{col1} <= {col2}",
                                "violations": int(inconsistent),
                            }
                        )

        # Check 2: Numeric relationships (e.g., total = sum of parts)
        numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()

        # Example: check if 'total' equals sum of component columns
        if "total" in [col.lower() for col in numeric_columns]:
            total_col = [col for col in numeric_columns if col.lower() == "total"][0]
            component_cols = [
                col for col in numeric_columns if col != total_col and "part" in col.lower()
            ]

            if component_cols:
                calculated_total = df[component_cols].sum(axis=1)
                inconsistent = (abs(df[total_col] - calculated_total) > 0.01).sum()
                consistency_issues += inconsistent
                checks_performed.append(
                    {
                        "check": f"{total_col} = sum({component_cols})",
                        "violations": int(inconsistent),
                    }
                )

        # Check 3: Duplicate rows (already checked in uniqueness, but affects consistency)
        duplicate_rows = df.duplicated().sum()
        consistency_issues += duplicate_rows
        checks_performed.append(
            {"check": "No duplicate rows", "violations": int(duplicate_rows)}
        )

        consistency_score = (
            1.0 - (consistency_issues / total_rows) if total_rows > 0 else 1.0
        )
        threshold = self.thresholds[QualityDimension.CONSISTENCY]

        return QualityCheckResult(
            dimension=QualityDimension.CONSISTENCY,
            score=consistency_score,
            passed=consistency_score >= threshold,
            threshold=threshold,
            details={
                "total_rows": total_rows,
                "consistency_issues": int(consistency_issues),
                "issue_percentage": float(consistency_issues / total_rows)
                if total_rows > 0
                else 0.0,
                "checks_performed": checks_performed,
            },
            checked_at=datetime.utcnow(),
        )

    def run_all_checks(self, df: pd.DataFrame) -> dict[str, Any]:
        """Run all quality checks and return comprehensive results.

        WHY: Single entry point for complete quality validation
        - Runs all 6 quality dimensions
        - Provides overall quality score
        - Compatible with existing API interface

        Args:
            df: DataFrame to validate

        Returns:
            Dictionary with all quality check results
        """
        logger.info(f"Running all quality checks on dataset ({len(df)} rows, {len(df.columns)} columns)")

        # Run all dimension checks
        completeness = self.check_completeness(df)
        uniqueness = self.check_uniqueness(df)
        timeliness = self.check_timeliness(df)
        validity = self.check_validity(df)
        accuracy = self.check_accuracy(df)
        consistency = self.check_consistency(df)

        # Calculate overall score (weighted average)
        overall_score = (
            completeness.score * 0.25
            + uniqueness.score * 0.15
            + timeliness.score * 0.10
            + validity.score * 0.20
            + accuracy.score * 0.15
            + consistency.score * 0.15
        )

        # Determine overall pass/fail
        all_passed = all(
            [
                completeness.passed,
                uniqueness.passed,
                timeliness.passed,
                validity.passed,
                accuracy.passed,
                consistency.passed,
            ]
        )

        results = {
            "overall_score": float(overall_score),
            "overall_passed": all_passed,
            "dimensions": {
                "completeness": {
                    "score": float(completeness.score),
                    "passed": completeness.passed,
                    "threshold": completeness.threshold,
                    "details": completeness.details,
                },
                "uniqueness": {
                    "score": float(uniqueness.score),
                    "passed": uniqueness.passed,
                    "threshold": uniqueness.threshold,
                    "details": uniqueness.details,
                },
                "timeliness": {
                    "score": float(timeliness.score),
                    "passed": timeliness.passed,
                    "threshold": timeliness.threshold,
                    "details": timeliness.details,
                },
                "validity": {
                    "score": float(validity.score),
                    "passed": validity.passed,
                    "threshold": validity.threshold,
                    "details": validity.details,
                },
                "accuracy": {
                    "score": float(accuracy.score),
                    "passed": accuracy.passed,
                    "threshold": accuracy.threshold,
                    "details": accuracy.details,
                },
                "consistency": {
                    "score": float(consistency.score),
                    "passed": consistency.passed,
                    "threshold": consistency.threshold,
                    "details": consistency.details,
                },
            },
            "checked_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Quality checks complete: overall score {overall_score:.2%}, "
            f"passed: {all_passed}"
        )

        return results

    def check_dataframe(self, df: pd.DataFrame) -> dict[str, Any]:
        """Check dataframe quality (compatible with SimpleQualityChecker interface).

        WHY: Maintains backward compatibility with existing API

        Args:
            df: DataFrame to check

        Returns:
            Dictionary with quality metrics in compatible format
        """
        all_results = self.run_all_checks(df)

        # Extract dimension scores for backward compatibility
        dimensions = all_results["dimensions"]

        return {
            "completeness_score": dimensions["completeness"]["score"],
            "validity_score": dimensions["validity"]["score"],
            "consistency_score": dimensions["consistency"]["score"],
            "overall_score": all_results["overall_score"],
            "details": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "total_cells": len(df) * len(df.columns),
                "all_dimensions": all_results["dimensions"],
            },
        }
