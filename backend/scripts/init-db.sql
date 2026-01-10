-- ============================================================================
-- Atlas Data Pipeline Platform - Database Initialization Script
-- ============================================================================
-- Description: Creates multiple databases for medallion architecture
-- Usage: Automatically executed by docker-entrypoint-initdb.d
-- ============================================================================

-- Create databases for different layers
CREATE DATABASE atlas_pipeline;
CREATE DATABASE atlas_bronze;
CREATE DATABASE atlas_silver;
CREATE DATABASE atlas_gold;
CREATE DATABASE atlas_pipeline_test;

-- Create user for Prefect (if not exists)
DO
$$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'prefect_user') THEN
        CREATE USER prefect_user WITH PASSWORD 'changethis';
    END IF;
END
$$;

-- Create Prefect database
CREATE DATABASE prefect;
GRANT ALL PRIVILEGES ON DATABASE prefect TO prefect_user;

-- Grant privileges to main user on all databases
GRANT ALL PRIVILEGES ON DATABASE atlas_pipeline TO atlas_user;
GRANT ALL PRIVILEGES ON DATABASE atlas_bronze TO atlas_user;
GRANT ALL PRIVILEGES ON DATABASE atlas_silver TO atlas_user;
GRANT ALL PRIVILEGES ON DATABASE atlas_gold TO atlas_user;
GRANT ALL PRIVILEGES ON DATABASE atlas_pipeline_test TO atlas_user;

-- Switch to main database
\c atlas_pipeline;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Create extensions for other databases
\c atlas_bronze;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\c atlas_silver;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\c atlas_gold;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\c atlas_pipeline_test;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Switch back to main database
\c atlas_pipeline;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS pipeline;
CREATE SCHEMA IF NOT EXISTS monitoring;
CREATE SCHEMA IF NOT EXISTS audit;

-- Grant usage on schemas
GRANT USAGE ON SCHEMA pipeline TO atlas_user;
GRANT USAGE ON SCHEMA monitoring TO atlas_user;
GRANT USAGE ON SCHEMA audit TO atlas_user;

-- Grant all privileges on all tables in schemas
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA pipeline TO atlas_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA monitoring TO atlas_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA audit TO atlas_user;

-- Grant all privileges on all sequences in schemas
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA pipeline TO atlas_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA monitoring TO atlas_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA audit TO atlas_user;

-- Default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA pipeline GRANT ALL ON TABLES TO atlas_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA monitoring GRANT ALL ON TABLES TO atlas_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT ALL ON TABLES TO atlas_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA pipeline GRANT ALL ON SEQUENCES TO atlas_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA monitoring GRANT ALL ON SEQUENCES TO atlas_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT ALL ON SEQUENCES TO atlas_user;

-- Success message
\echo 'Database initialization complete!'
