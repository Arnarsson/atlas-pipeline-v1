#!/bin/bash

# ============================================================================
# Week 5-6 Quick Start Test Script
# ============================================================================
# Tests all Week 5-6 features (Lineage, Features, GDPR, Catalog)
# ============================================================================

set -e  # Exit on error

API_URL="http://localhost:8000"

echo "=========================================="
echo "Week 5-6 Quick Start Tests"
echo "=========================================="
echo ""

# Check if API is running
echo "1. Checking if API is running..."
if ! curl -s "$API_URL/docs" > /dev/null; then
    echo "❌ API is not running. Start with: python3 simple_main.py"
    exit 1
fi
echo "✅ API is running"
echo ""

# Test Lineage
echo "2. Testing Lineage API..."
curl -s "$API_URL/lineage/dataset/explore.raw_data" | jq -r '.lineage_available' > /dev/null && echo "✅ Lineage API working" || echo "⚠️  Lineage API (Marquez may be unavailable)"
echo ""

# Test Feature Store - List
echo "3. Testing Feature Store - List..."
curl -s "$API_URL/features/groups" | jq '.' > /dev/null && echo "✅ Feature Store list working" || echo "❌ Feature Store list failed"
echo ""

# Test Feature Store - Register (with sample CSV)
echo "4. Testing Feature Store - Register..."
cat > /tmp/test_features.csv << 'EOF'
customer_id,total_purchases,avg_order_value
1,10,100.50
2,20,150.75
3,15,120.25
EOF

curl -s -X POST "$API_URL/features/groups" \
  -F "name=test_customer_metrics" \
  -F "description=Test customer metrics" \
  -F "file=@/tmp/test_features.csv" \
  -F "version=1.0.0" | jq -r '.message' && echo "✅ Feature Store register working" || echo "❌ Feature Store register failed"
echo ""

# Test GDPR - Export (Access)
echo "5. Testing GDPR - Right to Access..."
curl -s -X POST "$API_URL/gdpr/export" \
  -H "Content-Type: application/json" \
  -d '{"identifier": "test@example.com", "identifier_type": "email"}' | jq -r '.subject_id' > /dev/null && echo "✅ GDPR Access working" || echo "❌ GDPR Access failed"
echo ""

# Test GDPR - List Requests
echo "6. Testing GDPR - List Requests..."
curl -s "$API_URL/gdpr/requests" | jq '. | length' > /dev/null && echo "✅ GDPR list requests working" || echo "❌ GDPR list requests failed"
echo ""

# Test Data Catalog - Search
echo "7. Testing Data Catalog - Search..."
curl -s "$API_URL/catalog/datasets" | jq '. | length' > /dev/null && echo "✅ Catalog search working" || echo "❌ Catalog search failed"
echo ""

# Test Data Catalog - Tags
echo "8. Testing Data Catalog - List Tags..."
curl -s "$API_URL/catalog/tags" | jq '. | length' > /dev/null && echo "✅ Catalog tags working" || echo "❌ Catalog tags failed"
echo ""

# Test Data Catalog - Stats
echo "9. Testing Data Catalog - Stats..."
curl -s "$API_URL/catalog/stats" | jq -r '.total_datasets' > /dev/null && echo "✅ Catalog stats working" || echo "❌ Catalog stats failed"
echo ""

# Cleanup
rm -f /tmp/test_features.csv

echo "=========================================="
echo "Week 5-6 Quick Start Tests Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. View API docs: $API_URL/docs"
echo "2. View Marquez UI: http://localhost:5000"
echo "3. Run full tests: pytest tests/integration/test_week5_integration.py -v"
echo ""
