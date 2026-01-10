-- ============================================================================
-- Atlas Data Pipeline Platform - Week 5-6 Migration
-- ============================================================================
-- Feature: Data Lineage, GDPR Workflows, Feature Store, Data Catalog
-- Version: 007
-- Date: 2026-01-09
-- Author: Atlas Team
-- ============================================================================

-- ============================================================================
-- FEATURE STORE SCHEMA
-- ============================================================================

-- Feature groups table
CREATE TABLE IF NOT EXISTS navigate.feature_groups (
    feature_group_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    version VARCHAR(50) NOT NULL,
    schema_definition JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255) NOT NULL DEFAULT 'system',
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],

    -- Metadata
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT feature_group_name_valid CHECK (name ~ '^[a-z][a-z0-9_]*$'),
    CONSTRAINT feature_group_version_valid CHECK (version ~ '^\d+\.\d+\.\d+$')
);

COMMENT ON TABLE navigate.feature_groups IS 'Feature groups registry for ML/AI features';
COMMENT ON COLUMN navigate.feature_groups.name IS 'Unique feature group name (e.g., customer_demographics)';
COMMENT ON COLUMN navigate.feature_groups.version IS 'Current semantic version (major.minor.patch)';
COMMENT ON COLUMN navigate.feature_groups.schema_definition IS 'JSON schema with fields array';


-- Feature versions table
CREATE TABLE IF NOT EXISTS navigate.feature_versions (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_group_id UUID NOT NULL REFERENCES navigate.feature_groups(feature_group_id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    dataset_location TEXT NOT NULL,
    row_count INTEGER NOT NULL DEFAULT 0,
    quality_score DECIMAL(5,3) CHECK (quality_score BETWEEN 0 AND 1),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_latest BOOLEAN NOT NULL DEFAULT FALSE,

    -- Metadata
    size_bytes BIGINT DEFAULT 0,
    export_format VARCHAR(50) DEFAULT 'parquet',

    -- Constraints
    CONSTRAINT feature_version_version_valid CHECK (version ~ '^\d+\.\d+\.\d+$'),
    CONSTRAINT feature_version_unique UNIQUE (feature_group_id, version)
);

COMMENT ON TABLE navigate.feature_versions IS 'Version history for feature groups';
COMMENT ON COLUMN navigate.feature_versions.dataset_location IS 'S3/file location of dataset';
COMMENT ON COLUMN navigate.feature_versions.is_latest IS 'Flag for latest version';

CREATE INDEX idx_feature_versions_group_id ON navigate.feature_versions(feature_group_id);
CREATE INDEX idx_feature_versions_latest ON navigate.feature_versions(feature_group_id, is_latest);


-- Feature metadata table
CREATE TABLE IF NOT EXISTS navigate.feature_metadata (
    feature_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_group_id UUID NOT NULL REFERENCES navigate.feature_groups(feature_group_id) ON DELETE CASCADE,
    feature_name VARCHAR(255) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    importance_score DECIMAL(5,3) CHECK (importance_score BETWEEN 0 AND 1),
    null_percentage DECIMAL(5,3) CHECK (null_percentage BETWEEN 0 AND 1),
    unique_percentage DECIMAL(5,3) CHECK (unique_percentage BETWEEN 0 AND 1),
    description TEXT,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT feature_metadata_unique UNIQUE (feature_group_id, feature_name)
);

COMMENT ON TABLE navigate.feature_metadata IS 'Metadata for individual features within feature groups';
COMMENT ON COLUMN navigate.feature_metadata.importance_score IS 'Feature importance from model training (0-1)';

CREATE INDEX idx_feature_metadata_group_id ON navigate.feature_metadata(feature_group_id);


-- ============================================================================
-- GDPR COMPLIANCE SCHEMA
-- ============================================================================

-- Data subjects table
CREATE TABLE IF NOT EXISTS compliance.data_subjects (
    subject_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identifier_type VARCHAR(50) NOT NULL,
    identifier_value VARCHAR(255) NOT NULL,
    consent_status VARCHAR(50) NOT NULL,
    consent_date TIMESTAMP,
    consent_purpose TEXT[],

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT subject_identifier_type_valid CHECK (identifier_type IN ('email', 'phone', 'cpr', 'ssn', 'customer_id', 'user_id')),
    CONSTRAINT subject_consent_status_valid CHECK (consent_status IN ('granted', 'withdrawn', 'expired', 'not_required')),
    CONSTRAINT subject_identifier_unique UNIQUE (identifier_type, identifier_value)
);

COMMENT ON TABLE compliance.data_subjects IS 'Data subjects registry for GDPR compliance';
COMMENT ON COLUMN compliance.data_subjects.identifier_type IS 'Type of identifier (email, phone, cpr, etc.)';
COMMENT ON COLUMN compliance.data_subjects.consent_status IS 'Current consent status';

CREATE INDEX idx_data_subjects_identifier ON compliance.data_subjects(identifier_type, identifier_value);
CREATE INDEX idx_data_subjects_consent_status ON compliance.data_subjects(consent_status);


-- GDPR requests table
CREATE TABLE IF NOT EXISTS compliance.gdpr_requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL REFERENCES compliance.data_subjects(subject_id) ON DELETE CASCADE,
    request_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    processed_by VARCHAR(255),
    result JSONB,
    error_message TEXT,

    -- Constraints
    CONSTRAINT gdpr_request_type_valid CHECK (request_type IN ('access', 'deletion', 'rectification', 'portability', 'restriction')),
    CONSTRAINT gdpr_request_status_valid CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled'))
);

