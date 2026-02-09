#!/bin/bash
# NPS — Oracle Tables Backup Script
# Backs up only Oracle domain tables (not the full database).
#
# Usage:
#   ./oracle_backup.sh              # Full backup (schema + data)
#   ./oracle_backup.sh --data-only  # Data-only backup
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_DIR="$(dirname "$SCRIPT_DIR")"
V4_DIR="$(dirname "$DB_DIR")"
BACKUP_DIR="$V4_DIR/backups/oracle"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Parse flags
DATA_ONLY=false
if [[ "${1:-}" == "--data-only" ]]; then
    DATA_ONLY=true
fi

# Load environment
if [ -f "$V4_DIR/.env" ]; then
    # shellcheck source=/dev/null
    source "$V4_DIR/.env"
fi

POSTGRES_DB="${POSTGRES_DB:-nps}"
POSTGRES_USER="${POSTGRES_USER:-nps}"

# Oracle tables to back up
ORACLE_TABLES=(
    "oracle_users"
    "oracle_readings"
    "oracle_reading_users"
    "oracle_audit_log"
)

# Build pg_dump table flags
TABLE_FLAGS=""
for table in "${ORACLE_TABLES[@]}"; do
    TABLE_FLAGS="$TABLE_FLAGS -t $table"
done

# Determine backup type
if $DATA_ONLY; then
    BACKUP_FILE="$BACKUP_DIR/oracle_data_${TIMESTAMP}.sql.gz"
    DUMP_FLAGS="--data-only"
    BACKUP_TYPE="data-only"
else
    BACKUP_FILE="$BACKUP_DIR/oracle_full_${TIMESTAMP}.sql.gz"
    DUMP_FLAGS=""
    BACKUP_TYPE="full"
fi

echo "=== NPS Oracle Backup ==="
echo "Type: $BACKUP_TYPE"
echo "Database: $POSTGRES_DB"
echo "Tables: ${ORACLE_TABLES[*]}"
echo "Output: $BACKUP_FILE"

mkdir -p "$BACKUP_DIR"

# Dump and compress
# shellcheck disable=SC2086
docker compose -f "$V4_DIR/docker-compose.yml" exec -T postgres \
    pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" $TABLE_FLAGS $DUMP_FLAGS | gzip > "$BACKUP_FILE"

# Verify
if [ -s "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "Backup complete: $BACKUP_FILE ($SIZE)"

    # Keep only last 30 backups (per type)
    if $DATA_ONLY; then
        ls -t "$BACKUP_DIR"/oracle_data_*.sql.gz 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null || true
    else
        ls -t "$BACKUP_DIR"/oracle_full_*.sql.gz 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null || true
    fi
    echo "Retention: keeping last 30 backups per type"
else
    echo "ERROR: Backup file is empty!"
    rm -f "$BACKUP_FILE"
    exit 1
fi
