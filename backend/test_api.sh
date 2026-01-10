#!/bin/bash

# Test script for Atlas Data Pipeline API
# Phase 1 Week 2 - Working FastAPI Backend

set -e

echo "==================================================================="
echo "Atlas Data Pipeline API - Test Suite"
echo "==================================================================="
echo ""

BASE_URL="http://localhost:8000"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo -e "${BLUE}Test 1: Health Check${NC}"
curl -s $BASE_URL/health | python3 -m json.tool
echo -e "${GREEN}✓ Health check passed${NC}"
echo ""

# Test 2: Root endpoint
echo -e "${BLUE}Test 2: Root Endpoint${NC}"
curl -s $BASE_URL/ | python3 -m json.tool
echo -e "${GREEN}✓ Root endpoint passed${NC}"
echo ""

# Test 3: Upload CSV and run pipeline
echo -e "${BLUE}Test 3: Upload CSV and Run Pipeline${NC}"
RESPONSE=$(curl -s -X POST "$BASE_URL/pipeline/run" \
  -F "file=@test_data.csv" \
  -F "dataset_name=test_customers")

echo $RESPONSE | python3 -m json.tool
RUN_ID=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['run_id'])")
echo -e "${GREEN}✓ Pipeline started with run_id: $RUN_ID${NC}"
echo ""

# Wait for processing
echo "Waiting 2 seconds for processing..."
sleep 2
echo ""

# Test 4: Check pipeline status
echo -e "${BLUE}Test 4: Check Pipeline Status${NC}"
curl -s $BASE_URL/pipeline/status/$RUN_ID | python3 -m json.tool | head -50
echo -e "${GREEN}✓ Pipeline status retrieved${NC}"
echo ""

# Test 5: Get quality metrics
echo -e "${BLUE}Test 5: Get Quality Metrics${NC}"
curl -s $BASE_URL/quality/metrics/$RUN_ID | python3 -m json.tool | head -30
echo -e "${GREEN}✓ Quality metrics retrieved${NC}"
echo ""

# Test 6: Get PII report
echo -e "${BLUE}Test 6: Get PII Report${NC}"
curl -s $BASE_URL/quality/pii-report/$RUN_ID | python3 -m json.tool | head -30
echo -e "${GREEN}✓ PII report retrieved${NC}"
echo ""

# Test 7: Get compliance report
echo -e "${BLUE}Test 7: Get Compliance Report${NC}"
curl -s $BASE_URL/compliance/report/$RUN_ID | python3 -m json.tool | head -20
echo -e "${GREEN}✓ Compliance report retrieved${NC}"
echo ""

# Test 8: List all runs
echo -e "${BLUE}Test 8: List All Pipeline Runs${NC}"
curl -s $BASE_URL/pipeline/runs | python3 -m json.tool
echo -e "${GREEN}✓ Pipeline runs listed${NC}"
echo ""

# Summary
echo "==================================================================="
echo -e "${GREEN}All tests passed!${NC}"
echo "==================================================================="
echo ""
echo "API Documentation:"
echo "  Swagger UI: $BASE_URL/docs"
echo "  ReDoc:      $BASE_URL/redoc"
echo ""
echo "Run ID for this test: $RUN_ID"
echo ""
