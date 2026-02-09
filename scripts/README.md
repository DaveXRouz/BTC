# NPS Scripts

## Overview

Deployment, backup, and operational scripts for NPS infrastructure management.

## Scripts

| Script        | Description                                                   |
| ------------- | ------------------------------------------------------------- |
| `deploy.sh`   | Build and deploy all services (pull, build, migrate, restart) |
| `backup.sh`   | PostgreSQL backup with encrypted findings export              |
| `restore.sh`  | Restore from backup (database + encrypted data)               |
| `rollback.sh` | Rollback to previous deployment version                       |

## Usage

```bash
# Deploy latest
./scripts/deploy.sh

# Backup database
./scripts/backup.sh

# Restore from backup
./scripts/restore.sh backups/nps_2026-02-08.sql.gz

# Rollback to previous version
./scripts/rollback.sh
```

## Notes

- All scripts expect to be run from the project root directory.
- Scripts use environment variables from `.env` for database credentials and paths.
- Backup files are stored in `backups/` (gitignored).
- Rollback keeps the previous Docker image tags for instant rollback.
