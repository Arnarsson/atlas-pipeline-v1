# AtlasIntelligence Production Deployment Guide

**Version**: 1.0.0
**Last Updated**: January 12, 2026
**Status**: Production Ready (90%)

---

## Overview

AtlasIntelligence is a unified connector platform providing access to 300+ data sources through:
- **13 MCP Connectors** - Lightweight, fast integrations (GitHub, Stripe, Salesforce, etc.)
- **70+ PyAirbyte Sources** - Expandable to 300+ via Airbyte protocol
- **N8N Workflows** - Automation and orchestration

This guide covers production deployment, configuration, and operations.

---

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Disk | 20 GB | 50+ GB SSD |
| Python | 3.10+ | 3.11+ |
| Node.js | 18+ | 20+ |

### Dependencies

**Backend:**
```bash
pip install fastapi uvicorn pydantic python-dotenv
pip install airbyte  # Optional: for PyAirbyte real connectors
```

**Frontend:**
```bash
npm install
```

---

## Configuration

### Environment Variables

Create `.env` file in the backend directory:

```bash
# AtlasIntelligence Configuration
ATLAS_INTELLIGENCE_ENABLED=true
ATLAS_INTELLIGENCE_MAX_CONCURRENT_JOBS=5
ATLAS_INTELLIGENCE_STATE_PERSISTENCE=postgresql

# Database (for state persistence)
DATABASE_URL=postgresql://atlas_user:password@localhost:5432/atlas_pipeline

# Redis (for job queue)
REDIS_URL=redis://localhost:6379

# MCP Connector API Keys (optional - can be set via UI)
GITHUB_API_KEY=ghp_xxxxxxxxxxxxx
STRIPE_API_KEY=sk_live_xxxxxxxxxxxxx
HUBSPOT_API_KEY=pat-xxxxxxxxxxxxx
SALESFORCE_API_KEY=xxxxxxxxxxxxx

# PyAirbyte Configuration
PYAIRBYTE_CACHE_DIR=/var/atlas/airbyte_cache
PYAIRBYTE_LOG_LEVEL=INFO
```

### API Keys Configuration

API keys can be configured:
1. **Via Environment Variables** - Set at deployment time
2. **Via UI** - Use the "API Keys" button in AtlasIntelligence dashboard
3. **Via API** - `POST /atlas-intelligence/credentials`

---

## Deployment Options

### Option 1: Docker Compose (Recommended)

```yaml
# docker-compose.atlas-intelligence.yml
version: '3.8'

services:
  atlas-backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://atlas_user:password@db:5432/atlas_pipeline
      - REDIS_URL=redis://redis:6379
      - ATLAS_INTELLIGENCE_ENABLED=true
      - ATLAS_INTELLIGENCE_MAX_CONCURRENT_JOBS=5
    depends_on:
      - db
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/atlas-intelligence/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  atlas-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - atlas-backend

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=atlas_user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=atlas_pipeline
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

Deploy:
```bash
docker-compose -f docker-compose.atlas-intelligence.yml up -d
```

### Option 2: Kubernetes

```yaml
# k8s/atlas-intelligence-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: atlas-intelligence
  labels:
    app: atlas-intelligence
spec:
  replicas: 3
  selector:
    matchLabels:
      app: atlas-intelligence
  template:
    metadata:
      labels:
        app: atlas-intelligence
    spec:
      containers:
      - name: backend
        image: atlas-pipeline/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: atlas-secrets
              key: database-url
        - name: ATLAS_INTELLIGENCE_MAX_CONCURRENT_JOBS
          value: "10"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /atlas-intelligence/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /atlas-intelligence/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: atlas-intelligence
spec:
  selector:
    app: atlas-intelligence
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: atlas-intelligence
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: atlas.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: atlas-intelligence
            port:
              number: 80
```

### Option 3: Standalone

```bash
# Backend
cd backend
source venv/bin/activate
uvicorn simple_main:app --host 0.0.0.0 --port 8000 --workers 4

# Frontend (separate terminal)
cd frontend
npm run build
npx serve -s dist -l 3000
```

---

## API Endpoints Reference

### Health & Status

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/atlas-intelligence/health` | GET | Platform health check |
| `/atlas-intelligence/stats` | GET | Overall statistics |
| `/atlas-intelligence/pyairbyte/health` | GET | PyAirbyte status |

### Connectors

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/atlas-intelligence/connectors` | GET | List MCP connectors |
| `/atlas-intelligence/pyairbyte/connectors` | GET | List PyAirbyte sources |
| `/atlas-intelligence/pyairbyte/categories` | GET | List categories |
| `/atlas-intelligence/pyairbyte/spec/{id}` | GET | Get connector spec |
| `/atlas-intelligence/pyairbyte/configure` | POST | Configure source |
| `/atlas-intelligence/pyairbyte/discover/{id}` | GET | Discover streams |
| `/atlas-intelligence/pyairbyte/read/{id}/{stream}` | GET | Read stream data |

### Credentials

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/atlas-intelligence/credentials` | GET | Get credential status |
| `/atlas-intelligence/credentials` | POST | Set credential |

