# NPS V4 — Numerology Puzzle Solver (Web Edition)

A distributed microservices architecture for FC60 numerology, oracle readings, and mathematical analysis. V4 transforms the V3 Python/tkinter desktop app into a web-accessible platform.

## Architecture

```
Browser (localhost:5173)
  |
  | Vite proxy /api -> :8000
  v
FastAPI API (:8000)
  |-- SQLAlchemy --> PostgreSQL (:5432)
  |-- redis.asyncio --> Redis (:6379) [optional]
  |-- sys.path shim --> V3 Oracle engines (direct import)
  |-- Auth middleware (JWT / API key / legacy)
  |-- Encryption service (AES-256-GCM, ENC4: prefix)
  |-- Audit logging (oracle_audit_log table)
```

## Current Status

| Component                        | Status           |
| -------------------------------- | ---------------- |
| Oracle API (13 endpoints)        | Production-ready |
| Oracle Frontend (React)          | Production-ready |
| PostgreSQL + Schema              | Production-ready |
| Auth (JWT + API key + legacy)    | Production-ready |
| Encryption at rest (AES-256-GCM) | Production-ready |
| Scanner service (Rust)           | Stub (Phase 4)   |
| Vault/Learning endpoints         | Stub (Phase 3)   |
| Frontend pages (non-Oracle)      | Stub (Phase 5)   |

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Python 3.11+
- Node.js 18+

### 1. Clone and configure

```bash
git clone https://github.com/DaveXRouz/BTC.git
cd BTC
cp .env.example .env
# Edit .env with your settings (generate encryption keys, set API_SECRET_KEY)
```

### 2. Start infrastructure

```bash
docker compose up -d postgres redis
```

### 3. Initialize database

```bash
docker compose exec postgres psql -U nps -d nps -f /docker-entrypoint-initdb.d/init.sql
```

### 4. Start API server

```bash
cd api && pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Start frontend

```bash
cd frontend && npm install && npm run dev
```

Open http://localhost:5173 in your browser.

## Development Workflow

```bash
# Run all tests
make test

# Run integration tests (requires running API + DB)
make test-integration

# Run E2E browser tests
make test-e2e

# Performance audit
python3 integration/scripts/perf_audit.py

# Security audit
python3 integration/scripts/security_audit.py

# Lint
make lint

# Format
make format
```

## API Documentation

- **Swagger UI:** http://localhost:8000/docs (auto-generated)
- **API Reference:** [docs/api/API_REFERENCE.md](docs/api/API_REFERENCE.md)
- **Deployment Guide:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Troubleshooting:** [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## Configuration

All configuration via environment variables. See [.env.example](.env.example) for full list.

Key variables:

| Variable              | Description                          | Required       |
| --------------------- | ------------------------------------ | -------------- |
| `POSTGRES_PASSWORD`   | Database password                    | Yes            |
| `API_SECRET_KEY`      | JWT signing key + legacy auth token  | Yes            |
| `NPS_ENCRYPTION_KEY`  | AES-256-GCM encryption key (hex)     | For encryption |
| `NPS_ENCRYPTION_SALT` | Encryption salt (hex)                | For encryption |
| `ANTHROPIC_API_KEY`   | Anthropic API for AI interpretations | Optional       |

## Repository Layout

```
BTC/
├── api/                  # FastAPI REST + WebSocket gateway
│   ├── app/routers/      # 6 routers: health, auth, scanner, oracle, vault, learning
│   ├── app/models/       # Pydantic request/response schemas
│   ├── app/middleware/    # Auth (JWT + API keys), rate limiting
│   ├── app/orm/          # SQLAlchemy ORM models
│   └── app/services/     # Business logic (oracle_reading, security, audit)
├── frontend/             # React + TypeScript + Tailwind (Vite)
│   ├── src/pages/        # 6 pages: Dashboard, Scanner, Oracle, Vault, Learning, Settings
│   ├── src/components/   # Shared + Oracle-specific components
│   └── e2e/              # Playwright browser tests
├── services/
│   ├── oracle/           # Python Oracle service (V3 engines)
│   └── scanner/          # Rust scanner (stub)
├── database/             # PostgreSQL schema (init.sql) + migrations
├── integration/          # Integration tests, scripts, reports
├── docs/                 # Architecture, API reference, deployment
├── .archive/             # Legacy versions (V1, V2, V3)
└── docker-compose.yml    # 7-container orchestration
```

## License

Private repository.
