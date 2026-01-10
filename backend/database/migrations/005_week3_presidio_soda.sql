-- ============================================================================
-- Week 3: Presidio PII Detection & Soda Core Quality Framework
-- ============================================================================
-- WHY: Upgrade from basic regex/SQL checks to production-grade validation
-- - Enhanced PII detection with confidence scores
-- - 6-dimension quality framework
-- - Integration with Presidio and Soda Core
-- - Backward compatible with Week 2 tables
-- ============================================================================

-- ============================================================================
-- Enhanced PII Detection Tables (Presidio Integration)
-- ============================================================================

-- Enhanced PII detections with Presidio confidence scores
CREATE TABLE IF NOT EXISTS compliance.pii_detections_v2 (
    detection_id BIGSERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    dataset_name VARCHAR(255) NOT NULL,

    -- Detection details
    column_name VARCHAR(255) NOT NULL,
    pii_type VARCHAR(100) NOT NULL,  -- EMAIL_ADDRESS, PHONE_NUMBER, PERSON, DK_CPR, etc.
    instances_found INTEGER NOT NULL DEFAULT 0,

    -- Presidio-specific fields
    confidence_score DECIMAL(5, 4),  -- Average confidence (0.0000-1.0000)
    min_confidence DECIMAL(5, 4),
    max_confidence DECIMAL(5, 4),
    confidence_scores JSONB,  -- Array of all confidence scores

    -- Sample data (masked)
    sample_values JSONB,  -- Array of masked sample values

    -- Anonymization tracking
    anonymization_strategy VARCHAR(50),  -- hash, mask, redact
    anonymized BOOLEAN DEFAULT FALSE,

    -- Metadata
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    detected_by VARCHAR(100) DEFAULT 'presidio-analyzer',

    -- Indexing
    CONSTRAINT fk_pii_v2_run FOREIGN KEY (run_id)
        REFERENCES pipeline.pipeline_runs(run_id) ON DELETE CASCADE
);

CREATE INDEX idx_pii_v2_run_id ON compliance.pii_detections_v2(run_id);
CREATE INDEX idx_pii_v2_dataset ON compliance.pii_detections_v2(dataset_name);
CREATE INDEX idx_pii_v2_type ON compliance.pii_detections_v2(pii_type);
CREATE INDEX idx_pii_v2_detected_at ON compliance.pii_detections_v2(detected_at);

COMMENT ON TABLE compliance.pii_detections_v2 IS
'Enhanced PII detection results using Microsoft Presidio with confidence scores and multi-language support';

COMMENT ON COLUMN compliance.pii_detections_v2.confidence_score IS
'Average confidence score from Presidio analyzer (0.0-1.0)';

COMMENT ON COLUMN compliance.pii_detections_v2.confidence_scores IS
'JSON array of all individual confidence scores for statistical analysis';


-- ============================================================================
-- Enhanced Quality Metrics Tables (Soda Core Integration)
-- ============================================================================

-- Enhanced quality check results with 6 dimensions
CREATE TABLE IF NOT EXISTS quality.check_results_v2 (
    check_id BIGSERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    dataset_name VARCHAR(255) NOT NULL,

    -- Quality dimensions
    dimension VARCHAR(50) NOT NULL,  -- completeness, uniqueness, timeliness, validity, accuracy, consistency

    -- Check results
    score DECIMAL(5, 4) NOT NULL,  -- Quality score (0.0000-1.0000)
    passed BOOLEAN NOT NULL,
    threshold DECIMAL(5, 4) NOT NULL,

    -- Dimension-specific details
    details JSONB NOT NULL,  -- Dimension-specific metrics and analysis

    -- Metadata
    checked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    checked_by VARCHAR(100) DEFAULT 'soda-core',

    -- Indexing
    CONSTRAINT fk_quality_v2_run FOREIGN KEY (run_id)
        REFERENCES pipeline.pipeline_runs(run_id) ON DELETE CASCADE,
    CONSTRAINT chk_dimension CHECK (
        dimension IN (
            'completeness',
            'uniqueness',
            'timeliness',
            'validity',
            'accuracy',
            'consistency'
        )
    )
);

