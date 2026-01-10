-- ============================================================================
-- Atlas Intelligence Data Pipeline - Data Quality Metrics
-- ============================================================================
-- Purpose: Track data quality test results, scorecards, and anomaly detection
-- Version: 1.0
-- Created: 2026-01-09
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS quality;

COMMENT ON SCHEMA quality IS 'Data quality testing framework and metrics storage';

-- ============================================================================
-- QUALITY DIMENSIONS & RULES
-- ============================================================================

-- Quality dimensions (6 pillars)
CREATE TABLE quality.dimensions (
    dimension_id        SERIAL PRIMARY KEY,
    dimension_name      VARCHAR(50) NOT NULL UNIQUE,
    description         TEXT,
    weight              DECIMAL(3,2) DEFAULT 1.0,  -- For weighted scoring
    is_active           BOOLEAN DEFAULT TRUE,

    CONSTRAINT chk_dimension_name CHECK (
        dimension_name IN ('completeness', 'uniqueness', 'timeliness', 'validity', 'accuracy', 'consistency')
    ),
    CONSTRAINT chk_weight CHECK (weight > 0 AND weight <= 2.0)
);

INSERT INTO quality.dimensions (dimension_name, description, weight) VALUES
('completeness', 'Percentage of non-null values in required fields', 1.0),
('uniqueness', 'Absence of unintended duplicate records', 1.2),
('timeliness', 'Data freshness relative to source', 1.0),
('validity', 'Conformance to business rules and formats', 1.5),
('accuracy', 'Correctness against reference data', 1.3),
('consistency', 'Agreement across multiple sources', 1.1);

COMMENT ON TABLE quality.dimensions IS '6 dimensions of data quality framework';

-- Quality rules/tests
CREATE TABLE quality.rules (
    rule_id             SERIAL PRIMARY KEY,
    rule_name           VARCHAR(200) NOT NULL UNIQUE,
    dimension_id        INTEGER NOT NULL REFERENCES quality.dimensions(dimension_id),
    schema_name         VARCHAR(100) NOT NULL,
    table_name          VARCHAR(100) NOT NULL,
    column_name         VARCHAR(100),      -- NULL if table-level rule
    rule_type           VARCHAR(50) NOT NULL,  -- 'not_null', 'unique', 'range', 'pattern', 'custom_sql'
    rule_definition     TEXT NOT NULL,     -- SQL query or validation expression
    severity            VARCHAR(20) DEFAULT 'warning',  -- 'info', 'warning', 'error', 'critical'
    threshold_value     DECIMAL(10,2),     -- Expected value (e.g., 95.0 for 95% completeness)
    threshold_operator  VARCHAR(10),       -- '>=', '<=', '=', '!='
    is_active           BOOLEAN DEFAULT TRUE,
    owner               VARCHAR(100),
    tags                TEXT[],
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_rule_type CHECK (
        rule_type IN ('not_null', 'unique', 'range', 'pattern', 'foreign_key', 'custom_sql', 'freshness', 'row_count')
    ),
    CONSTRAINT chk_severity CHECK (
        severity IN ('info', 'warning', 'error', 'critical')
    ),
    CONSTRAINT chk_threshold_operator CHECK (
        threshold_operator IN ('>=', '<=', '=', '!=', '>', '<')
    )
);

CREATE INDEX idx_quality_rules_table ON quality.rules(schema_name, table_name);
CREATE INDEX idx_quality_rules_dimension ON quality.rules(dimension_id);
CREATE INDEX idx_quality_rules_severity ON quality.rules(severity) WHERE is_active = TRUE;
CREATE INDEX idx_quality_rules_tags ON quality.rules USING GIN(tags);

COMMENT ON TABLE quality.rules IS 'Data quality test definitions';
COMMENT ON COLUMN quality.rules.rule_definition IS 'SQL query returning pass/fail count or validation logic';

-- ============================================================================
-- QUALITY TEST EXECUTION
-- ============================================================================

