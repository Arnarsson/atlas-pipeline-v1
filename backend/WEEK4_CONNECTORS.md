# Week 4: Database Connectors & Automated Scheduling

**Implementation Date**: January 2026
**Status**: ✅ Complete
**Version**: 1.0.0

## Overview

Week 4 adds comprehensive data source connectivity to the Atlas Data Pipeline Platform, enabling automated data ingestion from PostgreSQL, MySQL, and REST APIs with scheduling capabilities.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Connector Types](#connector-types)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Scheduling](#scheduling)
- [Usage Examples](#usage-examples)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Features

### Core Capabilities

✅ **Multi-Source Connectivity**
- PostgreSQL with connection pooling (asyncpg)
- MySQL with async support (aiomysql)
- REST API with authentication and pagination

✅ **Incremental Loading**
- Timestamp-based change data capture
- Automatic state tracking
- Configurable sync columns

✅ **Automated Scheduling**
- Cron-based scheduling via Celery Beat
- Manual sync triggers via API
- Health monitoring and alerts

✅ **Production Features**
- Connection pooling for databases
- Retry logic with exponential backoff
- Rate limiting for APIs
- Comprehensive error handling

## Architecture

### Component Structure

```
app/
├── connectors/
│   ├── base.py              # Base connector interface
│   ├── postgresql.py        # PostgreSQL implementation
│   ├── mysql.py             # MySQL implementation
│   ├── rest_api.py          # REST API implementation
│   └── registry.py          # Connector registry
└── scheduler/
    ├── celery_app.py        # Celery configuration
    └── tasks.py             # Scheduled tasks
```

### Database Schema

```
pipeline.connectors         # Connector configurations
pipeline.connector_state    # Incremental loading state
pipeline.scheduled_runs     # Execution history
```

## Connector Types

### 1. PostgreSQL Connector

**Features**:
- Async connection pooling (2-10 connections)
- Schema introspection
- Incremental loading support
- Transaction management

**Configuration**:
```json
{
  "source_type": "postgresql",
  "source_name": "production_db",
  "host": "localhost",
  "port": 5432,
  "database": "mydb",
  "username": "user",
  "password": "password",
  "additional_params": {
    "sslmode": "require"
  }
}
```

### 2. MySQL Connector

**Features**:
- Async connection pooling
- Information schema queries
- CDC via timestamp or auto_increment
- MySQL-specific SQL handling

**Configuration**:
```json
{
  "source_type": "mysql",
  "source_name": "legacy_mysql",
  "host": "mysql.example.com",
  "port": 3306,
  "database": "production",
  "username": "user",
  "password": "password",
  "additional_params": {
    "charset": "utf8mb4"
  }
}
```

### 3. REST API Connector

**Features**:
- Multiple authentication types (Bearer, API Key, Basic, OAuth2)
- Pagination strategies (offset, cursor, page-based)
- Rate limiting with backoff
- Response parsing (JSON, XML, CSV)

**Configuration**:
```json
{
  "source_type": "rest_api",
  "source_name": "external_api",
  "base_url": "https://api.example.com",
  "auth_type": "bearer",
  "auth_token": "your_token",
  "additional_params": {
    "pagination_type": "offset",
    "page_size": 100,
    "data_key": "results"
  }
}
```

### Authentication Types

#### Bearer Token
```json
{
  "auth_type": "bearer",
  "auth_token": "your_bearer_token"
}
```

#### API Key
```json
{
  "auth_type": "apikey",
  "api_key": "your_api_key",
  "additional_params": {
    "header_name": "X-Custom-API-Key"  // Optional
  }
}
```

#### Basic Authentication
```json
{
  "auth_type": "basic",
  "username": "user",
  "password": "password"
}
```

### Pagination Strategies

#### Offset/Limit Pagination
```json
{
  "pagination_type": "offset",
  "page_size": 100
}
```
Generates: `/api/data?offset=0&limit=100`, `/api/data?offset=100&limit=100`, ...

#### Cursor-Based Pagination
```json
{
  "pagination_type": "cursor",
  "cursor_key": "next_cursor"
}
```
Expects response: `{"data": [...], "next_cursor": "abc123"}`

#### Page-Based Pagination
```json
{
  "pagination_type": "page",
  "page_size": 50
}
```
Generates: `/api/data?page=1&page_size=50`, `/api/data?page=2&page_size=50`, ...

## Configuration

### Connector Registration

Register a connector via API:

```bash
curl -X POST http://localhost:8000/connectors/ \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "postgresql",
    "source_name": "my_database",
    "config": {
      "source_type": "postgresql",
      "source_name": "my_database",
      "host": "localhost",
      "port": 5432,
      "database": "mydb",
      "username": "user",
      "password": "password"
    },
    "schedule_cron": "0 * * * *",
    "enabled": true,
    "incremental": true,
    "timestamp_column": "updated_at",
    "table": "users"
  }'
```

### Cron Schedule Format

Standard cron format: `minute hour day month weekday`

**Examples**:
- `0 * * * *` - Every hour at :00
- `*/15 * * * *` - Every 15 minutes
- `0 0 * * *` - Daily at midnight
- `0 */6 * * *` - Every 6 hours
- `0 9 * * 1-5` - Weekdays at 9 AM

### Incremental Loading

Enable incremental loading to sync only new/updated records:

```json
{
  "incremental": true,
  "timestamp_column": "updated_at"
}
```

**How it works**:
1. First sync: Fetch all records
2. Store max timestamp value
3. Subsequent syncs: Fetch only records where `timestamp_column > last_sync_timestamp`

## API Endpoints

### Connector Management

#### List Connector Types
```
GET /connectors/types
```

Response:
```json
{
  "connector_types": ["postgresql", "mysql", "rest_api"],
  "total": 3
}
```

#### Register Connector
```
POST /connectors/
```

Request body: See [Connector Registration](#connector-registration)

#### List All Connectors
```
GET /connectors/
```

Response:
```json
[
  {
    "connector_id": "uuid-here",
    "source_type": "postgresql",
    "source_name": "my_database",
    "enabled": true,
    "schedule_cron": "0 * * * *",
    "last_sync_at": "2026-01-09T10:00:00Z",
    "last_sync_status": "completed"
  }
]
```

#### Get Connector Details
```
GET /connectors/{connector_id}
```

#### Update Connector
```
PUT /connectors/{connector_id}
```

#### Delete Connector
```
DELETE /connectors/{connector_id}
```

### Connector Operations

#### Test Connection
```
POST /connectors/{connector_id}/test
```

Response:
```json
{
  "connector_id": "uuid-here",
  "source_name": "my_database",
  "connection_status": "success",
  "message": "Connection test successful"
}
```

#### Manual Sync
```
POST /connectors/{connector_id}/sync
```

Response:
```json
{
  "connector_id": "uuid-here",
  "run_id": "celery-task-id",
  "status": "queued",
  "message": "Manual sync queued for connector uuid-here"
}
```

#### Sync History
```
GET /connectors/{connector_id}/history
```

Response:
```json
{
  "connector_id": "uuid-here",
  "source_name": "my_database",
  "total_runs": 24,
  "runs": [
    {
      "run_id": "uuid",
      "triggered_by": "schedule",
      "started_at": "2026-01-09T10:00:00Z",
      "completed_at": "2026-01-09T10:01:30Z",
      "status": "completed",
      "rows_processed": 1500,
      "duration_seconds": 90
    }
  ]
}
```

## Scheduling

### Celery Setup

Start Celery worker:
```bash
celery -A app.scheduler.celery_app worker --loglevel=info
```

Start Celery Beat (scheduler):
```bash
celery -A app.scheduler.celery_app beat --loglevel=info
```

### Scheduled Tasks

#### Hourly Sync
- Task: `sync_all_scheduled_sources`
- Schedule: Every hour at :00
- Action: Runs all enabled connectors with schedules

#### Health Check
- Task: `test_connector_health`
- Schedule: Every 15 minutes
- Action: Tests all enabled connectors

### Manual Task Execution

Execute sync task manually:
```python
from app.scheduler.tasks import run_connector_pipeline

# Queue task
task = run_connector_pipeline.delay(connector_id, triggered_by="manual")

# Get task result
result = task.get()
```

## Usage Examples

### Example 1: PostgreSQL Incremental Sync

```python
import httpx

# Register connector
connector = {
    "source_type": "postgresql",
    "source_name": "users_db",
    "config": {
        "source_type": "postgresql",
        "source_name": "users_db",
        "host": "db.example.com",
        "port": 5432,
        "database": "production",
        "username": "readonly",
        "password": "secure_password"
    },
    "schedule_cron": "0 */2 * * *",  # Every 2 hours
    "enabled": true,
    "incremental": true,
    "timestamp_column": "updated_at",
    "table": "users",
    "description": "Production users table"
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/connectors/",
        json=connector
    )
    connector_data = response.json()

    # Test connection
    test_response = await client.post(
        f"http://localhost:8000/connectors/{connector_data['connector_id']}/test"
    )
    print(test_response.json())
```

### Example 2: REST API with Pagination

```python
# REST API with cursor pagination
api_connector = {
    "source_type": "rest_api",
    "source_name": "github_api",
    "config": {
        "source_type": "rest_api",
        "source_name": "github_api",
        "base_url": "https://api.github.com",
        "auth_type": "bearer",
        "auth_token": "ghp_your_token",
        "additional_params": {
            "pagination_type": "cursor",
            "cursor_key": "next",
            "data_key": "items"
        }
    },
    "schedule_cron": "0 0 * * *",  # Daily at midnight
    "enabled": true,
    "query": "/search/repositories?q=python",
    "description": "GitHub trending Python repos"
}

# Register and sync
response = requests.post(
    "http://localhost:8000/connectors/",
    json=api_connector
)
connector_id = response.json()["connector_id"]

# Trigger manual sync
sync_response = requests.post(
    f"http://localhost:8000/connectors/{connector_id}/sync"
)
print(f"Sync queued: {sync_response.json()['run_id']}")
```

### Example 3: MySQL CDC

```python
# MySQL with incremental loading via auto_increment
mysql_connector = {
    "source_type": "mysql",
    "source_name": "orders_db",
    "config": {
        "source_type": "mysql",
        "source_name": "orders_db",
        "host": "mysql.example.com",
        "port": 3306,
        "database": "ecommerce",
        "username": "etl_user",
        "password": "password"
    },
    "schedule_cron": "*/30 * * * *",  # Every 30 minutes
    "enabled": true,
    "incremental": true,
    "timestamp_column": "id",  # Use auto_increment ID
    "table": "orders",
    "description": "E-commerce orders"
}
```

## Testing

### Unit Tests

Run unit tests:
```bash
pytest tests/unit/test_connectors.py -v
```

### Integration Tests

Run integration tests (requires running databases):
```bash
# Start test databases
docker-compose -f docker-compose.test.yml up -d

# Run tests
pytest tests/integration/test_postgresql_connector.py -v
pytest tests/integration/test_mysql_connector.py -v
pytest tests/integration/test_rest_api_connector.py -v

# Cleanup
docker-compose -f docker-compose.test.yml down
```

### End-to-End Test

```bash
pytest tests/integration/test_week4_e2e.py -v
```

## Troubleshooting

### Connection Failures

**PostgreSQL connection timeout**:
```python
# Add connection timeout to config
"additional_params": {
    "command_timeout": 60,
    "server_settings": {
        "application_name": "atlas_pipeline"
    }
}
```

**MySQL connection refused**:
- Check host/port are correct
- Verify firewall allows connections
- Ensure user has remote access: `GRANT ALL ON *.* TO 'user'@'%'`

### Incremental Loading Issues

**No new records fetched**:
- Check `timestamp_column` exists in table
- Verify column contains valid timestamps
- Check `last_sync_timestamp` in state table

**Duplicate records**:
- Ensure timestamp column is indexed
- Use unique constraint or deduplication in Chart layer

### REST API Issues

**Rate limiting (429)**:
- Increase `_rate_limit_delay` in connector config
- Implement exponential backoff (already built-in)
- Check API documentation for rate limits

**Pagination not working**:
- Verify `pagination_type` matches API (offset/cursor/page)
- Check `data_key` points to correct response field
- Inspect API responses in logs

### Celery Issues

**Tasks not executing**:
```bash
# Check Celery worker is running
celery -A app.scheduler.celery_app inspect active

# Check Beat scheduler is running
celery -A app.scheduler.celery_app inspect scheduled

# Verify Redis is accessible
redis-cli ping
```

**Task failures**:
```bash
# View task traceback
celery -A app.scheduler.celery_app inspect active

# Check worker logs
tail -f celery_worker.log
```

## Performance Optimization

### Database Connectors

1. **Connection Pooling**: Adjust pool size based on workload
   ```python
   "additional_params": {
       "min_size": 5,
       "max_size": 20
   }
   ```

2. **Query Optimization**: Use indexes on timestamp columns
   ```sql
   CREATE INDEX idx_updated_at ON users(updated_at);
   ```

3. **Batch Size**: For large tables, add LIMIT to queries
   ```python
   "query": "SELECT * FROM large_table ORDER BY id LIMIT 10000"
   ```

### REST API Connectors

1. **Parallel Requests**: For independent endpoints, use multiple connectors
2. **Caching**: Cache frequently accessed reference data
3. **Compression**: Enable gzip if API supports it

## Security Best Practices

### Credential Management

1. **Never commit credentials** to version control
2. **Encrypt passwords** before storing in database
3. **Use environment variables** for sensitive data
4. **Rotate credentials** regularly
5. **Use read-only accounts** when possible

### Network Security

1. **Use SSL/TLS** for database connections
2. **Whitelist IPs** for database access
3. **VPN or SSH tunnels** for sensitive data sources
4. **API key rotation** for external APIs

## Next Steps

**Week 5**: Database Persistence
- Replace in-memory storage with PostgreSQL
- Implement connector state management
- Add run history retention policies

**Week 6**: Advanced Features
- WebSocket support for real-time data
- S3/Object storage connectors
- GraphQL API support

## Support

For issues or questions:
- Check logs: `tail -f logs/connectors.log`
- Review API docs: `http://localhost:8000/docs`
- Run health check: `GET /connectors/{id}/test`
