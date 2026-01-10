-- ============================================================================
-- Atlas Intelligence Data Pipeline - Core Tables
-- Explore/Chart/Navigate Medallion Architecture
-- ============================================================================
-- Purpose: Raw data storage across all zones with proper partitioning
-- Version: 1.0
-- Created: 2026-01-09
-- ============================================================================

-- Create schemas for medallion architecture
CREATE SCHEMA IF NOT EXISTS explore;
CREATE SCHEMA IF NOT EXISTS chart;
CREATE SCHEMA IF NOT EXISTS navigate;
CREATE SCHEMA IF NOT EXISTS archive;

COMMENT ON SCHEMA explore IS 'Raw data zone - unmodified copies from source systems';
COMMENT ON SCHEMA chart IS 'Processed data zone - cleaned, deduplicated, validated';
COMMENT ON SCHEMA navigate IS 'Curated data zone - business-ready, aggregated, enriched';
COMMENT ON SCHEMA archive IS 'Historical data archive for compliance and recovery';

-- ============================================================================
-- EXPLORE LAYER - Raw Data Landing Zone
-- ============================================================================

-- Explore: Source System Registry
-- Tracks all connected data sources
CREATE TABLE explore.source_systems (
    source_system_id    SERIAL PRIMARY KEY,
    system_name         VARCHAR(100) NOT NULL UNIQUE,
    system_type         VARCHAR(50) NOT NULL,  -- 'ERP', 'CRM', 'HR', 'DOCUMENT', 'API'
    description         TEXT,
    connection_type     VARCHAR(50),           -- 'api', 'database', 'file', 'stream'
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_system_type CHECK (
        system_type IN ('ERP', 'CRM', 'HR', 'DOCUMENT', 'API', 'DATABASE', 'FILE', 'STREAM')
    )
);

CREATE INDEX idx_source_systems_active ON explore.source_systems(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE explore.source_systems IS 'Registry of all connected source systems';
COMMENT ON COLUMN explore.source_systems.system_type IS 'Category of source system for connector selection';

-- Explore: Raw Data Tables Template
-- Generic structure for raw data ingestion
-- Actual tables created dynamically per source
CREATE TABLE explore.raw_data_template (
    raw_id              BIGSERIAL,
    source_system_id    INTEGER NOT NULL REFERENCES explore.source_systems(source_system_id),
    source_table_name   VARCHAR(200) NOT NULL,
    source_record_id    VARCHAR(200),
    raw_data            JSONB NOT NULL,
    source_timestamp    TIMESTAMP WITH TIME ZONE,
    ingestion_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ingestion_batch_id  UUID NOT NULL,
    is_deleted          BOOLEAN DEFAULT FALSE,
    checksum            VARCHAR(64),  -- SHA-256 hash for deduplication

    PRIMARY KEY (raw_id, ingestion_timestamp)
) PARTITION BY RANGE (ingestion_timestamp);

CREATE INDEX idx_raw_data_source ON explore.raw_data_template(source_system_id, source_table_name);
CREATE INDEX idx_raw_data_batch ON explore.raw_data_template(ingestion_batch_id);
CREATE INDEX idx_raw_data_timestamp ON explore.raw_data_template(ingestion_timestamp);
CREATE INDEX idx_raw_data_checksum ON explore.raw_data_template(checksum);
CREATE INDEX idx_raw_data_jsonb ON explore.raw_data_template USING GIN(raw_data);

COMMENT ON TABLE explore.raw_data_template IS 'Template for partitioned raw data tables - create per source';
COMMENT ON COLUMN explore.raw_data_template.raw_data IS 'Original data in JSONB format for schema flexibility';
COMMENT ON COLUMN explore.raw_data_template.checksum IS 'SHA-256 hash of raw_data for deduplication';

-- Create partitions for last 3 months and next month
DO $$
DECLARE
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
BEGIN
    FOR i IN -3..1 LOOP
        start_date := date_trunc('month', CURRENT_DATE + (i || ' months')::INTERVAL);
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'raw_data_' || to_char(start_date, 'YYYY_MM');

        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS explore.%I PARTITION OF explore.raw_data_template
            FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );
    END LOOP;
