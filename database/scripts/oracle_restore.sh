#!/bin/bash
# NPS — Oracle Tables Restore Script
# Restores only Oracle domain tables from a backup file.
# Does NOT drop the entire database — only truncates Oracle tables.
#
# Usage:
#   ./oracle_restore.sh <backup_file.sql.gz>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_DIR="$(dirname "$SCRIPT_DIR")"
V4_DIR="$(dirname "$DB_DIR")"
BACKUP_DIR="$V4_DIR/backups/oracle"

# Load environment
if [ -f "$V4_DIR/.env" ]; then
    # shellcheck source=/dev/null
    source "$V4_DIR/.env"
fi

POSTGRES_DB="${POSTGRES_DB:-nps}"
POSTGRES_USER="${POSTGRES_USER:-nps}"

# Oracle tables (in dependency order for truncation)
ORACLE_TABLES=(
    "oracle_reading_users"
    "oracle_audit_log"
    "oracle_readings"
    "oracle_users"
)

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo ""
    echo "Available Oracle backups:"
    ls -lt "$BACKUP_DIR"/oracle_*.sql.gz 2>/dev/null | head -10 || echo "  (none found)"
    exit 1
fi

BACKUP_FILE="$1"
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "=== NPS Oracle Restore ==="
echo "Database: $POSTGRES_DB"
echo "Backup: $BACKUP_FILE"
echo "Tables: ${ORACLE_TABLES[*]}"
echo ""
echo "WARNING: This will TRUNCATE all Oracle tables and restore from backup!"
read -p "Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Truncate Oracle tables (cascade handles FK dependencies)
echo "Truncating Oracle tables..."
docker compose -f "$V4_DIR/docker-compose.yml" exec -T postgres \
    psql -U "$POSTGRES_USER" "$POSTGRES_DB" -c \
    "TRUNCATE oracle_reading_users, oracle_audit_log, oracle_readings, oracle_users RESTART IDENTITY CASCADE;"

# Restore from backup
echo "Restoring from backup..."
gunzip -c "$BACKUP_FILE" | docker compose -f "$V4_DIR/docker-compose.yml" exec -T postgres \
    psql -U "$POSTGRES_USER" "$POSTGRES_DB"

# Verify row counts
echo ""
echo "=== Verification ==="
for table in oracle_users oracle_readings oracle_reading_users oracle_audit_log; do
    COUNT=$(docker compose -f "$V4_DIR/docker-compose.yml" exec -T postgres \
        psql -U "$POSTGRES_USER" "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM $table;" 2>/dev/null | tr -d ' ')
    echo "  $table: $COUNT rows"
done

echo ""
echo "Restore complete."
