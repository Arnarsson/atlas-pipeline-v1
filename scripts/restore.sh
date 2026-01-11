#!/bin/bash
# ============================================================================
# Atlas Data Pipeline - Database Restore Script
# ============================================================================
# Purpose: Restore PostgreSQL database from backup
# Usage: ./restore.sh <backup_file>
# ============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration
POSTGRES_HOST="${POSTGRES_SERVER:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-atlas_pipeline}"
POSTGRES_USER="${POSTGRES_USER:-atlas_user}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Validate arguments
if [ $# -eq 0 ]; then
    error "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Confirm restore
log "=== Atlas Data Pipeline Database Restore ==="
log "Backup file: $BACKUP_FILE"
log "Target database: $POSTGRES_DB on $POSTGRES_HOST:$POSTGRES_PORT"
warn "This will OVERWRITE the current database!"

read -p "Are you sure you want to proceed? (yes/no): " confirmation
if [ "$confirmation" != "yes" ]; then
    log "Restore cancelled by user"
    exit 0
fi

# Create backup of current database before restore
log "Creating safety backup of current database..."
SAFETY_BACKUP="/tmp/atlas_pre_restore_$(date +%Y%m%d_%H%M%S).sql.gz"
PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    | gzip > "$SAFETY_BACKUP"
log "Safety backup created: $SAFETY_BACKUP"

# Restore database
log "Starting database restore..."

gunzip -c "$BACKUP_FILE" | PGPASSWORD="$POSTGRES_PASSWORD" psql \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --quiet

if [ $? -eq 0 ]; then
    log "Database restore completed successfully"
    log "Safety backup available at: $SAFETY_BACKUP"
else
    error "Database restore failed"
    log "Safety backup available at: $SAFETY_BACKUP"
    exit 1
fi