-- Test execution history
CREATE TABLE quality.test_runs (
    test_run_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id             INTEGER NOT NULL REFERENCES quality.rules(rule_id),
    pipeline_run_id     UUID REFERENCES pipeline.pipeline_runs(run_id),
    execution_time      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status              VARCHAR(20) NOT NULL,  -- 'passed', 'failed', 'warning', 'error', 'skipped'

    -- Metrics
    total_rows          BIGINT,
    passed_rows         BIGINT,
    failed_rows         BIGINT,
    pass_rate_percent   DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE WHEN total_rows > 0
            THEN ROUND(100.0 * passed_rows / total_rows, 2)
            ELSE 0
        END
    ) STORED,

    -- Measured value vs threshold
    measured_value      DECIMAL(20,4),
    threshold_value     DECIMAL(20,4),
    threshold_passed    BOOLEAN,

    -- Details
    error_message       TEXT,
    execution_time_ms   INTEGER,
    sample_failures     JSONB,         -- Sample of failed records for debugging
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_test_status CHECK (
        status IN ('passed', 'failed', 'warning', 'error', 'skipped')
    )
);

CREATE INDEX idx_test_runs_rule ON quality.test_runs(rule_id, execution_time DESC);
CREATE INDEX idx_test_runs_pipeline ON quality.test_runs(pipeline_run_id);
CREATE INDEX idx_test_runs_execution ON quality.test_runs(execution_time DESC);
CREATE INDEX idx_test_runs_status ON quality.test_runs(status, execution_time) WHERE status IN ('failed', 'error');

-- Partition by execution_time for scale
CREATE TABLE quality.test_runs_2024 PARTITION OF quality.test_runs
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
CREATE TABLE quality.test_runs_2025 PARTITION OF quality.test_runs
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE quality.test_runs_2026 PARTITION OF quality.test_runs
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

COMMENT ON TABLE quality.test_runs IS 'Historical record of quality test executions';
COMMENT ON COLUMN quality.test_runs.sample_failures IS 'Sample failed records (max 100) for debugging';

-- ============================================================================
-- QUALITY SCORECARDS
-- ============================================================================

-- Table-level quality scores
CREATE TABLE quality.table_scores (
    score_id            BIGSERIAL PRIMARY KEY,
    schema_name         VARCHAR(100) NOT NULL,
    table_name          VARCHAR(100) NOT NULL,
    score_date          DATE NOT NULL,

    -- Overall score
    overall_score       DECIMAL(5,2),  -- 0-100
    overall_grade       CHAR(1) GENERATED ALWAYS AS (
        CASE
            WHEN overall_score >= 95 THEN 'A'
            WHEN overall_score >= 85 THEN 'B'
            WHEN overall_score >= 70 THEN 'C'
            WHEN overall_score >= 50 THEN 'D'
            ELSE 'F'
        END
    ) STORED,

    -- Dimension scores
    completeness_score  DECIMAL(5,2),
    uniqueness_score    DECIMAL(5,2),
    timeliness_score    DECIMAL(5,2),
    validity_score      DECIMAL(5,2),
    accuracy_score      DECIMAL(5,2),
    consistency_score   DECIMAL(5,2),

    -- Metrics
    total_tests         INTEGER,
    passed_tests        INTEGER,
    failed_tests        INTEGER,
    total_rows          BIGINT,

    -- Trends
    score_change        DECIMAL(5,2),  -- vs previous period
    trend               VARCHAR(10) GENERATED ALWAYS AS (
        CASE
            WHEN score_change > 1 THEN 'improving'
            WHEN score_change < -1 THEN 'degrading'
            ELSE 'stable'
        END
    ) STORED,

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT uq_table_score_date UNIQUE (schema_name, table_name, score_date),
    CONSTRAINT chk_scores CHECK (
        overall_score >= 0 AND overall_score <= 100 AND
        completeness_score >= 0 AND completeness_score <= 100 AND
        uniqueness_score >= 0 AND uniqueness_score <= 100 AND
        timeliness_score >= 0 AND timeliness_score <= 100 AND
        validity_score >= 0 AND validity_score <= 100 AND
        accuracy_score >= 0 AND accuracy_score <= 100 AND
        consistency_score >= 0 AND consistency_score <= 100
    )
);

