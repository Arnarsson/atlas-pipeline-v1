# Airbyte Docker Integration Guide

Atlas Pipeline now supports Docker-based Airbyte connector execution, enabling access to 100+ official Airbyte connectors.

## Overview

Atlas provides two modes for Airbyte connector execution:

| Mode | Use Case | Requirements | Connectors |
|------|----------|--------------|------------|
| **Docker-based** | Production | Docker installed | 100+ official images |
| **PyAirbyte SDK** | Development | Python packages | 70+ SDK connectors |

## Quick Start

### Prerequisites

1. **Docker installed and running**
   ```bash
   docker --version
   docker info
   ```

2. **Atlas backend running**
   ```bash
   cd backend
   python3 simple_main.py
   ```

### Check Docker Availability

```bash
curl http://localhost:8000/atlas-intelligence/docker/health
```

Response:
```json
{
  "docker_available": true,
  "status": "healthy",
  "message": "Docker is ready for Airbyte connector execution",
  "total_connectors": 100,
  "execution_mode": "docker"
}
```

## API Endpoints

### List Available Connectors

```bash
# List all connectors
curl http://localhost:8000/atlas-intelligence/docker/connectors

# Filter by category
curl "http://localhost:8000/atlas-intelligence/docker/connectors?category=database"

# Search connectors
curl "http://localhost:8000/atlas-intelligence/docker/connectors?search=postgres"
```

### Get Connector Categories

```bash
curl http://localhost:8000/atlas-intelligence/docker/categories
```

Response:
```json
{
  "categories": [
    {"id": "database", "name": "Database", "count": 20},
    {"id": "marketing", "name": "Marketing", "count": 15},
    {"id": "crm", "name": "Crm", "count": 10}
  ],
  "total_connectors": 100
}
```

### Get Connector Specification

Get the configuration schema for a connector:

```bash
curl http://localhost:8000/atlas-intelligence/docker/connectors/source-postgres/spec
```

Response includes the JSON Schema for configuration fields.

### Test Connection (CHECK)

```bash
curl -X POST http://localhost:8000/atlas-intelligence/docker/check \
  -H "Content-Type: application/json" \
  -d '{
    "connector_name": "source-postgres",
    "config": {
      "host": "localhost",
      "port": 5432,
      "database": "mydb",
      "username": "user",
      "password": "pass"
    }
  }'
```

Response:
```json
{
  "status": "succeeded",
  "message": "Connection successful",
  "connector_name": "source-postgres",
  "success": true
}
```

### Discover Streams (DISCOVER)

```bash
curl -X POST http://localhost:8000/atlas-intelligence/docker/discover \
  -H "Content-Type: application/json" \
  -d '{
    "connector_name": "source-postgres",
    "config": {
      "host": "localhost",
      "port": 5432,
      "database": "mydb",
      "username": "user",
      "password": "pass"
    }
  }'
```

Response:
```json
{
  "connector_name": "source-postgres",
  "streams": [
    {
      "name": "users",
      "namespace": "public",
      "supported_sync_modes": ["full_refresh", "incremental"],
      "source_defined_cursor": true,
      "default_cursor_field": ["updated_at"],
      "primary_key": [["id"]],
      "json_schema": {...}
    }
  ],
  "total_streams": 5
}
```

### Read Data (READ)

```bash
curl -X POST http://localhost:8000/atlas-intelligence/docker/read \
  -H "Content-Type: application/json" \
  -d '{
    "connector_name": "source-postgres",
    "config": {
      "host": "localhost",
      "port": 5432,
      "database": "mydb",
      "username": "user",
      "password": "pass"
    },
    "stream_name": "users",
    "incremental": false
  }'
```

Response:
```json
{
  "status": "success",
  "connector_name": "source-postgres",
  "stream_name": "users",
  "records_count": 100,
  "columns": ["id", "name", "email", "created_at"],
  "data": [...],
  "state": null,
  "message": "Read 100 records from users"
}
```

### Incremental Read with State

