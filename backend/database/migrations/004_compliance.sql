-- ============================================================================
-- Atlas Intelligence Data Pipeline - Compliance & Data Governance
-- ============================================================================
-- Purpose: PII detection, GDPR compliance, audit trails, data classification
-- Version: 1.0
-- Created: 2026-01-09
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS compliance;

COMMENT ON SCHEMA compliance IS 'GDPR compliance, PII tracking, and audit trails';

-- ============================================================================
-- DATA CLASSIFICATION
-- ============================================================================

-- Classification levels
CREATE TABLE compliance.classification_levels (
    level_id            SERIAL PRIMARY KEY,
    level_name          VARCHAR(50) NOT NULL UNIQUE,
    sensitivity_rank    INTEGER NOT NULL UNIQUE,  -- 1=public, 5=highly confidential
    description         TEXT,
    retention_years     INTEGER,
    encryption_required BOOLEAN DEFAULT FALSE,
    access_control      VARCHAR(50),  -- 'public', 'internal', 'restricted', 'confidential'
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_sensitivity_rank CHECK (sensitivity_rank >= 1 AND sensitivity_rank <= 5),
    CONSTRAINT chk_access_control CHECK (
        access_control IN ('public', 'internal', 'restricted', 'confidential')
    )
);

INSERT INTO compliance.classification_levels (level_name, sensitivity_rank, description, retention_years, encryption_required, access_control) VALUES
('public', 1, 'Publicly available information', 1, FALSE, 'public'),
('internal', 2, 'Internal use only - non-sensitive', 3, FALSE, 'internal'),
('confidential', 3, 'Sensitive business information', 5, TRUE, 'restricted'),
('pii', 4, 'Personally Identifiable Information', 7, TRUE, 'restricted'),
('highly_confidential', 5, 'Critical business secrets, regulated data', 10, TRUE, 'confidential');

COMMENT ON TABLE compliance.classification_levels IS 'Data classification framework (5 levels)';
COMMENT ON COLUMN compliance.classification_levels.retention_years IS 'Minimum retention period by law/policy';

-- Data asset classification
CREATE TABLE compliance.data_assets (
    asset_id            SERIAL PRIMARY KEY,
    schema_name         VARCHAR(100) NOT NULL,
    table_name          VARCHAR(100) NOT NULL,
    column_name         VARCHAR(100),  -- NULL = table-level classification
    classification_id   INTEGER NOT NULL REFERENCES compliance.classification_levels(level_id),
    classification_reason TEXT,
    contains_pii        BOOLEAN DEFAULT FALSE,
    pii_types           TEXT[],  -- ['email', 'ssn', 'phone', 'address']
    data_owner          VARCHAR(100),
    business_purpose    TEXT,
    legal_basis         VARCHAR(100),  -- GDPR legal basis: 'consent', 'contract', 'legal_obligation', etc.
    is_active           BOOLEAN DEFAULT TRUE,
    classified_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    classified_by       VARCHAR(100),
    last_reviewed       DATE,
    next_review_date    DATE,

    CONSTRAINT uq_data_asset UNIQUE (schema_name, table_name, column_name)
);

CREATE INDEX idx_data_assets_classification ON compliance.data_assets(classification_id);
CREATE INDEX idx_data_assets_pii ON compliance.data_assets(contains_pii) WHERE contains_pii = TRUE;
CREATE INDEX idx_data_assets_table ON compliance.data_assets(schema_name, table_name);
CREATE INDEX idx_data_assets_review ON compliance.data_assets(next_review_date) WHERE is_active = TRUE;

COMMENT ON TABLE compliance.data_assets IS 'Inventory of all data assets with classification';
COMMENT ON COLUMN compliance.data_assets.legal_basis IS 'GDPR Article 6 legal basis for processing';

-- ============================================================================
-- PII DETECTION & TRACKING
-- ============================================================================

-- PII detection patterns
CREATE TABLE compliance.pii_patterns (
    pattern_id          SERIAL PRIMARY KEY,
    pii_type            VARCHAR(50) NOT NULL,  -- 'email', 'ssn', 'credit_card', 'phone', 'ip_address'
    pattern_name        VARCHAR(100) NOT NULL UNIQUE,
    regex_pattern       TEXT,
    detection_method    VARCHAR(50),  -- 'regex', 'nlp', 'lookup', 'checksum'
    confidence_threshold DECIMAL(3,2) DEFAULT 0.85,
    severity            VARCHAR(20) DEFAULT 'high',
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_pii_type CHECK (
        pii_type IN ('email', 'ssn', 'credit_card', 'phone', 'address', 'name', 'dob', 'ip_address', 'passport', 'license')
    ),
    CONSTRAINT chk_confidence CHECK (confidence_threshold >= 0 AND confidence_threshold <= 1)
);

