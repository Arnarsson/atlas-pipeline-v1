#!/bin/bash
# Atlas Pipeline Pre-PR Testing Script
# Run this before creating a PR to ensure all systems are working

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
PASSED=0
FAILED=0

echo "=========================================="
echo "  Atlas Pipeline Pre-PR Test Suite"
echo "=========================================="
echo ""

# Function to test an endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local expected_status="${4:-200}"
    local data="$5"

    if [ "$method" = "GET" ]; then
        status=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL$endpoint")
    else
        status=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$BACKEND_URL$endpoint" -H "Content-Type: application/json" -d "$data")
    fi

    if [ "$status" = "$expected_status" ]; then
        echo -e "  ${GREEN}✓${NC} $name ($status)"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}✗${NC} $name (got $status, expected $expected_status)"
        FAILED=$((FAILED + 1))
    fi
}

# Test server is running
echo "1. Backend Server Health"
echo "-------------------------"
if curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Server is running"
    PASSED=$((PASSED + 1))
else
    echo -e "  ${RED}✗${NC} Server is not running"
    echo "Please start the backend server first:"
    echo "  cd backend && python3 simple_main.py"
    exit 1
fi

# Test core endpoints
echo ""
echo "2. Core API Endpoints"
echo "---------------------"
test_endpoint "Root endpoint" "GET" "/"
test_endpoint "Health check" "GET" "/health"
test_endpoint "Dashboard stats" "GET" "/dashboard/stats"
test_endpoint "Connector types" "GET" "/connectors/types"
test_endpoint "Metrics" "GET" "/metrics"

# Test Pipeline endpoints
echo ""
echo "3. Pipeline Endpoints"
echo "--------------------"
test_endpoint "Pipeline runs list" "GET" "/pipeline/runs"

# Test Quality endpoints
echo ""
echo "4. Quality Endpoints"
echo "-------------------"
# These return 404 for non-existent runs which is correct
test_endpoint "Quality metrics (404 expected)" "GET" "/quality/metrics/test-run" "404"
test_endpoint "Quality dimensions (404 expected)" "GET" "/quality/dimensions/test-run" "404"

# Test GDPR endpoints
echo ""
echo "5. GDPR Endpoints"
echo "-----------------"
test_endpoint "GDPR requests list" "GET" "/gdpr/requests"
test_endpoint "GDPR export" "POST" "/gdpr/export?identifier=test@test.com&identifier_type=email"
test_endpoint "GDPR delete" "POST" "/gdpr/delete?identifier=test@test.com&identifier_type=email"

# Test Lineage endpoints
echo ""
echo "6. Lineage Endpoints"
echo "-------------------"
test_endpoint "Dataset lineage" "GET" "/lineage/dataset/test_dataset"

# Test Feature Store endpoints
echo ""
echo "7. Feature Store Endpoints"
echo "-------------------------"
test_endpoint "Feature groups" "GET" "/features/groups"

# Test Phase 0: EU AI Act Compliance endpoints
echo ""
echo "8. EU AI Act Compliance Endpoints (Phase 0)"
echo "-------------------------------------------"
test_endpoint "Risk levels" "GET" "/compliance/eu-ai-act/risk-levels"
test_endpoint "Areas" "GET" "/compliance/eu-ai-act/areas"
test_endpoint "Articles" "GET" "/compliance/eu-ai-act/articles"
test_endpoint "Quick check" "GET" "/compliance/eu-ai-act/quick-check?area=employment"

# Test Phase 0: Governance RBAC endpoints
echo ""
echo "9. Governance RBAC Endpoints (Phase 0)"
echo "--------------------------------------"
test_endpoint "Roles list" "GET" "/governance/roles"
test_endpoint "Permissions list" "GET" "/governance/permissions"
test_endpoint "Audit logs" "GET" "/governance/audit"
test_endpoint "Compliance status" "GET" "/governance/compliance/status"

# Test AtlasIntelligence endpoints
echo ""
echo "10. AtlasIntelligence Endpoints"
echo "-------------------------------"
test_endpoint "Platform health" "GET" "/atlas-intelligence/health"
test_endpoint "PyAirbyte connectors" "GET" "/atlas-intelligence/pyairbyte/connectors"
test_endpoint "PyAirbyte categories" "GET" "/atlas-intelligence/pyairbyte/categories"
test_endpoint "MCP connectors" "GET" "/atlas-intelligence/connectors"

# Test E2E CSV Upload
echo ""
echo "11. E2E CSV Upload Test"
echo "----------------------"
CSV_FILE="/home/user/atlas-pipeline-v1/demo_customer_data.csv"
if [ -f "$CSV_FILE" ]; then
    UPLOAD_RESULT=$(curl -s -X POST "$BACKEND_URL/pipeline/run" \
        -F "file=@$CSV_FILE" \
        -F "dataset_name=pre_pr_test")

    RUN_ID=$(echo "$UPLOAD_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('run_id', ''))" 2>/dev/null)

    if [ -n "$RUN_ID" ]; then
        echo -e "  ${GREEN}✓${NC} CSV upload successful (run_id: $RUN_ID)"
        PASSED=$((PASSED + 1))

        # Wait for processing
        sleep 2

        # Check status
        STATUS=$(curl -s "$BACKEND_URL/pipeline/status/$RUN_ID" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)
        if [ "$STATUS" = "completed" ]; then
            echo -e "  ${GREEN}✓${NC} Pipeline completed successfully"
            PASSED=$((PASSED + 1))
        else
            echo -e "  ${YELLOW}⚠${NC} Pipeline status: $STATUS"
        fi

        # Check quality metrics
        QUALITY=$(curl -s "$BACKEND_URL/quality/metrics/$RUN_ID" | python3 -c "import sys, json; d = json.load(sys.stdin); print(d.get('overall_score', 0))" 2>/dev/null)
        if [ -n "$QUALITY" ]; then
            echo -e "  ${GREEN}✓${NC} Quality score: $QUALITY"
            PASSED=$((PASSED + 1))
        fi

        # Check PII detection
        PII=$(curl -s "$BACKEND_URL/quality/pii-report/$RUN_ID" | python3 -c "import sys, json; d = json.load(sys.stdin); print(d.get('pii_count', 0))" 2>/dev/null)
        if [ -n "$PII" ]; then
            echo -e "  ${GREEN}✓${NC} PII detections: $PII"
            PASSED=$((PASSED + 1))
        fi
    else
        echo -e "  ${RED}✗${NC} CSV upload failed"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "  ${YELLOW}⚠${NC} Demo CSV file not found, skipping E2E test"
fi

# Summary
echo ""
echo "=========================================="
echo "  Test Summary"
echo "=========================================="
echo -e "  ${GREEN}Passed:${NC} $PASSED"
echo -e "  ${RED}Failed:${NC} $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! Ready for PR.${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please fix before creating PR.${NC}"
    exit 1
fi
