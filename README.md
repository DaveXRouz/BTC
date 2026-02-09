# NPS — Numerology Puzzle Solver (Web Edition)

A distributed microservices system for Bitcoin wallet discovery through numerological pattern analysis. NPS transforms the legacy desktop app into a web-accessible platform with AI-powered Oracle guidance.

---

## How It Works

```
Scanner (Rust)              Oracle (Python)
Generates keys              Analyzes patterns
Checks balances             Suggests lucky ranges
5000+ keys/sec              FC60 + Numerology + AI
        \                   /
         \                 /
          ▼               ▼
       ┌─────────────────────┐
       │     PostgreSQL       │
       │  Shared learning DB  │
       │  Self-improving loop │
       └─────────┬───────────┘
                 │
          ┌──────▼──────┐
          │  FastAPI     │
          │  REST + WS   │
          └──────┬──────┘
                 │
          ┌──────▼──────┐
          │  React UI    │
          │  EN + FA     │
          └─────────────┘
```

## Current Status

| Component                    | Status                            |
| ---------------------------- | --------------------------------- |
| Oracle API (13 endpoints)    | Scaffolded — rewriting logic      |
| Oracle Frontend (React)      | Scaffolded — rewriting components |
| PostgreSQL + Schema          | Production-ready                  |
| Auth (JWT + API key)         | Production-ready                  |
| Encryption (AES-256-GCM)     | Production-ready                  |
| Scanner (Rust)               | Stub — future project             |
| Bilingual (EN + Persian RTL) | In progress                       |
| AI Interpretation            | In progress                       |

**Active work:** 45-session Oracle rebuild.

---

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Python 3.11+
- Node.js 18+

### Setup

```bash
git clone https://github.com/DaveXRouz/NPS.git
cd NPS
cp .env.example .env        # Edit with your settings
docker compose up -d postgres redis
docker compose exec postgres psql -U nps -d nps -f /docker-entrypoint-initdb.d/init.sql
cd api && pip install -e ".[dev]" && uvicorn app.main:app --reload &
cd frontend && npm install && npm run dev
```

Open http://localhost:5173

---

## Development Commands

```bash
make up              # Start all services
make dev-api         # FastAPI :8000
make dev-frontend    # Vite :5173
make test            # All tests
make lint            # Lint all
make format          # Format all
make backup          # Backup database
```

---

## Documentation

| Doc             | Location                          |
| --------------- | --------------------------------- |
| API Swagger     | http://localhost:8000/docs        |
| API Reference   | `docs/api/API_REFERENCE.md`       |
| Architecture    | `logic/ARCHITECTURE_DECISIONS.md` |
| FC60 Algorithm  | `logic/FC60_ALGORITHM.md`         |
| Deployment      | `docs/DEPLOYMENT.md`              |
| Troubleshooting | `docs/TROUBLESHOOTING.md`         |

---

## Configuration

All via environment variables. See `.env.example` for full list.

| Variable             | Purpose               | Required       |
| -------------------- | --------------------- | -------------- |
| `POSTGRES_PASSWORD`  | Database password     | Yes            |
| `API_SECRET_KEY`     | JWT signing key       | Yes            |
| `NPS_ENCRYPTION_KEY` | AES-256-GCM key (hex) | For encryption |
| `ANTHROPIC_API_KEY`  | AI interpretations    | Optional       |

---

## License

Private repository.
