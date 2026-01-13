-- Airbyte Integration Migration
-- Migration 008: Docker-based Airbyte connector support
-- Enables Atlas to run 100+ Airbyte connectors via Docker execution

-- ============================================================================
-- Extend Connectors Table for Airbyte Support
-- ============================================================================

-- Add Airbyte-specific columns to existing connectors table
ALTER TABLE pipeline.connectors
    ADD COLUMN IF NOT EXISTS airbyte_image VARCHAR(255),
    ADD COLUMN IF NOT EXISTS airbyte_protocol_version VARCHAR(20) DEFAULT '0.2.0',
    ADD COLUMN IF NOT EXISTS airbyte_config JSONB,
    ADD COLUMN IF NOT EXISTS is_airbyte BOOLEAN DEFAULT false;

-- Update source_type constraint to include Airbyte types
-- First, drop the old constraint and add a new one
ALTER TABLE pipeline.connectors
    DROP CONSTRAINT IF EXISTS connectors_source_type_check;

ALTER TABLE pipeline.connectors
    ADD CONSTRAINT connectors_source_type_check
    CHECK (source_type IN (
        -- Legacy Atlas connectors
        'postgresql', 'mysql', 'rest_api', 'google_sheets', 'salesforce',
        -- Airbyte connectors (prefix with 'airbyte:')
        'airbyte:source-postgres', 'airbyte:source-mysql', 'airbyte:source-mssql',
        'airbyte:source-mongodb-v2', 'airbyte:source-snowflake', 'airbyte:source-bigquery',
        'airbyte:source-salesforce', 'airbyte:source-hubspot', 'airbyte:source-stripe',
        'airbyte:source-shopify', 'airbyte:source-github', 'airbyte:source-jira',
        'airbyte:source-slack', 'airbyte:source-google-ads', 'airbyte:source-facebook-marketing',
        'airbyte:source-google-analytics-v4', 'airbyte:source-google-analytics-data-api',
        'airbyte:source-mixpanel', 'airbyte:source-amplitude', 'airbyte:source-s3',
        'airbyte:source-gcs', 'airbyte:source-google-sheets', 'airbyte:source-notion',
        -- Generic category for any Airbyte connector
        'airbyte'
    ));

-- Index for Airbyte connectors
CREATE INDEX IF NOT EXISTS idx_connectors_airbyte ON pipeline.connectors(is_airbyte) WHERE is_airbyte = true;
CREATE INDEX IF NOT EXISTS idx_connectors_airbyte_image ON pipeline.connectors(airbyte_image);

-- ============================================================================
-- Airbyte Catalogs (Cached Schema Discovery)
-- ============================================================================

CREATE TABLE IF NOT EXISTS pipeline.airbyte_catalogs (
    catalog_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connector_id UUID REFERENCES pipeline.connectors(connector_id) ON DELETE CASCADE,

    -- Connector identification
    airbyte_image VARCHAR(255) NOT NULL,
    config_hash VARCHAR(64) NOT NULL, -- SHA256 of config for cache validation

    -- Catalog data (from DISCOVER command)
    catalog JSONB NOT NULL,
    streams_count INTEGER NOT NULL DEFAULT 0,
    stream_names TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],

    -- Timestamps
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP, -- Optional TTL for cache

    -- Metadata
    discovery_duration_ms INTEGER,
    protocol_version VARCHAR(20),

    UNIQUE (connector_id)
);

-- Indexes for catalog lookup
CREATE INDEX IF NOT EXISTS idx_airbyte_catalogs_connector ON pipeline.airbyte_catalogs(connector_id);
CREATE INDEX IF NOT EXISTS idx_airbyte_catalogs_image ON pipeline.airbyte_catalogs(airbyte_image);
CREATE INDEX IF NOT EXISTS idx_airbyte_catalogs_discovered ON pipeline.airbyte_catalogs(discovered_at DESC);

-- ============================================================================
-- Airbyte Sync State (Enhanced State Management)
-- ============================================================================

