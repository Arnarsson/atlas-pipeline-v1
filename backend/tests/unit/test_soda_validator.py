"""Unit tests for Soda Core Quality Validator.

WHY: Validate Week 3 quality framework upgrade
- Test all 6 quality dimensions
- Test threshold validation
- Test detailed reporting
- Test backward compatibility
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta

try:
    from app.pipeline.quality.soda_validator import (
        SodaQualityValidator,
        QualityDimension,
        QualityCheckResult,
    )

    SODA_AVAILABLE = True
except ImportError:
    SODA_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason="Soda Core dependencies not installed")


@pytest.fixture
def quality_validator():
    """Fixture for quality validator instance."""
    if not SODA_AVAILABLE:
        return None
    return SodaQualityValidator()


@pytest.fixture
def perfect_data():
    """Sample data with perfect quality."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
            "email": [
                "alice@example.com",
                "bob@example.com",
                "charlie@example.com",
                "david@example.com",
                "eve@example.com",
            ],
            "age": [25, 30, 35, 40, 45],
            "created_at": [
                datetime.utcnow() - timedelta(days=i) for i in range(5)
            ],
        }
    )


@pytest.fixture
def data_with_issues():
    """Sample data with quality issues."""
    return pd.DataFrame(
        {
            "id": [1, 2, 2, 4, 5],  # Duplicate ID
            "name": ["Alice", None, "Charlie", "", "Eve"],  # Missing and empty
            "email": [
                "alice@example.com",
                "invalid-email",
                "charlie@example.com",
                None,
                "eve@example.com",
            ],
            "age": [25, -5, 35, 200, 45],  # Negative and outlier
            "score": [95, 88, float("inf"), 92, 87],  # Invalid inf value
        }
    )


