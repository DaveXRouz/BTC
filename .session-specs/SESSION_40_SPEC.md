# SESSION 40 SPEC — Backup, Restore & Infrastructure Polish

**Block:** Admin & DevOps (Sessions 38-40)
**Estimated Duration:** 5-6 hours
**Complexity:** Medium-High
**Dependencies:** Session 39 (monitoring dashboard, admin API patterns), Session 38 (admin UI, routing, auth)

---

## TL;DR

- Enhance the existing `database/scripts/oracle_backup.sh` and `oracle_restore.sh` with scheduled cron support, age-based retention, Telegram notifications, and non-interactive mode for API-triggered invocation
- Enhance `scripts/backup.sh` and `scripts/restore.sh` with the same improvements (full-database variants)
- Create a `BackupManager.tsx` admin UI component at `/admin/backups` for triggering manual backups, browsing backup history, restoring from selected backups, and viewing backup schedules
- Create backup/restore API endpoints in `api/app/routers/admin.py` (extend the existing Session 38/39 admin router)
- Create `scripts/validate_env.py` that checks all required environment variables, tests database/Redis/service connectivity, and reports pass/fail
- Polish `docker-compose.yml` with verified health checks, restart policies, resource limits, and a new `backup` service for automated daily/weekly backups via cron
- This is the final session of the Admin & DevOps block; handoff to Session 41 (Testing & Deployment block)

---

## OBJECTIVES

1. **Automated backup scheduling** -- Add a lightweight Docker container running cron jobs for daily Oracle-table backups (midnight) and weekly full-database backups (Sunday 3 AM)
2. **Manual backup via admin UI** -- Admin users can trigger an immediate Oracle or full-database backup from the `/admin/backups` page
3. **Restore via admin UI** -- Admin users can browse available backups, see metadata (size, date, type), and restore from a selected backup with a two-step confirmation flow
4. **Backup retention** -- Auto-delete Oracle backups older than 30 days and full-database backups older than 60 days; display retention policy in UI
5. **Backup shell script improvements** -- Add `--non-interactive` flag to restore scripts (skip confirmation prompt when triggered from API), add exit codes, add Telegram notification on backup success/failure
6. **Docker Compose polish** -- Verify every service has correct health checks, restart policies, resource limits, dependency ordering, and volume mounts
7. **Environment validation** -- Create a script that checks every required `.env` variable exists and is non-empty, tests database connectivity, tests Redis connectivity, validates encryption key format, and prints a pass/fail report
8. **Admin API endpoints** -- Add `GET /api/admin/backups` (list), `POST /api/admin/backups` (trigger), `POST /api/admin/backups/restore` (restore), `DELETE /api/admin/backups/{filename}` (delete)
9. **Access control** -- All backup/restore operations restricted to `admin` scope

---

## PREREQUISITES

- [ ] Session 38 complete -- `api/app/routers/admin.py` exists with admin user management endpoints
- [ ] Session 39 complete -- `api/app/routers/admin.py` extended with analytics/logs/errors endpoints; `frontend/src/pages/AdminMonitoring.tsx` exists
- [ ] Admin routing at `/admin/*` registered in `App.tsx` with `AdminGuard`
- [ ] Auth middleware `require_scope("admin")` functional at `api/app/middleware/auth.py`
- [ ] Existing backup scripts at `database/scripts/oracle_backup.sh` (86 lines) and `database/scripts/oracle_restore.sh` (81 lines)
- [ ] Existing full-database scripts at `scripts/backup.sh` (42 lines) and `scripts/restore.sh` (54 lines)
- [ ] Docker Compose at project root with 8 services (frontend, api, oracle-service, scanner-service, postgres, redis, oracle-alerter, nginx)
- [ ] `.env.example` documenting all environment variables (67 lines)

**Verification:**

```bash
# Session 38/39 admin router exists
test -f api/app/routers/admin.py && echo "OK: admin router"

# Admin auth middleware
grep -n "require_scope" api/app/middleware/auth.py

# Existing backup scripts
test -f database/scripts/oracle_backup.sh && echo "OK: oracle backup"
test -f database/scripts/oracle_restore.sh && echo "OK: oracle restore"
test -f scripts/backup.sh && echo "OK: full backup"
test -f scripts/restore.sh && echo "OK: full restore"

# Docker Compose
test -f docker-compose.yml && echo "OK: docker-compose"

# .env.example
test -f .env.example && echo "OK: .env.example"
```

---

## EXISTING CODE ANALYSIS

### What EXISTS (modify, do NOT rebuild):

| Component             | File                                 | Current State                                                                                                         |
| --------------------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| Full DB backup        | `scripts/backup.sh`                  | 42 lines. `pg_dump` via Docker, gzip, retains last 30. No scheduling, no non-interactive mode.                        |
| Full DB restore       | `scripts/restore.sh`                 | 54 lines. Interactive `read -p` confirmation, drops & recreates DB. Cannot be called from API (requires tty).         |
| Oracle tables backup  | `database/scripts/oracle_backup.sh`  | 86 lines. Backs up 4 Oracle tables, supports `--data-only`, retains last 30 per type. No metadata file.               |
| Oracle tables restore | `database/scripts/oracle_restore.sh` | 81 lines. Truncates Oracle tables, restores from gzip. Interactive confirmation. Post-restore row count verification. |
| Health check          | `scripts/health-check.sh`            | 69 lines. Checks 7 Docker services, reports PASS/FAIL/WAIT.                                                           |
| Deploy script         | `scripts/deploy.sh`                  | 46 lines. Builds images, starts services, basic health wait.                                                          |
| Docker Compose        | `docker-compose.yml`                 | 224 lines, 8 services. All have health checks and restart policies. Missing: backup service, backup volume on API.    |
| Health router         | `api/app/routers/health.py`          | 71 lines. `/api/health`, `/api/health/ready`, `/api/health/performance` (TODO stub).                                  |
| Admin router          | `api/app/routers/admin.py`           | Created in Session 38, extended in Session 39. Has user management + monitoring endpoints.                            |
| .env.example          | `.env.example`                       | 67 lines. All core env vars documented. No backup-specific vars.                                                      |

### What does NOT exist (must create):

| Component                                         | Why Needed                                    |
| ------------------------------------------------- | --------------------------------------------- |
| `frontend/src/components/admin/BackupManager.tsx` | Admin UI for backup listing, trigger, restore |
| `scripts/validate_env.py`                         | Environment validation script                 |
| `scripts/backup_cron.sh`                          | Cron wrapper for scheduled backups            |
| `scripts/Dockerfile.backup`                       | Docker image for backup cron container        |
| `scripts/crontab`                                 | Cron schedule definition                      |
| `api/app/models/backup.py`                        | Pydantic models for backup API                |

---

## FILES TO CREATE

| File                                                             | Purpose                                                  | Est. Lines |
| ---------------------------------------------------------------- | -------------------------------------------------------- | ---------- |
| `frontend/src/components/admin/BackupManager.tsx`                | Admin UI for backup/restore operations                   | ~350       |
| `frontend/src/components/admin/__tests__/BackupManager.test.tsx` | Tests for BackupManager component                        | ~200       |
| `scripts/validate_env.py`                                        | Environment validation script                            | ~250       |
| `scripts/backup_cron.sh`                                         | Cron wrapper that runs daily/weekly backups with logging | ~80        |
| `scripts/Dockerfile.backup`                                      | Dockerfile for the backup cron container                 | ~30        |
| `scripts/crontab`                                                | Cron schedule definition                                 | ~10        |
| `api/app/models/backup.py`                                       | Pydantic models for backup API endpoints                 | ~60        |
| `api/app/routers/__tests__/test_backup.py`                       | API tests for backup endpoints                           | ~200       |