END $$;

-- ============================================================================
-- CHART LAYER - Processed & Standardized Data
-- ============================================================================

-- Chart: Staging Tables Template
-- Cleaned and validated data ready for business logic
CREATE TABLE chart.staging_template (
    staging_id          BIGSERIAL PRIMARY KEY,
    source_system_id    INTEGER NOT NULL REFERENCES explore.source_systems(source_system_id),
    entity_type         VARCHAR(100) NOT NULL,  -- 'customer', 'order', 'product', etc.
    business_key        VARCHAR(200) NOT NULL,
    data_payload        JSONB NOT NULL,
    validation_status   VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'valid', 'invalid', 'quarantine'
    validation_errors   JSONB,
    quality_score       DECIMAL(5,2),  -- 0-100 score
    processed_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    pipeline_run_id     UUID NOT NULL,
    is_duplicate        BOOLEAN DEFAULT FALSE,
    master_record_id    BIGINT,  -- For deduplication tracking

    CONSTRAINT chk_validation_status CHECK (
        validation_status IN ('pending', 'valid', 'invalid', 'quarantine')
    ),
    CONSTRAINT chk_quality_score CHECK (quality_score >= 0 AND quality_score <= 100)
);

CREATE INDEX idx_staging_entity ON chart.staging_template(entity_type, business_key);
CREATE INDEX idx_staging_validation ON chart.staging_template(validation_status) WHERE validation_status != 'valid';
CREATE INDEX idx_staging_pipeline ON chart.staging_template(pipeline_run_id);
CREATE INDEX idx_staging_duplicates ON chart.staging_template(is_duplicate) WHERE is_duplicate = TRUE;

COMMENT ON TABLE chart.staging_template IS 'Template for cleaned staging tables - one per entity type';
COMMENT ON COLUMN chart.staging_template.quality_score IS 'Overall data quality score from validation checks';
COMMENT ON COLUMN chart.staging_template.master_record_id IS 'Points to master record when is_duplicate=true';

-- ============================================================================
-- NAVIGATE LAYER - Business-Ready Curated Data
-- ============================================================================

-- Navigate: Dimension Tables Template
-- Slowly Changing Dimensions (SCD Type 2)
CREATE TABLE navigate.dimension_template (
    surrogate_key       BIGSERIAL PRIMARY KEY,
    business_key        VARCHAR(200) NOT NULL,
    source_system       VARCHAR(100) NOT NULL,

    -- Dimension attributes (varies per dimension)
    attributes          JSONB NOT NULL,

    -- SCD Type 2 fields
    valid_from          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_to            TIMESTAMP WITH TIME ZONE DEFAULT '9999-12-31 23:59:59'::TIMESTAMP WITH TIME ZONE,
    is_current          BOOLEAN DEFAULT TRUE,
    version             INTEGER DEFAULT 1,

    -- Metadata
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    pipeline_run_id     UUID NOT NULL,

    CONSTRAINT chk_valid_period CHECK (valid_from < valid_to)
);

CREATE INDEX idx_dimension_business_key ON navigate.dimension_template(business_key, is_current) WHERE is_current = TRUE;
CREATE INDEX idx_dimension_valid_period ON navigate.dimension_template(valid_from, valid_to);
CREATE INDEX idx_dimension_attributes ON navigate.dimension_template USING GIN(attributes);

COMMENT ON TABLE navigate.dimension_template IS 'Template for SCD Type 2 dimension tables';
COMMENT ON COLUMN navigate.dimension_template.is_current IS 'TRUE for active version, FALSE for historical';

-- Navigate: Fact Tables Template
-- Transaction/Event data
CREATE TABLE navigate.fact_template (
    fact_id             BIGSERIAL,
    business_date       DATE NOT NULL,

    -- Dimension foreign keys (example structure)
    dimension_keys      JSONB NOT NULL,

    -- Measures
    measures            JSONB NOT NULL,

    -- Degenerate dimensions
    transaction_id      VARCHAR(200),

    -- Metadata
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    pipeline_run_id     UUID NOT NULL,

    PRIMARY KEY (fact_id, business_date)
) PARTITION BY RANGE (business_date);

