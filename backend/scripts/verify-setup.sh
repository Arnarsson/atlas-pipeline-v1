#!/bin/bash
# ============================================================================
# Atlas Data Pipeline Platform - Setup Verification Script
# ============================================================================
# Description: Verifies all components are properly configured
# Usage: ./scripts/verify-setup.sh
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Atlas Data Pipeline Platform - Setup Verification${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Function to check Docker services
check_docker_services() {
    echo -e "${CYAN}Checking Docker Services...${NC}"

    if docker ps | grep -q atlas-db; then
        echo -e "${GREEN}✓ PostgreSQL container is running${NC}"
    else
        echo -e "${RED}✗ PostgreSQL container is not running${NC}"
        return 1
    fi

    if docker ps | grep -q atlas-redis; then
        echo -e "${GREEN}✓ Redis container is running${NC}"
    else
        echo -e "${RED}✗ Redis container is not running${NC}"
        return 1
    fi

    echo ""
}

# Function to verify databases
verify_databases() {
    echo -e "${CYAN}Verifying Databases...${NC}"

    DATABASES=("atlas_pipeline" "atlas_bronze" "atlas_silver" "atlas_gold" "atlas_pipeline_test" "prefect")

    for db in "${DATABASES[@]}"; do
        if docker exec atlas-db psql -U atlas_user -lqt | cut -d \| -f 1 | grep -qw "$db"; then
            echo -e "${GREEN}✓ Database '$db' exists${NC}"
        else
            echo -e "${RED}✗ Database '$db' does not exist${NC}"
            return 1
        fi
    done

    echo ""
}

# Function to verify PostgreSQL extensions
verify_extensions() {
    echo -e "${CYAN}Verifying PostgreSQL Extensions...${NC}"

    EXTENSIONS=("uuid-ossp" "pg_trgm" "btree_gin" "btree_gist")

    for ext in "${EXTENSIONS[@]}"; do
        if docker exec atlas-db psql -U atlas_user -d atlas_pipeline -c "\dx" | grep -q "$ext"; then
            echo -e "${GREEN}✓ Extension '$ext' is installed${NC}"
        else
            echo -e "${YELLOW}⚠ Extension '$ext' is not installed${NC}"
        fi
    done

    echo ""
}

# Function to verify schemas
verify_schemas() {
    echo -e "${CYAN}Verifying Database Schemas...${NC}"

    SCHEMAS=("pipeline" "monitoring" "audit")

    for schema in "${SCHEMAS[@]}"; do
        if docker exec atlas-db psql -U atlas_user -d atlas_pipeline -c "\dn" | grep -q "$schema"; then
            echo -e "${GREEN}✓ Schema '$schema' exists${NC}"
        else
            echo -e "${RED}✗ Schema '$schema' does not exist${NC}"
            return 1
        fi
    done

    echo ""
}

# Function to test Redis
test_redis() {
    echo -e "${CYAN}Testing Redis...${NC}"

    if docker exec atlas-redis redis-cli -a changethis ping | grep -q "PONG"; then
        echo -e "${GREEN}✓ Redis is responding${NC}"
    else
        echo -e "${RED}✗ Redis is not responding${NC}"
        return 1
    fi

    # Test set/get
    docker exec atlas-redis redis-cli -a changethis SET test_key "test_value" > /dev/null 2>&1
    if docker exec atlas-redis redis-cli -a changethis GET test_key | grep -q "test_value"; then
        echo -e "${GREEN}✓ Redis read/write works${NC}"
        docker exec atlas-redis redis-cli -a changethis DEL test_key > /dev/null 2>&1
    else
        echo -e "${RED}✗ Redis read/write failed${NC}"
        return 1
    fi

    echo ""
}

# Function to verify Alembic
verify_alembic() {
    echo -e "${CYAN}Verifying Alembic Setup...${NC}"

    if [ -f "alembic.ini" ]; then
        echo -e "${GREEN}✓ alembic.ini exists${NC}"
    else
        echo -e "${RED}✗ alembic.ini not found${NC}"
        return 1
    fi

    if [ -d "app/alembic/versions" ]; then
        MIGRATION_COUNT=$(ls -1 app/alembic/versions/*.py 2>/dev/null | grep -v __pycache__ | wc -l)
        echo -e "${GREEN}✓ Alembic migrations directory exists ($MIGRATION_COUNT migrations)${NC}"
    else
        echo -e "${RED}✗ Alembic migrations directory not found${NC}"
        return 1
    fi

    echo ""
}

# Function to verify environment configuration
verify_env_config() {
    echo -e "${CYAN}Verifying Environment Configuration...${NC}"

    if [ -f ".env" ]; then
        echo -e "${GREEN}✓ .env file exists${NC}"
    else
        echo -e "${YELLOW}⚠ .env file not found (using .env.example)${NC}"
    fi

    if [ -f ".env.example" ]; then
        echo -e "${GREEN}✓ .env.example exists${NC}"
    else
        echo -e "${RED}✗ .env.example not found${NC}"
    fi

    echo ""
}

# Function to check PostgreSQL performance settings
check_postgres_performance() {
    echo -e "${CYAN}Checking PostgreSQL Performance Settings...${NC}"

    # Check shared_buffers
    SHARED_BUFFERS=$(docker exec atlas-db psql -U atlas_user -d atlas_pipeline -t -c "SHOW shared_buffers;" | xargs)
    echo -e "${GREEN}✓ shared_buffers: $SHARED_BUFFERS${NC}"

    # Check max_connections
    MAX_CONN=$(docker exec atlas-db psql -U atlas_user -d atlas_pipeline -t -c "SHOW max_connections;" | xargs)
    echo -e "${GREEN}✓ max_connections: $MAX_CONN${NC}"

    # Check effective_cache_size
    CACHE_SIZE=$(docker exec atlas-db psql -U atlas_user -d atlas_pipeline -t -c "SHOW effective_cache_size;" | xargs)
    echo -e "${GREEN}✓ effective_cache_size: $CACHE_SIZE${NC}"

    echo ""
}

# Function to check Redis configuration
check_redis_config() {
    echo -e "${CYAN}Checking Redis Configuration...${NC}"

    # Check max memory
    MAX_MEM=$(docker exec atlas-redis redis-cli -a changethis CONFIG GET maxmemory 2>/dev/null | tail -1)
    echo -e "${GREEN}✓ maxmemory: $MAX_MEM bytes${NC}"

    # Check max memory policy
    MEM_POLICY=$(docker exec atlas-redis redis-cli -a changethis CONFIG GET maxmemory-policy 2>/dev/null | tail -1)
    echo -e "${GREEN}✓ maxmemory-policy: $MEM_POLICY${NC}"

    # Check persistence
    AOF=$(docker exec atlas-redis redis-cli -a changethis CONFIG GET appendonly 2>/dev/null | tail -1)
    echo -e "${GREEN}✓ appendonly (AOF): $AOF${NC}"

    echo ""
}

# Print summary
print_summary() {
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}Summary${NC}"
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${GREEN}All verification checks passed!${NC}"
    echo ""
    echo -e "${CYAN}Services:${NC}"
    echo -e "  • PostgreSQL: http://localhost:5432"
    echo -e "  • Redis: http://localhost:6379"
    echo -e "  • Adminer (DB UI): http://localhost:8081"
    echo ""
    echo -e "${CYAN}Databases:${NC}"
    echo -e "  • atlas_pipeline (main)"
    echo -e "  • atlas_bronze (medallion layer)"
    echo -e "  • atlas_silver (medallion layer)"
    echo -e "  • atlas_gold (medallion layer)"
    echo -e "  • atlas_pipeline_test (testing)"
    echo -e "  • prefect (orchestration)"
    echo ""
    echo -e "${CYAN}Next Steps:${NC}"
    echo -e "  1. Run migrations: docker-compose run --rm backend alembic upgrade head"
    echo -e "  2. Start backend: docker-compose up -d backend"
    echo -e "  3. View logs: docker-compose logs -f backend"
    echo ""
}

# Run all checks
FAILED=0

check_docker_services || FAILED=1
verify_databases || FAILED=1
verify_extensions || FAILED=1
verify_schemas || FAILED=1
test_redis || FAILED=1
verify_alembic || FAILED=1
verify_env_config || FAILED=1
check_postgres_performance || FAILED=1
check_redis_config || FAILED=1

if [ $FAILED -eq 0 ]; then
    print_summary
    exit 0
else
    echo -e "${RED}Some verification checks failed!${NC}"
    echo -e "${YELLOW}Please review the errors above and fix them.${NC}"
    exit 1
fi