CREATE INDEX idx_quality_v2_run_id ON quality.check_results_v2(run_id);
CREATE INDEX idx_quality_v2_dataset ON quality.check_results_v2(dataset_name);
CREATE INDEX idx_quality_v2_dimension ON quality.check_results_v2(dimension);
CREATE INDEX idx_quality_v2_passed ON quality.check_results_v2(passed);
CREATE INDEX idx_quality_v2_checked_at ON quality.check_results_v2(checked_at);

COMMENT ON TABLE quality.check_results_v2 IS
'Enhanced quality check results using Soda Core 6-dimension quality framework';

COMMENT ON COLUMN quality.check_results_v2.dimension IS
'Quality dimension: completeness, uniqueness, timeliness, validity, accuracy, consistency';

COMMENT ON COLUMN quality.check_results_v2.details IS
'JSON object with dimension-specific metrics and analysis details';


-- Overall quality summary per run
CREATE TABLE IF NOT EXISTS quality.quality_summary_v2 (
    summary_id BIGSERIAL PRIMARY KEY,
    run_id UUID NOT NULL UNIQUE,
    dataset_name VARCHAR(255) NOT NULL,

    -- Overall scores
    overall_score DECIMAL(5, 4) NOT NULL,
    overall_passed BOOLEAN NOT NULL,

    -- Individual dimension scores
    completeness_score DECIMAL(5, 4),
    uniqueness_score DECIMAL(5, 4),
    timeliness_score DECIMAL(5, 4),
    validity_score DECIMAL(5, 4),
    accuracy_score DECIMAL(5, 4),
    consistency_score DECIMAL(5, 4),

    -- Pass/fail per dimension
    completeness_passed BOOLEAN,
    uniqueness_passed BOOLEAN,
    timeliness_passed BOOLEAN,
    validity_passed BOOLEAN,
    accuracy_passed BOOLEAN,
    consistency_passed BOOLEAN,

    -- Dataset info
    total_rows INTEGER NOT NULL,
    total_columns INTEGER NOT NULL,
    total_cells INTEGER NOT NULL,

    -- Metadata
    summary_created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Indexing
    CONSTRAINT fk_summary_v2_run FOREIGN KEY (run_id)
        REFERENCES pipeline.pipeline_runs(run_id) ON DELETE CASCADE
);

CREATE INDEX idx_summary_v2_dataset ON quality.quality_summary_v2(dataset_name);
CREATE INDEX idx_summary_v2_overall_score ON quality.quality_summary_v2(overall_score);
CREATE INDEX idx_summary_v2_overall_passed ON quality.quality_summary_v2(overall_passed);

COMMENT ON TABLE quality.quality_summary_v2 IS
'Overall quality summary per pipeline run with all 6 dimensions';


-- ============================================================================
-- PII Audit Trail Enhancement
-- ============================================================================

-- Enhanced audit trail with Presidio metadata
CREATE TABLE IF NOT EXISTS compliance.pii_audit_trail_v2 (
    audit_id BIGSERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    detection_id BIGINT,  -- Optional link to pii_detections_v2

    -- Audit event details
    event_type VARCHAR(50) NOT NULL,  -- detected, anonymized, accessed, exported
    pii_type VARCHAR(100),
    column_name VARCHAR(255),

    -- Anonymization details
    anonymization_strategy VARCHAR(50),
    anonymization_success BOOLEAN,

    -- Confidence tracking
    confidence_score DECIMAL(5, 4),

    -- Actor information
    actor_type VARCHAR(50),  -- system, user, api
    actor_id VARCHAR(255),

    -- Metadata
    event_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_details JSONB,

    -- Indexing
    CONSTRAINT fk_audit_v2_run FOREIGN KEY (run_id)
        REFERENCES pipeline.pipeline_runs(run_id) ON DELETE CASCADE,
    CONSTRAINT fk_audit_v2_detection FOREIGN KEY (detection_id)
        REFERENCES compliance.pii_detections_v2(detection_id) ON DELETE SET NULL
);