## FILES TO MODIFY

| File                                 | Current State               | Action | Notes                                                                        |
| ------------------------------------ | --------------------------- | ------ | ---------------------------------------------------------------------------- |
| `database/scripts/oracle_backup.sh`  | 86 lines                    | MODIFY | Add `--non-interactive`, Telegram notify, metadata JSON, age-based retention |
| `database/scripts/oracle_restore.sh` | 81 lines                    | MODIFY | Add `--non-interactive` flag, API-friendly exit codes                        |
| `scripts/backup.sh`                  | 42 lines                    | MODIFY | Add `--non-interactive`, Telegram notify, metadata JSON, age-based retention |
| `scripts/restore.sh`                 | 54 lines                    | MODIFY | Add `--non-interactive` flag                                                 |
| `api/app/routers/admin.py`           | ~220+ lines (after S38/S39) | MODIFY | Add backup/restore endpoints                                                 |
| `docker-compose.yml`                 | 224 lines                   | MODIFY | Add `backup` service, polish health checks, add backup volume to API         |
| `frontend/src/App.tsx`               | ~40 lines (after S38/S39)   | MODIFY | Add `/admin/backups` route                                                   |
| `frontend/src/services/api.ts`       | Modified in S39             | MODIFY | Add backup API client methods                                                |
| `frontend/src/types/index.ts`        | Modified in S39             | MODIFY | Add backup TypeScript types                                                  |
| `frontend/src/hooks/useAdminData.ts` | Created in S39              | MODIFY | Add backup React Query hooks                                                 |
| `frontend/src/locales/en.json`       | Modified in S39             | MODIFY | Add backup i18n keys                                                         |
| `frontend/src/locales/fa.json`       | Modified in S39             | MODIFY | Add backup i18n keys (Persian)                                               |

## FILES TO DELETE

None.

---

## IMPLEMENTATION PHASES

### Phase 1: Shell Script Enhancements (~45 min)

**Improve all 4 backup/restore scripts with consistent flags, exit codes, and notifications.**

#### 1.1 Modify `database/scripts/oracle_backup.sh`

Add the following capabilities to the existing script:

**New flags:**

- `--non-interactive` -- Skip any prompts (for API/cron invocation)
- `--notify` -- Send Telegram notification on completion or failure

**New features:**

- JSON metadata file alongside each backup: `oracle_full_TIMESTAMP.meta.json` containing `{"filename": "...", "type": "full|data-only", "timestamp": "ISO8601", "size_bytes": N, "tables": [...], "database": "nps"}`
- Exit code 0 on success, 1 on failure
- Retention cleanup: delete backups older than 30 days (replace the current "keep last 30" logic with age-based cleanup)
- Optional Telegram notification via `NPS_BOT_TOKEN` and `NPS_CHAT_ID` environment variables

**Code pattern for Telegram notification (add as function):**

```bash
notify_telegram() {
    local message="$1"
    if [ -n "${NPS_BOT_TOKEN:-}" ] && [ -n "${NPS_CHAT_ID:-}" ]; then
        curl -s -X POST "https://api.telegram.org/bot${NPS_BOT_TOKEN}/sendMessage" \
            -d "chat_id=${NPS_CHAT_ID}" \
            -d "text=${message}" \
            -d "parse_mode=Markdown" > /dev/null 2>&1 || true
    fi
}
```

**Retention cleanup (replace existing logic):**

```bash
# Delete backups older than 30 days
find "$BACKUP_DIR" -name "oracle_*.sql.gz" -mtime +30 -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "oracle_*.meta.json" -mtime +30 -delete 2>/dev/null || true
echo "Retention: deleted backups older than 30 days"
```

**Metadata file creation (add after successful backup):**

```bash
# Write metadata
cat > "${BACKUP_FILE%.sql.gz}.meta.json" <<METAEOF
{
    "filename": "$(basename "$BACKUP_FILE")",
    "type": "$BACKUP_TYPE",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "size_bytes": $(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat --format=%s "$BACKUP_FILE" 2>/dev/null || echo 0),
    "tables": $(printf '%s\n' "${ORACLE_TABLES[@]}" | jq -R . | jq -s .),
    "database": "$POSTGRES_DB"
}
METAEOF
```

#### 1.2 Modify `database/scripts/oracle_restore.sh`

**New flags:**

- `--non-interactive` -- Skip the `read -p "Continue? [y/N]"` confirmation prompt
- `--notify` -- Send Telegram notification on completion

**Changes:**

- Parse `--non-interactive` flag before the backup file argument
- When `--non-interactive` is set, skip the `read -p` prompt and proceed directly
- Add JSON output on success: `{"status": "success", "backup": "filename", "rows": {"oracle_users": N, ...}}`
- Exit code 0 on success, 1 on failure

**Code pattern:**

```bash
NON_INTERACTIVE=false
NOTIFY=false
POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --non-interactive) NON_INTERACTIVE=true; shift ;;
        --notify) NOTIFY=true; shift ;;
        *) POSITIONAL_ARGS+=("$1"); shift ;;
    esac
done

BACKUP_FILE="${POSITIONAL_ARGS[0]:-}"

# ... later, replace the confirmation prompt:
if ! $NON_INTERACTIVE; then
    read -p "Continue? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
fi
```

#### 1.3 Modify `scripts/backup.sh`

Same improvements as oracle_backup.sh:

- `--non-interactive` flag
- `--notify` flag for Telegram
- JSON metadata file (`nps_backup_TIMESTAMP.meta.json`)
- Age-based retention: delete full backups older than 60 days
- Exit codes

#### 1.4 Modify `scripts/restore.sh`

Same improvements as oracle_restore.sh:

- `--non-interactive` flag
- `--notify` flag
- JSON output on success
- Exit codes

**STOP checkpoint:** All 4 scripts accept `--non-interactive` and `--notify` flags. Running `oracle_backup.sh --non-interactive` produces a backup file plus a `.meta.json` file. Running `oracle_restore.sh --non-interactive <file>` restores without prompting. Exit codes are correct.

```bash
# Test non-interactive backup
./database/scripts/oracle_backup.sh --non-interactive
echo "Exit code: $?"
ls -la backups/oracle/*.meta.json | tail -1

# Test non-interactive restore (dry run -- just verify flag parsing)
./database/scripts/oracle_restore.sh --help 2>&1 || true
```

---

### Phase 2: Backup Cron Container (~30 min)

**Create a lightweight Docker container that runs daily and weekly backup schedules.**

#### 2.1 Create `scripts/crontab`

```
# NPS Automated Backup Schedule
# Daily: Oracle tables at midnight UTC
0 0 * * * /app/scripts/backup_cron.sh daily >> /var/log/cron.log 2>&1

# Weekly: Full database on Sunday at 3 AM UTC
0 3 * * 0 /app/scripts/backup_cron.sh weekly >> /var/log/cron.log 2>&1
```

#### 2.2 Create `scripts/backup_cron.sh`

```bash
#!/bin/bash
# NPS Backup Cron Wrapper
# Usage: backup_cron.sh daily|weekly
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V4_DIR="$(dirname "$SCRIPT_DIR")"
MODE="${1:-daily}"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

echo "[$TIMESTAMP] Starting $MODE backup..."

case "$MODE" in
    daily)
        # Oracle tables backup
        "$V4_DIR/database/scripts/oracle_backup.sh" --non-interactive --notify
        EXIT_CODE=$?
        ;;
    weekly)
        # Full database backup
        "$V4_DIR/scripts/backup.sh" --non-interactive --notify
        EXIT_CODE=$?
        ;;
    *)
        echo "Unknown mode: $MODE (expected: daily|weekly)"
        exit 1
        ;;
esac

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$TIMESTAMP] $MODE backup completed successfully"
else
    echo "[$TIMESTAMP] $MODE backup FAILED with exit code $EXIT_CODE"
fi

exit $EXIT_CODE
```

