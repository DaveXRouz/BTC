# SESSION 44 SPEC — Performance Optimization

**Block:** Testing & Deployment (Sessions 41-45)
**Estimated Duration:** 6-8 hours
**Complexity:** High
**Dependencies:** Sessions 41-43 (all tests passing, full stack operational)

---

## TL;DR

- Profile and optimize the full NPS stack to meet all 5 performance targets from CLAUDE.md
- API: Add Redis-backed response caching middleware, optimize SQLAlchemy connection pooling, add ETag/Cache-Control headers, add X-Response-Time header to all responses
- Database: Run EXPLAIN ANALYZE on all critical queries, add missing indexes via migration, tune PostgreSQL server parameters
- Frontend: Convert eager page imports to `React.lazy()` with Suspense, configure Vite manual chunk splitting for vendor separation, add resource preload hints
- Nginx: Add gzip compression, static asset caching headers, upstream keepalive connections, proxy buffering
- Benchmark: Enhance `perf_audit.py` with configurable iterations, warm-up rounds, p99 metric, concurrent request testing, baseline comparison; create dedicated `benchmark_readings.py` for focused reading throughput measurement with p50/p95/p99
- Verify all 5 targets: API simple < 50ms p95, API reading < 5s p95, frontend load < 2s, page transitions < 100ms, DB indexed < 100ms

---

## OBJECTIVES

1. **Meet API response time targets** -- simple endpoints < 50ms p95, reading generation < 5s p95, profile queries < 100ms indexed
2. **Meet frontend performance targets** -- initial load < 2 seconds, page transitions < 100ms, time to interactive < 3 seconds
3. **Meet database query targets** -- indexed queries < 100ms, full-text search < 500ms
4. **Build comprehensive benchmark tooling** -- `perf_audit.py` enhanced with warm-up, concurrency, p99; new `benchmark_readings.py` for focused reading throughput measurement
5. **Add caching infrastructure** -- Redis-backed API response cache with configurable TTL, ETag support, cache invalidation on writes, and graceful degradation when Redis is unavailable

---

## PREREQUISITES

- [ ] Sessions 41-43 complete -- full test suites passing (unit, integration, E2E)
- [ ] All 7 Docker services start successfully (`make up`)
- [ ] PostgreSQL has seed data loaded (at least 3 oracle_users, some oracle_readings)
- [ ] Redis is running and reachable on port 6379
- [ ] API server responds to `/api/health` with 200
- Verification:
  ```bash
  curl -s http://localhost:8000/api/health | python3 -c "import sys,json; d=json.load(sys.stdin); print('API OK' if d.get('status')=='ok' else 'API FAIL')"
  docker-compose exec redis redis-cli ping | grep -q PONG && echo "Redis OK"
  docker-compose exec postgres pg_isready -U nps && echo "PostgreSQL OK"
  ```

---

## PERFORMANCE TARGETS

### Primary Targets (from CLAUDE.md)

| Metric                    | Target      | Measurement Method                                         |
| ------------------------- | ----------- | ---------------------------------------------------------- |
| API response (simple)     | < 50ms p95  | `perf_audit.py` against `/api/health`, `/api/oracle/users` |
| API response (reading)    | < 5 seconds | `benchmark_readings.py` against `/api/oracle/reading`      |
| Frontend initial load     | < 2 seconds | Vite bundle size analysis + gzip transfer budget           |
| Frontend page transitions | < 100ms     | React.lazy chunk size analysis + manual testing            |
| Database query (indexed)  | < 100ms     | EXPLAIN ANALYZE on critical queries                        |

### Additional Targets (Session 44 scope)

| Metric                 | Target       | Rationale                                                |
| ---------------------- | ------------ | -------------------------------------------------------- |
| Frontend TTI           | < 3 seconds  | Time to interactive -- user can start clicking           |
| DB full-text search    | < 500ms      | Oracle user name search with LIKE patterns               |
| API p99 (simple)       | < 200ms      | Tail latency guard -- no single request egregiously slow |
| Vite production bundle | < 500KB gzip | Network transfer budget for initial load on broadband    |

---

## FILES TO CREATE

- `api/app/middleware/cache.py` -- Redis-backed HTTP response cache middleware with ETag support and cache invalidation
- `integration/scripts/benchmark_readings.py` -- Dedicated reading benchmark: N iterations, p50/p95/p99, warm-up, JSON output
- `api/tests/test_cache_middleware.py` -- 15+ tests for the cache middleware
- `database/migrations/XXX_performance_indexes.sql` -- Missing composite and partial indexes
- `database/migrations/XXX_performance_indexes_rollback.sql` -- Index rollback

## FILES TO MODIFY

- `integration/scripts/perf_audit.py` -- Add warm-up rounds, p99 metric, concurrent testing, CLI args, baseline comparison
- `api/app/database.py` -- Tune SQLAlchemy engine pool size, max overflow, pool recycle, pool pre-ping
- `api/app/main.py` -- Register cache middleware, add response timing header
- `api/app/config.py` -- Add cache TTL settings, connection pool size settings
- `frontend/src/App.tsx` -- Convert page imports to `React.lazy()` with `Suspense` fallback
- `frontend/vite.config.ts` -- Add `build.rollupOptions.output.manualChunks` for vendor splitting
- `infrastructure/nginx/nginx.conf` -- Add gzip, static asset caching, upstream keepalive, proxy buffering
- `docker-compose.yml` -- Add PostgreSQL shared_buffers/work_mem tuning via command args

## FILES TO DELETE

- None

---

## IMPLEMENTATION PHASES

### Phase 1: Baseline Measurement (~45 min)

**Tasks:**

1. Start the full stack and run the existing `perf_audit.py` to establish a performance baseline BEFORE any changes:

   ```bash
   make up
   sleep 10  # Wait for services to stabilize
   python3 integration/scripts/perf_audit.py
   ```

   Record the output. The script already saves to `integration/reports/performance_baseline.json`. Copy it to `integration/reports/performance_baseline_before.json` so it is preserved after the "after" run overwrites it.

2. Run EXPLAIN ANALYZE on all critical database queries manually via psql:

   ```sql
   -- Profile query: get user by ID (indexed)
   EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM oracle_users WHERE id = 1 AND deleted_at IS NULL;

   -- List query: paginated users with search
   EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM oracle_users
     WHERE deleted_at IS NULL
       AND (LOWER(name) LIKE LOWER('%test%') OR LOWER(name_persian) LIKE LOWER('%test%'))
     ORDER BY created_at DESC LIMIT 20 OFFSET 0;

   -- Count query (for pagination total)
   EXPLAIN (ANALYZE, BUFFERS) SELECT COUNT(*) FROM oracle_users WHERE deleted_at IS NULL;

   -- Reading query: list readings with filter
   EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM oracle_readings
     WHERE sign_type = 'reading' ORDER BY created_at DESC LIMIT 20 OFFSET 0;

   -- Audit log query
   EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM oracle_audit_log
     WHERE action = 'reading.created' ORDER BY created_at DESC LIMIT 50 OFFSET 0;

   -- Daily readings lookup
   EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM oracle_daily_readings
     WHERE user_id = 1 AND reading_date = CURRENT_DATE;
   ```

   For each query, record: execution time, whether it uses Index Scan vs Seq Scan, and buffer hits.

