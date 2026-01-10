-- ============================================================================
-- Atlas Intelligence Data Pipeline - Pipeline Metadata & Execution Tracking
-- ============================================================================
-- Purpose: Track pipeline runs, task execution, schedules, and dependencies
-- Version: 1.0
-- Created: 2026-01-09
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS pipeline;

COMMENT ON SCHEMA pipeline IS 'Pipeline orchestration metadata and execution tracking';

-- ============================================================================
-- PIPELINE DEFINITIONS
-- ============================================================================

-- Pipeline registry
CREATE TABLE pipeline.pipelines (
    pipeline_id         SERIAL PRIMARY KEY,
    pipeline_name       VARCHAR(200) NOT NULL UNIQUE,
    description         TEXT,
    pipeline_type       VARCHAR(50) NOT NULL,  -- 'batch', 'streaming', 'micro_batch'
    category            VARCHAR(50),           -- 'ingestion', 'transformation', 'validation', 'export'
    source_system_id    INTEGER REFERENCES explore.source_systems(source_system_id),
    schedule_cron       VARCHAR(100),          -- Cron expression for scheduling
    is_active           BOOLEAN DEFAULT TRUE,
    retry_policy        JSONB,                 -- {max_attempts, backoff_multiplier, initial_delay_seconds}
    timeout_seconds     INTEGER,
    priority            INTEGER DEFAULT 5,     -- 1-10, higher = more important
    owner               VARCHAR(100),
    tags                TEXT[],
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by          VARCHAR(100),

    CONSTRAINT chk_pipeline_type CHECK (
        pipeline_type IN ('batch', 'streaming', 'micro_batch')
    ),
    CONSTRAINT chk_priority CHECK (priority >= 1 AND priority <= 10)
);