CREATE INDEX idx_fact_business_date ON navigate.fact_template(business_date);
CREATE INDEX idx_fact_pipeline ON navigate.fact_template(pipeline_run_id);
CREATE INDEX idx_fact_dimension_keys ON navigate.fact_template USING GIN(dimension_keys);
CREATE INDEX idx_fact_measures ON navigate.fact_template USING GIN(measures);

COMMENT ON TABLE navigate.fact_template IS 'Template for partitioned fact tables - partition by business_date';
COMMENT ON COLUMN navigate.fact_template.dimension_keys IS 'JSONB object with all dimension foreign keys';
COMMENT ON COLUMN navigate.fact_template.measures IS 'JSONB object with all numeric measures';

-- Create fact table partitions (yearly partitions for performance)
DO $$
DECLARE
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
BEGIN
    FOR i IN -2..1 LOOP
        start_date := date_trunc('year', CURRENT_DATE + (i || ' years')::INTERVAL);
        end_date := start_date + INTERVAL '1 year';
        partition_name := 'fact_' || to_char(start_date, 'YYYY');

        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS navigate.%I PARTITION OF navigate.fact_template
            FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );
    END LOOP;
END $$;

-- ============================================================================
-- Example: Customer Dimension (Navigate Layer)
-- ============================================================================

