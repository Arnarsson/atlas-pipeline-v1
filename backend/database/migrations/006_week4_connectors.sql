-- Week 4: Database Connectors & Automated Scheduling
-- Migration 006: Connector configurations, state, and scheduled runs

-- ============================================================================
-- Connector Configurations
-- ============================================================================

CREATE TABLE IF NOT EXISTS pipeline.connectors (
    connector_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('postgresql', 'mysql', 'rest_api')),
    source_name VARCHAR(255) NOT NULL UNIQUE,

    -- Configuration stored as JSONB for flexibility
    config JSONB NOT NULL,

    -- Scheduling
    schedule_cron VARCHAR(100), -- Cron expression (e.g., '0 * * * *' for hourly)
    enabled BOOLEAN DEFAULT true,

    -- Incremental loading settings
    incremental BOOLEAN DEFAULT true,
    timestamp_column VARCHAR(255), -- Column to use for incremental loading
    table_name VARCHAR(255), -- Table or endpoint to query
    custom_query TEXT, -- Optional custom SQL query or API endpoint

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),

    -- Last sync tracking
    last_sync_at TIMESTAMP,
    last_sync_status VARCHAR(50) CHECK (last_sync_status IN ('completed', 'failed', 'running')),
    last_sync_rows INTEGER,

    -- Additional metadata
    description TEXT,
    tags JSONB DEFAULT '[]'::JSONB
);

-- Indexes for connectors
CREATE INDEX IF NOT EXISTS idx_connectors_source_type ON pipeline.connectors(source_type);
CREATE INDEX IF NOT EXISTS idx_connectors_enabled ON pipeline.connectors(enabled);
CREATE INDEX IF NOT EXISTS idx_connectors_last_sync ON pipeline.connectors(last_sync_at DESC);

-- Update timestamp trigger for connectors
CREATE OR REPLACE FUNCTION update_connector_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_connector_timestamp
    BEFORE UPDATE ON pipeline.connectors
    FOR EACH ROW
    EXECUTE FUNCTION update_connector_timestamp();

-- ============================================================================
-- Connector State (for Incremental Loading)
-- ============================================================================

CREATE TABLE IF NOT EXISTS pipeline.connector_state (
    connector_id UUID REFERENCES pipeline.connectors(connector_id) ON DELETE CASCADE,
    state_key VARCHAR(255) NOT NULL,
    state_value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (connector_id, state_key)
);

-- Indexes for connector state
CREATE INDEX IF NOT EXISTS idx_connector_state_updated ON pipeline.connector_state(updated_at DESC);

-- Update timestamp trigger for connector state
CREATE OR REPLACE FUNCTION update_connector_state_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_connector_state_timestamp
    BEFORE UPDATE ON pipeline.connector_state
    FOR EACH ROW
    EXECUTE FUNCTION update_connector_state_timestamp();

-- ============================================================================
-- Scheduled Runs History
-- ============================================================================

CREATE TABLE IF NOT EXISTS pipeline.scheduled_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connector_id UUID REFERENCES pipeline.connectors(connector_id) ON DELETE CASCADE,

    -- Run metadata
    triggered_by VARCHAR(50) NOT NULL CHECK (triggered_by IN ('schedule', 'manual', 'api')),
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,

    -- Status and results
    status VARCHAR(50) NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    rows_processed INTEGER DEFAULT 0,
    error_message TEXT,
    duration_seconds INTEGER,

    -- Additional metadata
    metadata JSONB DEFAULT '{}'::JSONB
);

-- Indexes for scheduled runs
CREATE INDEX IF NOT EXISTS idx_scheduled_runs_connector ON pipeline.scheduled_runs(connector_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_runs_status ON pipeline.scheduled_runs(status);
CREATE INDEX IF NOT EXISTS idx_scheduled_runs_started ON pipeline.scheduled_runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_scheduled_runs_completed ON pipeline.scheduled_runs(completed_at DESC);

-- Computed column for duration
CREATE OR REPLACE FUNCTION compute_run_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.completed_at IS NOT NULL AND NEW.started_at IS NOT NULL THEN
        NEW.duration_seconds = EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at))::INTEGER;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_compute_run_duration
    BEFORE INSERT OR UPDATE ON pipeline.scheduled_runs
    FOR EACH ROW
    EXECUTE FUNCTION compute_run_duration();

-- ============================================================================
-- Helper Views
-- ============================================================================