CREATE INDEX idx_pipelines_active ON pipeline.pipelines(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_pipelines_type ON pipeline.pipelines(pipeline_type);
CREATE INDEX idx_pipelines_category ON pipeline.pipelines(category);
CREATE INDEX idx_pipelines_tags ON pipeline.pipelines USING GIN(tags);

COMMENT ON TABLE pipeline.pipelines IS 'Master registry of all data pipelines';
COMMENT ON COLUMN pipeline.pipelines.retry_policy IS 'JSON retry configuration matching Atlas standard';
COMMENT ON COLUMN pipeline.pipelines.schedule_cron IS 'Cron expression: "0 2 * * *" = daily at 2am';

-- ============================================================================
-- PIPELINE DEPENDENCIES
-- ============================================================================

-- Track dependencies between pipelines
CREATE TABLE pipeline.dependencies (
    dependency_id       SERIAL PRIMARY KEY,
    pipeline_id         INTEGER NOT NULL REFERENCES pipeline.pipelines(pipeline_id) ON DELETE CASCADE,
    depends_on_id       INTEGER NOT NULL REFERENCES pipeline.pipelines(pipeline_id) ON DELETE CASCADE,
    dependency_type     VARCHAR(20) DEFAULT 'sequential',  -- 'sequential', 'conditional', 'trigger'
    condition_expr      TEXT,              -- Expression for conditional dependencies
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_no_self_dependency CHECK (pipeline_id != depends_on_id),
    CONSTRAINT chk_dependency_type CHECK (
        dependency_type IN ('sequential', 'conditional', 'trigger')
    ),
    CONSTRAINT uq_dependency UNIQUE (pipeline_id, depends_on_id)
);

CREATE INDEX idx_dependencies_pipeline ON pipeline.dependencies(pipeline_id);
CREATE INDEX idx_dependencies_depends_on ON pipeline.dependencies(depends_on_id);

COMMENT ON TABLE pipeline.dependencies IS 'DAG dependencies between pipelines for orchestration';
COMMENT ON COLUMN pipeline.dependencies.dependency_type IS 'sequential=must complete, conditional=based on expression, trigger=event-based';

-- ============================================================================
-- PIPELINE TASKS
-- ============================================================================

-- Individual tasks within a pipeline
CREATE TABLE pipeline.tasks (
    task_id             SERIAL PRIMARY KEY,
    pipeline_id         INTEGER NOT NULL REFERENCES pipeline.pipelines(pipeline_id) ON DELETE CASCADE,
    task_name           VARCHAR(200) NOT NULL,
    task_order          INTEGER NOT NULL,      -- Execution order within pipeline
    task_type           VARCHAR(50) NOT NULL,  -- 'extract', 'transform', 'load', 'validate', 'notify'
    executor            VARCHAR(50),           -- 'python', 'sql', 'bash', 'spark', 'dbt'
    command_or_query    TEXT NOT NULL,
    parameters          JSONB,
    retry_policy        JSONB,                 -- Override pipeline retry policy
    timeout_seconds     INTEGER,
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT uq_task_order UNIQUE (pipeline_id, task_order),
    CONSTRAINT chk_task_type CHECK (
        task_type IN ('extract', 'transform', 'load', 'validate', 'notify', 'checkpoint')
    )
);

CREATE INDEX idx_tasks_pipeline ON pipeline.tasks(pipeline_id, task_order);
CREATE INDEX idx_tasks_type ON pipeline.tasks(task_type);

COMMENT ON TABLE pipeline.tasks IS 'Individual executable tasks within pipelines';
COMMENT ON COLUMN pipeline.tasks.task_order IS 'Execution sequence - tasks run in order within pipeline';
COMMENT ON COLUMN pipeline.tasks.executor IS 'Execution engine for the task';

-- ============================================================================
-- PIPELINE EXECUTION TRACKING
-- ============================================================================

-- Pipeline run tracking
CREATE TABLE pipeline.pipeline_runs (
    run_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id         INTEGER NOT NULL REFERENCES pipeline.pipelines(pipeline_id),
    run_number          BIGSERIAL,                         -- Sequential run counter
    status              VARCHAR(20) DEFAULT 'pending',     -- 'pending', 'running', 'success', 'failed', 'cancelled', 'retry'
    trigger_type        VARCHAR(50),                       -- 'scheduled', 'manual', 'dependency', 'event'
    triggered_by        VARCHAR(100),
    start_time          TIMESTAMP WITH TIME ZONE,
    end_time            TIMESTAMP WITH TIME ZONE,
    duration_seconds    INTEGER GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (end_time - start_time))::INTEGER
    ) STORED,

    -- Metrics
    records_processed   BIGINT,
    records_failed      BIGINT,
    bytes_processed     BIGINT,

    -- Error handling
    error_message       TEXT,
    error_details       JSONB,
    retry_count         INTEGER DEFAULT 0,
    parent_run_id       UUID REFERENCES pipeline.pipeline_runs(run_id),  -- For retries

    -- Context
    execution_context   JSONB,             -- Environment, parameters, etc.
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_run_status CHECK (
        status IN ('pending', 'running', 'success', 'failed', 'cancelled', 'retry')
    ),
    CONSTRAINT chk_run_times CHECK (start_time IS NULL OR end_time IS NULL OR end_time >= start_time)
);

CREATE INDEX idx_pipeline_runs_pipeline ON pipeline.pipeline_runs(pipeline_id, start_time DESC);
CREATE INDEX idx_pipeline_runs_status ON pipeline.pipeline_runs(status, start_time) WHERE status IN ('pending', 'running');
CREATE INDEX idx_pipeline_runs_created ON pipeline.pipeline_runs(created_at DESC);
CREATE INDEX idx_pipeline_runs_parent ON pipeline.pipeline_runs(parent_run_id) WHERE parent_run_id IS NOT NULL;

-- Partition by created_at for scalability
-- Note: Add partitioning for high-volume production use

COMMENT ON TABLE pipeline.pipeline_runs IS 'Execution history of pipeline runs with full metrics';
COMMENT ON COLUMN pipeline.pipeline_runs.trigger_type IS 'How this run was initiated';
COMMENT ON COLUMN pipeline.pipeline_runs.parent_run_id IS 'Links to original run if this is a retry';