COMMENT ON TABLE compliance.gdpr_requests IS 'GDPR data subject requests (Articles 15-20)';
COMMENT ON COLUMN compliance.gdpr_requests.request_type IS 'GDPR right (access, deletion, etc.)';
COMMENT ON COLUMN compliance.gdpr_requests.result IS 'JSON result of processing';

CREATE INDEX idx_gdpr_requests_subject_id ON compliance.gdpr_requests(subject_id);
CREATE INDEX idx_gdpr_requests_status ON compliance.gdpr_requests(status);
CREATE INDEX idx_gdpr_requests_type ON compliance.gdpr_requests(request_type);


-- GDPR audit trail table
CREATE TABLE IF NOT EXISTS compliance.gdpr_audit_trail (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL REFERENCES compliance.data_subjects(subject_id) ON DELETE CASCADE,
    operation VARCHAR(100) NOT NULL,
    performed_by VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details JSONB,
    ip_address INET,

    -- Metadata
    user_agent TEXT,
    request_id UUID REFERENCES compliance.gdpr_requests(request_id)
);

COMMENT ON TABLE compliance.gdpr_audit_trail IS 'Audit trail for all GDPR operations';
COMMENT ON COLUMN compliance.gdpr_audit_trail.operation IS 'Operation performed (register_subject, data_access, etc.)';

CREATE INDEX idx_gdpr_audit_subject_id ON compliance.gdpr_audit_trail(subject_id);
CREATE INDEX idx_gdpr_audit_timestamp ON compliance.gdpr_audit_trail(timestamp DESC);
CREATE INDEX idx_gdpr_audit_operation ON compliance.gdpr_audit_trail(operation);


-- ============================================================================
-- DATA CATALOG SCHEMA
-- ============================================================================

-- Create catalog schema if not exists
CREATE SCHEMA IF NOT EXISTS catalog;

COMMENT ON SCHEMA catalog IS 'Data catalog for dataset discovery and metadata';


-- Catalog datasets table
CREATE TABLE IF NOT EXISTS catalog.datasets (
    dataset_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    namespace VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    schema_definition JSONB NOT NULL,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    owner VARCHAR(255) NOT NULL DEFAULT 'system',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    row_count_estimate INTEGER DEFAULT 0,
    size_bytes BIGINT DEFAULT 0,

    -- Constraints
    CONSTRAINT catalog_dataset_namespace_valid CHECK (namespace IN ('explore', 'chart', 'navigate', 'features')),
    CONSTRAINT catalog_dataset_unique UNIQUE (namespace, name)
);