3. Measure frontend bundle size:

   ```bash
   cd frontend && npm run build
   ls -lh dist/assets/*.js dist/assets/*.css
   # Check gzipped sizes:
   for f in dist/assets/*.js dist/assets/*.css; do
       gzip -c "$f" | wc -c | awk -v f="$f" '{printf "%s: %.1f KB gzip\n", f, $1/1024}'
   done
   ```

   Record total JS bundle size (gzipped) and individual chunk sizes.

4. Document all baseline measurements for comparison in Phase 7.

**Checkpoint:**

- [ ] Baseline performance report copied to `integration/reports/performance_baseline_before.json`
- [ ] EXPLAIN ANALYZE results documented for all 6 critical queries
- [ ] Frontend bundle sizes recorded (total gzip KB)
- Verify: `test -f integration/reports/performance_baseline_before.json && echo "Baseline OK"`

STOP if baseline cannot be established (services not running)

---

### Phase 2: Database Optimization (~60 min)

**Tasks:**

1. **Add missing indexes** based on EXPLAIN ANALYZE results from Phase 1.

   Create `database/migrations/XXX_performance_indexes.sql` (use next available migration number):

   ```sql
   -- Migration XXX: Performance indexes
   -- Date: 2026-02-10
   -- Description: Add composite and partial indexes for query performance

   BEGIN;

   -- oracle_users: partial index for soft-delete filter (used in every query)
   CREATE INDEX IF NOT EXISTS idx_oracle_users_active
     ON oracle_users(id) WHERE deleted_at IS NULL;

   -- oracle_users: search by name (used in list endpoint LIKE query)
   CREATE INDEX IF NOT EXISTS idx_oracle_users_name_lower
     ON oracle_users(LOWER(name) varchar_pattern_ops);

   -- oracle_users: search by persian name
   CREATE INDEX IF NOT EXISTS idx_oracle_users_name_persian_lower
     ON oracle_users(LOWER(name_persian) varchar_pattern_ops)
     WHERE name_persian IS NOT NULL;

   -- oracle_users: ordering for paginated list
   CREATE INDEX IF NOT EXISTS idx_oracle_users_active_created
     ON oracle_users(created_at DESC) WHERE deleted_at IS NULL;

   -- oracle_readings: filter by sign_type + ordering
   CREATE INDEX IF NOT EXISTS idx_oracle_readings_sign_type_created
     ON oracle_readings(sign_type, created_at DESC);

   -- oracle_readings: user-specific reading lookup
   CREATE INDEX IF NOT EXISTS idx_oracle_readings_user_created
     ON oracle_readings(user_id, created_at DESC) WHERE user_id IS NOT NULL;

   -- oracle_audit_log: filter by action + ordering
   CREATE INDEX IF NOT EXISTS idx_oracle_audit_log_action_created
     ON oracle_audit_log(action, created_at DESC);

   -- oracle_audit_log: filter by resource
   CREATE INDEX IF NOT EXISTS idx_oracle_audit_log_resource
     ON oracle_audit_log(resource_type, resource_id)
     WHERE resource_id IS NOT NULL;

   COMMIT;
   ```

   **Decision rule:** Only add indexes that EXPLAIN ANALYZE from Phase 1 shows are needed (Seq Scan on a table with 100+ rows). If a query already uses an index, skip it. Each index has write overhead.

   Create matching rollback file `database/migrations/XXX_performance_indexes_rollback.sql`:

   ```sql
   BEGIN;
   DROP INDEX IF EXISTS idx_oracle_users_active;
   DROP INDEX IF EXISTS idx_oracle_users_name_lower;
   DROP INDEX IF EXISTS idx_oracle_users_name_persian_lower;
   DROP INDEX IF EXISTS idx_oracle_users_active_created;
   DROP INDEX IF EXISTS idx_oracle_readings_sign_type_created;
   DROP INDEX IF EXISTS idx_oracle_readings_user_created;
   DROP INDEX IF EXISTS idx_oracle_audit_log_action_created;
   DROP INDEX IF EXISTS idx_oracle_audit_log_resource;
   COMMIT;
   ```

2. **Tune SQLAlchemy connection pool** in `api/app/database.py`.

   Current engine creation uses minimal configuration (`pool_pre_ping=True` only). Add pool tuning:

   ```python
   eng = create_engine(
       url,
       pool_pre_ping=True,          # Already present
       pool_size=settings.db_pool_size,            # NEW: configurable (default 10)
       max_overflow=settings.db_max_overflow,       # NEW: configurable (default 20)
       pool_recycle=settings.db_pool_recycle,       # NEW: recycle after 30 min
       pool_timeout=30,              # NEW: wait up to 30s for connection
       echo=False,                   # Ensure SQL logging is off
   )
   ```

3. **Add pool settings to `api/app/config.py`** in the Settings class:

   ```python
   # Database pool
   db_pool_size: int = 10
   db_max_overflow: int = 20
   db_pool_recycle: int = 1800
   ```

4. **Add PostgreSQL server tuning** via `docker-compose.yml` command args.

   Update the postgres service to include tuning parameters:

   ```yaml
   postgres:
     image: postgres:15-alpine
     command:
       - "postgres"
       - "-c"
       - "shared_buffers=256MB"
       - "-c"
       - "work_mem=16MB"
       - "-c"
       - "effective_cache_size=512MB"
       - "-c"
       - "random_page_cost=1.1"
       - "-c"
       - "effective_io_concurrency=200"
       - "-c"
       - "max_connections=100"
   ```

   These values are tuned for the 1GB memory limit already set in docker-compose. `shared_buffers=256MB` is 25% of the container memory (standard recommendation). `random_page_cost=1.1` assumes SSD storage (Docker volumes typically run on SSD).

   **Important:** Only add the `command` block if it does not already exist. If it exists, merge the parameters.

5. **Apply the migration** and re-run EXPLAIN ANALYZE:

   ```bash
   docker-compose exec postgres psql -U nps -d nps -f /path/to/migration.sql
   ```

   Re-run the same 6 queries from Phase 1. All should now show Index Scan and execute in < 10ms.

**Checkpoint:**

- [ ] Migration file created with all indexes (using IF NOT EXISTS for idempotency)
- [ ] Rollback file drops all created indexes
- [ ] EXPLAIN ANALYZE shows Index Scan (not Seq Scan) for all critical queries
- [ ] SQLAlchemy pool configured with pool_size, max_overflow, pool_recycle from Settings
- [ ] Config settings for pool size are environment-variable driven
- [ ] PostgreSQL tuning parameters added to docker-compose.yml
- Verify: `grep "pool_size" api/app/database.py && grep "db_pool_size" api/app/config.py && echo "Pool config OK"`

STOP if EXPLAIN ANALYZE still shows sequential scans on tables with > 100 rows

---