-- Task execution tracking
CREATE TABLE pipeline.task_runs (
    task_run_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id              UUID NOT NULL REFERENCES pipeline.pipeline_runs(run_id) ON DELETE CASCADE,
    task_id             INTEGER NOT NULL REFERENCES pipeline.tasks(task_id),
    status              VARCHAR(20) DEFAULT 'pending',
    start_time          TIMESTAMP WITH TIME ZONE,
    end_time            TIMESTAMP WITH TIME ZONE,
    duration_seconds    INTEGER GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (end_time - start_time))::INTEGER
    ) STORED,

    -- Output tracking
    records_processed   BIGINT,
    records_failed      BIGINT,
    output_location     TEXT,              -- Table name, file path, etc.

    -- Error handling
    error_message       TEXT,
    error_details       JSONB,
    retry_count         INTEGER DEFAULT 0,
    exit_code           INTEGER,

    -- Logging
    log_location        TEXT,              -- Path to detailed logs
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_task_run_status CHECK (
        status IN ('pending', 'running', 'success', 'failed', 'skipped', 'retry')
    ),
    CONSTRAINT chk_task_run_times CHECK (start_time IS NULL OR end_time IS NULL OR end_time >= start_time)
);

CREATE INDEX idx_task_runs_run ON pipeline.task_runs(run_id, created_at);
CREATE INDEX idx_task_runs_task ON pipeline.task_runs(task_id, start_time DESC);
CREATE INDEX idx_task_runs_status ON pipeline.task_runs(status) WHERE status IN ('pending', 'running', 'failed');

COMMENT ON TABLE pipeline.task_runs IS 'Detailed execution tracking for individual tasks';
COMMENT ON COLUMN pipeline.task_runs.exit_code IS 'Process exit code (0=success, non-zero=error)';

-- ============================================================================
-- SCHEDULING
-- ============================================================================

-- Schedule registry
CREATE TABLE pipeline.schedules (
    schedule_id         SERIAL PRIMARY KEY,
    pipeline_id         INTEGER NOT NULL REFERENCES pipeline.pipelines(pipeline_id) ON DELETE CASCADE,
    schedule_name       VARCHAR(200) NOT NULL,
    cron_expression     VARCHAR(100) NOT NULL,
    timezone            VARCHAR(50) DEFAULT 'UTC',
    is_active           BOOLEAN DEFAULT TRUE,
    start_date          DATE,
    end_date            DATE,
    max_active_runs     INTEGER DEFAULT 1,     -- Prevent concurrent runs
    catchup             BOOLEAN DEFAULT FALSE, -- Backfill missed runs
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by          VARCHAR(100),

    CONSTRAINT chk_schedule_dates CHECK (start_date IS NULL OR end_date IS NULL OR end_date >= start_date),
    CONSTRAINT uq_schedule_name UNIQUE (pipeline_id, schedule_name)
);

CREATE INDEX idx_schedules_pipeline ON pipeline.schedules(pipeline_id) WHERE is_active = TRUE;
CREATE INDEX idx_schedules_active ON pipeline.schedules(is_active, start_date, end_date);

COMMENT ON TABLE pipeline.schedules IS 'Cron-based scheduling configuration for pipelines';
COMMENT ON COLUMN pipeline.schedules.catchup IS 'If TRUE, backfill missed scheduled runs';
COMMENT ON COLUMN pipeline.schedules.max_active_runs IS 'Limit concurrent executions';

-- ============================================================================
-- CHECKPOINTS & STATE MANAGEMENT
-- ============================================================================

-- Incremental load checkpoints
CREATE TABLE pipeline.checkpoints (
    checkpoint_id       SERIAL PRIMARY KEY,
    pipeline_id         INTEGER NOT NULL REFERENCES pipeline.pipelines(pipeline_id),
    source_table        VARCHAR(200) NOT NULL,
    checkpoint_column   VARCHAR(100) NOT NULL,  -- 'updated_at', 'id', etc.
    checkpoint_value    TEXT NOT NULL,          -- Last processed value
    checkpoint_type     VARCHAR(20) NOT NULL,   -- 'timestamp', 'integer', 'string'
    records_processed   BIGINT,
    last_run_id         UUID REFERENCES pipeline.pipeline_runs(run_id),
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT uq_checkpoint UNIQUE (pipeline_id, source_table, checkpoint_column)
);

CREATE INDEX idx_checkpoints_pipeline ON pipeline.checkpoints(pipeline_id);
CREATE INDEX idx_checkpoints_updated ON pipeline.checkpoints(updated_at DESC);

COMMENT ON TABLE pipeline.checkpoints IS 'Incremental load state - tracks last processed values';
COMMENT ON COLUMN pipeline.checkpoints.checkpoint_value IS 'Last successfully processed value for incremental loading';