#### 2.3 Create `scripts/Dockerfile.backup`

```dockerfile
FROM postgres:15-alpine

# Install cron and curl (for Telegram notifications) and jq (for metadata)
RUN apk add --no-cache bash curl jq

# Copy all scripts
COPY scripts/backup_cron.sh /app/scripts/backup_cron.sh
COPY scripts/backup.sh /app/scripts/backup.sh
COPY scripts/restore.sh /app/scripts/restore.sh
COPY scripts/crontab /etc/crontabs/root
COPY database/scripts/oracle_backup.sh /app/database/scripts/oracle_backup.sh
COPY database/scripts/oracle_restore.sh /app/database/scripts/oracle_restore.sh

# Make scripts executable
RUN chmod +x /app/scripts/*.sh /app/database/scripts/*.sh

# Create backup and log directories
RUN mkdir -p /app/backups/oracle /var/log

# Start cron in foreground
CMD ["crond", "-f", "-d", "8"]
```

**Note:** The build context for this Dockerfile is the project root directory. All COPY paths are relative to the project root.

**STOP checkpoint:** Backup Dockerfile builds. Cron schedule is correct. `backup_cron.sh daily` invokes `oracle_backup.sh --non-interactive --notify`. `backup_cron.sh weekly` invokes full `backup.sh --non-interactive --notify`.

```bash
# Verify Dockerfile builds (dry run)
docker build -f scripts/Dockerfile.backup -t nps-backup-test .

# Verify crontab syntax
cat scripts/crontab
```

---

### Phase 3: Docker Compose Polish (~30 min)

**Add the backup service and verify/polish all existing services.**

#### 3.1 Add `backup` service to `docker-compose.yml`

```yaml
# --- Backup Scheduler ---
backup:
  build:
    context: .
    dockerfile: scripts/Dockerfile.backup
  container_name: nps-backup
  env_file: .env
  depends_on:
    postgres:
      condition: service_healthy
  volumes:
    - ./backups:/app/backups
    - ./database/scripts:/app/database/scripts:ro
    - ./scripts:/app/scripts:ro
  restart: unless-stopped
  deploy:
    resources:
      limits:
        cpus: "0.25"
        memory: 256M
```

Also add the `backups` bind mount to the `api` service (for listing and triggering backups):

```yaml
api:
  # ... existing config ...
  volumes:
    - ./backups:/app/backups
```

#### 3.2 Verify and polish all existing services

Review each service in `docker-compose.yml` and ensure consistency:

**All services must have:**

- `restart: unless-stopped` (already present on all -- verified)
- `deploy.resources.limits` for CPU and memory (already present on all -- verified)
- `healthcheck` with appropriate test, interval, timeout, start_period, retries (already present on all except oracle-alerter)
- Correct `depends_on` with `condition: service_healthy` (already present)

**Specific polishes to apply:**

1. **postgres** -- Add `shm_size: 256mb` for better performance with larger datasets:

```yaml
postgres:
  # ... existing config ...
  shm_size: 256mb
```

2. **redis** -- Add `command` with recommended production settings:

```yaml
redis:
  # ... existing config ...
  command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
```

3. **nginx** -- Tighten healthcheck to test the reverse proxy path:

```yaml
nginx:
  # ... existing config ...
  healthcheck:
    test: ["CMD", "wget", "-q", "--spider", "http://localhost:80/api/health"]
    interval: 30s
    timeout: 5s
    start_period: 15s
    retries: 3
```

4. **oracle-alerter** -- Add a healthcheck (currently has none):

```yaml
oracle-alerter:
  # ... existing config ...
  healthcheck:
    test: ["CMD-SHELL", "pgrep -f oracle_alerts || exit 1"]
    interval: 60s
    timeout: 5s
    start_period: 10s
    retries: 3
```

5. **Add logging driver** to all services for consistent log management:

```yaml
logging:
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"
```

6. **Verify `backups/` is in `.gitignore`** -- Add if missing.

**STOP checkpoint:** `docker-compose config` validates without errors. All services have health checks. Backup service is defined. Resource limits are set on all services.

```bash
docker compose config --quiet && echo "OK: compose valid" || echo "FAIL: compose invalid"
docker compose config --services | sort
# Expected: api, backup, frontend, nginx, oracle-alerter, oracle-service, postgres, redis, scanner-service
```

---

### Phase 4: Backup API Endpoints (~60 min)

**Add backup/restore endpoints to the admin API router.**

#### 4.1 Create `api/app/models/backup.py`

Pydantic models for backup API requests and responses:

```python
"""Backup and restore Pydantic models."""
from datetime import datetime
from pydantic import BaseModel, Field


class BackupInfo(BaseModel):
    """Information about a single backup file."""
    filename: str
    type: str  # "oracle_full" | "oracle_data" | "full_database"
    timestamp: datetime
    size_bytes: int
    size_human: str  # "12.5 MB"
    tables: list[str] = []
    database: str = "nps"


class BackupListResponse(BaseModel):
    """Response for listing available backups."""
    backups: list[BackupInfo]
    total: int
    retention_policy: str  # "Oracle: 30 days, Full: 60 days"
    backup_directory: str


class BackupTriggerRequest(BaseModel):
    """Request to trigger a manual backup."""
    backup_type: str = Field(
        ...,
        pattern="^(oracle_full|oracle_data|full_database)$",
        description="Type of backup to create"
    )


class BackupTriggerResponse(BaseModel):
    """Response after triggering a backup."""
    status: str  # "success" | "failed"
    message: str
    backup: BackupInfo | None = None


class RestoreRequest(BaseModel):
    """Request to restore from a backup."""
    filename: str = Field(..., min_length=1)
    confirm: bool = Field(
        ...,
        description="Must be True to confirm restore"
    )


class RestoreResponse(BaseModel):
    """Response after a restore operation."""
    status: str  # "success" | "failed"
    message: str
    rows_restored: dict[str, int] = {}


class BackupDeleteResponse(BaseModel):
    """Response after deleting a backup."""
    status: str
    message: str
    filename: str
```

#### 4.2 Extend `api/app/routers/admin.py` with backup endpoints

Add the following endpoints to the existing admin router:

**`GET /admin/backups`** -- List all available backups

```python
@router.get(
    "/backups",
    response_model=BackupListResponse,
    dependencies=[Depends(require_scope("admin"))],
)
async def list_backups():
    """List available backup files with metadata."""
    # Scan backups/oracle/ and backups/ for .sql.gz files
    # For each file, try to read .meta.json sidecar; fallback to stat() for size/date
    # Return sorted by timestamp descending (newest first)
    # Include retention policy string
```

Implementation details:

- Backup directories: `backups/oracle/` for Oracle backups, `backups/` for full-database backups
- For each `.sql.gz` file, check for a `.meta.json` sidecar file
- If `.meta.json` exists, parse it for structured metadata
- If `.meta.json` does not exist, derive metadata from filename (timestamp from `_YYYYMMDD_HHMMSS.sql.gz` pattern) and `os.stat()` for size
- Classify type based on filename prefix: `oracle_full_*` = oracle*full, `oracle_data*_`= oracle_data,`nps*backup*_` = full_database
- Return human-readable size (e.g., "12.5 MB")
- Use `Path(__file__).resolve().parents[3]` to find the project root

**`POST /admin/backups`** -- Trigger a manual backup

