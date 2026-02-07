#!/bin/bash
# NPS V4 — PostgreSQL backup script
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V4_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$V4_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/nps_backup_${TIMESTAMP}.sql.gz"

# Load environment
if [ -f "$V4_DIR/.env" ]; then
    source "$V4_DIR/.env"
fi

POSTGRES_DB="${POSTGRES_DB:-nps}"
POSTGRES_USER="${POSTGRES_USER:-nps}"

echo "=== NPS V4 Database Backup ==="
echo "Database: $POSTGRES_DB"
echo "Output: $BACKUP_FILE"

mkdir -p "$BACKUP_DIR"

# Dump and compress
docker compose -f "$V4_DIR/docker-compose.yml" exec -T postgres \
    pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$BACKUP_FILE"

# Verify
if [ -s "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "Backup complete: $BACKUP_FILE ($SIZE)"

    # Keep only last 30 backups
    ls -t "$BACKUP_DIR"/nps_backup_*.sql.gz | tail -n +31 | xargs rm -f 2>/dev/null || true
    echo "Retention: keeping last 30 backups"
else
    echo "ERROR: Backup file is empty!"
    rm -f "$BACKUP_FILE"
    exit 1
fi
