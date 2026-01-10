#!/bin/bash
# ============================================================================
# Database Health Check Script
# ============================================================================
# Description: Checks health of PostgreSQL and Redis
# Usage: ./scripts/db-health-check.sh
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values (can be overridden by environment variables)
POSTGRES_HOST=${POSTGRES_SERVER:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_USER=${POSTGRES_USER:-atlas_user}
POSTGRES_DB=${POSTGRES_DB:-atlas_pipeline}
REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Atlas Data Pipeline - Database Health Check${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Function to check PostgreSQL
check_postgres() {
    echo -e "${BLUE}Checking PostgreSQL...${NC}"

    if command -v pg_isready &> /dev/null; then
        if pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" &> /dev/null; then
            echo -e "${GREEN}✓ PostgreSQL is ready${NC}"

            # Try to connect and get version
            if command -v psql &> /dev/null; then
                VERSION=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT version();" 2>/dev/null | head -n1)
                echo -e "${GREEN}  Version: ${VERSION}${NC}"
            fi

            return 0
        else
            echo -e "${RED}✗ PostgreSQL is not ready${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠ pg_isready not found, trying alternative method...${NC}"

        # Alternative check using psql
        if PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' &> /dev/null; then
            echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
            return 0
        else
            echo -e "${RED}✗ PostgreSQL is not ready${NC}"
            return 1
        fi
    fi
}

# Function to check Redis
check_redis() {
    echo -e "${BLUE}Checking Redis...${NC}"

    if command -v redis-cli &> /dev/null; then
        if [ -n "$REDIS_PASSWORD" ]; then
            if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" ping &> /dev/null; then
                echo -e "${GREEN}✓ Redis is ready${NC}"

                # Get Redis info
                VERSION=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" INFO server | grep redis_version | cut -d: -f2 | tr -d '\r')
                echo -e "${GREEN}  Version: ${VERSION}${NC}"

                return 0
            else
                echo -e "${RED}✗ Redis is not ready${NC}"
                return 1
            fi
        else
            if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping &> /dev/null; then
                echo -e "${GREEN}✓ Redis is ready${NC}"
                return 0
            else
                echo -e "${RED}✗ Redis is not ready${NC}"
                return 1
            fi
        fi
    else
        echo -e "${YELLOW}⚠ redis-cli not found${NC}"

        # Try using netcat as fallback
        if command -v nc &> /dev/null; then
            if nc -z "$REDIS_HOST" "$REDIS_PORT" &> /dev/null; then
                echo -e "${GREEN}✓ Redis port is open${NC}"
                return 0
            else
                echo -e "${RED}✗ Redis port is not accessible${NC}"
                return 1
            fi
        else
            echo -e "${YELLOW}⚠ Cannot verify Redis (no redis-cli or nc)${NC}"
            return 2
        fi
    fi
}

# Run checks
POSTGRES_OK=0
REDIS_OK=0

if ! check_postgres; then
    POSTGRES_OK=1
fi
echo ""

if ! check_redis; then
    REDIS_OK=1
fi
echo ""

# Summary
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}============================================================================${NC}"

if [ $POSTGRES_OK -eq 0 ] && [ $REDIS_OK -eq 0 ]; then
    echo -e "${GREEN}All database services are healthy!${NC}"
    exit 0
elif [ $POSTGRES_OK -ne 0 ] && [ $REDIS_OK -ne 0 ]; then
    echo -e "${RED}Both PostgreSQL and Redis are not healthy!${NC}"
    exit 1
elif [ $POSTGRES_OK -ne 0 ]; then
    echo -e "${YELLOW}PostgreSQL is not healthy!${NC}"
    exit 1
elif [ $REDIS_OK -ne 0 ]; then
    echo -e "${YELLOW}Redis is not healthy!${NC}"
    exit 1
fi