```python
@router.post(
    "/backups",
    response_model=BackupTriggerResponse,
    dependencies=[Depends(require_scope("admin"))],
)
async def trigger_backup(body: BackupTriggerRequest):
    """Trigger an immediate backup."""
    # Map backup_type to the correct script:
    #   oracle_full -> database/scripts/oracle_backup.sh --non-interactive
    #   oracle_data -> database/scripts/oracle_backup.sh --data-only --non-interactive
    #   full_database -> scripts/backup.sh --non-interactive
    # Run via subprocess.run() with timeout of 120 seconds
    # Capture stdout/stderr
    # Parse the output to find the backup filename
    # Read the .meta.json if created
    # Return success/failure with backup info
```

Implementation details:

- Use `subprocess.run()` with `capture_output=True`, `text=True`, `timeout=120`
- Project root: `Path(__file__).resolve().parents[3]`
- On success (returncode 0), scan for the newest backup file to return its info
- On failure (returncode != 0), return the stderr as the error message
- On timeout (`subprocess.TimeoutExpired`), return a timeout error message
- Log the operation to `oracle_audit_log` table

**`POST /admin/backups/restore`** -- Restore from a backup

```python
@router.post(
    "/backups/restore",
    response_model=RestoreResponse,
    dependencies=[Depends(require_scope("admin"))],
)
async def restore_backup(body: RestoreRequest):
    """Restore database from a backup file."""
    # Validate: body.confirm must be True
    # Validate: filename exists in backup directories
    # Determine script: oracle_* files use oracle_restore.sh, nps_backup_* files use restore.sh
    # Run via subprocess.run() with --non-interactive flag and timeout of 300 seconds
    # Parse stdout for row counts
    # Log to oracle_audit_log
    # Return success/failure with row counts
```

Implementation details:

- Reject if `body.confirm is not True` with 400 error
- Validate that the filename exists and is in the expected backup directory (prevent path traversal: `os.path.basename(filename) == filename`)
- Determine full path: check `backups/oracle/` first, then `backups/`
- For Oracle restores: parse the verification output to extract row counts
- For full-database restores: return generic success message
- This is a destructive operation -- log it prominently

**`DELETE /admin/backups/{filename}`** -- Delete a backup file

```python
@router.delete(
    "/backups/{filename}",
    response_model=BackupDeleteResponse,
    dependencies=[Depends(require_scope("admin"))],
)
async def delete_backup(filename: str):
    """Delete a specific backup file."""
    # Validate: filename is a safe basename (no path traversal)
    # Find the file in backups/oracle/ or backups/
    # Delete the .sql.gz file and its .meta.json sidecar if present
    # Log to oracle_audit_log
    # Return success
```

Implementation details:

- Security: `os.path.basename(filename) == filename` and filename ends with `.sql.gz`
- Delete both the backup file and its metadata sidecar
- Return 404 if file not found

#### 4.3 Audit logging for backup operations

All backup/restore/delete operations must be logged to the `oracle_audit_log` table:

```python
def log_backup_audit(
    db: Session,
    action: str,       # "backup_trigger", "backup_restore", "backup_delete"
    user_id: str,
    details: str,
    success: bool,
):
    """Log backup operation to audit trail."""
    db.execute(
        text("""
            INSERT INTO oracle_audit_log (action, user_id, details, success, created_at)
            VALUES (:action, :user_id, :details, :success, NOW())
        """),
        {"action": action, "user_id": user_id, "details": details, "success": success}
    )
    db.commit()
```

**Note:** Verify the exact `oracle_audit_log` table schema against `database/init.sql` during implementation and adapt column names if needed.

**STOP checkpoint:** All 4 backup API endpoints respond with correct JSON. `GET /api/admin/backups` returns a list of existing backups. `POST /api/admin/backups` triggers a backup and returns its info. `POST /api/admin/backups/restore` restores and returns row counts. `DELETE /api/admin/backups/{filename}` removes a backup. All endpoints return 403 for non-admin users.

```bash
# Verify endpoints (with admin token)
curl -H "Authorization: Bearer <admin_token>" http://localhost:8000/api/admin/backups | python3 -m json.tool
curl -X POST -H "Authorization: Bearer <admin_token>" -H "Content-Type: application/json" \
    -d '{"backup_type": "oracle_full"}' http://localhost:8000/api/admin/backups | python3 -m json.tool

# Verify non-admin gets 403
curl -H "Authorization: Bearer <user_token>" http://localhost:8000/api/admin/backups
# Expected: 403
```

---

### Phase 5: TypeScript Types + API Client + Hooks (~30 min)

**Add frontend type definitions and data fetching for backup operations.**

#### 5.1 Add backup types to `frontend/src/types/index.ts`

```tsx
// --- Backups ---

export interface BackupInfo {
  filename: string;
  type: "oracle_full" | "oracle_data" | "full_database";
  timestamp: string;
  size_bytes: number;
  size_human: string;
  tables: string[];
  database: string;
}

export interface BackupListResponse {
  backups: BackupInfo[];
  total: number;
  retention_policy: string;
  backup_directory: string;
}

export interface BackupTriggerResponse {
  status: "success" | "failed";
  message: string;
  backup: BackupInfo | null;
}

export interface RestoreResponse {
  status: "success" | "failed";
  message: string;
  rows_restored: Record<string, number>;
}

export interface BackupDeleteResponse {
  status: string;
  message: string;
  filename: string;
}
```

#### 5.2 Add backup API client to `frontend/src/services/api.ts`

Add to the existing `admin` namespace (created in Session 39):

```tsx
// Inside the admin object:
backups: () => request<BackupListResponse>("/admin/backups"),
triggerBackup: (backupType: string) =>
  request<BackupTriggerResponse>("/admin/backups", {
    method: "POST",
    body: JSON.stringify({ backup_type: backupType }),
  }),
restoreBackup: (filename: string) =>
  request<RestoreResponse>("/admin/backups/restore", {
    method: "POST",
    body: JSON.stringify({ filename, confirm: true }),
  }),
deleteBackup: (filename: string) =>
  request<BackupDeleteResponse>(`/admin/backups/${filename}`, {
    method: "DELETE",
  }),
```

#### 5.3 Add backup hooks to `frontend/src/hooks/useAdminData.ts`

```tsx
export function useBackups(): UseQueryResult<BackupListResponse> {
  return useQuery({
    queryKey: ["admin", "backups"],
    queryFn: () => api.admin.backups(),
    staleTime: 30_000, // 30 seconds
  });
}

export function useTriggerBackup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (backupType: string) => api.admin.triggerBackup(backupType),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["admin", "backups"] }),
  });
}

export function useRestoreBackup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (filename: string) => api.admin.restoreBackup(filename),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["admin", "backups"] }),
  });
}

export function useDeleteBackup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (filename: string) => api.admin.deleteBackup(filename),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["admin", "backups"] }),
  });
}
```

#### 5.4 Add i18n keys to locale files

**`frontend/src/locales/en.json`** -- add to the existing `admin` object:

```json
"backups": "Backups",
"backup_manager": "Backup Manager",
"trigger_backup": "Create Backup",
"restore_backup": "Restore",
"delete_backup": "Delete",
"backup_type": "Backup Type",
"backup_type_oracle_full": "Oracle (Full)",
"backup_type_oracle_data": "Oracle (Data Only)",
"backup_type_full_database": "Full Database",
"backup_size": "Size",
"backup_date": "Date",
"backup_tables": "Tables",
"backup_retention": "Retention Policy",
"backup_schedule": "Schedule",
"backup_schedule_daily": "Daily at midnight UTC (Oracle tables)",
"backup_schedule_weekly": "Weekly on Sunday at 3 AM UTC (Full database)",
"backup_confirm_restore": "Are you sure you want to restore from this backup? This will overwrite current data.",
"backup_confirm_restore_title": "Confirm Restore",
"backup_confirm_restore_type": "Type RESTORE to confirm",
"backup_confirm_delete": "Delete this backup? This cannot be undone.",
"backup_in_progress": "Backup in progress...",
"backup_success": "Backup created successfully",
"backup_failed": "Backup failed",
"restore_in_progress": "Restore in progress...",
"restore_success": "Restore completed successfully",
"restore_failed": "Restore failed",
"no_backups": "No backups available",
"rows_restored": "Rows restored"
```