```bash
curl -X POST http://localhost:8000/atlas-intelligence/docker/read \
  -H "Content-Type: application/json" \
  -d '{
    "connector_name": "source-postgres",
    "config": {...},
    "stream_name": "users",
    "incremental": true,
    "cursor_field": "updated_at",
    "state": {"cursor": "2024-01-01T00:00:00Z"}
  }'
```

## Python Usage

### Using the Adapter

```python
from app.connectors.airbyte import create_airbyte_adapter

# Create adapter
adapter = create_airbyte_adapter(
    "source-postgres",
    {
        "host": "localhost",
        "port": 5432,
        "database": "mydb",
        "username": "user",
        "password": "pass"
    }
)

# Test connection
await adapter.test_connection()

# List available streams
streams = await adapter.list_tables()
print(streams)  # ['users', 'orders', 'products']

# Get schema
schema = await adapter.get_schema("users")
print(schema)  # {'id': 'INTEGER', 'name': 'VARCHAR', ...}

# Read data
df = await adapter.get_data(table="users")
print(df.head())

# Incremental read
df = await adapter.get_data(
    table="users",
    incremental=True,
    timestamp_column="updated_at"
)

# Close adapter
await adapter.close()
```

### Using the Docker Executor Directly

```python
from app.connectors.airbyte import (
    get_docker_executor,
    check_docker_available,
    pull_image
)

# Check Docker availability
if await check_docker_available():
    executor = get_docker_executor()

    # Get connector spec
    spec = await executor.spec("airbyte/source-postgres:latest")
    print(spec.connectionSpecification)

    # Test connection
    status = await executor.check(
        "airbyte/source-postgres:latest",
        {"host": "localhost", "port": 5432, ...}
    )
    print(status.status)  # SUCCEEDED or FAILED

    # Discover streams
    catalog = await executor.discover(
        "airbyte/source-postgres:latest",
        {"host": "localhost", ...}
    )
    for stream in catalog.streams:
        print(f"Stream: {stream.name}")
```

### Using the Registry

```python
from app.connectors.airbyte import (
    list_connectors,
    search_connectors,
    get_connector_image,
    get_connector_info,
    ConnectorCategory
)

# List all connectors
connectors = list_connectors()
print(f"Total: {len(connectors)}")

# Filter by category
databases = list_connectors(category=ConnectorCategory.DATABASE)

# Search
results = search_connectors("postgres")

# Get specific connector
info = get_connector_info("source-postgres")
print(info.docker_image)  # airbyte/source-postgres:latest
```

## Available Connectors

### Database (20+)
- PostgreSQL, MySQL, SQL Server, MongoDB
- Oracle, CockroachDB, ClickHouse
- Redshift, BigQuery, Snowflake
- DynamoDB, Elasticsearch, Neo4j

### CRM (10+)
- Salesforce, HubSpot, Pipedrive
- Zoho CRM, Freshsales, Intercom
- Zendesk Support, Drift

### Marketing (15+)
- Google Ads, Facebook Marketing
- LinkedIn Ads, Twitter Ads, TikTok
- Mailchimp, SendGrid, Klaviyo
- Braze, Iterable, Marketo

### Analytics (10+)
- Google Analytics (UA & GA4)
- Mixpanel, Amplitude, Segment
- Heap, PostHog, Pendo

### E-commerce (10+)
- Shopify, Stripe, WooCommerce
- Amazon Seller Partner, Square
- PayPal, Chargebee, Recharge

### Development (10+)
- GitHub, GitLab, Bitbucket
- Jira, Linear, PagerDuty
- Datadog, Sentry

### And More...
- Finance: QuickBooks, Xero, NetSuite
- HR: Greenhouse, BambooHR, Workday
- Communication: Slack, Teams, Twilio
- Storage: S3, GCS, Azure Blob

## Configuration Examples

### PostgreSQL

```json
{
  "host": "localhost",
  "port": 5432,
  "database": "mydb",
  "username": "user",
  "password": "pass",
  "ssl_mode": "require"
}
```

### MySQL

```json
{
  "host": "localhost",
  "port": 3306,
  "database": "mydb",
  "username": "user",
  "password": "pass"
}
```

### Stripe