CREATE TABLE IF NOT EXISTS pipeline.airbyte_state (
    state_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connector_id UUID REFERENCES pipeline.connectors(connector_id) ON DELETE CASCADE,

    -- Stream identification
    stream_name VARCHAR(255) NOT NULL,
    stream_namespace VARCHAR(255),

    -- State data (Airbyte STATE message format)
    state_type VARCHAR(20) NOT NULL CHECK (state_type IN ('STREAM', 'GLOBAL', 'LEGACY')),
    state_data JSONB NOT NULL,

    -- Cursor tracking
    cursor_field TEXT[],
    cursor_value JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Metadata
    records_synced BIGINT DEFAULT 0,
    last_record_emitted_at TIMESTAMP,

    UNIQUE (connector_id, stream_name, COALESCE(stream_namespace, ''))
);

-- Indexes for state lookup
CREATE INDEX IF NOT EXISTS idx_airbyte_state_connector ON pipeline.airbyte_state(connector_id);
CREATE INDEX IF NOT EXISTS idx_airbyte_state_stream ON pipeline.airbyte_state(stream_name);
CREATE INDEX IF NOT EXISTS idx_airbyte_state_updated ON pipeline.airbyte_state(updated_at DESC);

-- Update timestamp trigger for state
CREATE OR REPLACE FUNCTION update_airbyte_state_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_airbyte_state_timestamp
    BEFORE UPDATE ON pipeline.airbyte_state
    FOR EACH ROW
    EXECUTE FUNCTION update_airbyte_state_timestamp();

-- ============================================================================
-- Airbyte Sync Statistics (Per-Stream Metrics)
-- ============================================================================

CREATE TABLE IF NOT EXISTS pipeline.airbyte_sync_stats (
    stats_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES pipeline.scheduled_runs(run_id) ON DELETE CASCADE,
    connector_id UUID REFERENCES pipeline.connectors(connector_id) ON DELETE CASCADE,

    -- Stream identification
    stream_name VARCHAR(255) NOT NULL,
    stream_namespace VARCHAR(255),

    -- Sync metrics
    records_emitted BIGINT DEFAULT 0,
    records_committed BIGINT DEFAULT 0,
    bytes_emitted BIGINT DEFAULT 0,

    -- Timing
    sync_started_at TIMESTAMP NOT NULL,
    sync_completed_at TIMESTAMP,
    duration_ms INTEGER,

    -- Status
    status VARCHAR(50) NOT NULL CHECK (status IN (
        'STARTED', 'RUNNING', 'COMPLETE', 'INCOMPLETE', 'FAILED'
    )),
    error_message TEXT,

    -- Estimates (from TRACE ESTIMATE messages)
    estimated_rows BIGINT,
    estimated_bytes BIGINT,

    -- Metadata
    state_messages_emitted INTEGER DEFAULT 0,
    log_messages_emitted INTEGER DEFAULT 0
);

-- Indexes for sync stats
CREATE INDEX IF NOT EXISTS idx_airbyte_sync_stats_run ON pipeline.airbyte_sync_stats(run_id);
CREATE INDEX IF NOT EXISTS idx_airbyte_sync_stats_connector ON pipeline.airbyte_sync_stats(connector_id);
CREATE INDEX IF NOT EXISTS idx_airbyte_sync_stats_stream ON pipeline.airbyte_sync_stats(stream_name);
CREATE INDEX IF NOT EXISTS idx_airbyte_sync_stats_started ON pipeline.airbyte_sync_stats(sync_started_at DESC);

-- ============================================================================
-- Airbyte Connector Registry (Local Cache)
-- ============================================================================