**`frontend/src/locales/fa.json`** -- add Persian translations:

```json
"backups": "پشتیبان‌گیری",
"backup_manager": "مدیریت پشتیبان",
"trigger_backup": "ایجاد پشتیبان",
"restore_backup": "بازگردانی",
"delete_backup": "حذف",
"backup_type": "نوع پشتیبان",
"backup_type_oracle_full": "اوراکل (کامل)",
"backup_type_oracle_data": "اوراکل (فقط داده)",
"backup_type_full_database": "پایگاه داده کامل",
"backup_size": "حجم",
"backup_date": "تاریخ",
"backup_tables": "جداول",
"backup_retention": "سیاست نگهداری",
"backup_schedule": "زمان‌بندی",
"backup_schedule_daily": "روزانه در نیمه‌شب UTC (جداول اوراکل)",
"backup_schedule_weekly": "هفتگی یکشنبه ساعت ۳ صبح UTC (پایگاه داده کامل)",
"backup_confirm_restore": "آیا مطمئن هستید که می‌خواهید از این پشتیبان بازگردانی کنید؟ داده‌های فعلی بازنویسی خواهند شد.",
"backup_confirm_restore_title": "تایید بازگردانی",
"backup_confirm_restore_type": "برای تایید RESTORE را تایپ کنید",
"backup_confirm_delete": "این پشتیبان حذف شود؟ این عمل قابل بازگشت نیست.",
"backup_in_progress": "پشتیبان‌گیری در حال انجام...",
"backup_success": "پشتیبان با موفقیت ایجاد شد",
"backup_failed": "پشتیبان‌گیری ناموفق بود",
"restore_in_progress": "بازگردانی در حال انجام...",
"restore_success": "بازگردانی با موفقیت انجام شد",
"restore_failed": "بازگردانی ناموفق بود",
"no_backups": "پشتیبانی موجود نیست",
"rows_restored": "ردیف‌های بازگردانی شده"
```

**STOP checkpoint:** Types compile. API client functions match endpoint signatures. Hooks return correct query states. i18n keys match between EN and FA.

```bash
cd frontend && npx tsc --noEmit
```

---

### Phase 6: BackupManager Component (~60 min)

**Build the admin backup management UI.**

#### 6.1 Create `frontend/src/components/admin/BackupManager.tsx`

**Layout:**

```
+------------------------------------------------------------------+
|  Backup Manager                              [Create Backup v]   |
+------------------------------------------------------------------+
|                                                                  |
|  Schedule:                                                       |
|  - Daily at midnight UTC: Oracle tables                          |
|  - Weekly Sunday 3 AM UTC: Full database                        |
|  Retention: Oracle 30 days, Full database 60 days               |
|                                                                  |
+------------------------------------------------------------------+
|                                                                  |
|  Available Backups (12)                                          |
|  +------------------------------------------------------------+ |
|  | Filename              | Type        | Date       | Size    | |
|  |-------------------------------------------------------     | |
|  | oracle_full_2026...   | Oracle Full | Feb 10     | 2.3 MB  | |
|  |                            [Restore] [Delete]              | |
|  | nps_backup_2026...    | Full DB     | Feb 9      | 45 MB   | |
|  |                            [Restore] [Delete]              | |
|  | oracle_full_2026...   | Oracle Full | Feb 9      | 2.1 MB  | |
|  |                            [Restore] [Delete]              | |
|  +------------------------------------------------------------+ |
|                                                                  |
+------------------------------------------------------------------+
```

**Component structure:**

```tsx
export function BackupManager() {
  const { t } = useTranslation();
  const { data: backupList, isLoading, error } = useBackups();
  const triggerBackup = useTriggerBackup();
  const restoreBackup = useRestoreBackup();
  const deleteBackup = useDeleteBackup();

  const [showCreateMenu, setShowCreateMenu] = useState(false);
  const [restoreTarget, setRestoreTarget] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [restoreConfirmText, setRestoreConfirmText] = useState("");
  const [statusMessage, setStatusMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  return (
    <div className="space-y-6">
      {/* Header with Create Backup dropdown button */}
      {/* Status message banner (auto-dismisses after 5s) */}
      {/* Schedule info card */}
      {/* Backup list table */}
      {/* Restore confirmation modal (two-step with type-to-confirm) */}
      {/* Delete confirmation modal */}
    </div>
  );
}
```

**Key UX details:**

1. **Create Backup dropdown:** Button with dropdown menu showing 3 options: Oracle Full, Oracle Data Only, Full Database. Clicking an option triggers the backup immediately. Show a loading spinner while the backup runs (can take 10-60 seconds). Disable the button during backup.

2. **Backup table:** Each row shows:
   - Filename (truncated with tooltip for full name)
   - Type badge (color-coded: blue for Oracle, purple for Full DB)
   - Formatted date (relative time like "2 hours ago" + absolute in tooltip)
   - Human-readable size
   - Actions column: Restore and Delete buttons

3. **Restore flow (two-step confirmation):**
   - Step 1: Click "Restore" button on a backup row
   - Step 2: Modal appears with warning message: "This will overwrite current data. Are you sure?"
   - Step 3: User must type the word "RESTORE" in an input field to enable the Confirm button
   - Step 4: Click "Confirm" to execute
   - This extra friction prevents accidental restores

4. **Delete flow:** Standard confirmation dialog (one step). "Delete this backup? This cannot be undone."

5. **Status messages:** Banner at the top of the component for success/error messages. Auto-dismiss after 5 seconds.

6. **Empty state:** "No backups available. Create your first backup using the button above."

7. **Type badges:**
   - Oracle Full: `bg-blue-500/20 text-blue-400` with label "Oracle Full"
   - Oracle Data: `bg-cyan-500/20 text-cyan-400` with label "Oracle Data"
   - Full Database: `bg-purple-500/20 text-purple-400` with label "Full DB"

**Styling:** Use Tailwind classes consistent with NPS dark theme (`bg-nps-bg-card`, `border-nps-border`, `text-nps-text`, etc.) and patterns from Session 38/39 admin components.

#### 6.2 Add route to `frontend/src/App.tsx`

Inside the admin layout Route group:

```tsx
<Route path="/admin/backups" element={<BackupManager />} />
```

#### 6.3 Add navigation link

Add "Backups" link in the admin sidebar/nav (alongside "Users", "Profiles", "Monitoring" from Sessions 38/39).

**STOP checkpoint:** BackupManager renders at `/admin/backups`. Create Backup dropdown shows 3 options. Backup table displays existing backups. Restore flow has two-step confirmation with type-to-confirm. Delete flow has confirmation dialog. Empty state displays correctly. RTL layout works in Persian locale.

---

### Phase 7: Environment Validation Script (~45 min)

**Create a comprehensive environment validation tool.**

#### 7.1 Create `scripts/validate_env.py`

```python
#!/usr/bin/env python3
"""
NPS Environment Validator

Checks all required environment variables, tests service connectivity,
and validates configuration format. Run before deployment or when
troubleshooting service issues.

Usage:
    python3 scripts/validate_env.py
    python3 scripts/validate_env.py --json     # JSON output for API consumption
    python3 scripts/validate_env.py --fix      # Suggest fixes for issues
"""
```

