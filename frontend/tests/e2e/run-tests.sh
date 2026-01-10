#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   Atlas Dashboard - E2E Test Suite                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check services
echo "🔍 Checking services..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Backend API not running"
    echo "   Start: cd /Users/sven/Desktop/MCP/.worktrees/atlas-api && python3 simple_main.py"
    exit 1
fi
echo "✅ Backend API running"

if ! curl -s http://localhost:5174 > /dev/null 2>&1; then
    echo "❌ Frontend not running"
    echo "   Start: npm run dev"
    exit 1
fi
echo "✅ Frontend running"
echo ""

# Run tests
echo "🧪 Running Playwright tests..."
npx playwright test "$@"

# Show report
echo ""
echo "📊 Test report: npx playwright show-report"