CREATE INDEX idx_table_scores_table ON quality.table_scores(schema_name, table_name, score_date DESC);
CREATE INDEX idx_table_scores_grade ON quality.table_scores(overall_grade, score_date);
CREATE INDEX idx_table_scores_trend ON quality.table_scores(trend, score_date) WHERE trend = 'degrading';

COMMENT ON TABLE quality.table_scores IS 'Daily quality scorecards per table';
COMMENT ON COLUMN quality.table_scores.overall_grade IS 'Letter grade: A(95+), B(85+), C(70+), D(50+), F(<50)';

-- ============================================================================
-- ANOMALY DETECTION
-- ============================================================================

-- Baseline statistics for anomaly detection
CREATE TABLE quality.baseline_statistics (
    baseline_id         SERIAL PRIMARY KEY,
    schema_name         VARCHAR(100) NOT NULL,
    table_name          VARCHAR(100) NOT NULL,
    column_name         VARCHAR(100),
    metric_name         VARCHAR(100) NOT NULL,  -- 'row_count', 'avg', 'std_dev', 'min', 'max', 'null_pct'

    -- Statistical measures
    mean_value          DECIMAL(20,4),
    std_dev             DECIMAL(20,4),
    min_value           DECIMAL(20,4),
    max_value           DECIMAL(20,4),
    median_value        DECIMAL(20,4),

    -- Confidence interval
    lower_bound         DECIMAL(20,4) GENERATED ALWAYS AS (mean_value - (2 * std_dev)) STORED,
    upper_bound         DECIMAL(20,4) GENERATED ALWAYS AS (mean_value + (2 * std_dev)) STORED,

    -- Training period
    training_start      DATE NOT NULL,
    training_end        DATE NOT NULL,
    sample_size         INTEGER,

    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT uq_baseline UNIQUE (schema_name, table_name, column_name, metric_name)
);

CREATE INDEX idx_baseline_stats_table ON quality.baseline_statistics(schema_name, table_name);

COMMENT ON TABLE quality.baseline_statistics IS 'Statistical baselines for anomaly detection (2 sigma approach)';

-- Detected anomalies
CREATE TABLE quality.anomalies (
    anomaly_id          BIGSERIAL PRIMARY KEY,
    baseline_id         INTEGER REFERENCES quality.baseline_statistics(baseline_id),
    pipeline_run_id     UUID REFERENCES pipeline.pipeline_runs(run_id),
    detected_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Anomaly details
    measured_value      DECIMAL(20,4) NOT NULL,
    expected_range_min  DECIMAL(20,4),
    expected_range_max  DECIMAL(20,4),
    deviation_sigma     DECIMAL(5,2),  -- How many std deviations away

    -- Classification
    anomaly_type        VARCHAR(50),   -- 'spike', 'drop', 'drift', 'missing'
    severity            VARCHAR(20),   -- 'low', 'medium', 'high', 'critical'

    -- Resolution
    is_acknowledged     BOOLEAN DEFAULT FALSE,
    acknowledged_by     VARCHAR(100),
    acknowledged_at     TIMESTAMP WITH TIME ZONE,
    resolution_notes    TEXT,

    CONSTRAINT chk_anomaly_type CHECK (
        anomaly_type IN ('spike', 'drop', 'drift', 'missing', 'pattern_break')
    ),
    CONSTRAINT chk_anomaly_severity CHECK (
        severity IN ('low', 'medium', 'high', 'critical')
    )
);

CREATE INDEX idx_anomalies_baseline ON quality.anomalies(baseline_id, detected_at DESC);
CREATE INDEX idx_anomalies_severity ON quality.anomalies(severity, is_acknowledged)
    WHERE is_acknowledged = FALSE;
CREATE INDEX idx_anomalies_pipeline ON quality.anomalies(pipeline_run_id);

