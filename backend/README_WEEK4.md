# Week 4: Database Connectors & Automated Scheduling - Quick Start

**Status**: ✅ Complete | **Date**: January 9, 2026

## What's New in Week 4

Atlas can now automatically ingest data from:
- **PostgreSQL databases** with incremental loading
- **MySQL databases** with change data capture
- **REST APIs** with authentication and pagination
- **Scheduled syncs** via Celery Beat

## Quick Start (5 Minutes)

### 1. Install Dependencies

```bash
cd /Users/sven/Desktop/MCP/.worktrees/atlas-api
pip install aiomysql
```

All other dependencies already installed.

### 2. Apply Database Migration

```bash
# Connect to PostgreSQL
docker exec -it atlas-db psql -U atlas_user -d atlas_pipeline

# Run migration
\i /app/database/migrations/006_week4_connectors.sql

# Verify tables created
\dt pipeline.connectors
\dt pipeline.connector_state
\dt pipeline.scheduled_runs
```

### 3. Start the API

```bash
python3 simple_main.py
```

API running at: http://localhost:8000

### 4. Test Connector System

```bash
# Run automated tests
./test_week4.sh
```

## Basic Usage

### Create a PostgreSQL Connector

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

### List All Connectors

```bash
curl http://localhost:8000/connectors/
```

### Test Connection

```bash
curl -X POST http://localhost:8000/connectors/{connector_id}/test
```

### Trigger Manual Sync

```bash
curl -X POST http://localhost:8000/connectors/{connector_id}/sync
```

## Connector Types

### 1. PostgreSQL

**Best for**: Transactional databases, data warehouses
**Features**: Connection pooling, async queries, schema introspection

Example:
```json
{
  "source_type": "postgresql",
  "config": {
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "username": "user",
    "password": "password"
  }
}
```

### 2. MySQL

**Best for**: Legacy systems, WordPress databases
**Features**: Async operations, CDC via timestamp/auto_increment

Example:
```json
{
  "source_type": "mysql",
  "config": {
    "host": "localhost",
    "port": 3306,
    "database": "mydb",
    "username": "user",
    "password": "password"
  }
}
```

### 3. REST API

**Best for**: External APIs, SaaS integrations
**Features**: Multiple auth types, pagination, rate limiting

Example:
```json
{
  "source_type": "rest_api",
  "config": {
    "base_url": "https://api.example.com",
    "auth_type": "bearer",
    "auth_token": "your_token",
    "additional_params": {
      "pagination_type": "offset",
      "page_size": 100
    }
  }
}
```

## Scheduling

### Cron Syntax

Format: `minute hour day month weekday`

**Common schedules**:
- Every hour: `0 * * * *`
- Every 15 minutes: `*/15 * * * *`
- Daily at midnight: `0 0 * * *`
- Weekdays at 9 AM: `0 9 * * 1-5`

### Start Celery (for scheduled syncs)

```bash
# Terminal 1: Start worker
celery -A app.scheduler.celery_app worker --loglevel=info

# Terminal 2: Start beat scheduler
celery -A app.scheduler.celery_app beat --loglevel=info
```

## Incremental Loading

Enable incremental loading to sync only new/updated records:

```json
{
  "incremental": true,
  "timestamp_column": "updated_at"
}
```

**How it works**:
1. First sync: Fetches all records
2. Stores max timestamp in `pipeline.connector_state`
3. Subsequent syncs: Fetch only `WHERE updated_at > last_sync_timestamp`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/connectors/types` | List connector types |
| POST | `/connectors/` | Create connector |
| GET | `/connectors/` | List all connectors |
| GET | `/connectors/{id}` | Get connector details |
| PUT | `/connectors/{id}` | Update connector |
| DELETE | `/connectors/{id}` | Delete connector |
| POST | `/connectors/{id}/test` | Test connection |
| POST | `/connectors/{id}/sync` | Manual sync |
| GET | `/connectors/{id}/history` | Sync history |

## Interactive API Documentation

Open browser: http://localhost:8000/docs

Try all endpoints with Swagger UI.

## Example Workflows

### Workflow 1: Hourly User Sync from PostgreSQL

```bash
# 1. Create connector
CONNECTOR_ID=$(curl -s -X POST http://localhost:8000/connectors/ \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "postgresql",
    "source_name": "users_hourly",
    "config": {...},
    "schedule_cron": "0 * * * *",
    "incremental": true,
    "timestamp_column": "updated_at",
    "table": "users"
  }' | jq -r '.connector_id')

# 2. Test connection
curl -X POST http://localhost:8000/connectors/$CONNECTOR_ID/test

# 3. Trigger first sync
curl -X POST http://localhost:8000/connectors/$CONNECTOR_ID/sync

# 4. Check history
curl http://localhost:8000/connectors/$CONNECTOR_ID/history
```

### Workflow 2: Daily API Data Pull

```bash
# Create REST API connector
curl -X POST http://localhost:8000/connectors/ \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "rest_api",
    "source_name": "github_repos",
    "config": {
      "base_url": "https://api.github.com",
      "auth_type": "bearer",
      "auth_token": "ghp_token",
      "additional_params": {
        "pagination_type": "cursor",
        "page_size": 100
      }
    },
    "schedule_cron": "0 0 * * *",
    "query": "/search/repositories?q=python"
  }'
```

## Troubleshooting

### API not starting?
```bash
# Check if port 8000 is already in use
lsof -i :8000

# Kill existing process
kill -9 $(lsof -t -i :8000)

# Restart
python3 simple_main.py
```

### Connection test failing?
- Verify database is running: `docker ps`
- Check credentials in connector config
- Test connection manually: `psql -h localhost -U user -d mydb`

### Scheduled syncs not running?
- Check Celery worker is running: `celery inspect active`
- Check Beat scheduler is running: `celery inspect scheduled`
- Verify Redis is accessible: `redis-cli ping`

### No data being synced?
- Check connector is enabled: `GET /connectors/{id}`
- Verify table/query exists in source
- Check sync history for errors: `GET /connectors/{id}/history`

## Next Steps

1. **Read full documentation**: `WEEK4_CONNECTORS.md`
2. **Configure your connectors**: See configuration examples
3. **Set up scheduling**: Start Celery worker and beat
4. **Monitor syncs**: Use `/connectors/{id}/history` endpoint

## Files Created

```
app/connectors/
├── base.py              # Base connector interface
├── postgresql.py        # PostgreSQL connector
├── mysql.py             # MySQL connector
├── rest_api.py          # REST API connector
└── registry.py          # Connector registry

app/scheduler/
├── celery_app.py        # Celery configuration
└── tasks.py             # Scheduled tasks

database/migrations/
└── 006_week4_connectors.sql  # Database schema

tests/unit/
└── test_connectors.py   # Unit tests

Documentation:
├── WEEK4_CONNECTORS.md  # Full user guide
├── WEEK4_SUMMARY.md     # Implementation summary
└── README_WEEK4.md      # This file
```

## Support

**API Documentation**: http://localhost:8000/docs
**Full Guide**: See `WEEK4_CONNECTORS.md`
**Implementation Details**: See `WEEK4_SUMMARY.md`

---

**Week 4 Achievement**: Transformed Atlas from CSV-only to a multi-source data platform with automated scheduling! 🚀