### Phase 3: API Response Caching (~90 min)

**Tasks:**

1. **Create `api/app/middleware/cache.py`** -- Redis-backed HTTP cache middleware.

   Full implementation requirements:

   **Cache strategy per endpoint:**

   | Endpoint Pattern             | TTL      | Cache Key Components                    |
   | ---------------------------- | -------- | --------------------------------------- |
   | `GET /api/health`            | 10s      | Path only                               |
   | `GET /api/oracle/daily`      | 300s     | Path + date param + auth token prefix   |
   | `GET /api/oracle/users`      | 60s      | Path + query params + auth token prefix |
   | `GET /api/oracle/readings`   | 60s      | Path + query params + auth token prefix |
   | `GET /api/oracle/users/{id}` | 30s      | Path + auth token prefix                |
   | All POST/PUT/DELETE          | No cache | Mutations are never cached              |

   **Implementation details:**
   - **Cache key formula:** `nps:cache:{sha256(method + path + sorted_query_params + auth_prefix)}`
   - **Auth token prefix:** First 16 characters of Bearer token. Different users may see different data (ownership filtering), so cache entries must be per-user. Using a prefix (not the full token) keeps keys manageable.
   - **Storage format:** JSON-serialized dict with keys `body` (base64 response body), `status` (HTTP status code), `content_type`, `headers` (dict of response headers to preserve). Stored in Redis with TTL via `SETEX`.
   - **ETag support:** Compute `ETag` as MD5 hex digest of response body (MD5 is fine for ETag -- not security-sensitive). On incoming requests with `If-None-Match` header, compare against stored ETag. If match, return 304 Not Modified with no body.
   - **Cache invalidation on writes:** When a POST/PUT/DELETE to `/api/oracle/users*` or `/api/oracle/reading*` completes, delete related cache entries by pattern (`nps:cache:*oracle*users*` or `nps:cache:*oracle*reading*`). Use Redis `SCAN` + `DEL` (not `KEYS` in production -- but acceptable at our scale).
   - **Diagnostic headers:** Add `X-Cache: HIT` or `X-Cache: MISS` to every response. Add `X-Response-Time: {ms}ms` to every response for performance monitoring.
   - **Graceful degradation:** If `request.app.state.redis` is `None` (Redis unavailable), skip all caching logic entirely -- requests pass through to the normal handler. Never crash due to cache failure.
   - **Do NOT cache:** Responses with status >= 400, WebSocket connections, or any response with `Cache-Control: no-store` already set.

   **Class structure:**

   ```python
   """
   Response Cache Middleware -- Redis-backed HTTP caching with ETag support.

   Caches GET responses for configured paths with configurable TTL.
   Falls back gracefully to no caching when Redis is unavailable.
   """

   from __future__ import annotations

   import base64
   import hashlib
   import json
   import logging
   import time
   from typing import TYPE_CHECKING

   from fastapi import Request
   from starlette.middleware.base import BaseHTTPMiddleware
   from starlette.responses import JSONResponse, Response

   if TYPE_CHECKING:
       import redis.asyncio as aioredis

   logger = logging.getLogger(__name__)

   # Path prefix → TTL in seconds
   _CACHE_TTLS: dict[str, int] = {
       "/api/health": 10,
       "/api/oracle/daily": 300,
       "/api/oracle/users": 60,
       "/api/oracle/readings": 60,
   }

   _CACHE_PREFIX = "nps:cache:"


   class ResponseCacheMiddleware(BaseHTTPMiddleware):
       """Redis-backed response caching with ETag and cache invalidation."""

       async def dispatch(self, request: Request, call_next) -> Response:
           start = time.perf_counter()
           try:
               response = await self._handle(request, call_next)
           except Exception:
               logger.exception("Cache middleware error, passing through")
               response = await call_next(request)

           elapsed_ms = (time.perf_counter() - start) * 1000
           response.headers["X-Response-Time"] = f"{elapsed_ms:.1f}ms"
           return response

       async def _handle(self, request: Request, call_next) -> Response:
           # Only cache GET requests
           if request.method != "GET":
               response = await call_next(request)
               # Invalidate related caches on write operations
               if request.method in ("POST", "PUT", "DELETE"):
                   response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
                   await self._invalidate_related(request)
               return response

           # Check if this path is cacheable
           ttl = self._get_ttl(request.url.path)
           if ttl is None:
               return await call_next(request)

           redis = getattr(request.app.state, "redis", None)
           if redis is None:
               response = await call_next(request)
               response.headers["X-Cache"] = "BYPASS"
               return response

           cache_key = self._build_key(request)

           # Check If-None-Match (ETag)
           if_none_match = request.headers.get("if-none-match")

           # Try cache hit
           try:
               cached = await redis.get(cache_key)
           except Exception:
               cached = None

           if cached:
               entry = json.loads(cached)
               etag = entry.get("etag", "")
               if if_none_match and if_none_match.strip('"') == etag:
                   return Response(status_code=304, headers={
                       "ETag": f'"{etag}"',
                       "X-Cache": "HIT",
                   })
               body = base64.b64decode(entry["body"])
               return Response(
                   content=body,
                   status_code=entry["status"],
                   headers={
                       "Content-Type": entry["content_type"],
                       "Cache-Control": f"public, max-age={ttl}",
                       "ETag": f'"{etag}"',
                       "X-Cache": "HIT",
                   },
               )

           # Cache miss -- call downstream
           response = await call_next(request)

           # Only cache successful responses
           if response.status_code < 400:
               body = b""
               async for chunk in response.body_iterator:
                   body += chunk if isinstance(chunk, bytes) else chunk.encode()

               etag = hashlib.md5(body).hexdigest()

               entry = json.dumps({
                   "body": base64.b64encode(body).decode(),
                   "status": response.status_code,
                   "content_type": response.headers.get("content-type", "application/json"),
                   "etag": etag,
               })

               try:
                   await redis.setex(cache_key, ttl, entry)
               except Exception as e:
                   logger.warning("Cache write failed: %s", e)

               return Response(
                   content=body,
                   status_code=response.status_code,
                   headers={
                       **dict(response.headers),
                       "Cache-Control": f"public, max-age={ttl}",
                       "ETag": f'"{etag}"',
                       "X-Cache": "MISS",
                   },
               )

           response.headers["X-Cache"] = "SKIP"
           return response
   ```

2. **Add cache configuration to `api/app/config.py`:**

   ```python
   # Cache
   cache_enabled: bool = True
   cache_default_ttl: int = 60
   cache_health_ttl: int = 10
   cache_daily_ttl: int = 300
   cache_user_ttl: int = 30
   cache_list_ttl: int = 60
   ```

3. **Register cache middleware in `api/app/main.py`:**

   Add AFTER CORS middleware, BEFORE rate limiting. This ordering means:
   - CORS headers are always set (even on cached responses)
   - Cached responses bypass rate limit counting (they are served instantly)
   - Rate limiting still applies to cache misses

   ```python
   from app.middleware.cache import ResponseCacheMiddleware

   # Response caching (after CORS, before rate limit)
   if settings.cache_enabled:
       app.add_middleware(ResponseCacheMiddleware)
   ```

4. **X-Response-Time header** is already integrated in the middleware above (added to every response in the `dispatch` method). This allows the benchmark scripts to measure server-side processing time independently of network latency.

**Checkpoint:**

- [ ] `api/app/middleware/cache.py` exists with `ResponseCacheMiddleware` class
- [ ] GET `/api/health` returns `X-Cache: MISS` on first call, `X-Cache: HIT` on second
- [ ] GET `/api/health` returns `Cache-Control: public, max-age=10` and `ETag` headers
- [ ] Request with matching `If-None-Match` returns 304 Not Modified
- [ ] POST to any endpoint returns `Cache-Control: no-store`
- [ ] POST to `/api/oracle/users` invalidates user list cache entries
- [ ] Redis down = cache bypassed, requests still work (passthrough)
- [ ] `X-Response-Time` header present on all responses
- [ ] 4xx/5xx responses are NOT stored in cache
- Verify: `curl -v http://localhost:8000/api/health 2>&1 | grep -E "X-Cache|Cache-Control|ETag|X-Response-Time"`

STOP if cache middleware breaks existing endpoints (run `cd api && python3 -m pytest tests/ -v --tb=short`)

---

### Phase 4: Frontend Performance (~60 min)

**Tasks:**

1. **Determine page export style** before converting to lazy imports.

   Check whether pages use named exports or default exports:

   ```bash
   grep -n "export " frontend/src/pages/*.tsx | head -20
   ```

   The current `App.tsx` uses named imports: `import { Dashboard } from "./pages/Dashboard"` which means the pages use `export const Dashboard` (named export). `React.lazy()` requires a module with a default export. Two approaches:

   **Approach A (preferred -- no page modifications):** Use `.then()` adapter:

   ```typescript
   const Dashboard = React.lazy(() =>
     import("./pages/Dashboard").then((m) => ({ default: m.Dashboard })),
   );
   ```

   **Approach B:** Add `export default` to each page file. Requires modifying 6 page files.

   **Decision: Approach A** -- avoids touching 6 additional files and is the standard pattern for lazy-loading named exports.

2. **Convert `frontend/src/App.tsx`** to use lazy imports with Suspense:

   ```tsx
   import React, { Suspense, useEffect } from "react";
   import { Routes, Route, Navigate } from "react-router-dom";
   import { useTranslation } from "react-i18next";
   import { Layout } from "./components/Layout";

   // ================================================================
   // Lazy-loaded pages (code-split into separate chunks)
   // ================================================================

   const Dashboard = React.lazy(() =>
     import("./pages/Dashboard").then((m) => ({ default: m.Dashboard })),
   );
   const Scanner = React.lazy(() =>
     import("./pages/Scanner").then((m) => ({ default: m.Scanner })),
   );
   const Oracle = React.lazy(() =>
     import("./pages/Oracle").then((m) => ({ default: m.Oracle })),
   );
   const Vault = React.lazy(() =>
     import("./pages/Vault").then((m) => ({ default: m.Vault })),
   );
   const Learning = React.lazy(() =>
     import("./pages/Learning").then((m) => ({ default: m.Learning })),
   );
   const Settings = React.lazy(() =>
     import("./pages/Settings").then((m) => ({ default: m.Settings })),
   );

   // ================================================================
   // Loading fallback
   // ================================================================

   const PageLoader: React.FC = () => (
     <div className="flex items-center justify-center h-screen">
       <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500" />
     </div>
   );

   // ================================================================
   // App
   // ================================================================

   export default function App() {
     const { i18n } = useTranslation();

     useEffect(() => {
       const dir = i18n.language === "fa" ? "rtl" : "ltr";
       document.documentElement.dir = dir;
       document.documentElement.lang = i18n.language;
     }, [i18n.language]);

     return (
       <Suspense fallback={<PageLoader />}>
         <Routes>
           <Route element={<Layout />}>
             <Route path="/" element={<Navigate to="/dashboard" replace />} />
             <Route path="/dashboard" element={<Dashboard />} />
             <Route path="/scanner" element={<Scanner />} />
             <Route path="/oracle" element={<Oracle />} />
             <Route path="/vault" element={<Vault />} />
             <Route path="/learning" element={<Learning />} />
             <Route path="/settings" element={<Settings />} />
           </Route>
         </Routes>
       </Suspense>
     );
   }
   ```

3. **Configure Vite manual chunk splitting** in `frontend/vite.config.ts`:

   ```typescript
   import { defineConfig } from "vite";
   import react from "@vitejs/plugin-react";
   import path from "path";

   export default defineConfig({
     plugins: [react()],
     resolve: {
       alias: {
         "@": path.resolve(__dirname, "./src"),
       },
     },
     build: {
       rollupOptions: {
         output: {
           manualChunks: {
             "vendor-react": ["react", "react-dom", "react-router-dom"],
             "vendor-i18n": [
               "i18next",
               "react-i18next",
               "i18next-browser-languagedetector",
             ],
             "vendor-query": ["@tanstack/react-query"],
           },
         },
       },
       target: "es2020",
       reportCompressedSize: true,
       chunkSizeWarningLimit: 250,
     },
     server: {
       port: 5173,
       proxy: {
         "/api": {
           target: "http://localhost:8000",
           changeOrigin: true,
         },
         "/ws": {
           target: "ws://localhost:8000",
           ws: true,
         },
       },
     },
   });
   ```

   **Key additions:**
   - `manualChunks`: Separates React core, i18n, and react-query into independent vendor chunks. These change infrequently and benefit from long-term browser caching.
   - `target: "es2020"`: Modern browser target produces smaller output (no unnecessary polyfills).
   - `reportCompressedSize: true`: Shows gzipped sizes in build output.
   - `chunkSizeWarningLimit: 250`: Warns if any chunk exceeds 250KB (catch regressions early).

4. **Add preconnect hint** to `frontend/index.html` (if not already present):

   ```html
   <link rel="preconnect" href="http://localhost:8000" crossorigin />
   ```

   Check if `index.html` already has preconnect hints before adding.

5. **Build and measure:**

   ```bash
   cd frontend && npm run build
   ls -lh dist/assets/*.js
   ```

   Expected output structure:

   ```
   dist/assets/vendor-react-XXXX.js   (~140KB, ~45KB gzip)
   dist/assets/vendor-i18n-XXXX.js    (~50KB, ~18KB gzip)
   dist/assets/vendor-query-XXXX.js   (~40KB, ~14KB gzip)
   dist/assets/index-XXXX.js          (~30KB, ~10KB gzip -- app code)
   dist/assets/Dashboard-XXXX.js      (~10KB, lazy)
   dist/assets/Oracle-XXXX.js         (~20KB, lazy)
   dist/assets/Scanner-XXXX.js        (~10KB, lazy)
   dist/assets/Vault-XXXX.js          (~10KB, lazy)
   dist/assets/Learning-XXXX.js       (~10KB, lazy)
   dist/assets/Settings-XXXX.js       (~10KB, lazy)
   ```

   Initial load = vendor-react + vendor-i18n + vendor-query + index = ~87KB gzip. Well under 500KB target.

**Checkpoint:**

- [ ] `App.tsx` uses `React.lazy()` for all 6 page imports
- [ ] `Suspense` wrapper with `PageLoader` fallback surrounds Routes
- [ ] `vite.config.ts` has `manualChunks` configuration with 3 vendor groups
- [ ] Build produces separate vendor chunks and per-page lazy chunks
- [ ] Total initial JS bundle (gzipped) < 500KB
- [ ] Build succeeds without errors: `cd frontend && npm run build`
- Verify: `cd frontend && npm run build 2>&1 | tail -20`

STOP if build fails or total bundle exceeds 500KB gzip

---

### Phase 5: Nginx & Infrastructure Optimization (~30 min)

**Tasks:**

1. **Update `infrastructure/nginx/nginx.conf`** with performance optimizations.

   Replace the full file with the optimized version:

   ```nginx
   # NPS -- Nginx reverse proxy configuration (optimized)
   events {
       worker_connections 1024;
       multi_accept on;
   }

   http {
       include       /etc/nginx/mime.types;
       default_type  application/octet-stream;

       # Performance tuning
       sendfile on;
       tcp_nopush on;
       tcp_nodelay on;
       keepalive_timeout 65;
       types_hash_max_size 2048;

       # Gzip compression (60-80% size reduction for text content)
       gzip on;
       gzip_vary on;
       gzip_proxied any;
       gzip_comp_level 4;
       gzip_min_length 256;
       gzip_types
           text/plain
           text/css
           text/javascript
           application/javascript
           application/json
           application/xml
           image/svg+xml;

       # Upstream servers with keepalive connections
       upstream frontend {
           server frontend:80;
           keepalive 16;
       }

       upstream api {
           server api:8000;
           keepalive 32;
       }

       server {
           listen 80;
           server_name _;

           # Static assets -- long cache (Vite hashed filenames are immutable)
           location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
               proxy_pass http://frontend;
               proxy_set_header Host $host;
               proxy_http_version 1.1;
               proxy_set_header Connection "";
               expires 30d;
               add_header Cache-Control "public, immutable";
               add_header Vary "Accept-Encoding";
           }

           # Frontend (React SPA -- index.html must NOT be long-cached)
           location / {
               proxy_pass http://frontend;
               proxy_set_header Host $host;
               proxy_set_header X-Real-IP $remote_addr;
               proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
               proxy_http_version 1.1;
               proxy_set_header Connection "";
               add_header Cache-Control "no-cache";
           }

           # API endpoints
           location /api/ {
               proxy_pass http://api;
               proxy_set_header Host $host;
               proxy_set_header X-Real-IP $remote_addr;
               proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
               proxy_http_version 1.1;
               proxy_set_header Connection "";
               proxy_buffering on;
               proxy_buffer_size 8k;
               proxy_buffers 8 8k;
           }

           # WebSocket
           location /ws {
               proxy_pass http://api;
               proxy_http_version 1.1;
               proxy_set_header Upgrade $http_upgrade;
               proxy_set_header Connection "upgrade";
               proxy_set_header Host $host;
               proxy_set_header X-Real-IP $remote_addr;
               proxy_read_timeout 86400;
           }

           # Health check for nginx itself
           location /nginx-health {
               return 200 "healthy\n";
               add_header Content-Type text/plain;
           }
       }

       # TODO: Add HTTPS server block with SSL termination (Session 45)
   }
   ```

   **Key changes from the current config:**
   - Added `gzip` block: Compresses JSON API responses (~70% smaller) and JS/CSS assets
   - Added `sendfile`, `tcp_nopush`, `tcp_nodelay`: Kernel-level I/O optimizations
   - Added `keepalive` to upstreams: Reuse TCP connections to frontend and API (avoids 3-way handshake per request)
   - Added `proxy_http_version 1.1` + `Connection ""`: Required for upstream keepalive to work
   - Added static asset location block: Matches hashed Vite assets, sets `expires 30d` + `Cache-Control: public, immutable`
   - Added `proxy_buffering on` for API: Buffers API responses before sending to client (frees upstream connection faster)
   - SPA index.html gets `Cache-Control: no-cache`: Always validate freshness on page reload (but still serves from browser cache if unchanged)
   - `gzip_comp_level 4` (not 6+): Good compression with minimal CPU. Level 4 compresses ~95% as well as level 9 at ~50% of the CPU cost.

2. **Verify nginx config syntax** (if Docker is running):

   ```bash
   docker run --rm -v $(pwd)/infrastructure/nginx/nginx.conf:/etc/nginx/nginx.conf:ro nginx:1.25-alpine nginx -t
   ```

**Checkpoint:**

- [ ] nginx.conf has `gzip on` directive
- [ ] Static assets matched by regex get 30-day cache + immutable
- [ ] API responses have proxy buffering enabled
- [ ] Upstream connections use keepalive (16 for frontend, 32 for API)
- [ ] SPA root location has `Cache-Control: no-cache`
- [ ] Config passes `nginx -t` syntax check
- Verify: `grep -c "gzip on" infrastructure/nginx/nginx.conf` returns 1

STOP if nginx config fails syntax validation

---

### Phase 6: Enhanced Benchmark Tooling (~90 min)

**Tasks:**

1. **Enhance `integration/scripts/perf_audit.py`** with these improvements:

   **a. CLI arguments:**

   ```python
   import argparse

   def parse_args():
       parser = argparse.ArgumentParser(description="NPS Performance Audit")
       parser.add_argument("-n", "--iterations", type=int, default=20,
                           help="Measured iterations per endpoint (default: 20)")
       parser.add_argument("--warmup", type=int, default=3,
                           help="Warm-up iterations, not counted (default: 3)")
       parser.add_argument("--concurrent", type=int, default=1,
                           help="Concurrent requests per endpoint (default: 1)")
       parser.add_argument("--output", type=str, default=None,
                           help="JSON output file path (default: auto)")
       parser.add_argument("--compare", type=str, default=None,
                           help="Compare against previous baseline JSON file")
       return parser.parse_args()
   ```

   **b. Warm-up phase:**
   Before the measured iterations for each endpoint, execute `args.warmup` throwaway requests. These prime connection pools, JIT compilation, and caches. Warm-up request times are discarded.

   **c. p99 metric:**
   Update `compute_stats()` to include p99:

   ```python
   def compute_stats(times: list[float]) -> dict:
       if not times:
           return {"p50": None, "p95": None, "p99": None, "mean": None, "min": None, "max": None}
       sorted_times = sorted(times)
       n = len(sorted_times)
       return {
           "p50": round(sorted_times[int(n * 0.50)], 1),
           "p95": round(sorted_times[min(int(n * 0.95), n - 1)], 1),
           "p99": round(sorted_times[min(int(n * 0.99), n - 1)], 1),
           "mean": round(statistics.mean(times), 1),
           "min": round(min(times), 1),
           "max": round(max(times), 1),
       }
   ```

   **d. Concurrent request support:**

   ```python
   from concurrent.futures import ThreadPoolExecutor, as_completed

   def run_concurrent(session, method, url, payload, n, concurrency):
       """Run n requests with given concurrency level."""
       times = []
       errors = 0

       def _single_request():
           try:
               _, ms = make_request(session, method, url, payload)
               return ms
           except Exception:
               return None

       with ThreadPoolExecutor(max_workers=concurrency) as executor:
           futures = [executor.submit(_single_request) for _ in range(n)]
           for future in as_completed(futures):
               result = future.result()
               if result is not None:
                   times.append(result)
               else:
                   errors += 1
       return times, errors
   ```

   **e. Baseline comparison:**
   If `--compare baseline.json` is passed, load the previous baseline and compare p95 values. Flag regressions (p95 increased > 20%) and improvements (p95 decreased > 20%).

   **f. Enhanced console output format:**

   ```
   ======================================================================
   NPS Performance Audit
   API: http://localhost:8000
   Iterations: 20 | Warm-up: 3 | Concurrency: 1
   ======================================================================

     [PASS] health                p50=   3ms  p95=   5ms  p99=   8ms  target=<50ms
     [PASS] user_list             p50=  12ms  p95=  25ms  p99=  31ms  target=<200ms
     [FAIL] reading               p50=2100ms  p95=5200ms  p99=6100ms  target=<5000ms

   ======================================================================
   Results: 8/10 endpoints within target
   Baseline saved to: integration/reports/performance_baseline.json
   ======================================================================
   ```

   **g. Update ITERATIONS constant** from 5 to the `args.iterations` value (default 20).