@pytest.fixture
def data_with_old_dates():
    """Sample data with stale dates."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "created_at": [
                datetime.utcnow() - timedelta(days=30),  # Old
                datetime.utcnow() - timedelta(days=15),  # Old
                datetime.utcnow() - timedelta(days=3),  # Recent
            ],
        }
    )


@pytest.mark.skipif(not SODA_AVAILABLE, reason="Soda Core not installed")
class TestSodaQualityValidator:
    """Test suite for SodaQualityValidator."""

    def test_validator_initialization(self, quality_validator):
        """Test that validator initializes with correct thresholds."""
        assert quality_validator is not None
        assert quality_validator.thresholds[QualityDimension.COMPLETENESS] == 0.95
        assert quality_validator.thresholds[QualityDimension.UNIQUENESS] == 0.98
        assert quality_validator.thresholds[QualityDimension.VALIDITY] == 0.90

    def test_custom_thresholds(self):
        """Test initialization with custom thresholds."""
        validator = SodaQualityValidator(
            completeness_threshold=0.90,
            uniqueness_threshold=0.95,
            validity_threshold=0.85,
        )

        assert validator.thresholds[QualityDimension.COMPLETENESS] == 0.90
        assert validator.thresholds[QualityDimension.UNIQUENESS] == 0.95
        assert validator.thresholds[QualityDimension.VALIDITY] == 0.85


@pytest.mark.skipif(not SODA_AVAILABLE, reason="Soda Core not installed")
class TestCompletenessCheck:
    """Test suite for completeness dimension."""

    def test_perfect_completeness(self, quality_validator, perfect_data):
        """Test completeness with no missing values."""
        result = quality_validator.check_completeness(perfect_data)

        assert result.dimension == QualityDimension.COMPLETENESS
        assert result.score == 1.0
        assert result.passed is True
        assert result.details["missing_values"] == 0

    def test_completeness_with_missing(self, quality_validator, data_with_issues):
        """Test completeness with missing values."""
        result = quality_validator.check_completeness(data_with_issues)

        assert result.dimension == QualityDimension.COMPLETENESS
        assert result.score < 1.0
        assert result.details["missing_values"] > 0

        # Check per-column completeness
        assert "column_completeness" in result.details
        assert "name" in result.details["column_completeness"]

    def test_completeness_threshold(self, quality_validator):
        """Test completeness threshold checking."""
        # Create data with 90% completeness
        df = pd.DataFrame({"col1": [1, 2, 3, 4, 5, None, None, None, None, 10]})

        result = quality_validator.check_completeness(df)

        # 80% complete (8/10), below 95% threshold
        assert result.score == 0.8
        assert result.passed is False  # Below 95% threshold


@pytest.mark.skipif(not SODA_AVAILABLE, reason="Soda Core not installed")
class TestUniquenessCheck:
    """Test suite for uniqueness dimension."""

    def test_perfect_uniqueness(self, quality_validator, perfect_data):
        """Test uniqueness with no duplicates."""
        result = quality_validator.check_uniqueness(perfect_data)

        assert result.dimension == QualityDimension.UNIQUENESS
        assert result.score == 1.0
        assert result.passed is True
        assert result.details["duplicate_rows"] == 0

    def test_uniqueness_with_duplicates(self, quality_validator, data_with_issues):
        """Test uniqueness with duplicate rows."""
        result = quality_validator.check_uniqueness(data_with_issues)

        assert result.dimension == QualityDimension.UNIQUENESS
        assert result.score < 1.0
        assert result.details["duplicate_rows"] > 0

    def test_column_uniqueness(self, quality_validator, data_with_issues):
        """Test per-column uniqueness analysis."""
        result = quality_validator.check_uniqueness(data_with_issues)

        assert "column_uniqueness" in result.details
        assert "id" in result.details["column_uniqueness"]

        # ID column has duplicate (2 appears twice)
        id_uniqueness = result.details["column_uniqueness"]["id"]
        assert id_uniqueness["duplicate_count"] > 0


@pytest.mark.skipif(not SODA_AVAILABLE, reason="Soda Core not installed")
class TestTimelinessCheck:
    """Test suite for timeliness dimension."""

    def test_timeliness_with_recent_dates(self, quality_validator, perfect_data):
        """Test timeliness with recent dates."""
        result = quality_validator.check_timeliness(perfect_data)

        assert result.dimension == QualityDimension.TIMELINESS
        assert result.score >= 0.8  # Most data is recent
        assert "column_timeliness" in result.details

    def test_timeliness_with_old_dates(
        self, quality_validator, data_with_old_dates
    ):
        """Test timeliness with stale dates."""
        result = quality_validator.check_timeliness(data_with_old_dates)

        assert result.dimension == QualityDimension.TIMELINESS
        # 2/3 dates are older than 7 days
        assert result.score < 1.0

    def test_timeliness_no_date_columns(self, quality_validator):
        """Test timeliness when no date columns exist."""
        df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})

        result = quality_validator.check_timeliness(df)

        # Should pass by default when no date columns
        assert result.score == 1.0
        assert result.passed is True
        assert "No date columns found" in result.details.get("message", "")


@pytest.mark.skipif(not SODA_AVAILABLE, reason="Soda Core not installed")
class TestValidityCheck:
    """Test suite for validity dimension."""

    def test_perfect_validity(self, quality_validator, perfect_data):
        """Test validity with valid data."""
        result = quality_validator.check_validity(perfect_data)

        assert result.dimension == QualityDimension.VALIDITY
        assert result.score >= 0.9
        assert result.passed is True

    def test_validity_with_invalid(self, quality_validator, data_with_issues):
        """Test validity with invalid values."""
        result = quality_validator.check_validity(data_with_issues)

        assert result.dimension == QualityDimension.VALIDITY
        assert result.score < 1.0
        assert result.details["invalid_count"] > 0

        # Check column validity
        assert "column_validity" in result.details

    def test_validity_empty_strings(self, quality_validator):
        """Test validity detection of empty strings."""
        df = pd.DataFrame({"name": ["Alice", "Bob", "", "  ", "Charlie"]})

        result = quality_validator.check_validity(df)

        # Should detect empty and whitespace-only strings
        assert result.details["invalid_count"] >= 2


@pytest.mark.skipif(not SODA_AVAILABLE, reason="Soda Core not installed")
class TestAccuracyCheck:
    """Test suite for accuracy dimension."""

    def test_perfect_accuracy(self, quality_validator, perfect_data):
        """Test accuracy with normal data."""
        result = quality_validator.check_accuracy(perfect_data)

        assert result.dimension == QualityDimension.ACCURACY
        assert result.score >= 0.9
        assert result.passed is True

    def test_accuracy_with_outliers(self, quality_validator, data_with_issues):
        """Test accuracy with statistical outliers."""
        result = quality_validator.check_accuracy(data_with_issues)

        assert result.dimension == QualityDimension.ACCURACY
        assert "column_accuracy" in result.details

        # Age column has outliers (-5, 200)
        if "age" in result.details["column_accuracy"]:
            age_accuracy = result.details["column_accuracy"]["age"]
            assert age_accuracy["outlier_count"] > 0

    def test_accuracy_numeric_outlier_detection(self, quality_validator):
        """Test outlier detection using IQR method."""
        # Create data with clear outlier
        df = pd.DataFrame({"value": [10, 12, 11, 13, 10, 12, 100]})  # 100 is outlier

        result = quality_validator.check_accuracy(df)

        assert "column_accuracy" in result.details
        value_accuracy = result.details["column_accuracy"]["value"]
        assert value_accuracy["outlier_count"] >= 1


@pytest.mark.skipif(not SODA_AVAILABLE, reason="Soda Core not installed")
class TestConsistencyCheck:
    """Test suite for consistency dimension."""

    def test_perfect_consistency(self, quality_validator, perfect_data):
        """Test consistency with consistent data."""
        result = quality_validator.check_consistency(perfect_data)

        assert result.dimension == QualityDimension.CONSISTENCY
        assert result.score >= 0.9
        assert result.passed is True

    def test_consistency_with_duplicates(self, quality_validator, data_with_issues):
        """Test consistency with duplicate rows."""
        result = quality_validator.check_consistency(data_with_issues)

        assert result.dimension == QualityDimension.CONSISTENCY
        assert result.score < 1.0
        assert "checks_performed" in result.details


@pytest.mark.skipif(not SODA_AVAILABLE, reason="Soda Core not installed")
class TestRunAllChecks:
    """Test suite for comprehensive quality validation."""

    def test_run_all_checks_perfect_data(self, quality_validator, perfect_data):
        """Test running all checks on perfect data."""
        results = quality_validator.run_all_checks(perfect_data)

        assert "overall_score" in results
        assert "overall_passed" in results
        assert "dimensions" in results

        # All 6 dimensions should be present
        assert len(results["dimensions"]) == 6
        assert "completeness" in results["dimensions"]
        assert "uniqueness" in results["dimensions"]
        assert "timeliness" in results["dimensions"]
        assert "validity" in results["dimensions"]
        assert "accuracy" in results["dimensions"]
        assert "consistency" in results["dimensions"]

        # Perfect data should have high overall score
        assert results["overall_score"] >= 0.9
        assert results["overall_passed"] is True

    def test_run_all_checks_problematic_data(
        self, quality_validator, data_with_issues
    ):
        """Test running all checks on problematic data."""
        results = quality_validator.run_all_checks(data_with_issues)

        # Should detect quality issues
        assert results["overall_score"] < 1.0

        # Check that individual dimensions are reported
        for dimension in results["dimensions"].values():
            assert "score" in dimension
            assert "passed" in dimension
            assert "threshold" in dimension
            assert "details" in dimension

    def test_check_dataframe_compatibility(self, quality_validator, perfect_data):
        """Test backward compatibility with SimpleQualityChecker interface."""
        results = quality_validator.check_dataframe(perfect_data)

        # Should have backward-compatible keys
        assert "completeness_score" in results
        assert "validity_score" in results
        assert "consistency_score" in results
        assert "overall_score" in results
        assert "details" in results

        # Details should contain all dimensions
        assert "all_dimensions" in results["details"]

    def test_weighted_scoring(self, quality_validator):
        """Test that overall score uses correct weighted average."""
        # Create data with known dimension scores
        df = pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "name": ["A", "B", "C", "D", "E"],
                "value": [10, 20, 30, 40, 50],
            }
        )

        results = quality_validator.run_all_checks(df)

        # Weighted average formula:
        # completeness * 0.25 + uniqueness * 0.15 + timeliness * 0.10 +
        # validity * 0.20 + accuracy * 0.15 + consistency * 0.15

        dims = results["dimensions"]
        expected_score = (
            dims["completeness"]["score"] * 0.25
            + dims["uniqueness"]["score"] * 0.15
            + dims["timeliness"]["score"] * 0.10
            + dims["validity"]["score"] * 0.20
            + dims["accuracy"]["score"] * 0.15
            + dims["consistency"]["score"] * 0.15
        )

        assert abs(results["overall_score"] - expected_score) < 0.01


@pytest.mark.skipif(not SODA_AVAILABLE, reason="Soda Core not installed")
class TestQualityCheckResult:
    """Test suite for QualityCheckResult dataclass."""

    def test_result_creation(self):
        """Test QualityCheckResult creation."""
        result = QualityCheckResult(
            dimension=QualityDimension.COMPLETENESS,
            score=0.95,
            passed=True,
            threshold=0.90,
            details={"missing_values": 5},
            checked_at=datetime.utcnow(),
        )

        assert result.dimension == QualityDimension.COMPLETENESS
        assert result.score == 0.95
        assert result.passed is True
        assert result.threshold == 0.90
        assert result.details["missing_values"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
