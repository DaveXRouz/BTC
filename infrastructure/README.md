# V4 Infrastructure

## Overview

Docker-based deployment with nginx reverse proxy and Prometheus monitoring.

## Components

### Docker Compose (`docker-compose.yml`)

7-container orchestration:

| Container    | Service              | Port  |
| ------------ | -------------------- | ----- |
| `frontend`   | React (nginx-served) | 80    |
| `api`        | FastAPI gateway      | 8000  |
| `scanner`    | Rust scanner (gRPC)  | 50051 |
| `oracle`     | Python Oracle (gRPC) | 50052 |
| `postgres`   | PostgreSQL 15        | 5432  |
| `nginx`      | Reverse proxy        | 443   |
| `prometheus` | Monitoring           | 9090  |

### Nginx (`nginx/`)

- SSL termination
- Reverse proxy to API and frontend
- WebSocket upgrade handling for `/ws` paths
- Rate limiting at the edge

### Monitoring (`monitoring/`)

- Prometheus scrape configs for all services
- Health check endpoints per service
- Metrics: scan rate, API latency, error rates, active connections

## Key Commands

```bash
# Start all services
cd v4 && docker-compose up -d

# View logs
docker-compose logs -f api scanner oracle

# Scale scanner workers
docker-compose up -d --scale scanner=3

# Stop all
docker-compose down
```

## Environment Variables

All configuration via `.env` file (see `.env.example`):

- `DATABASE_URL` — PostgreSQL connection string
- `JWT_SECRET` — JWT signing key
- `ENCRYPTION_KEY` — AES-256-GCM key for vault
- `TELEGRAM_BOT_TOKEN` — Telegram bot token
- API keys for chain providers (Etherscan, BSCScan, etc.)
