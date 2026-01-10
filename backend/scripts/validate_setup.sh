#!/bin/bash

# ============================================================================
# Atlas Data Pipeline Platform - Setup Validation Script
# ============================================================================
#
# This script validates the Day 4 CI/CD and Monitoring setup:
# 1. GitHub Actions workflow syntax
# 2. Pre-commit hooks configuration
# 3. Code quality tools (ruff, black, mypy)
# 4. Pytest configuration
# 5. Prometheus metrics
#
# Usage: ./scripts/validate_setup.sh

set -e  # Exit on error

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Atlas Data Pipeline - Setup Validation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

ERRORS=0
WARNINGS=0

# ============================================================================
# Helper Functions
# ============================================================================

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ERRORS=$((ERRORS + 1))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

# ============================================================================
# 1. Check GitHub Actions Workflow
# ============================================================================

echo -e "${BLUE}[1/7] Checking GitHub Actions workflow...${NC}"

if [ -f ".github/workflows/ci.yml" ]; then
    check_pass "CI workflow file exists"

    # Validate YAML syntax (basic check)
    if command -v yamllint &> /dev/null; then
        if yamllint -d relaxed .github/workflows/ci.yml &> /dev/null; then
            check_pass "CI workflow YAML syntax is valid"
        else
            check_fail "CI workflow YAML syntax is invalid"
        fi
    else
        check_warn "yamllint not found, skipping YAML validation"
    fi

    # Check for required jobs
    if grep -q "jobs:" .github/workflows/ci.yml && \
       grep -q "lint:" .github/workflows/ci.yml && \
       grep -q "test:" .github/workflows/ci.yml; then
        check_pass "Required CI jobs are configured"
    else
        check_fail "Missing required CI jobs"
    fi
else
    check_fail "CI workflow file not found"
fi

echo ""

# ============================================================================
# 2. Check Pre-commit Configuration
# ============================================================================

echo -e "${BLUE}[2/7] Checking pre-commit configuration...${NC}"

if [ -f ".pre-commit-config.yaml" ]; then
    check_pass "Pre-commit config file exists"

    # Check for required hooks
    if grep -q "black" .pre-commit-config.yaml && \
       grep -q "ruff" .pre-commit-config.yaml && \
       grep -q "mypy" .pre-commit-config.yaml; then
        check_pass "Required pre-commit hooks are configured"
    else
        check_fail "Missing required pre-commit hooks"
    fi
else
    check_fail "Pre-commit config file not found"
fi

echo ""

# ============================================================================
# 3. Check Code Quality Tools Configuration
# ============================================================================

echo -e "${BLUE}[3/7] Checking code quality tools...${NC}"

# Check pyproject.toml
if [ -f "pyproject.toml" ]; then
    check_pass "pyproject.toml exists"

    # Check tool configurations
    if grep -q "\[tool.ruff\]" pyproject.toml; then
        check_pass "Ruff configuration found"
    else
        check_fail "Ruff configuration missing"
    fi

    if grep -q "\[tool.black\]" pyproject.toml; then
        check_pass "Black configuration found"
    else
        check_fail "Black configuration missing"
    fi

    if grep -q "\[tool.mypy\]" pyproject.toml; then
        check_pass "Mypy configuration found"
    else
        check_fail "Mypy configuration missing"
    fi

    if grep -q "\[tool.pytest" pyproject.toml; then
        check_pass "Pytest configuration found"
    else
        check_fail "Pytest configuration missing"
    fi

    if grep -q "\[tool.coverage" pyproject.toml; then
        check_pass "Coverage configuration found"
    else
        check_fail "Coverage configuration missing"
    fi
else
    check_fail "pyproject.toml not found"
fi

echo ""

# ============================================================================
# 4. Check Python Tools Available
# ============================================================================

echo -e "${BLUE}[4/7] Checking Python tools availability...${NC}"

if command -v ruff &> /dev/null; then
    check_pass "ruff is available ($(ruff --version))"
else
    check_fail "ruff is not installed"
fi

if command -v black &> /dev/null; then
    check_pass "black is available ($(black --version))"
else
    check_fail "black is not installed"
fi

if command -v mypy &> /dev/null; then
    check_pass "mypy is available ($(mypy --version))"
else
    check_fail "mypy is not installed"
fi

if command -v pytest &> /dev/null; then
    check_pass "pytest is available ($(pytest --version | head -1))"
else
    check_fail "pytest is not installed"
fi

echo ""

# ============================================================================
# 5. Check Test Framework
# ============================================================================

echo -e "${BLUE}[5/7] Checking test framework...${NC}"

if [ -f "tests/conftest.py" ]; then
    check_pass "Test fixtures file exists"

    # Check for required fixtures
    if grep -q "def db(" tests/conftest.py && \
       grep -q "def client(" tests/conftest.py; then
        check_pass "Required test fixtures are defined"
    else
        check_fail "Missing required test fixtures"
    fi
else
    check_fail "Test fixtures file not found"
fi

if [ -d "tests/pipeline" ]; then
    check_pass "Pipeline tests directory exists"
else
    check_warn "Pipeline tests directory not found"
fi

echo ""

# ============================================================================
# 6. Check Prometheus Metrics
# ============================================================================

echo -e "${BLUE}[6/7] Checking Prometheus metrics setup...${NC}"

if [ -f "app/core/metrics.py" ]; then
    check_pass "Metrics module exists"

    # Check for key metric functions
    if grep -q "create_instrumentator" app/core/metrics.py && \
       grep -q "record_pipeline_execution" app/core/metrics.py && \
       grep -q "record_quality_check" app/core/metrics.py; then
        check_pass "Required metric functions are defined"
    else
        check_fail "Missing required metric functions"
    fi
else
    check_fail "Metrics module not found"
fi

if [ -f "app/main.py" ]; then
    if grep -q "from app.core.metrics import" app/main.py; then
        check_pass "Metrics integrated into FastAPI app"
    else
        check_fail "Metrics not integrated into FastAPI app"
    fi
fi

if [ -f "docs/METRICS.md" ]; then
    check_pass "Metrics documentation exists"
else
    check_warn "Metrics documentation not found"
fi

echo ""

# ============================================================================
# 7. Check Makefile
# ============================================================================

echo -e "${BLUE}[7/7] Checking development Makefile...${NC}"

if [ -f "Makefile" ]; then
    check_pass "Makefile exists"

    # Check for required targets
    if grep -q "^lint:" Makefile && \
       grep -q "^test:" Makefile && \
       grep -q "^format:" Makefile && \
       grep -q "^type-check:" Makefile; then
        check_pass "Required Makefile targets are defined"
    else
        check_fail "Missing required Makefile targets"
    fi
else
    check_warn "Makefile not found"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Validation Summary${NC}"
echo -e "${BLUE}========================================${NC}"

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
else
    echo -e "${RED}✗ Found $ERRORS error(s)${NC}"
fi

if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠ Found $WARNINGS warning(s)${NC}"
fi

echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}CI/CD and Monitoring setup is complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Install pre-commit hooks: make install-pre-commit"
    echo "2. Run tests: make test"
    echo "3. Run quality checks: make quality"
    echo "4. Start dev server: make dev"
    echo "5. View metrics: curl http://localhost:8000/metrics"
    exit 0
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}Please fix the errors before proceeding${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi
