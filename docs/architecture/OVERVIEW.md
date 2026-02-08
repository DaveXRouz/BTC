# V4 Architecture Overview

## 7-Layer Distributed Architecture

NPS V4 transforms the V3 Python/Tkinter monolith into a distributed microservices architecture targeting web deployment.

```
┌─────────────────────────────────────────────────────┐
│                   Layer 1: Frontend                  │
│              React + TypeScript + Tailwind           │
│                  (Vite, port 5173)                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│            Layer 2: Reverse Proxy (Nginx)            │
│        SSL termination, rate limiting, routing       │
│                    (port 443/80)                     │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│            Layer 3: API Gateway (FastAPI)            │
│     REST + WebSocket, JWT/API key auth, models      │
│                    (port 8000)                       │
│                                                     │
├──────────────────────┬──────────────────────────────┤
│                      │                              │
│  Layer 4: Scanner    │   Layer 5: Oracle Service    │
│     (Rust/gRPC)      │      (Python/gRPC)           │
│    (port 50051)      │     (port 50052)             │
│                      │                              │
│  - Key generation    │  - FC60 numerology           │
│  - Address derivation│  - Oracle readings           │
│  - Balance checking  │  - AI learning               │
│  - Checkpoints       │  - Timing/strategy           │
│                      │  - Scoring                   │
├──────────────────────┴──────────────────────────────┤
│                                                     │
│            Layer 6: Database (PostgreSQL)            │
│          10 tables, encrypted findings,             │
│          session/checkpoint persistence             │
│                    (port 5432)                       │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│          Layer 7: Infrastructure & DevOps           │
│      Docker Compose, Prometheus, backup scripts     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Component Relationships

### Data Flow

```
User Browser
    │
    ▼
React Frontend ──HTTP/WS──▶ Nginx ──proxy──▶ FastAPI Gateway
                                                  │
                                         ┌────────┴────────┐
                                         │                 │
                                    gRPC │            gRPC │
                                         ▼                 ▼
                                   Rust Scanner    Python Oracle
                                         │                 │
                                         └────────┬────────┘
                                                  │
                                                  ▼
                                             PostgreSQL
```

### Communication Rules

1. **Frontend -> API only** — React never calls gRPC services directly
2. **API -> Services via gRPC** — Protobuf contracts in `proto/` are the source of truth
3. **Services -> Database** — Each service manages its own data through the API layer
4. **No service-to-service calls** — Scanner and Oracle do not communicate directly

### Real-Time Updates

The WebSocket connection (`/ws`) provides:

- Scanner progress (keys/sec, keys tested, checkpoints)
- Finding alerts (balance found, high scores)
- Health status changes
- AI learning events (level up, insights)

## V3 to V4 Migration Path

| V3 Component                    | V4 Home                                                      | Status           |
| ------------------------------- | ------------------------------------------------------------ | ---------------- |
| `nps/engines/fc60.py`           | Oracle service engines                                       | Copied as-is     |
| `nps/engines/numerology.py`     | Oracle service engines                                       | Copied as-is     |
| `nps/engines/oracle.py`         | Oracle service engines                                       | Copied as-is     |
| `nps/engines/scoring.py`        | Oracle service engines                                       | Copied as-is     |
| `nps/engines/crypto.py`         | Rust scanner (reference in `scanner/docs/`)                  | Rewrite to Rust  |
| `nps/engines/bip39.py`          | Rust scanner (reference in `scanner/docs/`)                  | Rewrite to Rust  |
| `nps/engines/balance.py`        | Rust scanner (reference in `scanner/docs/`)                  | Rewrite to Rust  |
| `nps/solvers/unified_solver.py` | Rust scanner                                                 | Rewrite to Rust  |
| `nps/gui/*.py`                  | React frontend (reference in `frontend/desktop-gui/legacy/`) | Rewrite to React |
| `nps/engines/vault.py`          | PostgreSQL `findings` table                                  | Adapt for SQL    |
| `nps/engines/config.py`         | Environment variables                                        | Adapt for .env   |
| `config.json`                   | `.env` + PostgreSQL `config` table                           | Migrate          |

## Security Architecture

- **Transport:** TLS via nginx (external), plain gRPC (internal Docker network)
- **Authentication:** JWT tokens (web) + API keys (programmatic/Telegram)
- **Encryption at rest:** AES-256-GCM (`ENC4:` prefix) for sensitive fields
- **Legacy support:** V3 `ENC:` (PBKDF2 + HMAC-SHA256) decrypt for migration
- **Key material:** Never leaves server; frontend displays only masked values

## Phase Roadmap

| Phase | Description                                | Dependencies |
| ----- | ------------------------------------------ | ------------ |
| 0     | Scaffolding (93 files)                     | None         |
| 1     | Foundation: DB + API skeleton + encryption | Phase 0      |
| 2     | Python Oracle service (gRPC)               | Phase 1      |
| 3     | API layer (all endpoints wired)            | Phase 1, 2   |
| 4     | Rust scanner                               | Phase 1      |
| 5     | React frontend                             | Phase 3      |
| 6     | Infrastructure + DevOps                    | Phase 4, 5   |
| 7     | Integration testing + polish               | Phase 6      |
