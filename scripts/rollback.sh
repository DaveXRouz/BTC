#!/bin/bash
# NPS V4 — Rollback to previous version
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V4_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== NPS V4 Rollback ==="

# Stop current services
echo "Stopping current services..."
cd "$V4_DIR"
docker compose down

# Find most recent backup
BACKUP_DIR="$V4_DIR/backups"
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/nps_backup_*.sql.gz 2>/dev/null | head -1)

if [ -n "$LATEST_BACKUP" ]; then
    echo "Latest backup: $LATEST_BACKUP"
    read -p "Restore this backup? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        "$SCRIPT_DIR/restore.sh" "$LATEST_BACKUP"
    fi
fi

# Restart services
echo "Restarting services..."
docker compose up -d

echo "Rollback complete."
