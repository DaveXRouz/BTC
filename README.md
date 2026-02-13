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
          v               v
       +---------------------+
       |     PostgreSQL       |
       |  Shared learning DB  |
       |  Self-improving loop |
       +---------+-----------+
                 |
          +------v------+
          |  FastAPI     |
          |  REST + WS   |
          +------+------+
                 |
          +------v------+
          |  React UI    |
          |  EN + FA     |
          +-------------+
```

## Current Status

| Component                    | Status                |
| ---------------------------- | --------------------- |
| Oracle API (20+ endpoints)   | Production-ready      |
| Oracle Frontend (React)      | Production-ready      |
| PostgreSQL + Schema          | Production-ready      |
| Auth (JWT + API key)         | Production-ready      |
| Encryption (AES-256-GCM)     | Production-ready      |
| Bilingual (EN + Persian RTL) | Production-ready      |
| AI Interpretation            | Production-ready      |
| Admin Panel                  | Production-ready      |
| Telegram Bot                 | Production-ready      |
| Export (PDF/CSV)             | Production-ready      |
| Monitoring & Backup          | Production-ready      |
| Scanner (Rust)               | Stub — future project |

### Final Metrics

```
Sessions: 45 | Layers: 7 | Endpoints: 20+ | Components: 30+
Tables: 10+ | Tests: 800+ | Docker services: 10 | Locales: EN + FA (RTL)
```

---

## Quick Start

### Prerequisites

- Docker 24+ and Docker Compose v2
- Python 3.11+
- Node.js 18+

### Docker Deploy (Recommended)

```bash
git clone https://github.com/DaveXRouz/NPS.git
cd NPS
cp .env.example .env

# Generate secure keys:
python3 -c "import secrets; print(f'API_SECRET_KEY={secrets.token_hex(32)}')"
python3 -c "import secrets; print(f'NPS_ENCRYPTION_KEY={secrets.token_hex(32)}')"
python3 -c "import secrets; print(f'NPS_ENCRYPTION_SALT={secrets.token_hex(16)}')"
python3 -c "import secrets; print(f'POSTGRES_PASSWORD={secrets.token_hex(16)}')"

# Edit .env with generated values, then:
docker compose up -d

# Verify
curl http://localhost:8000/api/health
```

### Railway Deploy

```bash
# 1. Install Railway CLI
npm i -g @railway/cli && railway login

# 2. Create project and link
railway init && railway link

# 3. Add PostgreSQL and Redis plugins via Railway dashboard

# 4. Set environment variables
railway variables set API_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
railway variables set NPS_ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# 5. Deploy
railway up
```

### Local Development

```bash
git clone https://github.com/DaveXRouz/NPS.git
cd NPS
cp .env.example .env        # Edit with your settings
docker compose up -d postgres redis
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

## Architecture

```
+---------------------------------------------+
|  LAYER 1: FRONTEND                          |
|  React + TypeScript + Tailwind + Vite       |
|  Port: 5173 (dev) / 80 (prod nginx)        |
|  i18n: English + Persian (RTL)              |
+--------------+------------------------------+
               | HTTP / WebSocket
+--------------v------------------------------+
|  LAYER 2: API GATEWAY                       |
|  FastAPI + Python 3.11+                     |
|  Port: 8000 | Docs: /docs (Swagger)        |
|  Auth: JWT + API Key + Legacy               |
+------+-------------------+------------------+
       | SQLAlchemy         | gRPC
+------v------+    +-------v------------------+
|  LAYER 4:   |    |  LAYER 3: BACKEND        |
|  DATABASE   |    |  Oracle (Python :50052)   |
|  PostgreSQL |<---|  Scanner (Rust :50051)    |
|  Port: 5432 |    |  AI via Anthropic API     |
+-------------+    +--------------------------+

LAYER 5: Docker Compose (10 containers)
LAYER 6: AES-256-GCM + API keys (3-tier)
LAYER 7: JSON logging + Prometheus + Telegram alerts
```

---

## Documentation

| Doc              | Location                          |
| ---------------- | --------------------------------- |
| API Swagger      | http://localhost:8000/docs        |
| API Reference    | `docs/api/API_REFERENCE.md`       |
| Architecture     | `logic/ARCHITECTURE_DECISIONS.md` |
| FC60 Algorithm   | `logic/FC60_ALGORITHM.md`         |
| Deployment Guide | `docs/DEPLOYMENT.md`              |
| Troubleshooting  | `docs/TROUBLESHOOTING.md`         |

---

## Configuration

All via environment variables. See `.env.example` for full list.

| Variable              | Purpose               | Required       |
| --------------------- | --------------------- | -------------- |
| `POSTGRES_PASSWORD`   | Database password     | Yes            |
| `API_SECRET_KEY`      | JWT signing key       | Yes            |
| `NPS_ENCRYPTION_KEY`  | AES-256-GCM key (hex) | For encryption |
| `NPS_ENCRYPTION_SALT` | Encryption salt (hex) | For encryption |
| `ANTHROPIC_API_KEY`   | AI interpretations    | Optional       |
| `NPS_BOT_TOKEN`       | Telegram bot token    | Optional       |

---

## Security

- AES-256-GCM encryption at rest (`ENC4:` prefix)
- JWT + API key authentication with SHA-256 hashed keys
- Three-tier RBAC: admin / moderator / user
- Nginx rate limiting (30r/s API, 5r/s auth)
- Security headers (X-Content-Type-Options, X-Frame-Options, HSTS)
- 20+ automated security checks via `integration/scripts/security_audit.py`
- No hardcoded secrets (`.env` only)

---

## License

Private repository.