2. **Create `integration/scripts/benchmark_readings.py`** -- focused reading performance benchmark:

   ```python
   #!/usr/bin/env python3
   """
   Reading Benchmark -- measures reading generation performance.

   Runs N reading requests and reports p50/p95/p99 response times.
   Supports multiple reading types (time, name, question, daily, multi-user).

   Usage:
       python3 integration/scripts/benchmark_readings.py -n 50 --type reading
       python3 integration/scripts/benchmark_readings.py -n 20 --type question --concurrent 4
       python3 integration/scripts/benchmark_readings.py -n 10 --type all
   """

   from __future__ import annotations

   import argparse
   import json
   import logging
   import os
   import statistics
   import sys
   import time
   from concurrent.futures import ThreadPoolExecutor, as_completed
   from pathlib import Path

   import requests

   logger = logging.getLogger(__name__)
   ```

   **CLI arguments:**
   - `-n` / `--count`: Number of measured iterations per type (default: 20)
   - `--type`: Reading type to benchmark: `reading`, `question`, `name`, `daily`, `multi_user_2`, `multi_user_5`, `all` (default: `all`)
   - `--warmup`: Warm-up iterations before measurement (default: 3)
   - `--concurrent`: Concurrent requests per type (default: 1)
   - `--output`: JSON output file (default: `integration/reports/reading_benchmark.json`)

   **Payload configuration per type:**

   | Type           | Method | Path                             | Payload                                     | Target ms |
   | -------------- | ------ | -------------------------------- | ------------------------------------------- | --------- |
   | `reading`      | POST   | `/api/oracle/reading`            | `{"datetime": "2024-06-15T14:30:00+00:00"}` | 5000      |
   | `question`     | POST   | `/api/oracle/question`           | `{"question": "Will the benchmark pass?"}`  | 5000      |
   | `name`         | POST   | `/api/oracle/name`               | `{"name": "Performance Test"}`              | 5000      |
   | `daily`        | GET    | `/api/oracle/daily`              | None                                        | 2000      |
   | `multi_user_2` | POST   | `/api/oracle/reading/multi-user` | 2-user payload                              | 8000      |
   | `multi_user_5` | POST   | `/api/oracle/reading/multi-user` | 5-user payload                              | 8000      |

   **JSON output format:**

   ```json
   {
     "measured_at": "2026-02-10T12:00:00Z",
     "config": {
       "iterations": 50,
       "warmup": 3,
       "concurrent": 1
     },
     "results": {
       "reading": {
         "p50_ms": 1200.5,
         "p95_ms": 2800.1,
         "p99_ms": 4100.3,
         "mean_ms": 1500.2,
         "min_ms": 800.0,
         "max_ms": 4500.0,
         "target_ms": 5000,
         "passed": true,
         "samples": 50,
         "errors": 0
       }
     },
     "summary": {
       "total_types": 6,
       "passed": 5,
       "failed": 1
     }
   }
   ```

   **Script structure:**
   - Reuse `compute_stats()` and `make_request()` patterns from `perf_audit.py`
   - Load `.env` for API_SECRET_KEY (same pattern as `perf_audit.py`)
   - Check API reachability before starting
   - Print progress during long-running benchmarks
   - Exit code 0 if all types pass, 1 if any fail

3. **Both scripts must follow project templates:**
   - `from __future__ import annotations`
   - `logging` module for debug output (not print)
   - `Path` for file paths (no string concatenation)
   - `argparse` for CLI arguments
   - Specific exception handling (no bare `except:`)
   - Type hints on all function signatures and return values
   - Google-style docstrings on all public functions

**Checkpoint:**

- [ ] `perf_audit.py` accepts `-n`, `--warmup`, `--concurrent`, `--output`, `--compare` args
- [ ] `perf_audit.py` runs warm-up rounds before measurement
- [ ] `perf_audit.py` reports p50/p95/p99 metrics
- [ ] `perf_audit.py` compares against previous baseline when `--compare` is used
- [ ] `benchmark_readings.py` exists and accepts `-n`, `--type`, `--warmup`, `--concurrent`, `--output` args
- [ ] `benchmark_readings.py` outputs structured JSON report
- [ ] Both scripts follow project Python templates
- Verify:
  ```bash
  python3 integration/scripts/perf_audit.py -n 5 --warmup 1 2>&1 | head -20
  python3 integration/scripts/benchmark_readings.py -n 3 --warmup 1 --type daily 2>&1 | head -20
  ```

STOP if either script errors out or produces invalid output

---

### Phase 7: Final Verification & After-Benchmarks (~45 min)

**Tasks:**

1. **Restart all services** to pick up all changes:

   ```bash
   make down && make up
   sleep 15  # Wait for all services to stabilize
   ```

2. **Run the enhanced perf_audit.py** with meaningful iterations:

   ```bash
   python3 integration/scripts/perf_audit.py -n 30 --warmup 5 \
     --output integration/reports/performance_baseline_after.json \
     --compare integration/reports/performance_baseline_before.json
   ```

   All 5 primary targets should pass. The comparison should show improvements.

3. **Run the reading benchmark:**

   ```bash
   python3 integration/scripts/benchmark_readings.py -n 20 --warmup 3 --type all \
     --output integration/reports/reading_benchmark.json
   ```

   All reading types should be within their targets.

4. **Verify database performance** by re-running the 6 EXPLAIN ANALYZE queries from Phase 1. All should show Index Scan and < 10ms execution time.

