"""Simple data quality checker."""

from typing import Any

import pandas as pd


class SimpleQualityChecker:
    """Simple data quality checker with basic validations."""

    def check_dataframe(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Check data quality of a dataframe.

        Args:
            df: Pandas dataframe to check

        Returns:
            Dictionary with quality metrics
        """
        total_cells = len(df) * len(df.columns)
        total_rows = len(df)
        total_columns = len(df.columns)

        # Completeness: Check for missing values
        missing_values = df.isnull().sum().sum()
        completeness_score = 1.0 - (missing_values / total_cells) if total_cells > 0 else 0.0

        # Validity: Check for valid data types and values
        validity_issues = 0
        column_validity = {}

        for column in df.columns:
            col_issues = 0

            # Check for empty strings
            if df[column].dtype == 'object':
                empty_strings = (df[column].astype(str).str.strip() == '').sum()
                col_issues += empty_strings

            # Check for negative values in numeric columns (example rule)
            if pd.api.types.is_numeric_dtype(df[column]):
                negative_count = (df[column] < 0).sum()
                # Negative values might be valid, so we just track them
                col_issues += 0  # Don't penalize for now

            column_validity[column] = {
                "issues": int(col_issues),
                "valid_percentage": float(1.0 - (col_issues / total_rows)) if total_rows > 0 else 1.0,
            }

            validity_issues += col_issues

        validity_score = 1.0 - (validity_issues / total_cells) if total_cells > 0 else 0.0

        # Consistency: Check for duplicates
        duplicate_rows = df.duplicated().sum()
        consistency_score = 1.0 - (duplicate_rows / total_rows) if total_rows > 0 else 1.0

        # Overall score (weighted average)
        overall_score = (
            completeness_score * 0.4 +
            validity_score * 0.4 +
            consistency_score * 0.2
        )

        # Detailed analysis per column
        column_details = {}
        for column in df.columns:
            col_data = df[column]

            column_details[column] = {
                "dtype": str(col_data.dtype),
                "missing_count": int(col_data.isnull().sum()),
                "missing_percentage": float(col_data.isnull().sum() / total_rows) if total_rows > 0 else 0.0,
                "unique_count": int(col_data.nunique()),
                "unique_percentage": float(col_data.nunique() / total_rows) if total_rows > 0 else 0.0,
            }

            # Add stats for numeric columns
            if pd.api.types.is_numeric_dtype(col_data):
                column_details[column].update({
                    "min": float(col_data.min()) if not col_data.isnull().all() else None,
                    "max": float(col_data.max()) if not col_data.isnull().all() else None,
                    "mean": float(col_data.mean()) if not col_data.isnull().all() else None,
                    "std": float(col_data.std()) if not col_data.isnull().all() else None,
                })

        return {
            "completeness_score": float(completeness_score),
            "validity_score": float(validity_score),
            "consistency_score": float(consistency_score),
            "overall_score": float(overall_score),
            "details": {
                "total_rows": total_rows,
                "total_columns": total_columns,
                "total_cells": total_cells,
                "missing_values": int(missing_values),
                "validity_issues": int(validity_issues),
                "duplicate_rows": int(duplicate_rows),
                "column_details": column_details,
            },
        }
