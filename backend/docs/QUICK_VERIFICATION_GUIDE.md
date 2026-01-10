# Quick Verification Guide
## Atlas Intelligence Data Pipeline - Week 1 Deployment

**Purpose:** Quickly verify that all Week 1 components are working correctly

**Time Required:** 2-3 minutes

---

## Quick Start

```bash
# Navigate to project directory
cd /Users/sven/Desktop/MCP/.worktrees/atlas-api

# Start services
docker-compose up -d db redis

# Wait 10 seconds for services to initialize
sleep 10

# Run verification tests
python3 tests/integration/test_week1_deployment.py
```

**Expected Result:** All 15 tests should pass (100%)

---

## Detailed Verification Steps

### Step 1: Verify Docker Services (30 seconds)

```bash
# Check running containers
docker-compose ps

# Should show:
# - atlas-db (running, port 5432)
# - atlas-redis (running, port 6379)
```

### Step 2: Check Database Connection (15 seconds)

```bash
# Test PostgreSQL connection
docker exec atlas-db pg_isready -U atlas_user

# Expected: "/var/run/postgresql:5432 - accepting connections"
```

### Step 3: Verify Schemas Exist (30 seconds)

```bash
# Connect to database
docker exec -it atlas-db psql -U atlas_user -d atlas_pipeline

# Inside psql, run:
\dn+

# Should show 7 schemas:
# - explore (Raw data zone)
# - chart (Processed data zone)
# - navigate (Business-ready zone)
# - pipeline (Orchestration metadata)
# - quality (Testing framework)
# - compliance (Governance & audit)
# - archive (Long-term storage)

# Exit psql
\q
```

### Step 4: Check Table Count (20 seconds)

```bash
# Count tables per schema
docker exec atlas-db psql -U atlas_user -d atlas_pipeline -c "
SELECT schemaname, COUNT(*) as table_count
FROM pg_tables
WHERE schemaname IN ('explore', 'chart', 'navigate', 'pipeline', 'quality', 'compliance', 'archive')
GROUP BY schemaname
ORDER BY schemaname;
"

# Expected counts:
# explore: ~8 tables (including partitions)
# chart: ~1 table
# navigate: ~8 tables (including partitions)
# pipeline: 11 tables
# quality: ~13 tables (including partitions)
# compliance: ~20 tables (including partitions)
# archive: 1 table
```

### Step 5: Verify Schema Renaming (15 seconds)

```bash
# Check that old schema names don't exist
docker exec atlas-db psql -U atlas_user -d atlas_pipeline -c "
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name IN ('bronze', 'silver', 'gold');
"

# Expected: (0 rows) - old names should not exist

# Check that new schema names exist
docker exec atlas-db psql -U atlas_user -d atlas_pipeline -c "
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name IN ('explore', 'chart', 'navigate')
ORDER BY schema_name;
"

# Expected: explore, chart, navigate
```

### Step 6: Test Redis Connection (15 seconds)

```bash
# Test Redis with password
docker exec atlas-redis redis-cli -a changethis ping

# Expected: PONG

# Test set/get operation
docker exec atlas-redis redis-cli -a changethis SET verification "test" EX 60
docker exec atlas-redis redis-cli -a changethis GET verification

# Expected: "test"
```

### Step 7: Check Partitions (30 seconds)

```bash
# Verify raw_data partitions (explore schema)
docker exec atlas-db psql -U atlas_user -d atlas_pipeline -c "
SELECT tablename
FROM pg_tables
WHERE schemaname = 'explore' AND tablename LIKE 'raw_data_%'
ORDER BY tablename;
"

# Expected: 6 partitions (raw_data_2025_10 through raw_data_2026_02)

# Verify fact partitions (navigate schema)
docker exec atlas-db psql -U atlas_user -d atlas_pipeline -c "
SELECT tablename
FROM pg_tables
WHERE schemaname = 'navigate' AND tablename LIKE 'fact_%'
ORDER BY tablename;
"

# Expected: 5 partitions (fact_2024 through fact_2027)

# Verify audit log partitions (compliance schema)
docker exec atlas-db psql -U atlas_user -d atlas_pipeline -c "
SELECT tablename
FROM pg_tables
WHERE schemaname = 'compliance' AND tablename LIKE 'audit_log_%'
ORDER BY tablename;
"

# Expected: 9 partitions (quarterly partitions)
```

### Step 8: Verify Seed Data (30 seconds)

