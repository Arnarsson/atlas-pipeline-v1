#!/bin/bash

# ============================================================================
# Week 3 Installation Script
# ============================================================================
# Installs Presidio, Soda Core, and spaCy dependencies for Week 3
# ============================================================================

set -e  # Exit on error

echo "==================================================================="
echo "Atlas Data Pipeline - Week 3 Installation"
echo "==================================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ============================================================================
# Step 1: Check Python version
# ============================================================================
echo "Step 1: Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.9"

if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION (meets requirement ≥$REQUIRED_VERSION)"
else
    echo -e "${RED}✗${NC} Python $PYTHON_VERSION is too old (requires ≥$REQUIRED_VERSION)"
    exit 1
fi

echo ""

# ============================================================================
# Step 2: Install Python packages
# ============================================================================
echo "Step 2: Installing Python packages..."

pip3 install --quiet presidio-analyzer==2.2.354
echo -e "${GREEN}✓${NC} presidio-analyzer installed"

pip3 install --quiet presidio-anonymizer==2.2.354
echo -e "${GREEN}✓${NC} presidio-anonymizer installed"

pip3 install --quiet spacy==3.7.2
echo -e "${GREEN}✓${NC} spacy installed"

pip3 install --quiet soda-core-postgres==3.3.2
echo -e "${GREEN}✓${NC} soda-core-postgres installed"

pip3 install --quiet soda-core-scientific==3.3.2
echo -e "${GREEN}✓${NC} soda-core-scientific installed"

pip3 install --quiet tenacity==8.2.3
echo -e "${GREEN}✓${NC} tenacity installed"

echo ""

# ============================================================================
# Step 3: Download spaCy models
# ============================================================================
echo "Step 3: Downloading spaCy language models..."

# English model (required)
if python3 -m spacy validate 2>&1 | grep -q "en_core_web_sm"; then
    echo -e "${YELLOW}→${NC} English model already installed, skipping..."
else
    echo "Downloading English model (en_core_web_sm)..."
    python3 -m spacy download en_core_web_sm
    echo -e "${GREEN}✓${NC} English model installed"
fi

# Danish model (optional)
echo ""
read -p "Install Danish language model (da_core_news_sm)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if python3 -m spacy validate 2>&1 | grep -q "da_core_news_sm"; then
        echo -e "${YELLOW}→${NC} Danish model already installed, skipping..."
    else
        echo "Downloading Danish model (da_core_news_sm)..."
        python3 -m spacy download da_core_news_sm
        echo -e "${GREEN}✓${NC} Danish model installed"
    fi
else
    echo -e "${YELLOW}→${NC} Skipping Danish model (can install later with: python -m spacy download da_core_news_sm)"
fi

echo ""

# ============================================================================
# Step 4: Verify installation
# ============================================================================
echo "Step 4: Verifying installation..."

# Test Presidio
if python3 -c "from presidio_analyzer import AnalyzerEngine" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Presidio can be imported"
else
    echo -e "${RED}✗${NC} Presidio import failed"
    exit 1
fi

# Test spaCy
if python3 -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} spaCy English model can be loaded"
else
    echo -e "${RED}✗${NC} spaCy model loading failed"
    exit 1
fi

# Test Soda Core
if python3 -c "from soda.scan import Scan" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Soda Core can be imported"
else
    echo -e "${YELLOW}⚠${NC} Soda Core import check skipped (optional)"
fi

echo ""

# ============================================================================
# Step 5: Run database migration (optional)
# ============================================================================
echo "Step 5: Database migration..."
echo ""
read -p "Run database migration now? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running migration..."
    if command -v docker &> /dev/null && docker ps | grep -q atlas-db; then
        # Docker-based database
        docker exec -i atlas-db psql -U atlas_user -d atlas_pipeline < database/migrations/005_week3_presidio_soda.sql
        echo -e "${GREEN}✓${NC} Migration applied (Docker)"
    elif command -v psql &> /dev/null; then
        # Local PostgreSQL
        psql -U atlas_user -d atlas_pipeline -f database/migrations/005_week3_presidio_soda.sql
        echo -e "${GREEN}✓${NC} Migration applied (local PostgreSQL)"
    else
        echo -e "${YELLOW}⚠${NC} Database migration skipped (run manually later)"
    fi
else
    echo -e "${YELLOW}→${NC} Skipping migration (run manually with: psql -U atlas_user -d atlas_pipeline -f database/migrations/005_week3_presidio_soda.sql)"
fi

echo ""

# ============================================================================
# Step 6: Run tests (optional)
# ============================================================================
echo "Step 6: Testing..."
echo ""
read -p "Run unit tests now? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v pytest &> /dev/null; then
        echo "Running unit tests..."
        pytest tests/unit/test_presidio_detector.py -v --tb=short
        pytest tests/unit/test_soda_validator.py -v --tb=short
        echo -e "${GREEN}✓${NC} Tests completed"
    else
        echo -e "${YELLOW}⚠${NC} pytest not installed (install with: pip install pytest)"
    fi
else
    echo -e "${YELLOW}→${NC} Skipping tests (run manually with: pytest tests/unit/ -v)"
fi

echo ""

# ============================================================================
# Success
# ============================================================================
echo "==================================================================="
echo -e "${GREEN}Week 3 installation complete!${NC}"
echo "==================================================================="
echo ""
echo "Next steps:"
echo "  1. Start the API server: python3 simple_main.py"
echo "  2. Access API docs: http://localhost:8000/docs"
echo "  3. Upload a CSV to test PII detection and quality validation"
echo ""
echo "For more information, see WEEK3_IMPLEMENTATION.md"
echo ""
