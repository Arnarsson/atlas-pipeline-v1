#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   Atlas Dashboard - E2E Test Setup Verification             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check counters
CHECKS_PASSED=0
CHECKS_FAILED=0

# Function to check
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗${NC} $1"
        ((CHECKS_FAILED++))
    fi
}

echo "🔍 Checking prerequisites..."
echo ""

# Check Node.js
node --version > /dev/null 2>&1
check "Node.js installed"

# Check npm
npm --version > /dev/null 2>&1
check "npm installed"

# Check Playwright
npx playwright --version > /dev/null 2>&1
check "Playwright installed"

# Check if browsers installed
if [ -d "$HOME/Library/Caches/ms-playwright" ]; then
    echo -e "${GREEN}✓${NC} Playwright browsers installed"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} Playwright browsers not installed"
    echo "  Run: npx playwright install"
    ((CHECKS_FAILED++))
fi

echo ""
echo "🌐 Checking services..."
echo ""

# Check backend API
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend API running (http://localhost:8000)"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} Backend API not running"
    echo "  Start: cd /Users/sven/Desktop/MCP/.worktrees/atlas-api && python3 simple_main.py"
    ((CHECKS_FAILED++))
fi

# Check frontend
if curl -s http://localhost:5174 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Frontend running (http://localhost:5174)"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} Frontend not running"
    echo "  Start: npm run dev"
    ((CHECKS_FAILED++))
fi

echo ""
echo "📁 Checking test files..."
echo ""

# Check test files exist
TEST_FILES=(
    "tests/e2e/01-navigation.spec.ts"
    "tests/e2e/02-csv-upload.spec.ts"
    "tests/e2e/03-connectors.spec.ts"
    "tests/e2e/04-quality-reports.spec.ts"
    "tests/e2e/05-gdpr.spec.ts"
    "tests/e2e/06-catalog.spec.ts"
    "tests/e2e/07-features.spec.ts"
    "tests/e2e/08-user-journey.spec.ts"
    "tests/e2e/09-performance.spec.ts"
    "tests/e2e/10-visual.spec.ts"
    "tests/e2e/helpers/setup.ts"
    "playwright.config.ts"
)

for file in "${TEST_FILES[@]}"; do
    if [ -f "$file" ]; then
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗${NC} Missing: $file"
        ((CHECKS_FAILED++))
    fi
done

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓${NC} All test files present (12 files)"
fi

echo ""
echo "📋 Checking package.json scripts..."
echo ""

# Check test scripts
if grep -q "test:e2e" package.json; then
    echo -e "${GREEN}✓${NC} Test scripts configured"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} Test scripts not configured"
    ((CHECKS_FAILED++))
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Results: ${GREEN}${CHECKS_PASSED} passed${NC}, ${RED}${CHECKS_FAILED} failed${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Setup verification complete - Ready to run tests!${NC}"
    echo ""
    echo "Run tests with:"
    echo "  npm run test:e2e          # Run all tests"
    echo "  npm run test:e2e:ui       # Interactive UI mode"
    echo "  npm run test:e2e:debug    # Debug mode"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Setup incomplete - Fix issues above before running tests${NC}"
    echo ""
    exit 1
fi