**What it checks:**

1. **`.env` file exists** -- Check that `.env` is present in project root
2. **Required environment variables** -- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `API_SECRET_KEY`, `API_HOST`, `API_PORT`, `REDIS_HOST`, `REDIS_PORT`
3. **Security variables (optional but validated if present)** -- `NPS_ENCRYPTION_KEY` (must be 64-char hex), `NPS_ENCRYPTION_SALT` (must be 32-char hex)
4. **Default value detection** -- Warn if `POSTGRES_PASSWORD` is still "changeme" or `API_SECRET_KEY` is the default placeholder
5. **Optional variables** -- `ANTHROPIC_API_KEY`, `NPS_BOT_TOKEN`, `NPS_CHAT_ID` (warn if absent, not fail)
6. **PostgreSQL connectivity** -- TCP connection test + actual authentication with `psycopg2`
7. **Redis connectivity** -- TCP connection test + PING command
8. **Docker availability** -- Check `docker compose version` is available
9. **Required files** -- `docker-compose.yml`, `database/init.sql` exist

**Output modes:**

- Default: Human-readable table with `[PASS]`, `[FAIL]`, `[WARN]`, `[SKIP]` prefixes
- `--json`: Structured JSON with `checks` array and `summary` object
- `--fix`: Shows suggested fix for each failed check

**Exit codes:**

- `0` if all required checks pass
- `1` if any required check fails

**Key class structure:**

```python
class CheckResult(NamedTuple):
    name: str
    status: str  # "pass" | "fail" | "warn" | "skip"
    message: str
    fix: str = ""

def check_env_var(name: str, required: bool = True, format_hint: str = "") -> CheckResult: ...
def check_env_var_format(name: str, validator, format_desc: str) -> CheckResult: ...
def check_tcp_connection(host: str, port: int, service_name: str, timeout: float = 5.0) -> CheckResult: ...
def check_postgres(host: str, port: int, db: str, user: str, password: str) -> CheckResult: ...
def check_redis(host: str, port: int) -> CheckResult: ...
def check_file_exists(filepath: str, description: str) -> CheckResult: ...
def check_docker() -> CheckResult: ...
def run_all_checks() -> list[CheckResult]: ...
def print_results(results: list[CheckResult], json_mode: bool, show_fixes: bool) -> int: ...
```

**Graceful handling:** If `psycopg2` or `redis` Python packages are not installed, skip those checks with status `"skip"` and suggest installing them.

**STOP checkpoint:** `python3 scripts/validate_env.py` runs and produces a pass/fail report. `--json` flag produces valid JSON. `--fix` flag shows suggestions. Exit code reflects check results.

```bash
python3 scripts/validate_env.py --fix
echo "Exit code: $?"

python3 scripts/validate_env.py --json | python3 -m json.tool
```

---

### Phase 8: Write Tests (~45 min)

**Write comprehensive tests for all new components and endpoints.**

#### Test File: `api/app/routers/__tests__/test_backup.py`

| #   | Test Name                          | What It Tests                                                    |
| --- | ---------------------------------- | ---------------------------------------------------------------- |
| 1   | `test_list_backups_admin_only`     | `GET /admin/backups` returns 403 for non-admin                   |
| 2   | `test_list_backups_returns_files`  | Response contains backup list with metadata                      |
| 3   | `test_list_backups_empty`          | Returns empty list when no backups exist                         |
| 4   | `test_trigger_backup_oracle_full`  | `POST /admin/backups` with `oracle_full` type succeeds           |
| 5   | `test_trigger_backup_invalid_type` | `POST /admin/backups` with invalid type returns 422              |
| 6   | `test_trigger_backup_admin_only`   | `POST /admin/backups` returns 403 for non-admin                  |
| 7   | `test_restore_requires_confirm`    | `POST /admin/backups/restore` with `confirm: false` returns 400  |
| 8   | `test_restore_nonexistent_file`    | `POST /admin/backups/restore` with bad filename returns 404      |
| 9   | `test_restore_path_traversal`      | `POST /admin/backups/restore` with `../` in filename returns 400 |
| 10  | `test_restore_admin_only`          | `POST /admin/backups/restore` returns 403 for non-admin          |
| 11  | `test_delete_backup`               | `DELETE /admin/backups/{filename}` removes file                  |
| 12  | `test_delete_nonexistent`          | `DELETE /admin/backups/{filename}` returns 404 for missing file  |
| 13  | `test_delete_path_traversal`       | `DELETE /admin/backups/../etc/passwd` returns 400                |
| 14  | `test_delete_admin_only`           | `DELETE /admin/backups/{filename}` returns 403 for non-admin     |
| 15  | `test_backup_info_metadata`        | BackupInfo model correctly parses `.meta.json` files             |

**Test patterns:**

- Use `pytest` + `TestClient`
- Mock `subprocess.run()` for backup/restore commands (do not actually run scripts in tests)
- Use `tmp_path` fixture to create fake backup files for list/delete tests
- Verify path traversal protection (filenames containing `..`, `/`, etc.)

#### Test File: `frontend/src/components/admin/__tests__/BackupManager.test.tsx`

| #   | Test Name                       | What It Tests                                              |
| --- | ------------------------------- | ---------------------------------------------------------- |
| 16  | `test_renders_backup_list`      | BackupManager displays backup table with mock data         |
| 17  | `test_empty_state`              | Shows "No backups available" when list is empty            |
| 18  | `test_create_backup_dropdown`   | Create Backup button opens dropdown with 3 options         |
| 19  | `test_trigger_backup_calls_api` | Clicking an option calls `triggerBackup` mutation          |
| 20  | `test_restore_two_step_confirm` | Restore requires typing "RESTORE" to enable confirm button |
| 21  | `test_delete_confirmation`      | Delete shows confirmation dialog before API call           |
| 22  | `test_type_badges`              | Correct color badges for each backup type                  |
| 23  | `test_loading_state`            | Shows loading indicator during backup operation            |
| 24  | `test_error_state`              | Shows error message when backup fails                      |
| 25  | `test_schedule_info_display`    | Schedule card shows daily and weekly schedule text         |

**Test patterns:**

- Use `vitest` + `@testing-library/react`
- Mock `api.admin.backups()` and mutation functions
- Test user interaction flows (click dropdown -> click option -> verify API call)
- Test confirmation modals (restore type-to-confirm, delete confirm)

**STOP checkpoint:** All tests pass.

```bash
cd api && python3 -m pytest app/routers/__tests__/test_backup.py -v
cd frontend && npx vitest run src/components/admin/__tests__/BackupManager.test.tsx --reporter=verbose
```

---

### Phase 9: Final Verification (~30 min)

**End-to-end verification of the complete backup/restore system and infrastructure polish.**

#### 9.1 Docker Compose Validation

```bash
# Validate compose file
docker compose config --quiet && echo "OK" || echo "FAIL"

# List all services
docker compose config --services | sort
# Expected: api, backup, frontend, nginx, oracle-alerter, oracle-service, postgres, redis, scanner-service

# Verify all services have health checks
docker compose config | grep -c "healthcheck"
# Expected: >= 9

# Verify all services have restart policies
docker compose config | grep -c "unless-stopped"
# Expected: >= 9

# Verify resource limits
docker compose config | grep -c "limits"
# Expected: >= 9
```

#### 9.2 Environment Validation

```bash
python3 scripts/validate_env.py --fix
# Expected: Shows all checks, identifies any issues with fixes

python3 scripts/validate_env.py --json | python3 -m json.tool
# Expected: Valid JSON output
```