-- Seed common PII patterns
INSERT INTO compliance.pii_patterns (pii_type, pattern_name, regex_pattern, detection_method) VALUES
('email', 'Standard Email', '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', 'regex'),
('ssn', 'US SSN', '^\d{3}-?\d{2}-?\d{4}$', 'regex'),
('credit_card', 'Credit Card (Visa/MC/Amex)', '^(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})$', 'regex'),
('phone', 'US Phone', '^(\+?1)?[- .]?\(?([0-9]{3})\)?[- .]?([0-9]{3})[- .]?([0-9]{4})$', 'regex'),
('ip_address', 'IPv4 Address', '^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', 'regex');

COMMENT ON TABLE compliance.pii_patterns IS 'PII detection patterns and rules';

-- PII detection results
CREATE TABLE compliance.pii_detections (
    detection_id        BIGSERIAL PRIMARY KEY,
    scan_id             UUID NOT NULL,
    pipeline_run_id     UUID REFERENCES pipeline.pipeline_runs(run_id),
    schema_name         VARCHAR(100) NOT NULL,
    table_name          VARCHAR(100) NOT NULL,
    column_name         VARCHAR(100) NOT NULL,

    -- Detection details
    pii_type            VARCHAR(50) NOT NULL,
    pattern_id          INTEGER REFERENCES compliance.pii_patterns(pattern_id),
    confidence_score    DECIMAL(4,3),  -- 0-1 confidence
    detection_method    VARCHAR(50),

    -- Sample data (masked)
    sample_count        INTEGER,
    total_rows_scanned  BIGINT,
    pii_prevalence_pct  DECIMAL(5,2) GENERATED ALWAYS AS (
        ROUND(100.0 * sample_count / NULLIF(total_rows_scanned, 0), 2)
    ) STORED,

    -- Status
    status              VARCHAR(20) DEFAULT 'detected',  -- 'detected', 'confirmed', 'false_positive', 'remediated'
    verified_by         VARCHAR(100),
    verified_at         TIMESTAMP WITH TIME ZONE,

    detected_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_pii_status CHECK (
        status IN ('detected', 'confirmed', 'false_positive', 'remediated')
    )
);

CREATE INDEX idx_pii_detections_scan ON compliance.pii_detections(scan_id);
CREATE INDEX idx_pii_detections_table ON compliance.pii_detections(schema_name, table_name, column_name);
CREATE INDEX idx_pii_detections_type ON compliance.pii_detections(pii_type);
CREATE INDEX idx_pii_detections_status ON compliance.pii_detections(status) WHERE status = 'detected';
CREATE INDEX idx_pii_detections_confidence ON compliance.pii_detections(confidence_score) WHERE confidence_score >= 0.85;

COMMENT ON TABLE compliance.pii_detections IS 'Automated PII detection scan results';
COMMENT ON COLUMN compliance.pii_detections.pii_prevalence_pct IS 'Percentage of rows containing PII';

-- ============================================================================
-- GDPR COMPLIANCE
-- ============================================================================

-- Data subject requests (GDPR Article 15-22)
CREATE TABLE compliance.data_subject_requests (
    request_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_type        VARCHAR(50) NOT NULL,  -- 'access', 'rectification', 'erasure', 'portability', 'restriction', 'objection'
    request_number      VARCHAR(50) NOT NULL UNIQUE,

    -- Subject information
    subject_identifier  VARCHAR(200) NOT NULL,  -- Email, user_id, etc.
    subject_name        VARCHAR(200),
    contact_email       VARCHAR(255),

    -- Request details
    request_date        DATE NOT NULL,
    due_date            DATE NOT NULL,  -- 30 days from request_date
    completion_date     DATE,
    status              VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'rejected', 'expired'

    -- Processing
    assigned_to         VARCHAR(100),
    affected_systems    TEXT[],
    affected_tables     JSONB,  -- {schema.table: row_count}

    -- Response
    response_method     VARCHAR(50),  -- 'email', 'portal', 'mail'
    response_sent_at    TIMESTAMP WITH TIME ZONE,
    rejection_reason    TEXT,

    -- Audit
    created_by          VARCHAR(100),
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_request_type CHECK (
        request_type IN ('access', 'rectification', 'erasure', 'portability', 'restriction', 'objection')
    ),
    CONSTRAINT chk_request_status CHECK (
        status IN ('pending', 'in_progress', 'completed', 'rejected', 'expired')
    ),
    CONSTRAINT chk_due_date CHECK (due_date >= request_date)
);

