#!/bin/bash
# ============================================================================
# Atlas Data Pipeline - Automated Backup Script
# ============================================================================
# Purpose: Perform automated backups of PostgreSQL database and configuration
# Usage: ./backup.sh [daily|weekly|monthly]
# ============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/atlas}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
POSTGRES_HOST="${POSTGRES_SERVER:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-atlas_pipeline}"
POSTGRES_USER="${POSTGRES_USER:-atlas_user}"
BACKUP_TYPE="${1:-daily}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="atlas_backup_${BACKUP_TYPE}_${TIMESTAMP}"

# S3 configuration (optional)
S3_BUCKET="${S3_BACKUP_BUCKET:-}"
S3_PREFIX="${S3_BACKUP_PREFIX:-backups/}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check if pg_dump is available
    if ! command -v pg_dump &> /dev/null; then
        error "pg_dump not found. Please install PostgreSQL client tools."
        exit 1
    fi

    # Check if backup directory exists, create if not
    if [ ! -d "$BACKUP_DIR" ]; then
        log "Creating backup directory: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
    fi

    # Check if we can write to backup directory
    if [ ! -w "$BACKUP_DIR" ]; then
        error "Cannot write to backup directory: $BACKUP_DIR"
        exit 1
    fi
}

# Backup PostgreSQL database
backup_database() {
    local backup_file="$BACKUP_DIR/${BACKUP_NAME}.sql.gz"

    log "Starting PostgreSQL database backup..."
    log "Database: $POSTGRES_DB"
    log "Backup file: $backup_file"

    # Perform backup with compression
    PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --format=plain \
        --clean \
        --if-exists \
        --no-owner \
        --no-acl \
        | gzip > "$backup_file"

    if [ $? -eq 0 ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        log "Database backup completed successfully (Size: $size)"
        echo "$backup_file"
    else
        error "Database backup failed"
        exit 1
    fi
}

# Backup configuration files
backup_config() {
    local backup_file="$BACKUP_DIR/${BACKUP_NAME}_config.tar.gz"

    log "Starting configuration backup..."

    # Create tar archive of configuration
    tar -czf "$backup_file" \
        -C / \
        etc/atlas/ \
        app/.env \
        monitoring/ \
        2>/dev/null || warn "Some config files may not exist"

    if [ -f "$backup_file" ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        log "Configuration backup completed (Size: $size)"
        echo "$backup_file"
    else
        warn "Configuration backup skipped (no files found)"
        echo ""
    fi
}

# Upload to S3 (if configured)
upload_to_s3() {
    local file="$1"

    if [ -z "$S3_BUCKET" ]; then
        warn "S3_BUCKET not configured, skipping cloud backup"
        return 0
    fi

    if ! command -v aws &> /dev/null; then
        warn "AWS CLI not found, skipping cloud backup"
        return 0
    fi

    log "Uploading to S3: s3://$S3_BUCKET/$S3_PREFIX$(basename $file)"

    aws s3 cp "$file" "s3://$S3_BUCKET/$S3_PREFIX$(basename $file)" \
        --storage-class STANDARD_IA \
        --server-side-encryption AES256

    if [ $? -eq 0 ]; then
        log "S3 upload completed successfully"
    else
        error "S3 upload failed (local backup preserved)"
    fi
}

# Clean up old backups
cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days..."

    # Count before
    local count_before=$(find "$BACKUP_DIR" -name "atlas_backup_*" -type f | wc -l)

    # Delete old backups
    find "$BACKUP_DIR" -name "atlas_backup_*" -type f -mtime +$RETENTION_DAYS -delete

    # Count after
    local count_after=$(find "$BACKUP_DIR" -name "atlas_backup_*" -type f | wc -l)
    local deleted=$((count_before - count_after))

    if [ $deleted -gt 0 ]; then
        log "Deleted $deleted old backup(s)"
    else
        log "No old backups to delete"
    fi

    # Show remaining backups
    log "Current backups: $count_after file(s)"
}

# Create backup manifest
create_manifest() {
    local db_backup="$1"
    local config_backup="$2"
    local manifest_file="$BACKUP_DIR/${BACKUP_NAME}_manifest.json"

    log "Creating backup manifest..."

    cat > "$manifest_file" << EOF
{
  "backup_name": "$BACKUP_NAME",
  "backup_type": "$BACKUP_TYPE",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "database": {
    "file": "$(basename $db_backup)",
    "size_bytes": $(stat -f%z "$db_backup" 2>/dev/null || stat -c%s "$db_backup"),
    "checksum": "$(md5sum "$db_backup" | cut -d' ' -f1)"
  },
  "config": {
    "file": "$(basename $config_backup)",
    "size_bytes": $(stat -f%z "$config_backup" 2>/dev/null || stat -c%s "$config_backup" 2>/dev/null || echo 0)
  },
  "retention_days": $RETENTION_DAYS,
  "postgres_version": "$(psql --version | head -n1)"
}
EOF

    log "Manifest created: $manifest_file"
}

# Main execution
main() {
    log "=== Atlas Data Pipeline Backup ==="
    log "Backup type: $BACKUP_TYPE"
    log "Timestamp: $TIMESTAMP"

    # Run backup steps
    check_prerequisites

    # Perform backups
    db_backup=$(backup_database)
    config_backup=$(backup_config)

    # Upload to cloud (if configured)
    if [ -n "$db_backup" ]; then
        upload_to_s3 "$db_backup"
    fi
    if [ -n "$config_backup" ]; then
        upload_to_s3 "$config_backup"
    fi

    # Create manifest
    create_manifest "$db_backup" "$config_backup"

    # Cleanup old backups
    cleanup_old_backups

    log "=== Backup completed successfully ==="
}

# Run main function
main "$@"