COMMENT ON TABLE catalog.datasets IS 'Dataset registry for data catalog';
COMMENT ON COLUMN catalog.datasets.namespace IS 'Dataset layer (explore, chart, navigate, features)';
COMMENT ON COLUMN catalog.datasets.schema_definition IS 'JSON schema with fields array';

CREATE INDEX idx_catalog_datasets_namespace ON catalog.datasets(namespace);
CREATE INDEX idx_catalog_datasets_owner ON catalog.datasets(owner);
CREATE INDEX idx_catalog_datasets_tags ON catalog.datasets USING GIN(tags);
CREATE INDEX idx_catalog_datasets_updated ON catalog.datasets(last_updated DESC);


-- Catalog columns table
CREATE TABLE IF NOT EXISTS catalog.columns (
    column_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL REFERENCES catalog.datasets(dataset_id) ON DELETE CASCADE,
    column_name VARCHAR(255) NOT NULL,
    data_type VARCHAR(100) NOT NULL,
    nullable BOOLEAN NOT NULL DEFAULT TRUE,
    pii_type VARCHAR(50),
    description TEXT,
    sample_values TEXT[],

    -- Statistics
    null_percentage DECIMAL(5,3),
    unique_percentage DECIMAL(5,3),

    -- Constraints
    CONSTRAINT catalog_column_unique UNIQUE (dataset_id, column_name)
);

COMMENT ON TABLE catalog.columns IS 'Column metadata for catalog datasets';
COMMENT ON COLUMN catalog.columns.pii_type IS 'PII type if column contains PII (email, phone, etc.)';

CREATE INDEX idx_catalog_columns_dataset_id ON catalog.columns(dataset_id);
CREATE INDEX idx_catalog_columns_pii_type ON catalog.columns(pii_type) WHERE pii_type IS NOT NULL;


-- Catalog tags table
CREATE TABLE IF NOT EXISTS catalog.tags (
    tag_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tag_name VARCHAR(100) UNIQUE NOT NULL,
    color VARCHAR(7) NOT NULL,
    description TEXT,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT catalog_tag_name_valid CHECK (tag_name ~ '^[a-z][a-z0-9_]*$'),
    CONSTRAINT catalog_tag_color_valid CHECK (color ~ '^#[0-9A-Fa-f]{6}$')
);

COMMENT ON TABLE catalog.tags IS 'Tags for categorizing datasets';
COMMENT ON COLUMN catalog.tags.color IS 'Hex color code for UI display';

-- Insert default tags
INSERT INTO catalog.tags (tag_name, color, description) VALUES
    ('finance', '#10B981', 'Financial data and transactions'),
    ('marketing', '#F59E0B', 'Marketing and customer engagement data'),
    ('pii', '#EF4444', 'Contains personally identifiable information'),
    ('gdpr', '#DC2626', 'GDPR-regulated data'),
    ('production', '#3B82F6', 'Production-ready data'),
    ('deprecated', '#6B7280', 'Deprecated dataset')
ON CONFLICT (tag_name) DO NOTHING;


-- Catalog quality history table
CREATE TABLE IF NOT EXISTS catalog.quality_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL REFERENCES catalog.datasets(dataset_id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completeness_score DECIMAL(5,3) NOT NULL CHECK (completeness_score BETWEEN 0 AND 1),
    validity_score DECIMAL(5,3) NOT NULL CHECK (validity_score BETWEEN 0 AND 1),
    consistency_score DECIMAL(5,3) NOT NULL CHECK (consistency_score BETWEEN 0 AND 1),
    overall_score DECIMAL(5,3) NOT NULL CHECK (overall_score BETWEEN 0 AND 1)
);

COMMENT ON TABLE catalog.quality_history IS 'Quality score history for datasets';