#### 9.3 Backup System Verification

```bash
# Test manual backup via script
./database/scripts/oracle_backup.sh --non-interactive
echo "Exit code: $?"
# Expected: 0

# Verify metadata file created
ls -la backups/oracle/*.meta.json | tail -1
# Expected: .meta.json file alongside the .sql.gz

# Test backup list API
curl -H "Authorization: Bearer <admin_token>" http://localhost:8000/api/admin/backups | python3 -m json.tool
# Expected: JSON with backups array

# Test manual backup via API
curl -X POST -H "Authorization: Bearer <admin_token>" \
    -H "Content-Type: application/json" \
    -d '{"backup_type": "oracle_full"}' \
    http://localhost:8000/api/admin/backups | python3 -m json.tool
# Expected: {"status": "success", "backup": {...}}

# Test delete via API
curl -X DELETE -H "Authorization: Bearer <admin_token>" \
    http://localhost:8000/api/admin/backups/<backup_filename> | python3 -m json.tool
# Expected: {"status": "success"}

# Test non-admin access
curl -H "Authorization: Bearer <user_token>" http://localhost:8000/api/admin/backups
# Expected: 403
```

#### 9.4 Frontend Verification

```bash
# TypeScript compilation
cd frontend && npx tsc --noEmit
# Expected: no errors

# Build
cd frontend && npm run build
# Expected: successful build

# All tests pass
cd frontend && npm test -- --run
cd api && python3 -m pytest -v
```

#### 9.5 RTL Verification

Switch to Persian locale and verify:

- Backup table is mirrored (actions on left for RTL)
- All text is translated
- Date formats are correct
- Buttons and dialogs display correctly

#### 9.6 Security Verification

```bash
# Path traversal protection
curl -X DELETE -H "Authorization: Bearer <admin_token>" \
    http://localhost:8000/api/admin/backups/..%2F..%2Fetc%2Fpasswd
# Expected: 400 Bad Request

curl -X POST -H "Authorization: Bearer <admin_token>" \
    -H "Content-Type: application/json" \
    -d '{"filename": "../../etc/passwd", "confirm": true}' \
    http://localhost:8000/api/admin/backups/restore
# Expected: 400 Bad Request
```

**STOP checkpoint:** All verifications pass. Docker Compose is valid with all services. Environment validator works. Backup create/list/restore/delete work end-to-end. Frontend compiles and tests pass. RTL layout correct. Security protections active.

---

## TESTS SUMMARY

| #   | Test File                                  | Test Name                          | What It Verifies           |
| --- | ------------------------------------------ | ---------------------------------- | -------------------------- |
| 1   | `api/app/routers/__tests__/test_backup.py` | `test_list_backups_admin_only`     | Non-admin gets 403         |
| 2   | `api/app/routers/__tests__/test_backup.py` | `test_list_backups_returns_files`  | Backup list with metadata  |
| 3   | `api/app/routers/__tests__/test_backup.py` | `test_list_backups_empty`          | Empty list when no backups |
| 4   | `api/app/routers/__tests__/test_backup.py` | `test_trigger_backup_oracle_full`  | Oracle backup triggers     |
| 5   | `api/app/routers/__tests__/test_backup.py` | `test_trigger_backup_invalid_type` | Invalid type rejected      |
| 6   | `api/app/routers/__tests__/test_backup.py` | `test_trigger_backup_admin_only`   | Non-admin gets 403         |
| 7   | `api/app/routers/__tests__/test_backup.py` | `test_restore_requires_confirm`    | Confirm false returns 400  |
| 8   | `api/app/routers/__tests__/test_backup.py` | `test_restore_nonexistent_file`    | Missing file returns 404   |
| 9   | `api/app/routers/__tests__/test_backup.py` | `test_restore_path_traversal`      | Path traversal blocked     |
| 10  | `api/app/routers/__tests__/test_backup.py` | `test_restore_admin_only`          | Non-admin gets 403         |
| 11  | `api/app/routers/__tests__/test_backup.py` | `test_delete_backup`               | Backup file deleted        |
| 12  | `api/app/routers/__tests__/test_backup.py` | `test_delete_nonexistent`          | Missing file returns 404   |
| 13  | `api/app/routers/__tests__/test_backup.py` | `test_delete_path_traversal`       | Path traversal blocked     |
| 14  | `api/app/routers/__tests__/test_backup.py` | `test_delete_admin_only`           | Non-admin gets 403         |
| 15  | `api/app/routers/__tests__/test_backup.py` | `test_backup_info_metadata`        | Metadata parsing correct   |
| 16  | `frontend/.../BackupManager.test.tsx`      | `test_renders_backup_list`         | Table renders with data    |
| 17  | `frontend/.../BackupManager.test.tsx`      | `test_empty_state`                 | Empty state message        |
| 18  | `frontend/.../BackupManager.test.tsx`      | `test_create_backup_dropdown`      | Dropdown with 3 options    |
| 19  | `frontend/.../BackupManager.test.tsx`      | `test_trigger_backup_calls_api`    | API call on trigger        |
| 20  | `frontend/.../BackupManager.test.tsx`      | `test_restore_two_step_confirm`    | Type-to-confirm flow       |
| 21  | `frontend/.../BackupManager.test.tsx`      | `test_delete_confirmation`         | Confirm before delete      |
| 22  | `frontend/.../BackupManager.test.tsx`      | `test_type_badges`                 | Color-coded type badges    |
| 23  | `frontend/.../BackupManager.test.tsx`      | `test_loading_state`               | Loading indicator          |
| 24  | `frontend/.../BackupManager.test.tsx`      | `test_error_state`                 | Error message display      |
| 25  | `frontend/.../BackupManager.test.tsx`      | `test_schedule_info_display`       | Schedule card text         |

**Total: 25 tests** (15 API + 10 frontend)

---

## ACCEPTANCE CRITERIA

- [ ] `docker-compose.yml` has a new `backup` service for automated daily/weekly backups
- [ ] All Docker Compose services have health checks, restart policies, and resource limits
- [ ] `database/scripts/oracle_backup.sh` supports `--non-interactive` and `--notify` flags and creates `.meta.json` sidecar files
- [ ] `database/scripts/oracle_restore.sh` supports `--non-interactive` flag for API invocation
- [ ] `scripts/backup.sh` supports `--non-interactive` and `--notify` flags with metadata
- [ ] `scripts/restore.sh` supports `--non-interactive` flag
- [ ] Backup retention: Oracle backups auto-deleted after 30 days, full DB after 60 days
- [ ] `GET /api/admin/backups` returns list of available backups with metadata
- [ ] `POST /api/admin/backups` triggers a manual backup and returns backup info
- [ ] `POST /api/admin/backups/restore` restores from a selected backup with confirmation
- [ ] `DELETE /api/admin/backups/{filename}` deletes a backup with path traversal protection
- [ ] All backup API endpoints are admin-only (403 for non-admin)
- [ ] All backup operations are logged to `oracle_audit_log`
- [ ] `/admin/backups` page displays backup list, schedule info, and action buttons
- [ ] Restore flow has two-step confirmation (type "RESTORE" to confirm)
- [ ] `scripts/validate_env.py` checks all required variables, tests connectivity, supports `--json` and `--fix`
- [ ] Persian RTL layout works for all backup UI components
- [ ] All 25 tests pass (15 API + 10 frontend)
- [ ] No regressions in existing tests
- [ ] `docker compose config` validates without errors

**Verification commands:**

