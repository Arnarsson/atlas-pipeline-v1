"""Simple PII detector using regex patterns."""

import re
from typing import Any

import pandas as pd


class SimplePIIDetector:
    """Simple regex-based PII detector for common PII types."""

    def __init__(self):
        """Initialize PII patterns."""
        self.patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            "zipcode": r'\b\d{5}(?:-\d{4})?\b',
        }

    def scan_dataframe(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Scan a dataframe for PII.

        Args:
            df: Pandas dataframe to scan

        Returns:
            Dictionary with PII findings
        """
        findings = []

        for column in df.columns:
            # Convert column to string for pattern matching
            column_str = df[column].astype(str)

            for pii_type, pattern in self.patterns.items():
                # Check if any value matches the pattern
                matches = column_str.str.contains(pattern, regex=True, na=False)

                if matches.any():
                    match_count = matches.sum()
                    sample_values = column_str[matches].head(3).tolist()

                    findings.append({
                        "column": column,
                        "type": pii_type,
                        "match_count": int(match_count),
                        "total_rows": len(df),
                        "percentage": float(match_count / len(df)),
                        "sample_values": [self._mask_value(v, pii_type) for v in sample_values],
                    })

        return {
            "findings": findings,
            "total_pii_fields": len(findings),
            "scanned_columns": len(df.columns),
            "scanned_rows": len(df),
        }

    def _mask_value(self, value: str, pii_type: str) -> str:
        """
        Mask a PII value for safe display.

        Args:
            value: The value to mask
            pii_type: Type of PII

        Returns:
            Masked value
        """
        if pii_type == "email":
            # Show first 2 chars and domain
            if "@" in value:
                local, domain = value.split("@")
                return f"{local[:2]}***@{domain}"
            return value[:2] + "***"

        elif pii_type == "phone":
            # Show last 4 digits
            digits = re.sub(r'\D', '', value)
            return f"***-***-{digits[-4:]}" if len(digits) >= 4 else "***"

        elif pii_type == "ssn":
            return "***-**-" + value[-4:]

        elif pii_type == "credit_card":
            digits = re.sub(r'\D', '', value)
            return f"****-****-****-{digits[-4:]}" if len(digits) >= 4 else "****"

        else:
            # Generic masking
            return value[:2] + "*" * (len(value) - 2) if len(value) > 2 else "***"
