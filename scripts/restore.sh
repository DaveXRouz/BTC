#!/bin/bash
# NPS — PostgreSQL restore script
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V4_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$V4_DIR/backups"

# Load environment
if [ -f "$V4_DIR/.env" ]; then
    source "$V4_DIR/.env"
fi

POSTGRES_DB="${POSTGRES_DB:-nps}"
POSTGRES_USER="${POSTGRES_USER:-nps}"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Available backups:"
    ls -lt "$BACKUP_DIR"/nps_backup_*.sql.gz 2>/dev/null | head -10
    exit 1
fi

BACKUP_FILE="$1"
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "=== NPS Database Restore ==="
echo "Database: $POSTGRES_DB"
echo "Backup: $BACKUP_FILE"
echo ""
echo "WARNING: This will DROP and recreate the database!"
read -p "Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Drop and recreate database
docker compose -f "$V4_DIR/docker-compose.yml" exec -T postgres \
    psql -U "$POSTGRES_USER" -c "DROP DATABASE IF EXISTS $POSTGRES_DB;"
docker compose -f "$V4_DIR/docker-compose.yml" exec -T postgres \
    psql -U "$POSTGRES_USER" -c "CREATE DATABASE $POSTGRES_DB;"

# Restore
gunzip -c "$BACKUP_FILE" | docker compose -f "$V4_DIR/docker-compose.yml" exec -T postgres \
    psql -U "$POSTGRES_USER" "$POSTGRES_DB"

echo "Restore complete."