CREATE INDEX idx_catalog_quality_dataset_id ON catalog.quality_history(dataset_id);
CREATE INDEX idx_catalog_quality_timestamp ON catalog.quality_history(timestamp DESC);


-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for feature_groups
CREATE TRIGGER update_feature_groups_updated_at
    BEFORE UPDATE ON navigate.feature_groups
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for data_subjects
CREATE TRIGGER update_data_subjects_updated_at
    BEFORE UPDATE ON compliance.data_subjects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for catalog datasets
CREATE TRIGGER update_catalog_datasets_updated_at
    BEFORE UPDATE ON catalog.datasets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- Function to ensure only one latest version per feature group
CREATE OR REPLACE FUNCTION ensure_single_latest_version()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_latest = TRUE THEN
        -- Set all other versions to not latest
        UPDATE navigate.feature_versions
        SET is_latest = FALSE
        WHERE feature_group_id = NEW.feature_group_id
          AND version_id != NEW.version_id;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER ensure_single_latest_version_trigger
    AFTER INSERT OR UPDATE ON navigate.feature_versions
    FOR EACH ROW
    WHEN (NEW.is_latest = TRUE)
    EXECUTE FUNCTION ensure_single_latest_version();


-- ============================================================================
-- VIEWS
-- ============================================================================

-- View for latest feature versions
CREATE OR REPLACE VIEW navigate.latest_feature_versions AS
SELECT
    fg.feature_group_id,
    fg.name,
    fg.description,
    fv.version_id,
    fv.version,
    fv.dataset_location,
    fv.row_count,
    fv.quality_score,
    fv.created_at,
    fg.tags
FROM navigate.feature_groups fg
JOIN navigate.feature_versions fv ON fg.feature_group_id = fv.feature_group_id
WHERE fv.is_latest = TRUE;

COMMENT ON VIEW navigate.latest_feature_versions IS 'Latest versions of all feature groups';


-- View for GDPR active subjects
CREATE OR REPLACE VIEW compliance.active_data_subjects AS
SELECT *
FROM compliance.data_subjects
WHERE consent_status IN ('granted', 'not_required');

COMMENT ON VIEW compliance.active_data_subjects IS 'Data subjects with active consent';


-- View for catalog dataset overview
CREATE OR REPLACE VIEW catalog.dataset_overview AS
SELECT
    d.dataset_id,
    d.namespace,
    d.name,
    d.description,
    d.owner,
    d.created_at,
    d.last_updated,
    d.row_count_estimate,
    d.size_bytes,
    d.tags,
    COUNT(c.column_id) as column_count,
    COUNT(c.column_id) FILTER (WHERE c.pii_type IS NOT NULL) as pii_column_count
FROM catalog.datasets d
LEFT JOIN catalog.columns c ON d.dataset_id = c.dataset_id
GROUP BY d.dataset_id;

COMMENT ON VIEW catalog.dataset_overview IS 'Dataset overview with column counts';


-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

-- Grant permissions on feature store tables
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA navigate TO atlas_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA navigate TO atlas_user;

-- Grant permissions on compliance tables
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA compliance TO atlas_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA compliance TO atlas_user;

-- Grant permissions on catalog schema
GRANT USAGE ON SCHEMA catalog TO atlas_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA catalog TO atlas_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA catalog TO atlas_user;


-- ============================================================================
-- COMPLETION
-- ============================================================================

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Week 5-6 migration completed successfully!';
    RAISE NOTICE 'Created:';
    RAISE NOTICE '  - Feature Store: 3 tables (feature_groups, feature_versions, feature_metadata)';
    RAISE NOTICE '  - GDPR: 3 tables (data_subjects, gdpr_requests, gdpr_audit_trail)';
    RAISE NOTICE '  - Data Catalog: 5 tables (datasets, columns, tags, quality_history)';
    RAISE NOTICE '  - 3 views for common queries';
    RAISE NOTICE '  - Triggers for updated_at and version management';
END $$;