-- View: Active connectors with recent run stats
CREATE OR REPLACE VIEW pipeline.v_active_connectors AS
SELECT
    c.connector_id,
    c.source_type,
    c.source_name,
    c.enabled,
    c.schedule_cron,
    c.last_sync_at,
    c.last_sync_status,
    c.last_sync_rows,
    COUNT(sr.run_id) FILTER (WHERE sr.started_at > NOW() - INTERVAL '24 hours') as runs_last_24h,
    COUNT(sr.run_id) FILTER (WHERE sr.status = 'completed' AND sr.started_at > NOW() - INTERVAL '24 hours') as successful_runs_24h,
    COUNT(sr.run_id) FILTER (WHERE sr.status = 'failed' AND sr.started_at > NOW() - INTERVAL '24 hours') as failed_runs_24h,
    AVG(sr.duration_seconds) FILTER (WHERE sr.status = 'completed' AND sr.started_at > NOW() - INTERVAL '7 days') as avg_duration_7d
FROM pipeline.connectors c
LEFT JOIN pipeline.scheduled_runs sr ON c.connector_id = sr.connector_id
WHERE c.enabled = true
GROUP BY c.connector_id;

-- View: Recent run history with connector details
CREATE OR REPLACE VIEW pipeline.v_recent_runs AS
SELECT
    sr.run_id,
    sr.connector_id,
    c.source_name,
    c.source_type,
    sr.triggered_by,
    sr.started_at,
    sr.completed_at,
    sr.status,
    sr.rows_processed,
    sr.duration_seconds,
    sr.error_message
FROM pipeline.scheduled_runs sr
JOIN pipeline.connectors c ON sr.connector_id = c.connector_id
ORDER BY sr.started_at DESC;

-- ============================================================================
-- Sample Data (for testing)
-- ============================================================================

-- Example PostgreSQL connector
INSERT INTO pipeline.connectors (
    source_type,
    source_name,
    config,
    schedule_cron,
    enabled,
    incremental,
    timestamp_column,
    table_name,
    description,
    created_by
) VALUES (
    'postgresql',
    'example_postgres_db',
    '{
        "source_type": "postgresql",
        "source_name": "example_postgres_db",
        "host": "localhost",
        "port": 5432,
        "database": "example_db",
        "username": "user",
        "password": "encrypted_password",
        "additional_params": {"sslmode": "require"}
    }'::JSONB,
    '0 * * * *',  -- Every hour
    false,  -- Disabled by default (example only)
    true,
    'updated_at',
    'users',
    'Example PostgreSQL connector for testing',
    'system'
) ON CONFLICT (source_name) DO NOTHING;

-- Example MySQL connector
INSERT INTO pipeline.connectors (
    source_type,
    source_name,
    config,
    schedule_cron,
    enabled,
    incremental,
    timestamp_column,
    table_name,
    description,
    created_by
) VALUES (
    'mysql',
    'example_mysql_db',
    '{
        "source_type": "mysql",
        "source_name": "example_mysql_db",
        "host": "localhost",
        "port": 3306,
        "database": "example_db",
        "username": "user",
        "password": "encrypted_password",
        "additional_params": {}
    }'::JSONB,
    '0 */6 * * *',  -- Every 6 hours
    false,  -- Disabled by default (example only)
    true,
    'modified_at',
    'products',
    'Example MySQL connector for testing',
    'system'
) ON CONFLICT (source_name) DO NOTHING;

-- Example REST API connector
INSERT INTO pipeline.connectors (
    source_type,
    source_name,
    config,
    schedule_cron,
    enabled,
    incremental,
    timestamp_column,
    custom_query,
    description,
    created_by
) VALUES (
    'rest_api',
    'example_api',
    '{
        "source_type": "rest_api",
        "source_name": "example_api",
        "base_url": "https://api.example.com",
        "auth_type": "bearer",
        "auth_token": "your_token_here",
        "additional_params": {
            "pagination_type": "offset",
            "page_size": 100,
            "data_key": "results"
        }
    }'::JSONB,
    '0 0 * * *',  -- Daily at midnight
    false,  -- Disabled by default (example only)
    true,
    'updated_at',
    '/api/v1/data',
    'Example REST API connector for testing',
    'system'
) ON CONFLICT (source_name) DO NOTHING;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE pipeline.connectors IS 'Data source connector configurations';
COMMENT ON TABLE pipeline.connector_state IS 'State tracking for incremental data loading';
COMMENT ON TABLE pipeline.scheduled_runs IS 'History of scheduled pipeline executions';
COMMENT ON VIEW pipeline.v_active_connectors IS 'Active connectors with recent run statistics';
COMMENT ON VIEW pipeline.v_recent_runs IS 'Recent pipeline runs with connector details';
