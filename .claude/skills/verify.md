# Verify Skill

Verify that all Atlas Pipeline services are running correctly.

## When to Use
- After making changes to verify nothing is broken
- Before committing code
- To diagnose issues

## Instructions

### 1. Check Backend Health

Verify the backend is running and AtlasIntelligence endpoints work:

```bash
# Test all critical endpoints
curl -s http://localhost:8000/atlas-intelligence/health
curl -s http://localhost:8000/atlas-intelligence/connectors
curl -s http://localhost:8000/atlas-intelligence/pyairbyte/connectors
curl -s http://localhost:8000/atlas-intelligence/sync/stats
```

Expected: All return HTTP 200 with valid JSON.

### 2. Check Frontend Build

Verify TypeScript compiles without errors:

```bash
cd /home/user/atlas-pipeline-v1/frontend
npm run build
```

Expected: Build succeeds with no TypeScript errors.

### 3. Check Frontend Dev Server

```bash
curl -s http://localhost:5173
```

Expected: Returns HTML with "Atlas Data Pipeline Platform" title.

### 4. Run Complete Verification Script

```bash
echo "=== AtlasIntelligence Verification ==="
PASS=0; FAIL=0

for endpoint in health connectors pyairbyte/connectors pyairbyte/categories sync/stats sync/jobs state/sources; do
    RESULT=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/atlas-intelligence/$endpoint")
    if [ "$RESULT" = "200" ]; then
        echo "OK: $endpoint"
        PASS=$((PASS + 1))
    else
        echo "FAIL: $endpoint (HTTP $RESULT)"
        FAIL=$((FAIL + 1))
    fi
done

echo "Results: $PASS passed, $FAIL failed"
```

## Common Issues

### Backend Not Running
Start with: `cd backend && python simple_main.py`

### Frontend Not Running
Start with: `cd frontend && npm run dev`

### TypeScript Errors
Common fixes:
- Unused variables: prefix with underscore `_varName`
- Missing imports: check import statements
- JSX.Element: use `ReactNode` from react instead
