#!/bin/bash
# Week 4 Testing Script
# Tests connector functionality without requiring external services

set -e

echo "========================================="
echo "Week 4 Connector System Test"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4

    echo -n "Testing: $name... "

    if [ "$method" = "POST" ] || [ "$method" = "PUT" ]; then
        response=$(curl -s -X $method "http://localhost:8000$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" \
            -w "\n%{http_code}")
    else
        response=$(curl -s -X $method "http://localhost:8000$endpoint" \
            -w "\n%{http_code}")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $http_code)"
        echo "Response: $body"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Check if API is running
echo "Checking if API is running..."
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${RED}ERROR: API is not running on port 8000${NC}"
    echo "Please start the API first: python3 simple_main.py"
    exit 1
fi
echo -e "${GREEN}✓ API is running${NC}"
echo ""

# 1. Test connector types listing
echo "========================================="
echo "1. Testing Connector Registry"
echo "========================================="
test_endpoint "List connector types" "GET" "/connectors/types"
echo ""

# 2. Test creating a connector
echo "========================================="
echo "2. Testing Connector Creation"
echo "========================================="

connector_json='{
  "source_type": "postgresql",
  "source_name": "test_db_'$(date +%s)'",
  "config": {
    "source_type": "postgresql",
    "source_name": "test_db",
    "host": "localhost",
    "port": 5432,
    "database": "atlas_pipeline",
    "username": "atlas_user",
    "password": "atlas_password"
  },
  "schedule_cron": "0 * * * *",
  "enabled": false,
  "incremental": true,
  "timestamp_column": "updated_at",
  "table": "test_table",
  "description": "Test connector"
}'

if test_endpoint "Create PostgreSQL connector" "POST" "/connectors/" "$connector_json"; then
    # Extract connector_id from response
    connector_id=$(curl -s -X POST "http://localhost:8000/connectors/" \
        -H "Content-Type: application/json" \
        -d "$connector_json" | python3 -c "import sys, json; print(json.load(sys.stdin)['connector_id'])")

    echo "Created connector: $connector_id"
else
    echo -e "${YELLOW}Warning: Could not extract connector_id${NC}"
    connector_id=""
fi
echo ""

# 3. Test listing connectors
echo "========================================="
echo "3. Testing Connector Listing"
echo "========================================="
test_endpoint "List all connectors" "GET" "/connectors/"
echo ""

# 4. Test connector details (if we have an ID)
if [ -n "$connector_id" ]; then
    echo "========================================="
    echo "4. Testing Connector Details"
    echo "========================================="
    test_endpoint "Get connector details" "GET" "/connectors/$connector_id"
    echo ""

    # 5. Test connector update
    echo "========================================="
    echo "5. Testing Connector Update"
    echo "========================================="
    update_json='{
      "description": "Updated test connector",
      "enabled": true
    }'
    test_endpoint "Update connector" "PUT" "/connectors/$connector_id" "$update_json"
    echo ""

    # 6. Test connector history
    echo "========================================="
    echo "6. Testing Connector History"
    echo "========================================="
    test_endpoint "Get connector history" "GET" "/connectors/$connector_id/history"
    echo ""

    # 7. Test connector deletion
    echo "========================================="
    echo "7. Testing Connector Deletion"
    echo "========================================="
    test_endpoint "Delete connector" "DELETE" "/connectors/$connector_id"
    echo ""
fi

# 8. Test creating different connector types
echo "========================================="
echo "8. Testing Different Connector Types"
echo "========================================="

# MySQL connector
mysql_json='{
  "source_type": "mysql",
  "source_name": "test_mysql_'$(date +%s)'",
  "config": {
    "source_type": "mysql",
    "source_name": "test_mysql",
    "host": "localhost",
    "port": 3306,
    "database": "testdb",
    "username": "user",
    "password": "password"
  },
  "enabled": false
}'
test_endpoint "Create MySQL connector" "POST" "/connectors/" "$mysql_json"

# REST API connector
api_json='{
  "source_type": "rest_api",
  "source_name": "test_api_'$(date +%s)'",
  "config": {
    "source_type": "rest_api",
    "source_name": "test_api",
    "base_url": "https://api.example.com",
    "auth_type": "bearer",
    "auth_token": "test_token",
    "additional_params": {
      "pagination_type": "offset"
    }
  },
  "enabled": false
}'
test_endpoint "Create REST API connector" "POST" "/connectors/" "$api_json"
echo ""

# Summary
echo "========================================="
echo "Test Summary"
echo "========================================="
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
else
    echo -e "${GREEN}Failed: 0${NC}"
fi
echo "Total: $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}========================================="
    echo "✓ All tests passed!"
    echo "=========================================${NC}"
    exit 0
else
    echo -e "${RED}========================================="
    echo "✗ Some tests failed"
    echo "=========================================${NC}"
    exit 1
fi