COMMENT ON TABLE quality.anomalies IS 'Detected data anomalies requiring investigation';
COMMENT ON COLUMN quality.anomalies.deviation_sigma IS 'Number of standard deviations from baseline mean';

-- ============================================================================
-- SODA CORE INTEGRATION
-- ============================================================================

-- Soda Core scan results
CREATE TABLE quality.soda_scans (
    scan_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id     UUID REFERENCES pipeline.pipeline_runs(run_id),
    scan_time           TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data_source         VARCHAR(100) NOT NULL,

    -- Scan summary
    total_checks        INTEGER,
    passed_checks       INTEGER,
    failed_checks       INTEGER,
    warning_checks      INTEGER,
    error_checks        INTEGER,

    -- Results
    scan_results        JSONB NOT NULL,  -- Full Soda Core JSON output
    execution_time_ms   INTEGER,

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_soda_scans_pipeline ON quality.soda_scans(pipeline_run_id);
CREATE INDEX idx_soda_scans_time ON quality.soda_scans(scan_time DESC);
CREATE INDEX idx_soda_scans_results ON quality.soda_scans USING GIN(scan_results);

COMMENT ON TABLE quality.soda_scans IS 'Soda Core data quality scan results';

-- ============================================================================
-- VIEWS FOR DASHBOARDS
-- ============================================================================

-- Current quality overview
CREATE OR REPLACE VIEW quality.v_current_quality AS
SELECT
    ts.schema_name,
    ts.table_name,
    ts.overall_score,
    ts.overall_grade,
    ts.trend,
    ts.completeness_score,
    ts.uniqueness_score,
    ts.timeliness_score,
    ts.validity_score,
    ts.accuracy_score,
    ts.consistency_score,
    ts.total_tests,
    ts.failed_tests,
    ts.score_date,
    COUNT(DISTINCT a.anomaly_id) FILTER (WHERE NOT a.is_acknowledged) AS active_anomalies
FROM quality.table_scores ts
LEFT JOIN quality.anomalies a ON
    a.baseline_id IN (
        SELECT baseline_id FROM quality.baseline_statistics
        WHERE schema_name = ts.schema_name AND table_name = ts.table_name
    )
    AND a.detected_at >= ts.score_date
    AND NOT a.is_acknowledged
WHERE ts.score_date = (
    SELECT MAX(score_date)
    FROM quality.table_scores
    WHERE schema_name = ts.schema_name
      AND table_name = ts.table_name
)
GROUP BY ts.schema_name, ts.table_name, ts.overall_score, ts.overall_grade,
         ts.trend, ts.completeness_score, ts.uniqueness_score, ts.timeliness_score,
         ts.validity_score, ts.accuracy_score, ts.consistency_score,
         ts.total_tests, ts.failed_tests, ts.score_date
ORDER BY ts.overall_score ASC;

COMMENT ON VIEW quality.v_current_quality IS 'Latest quality scores per table with active anomalies';

-- Failed tests requiring attention
CREATE OR REPLACE VIEW quality.v_failed_tests AS
SELECT
    r.rule_name,
    r.schema_name,
    r.table_name,
    r.column_name,
    r.severity,
    d.dimension_name,
    tr.execution_time,
    tr.status,
    tr.pass_rate_percent,
    tr.measured_value,
    tr.threshold_value,
    tr.sample_failures,
    tr.error_message
FROM quality.test_runs tr
JOIN quality.rules r USING (rule_id)
JOIN quality.dimensions d USING (dimension_id)
WHERE tr.status IN ('failed', 'error')
  AND tr.execution_time >= NOW() - INTERVAL '24 hours'
ORDER BY
    CASE r.severity
        WHEN 'critical' THEN 1
        WHEN 'error' THEN 2
        WHEN 'warning' THEN 3
        ELSE 4
    END,
    tr.execution_time DESC;

COMMENT ON VIEW quality.v_failed_tests IS 'Failed quality tests in last 24 hours by severity';

-- Quality trends (7-day moving average)
CREATE OR REPLACE VIEW quality.v_quality_trends AS
SELECT
    schema_name,
    table_name,
    score_date,
    overall_score,
    AVG(overall_score) OVER (
        PARTITION BY schema_name, table_name
        ORDER BY score_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS moving_avg_7d,
    completeness_score,
    uniqueness_score,
    validity_score,
    trend
FROM quality.table_scores
WHERE score_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY schema_name, table_name, score_date;

COMMENT ON VIEW quality.v_quality_trends IS '30-day quality trends with 7-day moving average';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Calculate table quality score
CREATE OR REPLACE FUNCTION quality.calculate_table_score(
    p_schema_name VARCHAR,
    p_table_name VARCHAR,
    p_score_date DATE DEFAULT CURRENT_DATE
)
RETURNS DECIMAL(5,2) AS $$
DECLARE
    v_dimension RECORD;
    v_weighted_sum DECIMAL(10,2) := 0;
    v_total_weight DECIMAL(5,2) := 0;
    v_dimension_score DECIMAL(5,2);
BEGIN
    -- Calculate weighted score per dimension
    FOR v_dimension IN
        SELECT d.dimension_id, d.dimension_name, d.weight
        FROM quality.dimensions d
        WHERE d.is_active = TRUE
    LOOP
        -- Get average pass rate for this dimension
        SELECT AVG(tr.pass_rate_percent) INTO v_dimension_score
        FROM quality.test_runs tr
        JOIN quality.rules r ON tr.rule_id = r.rule_id
        WHERE r.schema_name = p_schema_name
          AND r.table_name = p_table_name
          AND r.dimension_id = v_dimension.dimension_id
          AND DATE(tr.execution_time) = p_score_date;

        IF v_dimension_score IS NOT NULL THEN
            v_weighted_sum := v_weighted_sum + (v_dimension_score * v_dimension.weight);
            v_total_weight := v_total_weight + v_dimension.weight;
        END IF;
    END LOOP;

    -- Return weighted average
    IF v_total_weight > 0 THEN
        RETURN ROUND(v_weighted_sum / v_total_weight, 2);
    ELSE
        RETURN NULL;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION quality.calculate_table_score IS 'Calculate weighted quality score for a table';

-- Detect anomaly
CREATE OR REPLACE FUNCTION quality.detect_anomaly(
    p_baseline_id INTEGER,
    p_measured_value DECIMAL(20,4),
    p_pipeline_run_id UUID DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_baseline RECORD;
    v_deviation DECIMAL(5,2);
    v_severity VARCHAR(20);
BEGIN
    -- Get baseline statistics
    SELECT * INTO v_baseline
    FROM quality.baseline_statistics
    WHERE baseline_id = p_baseline_id
      AND is_active = TRUE;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    -- Check if value is outside 2-sigma range
    IF p_measured_value < v_baseline.lower_bound OR p_measured_value > v_baseline.upper_bound THEN
        -- Calculate deviation in sigmas
        v_deviation := ABS(p_measured_value - v_baseline.mean_value) / NULLIF(v_baseline.std_dev, 0);

        -- Determine severity
        v_severity := CASE
            WHEN v_deviation > 4 THEN 'critical'
            WHEN v_deviation > 3 THEN 'high'
            WHEN v_deviation > 2 THEN 'medium'
            ELSE 'low'
        END;

        -- Insert anomaly record
        INSERT INTO quality.anomalies (
            baseline_id, pipeline_run_id, measured_value,
            expected_range_min, expected_range_max,
            deviation_sigma, severity,
            anomaly_type
        )
        VALUES (
            p_baseline_id, p_pipeline_run_id, p_measured_value,
            v_baseline.lower_bound, v_baseline.upper_bound,
            v_deviation, v_severity,
            CASE
                WHEN p_measured_value > v_baseline.upper_bound THEN 'spike'
                ELSE 'drop'
            END
        );

        RETURN TRUE;
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION quality.detect_anomaly IS 'Detect and record anomalies based on baseline statistics';
