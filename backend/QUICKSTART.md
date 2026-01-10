# Atlas Data Pipeline Platform - Quick Start Guide

## Prerequisites

- Docker Desktop installed and running
- Git (for version control)
- 8GB+ RAM available
- Ports 5432, 6379, 8000, 8081 available

## Setup (5 minutes)

### 1. Start Infrastructure Services

```bash
# Start PostgreSQL and Redis
docker-compose up -d db redis

# Wait for health checks (about 30 seconds)
docker-compose ps

# Expected output:
# atlas-db      healthy
# atlas-redis   healthy
```

### 2. Verify Database Setup

```bash
# Run verification script
./scripts/verify-setup.sh

# Should show all green checkmarks ✓
```

### 3. Run Database Migrations

```bash
# Apply all migrations
docker-compose run --rm backend alembic upgrade head

# Verify migration status
docker-compose run --rm backend alembic current
```

### 4. Start Application Services

```bash
# Start backend API
docker-compose up -d backend

# Start Celery worker
docker-compose up -d celery-worker

# Start Celery beat (scheduler)
docker-compose up -d celery-beat

# Optional: Start Flower (Celery monitoring)
docker-compose up -d flower
```

### 5. Verify Everything Works

```bash
# Check all services
docker-compose ps

# Test API health endpoint
curl http://localhost:8000/api/v1/health

# View backend logs
docker-compose logs -f backend
```

## Access Points

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

### Database Management
- **Adminer (Web UI)**: http://localhost:8081
  - System: PostgreSQL
  - Server: db
  - Username: atlas_user
  - Password: changethis
  - Database: atlas_pipeline

### Monitoring
- **Flower (Celery)**: http://localhost:5555
- **Prefect UI**: http://localhost:4200 (if started)
- **MinIO Console**: http://localhost:9001 (if started)

## Common Commands

### Service Management
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a service
docker-compose restart backend

# View logs
docker-compose logs -f backend
docker-compose logs -f celery-worker

# Check service status
docker-compose ps
```

### Database Operations
```bash
# Access PostgreSQL CLI
docker exec -it atlas-db psql -U atlas_user -d atlas_pipeline

# List databases
docker exec atlas-db psql -U atlas_user -c "\l"

# Backup database
docker exec atlas-db pg_dump -U atlas_user atlas_pipeline > backup.sql

# Restore database
docker exec -i atlas-db psql -U atlas_user -d atlas_pipeline < backup.sql
```

### Redis Operations
```bash
# Access Redis CLI
docker exec -it atlas-redis redis-cli -a changethis

# Test connection
docker exec atlas-redis redis-cli -a changethis ping

# Clear all cache
docker exec atlas-redis redis-cli -a changethis FLUSHALL

# Monitor commands
docker exec atlas-redis redis-cli -a changethis monitor
```

### Alembic Migrations
```bash
# Create new migration
docker-compose run --rm backend alembic revision --autogenerate -m "description"

# Upgrade to latest
docker-compose run --rm backend alembic upgrade head

# Downgrade one version
docker-compose run --rm backend alembic downgrade -1

# Show migration history
docker-compose run --rm backend alembic history

# Show current version
docker-compose run --rm backend alembic current
```

## Development Workflow

### 1. Code Changes
- Edit files in `app/` directory
- Changes auto-reload in development mode
- Watch logs: `docker-compose logs -f backend`

### 2. Database Changes
```bash
# 1. Update models in app/models/
# 2. Generate migration
docker-compose run --rm backend alembic revision --autogenerate -m "add_new_field"

# 3. Review migration file in app/alembic/versions/

# 4. Apply migration
docker-compose run --rm backend alembic upgrade head
```

### 3. Testing
```bash
# Run all tests
docker-compose run --rm backend pytest

# Run specific test file
docker-compose run --rm backend pytest tests/test_api.py

# Run with coverage
docker-compose run --rm backend pytest --cov=app

# Run tests in watch mode
docker-compose run --rm backend pytest-watch
```

### 4. Code Quality
```bash
# Format code
docker-compose run --rm backend black app/

# Lint code
docker-compose run --rm backend ruff check app/

# Type check
docker-compose run --rm backend mypy app/

# Run all checks
./scripts/lint.sh
./scripts/format.sh
```

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # Backend

# Change port in docker-compose.yml or kill the process
```

### Database Connection Failed
```bash
# Check if PostgreSQL is running
docker-compose ps db

# Check logs
docker-compose logs db

# Restart PostgreSQL
docker-compose restart db

# Re-run init script
docker exec -i atlas-db psql -U atlas_user -d postgres < scripts/init-db.sql
```

### Redis Connection Failed
```bash
# Check if Redis is running
docker-compose ps redis

# Check logs
docker-compose logs redis

# Test connection
docker exec atlas-redis redis-cli -a changethis ping
```

### Backend Won't Start
```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. Database not ready - wait for health check
# 2. Missing .env file - copy from .env.example
# 3. Port conflict - change port in docker-compose.yml

# Rebuild if dependencies changed
docker-compose build backend
docker-compose up -d backend
```

### Celery Worker Issues
```bash
# Check logs
docker-compose logs celery-worker

# Restart worker
docker-compose restart celery-worker

# Check Redis connection
docker exec atlas-redis redis-cli -a changethis ping
```

## Clean Start

If you need to start fresh:

```bash
# Stop all services
docker-compose down

# Remove all data (⚠️ This deletes everything)
docker-compose down -v

# Start fresh
docker-compose up -d db redis
./scripts/verify-setup.sh
docker-compose run --rm backend alembic upgrade head
docker-compose up -d
```

## Environment Configuration

Key settings in `.env`:

```bash
# Development mode
DEBUG=true
RELOAD=true
TESTING=false

# Database
POSTGRES_SERVER=localhost  # Use 'db' in Docker
POSTGRES_PORT=5432
POSTGRES_DB=atlas_pipeline

# Redis
REDIS_HOST=localhost  # Use 'redis' in Docker
REDIS_PORT=6379

# API
API_RATE_LIMIT=100
API_BURST_LIMIT=200
```

## Next Steps

1. **Read the Documentation**
   - `docs/DAY_3_DOCKER_DATABASE_SETUP.md` - Setup details
   - `docs/IMPLEMENTATION_PLAN.md` - Full roadmap
   - `README.md` - Project overview

2. **Explore the API**
   - Visit http://localhost:8000/docs
   - Try the health endpoint
   - Test authentication

3. **Start Development**
   - Create your first pipeline
   - Add data sources
   - Configure transformations

4. **Monitor Your System**
   - Check Flower for tasks
   - Use Adminer for database
   - Review logs

## Getting Help

- **Logs**: `docker-compose logs -f [service]`
- **Health Checks**: `./scripts/verify-setup.sh`
- **Database Check**: `./scripts/db-health-check.sh`
- **API Docs**: http://localhost:8000/docs

## Production Deployment

⚠️ **This setup is for development only!**

Before deploying to production:
1. Change all default passwords
2. Use proper secrets management
3. Enable SSL/TLS
4. Configure proper logging
5. Set up monitoring and alerting
6. Review security settings
7. Use managed databases
8. Implement backup strategies

See `docs/DEPLOYMENT.md` for production deployment guide.
