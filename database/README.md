# V4 Database Layer

## Overview

PostgreSQL database replacing V3's JSON/JSONL file-based storage. Provides ACID transactions, proper indexing, and concurrent access for all V4 services.

## Schema

Defined in `init.sql` with 10 tables:

| Table              | V3 Source                | Description              |
| ------------------ | ------------------------ | ------------------------ |
| `users`            | New                      | User accounts with auth  |
| `api_keys`         | New                      | API key management       |
| `scan_sessions`    | `data/sessions/` JSON    | Scan session tracking    |
| `scan_checkpoints` | `data/checkpoints/` JSON | Scanner checkpoint state |
| `findings`         | `data/findings/` JSONL   | Encrypted findings vault |
| `oracle_readings`  | In-memory                | Oracle reading history   |
| `learning_data`    | `data/learning/` JSON    | AI learning state        |
| `learning_history` | `data/learning/` JSON    | XP/level history         |
| `patterns`         | `data/learning/` JSON    | Pattern analysis data    |
| `config`           | `config.json`            | Runtime configuration    |

## Migration from V3

V3 stores data in flat files under `nps/data/`:

- `findings/` — JSONL with encrypted fields
- `sessions/` — JSON session files
- `checkpoints/` — JSON checkpoint files
- `learning/` — JSON learning state

Migration scripts in `migrations/` handle:

1. Reading V3 JSON/JSONL files
2. Decrypting V3 `ENC:` encrypted fields
3. Re-encrypting with V4 `ENC4:` (AES-256-GCM)
4. Inserting into PostgreSQL tables

Seed data in `seeds/` provides development defaults.

## Key Commands

```bash
# Initialize database (Docker)
docker-compose up -d postgres
docker-compose exec postgres psql -U nps -f /docker-entrypoint-initdb.d/init.sql

# Run migrations
python migrations/v3_to_v4.py --v3-data-dir ../../nps/data

# Backup
../scripts/backup.sh

# Restore
../scripts/restore.sh <backup-file>
```

## Security

- All sensitive fields (private keys, seeds, mnemonics) are encrypted at the application level before storage.
- Database credentials via environment variables, never in code.
- Connection pooling via asyncpg for the API layer.