```bash
# Docker Compose validation
docker compose config --quiet

# Environment validation
python3 scripts/validate_env.py

# API tests
cd api && python3 -m pytest app/routers/__tests__/test_backup.py -v

# Frontend tests
cd frontend && npx vitest run src/components/admin/__tests__/BackupManager.test.tsx --reporter=verbose

# TypeScript compilation
cd frontend && npx tsc --noEmit

# All tests pass (no regressions)
cd api && python3 -m pytest -v
cd frontend && npm test -- --run
```

---

## ERROR SCENARIOS

### Scenario 1: Backup script fails (disk full or permission denied)

**Trigger:** `subprocess.run()` of backup script returns non-zero exit code.

**Recovery:**

1. API catches the non-zero exit code from `subprocess.run()`
2. Returns `{"status": "failed", "message": "<stderr output>"}` with HTTP 500
3. Frontend shows error banner with the failure message
4. Telegram notification sent (if `--notify` flag was used) with failure details
5. No partial backup file left behind (existing script already handles cleanup on empty file)
6. Admin can check disk space via the health dashboard (Session 39) and resolve

### Scenario 2: Restore fails mid-way (connection drop during restore)

**Trigger:** PostgreSQL connection drops during `psql` restore command.

**Recovery:**

1. The restore script returns non-zero exit code
2. API returns `{"status": "failed", "message": "Restore interrupted"}`
3. Database may be in an inconsistent state (Oracle tables truncated but not fully restored)
4. Admin should re-run the restore from the same backup
5. For full-database restores, the database was dropped and recreated -- admin must restore again
6. The original backup file is never modified or deleted during restore

### Scenario 3: Path traversal attack on backup filename

**Trigger:** Malicious filename like `../../etc/passwd` or `../docker-compose.yml`.

**Recovery:**

1. API validates: `os.path.basename(filename) == filename` -- rejects filenames with path separators
2. API validates: filename ends with `.sql.gz` -- rejects non-backup files
3. API validates: resolved file path starts with the expected backup directory
4. Returns HTTP 400 with `"Invalid filename"` message
5. The operation is logged to audit log as a failed attempt

### Scenario 4: Backup cron container fails to start

**Trigger:** Dockerfile build error or missing scripts.

**Recovery:**

1. Docker Compose shows the `backup` container as stopped or restarting
2. Check logs: `docker compose logs backup`
3. Common fix: scripts not executable (add `chmod +x` in Dockerfile)
4. Common fix: crontab syntax error
5. Manual backups still work via the API (API calls scripts directly, not via cron container)
6. The cron container failure does not affect any other service

### Scenario 5: `validate_env.py` reports failures on fresh install

**Trigger:** Running validation before configuring `.env`.

**Recovery:**

1. Script shows `[FAIL]` for missing or default-valued variables
2. Running with `--fix` shows specific instructions for each failure
3. User follows fix suggestions to populate `.env` from `.env.example`
4. Re-run validation to confirm all checks pass
5. The script is informational only -- it does not modify any files

### Scenario 6: Large backup takes longer than API timeout

**Trigger:** Full database backup exceeds the 120-second `subprocess.run()` timeout.

**Recovery:**

1. `subprocess.run()` raises `subprocess.TimeoutExpired`
2. API catches the exception and returns `{"status": "failed", "message": "Backup timed out after 120 seconds"}`
3. The backup process is killed by the subprocess timeout
4. Admin can run the backup manually via CLI for very large databases: `scripts/backup.sh --non-interactive`
5. For full-database backups, the timeout is set to 300 seconds (vs 120 for Oracle table backups) to accommodate larger data
6. Consider making the timeout configurable via an environment variable in future sessions

### Scenario 7: Multiple admins trigger backups simultaneously

**Trigger:** Two admins click "Create Backup" at the same time.

**Recovery:**

1. Both `subprocess.run()` calls will execute `pg_dump` concurrently
2. PostgreSQL handles concurrent reads gracefully -- both backups will succeed
3. Both backup files will have different timestamps and will not conflict
4. No data corruption risk since `pg_dump` uses `MVCC` snapshots
5. The API does not need a mutex for this case

---

## HANDOFF

### What Session 41 Receives

Session 41 begins the **Testing & Deployment** block (Sessions 41-45). It inherits a fully functional Admin & DevOps system:

1. **Admin panel** -- User management (Session 38), system monitoring (Session 39), backup/restore (Session 40) at `/admin/*`
2. **Automated backups** -- Daily Oracle table backups and weekly full-database backups via cron Docker container
3. **Infrastructure** -- All Docker Compose services verified with health checks, restart policies, and resource limits
4. **Environment validation** -- `scripts/validate_env.py` for pre-deployment checks
5. **Monitoring** -- Health dashboard, log viewer, analytics charts, Telegram alerts
6. **Complete admin API** -- User CRUD, analytics, logs, errors, backups, restore endpoints

### Files Session 41 Will Use

| File                                | How Session 41 Uses It                           |
| ----------------------------------- | ------------------------------------------------ |
| `docker-compose.yml`                | Base for deployment optimization and CI/CD       |
| `scripts/validate_env.py`           | Include in CI/CD pipeline and deployment scripts |
| `scripts/deploy.sh`                 | Enhance with pre-deployment validation           |
| `scripts/health-check.sh`           | Include in deployment verification               |
| `api/app/routers/admin.py`          | Reference for integration test patterns          |
| `database/scripts/oracle_backup.sh` | Include in deployment rollback procedures        |

### State After Session 40

```
database/scripts/
  oracle_backup.sh              # MODIFIED -- non-interactive, notify, metadata, age-based retention
  oracle_restore.sh             # MODIFIED -- non-interactive mode
  README.md                     # Existing

scripts/
  backup.sh                     # MODIFIED -- non-interactive, notify, metadata, age-based retention
  restore.sh                    # MODIFIED -- non-interactive mode
  backup_cron.sh                # NEW -- cron wrapper for daily/weekly
  crontab                       # NEW -- cron schedule definition
  Dockerfile.backup             # NEW -- backup cron container
  validate_env.py               # NEW -- environment validation tool
  deploy.sh                     # Existing
  health-check.sh               # Existing
  rollback.sh                   # Existing

api/app/
  routers/
    admin.py                    # MODIFIED -- added backup/restore endpoints
    __tests__/
      test_backup.py            # NEW -- 15 API tests
  models/
    backup.py                   # NEW -- Pydantic backup models

frontend/src/
  components/admin/
    BackupManager.tsx           # NEW -- backup management UI
    __tests__/
      BackupManager.test.tsx    # NEW -- 10 frontend tests
  hooks/
    useAdminData.ts             # MODIFIED -- added backup hooks
  services/
    api.ts                      # MODIFIED -- added backup API client
  types/
    index.ts                    # MODIFIED -- added backup types
  locales/
    en.json                     # MODIFIED -- added backup i18n keys
    fa.json                     # MODIFIED -- added backup i18n keys (Persian)
  App.tsx                       # MODIFIED -- added /admin/backups route

docker-compose.yml              # MODIFIED -- added backup service, polished health checks
```

### Admin & DevOps Block Complete

With Session 40 done, the Admin & DevOps block (Sessions 38-40) is fully complete:

| Session | Feature                          | Status   |
| ------- | -------------------------------- | -------- |
| 38      | Admin Panel: User Management     | Complete |
| 39      | Admin Panel: System Monitoring   | Complete |
| 40      | Backup, Restore & Infrastructure | Complete |

The project moves to the **Testing & Deployment** block (Sessions 41-45):

- Session 41: Integration test suite expansion
- Session 42: Performance optimization
- Session 43: E2E tests with Playwright
- Session 44: CI/CD pipeline
- Session 45: Production deployment

---

_Specification Version: 2.0_
_Created: 2026-02-10_
_Status: Ready for Review_
