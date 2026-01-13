# Atlas Data Pipeline - Deployment Guide

Production deployment for the Atlas Data Pipeline with real persistence, authentication, and AI capabilities.

## Quick Start (Development)

```bash
# 1. Start databases
docker-compose up -d postgres redis

# 2. Start backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-simple.txt
python simple_main.py

# 3. Start frontend (new terminal)
cd frontend
npm install
npm run dev

# 4. Verify
python scripts/test_e2e_pipeline.py --quick
```

**URLs:**
- Backend API: http://localhost:8000
- Frontend Dashboard: http://localhost:5173
- API Docs: http://localhost:8000/docs

---

## Production Deployment

### Option 1: Docker Compose (Recommended)

```bash
# Deploy full stack
docker-compose up -d

# Scale backend
docker-compose up -d --scale backend=3
```

**Services:**
| Service | Port | Purpose |
|---------|------|---------|
| postgres | 5432 | PostgreSQL with pgvector |
| redis | 6379 | Caching & rate limiting |
| backend | 8000 | FastAPI application |
| frontend | 80 | React dashboard |
| prometheus | 9090 | Metrics collection |
| grafana | 3000 | Monitoring dashboards |

### Option 2: Kubernetes

```yaml
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Or use Helm
helm install atlas ./charts/atlas-pipeline
```

---

## Environment Variables

Create `.env` file in project root:

```env
# Database
POSTGRES_USER=atlas_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=atlas_pipeline
DATABASE_URL=postgresql://atlas_user:password@localhost:5432/atlas_pipeline

# Redis
REDIS_URL=redis://localhost:6379/0

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=production

# Authentication
ADMIN_API_KEY=your_admin_key_here
JWT_SECRET=your_jwt_secret_here

# AI/Embeddings (optional)
OPENAI_API_KEY=sk-...  # For OpenAI embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Local model
```

---

## Client Authentication

### Create API Key (Admin)

```bash
curl -X POST http://localhost:8000/auth/keys \
  -H "X-Admin-Key: atlas_admin_key_change_me" \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "production_client",
    "scopes": ["read", "write"],
    "expires_in_days": 365,
    "rate_limit": 5000
  }'
```

Response:
```json
{
  "client_id": "uuid",
  "api_key": "atlas_xxxxx...",  // Store securely!
  "message": "Store this API key securely - it cannot be retrieved again!"
}
```

### Using API Key

```bash
# All authenticated requests
curl http://localhost:8000/ai/datasets \
  -H "X-API-Key: atlas_xxxxx..."
```

---

## Data Pipeline Usage

### 1. Upload Data (Persistent)

```bash
curl -X POST http://localhost:8000/pipeline/run/persistent \
  -H "X-API-Key: atlas_xxxxx..." \
  -F "file=@data.csv" \
  -F "dataset_name=customers" \
  -F "embed_for_rag=true"
```

### 2. Query Data (AI Agent)

```bash
curl -X POST http://localhost:8000/ai/query \
  -H "X-API-Key: atlas_xxxxx..." \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_name": "customers",
    "query_type": "select",
    "filters": {"revenue": {"$gt": 50000}},
    "limit": 100
  }'
```

### 3. Semantic Search

```bash
curl -X POST http://localhost:8000/ai/search \
  -H "X-API-Key: atlas_xxxxx..." \
  -H "Content-Type: application/json" \
  -d '{
    "query": "high value enterprise customers",
    "limit": 10
  }'
```

### 4. View Audit Logs

```bash
curl http://localhost:8000/ai/audit?limit=50 \
  -H "X-API-Key: atlas_xxxxx..."
```

---

## Database Schemas

The pipeline uses three data layers:

| Schema | Purpose | Retention |
|--------|---------|-----------|
| `explore.*` | Raw data (bronze) | 90 days |
| `chart.*` | Validated + PII tagged (silver) | 1 year |
| `navigate.*` | Business-ready, SCD Type 2 (gold) | 5+ years |
| `audit.*` | Access logs (EU AI Act Art. 12) | 5+ years |
| `vectors.*` | Embeddings for RAG | As needed |

### Initialize Schema

```sql
-- Auto-created on startup, or run manually:
psql -U atlas_user -d atlas_pipeline -f backend/database/schema.sql
```

---

## Monitoring

### Prometheus Metrics

Available at `http://localhost:8000/metrics`:

- `atlas_http_requests_total` - Request count by endpoint
- `atlas_pipeline_runs_total` - Pipeline executions
- `atlas_pii_detections_total` - PII findings by type
- `atlas_quality_score` - Quality scores by dimension
- `atlas_rate_limit_exceeded_total` - Rate limit hits

### Grafana Dashboards

Access at `http://localhost:3000` (admin/admin):

1. **Atlas Overview** - Request rates, latency, errors
2. **Pipeline Performance** - Run times, success rates
3. **Data Quality** - Score trends, PII detection

---

## Backup & Recovery

### Automated Backups

```bash
# Daily backup script
./scripts/backup.sh

# Backups stored in ./backups/
# - daily/ (30-day retention)
# - weekly/ (90-day retention)
# - monthly/ (365-day retention)
```

### Manual Backup

```bash
pg_dump -U atlas_user atlas_pipeline > backup_$(date +%Y%m%d).sql
```

### Restore

```bash
./scripts/restore.sh backup_20260113.sql
```

---

## Security Checklist

- [ ] Change default `ADMIN_API_KEY` in production
- [ ] Use strong `POSTGRES_PASSWORD`
- [ ] Enable TLS for all services
- [ ] Set up firewall rules (only expose 80/443)
- [ ] Configure rate limiting appropriately
- [ ] Enable audit logging
- [ ] Regular security scans with `bandit` and `safety`

---

## Troubleshooting

### Backend won't start

```bash
# Check dependencies
pip install -r requirements-simple.txt

# Check port availability
lsof -i :8000

# Check database connection
psql -U atlas_user -h localhost -d atlas_pipeline -c "SELECT 1"
```

### Database connection failed

```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Test connection
pg_isready -h localhost -U atlas_user
```

### Rate limit exceeded

```bash
# Check current usage
curl http://localhost:8000/auth/usage \
  -H "X-API-Key: atlas_xxxxx..."

# Request limit increase via admin
```

---

## Support

- GitHub Issues: https://github.com/Arnarsson/atlas-pipeline-v1/issues
- Documentation: See `CLAUDE.md` for complete feature reference