CREATE TABLE IF NOT EXISTS pipeline.airbyte_connector_registry (
    registry_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Connector identification
    connector_name VARCHAR(255) NOT NULL UNIQUE,
    docker_image VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,

    -- Classification
    category VARCHAR(50) NOT NULL CHECK (category IN (
        'database', 'file', 'api', 'crm', 'marketing', 'analytics',
        'ecommerce', 'finance', 'hr', 'productivity', 'communication',
        'development', 'storage', 'other'
    )),

    -- Capabilities
    supports_incremental BOOLEAN DEFAULT true,
    supports_normalization BOOLEAN DEFAULT false,
    supports_cdc BOOLEAN DEFAULT false,

    -- Documentation
    documentation_url TEXT,
    icon_url TEXT,

    -- Status
    is_available BOOLEAN DEFAULT true,
    latest_version VARCHAR(50),
    last_checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for registry
CREATE INDEX IF NOT EXISTS idx_airbyte_registry_category ON pipeline.airbyte_connector_registry(category);
CREATE INDEX IF NOT EXISTS idx_airbyte_registry_available ON pipeline.airbyte_connector_registry(is_available);

-- Populate with common connectors
INSERT INTO pipeline.airbyte_connector_registry (
    connector_name, docker_image, display_name, category, supports_incremental, supports_cdc, documentation_url
) VALUES
    -- Database Connectors
    ('source-postgres', 'airbyte/source-postgres:latest', 'PostgreSQL', 'database', true, true, 'https://docs.airbyte.com/integrations/sources/postgres'),
    ('source-mysql', 'airbyte/source-mysql:latest', 'MySQL', 'database', true, true, 'https://docs.airbyte.com/integrations/sources/mysql'),
    ('source-mssql', 'airbyte/source-mssql:latest', 'Microsoft SQL Server', 'database', true, true, 'https://docs.airbyte.com/integrations/sources/mssql'),
    ('source-mongodb-v2', 'airbyte/source-mongodb-v2:latest', 'MongoDB', 'database', true, true, 'https://docs.airbyte.com/integrations/sources/mongodb-v2'),
    ('source-snowflake', 'airbyte/source-snowflake:latest', 'Snowflake', 'database', true, false, 'https://docs.airbyte.com/integrations/sources/snowflake'),
    ('source-bigquery', 'airbyte/source-bigquery:latest', 'Google BigQuery', 'database', true, false, 'https://docs.airbyte.com/integrations/sources/bigquery'),
    ('source-redshift', 'airbyte/source-redshift:latest', 'Amazon Redshift', 'database', true, false, 'https://docs.airbyte.com/integrations/sources/redshift'),
    ('source-clickhouse', 'airbyte/source-clickhouse:latest', 'ClickHouse', 'database', true, false, 'https://docs.airbyte.com/integrations/sources/clickhouse'),

    -- CRM Connectors
    ('source-salesforce', 'airbyte/source-salesforce:latest', 'Salesforce', 'crm', true, false, 'https://docs.airbyte.com/integrations/sources/salesforce'),
    ('source-hubspot', 'airbyte/source-hubspot:latest', 'HubSpot', 'crm', true, false, 'https://docs.airbyte.com/integrations/sources/hubspot'),
    ('source-pipedrive', 'airbyte/source-pipedrive:latest', 'Pipedrive', 'crm', true, false, NULL),
    ('source-zendesk-support', 'airbyte/source-zendesk-support:latest', 'Zendesk Support', 'crm', true, false, 'https://docs.airbyte.com/integrations/sources/zendesk-support'),
    ('source-intercom', 'airbyte/source-intercom:latest', 'Intercom', 'crm', true, false, 'https://docs.airbyte.com/integrations/sources/intercom'),

    -- Marketing Connectors
    ('source-google-ads', 'airbyte/source-google-ads:latest', 'Google Ads', 'marketing', true, false, 'https://docs.airbyte.com/integrations/sources/google-ads'),
    ('source-facebook-marketing', 'airbyte/source-facebook-marketing:latest', 'Facebook Marketing', 'marketing', true, false, 'https://docs.airbyte.com/integrations/sources/facebook-marketing'),
    ('source-linkedin-ads', 'airbyte/source-linkedin-ads:latest', 'LinkedIn Ads', 'marketing', true, false, NULL),
    ('source-mailchimp', 'airbyte/source-mailchimp:latest', 'Mailchimp', 'marketing', true, false, 'https://docs.airbyte.com/integrations/sources/mailchimp'),
    ('source-sendgrid', 'airbyte/source-sendgrid:latest', 'SendGrid', 'marketing', true, false, NULL),

    -- Analytics Connectors
    ('source-google-analytics-v4', 'airbyte/source-google-analytics-v4:latest', 'Google Analytics (UA)', 'analytics', true, false, 'https://docs.airbyte.com/integrations/sources/google-analytics-v4'),
    ('source-google-analytics-data-api', 'airbyte/source-google-analytics-data-api:latest', 'Google Analytics 4', 'analytics', true, false, NULL),
    ('source-mixpanel', 'airbyte/source-mixpanel:latest', 'Mixpanel', 'analytics', true, false, 'https://docs.airbyte.com/integrations/sources/mixpanel'),
    ('source-amplitude', 'airbyte/source-amplitude:latest', 'Amplitude', 'analytics', true, false, 'https://docs.airbyte.com/integrations/sources/amplitude'),

    -- E-Commerce Connectors
    ('source-shopify', 'airbyte/source-shopify:latest', 'Shopify', 'ecommerce', true, false, 'https://docs.airbyte.com/integrations/sources/shopify'),
    ('source-stripe', 'airbyte/source-stripe:latest', 'Stripe', 'ecommerce', true, false, 'https://docs.airbyte.com/integrations/sources/stripe'),
    ('source-woocommerce', 'airbyte/source-woocommerce:latest', 'WooCommerce', 'ecommerce', true, false, NULL),
    ('source-square', 'airbyte/source-square:latest', 'Square', 'ecommerce', true, false, NULL),

    -- Development Connectors
    ('source-github', 'airbyte/source-github:latest', 'GitHub', 'development', true, false, 'https://docs.airbyte.com/integrations/sources/github'),
    ('source-gitlab', 'airbyte/source-gitlab:latest', 'GitLab', 'development', true, false, 'https://docs.airbyte.com/integrations/sources/gitlab'),
    ('source-jira', 'airbyte/source-jira:latest', 'Jira', 'productivity', true, false, 'https://docs.airbyte.com/integrations/sources/jira'),
    ('source-linear', 'airbyte/source-linear:latest', 'Linear', 'development', true, false, NULL),

    -- Communication Connectors
    ('source-slack', 'airbyte/source-slack:latest', 'Slack', 'communication', true, false, 'https://docs.airbyte.com/integrations/sources/slack'),
    ('source-twilio', 'airbyte/source-twilio:latest', 'Twilio', 'communication', true, false, NULL),

    -- Storage Connectors
    ('source-s3', 'airbyte/source-s3:latest', 'Amazon S3', 'storage', true, false, 'https://docs.airbyte.com/integrations/sources/s3'),
    ('source-gcs', 'airbyte/source-gcs:latest', 'Google Cloud Storage', 'storage', true, false, NULL),
    ('source-google-sheets', 'airbyte/source-google-sheets:latest', 'Google Sheets', 'file', false, false, 'https://docs.airbyte.com/integrations/sources/google-sheets'),

    -- Productivity Connectors
    ('source-notion', 'airbyte/source-notion:latest', 'Notion', 'productivity', true, false, 'https://docs.airbyte.com/integrations/sources/notion'),
    ('source-airtable', 'airbyte/source-airtable:latest', 'Airtable', 'productivity', false, false, NULL),
    ('source-asana', 'airbyte/source-asana:latest', 'Asana', 'productivity', true, false, NULL)

ON CONFLICT (connector_name) DO NOTHING;

-- ============================================================================
-- Helper Views
-- ============================================================================

-- View: Airbyte connectors with sync stats
CREATE OR REPLACE VIEW pipeline.v_airbyte_connectors AS
SELECT
    c.connector_id,
    c.source_name,
    c.airbyte_image,
    c.airbyte_protocol_version,
    c.enabled,
    c.schedule_cron,
    c.last_sync_at,
    c.last_sync_status,
    ac.streams_count,
    ac.stream_names,
    ac.discovered_at as catalog_discovered_at,
    COUNT(DISTINCT ast.stream_name) as streams_with_state,
    SUM(ast.records_synced) as total_records_synced
FROM pipeline.connectors c
LEFT JOIN pipeline.airbyte_catalogs ac ON c.connector_id = ac.connector_id
LEFT JOIN pipeline.airbyte_state ast ON c.connector_id = ast.connector_id
WHERE c.is_airbyte = true
GROUP BY c.connector_id, ac.streams_count, ac.stream_names, ac.discovered_at;

-- View: Stream-level sync history
CREATE OR REPLACE VIEW pipeline.v_airbyte_stream_stats AS
SELECT
    ass.connector_id,
    c.source_name,
    ass.stream_name,
    ass.stream_namespace,
    ass.status,
    ass.records_emitted,
    ass.bytes_emitted,
    ass.duration_ms,
    ass.sync_started_at,
    ass.sync_completed_at,
    ass.error_message,
    sr.run_id,
    sr.triggered_by
FROM pipeline.airbyte_sync_stats ass
JOIN pipeline.connectors c ON ass.connector_id = c.connector_id
JOIN pipeline.scheduled_runs sr ON ass.run_id = sr.run_id
ORDER BY ass.sync_started_at DESC;

-- View: Connector registry summary
CREATE OR REPLACE VIEW pipeline.v_airbyte_registry_summary AS
SELECT
    category,
    COUNT(*) as connector_count,
    COUNT(*) FILTER (WHERE supports_incremental) as incremental_count,
    COUNT(*) FILTER (WHERE supports_cdc) as cdc_count,
    COUNT(*) FILTER (WHERE is_available) as available_count
FROM pipeline.airbyte_connector_registry
GROUP BY category
ORDER BY connector_count DESC;

-- ============================================================================
-- Functions
-- ============================================================================

-- Function: Get connector state for incremental sync
CREATE OR REPLACE FUNCTION pipeline.get_airbyte_state(
    p_connector_id UUID,
    p_stream_name VARCHAR(255),
    p_stream_namespace VARCHAR(255) DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_state JSONB;
BEGIN
    SELECT state_data INTO v_state
    FROM pipeline.airbyte_state
    WHERE connector_id = p_connector_id
      AND stream_name = p_stream_name
      AND COALESCE(stream_namespace, '') = COALESCE(p_stream_namespace, '');

    RETURN v_state;
END;
$$ LANGUAGE plpgsql;

-- Function: Update connector state after sync
CREATE OR REPLACE FUNCTION pipeline.update_airbyte_state(
    p_connector_id UUID,
    p_stream_name VARCHAR(255),
    p_stream_namespace VARCHAR(255),
    p_state_type VARCHAR(20),
    p_state_data JSONB,
    p_records_synced BIGINT DEFAULT 0
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO pipeline.airbyte_state (
        connector_id, stream_name, stream_namespace, state_type, state_data, records_synced, last_record_emitted_at
    ) VALUES (
        p_connector_id, p_stream_name, p_stream_namespace, p_state_type, p_state_data, p_records_synced, CURRENT_TIMESTAMP
    )
    ON CONFLICT (connector_id, stream_name, COALESCE(stream_namespace, ''))
    DO UPDATE SET
        state_data = EXCLUDED.state_data,
        records_synced = pipeline.airbyte_state.records_synced + EXCLUDED.records_synced,
        last_record_emitted_at = EXCLUDED.last_record_emitted_at;
END;
$$ LANGUAGE plpgsql;

-- Function: Clear state for full refresh
CREATE OR REPLACE FUNCTION pipeline.clear_airbyte_state(
    p_connector_id UUID,
    p_stream_name VARCHAR(255) DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER;
BEGIN
    IF p_stream_name IS NULL THEN
        DELETE FROM pipeline.airbyte_state WHERE connector_id = p_connector_id;
    ELSE
        DELETE FROM pipeline.airbyte_state
        WHERE connector_id = p_connector_id AND stream_name = p_stream_name;
    END IF;

    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE pipeline.airbyte_catalogs IS 'Cached schema discovery results from Airbyte DISCOVER command';
COMMENT ON TABLE pipeline.airbyte_state IS 'Incremental sync state per stream (Airbyte STATE messages)';
COMMENT ON TABLE pipeline.airbyte_sync_stats IS 'Per-stream sync statistics and metrics';
COMMENT ON TABLE pipeline.airbyte_connector_registry IS 'Local cache of available Airbyte connectors';

COMMENT ON COLUMN pipeline.connectors.airbyte_image IS 'Docker image for Airbyte connector (e.g., airbyte/source-postgres:latest)';
COMMENT ON COLUMN pipeline.connectors.airbyte_protocol_version IS 'Airbyte protocol version (default 0.2.0)';
COMMENT ON COLUMN pipeline.connectors.airbyte_config IS 'Airbyte-specific configuration JSON';
COMMENT ON COLUMN pipeline.connectors.is_airbyte IS 'Whether this connector uses Airbyte Docker execution';

COMMENT ON VIEW pipeline.v_airbyte_connectors IS 'Airbyte connectors with catalog and sync state summary';
COMMENT ON VIEW pipeline.v_airbyte_stream_stats IS 'Stream-level sync statistics with run history';
COMMENT ON VIEW pipeline.v_airbyte_registry_summary IS 'Summary of connectors by category';

COMMENT ON FUNCTION pipeline.get_airbyte_state IS 'Get state data for incremental sync of a specific stream';
COMMENT ON FUNCTION pipeline.update_airbyte_state IS 'Update or insert state after sync completion';
COMMENT ON FUNCTION pipeline.clear_airbyte_state IS 'Clear state to trigger full refresh';