CREATE INDEX idx_dsr_status ON compliance.data_subject_requests(status, due_date) WHERE status IN ('pending', 'in_progress');
CREATE INDEX idx_dsr_subject ON compliance.data_subject_requests(subject_identifier);
CREATE INDEX idx_dsr_type ON compliance.data_subject_requests(request_type);
CREATE INDEX idx_dsr_overdue ON compliance.data_subject_requests(due_date) WHERE status IN ('pending', 'in_progress') AND due_date < CURRENT_DATE;

COMMENT ON TABLE compliance.data_subject_requests IS 'GDPR data subject request tracking (30-day SLA)';
COMMENT ON COLUMN compliance.data_subject_requests.due_date IS 'GDPR requires response within 30 days';

-- Data processing activities (GDPR Article 30)
CREATE TABLE compliance.processing_activities (
    activity_id         SERIAL PRIMARY KEY,
    activity_name       VARCHAR(200) NOT NULL UNIQUE,
    description         TEXT,

    -- Controller/Processor
    data_controller     VARCHAR(200),
    data_processor      VARCHAR(200),
    dpo_contact         VARCHAR(200),  -- Data Protection Officer

    -- Purpose and legal basis
    processing_purpose  TEXT NOT NULL,
    legal_basis         VARCHAR(100) NOT NULL,  -- 'consent', 'contract', 'legal_obligation', 'vital_interest', 'public_task', 'legitimate_interest'
    legitimate_interest TEXT,  -- Required if legal_basis = 'legitimate_interest'

    -- Data categories
    data_categories     TEXT[],  -- ['contact_info', 'financial', 'health', 'biometric']
    special_categories  TEXT[],  -- Sensitive data (GDPR Article 9)
    data_subjects       TEXT[],  -- ['customers', 'employees', 'suppliers']

    -- Retention
    retention_period    VARCHAR(100),
    retention_justification TEXT,

    -- Recipients
    data_recipients     TEXT[],  -- Who receives the data
    third_country_transfers BOOLEAN DEFAULT FALSE,
    transfer_safeguards TEXT,  -- If third_country_transfers = TRUE

    -- Technical measures
    security_measures   TEXT[],
    encryption_used     BOOLEAN DEFAULT FALSE,
    pseudonymization    BOOLEAN DEFAULT FALSE,

    -- Review
    last_reviewed       DATE,
    next_review_date    DATE,
    is_active           BOOLEAN DEFAULT TRUE,

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_legal_basis CHECK (
        legal_basis IN ('consent', 'contract', 'legal_obligation', 'vital_interest', 'public_task', 'legitimate_interest')
    )
);

CREATE INDEX idx_processing_activities_basis ON compliance.processing_activities(legal_basis);
CREATE INDEX idx_processing_activities_review ON compliance.processing_activities(next_review_date) WHERE is_active = TRUE;

COMMENT ON TABLE compliance.processing_activities IS 'GDPR Article 30 Record of Processing Activities (RoPA)';
COMMENT ON COLUMN compliance.processing_activities.special_categories IS 'Sensitive data requiring extra protection (race, health, biometric, etc.)';