-- Pipeline state for stateful operations
CREATE TABLE pipeline.pipeline_state (
    state_id            SERIAL PRIMARY KEY,
    pipeline_id         INTEGER NOT NULL REFERENCES pipeline.pipelines(pipeline_id),
    state_key           VARCHAR(200) NOT NULL,
    state_value         JSONB NOT NULL,
    version             INTEGER DEFAULT 1,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT uq_pipeline_state UNIQUE (pipeline_id, state_key)
);

CREATE INDEX idx_pipeline_state_pipeline ON pipeline.pipeline_state(pipeline_id);

COMMENT ON TABLE pipeline.pipeline_state IS 'Key-value store for pipeline state management';
COMMENT ON COLUMN pipeline.pipeline_state.version IS 'Optimistic locking version';

-- ============================================================================
-- ALERTS & NOTIFICATIONS
-- ============================================================================

-- Alert configuration
CREATE TABLE pipeline.alert_rules (
    alert_rule_id       SERIAL PRIMARY KEY,
    rule_name           VARCHAR(200) NOT NULL UNIQUE,
    pipeline_id         INTEGER REFERENCES pipeline.pipelines(pipeline_id),  -- NULL = applies to all
    alert_type          VARCHAR(50) NOT NULL,  -- 'failure', 'duration_exceeded', 'volume_anomaly', 'quality_threshold'
    condition_expr      TEXT NOT NULL,         -- SQL expression or threshold
    severity            VARCHAR(20) DEFAULT 'warning',  -- 'info', 'warning', 'error', 'critical'
    notification_channels JSONB,               -- ['slack', 'email', 'pagerduty']
    is_active           BOOLEAN DEFAULT TRUE,
    cooldown_minutes    INTEGER DEFAULT 60,    -- Prevent alert spam
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_alert_type CHECK (
        alert_type IN ('failure', 'duration_exceeded', 'volume_anomaly', 'quality_threshold', 'schema_change')
    ),
    CONSTRAINT chk_severity CHECK (
        severity IN ('info', 'warning', 'error', 'critical')
    )
);

CREATE INDEX idx_alert_rules_pipeline ON pipeline.alert_rules(pipeline_id) WHERE is_active = TRUE;
CREATE INDEX idx_alert_rules_type ON pipeline.alert_rules(alert_type);

COMMENT ON TABLE pipeline.alert_rules IS 'Alerting rules for pipeline monitoring';
COMMENT ON COLUMN pipeline.alert_rules.cooldown_minutes IS 'Minimum time between repeated alerts';

