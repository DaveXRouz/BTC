# V4 API Gateway

## Overview

FastAPI-based REST + WebSocket gateway. This is the single entry point for all clients (React frontend, Telegram bot, external integrations). The API layer proxies requests to backend services (scanner, oracle) via gRPC.

## Tech Stack

- **FastAPI** with async support
- **JWT + API key** authentication
- **WebSocket** for real-time updates
- **gRPC clients** for scanner and oracle services
- **Pydantic** models for request/response validation

## Routers

| Router        | Prefix      | Description                                |
| ------------- | ----------- | ------------------------------------------ |
| `health.py`   | `/health`   | Service health, readiness, liveness        |
| `auth.py`     | `/auth`     | Login, token refresh, API key management   |
| `scanner.py`  | `/scanner`  | Start/stop scans, status, checkpoints      |
| `oracle.py`   | `/oracle`   | Oracle readings, questions, insights       |
| `vault.py`    | `/vault`    | Findings CRUD, encrypted storage           |
| `learning.py` | `/learning` | XP/level, learning history, AI suggestions |

## Directory Structure

```
app/
  routers/        — 6 route modules
  models/         — Pydantic request/response schemas
  middleware/     — Auth (JWT + API keys), rate limiting
  services/       — WebSocket manager, security utilities
```

## Authentication

Two auth modes:

1. **JWT tokens** — For web frontend (login -> access token + refresh token)
2. **API keys** — For Telegram bot and programmatic access (X-API-Key header)

Rate limiting applies per-key/per-user with configurable thresholds.

## Key Commands

```bash
# Development server (port 8000)
uvicorn app.main:app --reload --port 8000

# Run tests
pytest tests/ -v
```

## Architecture Rules

- API is the **only gateway** — clients never call gRPC services directly.
- All scanner/oracle operations go through gRPC to their respective services.
- Environment variables (`.env`) for configuration, not config files.
- WebSocket manager broadcasts real-time events from scanner and oracle services.