-- Consent management
CREATE TABLE compliance.consent_records (
    consent_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_identifier  VARCHAR(200) NOT NULL,
    processing_activity_id INTEGER REFERENCES compliance.processing_activities(activity_id),

    -- Consent details
    consent_given       BOOLEAN NOT NULL,
    consent_date        TIMESTAMP WITH TIME ZONE NOT NULL,
    consent_method      VARCHAR(50),  -- 'web_form', 'email', 'paper', 'api'
    consent_version     VARCHAR(50),  -- Version of consent text

    -- Purpose
    purpose_description TEXT NOT NULL,
    data_categories     TEXT[],

    -- Withdrawal
    is_withdrawn        BOOLEAN DEFAULT FALSE,
    withdrawn_date      TIMESTAMP WITH TIME ZONE,
    withdrawal_method   VARCHAR(50),

    -- Audit trail
    ip_address          INET,
    user_agent          TEXT,
    consent_text_hash   VARCHAR(64),  -- SHA-256 of consent text for proof

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_consent_subject ON compliance.consent_records(subject_identifier, is_withdrawn);
CREATE INDEX idx_consent_activity ON compliance.consent_records(processing_activity_id);
CREATE INDEX idx_consent_date ON compliance.consent_records(consent_date DESC);

COMMENT ON TABLE compliance.consent_records IS 'GDPR consent tracking with withdrawal capability';
COMMENT ON COLUMN compliance.consent_records.consent_text_hash IS 'Proof of consent text shown to user';

-- ============================================================================
-- AUDIT TRAIL
-- ============================================================================

-- Data access audit log
CREATE TABLE compliance.audit_log (
    audit_id            BIGSERIAL,
    event_time          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Actor
    user_id             VARCHAR(100) NOT NULL,
    user_role           VARCHAR(50),
    session_id          VARCHAR(100),
    ip_address          INET,

    -- Action
    action_type         VARCHAR(50) NOT NULL,  -- 'select', 'insert', 'update', 'delete', 'export', 'access'
    schema_name         VARCHAR(100),
    table_name          VARCHAR(100),
    row_id              VARCHAR(200),  -- Primary key of affected row

    -- Details
    query_hash          VARCHAR(64),  -- Hash of query for deduplication
    rows_affected       INTEGER,
    sensitive_data_accessed BOOLEAN DEFAULT FALSE,
    classification_level VARCHAR(50),

    -- Purpose
    access_purpose      TEXT,
    legal_basis         VARCHAR(100),

    -- Context
    application_name    VARCHAR(100),
    execution_context   JSONB,

    PRIMARY KEY (audit_id, event_time)
) PARTITION BY RANGE (event_time);

CREATE INDEX idx_audit_log_user ON compliance.audit_log(user_id, event_time DESC);
CREATE INDEX idx_audit_log_action ON compliance.audit_log(action_type, event_time);
CREATE INDEX idx_audit_log_table ON compliance.audit_log(schema_name, table_name, event_time);
CREATE INDEX idx_audit_log_sensitive ON compliance.audit_log(event_time) WHERE sensitive_data_accessed = TRUE;

-- Create partitions for audit log (quarterly)
DO $$
DECLARE
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
BEGIN
    FOR i IN -4..4 LOOP
        start_date := date_trunc('quarter', CURRENT_DATE + (i || ' months')::INTERVAL * 3);
        end_date := start_date + INTERVAL '3 months';
        partition_name := 'audit_log_' || to_char(start_date, 'YYYY_Q');

        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS compliance.%I PARTITION OF compliance.audit_log
            FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );
    END LOOP;
END $$;

COMMENT ON TABLE compliance.audit_log IS 'Comprehensive audit trail of all data access (7-year retention)';
COMMENT ON COLUMN compliance.audit_log.query_hash IS 'Deduplication key for identical queries';

-- Data lineage for audit (lightweight version - full lineage in lineage schema)
CREATE TABLE compliance.data_modifications (
    modification_id     BIGSERIAL PRIMARY KEY,
    pipeline_run_id     UUID REFERENCES pipeline.pipeline_runs(run_id),
    schema_name         VARCHAR(100) NOT NULL,
    table_name          VARCHAR(100) NOT NULL,
    operation           VARCHAR(20) NOT NULL,  -- 'insert', 'update', 'delete', 'truncate'
    rows_affected       BIGINT,
    modified_by         VARCHAR(100),
    modification_time   TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Change details
    before_snapshot     JSONB,  -- Sample before state
    after_snapshot      JSONB,  -- Sample after state
    change_reason       TEXT,

    CONSTRAINT chk_operation CHECK (
        operation IN ('insert', 'update', 'delete', 'truncate', 'merge')
    )
);

CREATE INDEX idx_data_modifications_table ON compliance.data_modifications(schema_name, table_name, modification_time DESC);
CREATE INDEX idx_data_modifications_pipeline ON compliance.data_modifications(pipeline_run_id);
CREATE INDEX idx_data_modifications_time ON compliance.data_modifications(modification_time DESC);

COMMENT ON TABLE compliance.data_modifications IS 'Track all data modifications for audit purposes';

-- ============================================================================
-- VIEWS FOR COMPLIANCE REPORTING
-- ============================================================================

-- Overdue GDPR requests
CREATE OR REPLACE VIEW compliance.v_overdue_requests AS
SELECT
    request_number,
    request_type,
    subject_identifier,
    request_date,
    due_date,
    CURRENT_DATE - due_date AS days_overdue,
    assigned_to,
    status
FROM compliance.data_subject_requests
WHERE status IN ('pending', 'in_progress')
  AND due_date < CURRENT_DATE
ORDER BY due_date;

COMMENT ON VIEW compliance.v_overdue_requests IS 'GDPR requests exceeding 30-day SLA';