5. **Verify frontend performance:**

   ```bash
   cd frontend && npm run build 2>&1
   ```

   Verify:
   - Total initial JS (gzipped) < 500KB
   - Per-page chunks are separate files (at least 9 JS files: 3 vendor + 1 index + 6 lazy pages, possibly with CSS)
   - Build output shows compressed sizes

6. **Run full test suite** to ensure no regressions from optimization changes:

   ```bash
   cd api && python3 -m pytest tests/ -v --tb=short
   cd services/oracle && python3 -m pytest tests/ -v --tb=short
   cd frontend && npm test
   python3 -m pytest integration/tests/ -v -s --tb=short
   ```

   All existing tests must pass. Zero regressions.

7. **Create performance results report** at `integration/reports/SESSION_44_RESULTS.md`:

   ```markdown
   # Session 44 Performance Optimization Results

   ## Before vs After

   | Metric               | Before | After | Target   | Status |
   | -------------------- | ------ | ----- | -------- | ------ |
   | Health p95           | Xms    | Xms   | < 50ms   | PASS   |
   | User list p95        | Xms    | Xms   | < 100ms  | PASS   |
   | Reading p95          | Xms    | Xms   | < 5000ms | PASS   |
   | Frontend bundle gzip | X KB   | X KB  | < 500KB  | PASS   |
   | DB user query        | Xms    | Xms   | < 100ms  | PASS   |

   ## Optimizations Applied

   1. ...
   2. ...

   ## Remaining Bottlenecks

   - ...
   ```

8. **Lint and format all modified files:**

   ```bash
   cd api && python3 -m black . && python3 -m ruff check --fix .
   cd frontend && npm run lint && npm run format
   ```

**Checkpoint:**

- [ ] All 5 CLAUDE.md performance targets met (or documented exception with remediation plan)
- [ ] Before/after comparison shows measurable improvement
- [ ] All existing tests still pass (zero regressions)
- [ ] Frontend build produces separate vendor + page chunks
- [ ] Results documented in `integration/reports/SESSION_44_RESULTS.md`
- [ ] All code linted and formatted
- Verify: `python3 integration/scripts/perf_audit.py -n 10 --warmup 2 2>&1 | tail -5`

STOP if any primary performance target is not met AND no remediation plan exists

---

## TESTS TO WRITE

### `api/tests/test_cache_middleware.py`

| Test Function                               | Verifies                                                         |
| ------------------------------------------- | ---------------------------------------------------------------- |
| `test_cache_miss_first_request`             | First GET request returns `X-Cache: MISS`                        |
| `test_cache_hit_second_request`             | Second identical GET request returns `X-Cache: HIT`              |
| `test_cache_not_applied_to_post`            | POST requests are never served from cache                        |
| `test_cache_control_header_on_get`          | GET responses include `Cache-Control` header with `max-age`      |
| `test_cache_control_no_store_on_post`       | POST responses include `Cache-Control: no-store`                 |
| `test_etag_present_on_cached`               | Cached GET responses include `ETag` header                       |
| `test_etag_if_none_match_returns_304`       | Request with matching `If-None-Match` returns 304 Not Modified   |
| `test_etag_if_none_match_mismatch`          | Request with non-matching `If-None-Match` returns full response  |
| `test_cache_invalidation_on_user_create`    | POST to `/oracle/users` invalidates user list cache              |
| `test_cache_invalidation_on_reading_create` | POST to `/oracle/reading` invalidates reading list cache         |
| `test_cache_different_auth_different_entry` | Different auth tokens produce separate cache entries             |
| `test_cache_graceful_without_redis`         | When Redis is None, requests work normally (no cache, no error)  |
| `test_error_responses_not_cached`           | 4xx and 5xx responses are NOT stored in cache                    |
| `test_response_time_header`                 | All responses include `X-Response-Time` header with milliseconds |
| `test_cache_ttl_expiry`                     | Cached entry expires after configured TTL                        |

### `integration/scripts/test_perf_stats.py` (unit tests for stats functions)

| Test Function                          | Verifies                                                              |
| -------------------------------------- | --------------------------------------------------------------------- |
| `test_compute_stats_basic`             | `compute_stats()` returns correct p50/p95/p99 for known input list    |
| `test_compute_stats_empty`             | `compute_stats()` handles empty list, returns None for all metrics    |
| `test_compute_stats_single_value`      | `compute_stats()` with 1 value returns that value for all percentiles |
| `test_baseline_comparison_regression`  | Regression detection flags p95 increase > 20%                         |
| `test_baseline_comparison_improvement` | Improvement detection notes p95 decrease > 20%                        |

### Frontend (manual/visual verification checklist)

| Verification                     | Method                                                                |
| -------------------------------- | --------------------------------------------------------------------- |
| `verify_lazy_loading_dashboard`  | Network tab shows Dashboard chunk loaded on navigate to /dashboard    |
| `verify_lazy_loading_oracle`     | Network tab shows Oracle chunk loaded only when visiting /oracle      |
| `verify_suspense_fallback`       | Slow network (throttle to 3G) shows loading spinner during chunk load |
| `verify_vendor_chunk_separation` | Build output shows separate react, i18n, query vendor chunks          |
| `verify_initial_load_size`       | Total initial JS transfer < 500KB gzipped                             |

**Total: 20 automated tests + 5 manual verifications**

---

## ACCEPTANCE CRITERIA

- [ ] API simple endpoints (health, user list, user get) respond in < 50ms p95 over 20+ iterations
- [ ] API reading endpoints respond in < 5 seconds p95 (including any AI calls) over 20+ iterations
- [ ] Database indexed queries execute in < 100ms per EXPLAIN ANALYZE
- [ ] Frontend initial JS bundle < 500KB gzipped total
- [ ] Frontend uses `React.lazy()` for all 6 page components with `Suspense` fallback
- [ ] Vite build produces separate vendor chunks (vendor-react, vendor-i18n, vendor-query)
- [ ] Redis-backed cache middleware returns `X-Cache: HIT` on repeated GET requests
- [ ] Cache middleware degrades gracefully when Redis is unavailable (passthrough, no crash)
- [ ] ETag + `If-None-Match` returns 304 Not Modified correctly
- [ ] Write operations (POST/PUT/DELETE) invalidate related GET cache entries
- [ ] All responses include `X-Response-Time` header
- [ ] Nginx has gzip compression enabled for JSON/JS/CSS content types
- [ ] Nginx serves static assets with `Cache-Control: public, immutable` + 30-day expiry
- [ ] SQLAlchemy connection pool tuned: pool_size, max_overflow, pool_recycle from environment
- [ ] `perf_audit.py` supports `--iterations`, `--warmup`, `--concurrent`, `--output`, `--compare` args
- [ ] `benchmark_readings.py` exists and produces JSON report with p50/p95/p99 per reading type
- [ ] All 15 cache middleware tests pass
- [ ] All 5 perf stats unit tests pass
- [ ] All existing tests still pass (no regressions from optimization changes)
- [ ] Before/after performance comparison documented in `SESSION_44_RESULTS.md`
- Verify all:
  ```bash
  test -f api/app/middleware/cache.py && \
  test -f integration/scripts/benchmark_readings.py && \
  grep -q "React.lazy" frontend/src/App.tsx && \
  grep -q "manualChunks" frontend/vite.config.ts && \
  grep -q "gzip on" infrastructure/nginx/nginx.conf && \
  grep -q "pool_size" api/app/database.py && \
  grep -q "cache_enabled" api/app/config.py && \
  grep -q "ResponseCacheMiddleware" api/app/main.py && \
  echo "ALL ACCEPTANCE CRITERIA VERIFIABLE"
  ```

