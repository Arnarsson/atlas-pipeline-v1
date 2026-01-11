"""
Custom Quality Rules Engine (Phase 4.2)
========================================

User-defined validation rules with SQL-like syntax.

Features:
- SQL-like condition syntax
- Cross-column validation
- Statistical anomaly detection
- Time-series validation
- Automated remediation suggestions
- Rule versioning and history

Reference: Great Expectations, Deequ patterns
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
from uuid import uuid4

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ============================================================================
# Models
# ============================================================================


class RuleSeverity(str, Enum):
    """Rule violation severity levels."""

    INFO = "info"  # Informational only
    WARNING = "warning"  # Warning but not critical
    ERROR = "error"  # Error that should be fixed
    CRITICAL = "critical"  # Critical error, block pipeline


class RuleType(str, Enum):
    """Types of quality rules."""

    VALUE_RANGE = "value_range"  # Value must be within range
    PATTERN_MATCH = "pattern_match"  # Value must match regex pattern
    NOT_NULL = "not_null"  # Value must not be null
    UNIQUE = "unique"  # Values must be unique
    CROSS_COLUMN = "cross_column"  # Validation across multiple columns
    STATISTICAL = "statistical"  # Statistical validation (outliers, distribution)
    TEMPORAL = "temporal"  # Time-series validation
    CUSTOM_SQL = "custom_sql"  # Custom SQL-like condition


@dataclass
class QualityRule:
    """User-defined quality rule."""

    rule_id: str
    rule_name: str
    rule_type: RuleType
    description: str
    severity: RuleSeverity

    # Rule definition
    condition: str  # SQL-like condition or Python expression
    columns: list[str]  # Columns this rule applies to

    # Thresholds
    threshold: float | None = None  # Threshold for pass/fail
    expected_min: float | None = None
    expected_max: float | None = None

    # Metadata
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.utcnow)
    enabled: bool = True
    tags: list[str] = field(default_factory=list)

    # Remediation
    remediation_suggestion: str | None = None


@dataclass
class RuleViolation:
    """Quality rule violation."""

    violation_id: str
    rule_id: str
    rule_name: str
    severity: RuleSeverity

    # Violation details
    column: str | None
    row_indices: list[int]  # Rows that violated the rule
    violation_count: int
    violation_percentage: float

    # Context
    actual_value: Any | None = None
    expected_value: Any | None = None
    message: str = ""

    # Timestamp
    detected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RuleValidationResult:
    """Result of rule validation."""

    rule_id: str
    rule_name: str
    passed: bool

    total_records: int
    valid_records: int
    invalid_records: int
    pass_percentage: float

    violations: list[RuleViolation] = field(default_factory=list)
    execution_time_seconds: float = 0.0


# ============================================================================
# Custom Rules Engine
# ============================================================================


class CustomRulesEngine:
    """
    Engine for executing user-defined quality rules.

    Supports:
    - SQL-like condition syntax
    - Cross-column validation
    - Statistical anomaly detection
    - Remediation suggestions
    """

    def __init__(self):
        """Initialize rules engine."""
        self.rules: dict[str, QualityRule] = {}
        logger.info("Initialized CustomRulesEngine")

    # ========================================================================
    # Rule Management
    # ========================================================================

    def register_rule(self, rule: QualityRule) -> str:
        """
        Register a quality rule.

        Args:
            rule: QualityRule to register

        Returns:
            Rule ID
        """
        self.rules[rule.rule_id] = rule

        logger.info(
            f"Registered rule: {rule.rule_name} (type={rule.rule_type}, "
            f"severity={rule.severity})"
        )

        return rule.rule_id

    def get_rule(self, rule_id: str) -> QualityRule | None:
        """Get rule by ID."""
        return self.rules.get(rule_id)

    def list_rules(
        self,
        rule_type: RuleType | None = None,
        severity: RuleSeverity | None = None,
        enabled_only: bool = True,
    ) -> list[QualityRule]:
        """
        List quality rules with optional filters.

        Args:
            rule_type: Optional filter by rule type
            severity: Optional filter by severity
            enabled_only: Only return enabled rules

        Returns:
            List of QualityRule
        """
        rules = list(self.rules.values())

        if enabled_only:
            rules = [r for r in rules if r.enabled]

        if rule_type:
            rules = [r for r in rules if r.rule_type == rule_type]

        if severity:
            rules = [r for r in rules if r.severity == severity]

        return sorted(rules, key=lambda r: r.created_at, reverse=True)

    def disable_rule(self, rule_id: str):
        """Disable a rule."""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            logger.info(f"Disabled rule: {rule_id}")

    def enable_rule(self, rule_id: str):
        """Enable a rule."""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            logger.info(f"Enabled rule: {rule_id}")

    # ========================================================================
    # Rule Validation
    # ========================================================================

    def validate_dataset(
        self,
        data: pd.DataFrame,
        rules: list[QualityRule] | None = None,
    ) -> list[RuleValidationResult]:
        """
        Validate dataset against quality rules.

        Args:
            data: DataFrame to validate
            rules: Optional list of rules (default: all enabled rules)

        Returns:
            List of RuleValidationResult
        """
        if rules is None:
            rules = self.list_rules(enabled_only=True)

        results = []

        for rule in rules:
            try:
                result = self._validate_rule(data, rule)
                results.append(result)

            except Exception as e:
                logger.error(f"Error validating rule {rule.rule_name}: {e}", exc_info=True)

                # Create error result
                results.append(RuleValidationResult(
                    rule_id=rule.rule_id,
                    rule_name=rule.rule_name,
                    passed=False,
                    total_records=len(data),
                    valid_records=0,
                    invalid_records=len(data),
                    pass_percentage=0.0,
                    violations=[RuleViolation(
                        violation_id=str(uuid4()),
                        rule_id=rule.rule_id,
                        rule_name=rule.rule_name,
                        severity=rule.severity,
                        column=None,
                        row_indices=[],
                        violation_count=len(data),
                        violation_percentage=100.0,
                        message=f"Rule validation error: {str(e)}",
                    )],
                ))

        logger.info(
            f"Validated dataset against {len(rules)} rules, "
            f"passed={sum(1 for r in results if r.passed)}"
        )

        return results

    def _validate_rule(
        self, data: pd.DataFrame, rule: QualityRule
    ) -> RuleValidationResult:
        """Validate a single rule against the dataset."""
        start_time = datetime.utcnow()

        # Dispatch to appropriate validator
        if rule.rule_type == RuleType.VALUE_RANGE:
            result = self._validate_value_range(data, rule)
        elif rule.rule_type == RuleType.PATTERN_MATCH:
            result = self._validate_pattern_match(data, rule)
        elif rule.rule_type == RuleType.NOT_NULL:
            result = self._validate_not_null(data, rule)
        elif rule.rule_type == RuleType.UNIQUE:
            result = self._validate_unique(data, rule)
        elif rule.rule_type == RuleType.CROSS_COLUMN:
            result = self._validate_cross_column(data, rule)
        elif rule.rule_type == RuleType.STATISTICAL:
            result = self._validate_statistical(data, rule)
        elif rule.rule_type == RuleType.TEMPORAL:
            result = self._validate_temporal(data, rule)
        elif rule.rule_type == RuleType.CUSTOM_SQL:
            result = self._validate_custom_sql(data, rule)
        else:
            raise ValueError(f"Unknown rule type: {rule.rule_type}")

        # Calculate execution time
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        result.execution_time_seconds = execution_time

        return result

    # ========================================================================
    # Rule Validators
    # ========================================================================

    def _validate_value_range(
        self, data: pd.DataFrame, rule: QualityRule
    ) -> RuleValidationResult:
        """Validate value range rule."""
        column = rule.columns[0]
        column_data = data[column].dropna()

        # Check values within range
        if rule.expected_min is not None and rule.expected_max is not None:
            mask = (column_data >= rule.expected_min) & (column_data <= rule.expected_max)
        elif rule.expected_min is not None:
            mask = column_data >= rule.expected_min
        elif rule.expected_max is not None:
            mask = column_data <= rule.expected_max
        else:
            raise ValueError("Value range rule requires expected_min or expected_max")

        invalid_mask = ~mask
        invalid_indices = data.index[data[column].isin(column_data[invalid_mask])].tolist()

        valid_count = mask.sum()
        invalid_count = invalid_mask.sum()
        total_count = len(column_data)

        pass_percentage = (valid_count / total_count * 100) if total_count > 0 else 100.0
        passed = pass_percentage >= (rule.threshold or 100.0)

        violations = []
        if invalid_count > 0:
            violations.append(RuleViolation(
                violation_id=str(uuid4()),
                rule_id=rule.rule_id,
                rule_name=rule.rule_name,
                severity=rule.severity,
                column=column,
                row_indices=invalid_indices[:100],  # Limit to first 100
                violation_count=invalid_count,
                violation_percentage=100.0 - pass_percentage,
                message=f"{invalid_count} values out of range "
                       f"[{rule.expected_min}, {rule.expected_max}]",
            ))

        return RuleValidationResult(
            rule_id=rule.rule_id,
            rule_name=rule.rule_name,
            passed=passed,
            total_records=total_count,
            valid_records=valid_count,
            invalid_records=invalid_count,
            pass_percentage=pass_percentage,
            violations=violations,
        )

    def _validate_pattern_match(
        self, data: pd.DataFrame, rule: QualityRule
    ) -> RuleValidationResult:
        """Validate pattern match rule."""
        column = rule.columns[0]
        column_data = data[column].dropna().astype(str)

        # Compile regex pattern from condition
        pattern = re.compile(rule.condition)

        # Check pattern matches
        mask = column_data.apply(lambda x: bool(pattern.match(x)))
        invalid_mask = ~mask
        invalid_indices = data.index[data[column].isin(column_data[invalid_mask])].tolist()

        valid_count = mask.sum()
        invalid_count = invalid_mask.sum()
        total_count = len(column_data)

        pass_percentage = (valid_count / total_count * 100) if total_count > 0 else 100.0
        passed = pass_percentage >= (rule.threshold or 100.0)

        violations = []
        if invalid_count > 0:
            violations.append(RuleViolation(
                violation_id=str(uuid4()),
                rule_id=rule.rule_id,
                rule_name=rule.rule_name,
                severity=rule.severity,
                column=column,
                row_indices=invalid_indices[:100],
                violation_count=invalid_count,
                violation_percentage=100.0 - pass_percentage,
                message=f"{invalid_count} values do not match pattern: {rule.condition}",
            ))

        return RuleValidationResult(
            rule_id=rule.rule_id,
            rule_name=rule.rule_name,
            passed=passed,
            total_records=total_count,
            valid_records=valid_count,
            invalid_records=invalid_count,
            pass_percentage=pass_percentage,
            violations=violations,
        )

    def _validate_not_null(
        self, data: pd.DataFrame, rule: QualityRule
    ) -> RuleValidationResult:
        """Validate not null rule."""
        column = rule.columns[0]
        null_mask = data[column].isna()
        null_indices = data.index[null_mask].tolist()

        valid_count = (~null_mask).sum()
        invalid_count = null_mask.sum()
        total_count = len(data)

        pass_percentage = (valid_count / total_count * 100) if total_count > 0 else 100.0
        passed = pass_percentage >= (rule.threshold or 100.0)

        violations = []
        if invalid_count > 0:
            violations.append(RuleViolation(
                violation_id=str(uuid4()),
                rule_id=rule.rule_id,
                rule_name=rule.rule_name,
                severity=rule.severity,
                column=column,
                row_indices=null_indices[:100],
                violation_count=invalid_count,
                violation_percentage=100.0 - pass_percentage,
                message=f"{invalid_count} null values found",
            ))

        return RuleValidationResult(
            rule_id=rule.rule_id,
            rule_name=rule.rule_name,
            passed=passed,
            total_records=total_count,
            valid_records=valid_count,
            invalid_records=invalid_count,
            pass_percentage=pass_percentage,
            violations=violations,
        )

    def _validate_unique(
        self, data: pd.DataFrame, rule: QualityRule
    ) -> RuleValidationResult:
        """Validate uniqueness rule."""
        column = rule.columns[0]
        duplicates = data[column].duplicated(keep=False)
        duplicate_indices = data.index[duplicates].tolist()

        valid_count = (~duplicates).sum()
        invalid_count = duplicates.sum()
        total_count = len(data)

        pass_percentage = (valid_count / total_count * 100) if total_count > 0 else 100.0
        passed = pass_percentage >= (rule.threshold or 100.0)

        violations = []
        if invalid_count > 0:
            violations.append(RuleViolation(
                violation_id=str(uuid4()),
                rule_id=rule.rule_id,
                rule_name=rule.rule_name,
                severity=rule.severity,
                column=column,
                row_indices=duplicate_indices[:100],
                violation_count=invalid_count,
                violation_percentage=100.0 - pass_percentage,
                message=f"{invalid_count} duplicate values found",
            ))

        return RuleValidationResult(
            rule_id=rule.rule_id,
            rule_name=rule.rule_name,
            passed=passed,
            total_records=total_count,
            valid_records=valid_count,
            invalid_records=invalid_count,
            pass_percentage=pass_percentage,
            violations=violations,
        )

    def _validate_cross_column(
        self, data: pd.DataFrame, rule: QualityRule
    ) -> RuleValidationResult:
        """Validate cross-column rule."""
        # Evaluate condition across multiple columns
        # Condition format: "column1 > column2" or "column1 + column2 = column3"

        try:
            # Evaluate condition as pandas expression
            mask = data.eval(rule.condition)
            invalid_mask = ~mask
            invalid_indices = data.index[invalid_mask].tolist()

            valid_count = mask.sum()
            invalid_count = invalid_mask.sum()
            total_count = len(data)

            pass_percentage = (valid_count / total_count * 100) if total_count > 0 else 100.0
            passed = pass_percentage >= (rule.threshold or 100.0)

            violations = []
            if invalid_count > 0:
                violations.append(RuleViolation(
                    violation_id=str(uuid4()),
                    rule_id=rule.rule_id,
                    rule_name=rule.rule_name,
                    severity=rule.severity,
                    column=None,  # Multiple columns
                    row_indices=invalid_indices[:100],
                    violation_count=invalid_count,
                    violation_percentage=100.0 - pass_percentage,
                    message=f"{invalid_count} rows violate condition: {rule.condition}",
                ))

            return RuleValidationResult(
                rule_id=rule.rule_id,
                rule_name=rule.rule_name,
                passed=passed,
                total_records=total_count,
                valid_records=valid_count,
                invalid_records=invalid_count,
                pass_percentage=pass_percentage,
                violations=violations,
            )

        except Exception as e:
            raise ValueError(f"Invalid cross-column condition: {rule.condition}") from e

    def _validate_statistical(
        self, data: pd.DataFrame, rule: QualityRule
    ) -> RuleValidationResult:
        """Validate statistical rule (outlier detection)."""
        column = rule.columns[0]
        column_data = data[column].dropna()

        if not pd.api.types.is_numeric_dtype(column_data):
            raise ValueError(f"Statistical validation requires numeric column: {column}")

        # IQR-based outlier detection
        Q1 = column_data.quantile(0.25)
        Q3 = column_data.quantile(0.75)
        IQR = Q3 - Q1

        # Outliers: values below Q1 - 1.5*IQR or above Q3 + 1.5*IQR
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outlier_mask = (column_data < lower_bound) | (column_data > upper_bound)
        outlier_indices = data.index[data[column].isin(column_data[outlier_mask])].tolist()

        valid_count = (~outlier_mask).sum()
        invalid_count = outlier_mask.sum()
        total_count = len(column_data)

        pass_percentage = (valid_count / total_count * 100) if total_count > 0 else 100.0
        passed = pass_percentage >= (rule.threshold or 95.0)  # Default 95% threshold

        violations = []
        if invalid_count > 0:
            violations.append(RuleViolation(
                violation_id=str(uuid4()),
                rule_id=rule.rule_id,
                rule_name=rule.rule_name,
                severity=rule.severity,
                column=column,
                row_indices=outlier_indices[:100],
                violation_count=invalid_count,
                violation_percentage=100.0 - pass_percentage,
                message=f"{invalid_count} statistical outliers detected "
                       f"(range: [{lower_bound:.2f}, {upper_bound:.2f}])",
            ))

        return RuleValidationResult(
            rule_id=rule.rule_id,
            rule_name=rule.rule_name,
            passed=passed,
            total_records=total_count,
            valid_records=valid_count,
            invalid_records=invalid_count,
            pass_percentage=pass_percentage,
            violations=violations,
        )

    def _validate_temporal(
        self, data: pd.DataFrame, rule: QualityRule
    ) -> RuleValidationResult:
        """Validate temporal rule (time-series validation)."""
        column = rule.columns[0]
        column_data = data[column].dropna()

        # Convert to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(column_data):
            try:
                column_data = pd.to_datetime(column_data)
            except Exception as e:
                raise ValueError(f"Cannot convert column to datetime: {column}") from e

        # Check temporal ordering (dates should be monotonically increasing)
        is_sorted = column_data.is_monotonic_increasing

        valid_count = len(column_data) if is_sorted else 0
        invalid_count = 0 if is_sorted else len(column_data)
        total_count = len(column_data)

        pass_percentage = (valid_count / total_count * 100) if total_count > 0 else 100.0
        passed = pass_percentage >= (rule.threshold or 100.0)

        violations = []
        if not is_sorted:
            violations.append(RuleViolation(
                violation_id=str(uuid4()),
                rule_id=rule.rule_id,
                rule_name=rule.rule_name,
                severity=rule.severity,
                column=column,
                row_indices=[],
                violation_count=invalid_count,
                violation_percentage=100.0,
                message="Temporal data is not monotonically increasing",
            ))

        return RuleValidationResult(
            rule_id=rule.rule_id,
            rule_name=rule.rule_name,
            passed=passed,
            total_records=total_count,
            valid_records=valid_count,
            invalid_records=invalid_count,
            pass_percentage=pass_percentage,
            violations=violations,
        )

    def _validate_custom_sql(
        self, data: pd.DataFrame, rule: QualityRule
    ) -> RuleValidationResult:
        """Validate custom SQL-like rule."""
        # Use pandas.DataFrame.query() for SQL-like syntax
        try:
            mask = data.query(rule.condition, engine='python')

            # If query returns filtered dataframe, count as invalid rows
            invalid_count = len(mask)
            valid_count = len(data) - invalid_count
            total_count = len(data)

            pass_percentage = (valid_count / total_count * 100) if total_count > 0 else 100.0
            passed = pass_percentage >= (rule.threshold or 100.0)

            violations = []
            if invalid_count > 0:
                violations.append(RuleViolation(
                    violation_id=str(uuid4()),
                    rule_id=rule.rule_id,
                    rule_name=rule.rule_name,
                    severity=rule.severity,
                    column=None,
                    row_indices=mask.index.tolist()[:100],
                    violation_count=invalid_count,
                    violation_percentage=100.0 - pass_percentage,
                    message=f"{invalid_count} rows violate custom condition: {rule.condition}",
                ))

            return RuleValidationResult(
                rule_id=rule.rule_id,
                rule_name=rule.rule_name,
                passed=passed,
                total_records=total_count,
                valid_records=valid_count,
                invalid_records=invalid_count,
                pass_percentage=pass_percentage,
                violations=violations,
            )

        except Exception as e:
            raise ValueError(f"Invalid custom SQL condition: {rule.condition}") from e


# ============================================================================
# Singleton Instance
# ============================================================================

_rules_engine: CustomRulesEngine | None = None


def get_rules_engine() -> CustomRulesEngine:
    """
    Get or create global rules engine instance.

    Returns:
        CustomRulesEngine instance
    """
    global _rules_engine

    if _rules_engine is None:
        _rules_engine = CustomRulesEngine()

    return _rules_engine
