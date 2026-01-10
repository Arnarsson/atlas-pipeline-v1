"""
Atlas Pipeline Integration: Soda Core Quality Checks
=====================================================

This example shows how to integrate:
1. Soda Core for data quality checks
2. YAML-based quality definitions
3. PostgreSQL for storing check results
4. Integration with Atlas pipeline layers

WHY THIS INTEGRATION:
- Soda Core provides declarative data quality checks (SQL-based)
- YAML configs make quality rules readable and version-controlled
- Automated quality gates prevent bad data from flowing downstream
- Historical quality metrics enable trend analysis and alerting

DEPENDENCIES:
pip install soda-core-postgres soda-core-scientific pandas sqlalchemy psycopg2-binary pyyaml
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import yaml
import json
import pandas as pd

# Soda Core imports
from soda.scan import Scan

# Database
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Float, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class QualityConfig:
    """
    WHY: Centralized configuration for Soda Core integration
    - data_source_name: Name for the data warehouse connection
    - checks_dir: Directory containing YAML quality checks
    - results_database: Where to store check results
    """
    data_source_name: str = "atlas_warehouse"
    warehouse_connection: str = "postgresql://user:password@localhost:5432/atlas_data"
    results_database: str = "postgresql://user:password@localhost:5432/atlas_quality"
    checks_dir: str = "quality_checks"

    # Quality thresholds
    # WHY: Define what constitutes "acceptable" quality
    min_completeness: float = 0.95  # 95% non-null
    max_duplicate_rate: float = 0.02  # 2% duplicates max
    min_validity: float = 0.98  # 98% valid values
    max_freshness_hours: int = 24  # Data must be < 24 hours old


# ============================================================================
# Database Models for Quality Results
# ============================================================================

Base = declarative_base()


class QualityCheckRun(Base):
    """
    WHY: Store quality check execution history
    - Enables tracking quality trends over time
    - Supports alerting on quality degradation
    - Provides audit trail for compliance
    """
    __tablename__ = "quality_check_runs"

    run_id = Column(String, primary_key=True)
    pipeline_run_id = Column(String, index=True)  # Link to pipeline execution
    table_name = Column(String, nullable=False, index=True)
    layer = Column(String, nullable=False)  # bronze, silver, or gold

    # Execution details
    scan_time = Column(DateTime, default=datetime.utcnow)
    execution_duration_seconds = Column(Float)

    # Overall results
    checks_total = Column(Integer)
    checks_passed = Column(Integer)
    checks_warned = Column(Integer)
    checks_failed = Column(Integer)
    overall_status = Column(String)  # pass, warn, fail

    # Detailed results
    check_results = Column(JSON)  # Full Soda scan results


class QualityMetric(Base):
    """
    WHY: Individual quality metric values over time
    - Enables time-series analysis of quality trends
    - Supports ML-based anomaly detection
    - Powers quality dashboards
    """
    __tablename__ = "quality_metrics"

    metric_id = Column(String, primary_key=True)
    run_id = Column(String, index=True)
    table_name = Column(String, nullable=False, index=True)
    check_name = Column(String, nullable=False)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float)
    passed = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.utcnow)


# WHY: Create quality results database
quality_engine = create_engine(QualityConfig().results_database)
Base.metadata.create_all(quality_engine)
QualitySessionLocal = sessionmaker(bind=quality_engine)


# ============================================================================
# Soda Core YAML Check Generators
# ============================================================================

class SodaCheckGenerator:
    """
    WHY: Generate Soda YAML checks programmatically
    - Standardizes check creation across tables
    - Enables dynamic check generation based on schema
    - Provides templates for common quality patterns
    """

    @staticmethod
    def generate_bronze_checks(table_name: str, columns: List[str]) -> str:
        """
        WHY: Bronze layer checks focus on raw data integrity
        - Ensure data is present
        - Check for obvious corruption
        - Verify expected schema

        Args:
            table_name: Name of bronze table
            columns: List of expected columns

        Returns:
            YAML string with quality checks
        """
        checks = {
            'checks for ' + table_name: [
                # WHY: Ensure table has data
                {
                    'row_count': {
                        'fail': {'when < 1': None}  # Must have at least 1 row
                    }
                },
                # WHY: Schema validation - ensure expected columns exist
                {
                    'schema': {
                        'warn': {
                            'when schema changes': None
                        },
                        'fail': {
                            'when required column missing': columns
                        }
                    }
                },
                # WHY: Check for duplicate records
                {
                    'duplicate_count': {
                        'warn': {'when > 0': None}
                    }
                },
                # WHY: Freshness check - data should be recent
                {
                    'freshness(created_at) < 24h': None
                }
            ]
        }

        # WHY: Add column-specific checks
        for col in columns:
            # Check for null values
            checks['checks for ' + table_name].append({
                f'missing_count({col})': {
                    'warn': {'when > 5%': None},
                    'fail': {'when > 10%': None}
                }
            })

        return yaml.dump(checks, sort_keys=False)

    @staticmethod
    def generate_silver_checks(
        table_name: str,
        pii_columns: List[str] = None,
        business_rules: Dict[str, Any] = None
    ) -> str:
        """
        WHY: Silver layer checks focus on data quality and compliance
        - Ensure PII is properly masked
        - Validate business rules
        - Check data quality metrics

        Args:
            table_name: Name of silver table
            pii_columns: Columns that should be anonymized
            business_rules: Custom business validation rules

        Returns:
            YAML string with quality checks
        """
        checks = {
            'checks for ' + table_name: [
                # WHY: Completeness - Silver should be cleaner than Bronze
                {
                    'row_count': {
                        'fail': {'when < 1': None}
                    }
                },
                # WHY: Ensure no duplicates in Silver
                {
                    'duplicate_count': {
                        'fail': {'when > 0': None}  # Stricter than Bronze
                    }
                },
                # WHY: Data quality score (composite metric)
                {
                    'missing_count': {
                        'fail': {'when > 5%': None}  # Max 5% missing values
                    }
                }
            ]
        }

        # WHY: PII masking validation
        if pii_columns:
            for col in pii_columns:
                # Check that PII columns don't contain plaintext patterns
                checks['checks for ' + table_name].append({
                    f'invalid_count({col})': {
                        'fail': {
                            # WHY: Hashed values should not match common PII patterns
                            'when contains @': None  # No email addresses
                        }
                    }
                })

        # WHY: Business rule validation
        if business_rules:
            for rule_name, rule_config in business_rules.items():
                checks['checks for ' + table_name].append({
                    rule_name: rule_config
                })

        return yaml.dump(checks, sort_keys=False)

    @staticmethod
    def generate_gold_checks(
        table_name: str,
        expected_metrics: List[str] = None,
        aggregation_rules: Dict[str, Any] = None
    ) -> str:
        """
        WHY: Gold layer checks focus on analytics quality
        - Ensure aggregations are correct
        - Validate business metrics
        - Check AI feature consistency

        Args:
            table_name: Name of gold table
            expected_metrics: List of expected metric columns
            aggregation_rules: Validation rules for aggregated data

        Returns:
            YAML string with quality checks
        """
        checks = {
            'checks for ' + table_name: [
                # WHY: Gold tables should always have data
                {
                    'row_count': {
                        'fail': {'when < 1': None}
                    }
                },
                # WHY: Aggregated data should have no duplicates
                {
                    'duplicate_count': {
                        'fail': {'when > 0': None}
                    }
                }
            ]
        }

        # WHY: Metric validation - ensure metrics exist and are reasonable
        if expected_metrics:
            for metric in expected_metrics:
                checks['checks for ' + table_name].extend([
                    # Check metric exists
                    {
                        f'missing_count({metric})': {
                            'fail': {'when > 0': None}
                        }
                    },
                    # Check for invalid values (NaN, Inf)
                    {
                        f'invalid_count({metric})': {
                            'fail': {'when > 0': None}
                        }
                    }
                ])

        # WHY: Custom aggregation validation
        if aggregation_rules:
            for rule_name, rule_config in aggregation_rules.items():
                checks['checks for ' + table_name].append({
                    rule_name: rule_config
                })

        return yaml.dump(checks, sort_keys=False)


# ============================================================================
# Quality Check Executor
# ============================================================================

class QualityCheckExecutor:
    """
    WHY: Execute Soda Core checks and store results
    - Runs checks against data warehouse
    - Parses results and stores in quality database
    - Provides pass/fail decisions for pipeline gates
    """

    def __init__(self, config: QualityConfig):
        self.config = config
        self.checks_dir = Path(config.checks_dir)
        self.checks_dir.mkdir(exist_ok=True)

        # WHY: Create Soda configuration file
        self._create_soda_config()

    def _create_soda_config(self):
        """
        WHY: Create Soda configuration file for data source connection
        - Defines connection to data warehouse
        - Used by all Soda scans
        """
        config_content = f"""