---

## ERROR SCENARIOS

| Scenario                                            | Expected Behavior                                                                          |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Redis unavailable during cache middleware init      | Cache disabled gracefully; all requests pass through without caching; warning logged       |
| Redis connection drops mid-request                  | Cache read/write fails silently; request served from API normally; error logged once       |
| Cache key collision (SHA-256 collision)             | Astronomically unlikely; if occurs, stale data served briefly until TTL expires            |
| Cache middleware raises unhandled exception         | Outer try/except in dispatch catches it; request passes through uncached; exception logged |
| Frontend lazy import fails (network error)          | React error boundary or Suspense fallback displays; user can retry navigation              |
| Vite manualChunks causes circular reference         | Build fails with clear Rollup error; remove problematic package from manualChunks config   |
| PostgreSQL runs out of connections (pool exhausted) | SQLAlchemy raises `TimeoutError` after pool_timeout; returns 503; pool_size should prevent |
| Benchmark script cannot connect to API              | Script exits with clear error message and non-zero exit code before any measurement        |
| Benchmark with 0 iterations requested               | argparse minimum validation rejects; or clamp to minimum 1                                 |
| EXPLAIN ANALYZE shows Seq Scan despite new index    | Table may have too few rows for index to be cost-effective; run `ANALYZE tablename;`       |
| Nginx gzip corrupts binary response                 | gzip_types explicitly lists only text/json types; binary content excluded by default       |
| Cache invalidation deletes too many keys            | Pattern `nps:cache:*oracle*users*` scoped to oracle user paths only; monitor key count     |
| ETag computed on different body encoding            | ETag computed on raw response body BEFORE any middleware transformation; remains stable    |
| Concurrent benchmark triggers rate limiting         | Benchmark uses auth token; rate limiter keys on token prefix, limit is 100/hour for AI     |
| Multiple uvicorn workers cause cache inconsistency  | Redis is external shared cache; all workers read/write same Redis; no inconsistency        |

---

## DESIGN DECISIONS

| Decision                             | Choice                                          | Rationale                                                                                                    |
| ------------------------------------ | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Cache backend                        | Redis (existing service)                        | Already in docker-compose, connected in lifespan. No new dependency. Shared across uvicorn workers.          |
| Cache invalidation strategy          | Pattern-based key deletion on writes            | Simple and effective at this scale. Avoids complex cache tags or pub/sub invalidation overhead.              |
| Cache key includes auth token prefix | First 16 chars of Bearer token                  | Different users may see different data (ownership filtering). Prevents cross-user cache data leaks.          |
| ETag algorithm                       | MD5 of response body                            | ETag is not security-sensitive. MD5 is fast and produces adequate collision resistance for cache validation. |
| Frontend code splitting              | React.lazy + Vite manualChunks                  | React.lazy is the standard React approach. manualChunks gives explicit vendor separation control.            |
| Named export adapter for React.lazy  | `.then(m => ({ default: m.X }))` pattern        | Avoids modifying 6 page files to add default exports. Standard community pattern.                            |
| SQLAlchemy pool_size=10              | 10 base + 20 overflow = 30 max connections      | PostgreSQL max_connections=100; other services also connect. 30 is conservative and safe.                    |
| Pool settings via environment        | Config class with defaults                      | Production can tune without code changes. Follows project's "Environment over config files" rule.            |
| Benchmark warm-up default=3          | 3 throwaway iterations before measurement       | Primes connection pools, Python bytecache, Redis. Results represent steady-state, not cold-start.            |
| Nginx gzip_comp_level=4              | Level 4 out of 9                                | Good ratio without excessive CPU. Level 4 achieves ~95% of level 9 compression at ~50% CPU.                  |
| Separate benchmark_readings.py       | Dedicated script, not merged into perf_audit.py | Readings are the heaviest endpoints; dedicated script allows focused, configurable per-type analysis.        |
| No CDN in this session               | Deferred to Session 45                          | CDN is a deployment/infrastructure concern. Session 45 handles production deployment configuration.          |
| PostgreSQL shared_buffers=256MB      | 25% of 1GB container memory                     | Standard PostgreSQL tuning recommendation. Matches the resource limit in docker-compose.yml.                 |

---

## HANDOFF

**Created:**

- `api/app/middleware/cache.py` -- Redis-backed response cache with ETag support and invalidation
- `api/tests/test_cache_middleware.py` -- 15 cache middleware tests
- `integration/scripts/benchmark_readings.py` -- Dedicated reading benchmark tool with p50/p95/p99
- `integration/reports/performance_baseline_before.json` -- Pre-optimization baseline
- `integration/reports/performance_baseline_after.json` -- Post-optimization baseline
- `integration/reports/reading_benchmark.json` -- Reading performance report
- `integration/reports/SESSION_44_RESULTS.md` -- Before/after comparison and analysis
- `database/migrations/XXX_performance_indexes.sql` -- Composite and partial indexes
- `database/migrations/XXX_performance_indexes_rollback.sql` -- Index rollback

**Modified:**

- `integration/scripts/perf_audit.py` -- CLI args, warm-up, p99, concurrent, baseline comparison
- `api/app/database.py` -- Connection pool tuning: pool_size, max_overflow, pool_recycle from settings
- `api/app/config.py` -- Cache TTL settings, pool size settings (environment-variable driven)
- `api/app/main.py` -- Cache middleware registration
- `frontend/src/App.tsx` -- React.lazy page imports, Suspense wrapper with PageLoader
- `frontend/vite.config.ts` -- manualChunks vendor splitting, es2020 target, compressed size reporting
- `infrastructure/nginx/nginx.conf` -- gzip compression, static caching, keepalive, proxy buffering
- `docker-compose.yml` -- PostgreSQL server tuning via command args

**Next session needs:**

- **Session 45 (Final Deployment & Documentation)** depends on:
  - All 5 performance targets met and verified by benchmark output
  - Benchmark tooling available for production monitoring (`perf_audit.py`, `benchmark_readings.py`)
  - Cache middleware stable and tested (Session 45 may add cache warming on startup)
  - Nginx config production-ready (Session 45 adds SSL/TLS termination, production server_name)
  - Frontend bundle optimized (Session 45 may add CDN configuration and asset fingerprinting verification)
  - PostgreSQL tuning applied (Session 45 verifies in production environment)
  - All performance reports available in `integration/reports/` for deployment documentation
  - No test regressions from optimization changes -- full test suite green
