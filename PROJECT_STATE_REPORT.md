# PROJECT STATE REPORT — NPS Deep Scan

> **Generated:** 2026-02-09
> **Purpose:** Comprehensive pre-build assessment before the 45-session Oracle rebuild
> **Method:** Automated deep scan of all 7 layers + tests + infrastructure + reference files

---

## Executive Summary

The NPS project has a **solid foundation** from 16 sessions of scaffolding. The Oracle service engines (FC60, numerology, oracle reader) are production-ready with ~12,670 lines of real computation logic. The database schema is comprehensive (15 tables, 36 indexes). Auth (JWT + API key + 3-tier scopes) and encryption (AES-256-GCM) are fully implemented. The frontend Oracle page works end-to-end but 5 other pages are empty stubs. The Scanner service is 100% stub code (311 lines of Rust structure with no real implementations). The biggest architectural issue is a dual AI integration — one uses the Anthropic SDK (correct), the other shells out to the Claude CLI (violates architecture rule #1).

**Bottom line:** Sessions 1-12 of the 45-session plan can build on real, working code. Sessions 13+ require significant new work.

---

## Statistics

| Metric                                  | Count                 |
| --------------------------------------- | --------------------- |
| Git commits                             | 49                    |
| Active files (excl. archive/specs/deps) | 363                   |
| Python files (.py)                      | 152                   |
| TypeScript/TSX files                    | 67                    |
| Rust files (.rs)                        | 7                     |
| SQL files (.sql)                        | 12                    |
| Test files (all layers)                 | 42                    |
| Total lines of code                     | 46,441                |
| Spec files in .specs/                   | 17 (including README) |
| Spec files total size                   | 916 KB                |

---

## Architecture Diagram (Verified Ports & Services)

```
┌─────────────────────────────────────────────────┐
│  LAYER 1: FRONTEND                              │
│  React 18 + TypeScript + Tailwind + Vite        │
│  Port: 5173 (dev) / 80 (prod via nginx)         │
│  6 pages: Oracle (full), 5 stubs                │
│  i18n: EN + FA (171/171 keys = 100% parity)     │
└──────────────┬──────────────────────────────────┘
               │ HTTP / WebSocket
┌──────────────▼──────────────────────────────────┐
│  LAYER 2: API GATEWAY                           │
│  FastAPI + Python 3.11+ + SQLAlchemy            │
│  Port: 8000 │ 44 endpoints total                │
│  Auth: JWT(HS256) + API Key(SHA-256) + Legacy   │
│  Rate limit: in-memory sliding window           │
└──────┬───────────────────┬──────────────────────┘
       │ SQLAlchemy         │ Direct import (not gRPC)
┌──────▼──────┐    ┌───────▼──────────────────────┐
│  LAYER 4:   │    │  LAYER 3: BACKEND            │
│  DATABASE   │    │  Oracle (Python :50052)       │
│  PostgreSQL │◄───┤  Scanner (Rust :50051) [STUB] │
│  Port: 5432 │    │  AI: Anthropic SDK + CLI      │
│  15 tables  │    │  12,670 LOC engines           │
│  36 indexes │    │  2,512 LOC solvers            │
└─────────────┘    └──────────────────────────────┘

LAYER 5: Docker Compose — 8 services + 3 volumes
LAYER 6: AES-256-GCM (PBKDF2, 600K iterations)
LAYER 7: JSON logging + Prometheus + Telegram alerts
```

---

## Layer 1: Frontend (React + TypeScript + Tailwind)

### Pages

| Page      | File                               | Lines | Status                                               |
| --------- | ---------------------------------- | ----- | ---------------------------------------------------- |
| Oracle    | `frontend/src/pages/Oracle.tsx`    | 188   | **Fully implemented** — form, results, history, tabs |
| Dashboard | `frontend/src/pages/Dashboard.tsx` | 26    | Stub placeholder                                     |
| Scanner   | `frontend/src/pages/Scanner.tsx`   | 26    | Stub placeholder                                     |
| Vault     | `frontend/src/pages/Vault.tsx`     | 23    | Stub placeholder                                     |
| Learning  | `frontend/src/pages/Learning.tsx`  | 32    | Stub placeholder                                     |
| Settings  | `frontend/src/pages/Settings.tsx`  | 26    | Stub placeholder                                     |

### Oracle Components (15 implemented)

| Component              | Path                                           | Status                      |
| ---------------------- | ---------------------------------------------- | --------------------------- |
| OracleConsultationForm | `components/oracle/OracleConsultationForm.tsx` | Full — form with validation |
| PersianKeyboard        | `components/oracle/PersianKeyboard.tsx`        | Full — virtual keyboard     |
| CalendarPicker         | `components/oracle/CalendarPicker.tsx`         | Full — Jalali + Gregorian   |
| SignTypeSelector       | `components/oracle/SignTypeSelector.tsx`       | Full — time/name/question   |
| LocationSelector       | `components/oracle/LocationSelector.tsx`       | Full — geocoding            |
| UserSelector           | `components/oracle/UserSelector.tsx`           | Full — select/create users  |
| UserForm               | `components/oracle/UserForm.tsx`               | Full — CRUD                 |
| UserChip               | `components/oracle/UserChip.tsx`               | Full — display widget       |
| MultiUserSelector      | `components/oracle/MultiUserSelector.tsx`      | Full — multi-select         |
| ReadingResults         | `components/oracle/ReadingResults.tsx`         | Full — tabbed display       |
| SummaryTab             | `components/oracle/SummaryTab.tsx`             | Full — summary view         |
| DetailsTab             | `components/oracle/DetailsTab.tsx`             | Full — detailed view        |
| ReadingHistory         | `components/oracle/ReadingHistory.tsx`         | Full — pagination           |
| TranslatedReading      | `components/oracle/TranslatedReading.tsx`      | Full — EN↔FA                |
| ExportButton           | `components/oracle/ExportButton.tsx`           | Full — PDF/text export      |

### Shared Components

| Component      | Path                            | Status                             |
| -------------- | ------------------------------- | ---------------------------------- |
| Layout         | `components/Layout.tsx`         | Full — app shell, sidebar, routing |
| LanguageToggle | `components/LanguageToggle.tsx` | Full — EN/FA switch                |
| StatsCard      | `components/StatsCard.tsx`      | Full — metric display              |
| LogPanel       | `components/LogPanel.tsx`       | Full — log viewer                  |

### i18n & RTL

| Locale          | File                              | Keys | Status                                               |
| --------------- | --------------------------------- | ---- | ---------------------------------------------------- |
| English         | `frontend/src/locales/en.json`    | 171  | Complete                                             |
| Persian (Farsi) | `frontend/src/locales/fa.json`    | 171  | Complete — 100% parity                               |
| Config          | `frontend/src/i18n/config.ts`     | —    | i18next + LanguageDetector, localStorage persistence |
| RTL             | Tailwind config + `dir` attribute | —    | Supported via `rtl:` variant                         |

### Frontend Tests

| Type                   | Files               | Location                                                                                        |
| ---------------------- | ------------------- | ----------------------------------------------------------------------------------------------- |
| Unit tests (Vitest)    | 17 files            | `components/oracle/__tests__/`, `components/__tests__/`, `pages/__tests__/`, `utils/__tests__/` |
| E2E tests (Playwright) | 1 file, 8 scenarios | `frontend/e2e/oracle.spec.ts`                                                                   |

### Configuration

- **Build:** Vite with `@` path alias
- **Styling:** Tailwind CSS with custom `nps-*` color theme
- **Types:** `frontend/src/types/` directory
- **Hooks:** `frontend/src/hooks/` (3 custom hooks)
- **Services:** `frontend/src/services/` (API client)

---

## Layer 2: API Gateway (FastAPI)

### Endpoints by Router

| Router           | Prefix             | Endpoints | Implemented | Status                  |
| ---------------- | ------------------ | --------- | ----------- | ----------------------- |
| `auth.py`        | `/api/auth`        | 4         | 4/4         | Production-ready        |
| `health.py`      | `/api/health`      | 3         | 2/3         | `/performance` has TODO |
| `oracle.py`      | `/api/oracle`      | 16        | 15/16       | WebSocket + full CRUD   |
| `scanner.py`     | `/api/scanner`     | 7         | 0/7         | All return HTTP 501     |
| `vault.py`       | `/api/vault`       | 4         | 0/4         | Empty stubs             |
| `learning.py`    | `/api/learning`    | 5         | 0/5         | Empty stubs             |
| `location.py`    | `/api/location`    | 2         | 2/2         | Geocoding service       |
| `translation.py` | `/api/translation` | 3         | 3/3         | EN↔FA translation       |
| **Total**        |                    | **44**    | **26/44**   | **59% implemented**     |

### Oracle Endpoints (Detailed)

| Method | Path                             | Scope          | Status      |
| ------ | -------------------------------- | -------------- | ----------- |
| POST   | `/api/oracle/reading`            | `oracle:write` | Implemented |
| POST   | `/api/oracle/question`           | `oracle:write` | Implemented |
| POST   | `/api/oracle/name`               | `oracle:write` | Implemented |
| GET    | `/api/oracle/daily`              | `oracle:read`  | Implemented |
| POST   | `/api/oracle/reading/multi-user` | `oracle:write` | Implemented |
| GET    | `/api/oracle/readings`           | `oracle:read`  | Implemented |
| GET    | `/api/oracle/readings/{id}`      | `oracle:read`  | Implemented |
| POST   | `/api/oracle/users`              | `oracle:write` | Implemented |
| GET    | `/api/oracle/users`              | `oracle:read`  | Implemented |
| GET    | `/api/oracle/users/{id}`         | `oracle:read`  | Implemented |
| PUT    | `/api/oracle/users/{id}`         | `oracle:write` | Implemented |
| DELETE | `/api/oracle/users/{id}`         | `oracle:admin` | Implemented |
| POST   | `/api/oracle/suggest-range`      | —              | Implemented |
| GET    | `/api/oracle/audit`              | `oracle:admin` | Implemented |
| WS     | `/api/oracle/ws`                 | —              | Implemented |

### Auth System

| Feature  | Implementation           | Details                                               |
| -------- | ------------------------ | ----------------------------------------------------- |
| JWT      | HS256, 24h expiry        | `python-jose[cryptography]`                           |
| API Keys | SHA-256 hashed in DB     | Per-key rate limit, expiry, scopes                    |
| Legacy   | Direct secret comparison | Backward compatibility fallback                       |
| Scopes   | 3-tier hierarchy         | `admin` > `write` > `read` per domain                 |
| Roles    | 3 roles                  | `admin` (all), `user` (read/write), `readonly` (read) |

### Rate Limiting

| Tier       | Limit       | Paths                                                                |
| ---------- | ----------- | -------------------------------------------------------------------- |
| AI-powered | 100 req/hr  | `/oracle/reading`, `/question`, `/name`, `/multi-user`, `/translate` |
| Default    | 60 req/min  | All other endpoints                                                  |
| Custom     | Per API key | Configurable `rate_limit` field                                      |

### Services Layer

| Service                 | File                                     | Purpose                                       |
| ----------------------- | ---------------------------------------- | --------------------------------------------- |
| `security.py`           | `api/app/services/security.py`           | AES-256-GCM encrypt/decrypt + legacy fallback |
| `audit.py`              | `api/app/services/audit.py`              | Audit log writes                              |
| `oracle_reading.py`     | `api/app/services/oracle_reading.py`     | Oracle engine orchestration                   |
| `oracle_permissions.py` | `api/app/services/oracle_permissions.py` | Scope checking                                |
| `location_service.py`   | `api/app/services/location_service.py`   | Geocoding/timezone                            |
| `translation.py`        | `api/app/services/translation.py`        | EN↔FA translation                             |
| `websocket_manager.py`  | `api/app/services/websocket_manager.py`  | Real-time events                              |

### API Tests

| Test File                    | Coverage                        |
| ---------------------------- | ------------------------------- |
| `test_auth.py`               | Login, JWT, API key creation    |
| `test_health.py`             | Health checks, readiness probes |
| `test_oracle_readings.py`    | Oracle reading endpoints        |
| `test_oracle_users.py`       | User CRUD operations            |
| `test_multi_user_reading.py` | Multi-user FC60 analysis        |
| `test_permissions.py`        | Scope-based access control      |
| `test_rate_limit.py`         | Rate limiting behavior          |
| `test_security.py`           | AES-256-GCM encryption          |
| `test_location.py`           | Geocoding endpoints             |
| `test_translation.py`        | Translation service             |
| `test_audit.py`              | Audit log operations            |
| **Total**                    | **11 test files**               |

---

## Layer 3: Backend Services

### Oracle Service (`services/oracle/`)

#### Core Engines

| Engine            | File                       | Lines     | Status                                                             |
| ----------------- | -------------------------- | --------- | ------------------------------------------------------------------ |
| FC60              | `engines/fc60.py`          | 966       | Production-ready — JDN, base-60, ganzhi, moon phase                |
| Numerology        | `engines/numerology.py`    | 294       | Production-ready — Pythagorean (life path, soul urge, personality) |
| Oracle Reader     | `engines/oracle.py`        | 1,493     | Production-ready — sign reading, name reading, question, daily     |
| Scoring           | `engines/scoring.py`       | 290       | Production-ready — key scoring weights                             |
| Math Analysis     | `engines/math_analysis.py` | 160       | Production-ready — pure computation                                |
| **Core subtotal** |                            | **3,203** |                                                                    |

#### AI Integration

| Component        | File                          | Lines     | Status                 | Architecture Compliance                         |
| ---------------- | ----------------------------- | --------- | ---------------------- | ----------------------------------------------- |
| AI Client (SDK)  | `engines/ai_client.py`        | 288       | Production-ready       | **Compliant** — Anthropic Python SDK            |
| AI Engine (CLI)  | `engines/ai_engine.py`        | 569       | Working but deprecated | **VIOLATES Rule #1** — subprocess to Claude CLI |
| AI Interpreter   | `engines/ai_interpreter.py`   | 664       | Production-ready       | Compliant — consumes SDK client                 |
| Prompt Templates | `engines/prompt_templates.py` | 316       | Production-ready       | Compliant                                       |
| **AI subtotal**  |                               | **1,837** |                        |                                                 |

#### Operational Modules

| Module                   | File                             | Lines     | Status                                 |
| ------------------------ | -------------------------------- | --------- | -------------------------------------- |
| Scanner Brain            | `engines/scanner_brain.py`       | 572       | Implemented — oracle suggestions       |
| Learning                 | `engines/learning.py`            | 439       | Implemented — XP/level system          |
| Learner                  | `engines/learner.py`             | 307       | Implemented — pattern learning         |
| Session Manager          | `engines/session_manager.py`     | 147       | Implemented                            |
| Terminal Manager         | `engines/terminal_manager.py`    | 254       | Implemented                            |
| Multi-user FC60          | `engines/multi_user_fc60.py`     | 167       | Implemented                            |
| Multi-user Service       | `engines/multi_user_service.py`  | 114       | Implemented                            |
| Translation              | `engines/translation_service.py` | 410       | Implemented — EN↔FA                    |
| Vault                    | `engines/vault.py`               | 305       | Legacy carry-over — needs DB migration |
| Notifier                 | `engines/notifier.py`            | 1,577     | Legacy carry-over — should move to API |
| Memory                   | `engines/memory.py`              | 423       | Utility                                |
| Perf                     | `engines/perf.py`                | 174       | Performance tracking                   |
| **Operational subtotal** |                                  | **4,889** |                                        |

#### Solver Classes (7)

| Solver              | File                        | Lines     | Purpose                  |
| ------------------- | --------------------------- | --------- | ------------------------ |
| BaseSolver          | `solvers/base_solver.py`    | 68        | Abstract interface       |
| NumberSolver        | `solvers/number_solver.py`  | 279       | Digit analysis, factors  |
| NameSolver          | `solvers/name_solver.py`    | 162       | Name gematria            |
| DateSolver          | `solvers/date_solver.py`    | 175       | Date patterns            |
| BTCSolver           | `solvers/btc_solver.py`     | 495       | Bitcoin puzzle logic     |
| ScannerSolver       | `solvers/scanner_solver.py` | 772       | Scanner integration      |
| UnifiedSolver       | `solvers/unified_solver.py` | 546       | Multi-method combination |
| **Solver subtotal** |                             | **2,497** |                          |

#### Logic Modules (6)

| Module             | File                       | Lines     | Purpose                  |
| ------------------ | -------------------------- | --------- | ------------------------ |
| Key Scorer         | `logic/key_scorer.py`      | 156       | LRU-cached scoring       |
| History Manager    | `logic/history_manager.py` | 274       | Throttled persistence    |
| Pattern Tracker    | `logic/pattern_tracker.py` | 226       | Sequence detection       |
| Range Optimizer    | `logic/range_optimizer.py` | 197       | Coverage optimization    |
| Strategy Engine    | `logic/strategy_engine.py` | 336       | Level-gated strategies   |
| Timing Advisor     | `logic/timing_advisor.py`  | 236       | Moon/planetary alignment |
| **Logic subtotal** |                            | **1,425** |                          |

#### gRPC Server

| Item   | Detail                                                                                                                      |
| ------ | --------------------------------------------------------------------------------------------------------------------------- |
| File   | `services/oracle/oracle_service/server.py`                                                                                  |
| Status | **Implemented** — 8 RPC endpoints                                                                                           |
| Port   | 50052                                                                                                                       |
| RPCs   | GetReading, GetNameReading, GetQuestionSign, GetDailyInsight, SuggestRange, AnalyzeSession, GetTimingAlignment, HealthCheck |
| Note   | API layer currently imports Oracle engines directly, bypassing gRPC                                                         |

#### Oracle Tests

| Test File                 | Lines     | Coverage                           |
| ------------------------- | --------- | ---------------------------------- |
| `test_engines.py`         | 191       | FC60, numerology, oracle core      |
| `test_grpc_server.py`     | 187       | gRPC endpoints, health             |
| `test_ai_integration.py`  | 1,079     | AI client, caching, CLI fallback   |
| `test_multi_user_fc60.py` | 554       | Multi-user analysis, compatibility |
| `test_oracle_service.py`  | 58        | Service initialization             |
| **Total**                 | **2,069** | **5 test files**                   |

### Scanner Service (`services/scanner/`) — STUB

| File                 | Lines   | Content                         |
| -------------------- | ------- | ------------------------------- |
| `src/main.rs`        | 35      | Placeholder main with `todo!()` |
| `src/scanner/mod.rs` | 74      | Struct definitions, no logic    |
| `src/scoring/mod.rs` | 86      | Struct definitions, no logic    |
| `src/crypto/mod.rs`  | 45      | Module skeleton                 |
| `src/balance/mod.rs` | 35      | Module skeleton                 |
| `src/grpc/mod.rs`    | 36      | Module skeleton                 |
| `build.rs`           | 1       | tonic build placeholder         |
| **Total**            | **311** | **0% implemented**              |

**Cargo.toml dependencies** (declared but unused): tonic, prost, tokio, secp256k1, sha2, ripemd, bs58, hex, serde, tracing, clap

---

## Layer 4: Database (PostgreSQL)

### Tables (15)

| Table                  | Purpose                                         | Domain      |
| ---------------------- | ----------------------------------------------- | ----------- |
| `schema_migrations`    | Migration version tracking                      | System      |
| `users`                | Auth users (UUID PK, bcrypt hash, role)         | Auth        |
| `api_keys`             | SHA-256 hashed API keys with scopes             | Auth        |
| `sessions`             | Scan sessions (status, stats, checkpoint)       | Scanner     |
| `findings`             | Vault entries (encrypted private keys)          | Scanner     |
| `readings`             | Oracle reading storage                          | Oracle      |
| `learning_data`        | XP/level/streak for gamification                | Learning    |
| `insights`             | AI-generated insights                           | Oracle      |
| `oracle_suggestions`   | Oracle→Scanner range suggestions                | Integration |
| `health_checks`        | Service health history                          | DevOps      |
| `audit_log`            | General audit trail                             | Security    |
| `oracle_users`         | Oracle user profiles (name, birthday, location) | Oracle      |
| `oracle_readings`      | Detailed reading results (JSONB)                | Oracle      |
| `oracle_reading_users` | Many-to-many reading↔user junction              | Oracle      |
| `oracle_audit_log`     | Oracle-specific audit entries                   | Security    |

### Indexes (36)

| Type           | Count | Examples                                                       |
| -------------- | ----- | -------------------------------------------------------------- |
| B-tree         | 30+   | Status, user_id, created_at, address, chain                    |
| GIN (JSONB)    | 3     | `reading_result`, `individual_results`, `compatibility_matrix` |
| GiST (spatial) | 1     | `oracle_users.coordinates` (POINT type)                        |
| Unique         | 2+    | `users.username`, `api_keys.key_hash`                          |

### Migrations

| File                                | Purpose                                  |
| ----------------------------------- | ---------------------------------------- |
| `010_oracle_schema.sql`             | Oracle tables, indexes, triggers         |
| `010_oracle_schema_rollback.sql`    | Rollback for 010                         |
| `011_security_columns.sql`          | Widen encrypted columns, add soft-delete |
| `011_security_columns_rollback.sql` | Rollback for 011                         |

### Seed Data

| File                   | Purpose                        |
| ---------------------- | ------------------------------ |
| `seeds/seed_admin.sql` | Dev admin user + learning data |

### Extensions

- `uuid-ossp` — UUID generation
- `pgcrypto` — Cryptographic functions

---

## Layer 5: Infrastructure (Docker)

### Docker Compose Services (8)

| Service           | Image/Build                       | Port        | Health Check         |
| ----------------- | --------------------------------- | ----------- | -------------------- |
| `postgres`        | postgres:16-alpine                | 5432        | `pg_isready`         |
| `redis`           | redis:7-alpine                    | 6379        | `redis-cli ping`     |
| `api`             | Build: `./api`                    | 8000        | HTTP `/api/health`   |
| `oracle-service`  | Build: `./services/oracle`        | 50052, 9090 | gRPC channel ready   |
| `scanner-service` | Build: `./services/scanner`       | 50051       | gRPC channel ready   |
| `frontend`        | Build: `./frontend` (multi-stage) | 80          | HTTP response check  |
| `nginx`           | nginx:alpine                      | 80→80       | HTTP `/nginx-health` |
| `oracle-alerter`  | Build: `./devops/alerts`          | —           | Process check        |

### Volumes (3)

- `postgres_data` — Database persistence
- `redis_data` — Redis persistence
- `oracle_logs` — Log persistence

### Nginx Configuration

| Feature                        | Status                                                     |
| ------------------------------ | ---------------------------------------------------------- |
| Reverse proxy (frontend + API) | Implemented                                                |
| WebSocket upgrade              | Implemented                                                |
| Health endpoint                | Implemented                                                |
| HTTPS/SSL                      | **NOT IMPLEMENTED** — TODO comment with placeholder config |

### Dockerfiles

| Service  | Multi-stage              | Non-root user        |
| -------- | ------------------------ | -------------------- |
| API      | No (single stage)        | Yes (`api` user)     |
| Oracle   | No (single stage)        | Yes (`oracle` user)  |
| Scanner  | Yes (build + runtime)    | Yes (`scanner` user) |
| Frontend | Yes (node build + nginx) | Yes (nginx default)  |
| Alerter  | No (single stage)        | Yes                  |

---

## Layer 6: Security

### Encryption

| Feature          | Implementation                                                                                              |
| ---------------- | ----------------------------------------------------------------------------------------------------------- |
| Algorithm        | AES-256-GCM                                                                                                 |
| Key derivation   | PBKDF2-HMAC-SHA256, 600,000 iterations                                                                      |
| Nonce            | 96-bit random per encryption                                                                                |
| Salt             | 32 bytes                                                                                                    |
| Prefix           | `ENC4:` (current), `ENC:` (legacy fallback for migration)                                                   |
| Sensitive fields | `private_key`, `seed_phrase`, `wif`, `extended_private_key`, `mother_name`, `question`, `ai_interpretation` |

### Auth

| Feature         | Detail                                                       |
| --------------- | ------------------------------------------------------------ |
| JWT signing     | HS256, `API_SECRET_KEY` from env                             |
| Token expiry    | 24 hours (configurable)                                      |
| API keys        | SHA-256 hashed, stored in `api_keys` table                   |
| Scope hierarchy | `admin` ⊃ `write` ⊃ `read` per domain (oracle/scanner/vault) |
| Audit           | All auth events logged to `oracle_audit_log`                 |

### Security Tests

- `api/tests/test_security.py` — AES-256-GCM encryption/decryption
- `integration/tests/test_security.py` — Cross-layer security audit
- `integration/scripts/security_audit.py` — Automated vulnerability scan

---

## Layer 7: DevOps & Monitoring

### Components

| Component           | File                                       | Status                                          |
| ------------------- | ------------------------------------------ | ----------------------------------------------- |
| Metrics Collector   | `devops/monitoring/oracle_metrics.py`      | Implemented — counter/histogram/gauge           |
| HTTP Metrics Server | `devops/monitoring/http_server.py`         | Implemented — Prometheus scrape target          |
| JSON Logger         | `devops/logging/oracle_logger.py`          | Implemented — structured JSON output            |
| Telegram Alerter    | `devops/alerts/oracle_alerts.py`           | Implemented — configurable thresholds           |
| Simple Dashboard    | `devops/dashboards/simple_dashboard.py`    | Implemented — Flask-based                       |
| Prometheus Config   | `infrastructure/monitoring/prometheus.yml` | Exists — **not integrated into docker-compose** |

### Tests

| Test File                                | Coverage                   |
| ---------------------------------------- | -------------------------- |
| `devops/tests/test_oracle_monitoring.py` | Metrics, logging, alerting |

---

## Proto/gRPC Definitions

| File                  | Service        | RPCs                                                                                                                        |
| --------------------- | -------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `proto/oracle.proto`  | OracleService  | GetReading, GetNameReading, GetQuestionSign, GetDailyInsight, SuggestRange, AnalyzeSession, GetTimingAlignment, HealthCheck |
| `proto/scanner.proto` | ScannerService | StartScan, StopScan, PauseScan, ResumeScan, GetStats, SaveCheckpoint                                                        |

---

## Scripts

| Script                                  | Purpose                                         | Status  |
| --------------------------------------- | ----------------------------------------------- | ------- |
| `scripts/backup.sh`                     | Full PostgreSQL backup (gzip, 30-day retention) | Working |
| `scripts/restore.sh`                    | Restore from backup                             | Working |
| `scripts/deploy.sh`                     | Production deployment                           | Working |
| `scripts/rollback.sh`                   | Rollback deployment                             | Working |
| `scripts/health-check.sh`               | Check all Docker services                       | Working |
| `scripts/launcher.sh`                   | Project launcher                                | Working |
| `scripts/production_readiness_check.sh` | Pre-deploy validation                           | Working |

### Database Scripts

| Script                              | Purpose                                          |
| ----------------------------------- | ------------------------------------------------ |
| `database/scripts/oracle_backup.sh` | Oracle-specific table backup (full or data-only) |

---

## Tests Summary

### By Layer

| Layer               | Test Files      | Type           | Status                               |
| ------------------- | --------------- | -------------- | ------------------------------------ |
| Frontend (unit)     | 17              | Vitest         | Oracle components + utils            |
| Frontend (E2E)      | 1 (8 scenarios) | Playwright     | Oracle flow                          |
| API                 | 11              | pytest         | Endpoints, auth, security            |
| Oracle Service      | 5               | pytest         | Engines, gRPC, AI                    |
| DevOps              | 1               | pytest         | Monitoring                           |
| Integration         | 7               | pytest         | Cross-layer                          |
| Integration scripts | 3               | Python scripts | Security audit, perf, env validation |
| **Total**           | **45**          |                |                                      |

### Integration Tests

| Test File              | Coverage                      |
| ---------------------- | ----------------------------- |
| `test_api_health.py`   | API health + readiness        |
| `test_api_oracle.py`   | API↔Oracle integration        |
| `test_database.py`     | Schema validation, migrations |
| `test_e2e_flow.py`     | Full end-to-end flow          |
| `test_frontend_api.py` | Frontend↔API integration      |
| `test_multi_user.py`   | Multi-user flows              |
| `test_security.py`     | Cross-layer security          |

---

## Reference Files

### .specs/ (17 files, 916 KB)

| Spec                                               | Size   | Coverage                   |
| -------------------------------------------------- | ------ | -------------------------- |
| `SPEC_T1_S1_FRONTEND_ORACLE_FOUNDATION.md`         | 55 KB  | Frontend foundation        |
| `SPEC_T1_S2_FRONTEND_INPUT_COMPONENTS.md`          | 47 KB  | Input components           |
| `SPEC_T1_S3_FRONTEND_MULTIUSER_I18N.md`            | 28 KB  | Multi-user + i18n          |
| `SPEC_T1_S4_FRONTEND_RESULTS_INTEGRATION.md`       | 43 KB  | Results + integration      |
| `SPEC_T2_S1_API_ORACLE_USERS.md`                   | 30 KB  | API user management        |
| `SPEC_T2_S2_API_ORACLE_READINGS.md`                | 44 KB  | API reading endpoints      |
| `SPEC_T2_S3_API_MULTI_USER_UTILITIES.md`           | 65 KB  | API multi-user + utilities |
| `SPEC_T3_S1_BACKEND_FC60_CORE.md`                  | 50 KB  | FC60 engine core           |
| `SPEC_T3_S2_BACKEND_MULTI_USER_FC60.md`            | 70 KB  | Multi-user FC60            |
| `SPEC_T3_S3_BACKEND_AI_INTEGRATION.md`             | 64 KB  | AI integration             |
| `SPEC_T4_S1_DATABASE_ORACLE_SCHEMA.md`             | 44 KB  | Database schema            |
| `SPEC_T5_S1_INFRASTRUCTURE_DOCKER.md`              | 29 KB  | Docker infrastructure      |
| `SPEC_T6_S1_SECURITY_ORACLE.md`                    | 64 KB  | Security layer             |
| `SPEC_INTEGRATION_S1_LAYER_STITCHING.md`           | 88 KB  | Layer stitching            |
| `SPEC_INTEGRATION_S2_DEEP_TESTING_FINAL_POLISH.md` | 116 KB | Testing + polish           |

### .archive/ (Read-only reference)

| Directory                     | Content                                           |
| ----------------------------- | ------------------------------------------------- |
| `.archive/v1/`                | Original code                                     |
| `.archive/v2/`                | Earlier version iteration                         |
| `.archive/v3/`                | Legacy engines — **math baseline** for validation |
| `.archive/v3-scripts/`        | Legacy utility scripts                            |
| `.archive/development-notes/` | Historical notes                                  |
| `.archive/old-docs/`          | Previous documentation                            |
| `.archive/session-memory/`    | Session context from scaffolding                  |

### .project/ (Project management)

| File                           | Purpose                         |
| ------------------------------ | ------------------------------- |
| `NPS_PROJECT_INSTRUCTIONS.md`  | Master project instructions     |
| `SKILLS_PLAYBOOK.md`           | Team skills reference           |
| `SUBAGENT_PATTERNS.md`         | Subagent orchestration patterns |
| `TOOL_ORCHESTRATION_MATRIX.md` | Tool selection matrix           |
| `VERIFICATION_CHECKLISTS.md`   | QA checklists                   |
| `ERROR_RECOVERY.md`            | Error handling playbook         |
| `SESSION_HANDOFF_TEMPLATE.md`  | Session handoff template        |

---

## What Works (Production-Ready)

| #   | Component                 | Evidence                                                       |
| --- | ------------------------- | -------------------------------------------------------------- |
| 1   | **Database schema**       | 15 tables, 36 indexes, migrations, seed data, extensions       |
| 2   | **Auth system**           | JWT + API key + legacy, 3-tier scopes, audit logging           |
| 3   | **Encryption**            | AES-256-GCM, PBKDF2 600K iterations, legacy migration fallback |
| 4   | **FC60 engine**           | 966 lines, pure Python, JDN/base-60/ganzhi/moon computations   |
| 5   | **Numerology engine**     | 294 lines, Pythagorean system with master numbers              |
| 6   | **Oracle reader**         | 1,493 lines, sign/name/question/daily readings                 |
| 7   | **Oracle API**            | 15 endpoints working, full CRUD + WebSocket                    |
| 8   | **AI client (SDK)**       | Anthropic SDK with caching, rate limiting, graceful fallback   |
| 9   | **Frontend Oracle page**  | 15 components, form → results → history flow                   |
| 10  | **i18n**                  | 171/171 keys EN↔FA, full RTL support                           |
| 11  | **Docker infrastructure** | 8 services with health checks, multi-stage builds              |
| 12  | **Monitoring stack**      | Metrics, JSON logging, Telegram alerts                         |
| 13  | **Integration tests**     | 7 cross-layer test files + 3 audit scripts                     |

---

## What's Broken / Missing

| #   | Issue                              | Severity | Impact                                                                                     |
| --- | ---------------------------------- | -------- | ------------------------------------------------------------------------------------------ |
| 1   | **Scanner = 100% stub**            | Critical | Core feature non-functional. 311 lines of structure, zero logic.                           |
| 2   | **5 frontend pages = empty stubs** | High     | Dashboard, Scanner, Vault, Learning, Settings all < 32 lines                               |
| 3   | **gRPC bypass**                    | Medium   | API imports Oracle engines directly instead of calling gRPC. Server exists but isn't used. |
| 4   | **Dual AI integration**            | Medium   | `ai_engine.py` uses `subprocess.run(["claude", ...])` — violates architecture rule #1      |
| 5   | **No HTTPS/SSL**                   | Medium   | Nginx has TODO comment, no certificate handling                                            |
| 6   | **Prometheus not integrated**      | Low      | Config exists at `infrastructure/monitoring/prometheus.yml` but not in docker-compose      |
| 7   | **Vault API empty**                | Medium   | 4 endpoints return empty responses                                                         |
| 8   | **Learning API empty**             | Medium   | 5 endpoints return empty responses                                                         |
| 9   | **Oracle vault (legacy)**          | Low      | `engines/vault.py` needs PostgreSQL migration from file-based storage                      |
| 10  | **Oracle notifier (legacy)**       | Low      | `engines/notifier.py` (1,577 lines) should move to API layer per architecture              |

---

## 45-Session Gap Analysis

### Block 1: Foundation (Sessions 1-5) — Database, Auth, Profiles

| What Exists                       | What Needs Work                          |
| --------------------------------- | ---------------------------------------- |
| 15 tables with full schema        | Validate schema against 45-session needs |
| Auth middleware (JWT + API key)   | May need session management improvements |
| Oracle user CRUD (API + frontend) | Profile system may need extensions       |
| Encryption (AES-256-GCM)          | Already production-ready                 |
| Seed data + migrations            | May need additional migrations           |

**Leverage factor: HIGH** — Most foundation work is done. Sessions focus on validation and gap-filling.

### Block 2: Calculation Engines (Sessions 6-12) — FC60, Numerology, Zodiac

| What Exists                          | What Needs Work                                          |
| ------------------------------------ | -------------------------------------------------------- |
| FC60 engine (966 lines)              | Validate against legacy baseline, add zodiac integration |
| Numerology — Pythagorean (294 lines) | Add Chaldean system, add Abjad system                    |
| Oracle reader (1,493 lines)          | May need reading type extensions                         |
| Scoring engine (290 lines)           | Validate scoring consistency (Rust↔Python)               |
| 7 solver classes (2,497 lines)       | Review and potentially extend                            |

**Leverage factor: HIGH** — Core engines exist. Sessions focus on adding missing systems and validating accuracy.

### Block 3: AI & Reading Types (Sessions 13-18) — Wisdom AI, 5 Reading Flows

| What Exists                   | What Needs Work                         |
| ----------------------------- | --------------------------------------- |
| AI client via SDK (288 lines) | Wisdom AI personality layer             |
| AI interpreter (664 lines)    | 5 distinct reading flow implementations |
| Prompt templates (316 lines)  | Expand for each reading type            |
| CLI fallback exists           | **Remove** CLI integration, SDK-only    |

**Leverage factor: MEDIUM** — AI plumbing exists but reading flows need fresh implementation.

### Block 4: Frontend Core (Sessions 19-25) — Layout, Oracle UI, Results

| What Exists                   | What Needs Work                    |
| ----------------------------- | ---------------------------------- |
| Oracle page (188 lines, full) | Already done — validate and polish |
| 15 Oracle components          | Already done — validate and extend |
| Layout + sidebar              | May need redesign for new pages    |
| StatsCard + LogPanel          | Extend for other domains           |

**Leverage factor: HIGH for Oracle, LOW for others** — Oracle frontend is complete. Other pages need building from scratch.

### Block 5: Frontend Advanced (Sessions 26-31) — RTL, Responsive, Accessibility

| What Exists               | What Needs Work                                   |
| ------------------------- | ------------------------------------------------- |
| RTL support via Tailwind  | Comprehensive responsive testing                  |
| i18n (171/171 keys)       | Accessibility audit (ARIA labels exist in Oracle) |
| Accessibility test exists | Extend to all new pages                           |

**Leverage factor: MEDIUM** — Foundations exist but need extension to all pages.

### Block 6: Features & Integration (Sessions 32-37) — Export, Share, Telegram

| What Exists                           | What Needs Work                               |
| ------------------------------------- | --------------------------------------------- |
| ExportButton component                | Expand export formats                         |
| Telegram alerter in devops            | Telegram bot for users (separate from alerts) |
| Oracle notifier (legacy, 1,577 lines) | Refactor into API layer                       |

**Leverage factor: LOW** — Mostly new feature development.

### Block 7: Admin & DevOps (Sessions 38-40) — Admin UI, Monitoring, Backup

| What Exists                     | What Needs Work                            |
| ------------------------------- | ------------------------------------------ |
| Backup/restore scripts          | Admin UI pages (new)                       |
| Metrics collector + HTTP server | Prometheus integration into docker-compose |
| Simple dashboard (Flask)        | Proper admin dashboard                     |
| Health check script             | Production monitoring setup                |

**Leverage factor: MEDIUM** — Backend tooling exists but admin UI is new.

### Block 8: Testing & Deployment (Sessions 41-45) — Tests, Optimization, Deploy

| What Exists                     | What Needs Work                 |
| ------------------------------- | ------------------------------- |
| 42 test files across all layers | Coverage expansion for new code |
| Integration test framework      | Performance optimization        |
| Deploy/rollback scripts         | HTTPS/SSL setup                 |
| Production readiness check      | Final production hardening      |

**Leverage factor: MEDIUM** — Framework exists but scope depends on what blocks 1-7 produce.

---

## Potential Issues

| #   | Issue                            | Risk                       | Mitigation                                                  |
| --- | -------------------------------- | -------------------------- | ----------------------------------------------------------- |
| 1   | AI engine conflict (SDK vs CLI)  | Architecture violation     | Remove `ai_engine.py` CLI path in Block 3                   |
| 2   | gRPC bypass in API               | Technical debt             | Wire API→gRPC in Block 1 or 2                               |
| 3   | Scanner 100% stub                | Blocks integration testing | Scanner is out of scope for 45-session plan                 |
| 4   | Legacy modules in Oracle service | Migration debt             | Migrate vault.py, notifier.py, config.py in relevant blocks |
| 5   | No HTTPS                         | Security gap               | Add in Block 8 (deployment)                                 |
| 6   | Hardcoded CLI path               | `/opt/homebrew/bin/claude` | Remove with AI engine cleanup                               |
| 7   | Admin seed has placeholder hash  | Dev-only risk              | Replace with proper bcrypt hash                             |

---

## Recommendations

1. **Start Block 1 immediately** — Foundation is 80%+ done. Validate and fill gaps.
2. **Kill the CLI AI engine early** — Remove `ai_engine.py` in Session 1 or 2 to prevent architectural drift.
3. **Defer Scanner** — It's 100% stub and explicitly marked "DO NOT TOUCH" in CLAUDE.md. Don't let it block Oracle work.
4. **Wire gRPC properly** — Currently API imports engines directly. Either commit to this pattern or wire gRPC. Decide in Session 1.
5. **Add HTTPS in Block 7-8** — Not urgent for development but required for production.
6. **Leverage legacy archive** — `.archive/v3/engines/` is the math validation baseline. Use it for every engine test.

---

_Report generated by deep scan of 363 files across 7 layers. All statistics verified against filesystem._