-- Alert history
CREATE TABLE pipeline.alerts (
    alert_id            BIGSERIAL PRIMARY KEY,
    alert_rule_id       INTEGER REFERENCES pipeline.alert_rules(alert_rule_id),
    run_id              UUID REFERENCES pipeline.pipeline_runs(run_id),
    pipeline_id         INTEGER REFERENCES pipeline.pipelines(pipeline_id),
    severity            VARCHAR(20),
    alert_message       TEXT NOT NULL,
    alert_details       JSONB,
    is_acknowledged     BOOLEAN DEFAULT FALSE,
    acknowledged_by     VARCHAR(100),
    acknowledged_at     TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_alerts_created ON pipeline.alerts(created_at DESC);
CREATE INDEX idx_alerts_pipeline ON pipeline.alerts(pipeline_id, created_at DESC);
CREATE INDEX idx_alerts_severity ON pipeline.alerts(severity, is_acknowledged) WHERE is_acknowledged = FALSE;
CREATE INDEX idx_alerts_rule ON pipeline.alerts(alert_rule_id);

COMMENT ON TABLE pipeline.alerts IS 'Historical record of triggered alerts';

-- ============================================================================
-- VIEWS FOR MONITORING
-- ============================================================================

-- Recent pipeline runs with key metrics
CREATE OR REPLACE VIEW pipeline.v_recent_runs AS
SELECT
    pr.run_id,
    p.pipeline_name,
    pr.status,
    pr.trigger_type,
    pr.start_time,
    pr.duration_seconds,
    pr.records_processed,
    pr.records_failed,
    pr.error_message,
    pr.retry_count,
    COUNT(tr.task_run_id) AS total_tasks,
    COUNT(CASE WHEN tr.status = 'success' THEN 1 END) AS successful_tasks,
    COUNT(CASE WHEN tr.status = 'failed' THEN 1 END) AS failed_tasks
FROM pipeline.pipeline_runs pr
JOIN pipeline.pipelines p USING (pipeline_id)
LEFT JOIN pipeline.task_runs tr USING (run_id)
WHERE pr.created_at >= NOW() - INTERVAL '7 days'
GROUP BY pr.run_id, p.pipeline_name, pr.status, pr.trigger_type,
         pr.start_time, pr.duration_seconds, pr.records_processed,
         pr.records_failed, pr.error_message, pr.retry_count
ORDER BY pr.start_time DESC;

COMMENT ON VIEW pipeline.v_recent_runs IS 'Last 7 days of pipeline runs with task summary';

-- Pipeline health dashboard
CREATE OR REPLACE VIEW pipeline.v_pipeline_health AS
SELECT
    p.pipeline_id,
    p.pipeline_name,
    p.is_active,
    p.schedule_cron,
    COUNT(DISTINCT pr.run_id) AS total_runs_7d,
    COUNT(DISTINCT CASE WHEN pr.status = 'success' THEN pr.run_id END) AS successful_runs_7d,
    COUNT(DISTINCT CASE WHEN pr.status = 'failed' THEN pr.run_id END) AS failed_runs_7d,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN pr.status = 'success' THEN pr.run_id END) /
          NULLIF(COUNT(DISTINCT pr.run_id), 0), 2) AS success_rate_percent,
    AVG(pr.duration_seconds) FILTER (WHERE pr.status = 'success') AS avg_duration_seconds,
    MAX(pr.start_time) AS last_run_time,
    MAX(CASE WHEN pr.status = 'success' THEN pr.start_time END) AS last_success_time
FROM pipeline.pipelines p
LEFT JOIN pipeline.pipeline_runs pr ON p.pipeline_id = pr.pipeline_id
    AND pr.created_at >= NOW() - INTERVAL '7 days'
WHERE p.is_active = TRUE
GROUP BY p.pipeline_id, p.pipeline_name, p.is_active, p.schedule_cron
ORDER BY p.pipeline_name;

COMMENT ON VIEW pipeline.v_pipeline_health IS 'Pipeline health metrics for operations dashboard';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get next checkpoint value
CREATE OR REPLACE FUNCTION pipeline.get_checkpoint(
    p_pipeline_id INTEGER,
    p_source_table VARCHAR,
    p_checkpoint_column VARCHAR
)
RETURNS TEXT AS $$
DECLARE
    v_checkpoint_value TEXT;
BEGIN
    SELECT checkpoint_value INTO v_checkpoint_value
    FROM pipeline.checkpoints
    WHERE pipeline_id = p_pipeline_id
      AND source_table = p_source_table
      AND checkpoint_column = p_checkpoint_column;

    RETURN COALESCE(v_checkpoint_value, '1970-01-01 00:00:00');
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION pipeline.get_checkpoint IS 'Retrieve checkpoint value for incremental loading';

-- Function to update checkpoint
CREATE OR REPLACE FUNCTION pipeline.update_checkpoint(
    p_pipeline_id INTEGER,
    p_source_table VARCHAR,
    p_checkpoint_column VARCHAR,
    p_checkpoint_value TEXT,
    p_checkpoint_type VARCHAR,
    p_records_processed BIGINT,
    p_run_id UUID
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO pipeline.checkpoints (
        pipeline_id, source_table, checkpoint_column,
        checkpoint_value, checkpoint_type, records_processed, last_run_id
    )
    VALUES (
        p_pipeline_id, p_source_table, p_checkpoint_column,
        p_checkpoint_value, p_checkpoint_type, p_records_processed, p_run_id
    )
    ON CONFLICT (pipeline_id, source_table, checkpoint_column)
    DO UPDATE SET
        checkpoint_value = EXCLUDED.checkpoint_value,
        records_processed = EXCLUDED.records_processed,
        last_run_id = EXCLUDED.last_run_id,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION pipeline.update_checkpoint IS 'Update or insert checkpoint after successful processing';
