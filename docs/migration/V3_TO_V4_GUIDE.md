# V3 to V4 Migration Guide

## Overview

This guide covers migrating from NPS V3 (Python/Tkinter desktop app) to V4 (distributed web architecture). The migration preserves all data and functionality while moving to a modern web-based platform.

## Prerequisites

- V3 running with data in `nps/data/`
- Docker and Docker Compose installed
- PostgreSQL client tools (for verification)

## Migration Steps

### 1. Backup V3 Data

Before migrating, create a complete backup of your V3 data:

```bash
# Create timestamped backup
tar czf nps_v3_backup_$(date +%Y%m%d).tar.gz nps/data/ nps/config.json
```

V3 data locations:

- `nps/data/findings/` — JSONL files with encrypted findings
- `nps/data/sessions/` — JSON session files
- `nps/data/checkpoints/` — JSON checkpoint state
- `nps/data/learning/` — JSON learning data
- `nps/config.json` — Runtime configuration

### 2. Start V4 Infrastructure

```bash
cd v4
docker-compose up -d postgres
```

Wait for PostgreSQL to initialize (check with `docker-compose logs postgres`).

### 3. Run Migration Script

The migration script reads V3 data, re-encrypts sensitive fields with V4 encryption, and inserts into PostgreSQL:

```bash
cd v4
python database/migrations/v3_to_v4.py \
  --v3-data-dir ../nps/data \
  --v3-config ../nps/config.json \
  --v3-password <your-v3-encryption-password>
```

The script handles:

| V3 Source            | V4 Destination                       | Notes                                       |
| -------------------- | ------------------------------------ | ------------------------------------------- |
| `findings/*.jsonl`   | `findings` table                     | Re-encrypts `ENC:` -> `ENC4:` (AES-256-GCM) |
| `sessions/*.json`    | `scan_sessions` table                | Preserves session history                   |
| `checkpoints/*.json` | `scan_checkpoints` table             | Checkpoints remain resumable                |
| `learning/*.json`    | `learning_data` + `learning_history` | XP/level preserved                          |
| `config.json`        | `.env` + `config` table              | API keys -> env vars                        |

### 4. Configure Environment

Create your `.env` file from the example:

```bash
cp .env.example .env
```

Key variables to set:

```env
# From V3 config.json
TELEGRAM_BOT_TOKEN=<from config.json telegram.bot_token>
ETHERSCAN_API_KEY=<from config.json chains.eth.api_key>
BSCSCAN_API_KEY=<from config.json chains.bsc.api_key>

# New for V4
DATABASE_URL=postgresql://nps:password@localhost:5432/nps
JWT_SECRET=<generate with: openssl rand -hex 32>
ENCRYPTION_KEY=<generate with: openssl rand -hex 32>
```

### 5. Verify Migration

```bash
# Check finding count matches
psql $DATABASE_URL -c "SELECT COUNT(*) FROM findings;"
# Compare with: wc -l nps/data/findings/*.jsonl

# Check sessions migrated
psql $DATABASE_URL -c "SELECT COUNT(*) FROM scan_sessions;"

# Check learning data
psql $DATABASE_URL -c "SELECT level, xp FROM learning_data ORDER BY updated_at DESC LIMIT 1;"

# Verify encryption (should show ENC4: prefix)
psql $DATABASE_URL -c "SELECT LEFT(private_key_enc, 10) FROM findings LIMIT 3;"
```

### 6. Start V4

```bash
cd v4
docker-compose up -d
```

Access the web UI at `http://localhost` (or your configured domain).

### 7. Verify Functionality

- [ ] Dashboard loads with session history
- [ ] Scanner starts and connects to Rust service
- [ ] Oracle readings match V3 output for same inputs
- [ ] Vault shows migrated findings
- [ ] Learning shows correct XP/level
- [ ] Telegram bot responds (if configured)

## Encryption Changes

| Feature        | V3                   | V4                                      |
| -------------- | -------------------- | --------------------------------------- |
| Algorithm      | PBKDF2 + HMAC-SHA256 | AES-256-GCM                             |
| Prefix         | `ENC:`               | `ENC4:`                                 |
| Key derivation | Password-based       | Environment variable                    |
| Legacy support | N/A                  | Reads V3 `ENC:` format (migration only) |

## Rollback

If migration fails, your V3 installation is untouched:

```bash
# V3 still works as before
cd nps && python3 main.py

# Or restore from backup
tar xzf nps_v3_backup_*.tar.gz
```

## Troubleshooting

**"ENC: decryption failed"** — Wrong V3 password. Check `nps/config.json` for the encryption settings.

**"Database connection refused"** — PostgreSQL container not running. Run `docker-compose up -d postgres` and wait for initialization.

**"Missing findings"** — Check if JSONL files have trailing newlines. The migration script skips empty lines.

**"Scoring mismatch between V3 and V4"** — Run the scoring test vectors: `cd v4 && make test-scoring-vectors`. Both Python and Rust must produce identical results.