data_source atlas_warehouse:
  type: postgres
  connection:
    host: localhost
    port: 5432
    username: user
    password: password
    database: atlas_data
"""
        config_path = self.checks_dir / "configuration.yml"
        config_path.write_text(config_content)
        logger.info(f"Created Soda config at {config_path}")

    def run_quality_checks(
        self,
        table_name: str,
        layer: str,
        checks_yaml: str,
        pipeline_run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute quality checks using Soda Core.

        WHY: This is where quality validation happens
        - Soda scans the data warehouse
        - Evaluates all checks defined in YAML
        - Returns structured results for storage

        Args:
            table_name: Table to check
            layer: Data layer (bronze/silver/gold)
            checks_yaml: YAML string with check definitions
            pipeline_run_id: Link to pipeline execution

        Returns:
            Dict with check results and overall status
        """
        logger.info(f"Running quality checks for {layer}.{table_name}")

        # WHY: Write checks to temporary file for Soda
        checks_file = self.checks_dir / f"{layer}_{table_name}_checks.yml"
        checks_file.write_text(checks_yaml)

        # WHY: Initialize Soda scan
        scan = Scan()
        scan.set_data_source_name(self.config.data_source_name)
        scan.add_configuration_yaml_file(str(self.checks_dir / "configuration.yml"))
        scan.add_sodacl_yaml_file(str(checks_file))

        # WHY: Execute the scan
        start_time = datetime.utcnow()
        scan.execute()
        execution_duration = (datetime.utcnow() - start_time).total_seconds()

        # WHY: Parse results
        results = {
            "run_id": f"qc_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "pipeline_run_id": pipeline_run_id,
            "table_name": table_name,
            "layer": layer,
            "scan_time": datetime.utcnow().isoformat(),
            "execution_duration_seconds": execution_duration,
            "checks_total": len(scan.scan_results),
            "checks_passed": 0,
            "checks_warned": 0,
            "checks_failed": 0,
            "overall_status": "unknown",
            "check_results": []
        }

        # WHY: Process each check result
        for check in scan.scan_results:
            check_result = {
                "check_name": check.check.name if hasattr(check, 'check') else "unknown",
                "outcome": check.outcome,
                "metric_value": check.metric_value if hasattr(check, 'metric_value') else None
            }
            results["check_results"].append(check_result)

            # WHY: Count outcomes
            if check.outcome == "pass":
                results["checks_passed"] += 1
            elif check.outcome == "warn":
                results["checks_warned"] += 1
            elif check.outcome == "fail":
                results["checks_failed"] += 1

        # WHY: Determine overall status
        if results["checks_failed"] > 0:
            results["overall_status"] = "fail"
        elif results["checks_warned"] > 0:
            results["overall_status"] = "warn"
        else:
            results["overall_status"] = "pass"

        # WHY: Store results in database
        self._store_results(results)

        logger.info(
            f"Quality check complete: {results['overall_status']} "
            f"({results['checks_passed']} passed, "
            f"{results['checks_warned']} warned, "
            f"{results['checks_failed']} failed)"
        )

        return results

    def _store_results(self, results: Dict[str, Any]):
        """
        WHY: Store check results in quality database
        - Enables historical trend analysis
        - Supports quality dashboards
        - Provides audit trail
        """
        db = QualitySessionLocal()
        try:
            # Store overall run
            check_run = QualityCheckRun(
                run_id=results["run_id"],
                pipeline_run_id=results["pipeline_run_id"],
                table_name=results["table_name"],
                layer=results["layer"],
                scan_time=datetime.fromisoformat(results["scan_time"]),
                execution_duration_seconds=results["execution_duration_seconds"],
                checks_total=results["checks_total"],
                checks_passed=results["checks_passed"],
                checks_warned=results["checks_warned"],
                checks_failed=results["checks_failed"],
                overall_status=results["overall_status"],
                check_results=results["check_results"]
            )
            db.add(check_run)

            # Store individual metrics
            for check in results["check_results"]:
                if check.get("metric_value") is not None:
                    metric = QualityMetric(
                        metric_id=f"{results['run_id']}_{check['check_name']}",
                        run_id=results["run_id"],
                        table_name=results["table_name"],
                        check_name=check["check_name"],
                        metric_name=check["check_name"],
                        metric_value=check["metric_value"],
                        passed=(check["outcome"] == "pass"),
                        timestamp=datetime.fromisoformat(results["scan_time"])
                    )
                    db.add(metric)

            db.commit()
            logger.info(f"Stored quality results for run {results['run_id']}")

        except Exception as e:
            logger.error(f"Failed to store quality results: {e}")
            db.rollback()
        finally:
            db.close()

    def get_quality_trends(
        self,
        table_name: str,
        metric_name: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        WHY: Analyze quality trends over time
        - Detect quality degradation
        - Support proactive alerting
        - Enable root cause analysis

        Args:
            table_name: Table to analyze
            metric_name: Specific metric to track
            days: Number of days to look back

        Returns:
            List of metric values over time
        """
        from datetime import timedelta

        db = QualitySessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            metrics = db.query(QualityMetric).filter(
                QualityMetric.table_name == table_name,
                QualityMetric.metric_name == metric_name,
                QualityMetric.timestamp >= cutoff_date
            ).order_by(QualityMetric.timestamp).all()

            return [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "value": m.metric_value,
                    "passed": m.passed
                }
                for m in metrics
            ]

        finally:
            db.close()


# ============================================================================
# Pipeline Integration with Quality Gates
# ============================================================================

class PipelineWithQualityGates:
    """
    WHY: Integrate quality checks into pipeline execution
    - Automatic quality validation at each layer
    - Pipeline stops if quality checks fail
    - Quality metrics tracked alongside data lineage
    """

    def __init__(self, config: QualityConfig):
        self.config = config
        self.check_generator = SodaCheckGenerator()
        self.check_executor = QualityCheckExecutor(config)

    def bronze_to_silver_with_quality(
        self,
        table_name: str,
        df: pd.DataFrame,
        pipeline_run_id: str
    ) -> tuple[pd.DataFrame, Dict[str, Any]]:
        """
        WHY: Bronze -> Silver transformation with quality gates

        Args:
            table_name: Name of table
            df: Bronze DataFrame
            pipeline_run_id: Pipeline execution ID

        Returns:
            Tuple of (transformed_df, quality_results)
        """
        logger.info(f"Starting Bronze->Silver with quality gates for {table_name}")

        # Step 1: Run Bronze quality checks
        # WHY: Validate raw data before transformation
        logger.info("Running Bronze quality checks...")
        bronze_checks = self.check_generator.generate_bronze_checks(
            table_name,
            df.columns.tolist()
        )
        bronze_quality = self.check_executor.run_quality_checks(
            table_name=table_name,
            layer="bronze",
            checks_yaml=bronze_checks,
            pipeline_run_id=pipeline_run_id
        )

        # WHY: Stop if Bronze quality is unacceptable
        if bronze_quality["overall_status"] == "fail":
            raise ValueError(
                f"Bronze quality check failed for {table_name}. "
                f"Cannot proceed to Silver. "
                f"Failed checks: {bronze_quality['checks_failed']}"
            )

        # Step 2: Transform to Silver
        # WHY: Apply data cleaning and standardization
        logger.info("Transforming to Silver...")
        silver_df = df.copy()
        # ... apply transformations ...

        # Step 3: Run Silver quality checks
        # WHY: Validate transformed data
        logger.info("Running Silver quality checks...")
        silver_checks = self.check_generator.generate_silver_checks(
            table_name,
            pii_columns=['email', 'phone']  # Example PII columns
        )
        silver_quality = self.check_executor.run_quality_checks(
            table_name=table_name,
            layer="silver",
            checks_yaml=silver_checks,
            pipeline_run_id=pipeline_run_id
        )

        # WHY: Quality results inform downstream decisions
        return silver_df, {
            "bronze_quality": bronze_quality,
            "silver_quality": silver_quality
        }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    """
    Example workflow:
    1. Generate quality checks for each layer
    2. Execute checks against data
    3. Store results in quality database
    4. Analyze quality trends
    """

    # Sample data
    sample_data = pd.DataFrame({
        'customer_id': ['C001', 'C002', 'C003', 'C003'],  # Note: duplicate
        'name': ['Anders Jensen', 'Maria Nielsen', None, 'Peter Hansen'],  # Note: null
        'email': ['anders@example.dk', 'invalid_email', 'maria@test.dk', 'peter@demo.dk'],
        'created_at': [datetime.utcnow()] * 4
    })

    # Initialize
    config = QualityConfig()
    pipeline = PipelineWithQualityGates(config)

    # Run pipeline with quality gates
    try:
        silver_df, quality_results = pipeline.bronze_to_silver_with_quality(
            table_name='customers',
            df=sample_data,
            pipeline_run_id='run_20260109_001'
        )

        print("\n=== QUALITY RESULTS ===")
        print(f"Bronze: {quality_results['bronze_quality']['overall_status']}")
        print(f"Silver: {quality_results['silver_quality']['overall_status']}")

        print("\n=== DETAILED RESULTS ===")
        print(json.dumps(quality_results, indent=2, default=str))

    except ValueError as e:
        print(f"\n❌ Pipeline stopped due to quality failure: {e}")

    # Analyze trends
    print("\n=== QUALITY TRENDS ===")
    executor = QualityCheckExecutor(config)
    trends = executor.get_quality_trends(
        table_name='customers',
        metric_name='missing_count',
        days=7
    )
    for trend in trends:
        print(f"{trend['timestamp']}: {trend['value']} (passed: {trend['passed']})")
