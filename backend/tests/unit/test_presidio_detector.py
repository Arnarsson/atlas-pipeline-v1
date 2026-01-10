"""Unit tests for Presidio PII Detector.

WHY: Validate Week 3 PII detection upgrade
- Test Presidio detection accuracy
- Test Danish CPR recognizer
- Test confidence scoring
- Test anonymization strategies
"""

import pytest
import pandas as pd

try:
    from app.pipeline.pii.presidio_detector import (
        PresidioPIIDetector,
        PIIDetectionResult,
        PIIDetectionError,
    )

    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason="Presidio dependencies not installed")


@pytest.fixture
def pii_detector():
    """Fixture for PII detector instance."""
    if not PRESIDIO_AVAILABLE:
        return None
    return PresidioPIIDetector(languages=["en"], confidence_threshold=0.7)


@pytest.fixture
def sample_data_with_pii():
    """Sample data containing various PII types."""
    return pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C003"],
            "name": ["John Smith", "Jane Doe", "Bob Johnson"],
            "email": ["john@example.com", "jane@test.com", "bob@demo.com"],
            "phone": ["+1-555-0001", "+1-555-0002", "+1-555-0003"],
            "notes": [
                "Customer called",
                "Email sent to jane@test.com",
                "Follow up needed",
            ],
        }
    )


@pytest.fixture
def sample_data_no_pii():
    """Sample data without PII."""
    return pd.DataFrame(
        {
            "product_id": ["P001", "P002", "P003"],
            "category": ["Electronics", "Clothing", "Books"],
            "price": [99.99, 49.99, 19.99],
            "quantity": [10, 25, 50],
        }
    )


@pytest.fixture
def sample_danish_data():
    """Sample data with Danish PII (CPR numbers)."""
    return pd.DataFrame(
        {
            "navn": ["Anders Jensen", "Maria Nielsen", "Peter Hansen"],
            "cpr": ["010190-1234", "150585-5678", "220375-9012"],
            "email": ["anders@example.dk", "maria@test.dk", "peter@demo.dk"],
        }
    )


@pytest.mark.skipif(not PRESIDIO_AVAILABLE, reason="Presidio not installed")
class TestPresidioPIIDetector:
    """Test suite for PresidioPIIDetector."""

    def test_detector_initialization(self, pii_detector):
        """Test that detector initializes correctly."""
        assert pii_detector is not None
        assert pii_detector.confidence_threshold == 0.7
        assert "en" in pii_detector.languages

    def test_detect_email_addresses(self, pii_detector, sample_data_with_pii):
        """Test detection of email addresses."""
        results = pii_detector.detect_pii_in_dataframe(
            sample_data_with_pii, columns_to_scan=["email"]
        )

        # Should detect EMAIL_ADDRESS entities
        email_results = [r for r in results if r.pii_type == "EMAIL_ADDRESS"]
        assert len(email_results) > 0
        assert email_results[0].instances_found == 3
        assert all(score >= 0.7 for score in email_results[0].confidence_scores)

    def test_detect_phone_numbers(self, pii_detector, sample_data_with_pii):
        """Test detection of phone numbers."""
        results = pii_detector.detect_pii_in_dataframe(
            sample_data_with_pii, columns_to_scan=["phone"]
        )

        # Should detect PHONE_NUMBER entities
        phone_results = [r for r in results if r.pii_type == "PHONE_NUMBER"]
        assert len(phone_results) > 0
        assert phone_results[0].instances_found == 3

    def test_detect_person_names(self, pii_detector, sample_data_with_pii):
        """Test detection of person names."""
        results = pii_detector.detect_pii_in_dataframe(
            sample_data_with_pii, columns_to_scan=["name"]
        )

        # Should detect PERSON entities
        person_results = [r for r in results if r.pii_type == "PERSON"]
        assert len(person_results) > 0
        assert person_results[0].instances_found == 3

    def test_detect_pii_in_text_columns(self, pii_detector, sample_data_with_pii):
        """Test detection of PII embedded in text columns."""
        results = pii_detector.detect_pii_in_dataframe(
            sample_data_with_pii, columns_to_scan=["notes"]
        )

        # Should detect email in notes column
        email_in_notes = [r for r in results if r.pii_type == "EMAIL_ADDRESS"]
        assert len(email_in_notes) > 0

    def test_no_pii_detected(self, pii_detector, sample_data_no_pii):
        """Test that no PII is detected in clean data."""
        results = pii_detector.detect_pii_in_dataframe(sample_data_no_pii)

        assert len(results) == 0

    def test_confidence_scores(self, pii_detector, sample_data_with_pii):
        """Test that confidence scores are within valid range."""
        results = pii_detector.detect_pii_in_dataframe(
            sample_data_with_pii, columns_to_scan=["email"]
        )

        for result in results:
            assert all(0.0 <= score <= 1.0 for score in result.confidence_scores)
            assert all(
                score >= pii_detector.confidence_threshold
                for score in result.confidence_scores
            )

    def test_sample_values_masked(self, pii_detector, sample_data_with_pii):
        """Test that sample values are masked."""
        results = pii_detector.detect_pii_in_dataframe(
            sample_data_with_pii, columns_to_scan=["email"]
        )

        for result in results:
            for sample in result.sample_values:
                # Masked values should contain asterisks
                assert "*" in sample or "MASKED" in sample

    def test_anonymize_hash_strategy(self, pii_detector, sample_data_with_pii):
        """Test hash anonymization strategy."""
        detection_results = pii_detector.detect_pii_in_dataframe(
            sample_data_with_pii, columns_to_scan=["email"]
        )

        anonymized_df = pii_detector.anonymize_dataframe(
            sample_data_with_pii, detection_results, strategy="hash"
        )

        # Emails should be hashed
        assert not any(
            "@" in str(email) for email in anonymized_df["email"] if pd.notna(email)
        )

    def test_anonymize_mask_strategy(self, pii_detector, sample_data_with_pii):
        """Test mask anonymization strategy."""
        detection_results = pii_detector.detect_pii_in_dataframe(
            sample_data_with_pii, columns_to_scan=["email"]
        )

        anonymized_df = pii_detector.anonymize_dataframe(
            sample_data_with_pii, detection_results, strategy="mask"
        )

        # Emails should be masked with asterisks
        assert all(
            "*" in str(email) for email in anonymized_df["email"] if pd.notna(email)
        )

    def test_anonymize_redact_strategy(self, pii_detector, sample_data_with_pii):
        """Test redact anonymization strategy."""
        detection_results = pii_detector.detect_pii_in_dataframe(
            sample_data_with_pii, columns_to_scan=["email"]
        )

        anonymized_df = pii_detector.anonymize_dataframe(
            sample_data_with_pii, detection_results, strategy="redact"
        )

        # Emails should be redacted (empty or redacted marker)
        assert all(
            email == "" or pd.isna(email) or "REDACT" in str(email)
            for email in anonymized_df["email"]
        )

    def test_scan_dataframe_compatibility(self, pii_detector, sample_data_with_pii):
        """Test backward compatibility with SimplePIIDetector interface."""
        results = pii_detector.scan_dataframe(sample_data_with_pii)

        assert "findings" in results
        assert "total_pii_fields" in results
        assert "scanned_columns" in results
        assert "scanned_rows" in results

        assert results["scanned_rows"] == 3
        assert results["total_pii_fields"] > 0

        # Check findings format
        for finding in results["findings"]:
            assert "column" in finding
            assert "type" in finding
            assert "match_count" in finding
            assert "confidence" in finding