```json
{
  "account_id": "acct_xxx",
  "api_key": "sk_live_xxx",
  "start_date": "2024-01-01T00:00:00Z"
}
```

### Salesforce

```json
{
  "client_id": "xxx",
  "client_secret": "xxx",
  "refresh_token": "xxx",
  "is_sandbox": false,
  "start_date": "2024-01-01T00:00:00Z"
}
```

### GitHub

```json
{
  "credentials": {
    "option_title": "PAT Credentials",
    "personal_access_token": "ghp_xxx"
  },
  "repository": "owner/repo",
  "start_date": "2024-01-01T00:00:00Z"
}
```

## Troubleshooting

### Docker Not Available

```
Error: Docker is not available. Please start Docker.
```

**Solution**: Start Docker Desktop or the Docker daemon:
```bash
# macOS/Windows
# Start Docker Desktop from applications

# Linux
sudo systemctl start docker
```

### Image Pull Failed

```
Error: Failed to pull image airbyte/source-xxx:latest
```

**Solution**:
1. Check internet connectivity
2. Verify Docker can pull images: `docker pull hello-world`
3. Check Docker Hub rate limits

### Connection Test Failed

```
Error: Connection refused
```

**Solution**:
1. Verify the source is accessible
2. Check firewall rules
3. For Docker networking, use `host.docker.internal` instead of `localhost`

### Timeout

```
Error: Execution timed out after 3600s
```

**Solution**:
1. Check source connectivity
2. Reduce dataset size with filters
3. Increase timeout in ExecutorConfig

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Atlas Pipeline                          │
├─────────────────────────────────────────────────────────────┤
│  API Layer (/atlas-intelligence/docker/*)                   │
├─────────────────────────────────────────────────────────────┤
│  Adapter Layer (AirbyteSourceAdapter)                       │
│  - Implements SourceConnector interface                     │
│  - Converts Airbyte format to DataFrame                     │
├─────────────────────────────────────────────────────────────┤
│  Docker Executor (AirbyteDockerExecutor)                    │
│  - Runs containers: docker run airbyte/source-xxx           │
│  - Commands: SPEC, CHECK, DISCOVER, READ                    │
├─────────────────────────────────────────────────────────────┤
│  Protocol Layer (AirbyteMessage)                            │
│  - Message types: RECORD, STATE, CATALOG, SPEC, etc.        │
│  - Parses JSON stdout from containers                       │
├─────────────────────────────────────────────────────────────┤
│  Registry (100+ ConnectorInfo)                              │
│  - Connector name → Docker image mapping                    │
│  - Categories: database, crm, marketing, etc.               │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

The migration `008_airbyte_integration.sql` adds:

- `pipeline.airbyte_catalogs` - Cached schema discoveries
- `pipeline.airbyte_state` - Per-stream sync state
- `pipeline.airbyte_sync_stats` - Stream-level metrics
- `pipeline.airbyte_connector_registry` - Local connector cache

## Performance Tips

1. **Pull images in advance**:
   ```bash
   curl -X POST http://localhost:8000/atlas-intelligence/docker/connectors/source-postgres/pull
   ```

2. **Use incremental syncs** for large datasets:
   ```json
   {"incremental": true, "cursor_field": "updated_at"}
   ```

3. **Configure resource limits** in ExecutorConfig:
   ```python
   config = ExecutorConfig(
       memory_limit="4g",
       cpu_limit=4.0,
       timeout_seconds=7200
   )
   ```

4. **Stream large datasets** instead of buffering:
   ```python
   async for df_batch in adapter.get_data_stream(table="large_table"):
       process(df_batch)
   ```

## Security Considerations

1. **Credentials**: Store in environment variables, not in code
2. **Network**: Docker runs with `--network=host` by default
3. **Resources**: Containers have memory/CPU limits
4. **Cleanup**: Containers are removed after execution (`--rm`)

## Related Documentation

- [Airbyte Protocol](https://docs.airbyte.com/understanding-airbyte/airbyte-protocol)
- [Airbyte Connectors](https://docs.airbyte.com/integrations/)
- [Atlas Pipeline API](/docs)
