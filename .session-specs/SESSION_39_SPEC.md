# SESSION 39 SPEC — Admin Panel: System Monitoring

**Block:** Admin & DevOps (Sessions 38-40)
**Estimated Duration:** 5-6 hours
**Complexity:** Medium-High
**Dependencies:** Session 38 (admin base — Admin.tsx page, AdminGuard, admin routing, user management UI)

---

## TL;DR

- Build `AdminMonitoring.tsx` page with 3 sub-components: `HealthDashboard`, `LogViewer`, `AnalyticsCharts`
- Extend FastAPI `/api/health` with 3 new admin-only endpoints: `/api/health/detailed`, `/api/health/logs`, `/api/health/analytics`
- Install `recharts` charting library for frontend analytics (lightweight, React-native, zero-dependency charts)
- Add auto-refresh polling (10s for health, 30s for analytics) with manual refresh buttons
- Update `devops/dashboards/simple_dashboard.py` to proxy the new detailed health endpoint
- Write 22+ tests (18 API + 4 frontend) covering health detail, log filtering, analytics aggregation, and admin-only access

---

## OBJECTIVES

1. **Health dashboard component** -- Real-time service status for API, Oracle, Scanner, Database, Redis, Telegram, and Nginx with uptime, memory usage, and CPU metrics
2. **Log viewer component** -- Paginated, filterable display of audit log entries from `oracle_audit_log` with severity filtering (INFO, WARNING, ERROR, CRITICAL) and text search
3. **Reading analytics component** -- Charts: readings per day (bar), readings by type (pie), average confidence trend (line), popular reading hours (bar)
4. **Admin-only API endpoints** -- 3 new endpoints under `/api/health` that require `admin` scope and return detailed system info, filtered logs, and aggregated analytics
5. **Simple dashboard update** -- Extend the existing Flask dashboard to display new detailed health data from the API

---

## PREREQUISITES

- [ ] Session 38 complete -- `Admin.tsx` page exists at `frontend/src/pages/Admin.tsx` with admin routing under `/admin/*`
- [ ] Session 38 complete -- `AdminGuard` component exists for role-based route protection
- [ ] Session 38 complete -- Admin navigation includes link to monitoring sub-page
- [ ] Existing `/api/health` and `/api/health/ready` endpoints work (unauthenticated, for Docker probes)
- [ ] `oracle_audit_log` table exists with action, timestamp, success, details columns
- [ ] `oracle_readings` table exists with sign_type, created_at, reading_result columns
- Verification:
  ```bash
  test -f api/app/routers/health.py && \
  test -f devops/dashboards/simple_dashboard.py && \
  test -f devops/logging/oracle_logger.py && \
  test -f api/app/services/audit.py && \
  test -f api/app/orm/audit_log.py && \
  echo "Prerequisites OK"
  ```

---

## EXISTING CODE ANALYSIS

### What Already Works (Keep & Extend)

**Health router** at `api/app/routers/health.py` (71 lines):

- `GET /api/health` -- Basic status + version (`{"status": "healthy", "version": "4.0.0"}`)
- `GET /api/health/ready` -- Readiness probe checking Database, Redis, Scanner, Oracle
- `GET /api/health/performance` -- Stub (TODO: implement)
- All 3 endpoints are unauthenticated (designed for Docker health probes)

**Audit service** at `api/app/services/audit.py` (207 lines):

- `AuditService.query_logs()` -- Generic log query with action, resource_type, resource_id filters + pagination
- `AuditService.get_failed_attempts()` -- Failed auth attempts in last N hours
- Already bound to `oracle_audit_log` ORM model via `api/app/orm/audit_log.py`

**Oracle logger** at `devops/logging/oracle_logger.py` (127 lines):

- `OracleJSONFormatter` -- Structured JSON with timestamp, level, service, logger, message, exception
- Rotating file handler: `oracle.log` (DEBUG+) and `error.log` (ERROR+)
- 10MB rotation, 5 backups

**Simple dashboard** at `devops/dashboards/simple_dashboard.py` (73 lines):

- Flask app on port 9000, fetches from Oracle HTTP sidecar at port 9090
- Proxies `/health` and `/metrics` endpoints
- Dark-themed HTML dashboard with auto-refresh (5s)

**Frontend API client** at `frontend/src/services/api.ts` (192 lines):

- `health.check()` and `health.ready()` already defined
- Auth token from `localStorage` automatically attached via `request<T>()` helper
- Follows `export const namespace = { method: () => request<Type>(...) }` pattern

**Frontend types** at `frontend/src/types/index.ts` (411 lines):

- `HealthStatus` interface exists: `{ status, checks }`
- `User` interface: `{ id, username, role }`

**Auth middleware** at `api/app/middleware/auth.py` (206 lines):

- `require_scope("admin")` dependency factory returns 403 for non-admin users
- `_ROLE_SCOPES["admin"]` includes `"admin"` scope
- Only admin role gets the `"admin"` scope

**Test infrastructure** at `api/tests/conftest.py` (146 lines):

- `client` fixture: authenticated admin with all scopes
- `readonly_client` fixture: read-only user, no admin scope
- `unauth_client` fixture: unauthenticated
- SQLite in-memory test database with `setup_database` autouse fixture

### What's Missing

| Component                 | Current State                                                                         | What Session 39 Adds                                                                  |
| ------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Detailed health endpoint  | None (basic and ready only)                                                           | `GET /api/health/detailed` (admin) with CPU, memory, uptime, all service statuses     |
| Log viewer endpoint       | `AuditService.query_logs()` exists but no HTTP endpoint for log viewing with severity | `GET /api/health/logs` (admin) with severity, date range, search filters              |
| Analytics endpoint        | No aggregation                                                                        | `GET /api/health/analytics` (admin) with readings-per-day, by-type, confidence trends |
| AdminMonitoring page      | Does not exist                                                                        | New page with 3 tab sections                                                          |
| HealthDashboard component | Does not exist                                                                        | Service status cards with live indicators                                             |
| LogViewer component       | Does not exist                                                                        | Filterable log table with severity badges                                             |
| AnalyticsCharts component | Does not exist                                                                        | 4 charts: readings/day, by type, confidence trend, popular hours                      |
| Charting library          | Not installed                                                                         | `recharts` (React charting, ~200KB gzipped, pure SVG)                                 |
| Admin health API types    | Does not exist                                                                        | TypeScript interfaces for detailed health, logs, analytics                            |

---

## FILES TO CREATE

- `frontend/src/pages/AdminMonitoring.tsx` -- Admin monitoring page with tab navigation between Health, Logs, Analytics
- `frontend/src/components/admin/HealthDashboard.tsx` -- Service status cards with color-coded indicators, uptime, resource usage
- `frontend/src/components/admin/LogViewer.tsx` -- Paginated log table with severity filter, time window picker, search
- `frontend/src/components/admin/AnalyticsCharts.tsx` -- 4 charts using recharts: readings/day, by type, confidence trend, popular hours
- `api/tests/test_health_admin.py` -- Tests for the 3 new admin-only health endpoints (18+ tests)
- `frontend/src/tests/AdminMonitoring.test.tsx` -- Frontend component tests (4+ tests)

## FILES TO MODIFY

