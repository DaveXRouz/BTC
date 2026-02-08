# NPS V4 Deployment Guide

## Prerequisites

- Docker 24+ and Docker Compose v2
- At least 2GB RAM available
- PostgreSQL 15+ (or use Docker)
- Node.js 18+ (for frontend builds)
- Python 3.11+ (for API)

## Docker Compose Deployment

### 1. Configure environment

```bash
cd v4
cp .env.example .env
```

Edit `.env` with production values:

```bash
# Generate secure keys:
python3 -c "import secrets; print(f'API_SECRET_KEY={secrets.token_hex(32)}')"
python3 -c "import secrets; print(f'NPS_ENCRYPTION_KEY={secrets.token_hex(32)}')"
python3 -c "import secrets; print(f'NPS_ENCRYPTION_SALT={secrets.token_hex(16)}')"
```

Set `POSTGRES_PASSWORD` to a strong password.

### 2. Start all services

```bash
docker compose up -d
```

This starts:

- PostgreSQL (port 5432)
- Redis (port 6379)
- API server (port 8000)
- Frontend (port 5173 dev / 80 production)

### 3. Initialize database

On first run, the database schema is applied automatically via Docker init scripts.

For manual initialization:

```bash
docker compose exec postgres psql -U nps -d nps -f /docker-entrypoint-initdb.d/init.sql
```

### 4. Verify deployment

```bash
# Health check
curl http://localhost:8000/api/health

# Run production readiness check
chmod +x scripts/production_readiness_check.sh
./scripts/production_readiness_check.sh
```

## Manual Deployment (Without Docker)

### Database

```bash
# Install PostgreSQL and create database
psql -U postgres -c "CREATE USER nps WITH PASSWORD 'your-password';"
psql -U postgres -c "CREATE DATABASE nps OWNER nps;"
psql -U nps -d nps -f database/init.sql
```

### API Server

```bash
cd api
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For production, use Gunicorn:

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend

```bash
cd frontend
npm install
npm run build
# Serve dist/ via nginx or any static server
```

## Environment Variables

See [.env.example](../.env.example) for the complete list with descriptions.

### Required

| Variable            | Description                         |
| ------------------- | ----------------------------------- |
| `POSTGRES_HOST`     | Database host (default: `postgres`) |
| `POSTGRES_PORT`     | Database port (default: `5432`)     |
| `POSTGRES_DB`       | Database name (default: `nps`)      |
| `POSTGRES_USER`     | Database user (default: `nps`)      |
| `POSTGRES_PASSWORD` | Database password                   |
| `API_SECRET_KEY`    | JWT signing key + legacy auth       |

### Optional

| Variable              | Description                                      |
| --------------------- | ------------------------------------------------ |
| `REDIS_HOST`          | Redis host (graceful degradation if unavailable) |
| `NPS_ENCRYPTION_KEY`  | AES-256-GCM key for encryption at rest           |
| `NPS_ENCRYPTION_SALT` | Encryption salt                                  |
| `ANTHROPIC_API_KEY`   | For AI interpretations (degrades gracefully)     |
| `NPS_BOT_TOKEN`       | Telegram bot token                               |

## SSL/TLS

For production, use a reverse proxy (nginx) with SSL:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        root /var/www/nps-frontend/dist;
        try_files $uri /index.html;
    }

    # WebSocket support
    location /api/oracle/ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Monitoring

- **Health endpoint:** `GET /api/health` — use for load balancer health checks
- **Swagger UI:** `http://localhost:8000/docs` — interactive API documentation
- **Logs:** `docker compose logs -f api`

## Backup and Restore

```bash
# Backup
./scripts/backup.sh

# Restore
./scripts/restore.sh
```

## Updating

```bash
git pull
docker compose build
docker compose up -d
```

If database schema has changed, re-run migrations:

```bash
docker compose exec postgres psql -U nps -d nps -f /docker-entrypoint-initdb.d/init.sql
```