CREATE INDEX idx_audit_v2_run_id ON compliance.pii_audit_trail_v2(run_id);
CREATE INDEX idx_audit_v2_event_type ON compliance.pii_audit_trail_v2(event_type);
CREATE INDEX idx_audit_v2_pii_type ON compliance.pii_audit_trail_v2(pii_type);
CREATE INDEX idx_audit_v2_timestamp ON compliance.pii_audit_trail_v2(event_timestamp);

COMMENT ON TABLE compliance.pii_audit_trail_v2 IS
'Enhanced audit trail for PII detection and anonymization events with Presidio integration';


-- ============================================================================
-- Views for Reporting
-- ============================================================================

-- Quality dimension summary view
CREATE OR REPLACE VIEW quality.quality_dimension_summary AS
SELECT
    run_id,
    dataset_name,
    dimension,
    score,
    passed,
    threshold,
    checked_at,
    ROW_NUMBER() OVER (PARTITION BY run_id ORDER BY checked_at DESC) as recency_rank
FROM quality.check_results_v2
ORDER BY run_id, dimension;

COMMENT ON VIEW quality.quality_dimension_summary IS
'Summary view of quality checks by dimension for easy reporting';


-- PII detection summary view
CREATE OR REPLACE VIEW compliance.pii_detection_summary AS
SELECT
    run_id,
    dataset_name,
    pii_type,
    COUNT(*) as detection_count,
    SUM(instances_found) as total_instances,
    AVG(confidence_score) as avg_confidence,
    MIN(confidence_score) as min_confidence,
    MAX(confidence_score) as max_confidence,
    COUNT(CASE WHEN anonymized THEN 1 END) as anonymized_count,
    MAX(detected_at) as latest_detection
FROM compliance.pii_detections_v2
GROUP BY run_id, dataset_name, pii_type
ORDER BY run_id, total_instances DESC;

COMMENT ON VIEW compliance.pii_detection_summary IS
'Summary view of PII detections aggregated by type and run';


-- Combined compliance and quality view
CREATE OR REPLACE VIEW compliance.compliance_quality_report AS
SELECT
    pr.run_id,
    pr.dataset_name,
    pr.status as pipeline_status,
    pr.started_at,
    pr.completed_at,

    -- Quality metrics
    qs.overall_score as quality_score,
    qs.overall_passed as quality_passed,
    qs.completeness_score,
    qs.uniqueness_score,
    qs.timeliness_score,
    qs.validity_score,
    qs.accuracy_score,
    qs.consistency_score,

    -- PII metrics
    COALESCE(pii_summary.total_pii_types, 0) as pii_types_found,
    COALESCE(pii_summary.total_pii_instances, 0) as total_pii_instances,
    COALESCE(pii_summary.avg_confidence, 0) as avg_pii_confidence,

    -- Compliance status
    CASE
        WHEN qs.overall_passed AND COALESCE(pii_summary.total_pii_instances, 0) = 0
            THEN 'compliant'
        WHEN qs.overall_passed AND COALESCE(pii_summary.total_pii_instances, 0) > 0
            THEN 'pii_detected'
        ELSE 'non_compliant'
    END as compliance_status

FROM pipeline.pipeline_runs pr
LEFT JOIN quality.quality_summary_v2 qs ON pr.run_id = qs.run_id
LEFT JOIN (
    SELECT
        run_id,
        COUNT(DISTINCT pii_type) as total_pii_types,
        SUM(instances_found) as total_pii_instances,
        AVG(confidence_score) as avg_confidence
    FROM compliance.pii_detections_v2
    GROUP BY run_id
) pii_summary ON pr.run_id = pii_summary.run_id
ORDER BY pr.started_at DESC;