-- PII exposure summary
CREATE OR REPLACE VIEW compliance.v_pii_exposure AS
SELECT
    pd.schema_name,
    pd.table_name,
    pd.column_name,
    pd.pii_type,
    AVG(pd.confidence_score) AS avg_confidence,
    MAX(pd.detected_at) AS last_detected,
    COUNT(*) AS detection_count,
    MAX(pd.pii_prevalence_pct) AS max_prevalence_pct,
    BOOL_OR(da.contains_pii) AS classified_as_pii
FROM compliance.pii_detections pd
LEFT JOIN compliance.data_assets da ON
    da.schema_name = pd.schema_name AND
    da.table_name = pd.table_name AND
    da.column_name = pd.column_name
WHERE pd.status IN ('detected', 'confirmed')
GROUP BY pd.schema_name, pd.table_name, pd.column_name, pd.pii_type
ORDER BY max_prevalence_pct DESC;

COMMENT ON VIEW compliance.v_pii_exposure IS 'Summary of PII detected across all tables';

-- Sensitive data access audit
CREATE OR REPLACE VIEW compliance.v_sensitive_access AS
SELECT
    al.user_id,
    al.action_type,
    al.schema_name,
    al.table_name,
    al.classification_level,
    COUNT(*) AS access_count,
    MIN(al.event_time) AS first_access,
    MAX(al.event_time) AS last_access,
    COUNT(DISTINCT DATE(al.event_time)) AS days_with_access
FROM compliance.audit_log al
WHERE al.sensitive_data_accessed = TRUE
  AND al.event_time >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY al.user_id, al.action_type, al.schema_name, al.table_name, al.classification_level
ORDER BY access_count DESC;

COMMENT ON VIEW compliance.v_sensitive_access IS 'Sensitive data access patterns for anomaly detection';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Mask PII data
CREATE OR REPLACE FUNCTION compliance.mask_pii(
    p_value TEXT,
    p_pii_type VARCHAR,
    p_mask_char CHAR DEFAULT '*'
)
RETURNS TEXT AS $$
BEGIN
    RETURN CASE p_pii_type
        WHEN 'email' THEN
            REGEXP_REPLACE(p_value, '^(.{2})(.+)(@.+)$', '\1' || REPEAT(p_mask_char, 5) || '\3')
        WHEN 'ssn' THEN
            REGEXP_REPLACE(p_value, '^(.{3})(.{2})(.{4})$', '\1-' || REPEAT(p_mask_char, 2) || '-' || REPEAT(p_mask_char, 4))
        WHEN 'credit_card' THEN
            REPEAT(p_mask_char, 12) || RIGHT(p_value, 4)
        WHEN 'phone' THEN
            REGEXP_REPLACE(p_value, '\d', p_mask_char)
        ELSE
            REPEAT(p_mask_char, LENGTH(p_value))
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION compliance.mask_pii IS 'Mask PII data for safe display';

-- Check if consent is valid
CREATE OR REPLACE FUNCTION compliance.has_valid_consent(
    p_subject_identifier VARCHAR,
    p_processing_activity_id INTEGER
)
RETURNS BOOLEAN AS $$
DECLARE
    v_has_consent BOOLEAN;
BEGIN
    SELECT consent_given AND NOT is_withdrawn INTO v_has_consent
    FROM compliance.consent_records
    WHERE subject_identifier = p_subject_identifier
      AND processing_activity_id = p_processing_activity_id
    ORDER BY consent_date DESC
    LIMIT 1;

    RETURN COALESCE(v_has_consent, FALSE);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION compliance.has_valid_consent IS 'Check if valid consent exists for processing activity';

-- ============================================================================
-- TRIGGERS FOR AUDIT LOGGING
-- ============================================================================

-- Note: Actual trigger implementation would go on specific tables
-- Example trigger function for audit logging:

CREATE OR REPLACE FUNCTION compliance.audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO compliance.audit_log (
        user_id, action_type, schema_name, table_name,
        row_id, rows_affected, sensitive_data_accessed
    )
    VALUES (
        CURRENT_USER,
        TG_OP,
        TG_TABLE_SCHEMA,
        TG_TABLE_NAME,
        COALESCE(NEW.id::TEXT, OLD.id::TEXT),
        1,
        TRUE  -- Set based on table classification
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION compliance.audit_trigger_func IS 'Generic audit trigger for sensitive tables';

-- Example: Apply to specific tables
-- CREATE TRIGGER audit_customer_changes
-- AFTER INSERT OR UPDATE OR DELETE ON gold.dim_customer
-- FOR EACH ROW EXECUTE FUNCTION compliance.audit_trigger_func();
