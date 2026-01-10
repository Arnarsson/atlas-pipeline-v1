#!/bin/bash
# Quick test script for Week 4 connectors

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   Atlas Week 4 - Quick Connector Test                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

API_URL="http://localhost:8000"

# Check API health
echo "1️⃣  Checking API status..."
if curl -s $API_URL/health > /dev/null 2>&1; then
    echo "   ✅ API is running"
else
    echo "   ❌ API is not running"
    echo "   Start with: cd /Users/sven/Desktop/MCP/.worktrees/atlas-api && python3 simple_main.py"
    exit 1
fi
echo ""

# List available connector types
echo "2️⃣  Available connector types:"
curl -s $API_URL/connectors/types | python3 << 'PYEOF'
import json, sys
try:
    data = json.load(sys.stdin)
    types = data.get('connector_types', [])
    for t in types:
        print(f"   • {t}")
except:
    print("   ⚠️  Could not fetch connector types")
PYEOF
echo ""

# Create a test PostgreSQL connector
echo "3️⃣  Creating test PostgreSQL connector..."
RESPONSE=$(curl -s -X POST $API_URL/connectors/ \
    -H "Content-Type: application/json" \
    -d '{
        "source_type": "postgresql",
        "source_name": "atlas_self_test",
        "config": {
            "source_type": "postgresql",
            "source_name": "atlas_self_test",
            "host": "localhost",
            "port": 5432,
            "database": "atlas_pipeline",
            "username": "atlas_user",
            "password": "atlas_password"
        },
        "schedule_cron": null,
        "enabled": true,
        "incremental": false,
        "table": "explore.source_systems"
    }')

CONNECTOR_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('connector_id', 'ERROR'))" 2>/dev/null)

if [ "$CONNECTOR_ID" = "ERROR" ]; then
    echo "   ⚠️  Connector creation response:"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    CONNECTOR_ID=$(curl -s $API_URL/connectors/ | python3 -c "import sys, json; connectors = json.load(sys.stdin).get('connectors', []); print(connectors[0]['connector_id'] if connectors else 'NONE')" 2>/dev/null)
    if [ "$CONNECTOR_ID" != "NONE" ] && [ "$CONNECTOR_ID" != "ERROR" ]; then
        echo "   ℹ️  Using existing connector: $CONNECTOR_ID"
    fi
fi

if [ "$CONNECTOR_ID" != "ERROR" ] && [ "$CONNECTOR_ID" != "NONE" ]; then
    echo "   ✅ Connector created: $CONNECTOR_ID"
    echo ""

    # Test connection
    echo "4️⃣  Testing connector connection..."
    TEST_RESULT=$(curl -s -X POST $API_URL/connectors/$CONNECTOR_ID/test)
    echo "$TEST_RESULT" | python3 << 'PYEOF'
import json, sys
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        print(f"   ✅ Connection successful")
        if 'message' in data:
            print(f"   {data['message']}")
    else:
        print(f"   ❌ Connection failed")
        if 'error' in data:
            print(f"   {data['error']}")
except:
    print("   ⚠️  Could not parse test result")
PYEOF
else
    echo "   ⚠️  Skipping connection test (no connector ID)"
fi
echo ""

# List all connectors
echo "5️⃣  Current connectors:"
curl -s $API_URL/connectors/ | python3 << 'PYEOF'
import json, sys
try:
    data = json.load(sys.stdin)
    connectors = data.get('connectors', [])
    print(f"   Total: {len(connectors)} connector(s)")
    for c in connectors:
        status = "✅" if c.get('enabled') else "⏸️ "
        print(f"   {status} {c.get('source_name')} ({c.get('source_type')})")
except:
    print("   ⚠️  Could not list connectors")
PYEOF
echo ""

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ Week 4 Quick Test Complete                               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📚 Next Steps:"
echo "   • View connector docs: cat WEEK4_CONNECTORS.md"
echo "   • API documentation: http://localhost:8000/docs"
echo "   • Create more connectors via API or web UI"
echo ""