```bash
# Check quality dimensions
docker exec atlas-db psql -U atlas_user -d atlas_pipeline -c "
SELECT COUNT(*) as dimension_count FROM quality.dimensions;
"
# Expected: 6

# Check compliance classification levels
docker exec atlas-db psql -U atlas_user -d atlas_pipeline -c "
SELECT COUNT(*) as classification_count FROM compliance.classification_levels;
"
# Expected: 5

# Check PII patterns
docker exec atlas-db psql -U atlas_user -d atlas_pipeline -c "
SELECT COUNT(*) as pii_pattern_count FROM compliance.pii_patterns;
"
# Expected: 5
```

### Step 9: Run Full Integration Tests (30 seconds)

```bash
# Run comprehensive test suite
python3 tests/integration/test_week1_deployment.py

# Expected output:
# ================================================================================
# Phase 1 Week 1 Day 5 - Integration Tests
# ================================================================================
# ✅ PASS - Database Connection
# ✅ PASS - Redis Connection
# ✅ PASS - Schema Verification
# ✅ PASS - Table Verification (7 schemas)
# ✅ PASS - Schema Rename Verification
# ✅ PASS - Partition Verification
# ✅ PASS - Seed Data Verification
# ✅ PASS - Redis Operations
# ✅ PASS - API Health Endpoint (Skipped)
# ================================================================================
# Total Tests: 15
# Passed: 15 ✅
# Failed: 0 ❌
# Pass Rate: 100.0%
# ================================================================================
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check for port conflicts
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# If ports are in use, stop other services or change ports in .env

# Check Docker status
docker-compose ps
docker-compose logs db
docker-compose logs redis
```

### Database Connection Failed

```bash
# Restart database
docker-compose restart db

# Wait for startup
sleep 10

# Check health
docker exec atlas-db pg_isready -U atlas_user
```

### Redis Authentication Failed

```bash
# Verify password in .env
cat .env | grep REDIS_PASSWORD

# Should be: REDIS_PASSWORD=changethis

# Test with correct password
docker exec atlas-redis redis-cli -a changethis ping
```

### Tests Failing

```bash
# Ensure .env file exists
ls -la .env

# If not, create from example
cp .env.example .env

# Check Python dependencies
python3 -c "import psycopg, redis, httpx, loguru; print('All dependencies installed')"

# If missing, install
pip3 install psycopg redis httpx loguru python-dotenv
```

---

## Success Criteria

All of the following should be true:

- ✅ Docker services running (2+: db, redis)
- ✅ PostgreSQL accepting connections
- ✅ Redis responding to ping
- ✅ 7 schemas exist (explore, chart, navigate, pipeline, quality, compliance, archive)
- ✅ 39+ tables created across all schemas
- ✅ 20+ partitions created (raw_data, fact, audit_log)
- ✅ Seed data loaded (6 quality dimensions, 5 classifications, 5 PII patterns)
- ✅ Integration tests passing (15/15 = 100%)
- ✅ No "bronze", "silver", "gold" schemas exist

---

## Quick Commands Reference

```bash
# Start everything
docker-compose up -d

# Stop everything
docker-compose down

# Restart services
docker-compose restart db redis

# View logs
docker-compose logs -f db
docker-compose logs -f redis

# Connect to database
docker exec -it atlas-db psql -U atlas_user -d atlas_pipeline

# Run tests
python3 tests/integration/test_week1_deployment.py

# Check service health
docker exec atlas-db pg_isready -U atlas_user
docker exec atlas-redis redis-cli -a changethis ping

# View all schemas
docker exec atlas-db psql -U atlas_user -d atlas_pipeline -c "\dn+"

# Count all tables
docker exec atlas-db psql -U atlas_user -d atlas_pipeline -c "
SELECT schemaname, COUNT(*) FROM pg_tables
WHERE schemaname IN ('explore','chart','navigate','pipeline','quality','compliance','archive')
GROUP BY schemaname ORDER BY schemaname;"
```

---

## Files to Review

- `docs/WEEK1_COMPLETION_REPORT.md` - Comprehensive completion report
- `docs/WEEK1_TEAM_REVIEW.md` - Team presentation materials
- `database/migrations/*.sql` - Database migration scripts
- `tests/integration/test_week1_deployment.py` - Integration test suite
- `docker-compose.yml` - Service orchestration
- `.env.example` - Configuration template

---

*Verification Guide Version: 1.0*
*Last Updated: 2026-01-09*
*Project: Atlas Intelligence Data Pipeline Platform*