### State Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/atlas-intelligence/state/sources` | GET | List source states |
| `/atlas-intelligence/state/sources` | POST | Create source state |
| `/atlas-intelligence/state/sources/{id}` | GET | Get source state |
| `/atlas-intelligence/state/sources/{id}/streams` | PUT | Update stream state |
| `/atlas-intelligence/state/sources/{id}/reset` | POST | Reset state |
| `/atlas-intelligence/state/export` | GET | Export all state |
| `/atlas-intelligence/state/import` | POST | Import state |

### Sync Jobs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/atlas-intelligence/sync/stats` | GET | Scheduler statistics |
| `/atlas-intelligence/sync/jobs` | GET | List jobs |
| `/atlas-intelligence/sync/jobs` | POST | Create job |
| `/atlas-intelligence/sync/jobs/{id}` | GET | Get job |
| `/atlas-intelligence/sync/jobs/{id}/run` | POST | Run job |
| `/atlas-intelligence/sync/jobs/{id}/cancel` | POST | Cancel job |
| `/atlas-intelligence/sync/running` | GET | List running jobs |

### Schedules

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/atlas-intelligence/sync/schedules` | GET | List schedules |
| `/atlas-intelligence/sync/schedules` | POST | Create schedule |
| `/atlas-intelligence/sync/schedules/{id}` | GET | Get schedule |
| `/atlas-intelligence/sync/schedules/{id}` | PUT | Update schedule |
| `/atlas-intelligence/sync/schedules/{id}` | DELETE | Delete schedule |
| `/atlas-intelligence/sync/schedules/{id}/run` | POST | Trigger schedule |

---

## Operations

### Monitoring

**Health Check:**
```bash
curl http://localhost:8000/atlas-intelligence/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "components": {
    "pyairbyte": "available",
    "state_manager": "healthy",
    "scheduler": "healthy"
  },
  "timestamp": "2026-01-12T12:00:00Z"
}
```

**Prometheus Metrics:**
AtlasIntelligence exposes metrics at `/metrics`:
- `atlas_sync_jobs_total` - Total sync jobs by status
- `atlas_sync_duration_seconds` - Sync duration histogram
- `atlas_records_synced_total` - Total records synced
- `atlas_connector_errors_total` - Connector errors by type

### Backup & Recovery

**Export State:**
```bash
curl http://localhost:8000/atlas-intelligence/state/export > state_backup.json
```

**Import State:**
```bash
curl -X POST http://localhost:8000/atlas-intelligence/state/import \
  -H "Content-Type: application/json" \
  -d @state_backup.json
```

**Recommended Backup Schedule:**
- Daily: Export state to S3/GCS
- Weekly: Full database backup
- Before major updates: Manual state export

### Scaling

**Horizontal Scaling:**
- Add more backend replicas (stateless)
- Use shared PostgreSQL for state
- Use Redis for job queue distribution

**Vertical Scaling:**
- Increase `ATLAS_INTELLIGENCE_MAX_CONCURRENT_JOBS` for more parallel syncs
- Increase worker memory for large datasets

**Recommended Limits:**
| Deployment Size | Concurrent Jobs | Workers |
|----------------|-----------------|---------|
| Small (<10 sources) | 3 | 2 |
| Medium (10-50 sources) | 5 | 4 |
| Large (50+ sources) | 10+ | 8+ |

---

## Troubleshooting

### Common Issues

**1. Connector Not Available**
```
Error: Connector source-xxx not found in catalog
```
Solution: Verify connector ID matches catalog. Use `/atlas-intelligence/pyairbyte/connectors` to list available.

**2. State Persistence Failure**
```
Error: Failed to save state
```
Solution: Check DATABASE_URL connection. Verify PostgreSQL is running.

**3. Sync Job Timeout**
```
Error: Job exceeded maximum duration
```
Solution: Increase timeout in scheduler config or reduce batch size.

**4. API Key Not Set**
```
Error: Authentication failed for connector
```
Solution: Set API key via UI or environment variable.

### Debug Mode

Enable debug logging:
```bash
export ATLAS_LOG_LEVEL=DEBUG
export PYAIRBYTE_LOG_LEVEL=DEBUG
```

### Support

- **GitHub Issues**: https://github.com/Arnarsson/atlas-pipeline-v1/issues
- **Documentation**: See CLAUDE.md for complete platform documentation

---

## Security Considerations

### API Key Storage
- Never commit API keys to version control
- Use environment variables or secrets manager
- Rotate keys regularly

### Network Security
- Use HTTPS in production
- Restrict API access with authentication
- Use network policies in Kubernetes

### Data Security
- Encrypt state at rest (PostgreSQL encryption)
- Use secure connections to data sources
- Audit access to sensitive connectors

---

## Changelog

### v1.0.0 (January 12, 2026)
- Initial release
- 13 MCP connectors
- 70+ PyAirbyte sources
- State management for incremental syncs
- Sync job scheduler with cron support
- Full UI for connector management
