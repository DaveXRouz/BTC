# Oracle Database Scripts

Scripts for backing up and restoring Oracle domain tables independently from the main NPS V4 database.

## Tables Covered

| Table                  | Description                             |
| ---------------------- | --------------------------------------- |
| `oracle_users`         | User profiles with Persian name support |
| `oracle_readings`      | FC60, numerology, and AI readings       |
| `oracle_reading_users` | Junction table for multi-user readings  |
| `oracle_audit_log`     | Security audit trail                    |

## Scripts

### `oracle_backup.sh`

Backs up only Oracle tables using `pg_dump -t`.

```bash
# Full backup (schema + data)
./oracle_backup.sh

# Data-only backup
./oracle_backup.sh --data-only
```

Backups are stored in `v4/backups/oracle/` as gzipped SQL files. Retention: 30 backups per type (full/data-only).

### `oracle_restore.sh`

Restores Oracle tables from a backup file. Truncates only Oracle tables (does NOT drop the full database).

```bash
# Restore from a specific backup
./oracle_restore.sh ../../../backups/oracle/oracle_full_20240115_143000.sql.gz

# List available backups (run with no args)
./oracle_restore.sh
```

Includes a confirmation prompt and post-restore row count verification.

## Environment Variables

| Variable        | Default | Description   |
| --------------- | ------- | ------------- |
| `POSTGRES_DB`   | `nps`   | Database name |
| `POSTGRES_USER` | `nps`   | Database user |

Variables are loaded from `v4/.env` if present, or can be set in the shell environment.

## Full Database Backup

For full database backup/restore (all tables), use the scripts in `v4/scripts/`:

```bash
v4/scripts/backup.sh      # Full database backup
v4/scripts/restore.sh      # Full database restore (drops and recreates DB)
```