@pytest.mark.skipif(not PRESIDIO_AVAILABLE, reason="Presidio not installed")
class TestDanishCPRRecognizer:
    """Test suite for Danish CPR recognizer."""

    def test_detect_danish_cpr_with_hyphen(self):
        """Test detection of CPR with hyphen format."""
        detector = PresidioPIIDetector(languages=["da"], confidence_threshold=0.7)

        df = pd.DataFrame({"cpr": ["010190-1234", "150585-5678", "220375-9012"]})

        results = detector.detect_pii_in_dataframe(df, columns_to_scan=["cpr"])

        # Should detect DK_CPR entities
        cpr_results = [r for r in results if r.pii_type == "DK_CPR"]
        assert len(cpr_results) > 0
        assert cpr_results[0].instances_found == 3

    def test_detect_danish_cpr_without_hyphen(self):
        """Test detection of CPR without hyphen format."""
        detector = PresidioPIIDetector(languages=["da"], confidence_threshold=0.7)

        df = pd.DataFrame({"cpr": ["0101901234", "1505855678", "2203759012"]})

        results = detector.detect_pii_in_dataframe(df, columns_to_scan=["cpr"])

        # Should detect DK_CPR entities
        cpr_results = [r for r in results if r.pii_type == "DK_CPR"]
        assert len(cpr_results) > 0


@pytest.mark.skipif(not PRESIDIO_AVAILABLE, reason="Presidio not installed")
class TestPIIDetectionResult:
    """Test suite for PIIDetectionResult dataclass."""

    def test_result_creation(self):
        """Test PIIDetectionResult creation."""
        from datetime import datetime

        result = PIIDetectionResult(
            column_name="email",
            pii_type="EMAIL_ADDRESS",
            instances_found=5,
            confidence_scores=[0.9, 0.85, 0.92],
            sample_values=["j***@example.com", "a***@test.com", "b***@demo.com"],
            detected_at=datetime.utcnow(),
        )

        assert result.column_name == "email"
        assert result.pii_type == "EMAIL_ADDRESS"
        assert result.instances_found == 5
        assert len(result.confidence_scores) == 3
        assert len(result.sample_values) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