- `api/app/routers/health.py` -- Add 3 admin-only endpoints: `/detailed`, `/logs`, `/analytics`
- `api/app/services/audit.py` -- Add `query_logs_extended()` method with search, success, hours filters
- `frontend/src/services/api.ts` -- Add `adminHealth` namespace with `detailed()`, `logs()`, `analytics()` methods
- `frontend/src/types/index.ts` -- Add admin monitoring TypeScript interfaces
- `frontend/src/App.tsx` -- Add `/admin/monitoring` route (or Session 38's admin sub-router)
- `frontend/package.json` -- Add `recharts` dependency
- `devops/dashboards/simple_dashboard.py` -- Add proxy for `/api/health/detailed` endpoint
- `devops/dashboards/templates/dashboard.html` -- Add system info display section

## FILES TO DELETE

- None

---

## IMPLEMENTATION PHASES

### Phase 1: API -- Detailed Health Endpoint (~60 min)

**Tasks:**

1. Add imports to `api/app/routers/health.py`:

   ```python
   import os
   import platform
   import time
   from datetime import datetime, timezone

   from fastapi import Depends, Query
   from sqlalchemy.orm import Session

   from app.database import get_db
   from app.middleware.auth import require_scope
   ```

2. Add server start time tracker (module-level):

   ```python
   _server_start_time = time.time()
   ```

3. Add cross-platform memory helper:

   ```python
   def _get_process_memory_mb() -> float:
       """Get current process RSS in megabytes, cross-platform."""
       try:
           import resource as resource_mod
           usage = resource_mod.getrusage(resource_mod.RUSAGE_SELF)
           rss = usage.ru_maxrss
           if platform.system() == "Darwin":
               return round(rss / (1024 * 1024), 1)  # macOS: bytes
           return round(rss / 1024, 1)  # Linux: KB
       except (ImportError, AttributeError):
           return 0.0
   ```

4. Add `GET /api/health/detailed` endpoint:

   ```python
   @router.get("/detailed")
   async def detailed_health(
       request: Request,
       _user: dict = Depends(require_scope("admin")),
   ):
       """Detailed system health -- admin only.

       Returns service statuses, resource usage, and system info.
       """
       checks = {}

       # 1. Database check
       try:
           with engine.connect() as conn:
               conn.execute(text("SELECT 1"))
               try:
                   db_info = conn.execute(text(
                       "SELECT pg_database_size(current_database()) as size_bytes"
                   )).first()
                   size_bytes = db_info.size_bytes if db_info else None
               except Exception:
                   size_bytes = None  # SQLite or insufficient permissions
           checks["database"] = {
               "status": "healthy",
               "type": "postgresql",
               "size_bytes": size_bytes,
           }
       except Exception as exc:
           logger.warning("Database health check failed: %s", exc)
           checks["database"] = {"status": "unhealthy", "error": str(exc)}

       # 2. Redis check
       redis = getattr(request.app.state, "redis", None)
       if redis:
           try:
               info = await redis.info("memory")
               await redis.ping()
               checks["redis"] = {
                   "status": "healthy",
                   "used_memory_bytes": info.get("used_memory", 0),
                   "used_memory_human": info.get("used_memory_human", "unknown"),
               }
           except Exception as exc:
               checks["redis"] = {"status": "unhealthy", "error": str(exc)}
       else:
           checks["redis"] = {"status": "not_connected"}

       # 3. Oracle gRPC check
       oracle_channel = getattr(request.app.state, "oracle_channel", None)
       if oracle_channel:
           try:
               import grpc
               grpc.channel_ready_future(oracle_channel).result(timeout=1)
               checks["oracle_service"] = {"status": "healthy", "mode": "grpc"}
           except Exception:
               checks["oracle_service"] = {"status": "unhealthy", "mode": "grpc"}
       else:
           checks["oracle_service"] = {"status": "direct_mode", "mode": "legacy"}

       # 4. Scanner service (Rust stub)
       checks["scanner_service"] = {"status": "not_deployed"}

       # 5. API self-check
       checks["api"] = {
           "status": "healthy",
           "version": "4.0.0",
           "python_version": platform.python_version(),
       }

       # 6. Telegram bot check (env var presence)
       telegram_token = os.environ.get("NPS_BOT_TOKEN")
       checks["telegram"] = {
           "status": "configured" if telegram_token else "not_configured",
       }

       # 7. Nginx (external to this process)
       checks["nginx"] = {"status": "external", "note": "Check via Docker health"}

       uptime_seconds = time.time() - _server_start_time

       return {
           "status": "healthy" if checks["database"]["status"] == "healthy" else "degraded",
           "timestamp": datetime.now(timezone.utc).isoformat(),
           "uptime_seconds": round(uptime_seconds),
           "system": {
               "platform": platform.platform(),
               "python_version": platform.python_version(),
               "cpu_count": os.cpu_count(),
               "process_memory_mb": _get_process_memory_mb(),
           },
           "services": checks,
       }
   ```

   **Key notes:**
   - `resource` module works on Unix/macOS only. For Docker (Linux), `ru_maxrss` is in KB. For macOS, it is in bytes. The helper detects platform and adjusts.
   - The endpoint requires `admin` scope via `Depends(require_scope("admin"))`. Non-admin users get 403.
   - Database size query uses `pg_database_size()` which requires PostgreSQL. Falls back gracefully on SQLite (test environment) via inner try/except.
   - The existing unauthenticated endpoints (`/health`, `/health/ready`) remain unchanged for Docker probes.

**Checkpoint:**

- [ ] `GET /api/health/detailed` returns all 7 service statuses (api, database, redis, oracle_service, scanner_service, telegram, nginx)
- [ ] Endpoint requires admin scope (non-admin gets 403)
- [ ] Response includes uptime_seconds, system info (platform, python_version, cpu_count, process_memory_mb), service details
- [ ] Database check includes size estimate (PostgreSQL only, null on SQLite)
- [ ] Redis check includes memory usage when connected
- Verify: `grep -c "detailed" api/app/routers/health.py` -- should return 2+

STOP if checkpoint fails

---

### Phase 2: API -- Log Viewer Endpoint (~45 min)

**Tasks:**

1. Add `query_logs_extended()` method to `api/app/services/audit.py`:

   ```python
   def query_logs_extended(
       self,
       *,
       action: str | None = None,
       resource_type: str | None = None,
       success: bool | None = None,
       search: str | None = None,
       hours: int = 24,
       limit: int = 50,
       offset: int = 0,
   ) -> tuple[list[OracleAuditLog], int]:
       """Extended log query with additional filters for admin monitoring.

       Parameters
       ----------
       action : str, optional
           Filter by exact action name (e.g., "oracle_reading.create").
       resource_type : str, optional
           Filter by resource type (e.g., "oracle_user").
       success : bool, optional
           Filter by success status.
       search : str, optional
           ILIKE search across action and details columns.
       hours : int
           Time window in hours (default 24, max 720).
       limit : int
           Max entries to return (default 50).
       offset : int
           Skip first N entries (default 0).

       Returns
       -------
       tuple[list[OracleAuditLog], int]
           List of log entries and total count matching filters.
       """
       since = datetime.now(timezone.utc) - timedelta(hours=hours)
       query = self.db.query(OracleAuditLog).filter(
           OracleAuditLog.timestamp >= since
       )
       if action:
           query = query.filter(OracleAuditLog.action == action)
       if resource_type:
           query = query.filter(OracleAuditLog.resource_type == resource_type)
       if success is not None:
           query = query.filter(OracleAuditLog.success == success)
       if search:
           search_pattern = f"%{search}%"
           query = query.filter(
               OracleAuditLog.action.ilike(search_pattern)
               | OracleAuditLog.details.ilike(search_pattern)
           )
       total = query.count()
       entries = (
           query.order_by(OracleAuditLog.timestamp.desc())
           .offset(offset)
           .limit(limit)
           .all()
       )
       return entries, total
   ```

2. Add severity derivation helper to `api/app/routers/health.py`:

   ```python
   def _derive_severity(entry: OracleAuditLog) -> str:
       """Derive log severity from audit log entry properties.

       Mapping:
       - success=False + "auth" in action -> "critical"
       - success=False -> "error"
       - "delete" or "deactivate" in action -> "warning"
       - everything else -> "info"
       """
       if not entry.success:
           if "auth" in (entry.action or ""):
               return "critical"
           return "error"
       action = entry.action or ""
       if "delete" in action or "deactivate" in action:
           return "warning"
       return "info"
   ```

3. Add `GET /api/health/logs` endpoint to `api/app/routers/health.py`:

   ```python
   from app.services.audit import AuditService, get_audit_service
   from app.orm.audit_log import OracleAuditLog
   import json as json_mod

   @router.get("/logs")
   async def get_logs(
       limit: int = Query(50, ge=1, le=500),
       offset: int = Query(0, ge=0),
       severity: str | None = Query(None, description="Filter: info, warning, error, critical"),
       action: str | None = Query(None, description="Filter by action type"),
       resource_type: str | None = Query(None),
       success: bool | None = Query(None),
       search: str | None = Query(None, description="Search in action and details"),
       hours: int = Query(24, ge=1, le=720, description="Time window in hours"),
       _user: dict = Depends(require_scope("admin")),
       audit: AuditService = Depends(get_audit_service),
   ):
       """Query audit logs with filtering -- admin only.

       Returns paginated log entries from oracle_audit_log table.
       Supports severity (derived from success+action), action type,
       resource type, success/failure, text search, and time window filters.
       """
       # Map severity filter to success filter
       effective_success = success
       if severity == "error":
           effective_success = False
       elif severity == "critical":
           effective_success = False
       elif severity == "info":
           if effective_success is None:
               effective_success = True

       entries, total = audit.query_logs_extended(
           action=action,
           resource_type=resource_type,
           success=effective_success,
           search=search,
           hours=hours,
           limit=limit,
           offset=offset,
       )

       logs = []
       for entry in entries:
           derived_severity = _derive_severity(entry)
           # If severity filter is set, skip non-matching entries
           if severity and derived_severity != severity:
               continue
           logs.append({
               "id": entry.id,
               "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
               "action": entry.action,
               "resource_type": entry.resource_type,
               "resource_id": entry.resource_id,
               "success": entry.success,
               "ip_address": entry.ip_address,
               "details": json_mod.loads(entry.details) if entry.details else None,
               "severity": derived_severity,
           })

       return {
           "logs": logs,
           "total": total,
           "limit": limit,
           "offset": offset,
           "time_window_hours": hours,
       }
   ```

**Checkpoint:**

- [ ] `GET /api/health/logs` returns paginated audit log entries with derived severity
- [ ] Severity filter maps correctly: error/critical -> success=False, info -> success=True
- [ ] Search filter does ILIKE on action + details
- [ ] Time window limits results (default 24 hours, max 720)
- [ ] Endpoint requires admin scope
- [ ] `AuditService.query_logs_extended()` method exists in `api/app/services/audit.py`
- Verify: `grep -c "def get_logs\|def query_logs_extended" api/app/routers/health.py api/app/services/audit.py` -- should return 2

STOP if checkpoint fails

---

### Phase 3: API -- Analytics Endpoint (~60 min)

**Tasks:**

1. Add `GET /api/health/analytics` to `api/app/routers/health.py`:

   ```python
   from sqlalchemy import cast, Date, Float, extract, func
   from datetime import date, timedelta
   from app.orm.oracle_reading import OracleReading

   @router.get("/analytics")
   async def reading_analytics(
       days: int = Query(30, ge=1, le=365, description="Time range in days"),
       _user: dict = Depends(require_scope("admin")),
       db: Session = Depends(get_db),
   ):
       """Reading analytics for admin dashboard -- admin only.

       Returns aggregated statistics over the specified time range:
       - readings_per_day: daily reading counts
       - readings_by_type: breakdown by sign_type
       - confidence_trend: average confidence score per day
       - popular_hours: reading count by hour of day (0-23)
       - totals: summary statistics
       """
       since = date.today() - timedelta(days=days)

       # Total readings in period
       total_readings = (
           db.query(func.count())
           .select_from(OracleReading)
           .filter(cast(OracleReading.created_at, Date) >= since)
           .scalar() or 0
       )

       # Readings per day
       readings_per_day_rows = (
           db.query(
               cast(OracleReading.created_at, Date).label("date"),
               func.count().label("count"),
           )
           .filter(cast(OracleReading.created_at, Date) >= since)
           .group_by(cast(OracleReading.created_at, Date))
           .order_by(cast(OracleReading.created_at, Date))
           .all()
       )
       readings_per_day = [
           {"date": str(row.date), "count": row.count}
           for row in readings_per_day_rows
       ]

       # Readings by type
       readings_by_type_rows = (
           db.query(
               OracleReading.sign_type.label("type"),
               func.count().label("count"),
           )
           .filter(cast(OracleReading.created_at, Date) >= since)
           .group_by(OracleReading.sign_type)
           .order_by(func.count().desc())
           .all()
       )
       readings_by_type = [
           {"type": row.type or "unknown", "count": row.count}
           for row in readings_by_type_rows
       ]

       # Confidence trend -- extract from reading_result JSONB
       # PostgreSQL: reading_result->'confidence'->>'score'
       # SQLite fallback: skip confidence data
       confidence_trend = []
       try:
           confidence_rows = (
               db.query(
                   cast(OracleReading.created_at, Date).label("date"),
                   func.avg(
                       cast(
                           OracleReading.reading_result["confidence"]["score"].as_string(),
                           Float,
                       )
                   ).label("avg_confidence"),
               )
               .filter(
                   cast(OracleReading.created_at, Date) >= since,
                   OracleReading.reading_result.isnot(None),
               )
               .group_by(cast(OracleReading.created_at, Date))
               .order_by(cast(OracleReading.created_at, Date))
               .all()
           )
           confidence_trend = [
               {
                   "date": str(row.date),
                   "avg_confidence": round(float(row.avg_confidence), 1)
                   if row.avg_confidence is not None else 0.0,
               }
               for row in confidence_rows
           ]
       except Exception:
           # SQLite does not support JSONB path extraction
           confidence_trend = []

       # Popular hours
       popular_hours_rows = (
           db.query(
               extract("hour", OracleReading.created_at).label("hour"),
               func.count().label("count"),
           )
           .filter(cast(OracleReading.created_at, Date) >= since)
           .group_by(extract("hour", OracleReading.created_at))
           .order_by(extract("hour", OracleReading.created_at))
           .all()
       )
       popular_hours = [
           {"hour": int(row.hour), "count": row.count}
           for row in popular_hours_rows
       ]

       # Error count from audit log
       error_count = (
           db.query(func.count())
           .select_from(OracleAuditLog)
           .filter(
               OracleAuditLog.success == False,  # noqa: E712
               OracleAuditLog.timestamp >= datetime.now(timezone.utc) - timedelta(days=days),
           )
           .scalar() or 0
       )

       # Determine most popular type and hour
       most_popular_type = readings_by_type[0]["type"] if readings_by_type else None
       most_active_hour = (
           max(popular_hours, key=lambda h: h["count"])["hour"]
           if popular_hours else None
       )

       return {
           "period_days": days,
           "readings_per_day": readings_per_day,
           "readings_by_type": readings_by_type,
           "confidence_trend": confidence_trend,
           "popular_hours": popular_hours,
           "totals": {
               "total_readings": total_readings,
               "avg_confidence": round(
                   sum(c["avg_confidence"] for c in confidence_trend) / len(confidence_trend), 1
               ) if confidence_trend else 0.0,
               "most_popular_type": most_popular_type,
               "most_active_hour": most_active_hour,
               "error_count": error_count,
           },
       }
   ```

   **Key notes:**
   - Confidence extraction uses JSONB path operators (`reading_result['confidence']['score']`). This works on PostgreSQL but not SQLite, so a try/except fallback returns empty.
   - All queries filter by date range using `cast(created_at, Date) >= since`.
   - Error count comes from `oracle_audit_log.success == False`.
   - `most_popular_type` and `most_active_hour` are derived from the aggregated data.

**Checkpoint:**

- [ ] `GET /api/health/analytics` returns all 5 sections (readings_per_day, readings_by_type, confidence_trend, popular_hours, totals)
- [ ] `readings_per_day` groups correctly by date
- [ ] `readings_by_type` groups by sign_type column
- [ ] `popular_hours` groups by hour (0-23)
- [ ] Confidence trend has SQLite fallback (empty array, no crash)
- [ ] Endpoint requires admin scope
- [ ] `totals` includes total_readings, avg_confidence, most_popular_type, most_active_hour, error_count
- Verify: `grep -c "analytics" api/app/routers/health.py` -- should return 3+

STOP if checkpoint fails

---

### Phase 4: Frontend Types & API Client (~30 min)

**Tasks:**

1. Add TypeScript interfaces to `frontend/src/types/index.ts` (append after existing `HealthStatus` interface):

   ```typescript
   // ---- Admin Monitoring ----

   export interface ServiceStatus {
     status:
       | "healthy"
       | "unhealthy"
       | "degraded"
       | "not_connected"
       | "not_deployed"
       | "direct_mode"
       | "configured"
       | "not_configured"
       | "external";
     error?: string;
     mode?: string;
     type?: string;
     size_bytes?: number | null;
     used_memory_bytes?: number;
     used_memory_human?: string;
     note?: string;
     python_version?: string;
     version?: string;
   }

   export interface DetailedHealth {
     status: "healthy" | "degraded";
     timestamp: string;
     uptime_seconds: number;
     system: {
       platform: string;
       python_version: string;
       cpu_count: number;
       process_memory_mb: number;
     };
     services: Record<string, ServiceStatus>;
   }

   export interface AuditLogEntry {
     id: number;
     timestamp: string;
     action: string;
     resource_type: string | null;
     resource_id: number | null;
     success: boolean;
     ip_address: string | null;
     details: Record<string, unknown> | null;
     severity: "info" | "warning" | "error" | "critical";
   }

   export interface LogsResponse {
     logs: AuditLogEntry[];
     total: number;
     limit: number;
     offset: number;
     time_window_hours: number;
   }

   export interface ReadingsPerDay {
     date: string;
     count: number;
   }

   export interface ReadingsByType {
     type: string;
     count: number;
   }

   export interface ConfidenceTrend {
     date: string;
     avg_confidence: number;
   }

   export interface PopularHour {
     hour: number;
     count: number;
   }

   export interface AnalyticsResponse {
     period_days: number;
     readings_per_day: ReadingsPerDay[];
     readings_by_type: ReadingsByType[];
     confidence_trend: ConfidenceTrend[];
     popular_hours: PopularHour[];
     totals: {
       total_readings: number;
       avg_confidence: number;
       most_popular_type: string | null;
       most_active_hour: number | null;
       error_count: number;
     };
   }
   ```

2. Add API methods to `frontend/src/services/api.ts` (append after existing `learning` namespace):

   ```typescript
   // ---- Admin Health (admin-only) ----

   export const adminHealth = {
     detailed: () =>
       request<import("@/types").DetailedHealth>("/health/detailed"),
     logs: (params?: {
       limit?: number;
       offset?: number;
       severity?: string;
       action?: string;
       search?: string;
       hours?: number;
       success?: boolean;
     }) => {
       const query = new URLSearchParams();
       if (params?.limit) query.set("limit", String(params.limit));
       if (params?.offset) query.set("offset", String(params.offset));
       if (params?.severity) query.set("severity", params.severity);
       if (params?.action) query.set("action", params.action);
       if (params?.search) query.set("search", params.search);
       if (params?.hours) query.set("hours", String(params.hours));
       if (params?.success !== undefined)
         query.set("success", String(params.success));
       return request<import("@/types").LogsResponse>(`/health/logs?${query}`);
     },
     analytics: (days?: number) =>
       request<import("@/types").AnalyticsResponse>(
         `/health/analytics${days ? `?days=${days}` : ""}`,
       ),
   };
   ```

**Checkpoint:**

- [ ] All TypeScript interfaces match API response structures exactly
- [ ] `adminHealth.detailed()`, `.logs()`, `.analytics()` methods exist in api.ts
- [ ] Query parameter serialization handles all optional filters
- [ ] No TypeScript compilation errors: `cd frontend && npx tsc --noEmit`
- Verify: `grep -c "adminHealth" frontend/src/services/api.ts` -- should return 1+

STOP if checkpoint fails

---

### Phase 5: Frontend -- HealthDashboard Component (~60 min)

**Tasks:**

1. Create `frontend/src/components/admin/HealthDashboard.tsx`:

   **Key elements:**
   - `StatusIndicator` sub-component: renders a colored dot based on service status
     - `healthy` -> `bg-green-500`
     - `unhealthy` -> `bg-red-500`
     - `degraded` -> `bg-yellow-500`
     - `not_connected` / `not_deployed` / `not_configured` -> `bg-gray-400`
     - `direct_mode` / `configured` / `external` -> `bg-blue-400`

   - `ServiceCard` sub-component: renders a card per service with name, status indicator, status text, optional error message, optional mode/memory info

   - `formatUptime(seconds: number)` helper: formats seconds into `Xd Yh Zm` string

   - Main `HealthDashboard` component:
     - `useState<DetailedHealth | null>` for health data
     - `useState<boolean>(true)` for loading state
     - `useState<string | null>` for error state
     - `useState<Date | null>` for last refresh timestamp
     - `useEffect` with `setInterval(fetchHealth, 10000)` for auto-refresh (10 seconds)
     - `useCallback` for `fetchHealth` function that calls `adminHealth.detailed()`
     - Manual refresh button

   **Layout structure:**

   ```
   +-----------------------------------------------------------+
   |  [Overall Status Badge]  Uptime: 2d 5h 30m                |
   |  Memory: 245.3 MB  |  CPUs: 4  |  Python 3.11.8          |
   +-----------------------------------------------------------+
   |  +----------+  +----------+  +----------+  +----------+   |
   |  |   API    |  | Database |  |  Redis   |  |  Oracle  |   |
   |  |  * OK    |  |  * OK    |  |  * 12MB  |  |  * gRPC  |   |
   |  +----------+  +----------+  +----------+  +----------+   |
   |  +----------+  +----------+  +----------+                  |
   |  | Scanner  |  | Telegram |  |  Nginx   |                  |
   |  | * Stub   |  | * Config |  | * Extern |                  |
   |  +----------+  +----------+  +----------+                  |
   +-----------------------------------------------------------+
   |  Last refresh: 10:30:05  [Refresh Now]                     |
   +-----------------------------------------------------------+
   ```

   - Use Tailwind classes consistent with existing `StatsCard.tsx` pattern: `bg-nps-bg-card`, `border-nps-border`, `text-nps-text-bright`, `text-nps-text-dim`
   - Service cards use a 2x4 grid on md+ screens (`grid grid-cols-2 md:grid-cols-4 gap-4`)
   - Loading state shows skeleton cards
   - Error state shows error message with retry button

2. Handle states:
   - **Loading:** Gray skeleton cards with pulse animation
   - **Error:** Red error banner with "Failed to fetch health data" + retry button
   - **Success:** Full service card grid + system info bar

**Checkpoint:**

- [ ] `HealthDashboard.tsx` renders all 7 service status cards
- [ ] Auto-refresh every 10 seconds with `setInterval`
- [ ] Manual refresh button triggers immediate `fetchHealth()`
- [ ] Color-coded status indicators match service status values
- [ ] Uptime formatted as human-readable string (Xd Yh Zm)
- [ ] Memory + CPU count + Python version displayed in system info bar
- [ ] Loading and error states handled gracefully
- Verify: `test -f frontend/src/components/admin/HealthDashboard.tsx && echo "Component OK"`

STOP if checkpoint fails

---

### Phase 6: Frontend -- LogViewer Component (~60 min)

**Tasks:**

1. Create `frontend/src/components/admin/LogViewer.tsx`:

   **Key elements:**
   - `SEVERITY_COLORS` constant mapping severity to Tailwind classes:
     - `info` -> `bg-blue-500/20 text-blue-400`
     - `warning` -> `bg-yellow-500/20 text-yellow-400`
     - `error` -> `bg-red-500/20 text-red-400`
     - `critical` -> `bg-red-700/20 text-red-300`

   - `SeverityBadge` sub-component: renders a `<span>` with severity name and color

   - `PAGE_SIZE = 25` constant

   - Main `LogViewer` component state:
     - `logs: AuditLogEntry[]`
     - `total: number`
     - `offset: number`
     - `loading: boolean`
     - `severity: string` (filter -- empty string = "all")
     - `search: string` (filter -- text search with 500ms debounce)
     - `hours: number` (time window -- default 24)
     - `expandedId: number | null` (which log entry is expanded)

   - Filter bar:
     - Severity dropdown: `<select>` with options All, Info, Warning, Error, Critical
     - Search input: `<input>` with 500ms debounce via `setTimeout` in `useEffect`
     - Time window dropdown: `<select>` with options 1h, 6h, 24h, 7d (168h), 30d (720h)
     - Refresh button

   - Log table columns: Timestamp | Severity | Action | Resource | Status | IP

   - Expandable detail: clicking a row toggles `expandedId`, showing the `details` JSON in a `<pre>` block with `font-mono bg-gray-900 p-3 rounded text-xs`

   - Pagination: Previous/Next buttons with "Showing X-Y of Z" counter

   - Reset offset to 0 when filters change (useEffect dependency on severity, search, hours)

   **Layout:**

   ```
   +-----------------------------------------------------------+
   | Severity: [All v]  Search: [________]  Window: [24h v]    |
   |                                              [Refresh]     |
   +-----------------------------------------------------------+
   | Time      | Sev    | Action             | Resource  | IP   |
   +-----------+--------+--------------------+-----------+------+
   | 10:30:05  | INFO   | reading.create     | reading   | 192. |
   | 10:29:42  | ERROR  | auth.failed        | -         | 10.  |
   |   v (expanded)                                             |
   |   {"reason": "invalid_token", "attempt": 3}               |
   | 10:28:15  | WARN   | user.delete        | user      | 192. |
   +-----------------------------------------------------------+
   | Showing 1-25 of 150  |  [<- Prev]  [Next ->]              |
   +-----------------------------------------------------------+
   ```

   - Timestamps format: `HH:MM:SS` for today, `MMM DD HH:MM` for older entries. Use `Intl.DateTimeFormat`.
   - Monospace font for the log table: `font-mono text-sm`

**Checkpoint:**

- [ ] `LogViewer.tsx` renders paginated log entries in a table
- [ ] Severity filter dropdown with options: All, Info, Warning, Error, Critical
- [ ] Search input with 500ms debounce
- [ ] Time window dropdown: 1h, 6h, 24h, 7d, 30d
- [ ] Pagination with prev/next buttons and count indicator
- [ ] Expandable detail rows show JSON in `<pre>` block
- [ ] Severity badges are color-coded
- [ ] Offset resets to 0 when filters change
- Verify: `test -f frontend/src/components/admin/LogViewer.tsx && echo "Component OK"`

STOP if checkpoint fails

---

### Phase 7: Frontend -- AnalyticsCharts Component (~60 min)

**Tasks:**

1. Install `recharts` charting library:

   ```bash
   cd frontend && npm install recharts
   ```

   **Why recharts:**
   - Built for React (uses React components as chart elements, not DOM manipulation)
   - Pure SVG rendering (no canvas, no WebGL -- works everywhere including SSR)
   - ~200KB gzipped (reasonable for an admin panel)
   - Supports BarChart, LineChart, PieChart, AreaChart (all needed here)
   - Active maintenance, TypeScript types included (`@types/recharts` bundled)
   - No additional peer dependencies beyond React

2. Create `frontend/src/components/admin/AnalyticsCharts.tsx`:

   **Key elements:**
   - `CHART_COLORS` array: `["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"]`
   - `POLL_INTERVAL = 30_000` (30 seconds)
   - State: `analytics: AnalyticsResponse | null`, `loading: boolean`, `days: number` (default 30)
   - `useEffect` with `setInterval(fetchAnalytics, POLL_INTERVAL)` for auto-refresh
   - Period selector: dropdown with options 7d, 14d, 30d, 90d, 365d

   **Chart 1: Readings Per Day (BarChart):**

   ```tsx
   <ResponsiveContainer width="100%" height={250}>
     <BarChart data={analytics.readings_per_day}>
       <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
       <XAxis
         dataKey="date"
         tick={{ fill: "#9ca3af", fontSize: 11 }}
         tickFormatter={(v: string) => v.slice(5)} // "MM-DD"
       />
       <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} />
       <Tooltip
         contentStyle={{
           backgroundColor: "#1f2937",
           border: "1px solid #374151",
         }}
         labelStyle={{ color: "#e5e7eb" }}
       />
       <Bar dataKey="count" fill="#3b82f6" radius={[2, 2, 0, 0]} />
     </BarChart>
   </ResponsiveContainer>
   ```

   **Chart 2: Readings By Type (PieChart):**

   ```tsx
   <ResponsiveContainer width="100%" height={250}>
     <PieChart>
       <Pie
         data={analytics.readings_by_type}
         dataKey="count"
         nameKey="type"
         cx="50%"
         cy="50%"
         outerRadius={80}
         label={({ type, count }: { type: string; count: number }) =>
           `${type}: ${count}`
         }
       >
         {analytics.readings_by_type.map((_, idx) => (
           <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
         ))}
       </Pie>
       <Tooltip
         contentStyle={{
           backgroundColor: "#1f2937",
           border: "1px solid #374151",
         }}
       />
       <Legend />
     </PieChart>
   </ResponsiveContainer>
   ```

   **Chart 3: Confidence Trend (LineChart):**

   ```tsx
   <ResponsiveContainer width="100%" height={250}>
     <LineChart data={analytics.confidence_trend}>
       <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
       <XAxis
         dataKey="date"
         tick={{ fill: "#9ca3af", fontSize: 11 }}
         tickFormatter={(v: string) => v.slice(5)}
       />
       <YAxis domain={[0, 100]} tick={{ fill: "#9ca3af", fontSize: 11 }} />
       <Tooltip
         contentStyle={{
           backgroundColor: "#1f2937",
           border: "1px solid #374151",
         }}
         formatter={(value: number) => [`${value.toFixed(1)}%`, "Confidence"]}
       />
       <Line
         type="monotone"
         dataKey="avg_confidence"
         stroke="#10b981"
         strokeWidth={2}
         dot={{ r: 3, fill: "#10b981" }}
       />
     </LineChart>
   </ResponsiveContainer>
   ```

   **Chart 4: Popular Hours (BarChart):**

   Fill all 24 hours (0-23) even if some have 0 readings:

   ```tsx
   const hoursData = Array.from({ length: 24 }, (_, hour) => {
     const found = analytics.popular_hours.find((h) => h.hour === hour);
     return { hour: `${hour}:00`, count: found?.count ?? 0 };
   });

   <ResponsiveContainer width="100%" height={250}>
     <BarChart data={hoursData}>
       <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
       <XAxis dataKey="hour" tick={{ fill: "#9ca3af", fontSize: 10 }} />
       <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} />
       <Tooltip
         contentStyle={{
           backgroundColor: "#1f2937",
           border: "1px solid #374151",
         }}
       />
       <Bar dataKey="count" fill="#f59e0b" radius={[2, 2, 0, 0]} />
     </BarChart>
   </ResponsiveContainer>;
   ```

   **Summary totals row** above charts (uses `StatsCard` pattern):

   ```
   Total Readings: 112  |  Avg Confidence: 73.2%  |  Top Type: time  |  Peak Hour: 14:00  |  Errors: 5
   ```

   **Layout (2x2 grid on md+ screens):**

   ```
   +----------------------------+----------------------------+
   |  Readings Per Day (Bar)    |  Readings By Type (Pie)    |
   +----------------------------+----------------------------+
   |  Confidence Trend (Line)   |  Popular Hours (Bar)       |
   +----------------------------+----------------------------+
   ```

   Use `grid grid-cols-1 md:grid-cols-2 gap-6`. Each chart wrapped in a card: `bg-nps-bg-card border border-nps-border rounded-lg p-4`.

   **Empty state:** When no readings exist, show "No reading data available" with a neutral icon/message instead of empty charts.

**Checkpoint:**

- [ ] `recharts` installed in `frontend/package.json` under `dependencies` (not devDependencies)
- [ ] `AnalyticsCharts.tsx` renders 4 charts in a 2x2 grid
- [ ] Bar chart for readings/day with "MM-DD" date labels
- [ ] Pie chart for readings by type with legend and labels
- [ ] Line chart for confidence trend with 0-100% Y-axis
- [ ] Bar chart for popular hours with all 24 hours filled (0:00 through 23:00)
- [ ] Period selector dropdown (7d, 14d, 30d, 90d, 365d)
- [ ] Auto-refresh every 30 seconds
- [ ] Summary totals row above charts
- [ ] Empty state handled gracefully
- Verify: `test -f frontend/src/components/admin/AnalyticsCharts.tsx && grep -q "recharts" frontend/package.json && echo "Charts OK"`

STOP if checkpoint fails

---

### Phase 8: Frontend -- AdminMonitoring Page & Routing (~30 min)

**Tasks:**

1. Create `frontend/src/pages/AdminMonitoring.tsx`:

   ```typescript
   import { useState } from "react";
   import { HealthDashboard } from "@/components/admin/HealthDashboard";
   import { LogViewer } from "@/components/admin/LogViewer";
   import { AnalyticsCharts } from "@/components/admin/AnalyticsCharts";

   type MonitoringTab = "health" | "logs" | "analytics";

   const TABS: { id: MonitoringTab; label: string }[] = [
     { id: "health", label: "Health" },
     { id: "logs", label: "Logs" },
     { id: "analytics", label: "Analytics" },
   ];

   export function AdminMonitoring() {
     const [activeTab, setActiveTab] = useState<MonitoringTab>("health");

     return (
       <div className="space-y-6">
         <div className="flex items-center justify-between">
           <h2 className="text-xl font-bold text-nps-text-bright">
             System Monitoring
           </h2>
         </div>

         {/* Tab navigation */}
         <div className="flex space-x-1 bg-nps-bg-card rounded-lg p-1 border border-nps-border">
           {TABS.map((tab) => (
             <button
               key={tab.id}
               onClick={() => setActiveTab(tab.id)}
               className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                 activeTab === tab.id
                   ? "bg-blue-600 text-white"
                   : "text-nps-text-dim hover:text-nps-text-bright hover:bg-nps-bg-card/50"
               }`}
             >
               {tab.label}
             </button>
           ))}
         </div>

         {/* Tab content */}
         {activeTab === "health" && <HealthDashboard />}
         {activeTab === "logs" && <LogViewer />}
         {activeTab === "analytics" && <AnalyticsCharts />}
       </div>
     );
   }
   ```

2. **Route registration:**

   Session 38 creates admin routing under `/admin/*`. The monitoring page goes at `/admin/monitoring`. Follow whatever pattern Session 38 established:
   - If Session 38 uses nested routes with `AdminGuard`:
     ```tsx
     <Route
       path="/admin/monitoring"
       element={
         <AdminGuard>
           <AdminMonitoring />
         </AdminGuard>
       }
     />
     ```
   - If Session 38 uses a sub-router inside `Admin.tsx` with `<Outlet>`:
     ```tsx
     <Route path="monitoring" element={<AdminMonitoring />} />
     ```

   Update `frontend/src/App.tsx` (or Session 38's admin router) to include:

   ```typescript
   import { AdminMonitoring } from "./pages/AdminMonitoring";
   // Add route inside admin route group
   ```

3. **Navigation link:** Add a "Monitoring" link to whatever admin navigation Session 38 established (sidebar, tab bar, or menu).

**Checkpoint:**

- [ ] `AdminMonitoring.tsx` exists with 3-tab navigation (Health, Logs, Analytics)
- [ ] Tab switching renders correct component for each tab
- [ ] Route `/admin/monitoring` registered and protected by admin guard
- [ ] Navigation link to monitoring exists in admin area
- Verify: `test -f frontend/src/pages/AdminMonitoring.tsx && echo "Page OK"`

STOP if checkpoint fails

---

### Phase 9: Update Simple Dashboard (~20 min)

**Tasks:**

1. Modify `devops/dashboards/simple_dashboard.py`:

   Add NPS API proxy capability alongside existing Oracle sidecar proxy:

   ```python
   API_URL = os.environ.get("NPS_API_URL", "http://api:8000")
   API_TOKEN = os.environ.get("NPS_API_TOKEN", "")

   def _fetch_api_json(path, timeout=5):
       """Fetch JSON from NPS API with auth header."""
       url = f"{API_URL}{path}"
       try:
           req = urllib.request.Request(url)
           if API_TOKEN:
               req.add_header("Authorization", f"Bearer {API_TOKEN}")
           with urllib.request.urlopen(req, timeout=timeout) as resp:
               return json.loads(resp.read().decode("utf-8"))
       except Exception as e:
           logger.debug("Failed to fetch %s: %s", url, e)
           return None
   ```

   Update the `/api/status` route to include detailed health:

   ```python
   @app.route("/api/status")
   def api_status():
       """Proxy health + metrics from Oracle sidecar and NPS API."""
       health = _fetch_json("/health")
       metrics = _fetch_json("/metrics")
       detailed = _fetch_api_json("/api/health/detailed")

       if health is None:
           health = {"status": "unreachable", "checks": {}}
       if metrics is None:
           metrics = {"rpcs": {}, "errors": {"total_count": 0, "rate_percent": 0}}

       return jsonify({
           "health": health,
           "metrics": metrics,
           "detailed": detailed or {},
       })
   ```

2. Update `devops/dashboards/templates/dashboard.html`:

   Add a "System Info" section below the Engine Health section that displays:
   - Platform, Python version, CPU count, process memory (from `detailed.system`)
   - Individual service status cards (from `detailed.services`)
   - Uptime (from `detailed.uptime_seconds`)

   Use the same dark-theme CSS classes already in `devops/dashboards/static/style.css`.

   Add JavaScript to the `refresh()` function to populate the new section from `data.detailed`.

**Checkpoint:**

- [ ] `simple_dashboard.py` has `_fetch_api_json()` function for NPS API requests
- [ ] `/api/status` route returns `detailed` key alongside `health` and `metrics`
- [ ] Auth token passed via `NPS_API_TOKEN` env var
- [ ] Dashboard HTML displays system info section when detailed data is available
- Verify: `grep -c "NPS_API_URL\|_fetch_api_json\|detailed" devops/dashboards/simple_dashboard.py` -- should return 4+

STOP if checkpoint fails

---

### Phase 10: Tests (~60 min)

**Tasks:**

1. Create `api/tests/test_health_admin.py` with 18 tests:

   ```python
   """Tests for admin-only health monitoring endpoints."""

   import pytest


   # ---- /api/health/detailed ----

   @pytest.mark.asyncio
   async def test_detailed_health_admin(client):
       """Admin can access detailed health with all service statuses."""
       response = await client.get("/api/health/detailed")
       assert response.status_code == 200
       data = response.json()
       assert "services" in data
       assert "system" in data
       assert "uptime_seconds" in data
       assert data["system"]["cpu_count"] > 0
       assert "api" in data["services"]
       assert "database" in data["services"]
       assert "redis" in data["services"]
       assert "oracle_service" in data["services"]
       assert "scanner_service" in data["services"]
       assert "telegram" in data["services"]
       assert "nginx" in data["services"]

   @pytest.mark.asyncio
   async def test_detailed_health_forbidden(readonly_client):
       """Non-admin (readonly) gets 403 on detailed health."""
       response = await readonly_client.get("/api/health/detailed")
       assert response.status_code == 403

   @pytest.mark.asyncio
   async def test_detailed_health_unauth(unauth_client):
       """Unauthenticated user gets 401 or 403 on detailed health."""
       response = await unauth_client.get("/api/health/detailed")
       assert response.status_code in (401, 403)

   @pytest.mark.asyncio
   async def test_detailed_health_system_info(client):
       """Detailed health includes system info fields."""
       response = await client.get("/api/health/detailed")
       data = response.json()
       system = data["system"]
       assert "platform" in system
       assert "python_version" in system
       assert "cpu_count" in system
       assert "process_memory_mb" in system
       assert isinstance(system["cpu_count"], int)
       assert system["cpu_count"] > 0


   # ---- /api/health/logs ----

   @pytest.mark.asyncio
   async def test_logs_endpoint(client):
       """Logs endpoint returns paginated structure."""
       response = await client.get("/api/health/logs")
       assert response.status_code == 200
       data = response.json()
       assert "logs" in data
       assert "total" in data
       assert "limit" in data
       assert "offset" in data
       assert "time_window_hours" in data
       assert isinstance(data["logs"], list)

   @pytest.mark.asyncio
   async def test_logs_severity_filter(client):
       """Severity=error returns only error/critical entries."""
       response = await client.get("/api/health/logs?severity=error")
       assert response.status_code == 200
       data = response.json()
       for log in data["logs"]:
           assert log["severity"] in ("error", "critical")

   @pytest.mark.asyncio
   async def test_logs_search_filter(client):
       """Search parameter filters logs without error."""
       response = await client.get("/api/health/logs?search=auth")
       assert response.status_code == 200

   @pytest.mark.asyncio
   async def test_logs_time_window(client):
       """Hours parameter is reflected in response."""
       response = await client.get("/api/health/logs?hours=1")
       assert response.status_code == 200
       data = response.json()
       assert data["time_window_hours"] == 1

   @pytest.mark.asyncio
   async def test_logs_pagination(client):
       """Limit and offset parameters work."""
       response = await client.get("/api/health/logs?limit=5&offset=0")
       assert response.status_code == 200
       data = response.json()
       assert data["limit"] == 5
       assert data["offset"] == 0

   @pytest.mark.asyncio
   async def test_logs_forbidden(readonly_client):
       """Non-admin gets 403 on logs."""
       response = await readonly_client.get("/api/health/logs")
       assert response.status_code == 403

   @pytest.mark.asyncio
   async def test_logs_empty_search(client):
       """Search for nonexistent term returns empty results."""
       response = await client.get("/api/health/logs?search=xyznonexistent&hours=1")
       assert response.status_code == 200
       data = response.json()
       assert data["total"] == 0
       assert data["logs"] == []


   # ---- /api/health/analytics ----

   @pytest.mark.asyncio
   async def test_analytics_endpoint(client):
       """Analytics returns all expected sections."""
       response = await client.get("/api/health/analytics")
       assert response.status_code == 200
       data = response.json()
       assert "readings_per_day" in data
       assert "readings_by_type" in data
       assert "confidence_trend" in data
       assert "popular_hours" in data
       assert "totals" in data
       assert isinstance(data["readings_per_day"], list)
       assert isinstance(data["readings_by_type"], list)

   @pytest.mark.asyncio
   async def test_analytics_custom_period(client):
       """Days parameter adjusts time range."""
       response = await client.get("/api/health/analytics?days=7")
       assert response.status_code == 200
       data = response.json()
       assert data["period_days"] == 7

   @pytest.mark.asyncio
   async def test_analytics_forbidden(readonly_client):
       """Non-admin gets 403 on analytics."""
       response = await readonly_client.get("/api/health/analytics")
       assert response.status_code == 403

   @pytest.mark.asyncio
   async def test_analytics_totals_structure(client):
       """Totals dict has all expected keys."""
       response = await client.get("/api/health/analytics")
       assert response.status_code == 200
       totals = response.json()["totals"]
       assert "total_readings" in totals
       assert "avg_confidence" in totals
       assert "most_popular_type" in totals
       assert "most_active_hour" in totals
       assert "error_count" in totals

   @pytest.mark.asyncio
   async def test_analytics_empty_database(client):
       """Empty DB returns empty arrays and zero totals."""
       response = await client.get("/api/health/analytics?days=1")
       assert response.status_code == 200
       data = response.json()
       assert data["totals"]["total_readings"] == 0
       assert data["readings_per_day"] == []
       assert data["readings_by_type"] == []


   # ---- Regression: existing endpoints still work ----

   @pytest.mark.asyncio
   async def test_basic_health_still_works(client):
       """Existing /api/health returns healthy (no regression)."""
       response = await client.get("/api/health")
       assert response.status_code == 200
       assert response.json()["status"] == "healthy"

   @pytest.mark.asyncio
   async def test_readiness_still_works(client):
       """Existing /api/health/ready returns checks (no regression)."""
       response = await client.get("/api/health/ready")
       assert response.status_code == 200
       assert "checks" in response.json()
   ```

   **Total: 18 API tests**

2. Create `frontend/src/tests/AdminMonitoring.test.tsx` (4 component render tests):

   ```typescript
   import { describe, it, expect, vi, beforeEach } from "vitest";
   import { render, screen } from "@testing-library/react";
   import { MemoryRouter } from "react-router-dom";

   // Mock API before importing components
   vi.mock("@/services/api", () => ({
     adminHealth: {
       detailed: vi.fn().mockResolvedValue({
         status: "healthy",
         timestamp: new Date().toISOString(),
         uptime_seconds: 3600,
         system: {
           platform: "Linux-5.15.0",
           python_version: "3.11.8",
           cpu_count: 4,
           process_memory_mb: 200.5,
         },
         services: {
           api: { status: "healthy", version: "4.0.0" },
           database: { status: "healthy", type: "postgresql" },
           redis: { status: "not_connected" },
           oracle_service: { status: "direct_mode", mode: "legacy" },
           scanner_service: { status: "not_deployed" },
           telegram: { status: "not_configured" },
           nginx: { status: "external" },
         },
       }),
       logs: vi.fn().mockResolvedValue({
         logs: [],
         total: 0,
         limit: 25,
         offset: 0,
         time_window_hours: 24,
       }),
       analytics: vi.fn().mockResolvedValue({
         period_days: 30,
         readings_per_day: [],
         readings_by_type: [],
         confidence_trend: [],
         popular_hours: [],
         totals: {
           total_readings: 0,
           avg_confidence: 0,
           most_popular_type: null,
           most_active_hour: null,
           error_count: 0,
         },
       }),
     },
   }));

   describe("AdminMonitoring", () => {
     it("renders tab navigation with Health, Logs, Analytics tabs", async () => {
       const { AdminMonitoring } = await import("@/pages/AdminMonitoring");
       render(
         <MemoryRouter>
           <AdminMonitoring />
         </MemoryRouter>
       );
       expect(screen.getByText("Health")).toBeDefined();
       expect(screen.getByText("Logs")).toBeDefined();
       expect(screen.getByText("Analytics")).toBeDefined();
     });
   });

   describe("HealthDashboard", () => {
     it("renders service status cards", async () => {
       const { HealthDashboard } = await import(
         "@/components/admin/HealthDashboard"
       );
       render(<HealthDashboard />);
       // Wait for async data
       await vi.waitFor(() => {
         expect(screen.getByText(/api/i)).toBeDefined();
         expect(screen.getByText(/database/i)).toBeDefined();
       });
     });
   });

   describe("LogViewer", () => {
     it("renders filter controls", async () => {
       const { LogViewer } = await import("@/components/admin/LogViewer");
       render(<LogViewer />);
       // Should have severity dropdown and search input
       expect(screen.getByRole("combobox") || screen.getByRole("textbox")).toBeDefined();
     });
   });

   describe("AnalyticsCharts", () => {
     it("renders period selector", async () => {
       const { AnalyticsCharts } = await import(
         "@/components/admin/AnalyticsCharts"
       );
       render(<AnalyticsCharts />);
       // Should have period dropdown
       await vi.waitFor(() => {
         expect(screen.getByText(/30/)).toBeDefined();
       });
     });
   });
   ```

   **Total: 4 frontend tests**

**Checkpoint:**

- [ ] `api/tests/test_health_admin.py` has 18 test functions
- [ ] `frontend/src/tests/AdminMonitoring.test.tsx` has 4 test cases
- [ ] All API tests pass: `cd api && python3 -m pytest tests/test_health_admin.py -v`
- [ ] Frontend tests pass: `cd frontend && npm test -- AdminMonitoring`
- [ ] Existing health tests still pass (no regression): `cd api && python3 -m pytest tests/test_health.py -v`
- Verify: `grep -c "async def test_" api/tests/test_health_admin.py` -- should return 18

STOP if checkpoint fails

---

### Phase 11: Final Verification & Quality (~15 min)

**Tasks:**

1. Run quality pipeline:

   ```bash
   cd api && python3 -m black . && python3 -m ruff check --fix .
   cd frontend && npx prettier --write src/ && npx eslint src/ --ext .ts,.tsx --fix
   ```

2. Run all tests:

   ```bash
   cd api && python3 -m pytest tests/ -v
   cd frontend && npm test
   ```

3. Verify no TypeScript errors:

   ```bash
   cd frontend && npx tsc --noEmit
   ```

4. Verify imports are clean:

   ```bash
   cd api && python3 -c "from app.routers.health import router; print('Health router OK')"
   ```

5. Verify recharts is in dependencies (not devDependencies):

   ```bash
   grep '"recharts"' frontend/package.json
   ```

6. Verify no new dependency security issues:

   ```bash
   cd frontend && npm audit --production
   ```

**Checkpoint:**

- [ ] Black + ruff pass with no errors
- [ ] Prettier + eslint pass with no errors
- [ ] TypeScript compiles with no errors (`tsc --noEmit`)
- [ ] All API tests pass
- [ ] All frontend tests pass
- [ ] No import errors
- [ ] `npm audit` shows no high/critical vulnerabilities from recharts

STOP if checkpoint fails

---

## TESTS TO WRITE

### `api/tests/test_health_admin.py`

| Test Function                      | Verifies                                                                    |
| ---------------------------------- | --------------------------------------------------------------------------- |
| `test_detailed_health_admin`       | Admin can access detailed health with all 7 service statuses                |
| `test_detailed_health_forbidden`   | Non-admin (readonly) gets 403                                               |
| `test_detailed_health_unauth`      | Unauthenticated gets 401/403                                                |
| `test_detailed_health_system_info` | System info includes platform, python_version, cpu_count, process_memory_mb |
| `test_logs_endpoint`               | Logs endpoint returns paginated structure with all expected keys            |
| `test_logs_severity_filter`        | Severity filter restricts results to matching entries                       |
| `test_logs_search_filter`          | Search filter works without error                                           |
| `test_logs_time_window`            | Hours parameter is reflected in response                                    |
| `test_logs_pagination`             | Limit and offset parameters work correctly                                  |
| `test_logs_forbidden`              | Non-admin gets 403 on logs                                                  |
| `test_logs_empty_search`           | Nonexistent search term returns empty results                               |
| `test_analytics_endpoint`          | Analytics returns all 5 sections                                            |
| `test_analytics_custom_period`     | Days parameter adjusts time range                                           |
| `test_analytics_forbidden`         | Non-admin gets 403 on analytics                                             |
| `test_analytics_totals_structure`  | Totals dict has all expected keys                                           |
| `test_analytics_empty_database`    | Empty DB returns empty arrays and zero totals                               |
| `test_basic_health_still_works`    | Existing `/api/health` returns healthy (no regression)                      |
| `test_readiness_still_works`       | Existing `/api/health/ready` returns checks (no regression)                 |

### `frontend/src/tests/AdminMonitoring.test.tsx`

| Test Function                              | Verifies                                           |
| ------------------------------------------ | -------------------------------------------------- |
| `AdminMonitoring: renders tab navigation`  | AdminMonitoring shows Health, Logs, Analytics tabs |
| `HealthDashboard: renders service cards`   | HealthDashboard renders service status cards       |
| `LogViewer: renders filter controls`       | LogViewer shows filter dropdown and search input   |
| `AnalyticsCharts: renders period selector` | AnalyticsCharts shows period dropdown              |

**Total: 22 tests minimum**

---

## ACCEPTANCE CRITERIA

- [ ] `GET /api/health/detailed` returns all 7 service statuses (api, database, redis, oracle_service, scanner_service, telegram, nginx)
- [ ] `GET /api/health/detailed` includes system info: platform, python_version, cpu_count, process_memory_mb
- [ ] `GET /api/health/detailed` includes uptime_seconds
- [ ] `GET /api/health/logs` returns paginated audit log entries with derived severity
- [ ] `GET /api/health/logs` supports severity, search, hours, success, action, resource_type filters
- [ ] `GET /api/health/analytics` returns readings_per_day, readings_by_type, confidence_trend, popular_hours, totals
- [ ] All 3 new endpoints require `admin` scope (non-admin gets 403)
- [ ] Existing `/api/health` and `/api/health/ready` still work unauthenticated (for Docker probes)
- [ ] `AdminMonitoring.tsx` page exists with 3 tabs (Health, Logs, Analytics)
- [ ] `HealthDashboard.tsx` renders 7 service cards with color-coded status indicators
- [ ] `HealthDashboard.tsx` auto-refreshes every 10 seconds
- [ ] `HealthDashboard.tsx` has manual refresh button
- [ ] `LogViewer.tsx` renders filterable, paginated log table
- [ ] `LogViewer.tsx` has expandable detail rows showing JSON
- [ ] `LogViewer.tsx` has severity filter, search input, time window selector
- [ ] `AnalyticsCharts.tsx` renders 4 charts using recharts (2 bar, 1 pie, 1 line)
- [ ] `AnalyticsCharts.tsx` has period selector (7d, 14d, 30d, 90d, 365d)
- [ ] `AnalyticsCharts.tsx` auto-refreshes every 30 seconds
- [ ] `recharts` installed as a production dependency in `frontend/package.json`
- [ ] Route `/admin/monitoring` is protected by AdminGuard (Session 38)
- [ ] `AuditService.query_logs_extended()` method exists with search, success, hours filters
- [ ] `devops/dashboards/simple_dashboard.py` fetches and displays detailed health info
- [ ] All 18 API tests pass
- [ ] All 4 frontend tests pass
- [ ] No TypeScript compilation errors
- Verify all:
  ```bash
  test -f frontend/src/pages/AdminMonitoring.tsx && \
  test -f frontend/src/components/admin/HealthDashboard.tsx && \
  test -f frontend/src/components/admin/LogViewer.tsx && \
  test -f frontend/src/components/admin/AnalyticsCharts.tsx && \
  test -f api/tests/test_health_admin.py && \
  grep -q "detailed" api/app/routers/health.py && \
  grep -q "recharts" frontend/package.json && \
  grep -q "adminHealth" frontend/src/services/api.ts && \
  grep -q "query_logs_extended" api/app/services/audit.py && \
  echo "ALL ACCEPTANCE CRITERIA VERIFIABLE"
  ```

---

## ERROR SCENARIOS

| Scenario                                              | Expected Behavior                                                                                            |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Non-admin calls `/api/health/detailed`                | 403 Forbidden with "Insufficient scope: requires 'admin'"                                                    |
| Non-admin calls `/api/health/logs`                    | 403 Forbidden                                                                                                |
| Non-admin calls `/api/health/analytics`               | 403 Forbidden                                                                                                |
| Unauthenticated request to any admin health endpoint  | 401 Unauthorized                                                                                             |
| Database is down when `/api/health/detailed` called   | Returns `database: {status: "unhealthy", error: "..."}`, overall status "degraded"                           |
| Redis is down when `/api/health/detailed` called      | Returns `redis: {status: "unhealthy", error: "..."}`, overall status still "healthy" (Redis is non-critical) |
| Oracle gRPC not connected                             | Returns `oracle_service: {status: "direct_mode", mode: "legacy"}`                                            |
| Empty audit log table when requesting logs            | Returns `{logs: [], total: 0}`                                                                               |
| No readings in database when requesting analytics     | Returns empty arrays and zero totals -- no crash                                                             |
| SQLite test environment (no JSONB support)            | Confidence trend query falls back to empty array via try/except                                              |
| Invalid severity filter value (e.g., "debug")         | Returns empty logs list (no entries match derived severity "debug")                                          |
| hours=0 or hours=-1 for logs                          | FastAPI validation rejects with 422 (ge=1 constraint)                                                        |
| days=0 or days=-1 for analytics                       | FastAPI validation rejects with 422 (ge=1 constraint)                                                        |
| days=500 for analytics                                | FastAPI validation rejects with 422 (le=365 constraint)                                                      |
| `resource` module unavailable (Windows dev)           | `_get_process_memory_mb()` returns 0.0 with graceful fallback                                                |
| `pg_database_size()` fails (insufficient permissions) | Database check still reports healthy, size_bytes=null                                                        |
| Frontend chart library fails to render (missing data) | Charts show empty state message, page does not crash                                                         |
| API returns 500 during health fetch                   | HealthDashboard shows error state with "Failed to fetch health data" + retry button                          |
| Network timeout on log fetch                          | LogViewer shows "Failed to load logs" with retry option                                                      |

---

## DESIGN DECISIONS

| Decision                                                  | Choice                                                   | Rationale                                                                                                                                                                                                                                                                                                                                   |
| --------------------------------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Charting library                                          | `recharts`                                               | React-native (JSX components), pure SVG, lightweight (~200KB gzipped), TypeScript support, active maintenance. Alternatives considered: Chart.js (canvas-based, needs react-chartjs-2 wrapper -- extra dependency), D3 (too low-level for simple admin charts), inline SVG (too much custom code for 4 chart types), Nivo (heavier ~400KB). |
| New endpoints in existing router vs separate admin router | Extend existing `health.py`                              | All health/monitoring endpoints belong together semantically. Adding a separate `admin.py` router would split health-related functionality across files. The 3 existing unauthenticated endpoints remain unchanged for Docker probes.                                                                                                       |
| Severity derivation                                       | Derive from audit log properties (success + action name) | No separate severity column exists in `oracle_audit_log`. Adding one would require a new migration. Deriving from `success` boolean + action name patterns is accurate and requires zero schema changes.                                                                                                                                    |
| Log data source                                           | `oracle_audit_log` table via AuditService                | The audit log already captures all security and CRUD events with structured data. File-based logs (from `devops/logging/oracle.log`) are harder to query, filter, and paginate. The audit table is the queryable, indexed source of truth.                                                                                                  |
| Analytics aggregation                                     | Server-side SQL GROUP BY                                 | Efficient aggregation in the database. Sending raw rows to the frontend for JavaScript grouping would be wasteful for large datasets. SQL is the right tool for aggregate queries.                                                                                                                                                          |
| Confidence trend extraction                               | JSONB path in PostgreSQL with SQLite fallback            | Confidence lives in `reading_result` JSONB at `['confidence']['score']`. PostgreSQL's JSONB operators extract it efficiently. SQLite fallback returns empty array (acceptable for test environment).                                                                                                                                        |
| Auto-refresh intervals                                    | 10s health, 30s analytics                                | Health should be near-real-time for incident detection. Analytics is aggregated data that changes slowly -- 30s avoids unnecessary DB load while keeping data fresh.                                                                                                                                                                        |
| Tab navigation vs separate pages                          | Tabs within one page                                     | All monitoring views are related and used together during debugging. Tabs keep everything accessible without route changes. No need for deep-linking individual monitoring sections.                                                                                                                                                        |
| Process memory via `resource` module                      | stdlib only, no psutil                                   | Avoids adding a new external dependency. `resource.getrusage()` provides RSS memory on Unix/macOS. psutil would give more data (CPU %, per-process) but is an external package requiring approval.                                                                                                                                          |
| Simple dashboard update scope                             | Proxy new endpoint only                                  | The Flask dashboard already proxies Oracle sidecar. Adding a proxy for the NPS API detailed health is consistent and minimal. The React admin panel is the primary monitoring UI; the Flask dashboard is for quick server-room checks.                                                                                                      |

---

## HANDOFF

**Created:**

- `frontend/src/pages/AdminMonitoring.tsx` (monitoring page with 3-tab navigation)
- `frontend/src/components/admin/HealthDashboard.tsx` (7 service status cards with auto-refresh)
- `frontend/src/components/admin/LogViewer.tsx` (filterable, paginated audit log table)
- `frontend/src/components/admin/AnalyticsCharts.tsx` (4 recharts visualizations)
- `api/tests/test_health_admin.py` (18 tests)
- `frontend/src/tests/AdminMonitoring.test.tsx` (4 tests)

**Modified:**

- `api/app/routers/health.py` (3 new admin-only endpoints: `/detailed`, `/logs`, `/analytics` + helper functions)
- `api/app/services/audit.py` (new `query_logs_extended()` method)
- `frontend/src/services/api.ts` (new `adminHealth` namespace with 3 methods)
- `frontend/src/types/index.ts` (admin monitoring TypeScript interfaces: DetailedHealth, LogsResponse, AnalyticsResponse, etc.)
- `frontend/src/App.tsx` (admin monitoring route registration)
- `frontend/package.json` (`recharts` dependency added)
- `devops/dashboards/simple_dashboard.py` (NPS API proxy for detailed health)
- `devops/dashboards/templates/dashboard.html` (system info display section)

**Next session needs:**

- **Session 40 (Backup & Recovery)** depends on:
  - Admin monitoring infrastructure being stable (health endpoints working)
  - AdminGuard and admin routing established (Sessions 38-39)
  - Database connectivity verified through health checks
  - The `require_scope("admin")` pattern proven and tested for new admin endpoints
  - Monitoring page provides visibility into system health during backup/restore operations
- Session 40 may add a "Backup" tab to the AdminMonitoring page or create a separate `/admin/backups` page following the same routing pattern
- The `devops/dashboards/simple_dashboard.py` can be further extended in Session 40 to show backup status
- The `AuditService.query_logs_extended()` method can be reused to audit backup/restore operations