COMMENT ON VIEW compliance.compliance_quality_report IS
'Combined view of compliance and quality metrics for comprehensive reporting';


-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function to calculate overall quality score
CREATE OR REPLACE FUNCTION quality.calculate_overall_score(
    p_completeness DECIMAL,
    p_uniqueness DECIMAL,
    p_timeliness DECIMAL,
    p_validity DECIMAL,
    p_accuracy DECIMAL,
    p_consistency DECIMAL
) RETURNS DECIMAL AS $$
BEGIN
    -- Weighted average (same as SodaQualityValidator)
    RETURN (
        p_completeness * 0.25 +
        p_uniqueness * 0.15 +
        p_timeliness * 0.10 +
        p_validity * 0.20 +
        p_accuracy * 0.15 +
        p_consistency * 0.15
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION quality.calculate_overall_score IS
'Calculate weighted overall quality score from 6 dimensions';


-- Function to get latest quality check for a run
CREATE OR REPLACE FUNCTION quality.get_latest_quality_check(p_run_id UUID)
RETURNS TABLE (
    dimension VARCHAR(50),
    score DECIMAL(5, 4),
    passed BOOLEAN,
    threshold DECIMAL(5, 4),
    details JSONB,
    checked_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        qc.dimension,
        qc.score,
        qc.passed,
        qc.threshold,
        qc.details,
        qc.checked_at
    FROM quality.check_results_v2 qc
    WHERE qc.run_id = p_run_id
    ORDER BY qc.checked_at DESC;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION quality.get_latest_quality_check IS
'Get latest quality check results for a specific pipeline run';


-- ============================================================================
-- Data Migration from Week 2 Tables (if they exist)
-- ============================================================================

-- Migrate existing PII detections to v2 format (if v1 exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'compliance'
        AND table_name = 'pii_detections'
    ) THEN
        INSERT INTO compliance.pii_detections_v2 (
            run_id,
            dataset_name,
            column_name,
            pii_type,
            instances_found,
            confidence_score,
            detected_at,
            detected_by
        )
        SELECT
            run_id,
            'migrated_dataset' as dataset_name,
            column_name,
            pii_type,
            match_count as instances_found,
            0.8 as confidence_score,  -- Default confidence for regex-based detections
            detected_at,
            'regex-migration' as detected_by
        FROM compliance.pii_detections
        WHERE NOT EXISTS (
            SELECT 1 FROM compliance.pii_detections_v2 v2
            WHERE v2.run_id = pii_detections.run_id
            AND v2.column_name = pii_detections.column_name
            AND v2.pii_type = pii_detections.pii_type
        );

        RAISE NOTICE 'Migrated existing PII detections to v2 format';
    END IF;
END $$;


-- ============================================================================
-- Grants (adjust as needed for your security model)
-- ============================================================================

-- Grant read access to application user (adjust username as needed)
-- GRANT SELECT ON ALL TABLES IN SCHEMA quality TO atlas_app_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA compliance TO atlas_app_user;

-- Grant write access for pipeline operations
-- GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA quality TO atlas_app_user;
-- GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA compliance TO atlas_app_user;

-- Grant sequence usage
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA quality TO atlas_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA compliance TO atlas_app_user;


-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Verify table creation
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname IN ('quality', 'compliance')
    AND tablename LIKE '%_v2'
ORDER BY schemaname, tablename;

-- Verify indexes
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname IN ('quality', 'compliance')
    AND indexname LIKE '%_v2_%'
ORDER BY schemaname, tablename, indexname;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Week 3 migration complete: Presidio PII detection & Soda Core quality framework';
    RAISE NOTICE '   - Created compliance.pii_detections_v2 table';
    RAISE NOTICE '   - Created quality.check_results_v2 table';
    RAISE NOTICE '   - Created quality.quality_summary_v2 table';
    RAISE NOTICE '   - Created compliance.pii_audit_trail_v2 table';
    RAISE NOTICE '   - Created reporting views and helper functions';
END $$;