CREATE TABLE navigate.dim_customer (
    customer_sk         BIGSERIAL PRIMARY KEY,

    -- Business Keys
    customer_id         VARCHAR(50) NOT NULL,
    source_system       VARCHAR(100) NOT NULL,

    -- Customer Attributes
    customer_name       VARCHAR(200),
    customer_type       VARCHAR(20),     -- 'B2B', 'B2C', 'PARTNER'
    industry_code       VARCHAR(10),
    country_code        CHAR(2),         -- ISO 3166-1 alpha-2
    email_address       VARCHAR(255),
    phone_number        VARCHAR(20),     -- E.164 format
    customer_segment    VARCHAR(50),

    -- Address
    address_line1       VARCHAR(200),
    address_line2       VARCHAR(200),
    city                VARCHAR(100),
    postal_code         VARCHAR(20),
    region              VARCHAR(100),

    -- SCD Type 2
    valid_from          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_to            TIMESTAMP WITH TIME ZONE DEFAULT '9999-12-31 23:59:59'::TIMESTAMP WITH TIME ZONE,
    is_current          BOOLEAN DEFAULT TRUE,
    version             INTEGER DEFAULT 1,

    -- Metadata
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active           BOOLEAN DEFAULT TRUE,
    pipeline_run_id     UUID NOT NULL,

    CONSTRAINT chk_customer_type CHECK (customer_type IN ('B2B', 'B2C', 'PARTNER')),
    CONSTRAINT chk_customer_valid_period CHECK (valid_from < valid_to),
    CONSTRAINT uq_customer_current UNIQUE (customer_id, source_system, is_current) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX idx_dim_customer_business_key ON navigate.dim_customer(customer_id, source_system, is_current)
    WHERE is_current = TRUE;
CREATE INDEX idx_dim_customer_name ON navigate.dim_customer(customer_name) WHERE is_current = TRUE;
CREATE INDEX idx_dim_customer_type ON navigate.dim_customer(customer_type) WHERE is_current = TRUE;
CREATE INDEX idx_dim_customer_country ON navigate.dim_customer(country_code) WHERE is_current = TRUE;
CREATE INDEX idx_dim_customer_valid_period ON navigate.dim_customer(valid_from, valid_to);

COMMENT ON TABLE navigate.dim_customer IS 'Customer master dimension - SCD Type 2 with full history';
COMMENT ON COLUMN navigate.dim_customer.customer_sk IS 'Surrogate key for fact table joins';
COMMENT ON COLUMN navigate.dim_customer.customer_id IS 'Natural business key from source system';

-- ============================================================================
-- ARCHIVE LAYER - Long-term Storage
-- ============================================================================

-- Archive: Historical snapshots for compliance
CREATE TABLE archive.snapshot_manifest (
    snapshot_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schema_name         VARCHAR(100) NOT NULL,
    table_name          VARCHAR(100) NOT NULL,
    snapshot_date       DATE NOT NULL,
    row_count           BIGINT,
    storage_path        TEXT,           -- S3/Azure path for external storage
    compression_type    VARCHAR(20),    -- 'gzip', 'parquet', 'none'
    file_size_bytes     BIGINT,
    retention_until     DATE,           -- When can be purged
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by          VARCHAR(100),

    CONSTRAINT uq_snapshot UNIQUE (schema_name, table_name, snapshot_date)
);

CREATE INDEX idx_snapshot_retention ON archive.snapshot_manifest(retention_until);
CREATE INDEX idx_snapshot_table ON archive.snapshot_manifest(schema_name, table_name);

COMMENT ON TABLE archive.snapshot_manifest IS 'Tracks archived data snapshots for compliance (7-year retention)';
COMMENT ON COLUMN archive.snapshot_manifest.retention_until IS 'Date when snapshot can be safely deleted';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to calculate checksum for deduplication
CREATE OR REPLACE FUNCTION explore.calculate_checksum(data JSONB)
RETURNS VARCHAR(64) AS $$
BEGIN
    RETURN encode(digest(data::TEXT, 'sha256'), 'hex');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION explore.calculate_checksum IS 'Calculate SHA-256 hash of JSONB data for deduplication';

-- Function to close SCD Type 2 records
CREATE OR REPLACE FUNCTION navigate.close_dimension_version(
    p_table_name TEXT,
    p_business_key VARCHAR,
    p_source_system VARCHAR,
    p_valid_to TIMESTAMP WITH TIME ZONE DEFAULT NOW()
)
RETURNS VOID AS $$
BEGIN
    EXECUTE format(
        'UPDATE navigate.%I
         SET valid_to = $1, is_current = FALSE, updated_at = NOW()
         WHERE business_key = $2
         AND source_system = $3
         AND is_current = TRUE',
        p_table_name
    ) USING p_valid_to, p_business_key, p_source_system;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION navigate.close_dimension_version IS 'Close current SCD Type 2 record before inserting new version';

-- ============================================================================
-- PERMISSIONS
-- ============================================================================

-- Create roles for data access control
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'atlas_read') THEN
        CREATE ROLE atlas_read;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'atlas_write') THEN
        CREATE ROLE atlas_write;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'atlas_admin') THEN
        CREATE ROLE atlas_admin;
    END IF;
END $$;

-- Grant appropriate permissions
GRANT USAGE ON SCHEMA explore, chart, navigate, archive TO atlas_read;
GRANT SELECT ON ALL TABLES IN SCHEMA explore, chart, navigate, archive TO atlas_read;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA explore, chart, navigate TO atlas_read;

GRANT atlas_read TO atlas_write;
GRANT INSERT, UPDATE ON ALL TABLES IN SCHEMA explore, chart TO atlas_write;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA explore, chart TO atlas_write;

GRANT atlas_write TO atlas_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA explore, chart, navigate, archive TO atlas_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA explore, chart, navigate TO atlas_admin;

-- ============================================================================
-- MAINTENANCE
-- ============================================================================

COMMENT ON SCHEMA explore IS 'Retention: 7 years (compliance), Compression: gzip, Partition: monthly';
COMMENT ON SCHEMA chart IS 'Retention: 3 years, Compression: none, Partition: none';
COMMENT ON SCHEMA navigate IS 'Retention: 1 year + snapshots, Compression: columnar on facts, Partition: yearly on facts';
COMMENT ON SCHEMA archive IS 'Retention: 7 years, Compression: parquet, Storage: S3/Azure cold tier';
