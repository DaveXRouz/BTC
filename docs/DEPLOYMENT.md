# NPS Deployment Guide

> Complete deployment reference for the NPS (Numerology Puzzle Solver) platform.
> Covers Railway, Docker Compose, and manual deployment strategies.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Railway Deployment](#2-railway-deployment)
3. [Self-Hosted Docker Compose](#3-self-hosted-docker-compose)
4. [Manual Deployment](#4-manual-deployment)
5. [Environment Variables Reference](#5-environment-variables-reference)
6. [SSL/TLS Configuration](#6-ssltls-configuration)
7. [Database Setup and Migration](#7-database-setup-and-migration)
8. [Monitoring and Health Checks](#8-monitoring-and-health-checks)
9. [Backup and Restore](#9-backup-and-restore)
10. [Scaling](#10-scaling)
11. [Rollback Procedures](#11-rollback-procedures)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Prerequisites

### Required Software

| Software          | Minimum Version | Purpose                    |
| ----------------- | --------------- | -------------------------- |
| Docker            | 24.0+           | Container orchestration    |
| Docker Compose    | 2.20+           | Multi-container management |
| Python            | 3.11+           | API and Oracle services    |
| Node.js           | 18.0+           | Frontend build toolchain   |
| PostgreSQL client | 15+             | Database management (psql) |
| Git               | 2.30+           | Source control             |

### Optional Software

| Software       | Purpose                                      |
| -------------- | -------------------------------------------- |
| Railway CLI    | Railway deployment (`npm i -g @railway/cli`) |
| Rust toolchain | Scanner service (stub, not yet required)     |
| Nginx          | Manual deployment reverse proxy              |
| Certbot        | Let's Encrypt SSL certificates               |
| Make           | Convenience targets via Makefile             |

### System Requirements

| Resource | Development | Production |
| -------- | ----------- | ---------- |
| CPU      | 2 cores     | 4+ cores   |
| RAM      | 4 GB        | 8+ GB      |
| Disk     | 10 GB       | 50+ GB     |
| Network  | Localhost   | Public IP  |

### Verify Prerequisites

```bash
docker --version          # Docker 24.0+
docker compose version    # Docker Compose 2.20+
python3 --version         # Python 3.11+
node --version            # Node.js 18+
psql --version            # PostgreSQL client 15+
git --version             # Git 2.30+
```

---

## 2. Railway Deployment

Railway provides the fastest path to production with managed PostgreSQL, Redis, auto-SSL, and zero-config deployments.

### 2.1 Create Railway Project

```bash
# Install Railway CLI
npm install -g @railway/cli

# Authenticate
railway login

# Initialize in the NPS repo root
cd /path/to/NPS
railway init
```

### 2.2 Add Database and Cache Plugins

In the Railway dashboard:

1. Open your project.
2. Click **+ New** and select **Database > PostgreSQL**. Railway provisions PostgreSQL 15 with automatic `DATABASE_URL` injection.
3. Click **+ New** and select **Database > Redis**. Railway provisions Redis 7 with automatic `REDIS_URL` injection.

### 2.3 Set Environment Variables

In the Railway dashboard, navigate to your service's **Variables** tab and set these:

```bash
# Core (Railway injects DATABASE_URL and REDIS_URL automatically)
API_SECRET_KEY=<generate with: python3 -c "import secrets; print(secrets.token_hex(32))">
API_CORS_ORIGINS=https://your-domain.railway.app
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Security
NPS_ENCRYPTION_KEY=<generate with: python3 -c "import secrets; print(secrets.token_hex(32))">
NPS_ENCRYPTION_SALT=<generate with: python3 -c "import secrets; print(secrets.token_hex(16))">
ENCRYPTION_ENABLED=true

# Railway-specific
RAILWAY_ENVIRONMENT=production
PRODUCTION_DOMAIN=your-domain.railway.app
FORCE_HTTPS=true
SWAGGER_ENABLED=false
DEBUG=false
PORT=8000

# Optional
ANTHROPIC_API_KEY=sk-ant-...
NPS_BOT_TOKEN=<telegram bot token>
NPS_CHAT_ID=<telegram chat id>
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 2.4 Deploy

```bash
# Deploy from the current branch
railway up

# Or link to GitHub for automatic deploys on push
railway link
```

Railway automatically detects the Dockerfile, builds the image, and deploys.

### 2.5 Custom Domain and Auto-SSL

1. In the Railway dashboard, go to **Settings > Networking > Custom Domain**.
2. Add your domain (e.g., `nps.yourdomain.com`).
3. Configure DNS: add a CNAME record pointing to your Railway-provided hostname.
4. Railway provisions and renews SSL certificates automatically.

### 2.6 Verify Deployment

```bash
# Health check
curl https://your-domain.railway.app/api/health
# Expected: {"status": "healthy", "version": "4.0.0"}

# Readiness check
curl https://your-domain.railway.app/api/health/ready
# Expected: {"status": "healthy", "checks": {"database": "healthy", ...}}

# API documentation (if SWAGGER_ENABLED=true)
open https://your-domain.railway.app/docs
```

---

## 3. Self-Hosted Docker Compose

### 3.1 Clone and Configure

```bash
# Clone the repository
git clone https://github.com/DaveXRouz/NPS.git
cd NPS

# Create environment file from template
cp .env.example .env
```

### 3.2 Generate Security Keys

```bash
# Generate API secret key
python3 -c "import secrets; print(f'API_SECRET_KEY={secrets.token_hex(32)}')"

# Generate encryption key (AES-256-GCM)
python3 -c "import secrets; print(f'NPS_ENCRYPTION_KEY={secrets.token_hex(32)}')"

# Generate encryption salt
python3 -c "import secrets; print(f'NPS_ENCRYPTION_SALT={secrets.token_hex(16)}')"

# Generate Telegram bot service key
python3 -c "import secrets; print(f'TELEGRAM_BOT_SERVICE_KEY={secrets.token_hex(32)}')"
```

Edit `.env` and replace all placeholder values (`changeme`, empty strings) with the generated keys and your actual configuration.

**Critical values to change before deploying:**

- `POSTGRES_PASSWORD` -- never use the default `changeme`
- `API_SECRET_KEY` -- used for JWT signing
- `NPS_ENCRYPTION_KEY` -- used for AES-256-GCM encryption
- `NPS_ENCRYPTION_SALT` -- used with encryption key

### 3.3 Development Mode

```bash
# Build and start all 10 services
docker compose up -d

# Or build first, then start
docker compose build
docker compose up -d

# View logs
docker compose logs -f

# Check health of all services
./scripts/health-check.sh
```

The platform starts 10 containers:

| Container            | Service         | Port(s)     | Resource Limits |
| -------------------- | --------------- | ----------- | --------------- |
| `nps-frontend`       | React SPA       | 5173:80     | 0.5 CPU, 256M   |
| `nps-api`            | FastAPI gateway | 8000:8000   | 1 CPU, 1G       |
| `nps-oracle`         | Oracle gRPC     | 50052, 9090 | 1 CPU, 1G       |
| `nps-scanner`        | Scanner gRPC    | 50051       | 2 CPU, 2G       |
| `nps-postgres`       | PostgreSQL 15   | 5432        | 1 CPU, 1G       |
| `nps-redis`          | Redis 7         | 6379        | 0.5 CPU, 512M   |
| `nps-nginx`          | Reverse proxy   | 80, 443     | 0.25 CPU, 128M  |
| `nps-telegram-bot`   | Telegram bot    | (internal)  | 0.25 CPU, 128M  |
| `nps-oracle-alerter` | Monitoring      | (internal)  | 0.1 CPU, 64M    |
| `nps-backup`         | Backup cron     | (internal)  | 0.25 CPU, 256M  |

Services available in development mode:

| Service             | URL                        |
| ------------------- | -------------------------- |
| Frontend            | http://localhost:5173      |
| API                 | http://localhost:8000      |
| API docs (Swagger)  | http://localhost:8000/docs |
| Nginx proxy         | http://localhost:80        |
| PostgreSQL          | localhost:5432             |
| Redis               | localhost:6379             |
| Oracle gRPC         | localhost:50052            |
| Prometheus (Oracle) | localhost:9090             |

### 3.4 Production Mode

For production, create a `docker-compose.prod.yml` override file:

```yaml
# docker-compose.prod.yml
version: "3.9"

services:
  frontend:
    restart: always
    deploy:
      resources:
        limits:
          cpus: "1"
          memory: 512M

  api:
    restart: always
    command: >
      gunicorn app.main:app
      --worker-class uvicorn.workers.UvicornWorker
      --workers 4
      --bind 0.0.0.0:8000
      --timeout 120
      --access-logfile -
      --error-logfile -
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 2G

  postgres:
    restart: always
    command:
      - "postgres"
      - "-c"
      - "shared_buffers=512MB"
      - "-c"
      - "work_mem=32MB"
      - "-c"
      - "effective_cache_size=1536MB"
      - "-c"
      - "random_page_cost=1.1"
      - "-c"
      - "effective_io_concurrency=200"
      - "-c"
      - "max_connections=200"
      - "-c"
      - "wal_buffers=16MB"
      - "-c"
      - "checkpoint_completion_target=0.9"
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 2G

  redis:
    restart: always
    command: >
      redis-server
      --appendonly yes
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
      --save 900 1
      --save 300 10

  nginx:
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infrastructure/nginx/nginx-ssl.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro

  oracle-service:
    restart: always
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 2G
```

Deploy with the production override:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 3.5 SSL Setup with Nginx

Create `infrastructure/nginx/nginx-ssl.conf` for HTTPS termination:

```nginx
events {
    worker_connections 1024;
    multi_accept on;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 4;
    gzip_min_length 256;
    gzip_types text/plain text/css text/javascript application/javascript
               application/json application/xml image/svg+xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

    upstream frontend {
        server frontend:80;
        keepalive 16;
    }

    upstream api {
        server api:8000;
        keepalive 32;
    }

    # HTTP -> HTTPS redirect
    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$host$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL certificates (Let's Encrypt)
        ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

        # SSL hardening
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 1d;
        ssl_session_tickets off;

        # HSTS (1 year, including subdomains)
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

        # Security headers
        add_header X-Frame-Options DENY always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy strict-origin-when-cross-origin always;

        # Static assets (long cache, Vite hashed filenames)
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # Frontend (React SPA)
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
            add_header Cache-Control "no-cache";
        }

        # API endpoints
        location /api/ {
            limit_req zone=api burst=50 nodelay;
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
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

        # Health check
        location /nginx-health {
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

---

## 4. Manual Deployment

For environments where Docker is not available or not desired.

### 4.1 PostgreSQL Setup

```bash
# Install PostgreSQL 15
# macOS:
brew install postgresql@15

# Ubuntu/Debian:
sudo apt install postgresql-15 postgresql-client-15

# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql@15  # macOS

# Create database and user
sudo -u postgres psql <<EOF
CREATE USER nps WITH PASSWORD 'your-secure-password';
CREATE DATABASE nps OWNER nps;
\c nps
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
EOF

# Apply schema
psql -U nps -d nps -f database/init.sql

# Apply all migrations (in order)
for f in database/migrations/0*.sql; do
    [[ "$f" == *rollback* ]] && continue
    echo "Applying $f..."
    psql -U nps -d nps -f "$f"
done
```

### 4.2 Redis Setup

```bash
# Install Redis 7
# macOS:
brew install redis

# Ubuntu/Debian:
sudo apt install redis-server

# Start Redis
sudo systemctl start redis  # Linux
brew services start redis    # macOS

# Verify
redis-cli ping
# Expected: PONG
```

### 4.3 API Service (FastAPI with Gunicorn)

```bash
cd api

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install .

# Development: Uvicorn with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production: Gunicorn with Uvicorn workers
pip install gunicorn
gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
```

For systemd service management, create `/etc/systemd/system/nps-api.service`:

```ini
[Unit]
Description=NPS API Service
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=nps
Group=nps
WorkingDirectory=/opt/nps/api
EnvironmentFile=/opt/nps/.env
ExecStart=/opt/nps/api/.venv/bin/gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8000 \
    --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable nps-api
sudo systemctl start nps-api
```

### 4.4 Frontend (Nginx Static Serve)

```bash
cd frontend

# Install dependencies and build
npm ci
npm run build
# Output: dist/ directory

# Copy to nginx webroot
sudo mkdir -p /var/www/nps
sudo cp -r dist/* /var/www/nps/
```

Create `/etc/nginx/sites-available/nps`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/nps;
    index index.html;

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/nps /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4.5 Oracle Service

```bash
cd services/oracle

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install .

# Run the gRPC server
python -m oracle_service.server
```

For systemd, create `/etc/systemd/system/nps-oracle.service`:

```ini
[Unit]
Description=NPS Oracle gRPC Service
After=network.target postgresql.service

[Service]
Type=simple
User=nps
Group=nps
WorkingDirectory=/opt/nps/services/oracle
EnvironmentFile=/opt/nps/.env
Environment=PYTHONPATH=/opt/nps/services/oracle:/opt/nps/numerology_ai_framework
ExecStart=/opt/nps/services/oracle/.venv/bin/python -m oracle_service.server
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 4.6 Environment for Manual Deployment

When running services outside Docker, update `.env` hostnames from container names to localhost:

```bash
POSTGRES_HOST=localhost
REDIS_HOST=localhost
ORACLE_GRPC_HOST=localhost
SCANNER_GRPC_HOST=localhost
TELEGRAM_BOT_API_URL=http://localhost:8000/api
```

---

## 5. Environment Variables Reference

All configuration is managed through environment variables defined in `.env`. Copy `.env.example` to `.env` and fill in the values.

### PostgreSQL

| Variable            | Default    | Required | Description                                                      |
| ------------------- | ---------- | -------- | ---------------------------------------------------------------- |
| `POSTGRES_HOST`     | `postgres` | Yes      | Database host (container name in Docker, `localhost` for manual) |
| `POSTGRES_PORT`     | `5432`     | Yes      | Database port                                                    |
| `POSTGRES_DB`       | `nps`      | Yes      | Database name                                                    |
| `POSTGRES_USER`     | `nps`      | Yes      | Database user                                                    |
| `POSTGRES_PASSWORD` | `changeme` | Yes      | Database password. **Change this.**                              |

### Redis

| Variable     | Default | Required | Description                           |
| ------------ | ------- | -------- | ------------------------------------- |
| `REDIS_HOST` | `redis` | Yes      | Redis host (container name in Docker) |
| `REDIS_PORT` | `6379`  | Yes      | Redis port                            |

### API Service

| Variable             | Default                                       | Required | Description                               |
| -------------------- | --------------------------------------------- | -------- | ----------------------------------------- |
| `API_HOST`           | `0.0.0.0`                                     | Yes      | API bind address                          |
| `API_PORT`           | `8000`                                        | Yes      | API port                                  |
| `API_SECRET_KEY`     | `changeme-...`                                | Yes      | JWT signing key. **Generate a real one.** |
| `API_CORS_ORIGINS`   | `http://localhost:5173,http://localhost:3000` | Yes      | Comma-separated allowed CORS origins      |
| `JWT_ALGORITHM`      | `HS256`                                       | Yes      | JWT signing algorithm                     |
| `JWT_EXPIRE_MINUTES` | `1440`                                        | No       | JWT token lifetime (default: 24 hours)    |

### gRPC Services

| Variable            | Default           | Required | Description       |
| ------------------- | ----------------- | -------- | ----------------- |
| `SCANNER_GRPC_HOST` | `scanner-service` | No       | Scanner gRPC host |
| `SCANNER_GRPC_PORT` | `50051`           | No       | Scanner gRPC port |
| `ORACLE_GRPC_HOST`  | `oracle-service`  | No       | Oracle gRPC host  |
| `ORACLE_GRPC_PORT`  | `50052`           | No       | Oracle gRPC port  |

### Telegram

| Variable                   | Default                 | Required | Description                                      |
| -------------------------- | ----------------------- | -------- | ------------------------------------------------ |
| `NPS_BOT_TOKEN`            | (empty)                 | No       | Telegram bot API token                           |
| `NPS_CHAT_ID`              | (empty)                 | No       | Default Telegram chat ID for notifications       |
| `NPS_ADMIN_CHAT_ID`        | (empty)                 | No       | Admin-only chat ID (falls back to `NPS_CHAT_ID`) |
| `TELEGRAM_ENABLED`         | `true`                  | No       | Enable/disable Telegram notifications            |
| `TELEGRAM_NOTIFY_BALANCE`  | `true`                  | No       | Notify on balance discoveries                    |
| `TELEGRAM_NOTIFY_ERROR`    | `true`                  | No       | Notify on errors                                 |
| `TELEGRAM_NOTIFY_DAILY`    | `true`                  | No       | Send daily summary                               |
| `TELEGRAM_BOT_API_URL`     | `http://api:8000/api`   | No       | Internal API URL for bot service                 |
| `TELEGRAM_BOT_SERVICE_KEY` | (empty)                 | No       | Service-to-service auth key for bot              |
| `TELEGRAM_RATE_LIMIT`      | `20`                    | No       | Max requests per minute for bot                  |
| `TELEGRAM_FRONTEND_URL`    | `http://localhost:5173` | No       | Frontend URL for links in Telegram messages      |

### Blockchain / Scanner

| Variable                      | Default                        | Required | Description                            |
| ----------------------------- | ------------------------------ | -------- | -------------------------------------- |
| `BTC_RPC_ENDPOINT`            | `https://blockstream.info/api` | No       | Bitcoin balance check endpoint         |
| `ETH_RPC_ENDPOINTS`           | `https://eth.llamarpc.com,...` | No       | Comma-separated Ethereum RPC endpoints |
| `BTC_DELAY`                   | `0.5`                          | No       | Delay between BTC API calls (seconds)  |
| `ETH_DELAY`                   | `0.3`                          | No       | Delay between ETH API calls (seconds)  |
| `SCANNER_CHAINS`              | `btc,eth`                      | No       | Active blockchain chains               |
| `SCANNER_BATCH_SIZE`          | `1000`                         | No       | Keys per batch                         |
| `SCANNER_CHECK_EVERY_N`       | `5000`                         | No       | Check balance every N keys             |
| `SCANNER_MODE`                | `both`                         | No       | Scanner mode: `btc`, `eth`, or `both`  |
| `SCANNER_THREADS`             | `4`                            | No       | Number of scanner threads              |
| `SCANNER_CHECKPOINT_INTERVAL` | `100000`                       | No       | Save checkpoint every N keys           |

### Security / Encryption

| Variable              | Default | Required    | Description                                                                     |
| --------------------- | ------- | ----------- | ------------------------------------------------------------------------------- |
| `ENCRYPTION_ENABLED`  | `true`  | No          | Enable AES-256-GCM encryption                                                   |
| `NPS_ENCRYPTION_KEY`  | (empty) | For encrypt | 64-char hex string: `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `NPS_ENCRYPTION_SALT` | (empty) | For encrypt | 32-char hex string: `python3 -c "import secrets; print(secrets.token_hex(16))"` |
| `V3_MASTER_PASSWORD`  | (empty) | No          | Legacy V3 password (migration only)                                             |

### Daily Scheduler

| Variable                      | Default | Required | Description                    |
| ----------------------------- | ------- | -------- | ------------------------------ |
| `NPS_DAILY_SCHEDULER_ENABLED` | `true`  | No       | Enable daily reading scheduler |
| `NPS_DAILY_SCHEDULER_HOUR`    | `0`     | No       | Hour (UTC) for daily job       |
| `NPS_DAILY_SCHEDULER_MINUTE`  | `5`     | No       | Minute for daily job           |

### AI / Oracle

| Variable            | Default | Required | Description                                                                      |
| ------------------- | ------- | -------- | -------------------------------------------------------------------------------- |
| `ANTHROPIC_API_KEY` | (empty) | No       | Anthropic API key for AI interpretations. System degrades gracefully without it. |

### Logging

| Variable     | Default | Required | Description                                    |
| ------------ | ------- | -------- | ---------------------------------------------- |
| `LOG_LEVEL`  | `INFO`  | No       | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | `json`  | No       | Log format: `json` or `text`                   |

### Railway-Specific Variables

These are set automatically by Railway or configured in the Railway dashboard.

| Variable              | Default      | Description                                     |
| --------------------- | ------------ | ----------------------------------------------- |
| `DATABASE_URL`        | (auto)       | PostgreSQL connection string (Railway-injected) |
| `REDIS_URL`           | (auto)       | Redis connection string (Railway-injected)      |
| `PORT`                | `8000`       | Port Railway exposes                            |
| `RAILWAY_ENVIRONMENT` | `production` | Railway environment name                        |
| `PRODUCTION_DOMAIN`   | (empty)      | Custom domain for the deployment                |
| `FORCE_HTTPS`         | `true`       | Redirect HTTP to HTTPS                          |
| `SWAGGER_ENABLED`     | `false`      | Enable Swagger UI in production                 |
| `DEBUG`               | `false`      | Debug mode (never `true` in production)         |

---

## 6. SSL/TLS Configuration

### 6.1 Railway (Automatic)

Railway automatically provisions and renews SSL certificates for both `*.railway.app` subdomains and custom domains. No manual SSL configuration is needed.

1. Add your custom domain in Railway dashboard under **Settings > Networking**.
2. Point your DNS CNAME to the Railway hostname.
3. SSL is provisioned within minutes.

### 6.2 Self-Hosted with Let's Encrypt

Install Certbot and obtain certificates:

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx  # Ubuntu/Debian
brew install certbot  # macOS

# Obtain certificate (stop nginx first if port 80 is in use)
sudo certbot certonly --standalone -d your-domain.com

# Or with nginx plugin (nginx must be running)
sudo certbot --nginx -d your-domain.com
```

Certificate files are stored in `/etc/letsencrypt/live/your-domain.com/`:

- `fullchain.pem` -- Full certificate chain
- `privkey.pem` -- Private key

#### Auto-Renewal

Certbot sets up automatic renewal via systemd timer or cron. Verify:

```bash
sudo certbot renew --dry-run
```

Add a post-renewal hook to reload nginx:

```bash
#!/bin/bash
# /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh
docker compose -f /path/to/NPS/docker-compose.yml exec nginx nginx -s reload
```

Make it executable:

```bash
sudo chmod +x /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh
```

### 6.3 Nginx SSL Configuration

See the `nginx-ssl.conf` template in [Section 3.5](#35-ssl-setup-with-nginx) for the full production SSL configuration.

Key SSL settings:

- **Protocols:** TLSv1.2 and TLSv1.3 only (TLSv1.0 and TLSv1.1 are disabled)
- **Ciphers:** Modern ECDHE-based cipher suites with forward secrecy
- **Session caching:** 10 MB shared cache with 1-day timeout
- **Session tickets:** Disabled for forward secrecy

### 6.4 HSTS Configuration

HSTS (HTTP Strict Transport Security) is configured in the nginx SSL configuration. The header instructs browsers to only use HTTPS:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

**Warning:** Only enable HSTS after confirming SSL works correctly. The `preload` directive is irreversible once submitted to browser preload lists.

To test HSTS:

```bash
curl -I https://your-domain.com | grep Strict
```

---

## 7. Database Setup and Migration

### 7.1 Initial Schema

The base schema is defined in `database/init.sql` and is automatically applied when the PostgreSQL container starts for the first time (via Docker's `docker-entrypoint-initdb.d` mechanism).

For manual setup:

```bash
psql -U nps -d nps -f database/init.sql
```

The schema creates:

- **Extensions:** `uuid-ossp`, `pgcrypto`
- **Core tables:** `users`, `api_keys`, `sessions`, `findings`
- **Oracle tables:** `oracle_users`, `oracle_readings`, `oracle_reading_users`, `oracle_audit_log`
- **Migration tracking:** `schema_migrations`
- **Auto-updated timestamps** via `update_updated_at()` trigger function

PostgreSQL tuning parameters applied in Docker Compose:

| Parameter                  | Value | Purpose                          |
| -------------------------- | ----- | -------------------------------- |
| `shared_buffers`           | 256MB | Shared memory for caching        |
| `work_mem`                 | 16MB  | Per-operation sort/hash memory   |
| `effective_cache_size`     | 512MB | Planner hint for available cache |
| `random_page_cost`         | 1.1   | SSD-optimized cost estimate      |
| `effective_io_concurrency` | 200   | SSD-optimized concurrent I/O     |
| `max_connections`          | 100   | Maximum concurrent connections   |

### 7.2 Migrations

Migrations are stored in `database/migrations/` and numbered sequentially:

```
database/migrations/
  010_oracle_schema.sql
  011_security_columns.sql
  012_framework_alignment.sql
  013_auth_hardening.sql
  013_share_links.sql
  014_user_management.sql
  015_feedback_learning.sql
  016_daily_readings_cache.sql
  017_reading_search.sql
  018_user_settings.sql
  019_telegram_links.sql
  020_telegram_daily_preferences.sql
  021_performance_indexes.sql
```

Each migration has a corresponding `*_rollback.sql` file for reversal.

Apply all migrations:

```bash
# Via Docker (apply init.sql)
make migrate

# Apply individual migrations manually
for f in database/migrations/0*.sql; do
    [[ "$f" == *rollback* ]] && continue
    echo "Applying: $f"
    psql -U nps -d nps -f "$f"
done

# Via Docker exec
docker compose exec -T postgres psql -U nps -d nps \
    -f /docker-entrypoint-initdb.d/init.sql
```

Roll back a specific migration:

```bash
psql -U nps -d nps -f database/migrations/021_performance_indexes_rollback.sql
```

### 7.3 V3 Data Migration

To migrate data from the legacy V3 SQLite database:

```bash
cd database/migrations
python migrate_all.py
```

This runs the individual migration scripts: `migrate_vault.py`, `migrate_sessions.py`, `migrate_readings.py`, and `migrate_learning.py`. Requires `V3_MASTER_PASSWORD` in `.env` if the V3 data was encrypted.

### 7.4 Admin User Seed

Create the initial admin user after schema setup:

```bash
# Generate a bcrypt password hash
python3 -c "import bcrypt; print(bcrypt.hashpw(b'your-password', bcrypt.gensalt()).decode())"

# Connect to the database
docker compose exec postgres psql -U nps -d nps

# Insert admin user (replace hash with the output above)
INSERT INTO users (username, password_hash, role)
VALUES ('admin', '$2b$12$YOUR_BCRYPT_HASH_HERE', 'admin');
```

### 7.5 Verification Queries

After setup, verify the database is correctly initialized:

```sql
-- Check all tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' ORDER BY table_name;

-- Check extensions
SELECT extname, extversion FROM pg_extension;

-- Count rows in core tables
SELECT 'users' AS tbl, COUNT(*) FROM users
UNION ALL SELECT 'oracle_users', COUNT(*) FROM oracle_users
UNION ALL SELECT 'oracle_readings', COUNT(*) FROM oracle_readings
UNION ALL SELECT 'api_keys', COUNT(*) FROM api_keys;

-- Check migrations applied
SELECT version, name, applied_at FROM schema_migrations ORDER BY version;

-- Database size
SELECT pg_size_pretty(pg_database_size('nps'));

-- Table sizes
SELECT relname AS table_name,
       pg_size_pretty(pg_total_relation_size(relid)) AS total_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

---

## 8. Monitoring and Health Checks

### 8.1 Health Check Endpoints

The API provides three unauthenticated health check endpoints and three admin-only monitoring endpoints:

| Endpoint                      | Auth  | Purpose                              |
| ----------------------------- | ----- | ------------------------------------ |
| `GET /api/health`             | None  | Basic liveness probe                 |
| `GET /api/health/ready`       | None  | Readiness probe (DB + Redis)         |
| `GET /api/health/performance` | None  | Performance metrics                  |
| `GET /api/health/detailed`    | Admin | Full system health with all services |
| `GET /api/health/analytics`   | Admin | Reading analytics dashboard data     |
| `GET /api/health/logs`        | Admin | Audit log query with filtering       |

#### Basic Health Check (Liveness)

```bash
curl http://localhost:8000/api/health
```

Response:

```json
{ "status": "healthy", "version": "4.0.0" }
```

Use this for Docker health checks and load balancer probes.

#### Readiness Check

```bash
curl http://localhost:8000/api/health/ready
```

Response:

```json
{
  "status": "healthy",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "scanner_service": "not_deployed",
    "oracle_service": "direct_mode"
  }
}
```

Returns `"degraded"` if the database is unhealthy. Use this for Kubernetes readiness probes or pre-deployment verification.

#### Detailed Health (Admin Only)

```bash
curl -H "Authorization: Bearer <admin-jwt>" http://localhost:8000/api/health/detailed
```

Returns full system information including:

- Database connectivity and size
- Redis memory usage
- Oracle gRPC service status
- Scanner service status
- Telegram configuration status
- System metrics: platform, Python version, CPU count, process memory, uptime

### 8.2 Docker Health Checks

All 10 services define health checks in `docker-compose.yml` with the following configuration:

| Service        | Check Method                        | Interval | Timeout | Start Period | Retries |
| -------------- | ----------------------------------- | -------- | ------- | ------------ | ------- |
| PostgreSQL     | `pg_isready`                        | 10s      | 5s      | 15s          | 5       |
| Redis          | `redis-cli ping`                    | 10s      | 5s      | 10s          | 5       |
| API            | HTTP GET `/api/health`              | 30s      | 5s      | 15s          | 3       |
| Frontend       | `wget --spider http://localhost:80` | 30s      | 5s      | 15s          | 3       |
| Oracle         | gRPC channel ready check            | 30s      | 5s      | 30s          | 3       |
| Scanner        | Binary `--health-check` flag        | 30s      | 5s      | 30s          | 3       |
| Nginx          | HTTP GET `/api/health` via proxy    | 30s      | 5s      | 15s          | 3       |
| Oracle Alerter | `pgrep -f oracle_alerts`            | 60s      | 5s      | 10s          | 3       |

View status:

```bash
# Quick overview
docker compose ps

# Detailed health check script
./scripts/health-check.sh

# Output example:
# NPS Health Check
# ===================
#   [PASS] postgres
#   [PASS] redis
#   [PASS] oracle-service
#   [----] scanner-service (not running)
#   [PASS] api
#   [PASS] frontend
#   [PASS] nginx
#
# Total: 7 | Healthy: 6 | Unhealthy: 0 | Not running: 1
```

### 8.3 Prometheus Metrics

The Oracle service exposes Prometheus metrics on port 9090:

```bash
curl http://localhost:9090/metrics
```

Configure Prometheus to scrape this endpoint by adding to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: "nps-oracle"
    static_configs:
      - targets: ["oracle-service:9090"]
    scrape_interval: 15s
```

### 8.4 Telegram Alerts

The Oracle Alerter container (`nps-oracle-alerter`) monitors the Oracle service and sends alerts to Telegram. It connects to the Oracle service at `http://oracle-service:9090`.

Required configuration:

- `NPS_BOT_TOKEN` -- Telegram bot token (create via [@BotFather](https://t.me/BotFather))
- `NPS_CHAT_ID` -- Chat ID for general alerts
- `NPS_ADMIN_CHAT_ID` -- Chat ID for admin-only system alerts (falls back to `NPS_CHAT_ID`)

Alert types controlled by environment variables:

- `TELEGRAM_NOTIFY_BALANCE=true` -- Triggered when a funded wallet is found
- `TELEGRAM_NOTIFY_ERROR=true` -- Triggered on service errors
- `TELEGRAM_NOTIFY_DAILY=true` -- Sent at the configured schedule time

### 8.5 Production Readiness Check

Run the automated production readiness check before deploying:

```bash
./scripts/production_readiness_check.sh
```

This script verifies 10 categories:

1. Database schema (init.sql integrity)
2. API entry point (app/main.py)
3. Oracle router existence
4. ORM models (deleted_at support)
5. Frontend configuration
6. Integration tests (minimum 6 test files)
7. Security audit script
8. Performance audit script
9. Documentation files
10. Environment configuration

---

## 9. Backup and Restore

### 9.1 Automated Backup Schedule

The backup container (`nps-backup`) runs two automated cron jobs defined in `scripts/crontab`:

| Schedule                      | Type          | Script                              | Retention |
| ----------------------------- | ------------- | ----------------------------------- | --------- |
| Daily at 00:00 UTC            | Oracle tables | `database/scripts/oracle_backup.sh` | 30 days   |
| Weekly on Sunday at 03:00 UTC | Full database | `scripts/backup.sh`                 | 60 days   |

Backup files are stored in:

- `./backups/` -- Full database backups (`nps_backup_YYYYMMDD_HHMMSS.sql.gz`)
- `./backups/oracle/` -- Oracle-only backups (`oracle_full_YYYYMMDD_HHMMSS.sql.gz`)

Each backup has a JSON metadata sidecar file (`.meta.json`) containing filename, type, timestamp, size, and table list.

### 9.2 Manual Backup

#### Full Database Backup

```bash
# Interactive
./scripts/backup.sh

# Non-interactive (for scripting/cron)
./scripts/backup.sh --non-interactive

# With Telegram notification
./scripts/backup.sh --non-interactive --notify

# Via Makefile
make backup
```

#### Oracle Tables Only

Backs up `oracle_users`, `oracle_readings`, `oracle_reading_users`, and `oracle_audit_log`:

```bash
# Full backup (schema + data)
./database/scripts/oracle_backup.sh --non-interactive

# Data-only backup
./database/scripts/oracle_backup.sh --data-only --non-interactive

# With notification
./database/scripts/oracle_backup.sh --non-interactive --notify
```

#### Quick Manual Backup via Docker

```bash
docker compose exec -T postgres pg_dump -U nps nps | gzip > backups/manual_$(date +%Y%m%d).sql.gz
```

### 9.3 Restore Procedure

#### Full Database Restore

**Warning:** This drops and recreates the entire database. All existing data will be lost.

```bash
# Interactive (prompts for confirmation)
./scripts/restore.sh backups/nps_backup_20260214_030000.sql.gz

# Non-interactive
./scripts/restore.sh --non-interactive backups/nps_backup_20260214_030000.sql.gz

# With Telegram notification
./scripts/restore.sh --non-interactive --notify backups/nps_backup_20260214_030000.sql.gz

# List available backups
./scripts/restore.sh

# Via Makefile
make restore
```

#### Oracle Tables Restore

This only truncates Oracle domain tables (with `CASCADE`), leaving the rest of the database intact:

```bash
# Interactive
./database/scripts/oracle_restore.sh backups/oracle/oracle_full_20260214_000000.sql.gz

# Non-interactive
./database/scripts/oracle_restore.sh --non-interactive backups/oracle/oracle_full_20260214_000000.sql.gz

# List available Oracle backups
./database/scripts/oracle_restore.sh
```

The Oracle restore script:

1. Truncates all Oracle tables with `RESTART IDENTITY CASCADE`
2. Restores from the backup file
3. Verifies row counts for all four Oracle tables
4. Outputs JSON for API consumption

### 9.4 Railway Snapshots

Railway provides automatic database snapshots:

1. Open the Railway dashboard.
2. Click on the PostgreSQL plugin.
3. Go to the **Backups** tab.
4. Click **Create Snapshot** for an on-demand backup.
5. To restore, click on a snapshot and select **Restore**.

### 9.5 Backup Verification

After restoring, verify data integrity:

```bash
docker compose exec postgres psql -U nps -d nps -c "
SELECT 'users' AS tbl, COUNT(*) FROM users
UNION ALL SELECT 'oracle_users', COUNT(*) FROM oracle_users
UNION ALL SELECT 'oracle_readings', COUNT(*) FROM oracle_readings
UNION ALL SELECT 'oracle_reading_users', COUNT(*) FROM oracle_reading_users
UNION ALL SELECT 'oracle_audit_log', COUNT(*) FROM oracle_audit_log;
"
```

---

## 10. Scaling

### 10.1 API Workers

The API service uses Uvicorn workers. Scale by adjusting the worker count:

```bash
# Development: single worker with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production: multiple workers via Gunicorn
gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers $(( 2 * $(nproc) + 1 )) \
    --bind 0.0.0.0:8000 \
    --timeout 120
```

Rule of thumb: `(2 * CPU_cores) + 1` workers.

In Docker Compose, override the API command in `docker-compose.prod.yml` (see [Section 3.4](#34-production-mode)).

### 10.2 Oracle gRPC Instances

Scale the Oracle service horizontally by running multiple instances:

```bash
docker compose up -d --scale oracle-service=3
```

For dedicated replicas with load balancing, add to `docker-compose.prod.yml`:

```yaml
services:
  oracle-service:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: "1"
          memory: 1G
```

### 10.3 PostgreSQL Connection Pooling with PgBouncer

For high-concurrency environments, add PgBouncer between the API and PostgreSQL:

```yaml
# Add to docker-compose.prod.yml
services:
  pgbouncer:
    image: edoburu/pgbouncer:1.21.0
    container_name: nps-pgbouncer
    environment:
      DATABASE_URL: postgresql://nps:${POSTGRES_PASSWORD}@postgres:5432/nps
      POOL_MODE: transaction
      MAX_CLIENT_CONN: 400
      DEFAULT_POOL_SIZE: 40
      MIN_POOL_SIZE: 10
      RESERVE_POOL_SIZE: 5
    ports:
      - "6432:6432"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
```

Then update the API to connect through PgBouncer:

```bash
POSTGRES_HOST=pgbouncer
POSTGRES_PORT=6432
```

### 10.4 Redis Scaling

For single-instance optimization, tune the Redis configuration:

```bash
redis-server \
    --appendonly yes \
    --maxmemory 1gb \
    --maxmemory-policy allkeys-lru \
    --save 900 1 \
    --save 300 10 \
    --tcp-backlog 511 \
    --timeout 300
```

For Redis Cluster (high availability):

```yaml
services:
  redis-master:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 512mb
    ports:
      - "6379:6379"

  redis-replica:
    image: redis:7-alpine
    command: redis-server --replicaof redis-master 6379 --appendonly yes
    depends_on:
      - redis-master

  redis-sentinel:
    image: redis:7-alpine
    command: redis-sentinel /etc/redis/sentinel.conf
    depends_on:
      - redis-master
      - redis-replica
```

### 10.5 Nginx Load Balancing

For multiple API instances, configure upstream load balancing in nginx:

```nginx
upstream api {
    least_conn;
    server api-1:8000;
    server api-2:8000;
    server api-3:8000;
    keepalive 32;
}
```

### 10.6 Resource Limits Reference

Current Docker Compose resource limits:

| Service        | CPU Limit | Memory Limit |
| -------------- | --------- | ------------ |
| Frontend       | 0.5       | 256M         |
| API            | 1.0       | 1G           |
| Scanner        | 2.0       | 2G           |
| Oracle         | 1.0       | 1G           |
| PostgreSQL     | 1.0       | 1G           |
| Redis          | 0.5       | 512M         |
| Nginx          | 0.25      | 128M         |
| Telegram Bot   | 0.25      | 128M         |
| Oracle Alerter | 0.1       | 64M          |
| Backup         | 0.25      | 256M         |
| **Total**      | **6.1**   | **5.3G**     |

---

## 11. Rollback Procedures

### 11.1 Railway One-Click Rollback

1. Open the Railway dashboard.
2. Navigate to **Deployments** for your service.
3. Find the previous successful deployment.
4. Click **Redeploy** or **Rollback** on that deployment.
5. Railway instantly switches to the previous image.

### 11.2 Docker Tag Rollback

Using the provided rollback script:

```bash
./scripts/rollback.sh
```

This script:

1. Stops all running services
2. Finds the most recent database backup
3. Prompts to restore the backup (optional)
4. Restarts all services

Manual rollback to a previous Git commit:

```bash
# Stop current services
docker compose down

# Find the commit to roll back to
git log --oneline -10

# Checkout the previous version
git checkout <commit-hash>

# Rebuild and restart
docker compose build
docker compose up -d

# Verify health
./scripts/health-check.sh
```

### 11.3 Database Migration Rollback

Roll back a specific database migration using its rollback script:

```bash
# Roll back the most recent migration (example: 021)
psql -U nps -d nps -f database/migrations/021_performance_indexes_rollback.sql

# Via Docker
docker compose exec -T postgres psql -U nps -d nps < database/migrations/021_performance_indexes_rollback.sql
```

Available rollback scripts:

```
database/migrations/010_oracle_schema_rollback.sql
database/migrations/011_security_columns_rollback.sql
database/migrations/012_framework_alignment_rollback.sql
database/migrations/013_auth_hardening_rollback.sql
database/migrations/013_share_links_rollback.sql
database/migrations/014_user_management_rollback.sql
database/migrations/015_feedback_learning_rollback.sql
database/migrations/017_reading_search_rollback.sql
database/migrations/018_user_settings_rollback.sql
database/migrations/019_telegram_links_rollback.sql
database/migrations/020_telegram_daily_preferences_rollback.sql
database/migrations/021_performance_indexes_rollback.sql
```

### 11.4 Full Database Restore

Restore the entire database from a backup:

```bash
# List available backups
ls -lt backups/nps_backup_*.sql.gz | head -5

# Restore (interactive)
./scripts/restore.sh backups/nps_backup_YYYYMMDD_HHMMSS.sql.gz

# Non-interactive (for automation)
./scripts/restore.sh --non-interactive backups/nps_backup_YYYYMMDD_HHMMSS.sql.gz
```

### 11.5 Emergency Rollback Procedure

In case of critical failure:

```bash
# 1. Stop all services immediately
docker compose down

# 2. Start only infrastructure services
docker compose up -d postgres redis
sleep 10

# 3. Verify database is accessible
docker compose exec postgres pg_isready -U nps -d nps

# 4. Restore database from latest backup (if needed)
LATEST=$(ls -t backups/nps_backup_*.sql.gz 2>/dev/null | head -1)
if [ -n "$LATEST" ]; then
    ./scripts/restore.sh --non-interactive "$LATEST"
fi

# 5. Roll back to the last known-good commit
git stash  # Save any local changes
git log --oneline -10  # Find the good commit
git checkout <last-known-good-commit>

# 6. Rebuild and restart all services
docker compose build
docker compose up -d

# 7. Verify everything is healthy
./scripts/health-check.sh
curl http://localhost:8000/api/health
curl http://localhost:8000/api/health/ready
```

---

## 12. Troubleshooting

### 12.1 Port Conflicts

**Symptom:** `Bind for 0.0.0.0:XXXX failed: port is already allocated`

```bash
# Find what is using the port
lsof -ti:8000  # API
lsof -ti:5432  # PostgreSQL
lsof -ti:6379  # Redis
lsof -ti:80    # Nginx/Frontend
lsof -ti:5173  # Frontend dev

# Kill the process using a specific port
lsof -ti:8000 | xargs kill -9

# Or change the port mapping in docker-compose.yml
# ports:
#   - "8001:8000"  # Map to a different host port
```

### 12.2 Database Connection Issues

**Symptom:** `connection refused` or `could not connect to server`

```bash
# Check if PostgreSQL container is running and healthy
docker compose ps postgres

# Check PostgreSQL logs
docker compose logs postgres

# Test connection from inside the Docker network
docker compose exec api python -c "
from sqlalchemy import create_engine, text
import os
url = f'postgresql://{os.environ[\"POSTGRES_USER\"]}:{os.environ[\"POSTGRES_PASSWORD\"]}@{os.environ[\"POSTGRES_HOST\"]}:{os.environ[\"POSTGRES_PORT\"]}/{os.environ[\"POSTGRES_DB\"]}'
engine = create_engine(url)
with engine.connect() as conn:
    print(conn.execute(text('SELECT version()')).scalar())
"

# Verify .env has correct values
grep POSTGRES .env
```

**Symptom:** `FATAL: password authentication failed`

```bash
# Verify the password matches between .env and the running container
docker compose exec postgres psql -U nps -d nps -c "SELECT 1"

# If password was changed after initial creation, recreate the volume:
docker compose down -v  # WARNING: Deletes all data!
docker compose up -d
```

### 12.3 Missing Environment Variables

**Symptom:** `KeyError` or `None` values at startup

```bash
# Verify .env file exists and is not empty
ls -la .env
wc -l .env

# Compare with .env.example to find missing variables
diff <(grep -v '^#' .env | grep -v '^$' | cut -d= -f1 | sort) \
     <(grep -v '^#' .env.example | grep -v '^$' | cut -d= -f1 | sort)

# Verify variables are available inside containers
docker compose exec api env | grep -E "POSTGRES|API_SECRET|NPS_"

# Critical variables that cause startup failures if missing:
#   POSTGRES_PASSWORD  - Database authentication
#   API_SECRET_KEY     - JWT signing
#   NPS_ENCRYPTION_KEY - Encryption operations (if ENCRYPTION_ENABLED=true)
```

### 12.4 Log Locations

```bash
# Docker container logs (most common)
docker compose logs api             # API service
docker compose logs oracle-service  # Oracle gRPC
docker compose logs postgres        # Database
docker compose logs redis           # Cache
docker compose logs nginx           # Reverse proxy
docker compose logs telegram-bot    # Telegram bot
docker compose logs oracle-alerter  # Monitoring alerts
docker compose logs backup          # Backup cron
docker compose logs frontend        # Frontend (nginx serving SPA)
docker compose logs scanner-service # Scanner (stub)

# Follow logs in real-time
docker compose logs -f api

# All services with timestamps, last 100 lines
docker compose logs -t --tail=100

# Oracle service file logs (inside container volume)
docker compose exec oracle-service ls /app/logs/

# Backup cron log (inside backup container)
docker compose exec backup cat /var/log/cron.log

# Manual deployment logs (systemd)
journalctl -u nps-api -f
journalctl -u nps-oracle -f
```

### 12.5 Common Errors and Solutions

#### `ModuleNotFoundError: No module named 'app'`

The API container cannot find the application module.

```bash
# Rebuild without cache
docker compose build api --no-cache
docker compose up -d api
```

#### `grpc._channel._InactiveRpcError: StatusCode.UNAVAILABLE`

The Oracle gRPC service is not reachable from the API.

```bash
# Check if Oracle service is running
docker compose ps oracle-service

# Test gRPC connectivity
docker compose exec api python -c "
import grpc
ch = grpc.insecure_channel('oracle-service:50052')
grpc.channel_ready_future(ch).result(timeout=5)
print('Oracle service is reachable')
"

# Restart Oracle service
docker compose restart oracle-service
```

Note: The API operates in "direct mode" when the Oracle gRPC service is unavailable, so this is not a critical failure.

#### `redis.exceptions.ConnectionError: Error connecting to redis`

```bash
# Check Redis is running
docker compose ps redis
docker compose exec redis redis-cli ping

# Verify Redis host in .env
grep REDIS .env
```

Note: The API degrades gracefully without Redis and falls back to in-memory caching.

#### `sqlalchemy.exc.OperationalError: could not translate host name "postgres" to address`

This occurs when running the API outside Docker but using Docker hostnames in `.env`.

```bash
# For local development outside Docker, update .env:
POSTGRES_HOST=localhost
REDIS_HOST=localhost
ORACLE_GRPC_HOST=localhost
```

#### Frontend build fails with `npm ERR! code ERESOLVE`

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

#### `PermissionError: [Errno 13] Permission denied: '/app/logs'`

```bash
# Fix permissions inside the container
docker compose exec --user root oracle-service chown -R oracle:oracle /app/logs

# Or rebuild the image
docker compose build oracle-service --no-cache
```

#### Backup container exits immediately

```bash
# Check backup container logs
docker compose logs backup

# Verify crontab is properly mounted
docker compose exec backup cat /etc/crontabs/root

# Expected output:
# 0 0 * * * /app/scripts/backup_cron.sh daily >> /var/log/cron.log 2>&1
# 0 3 * * 0 /app/scripts/backup_cron.sh weekly >> /var/log/cron.log 2>&1

# Test backup manually inside the container
docker compose exec backup /app/scripts/backup_cron.sh daily
```

#### `shared_buffers` or memory-related PostgreSQL errors

The PostgreSQL container has a `shm_size: 256mb` setting. If you increase `shared_buffers` beyond 256MB, update `shm_size` accordingly in `docker-compose.yml`.

### 12.6 Useful Diagnostic Commands

```bash
# Full system status
docker compose ps
./scripts/health-check.sh

# Resource usage per container
docker stats --no-stream

# Disk usage by Docker
docker system df

# Database size
docker compose exec postgres psql -U nps -d nps \
    -c "SELECT pg_size_pretty(pg_database_size('nps'));"

# Redis memory usage
docker compose exec redis redis-cli info memory | grep used_memory_human

# API endpoint tests
curl -s http://localhost:8000/api/health | python3 -m json.tool
curl -s http://localhost:8000/api/health/ready | python3 -m json.tool

# Network inspection (verify services can reach each other)
docker network ls
docker network inspect nps_default

# Production readiness check
./scripts/production_readiness_check.sh

# Run all tests
make test

# Run specific test suites
make test-api          # API unit tests
make test-oracle       # Oracle service tests
make test-frontend     # Frontend unit tests
make test-e2e          # Playwright end-to-end tests
make test-integration  # Cross-service integration tests

# Run all quality checks
make check             # lint + format-check + test
```

---

## Quick Reference

### Deploy Commands

```bash
# Development
make up                    # Start all services (Docker)
make dev-api               # Local API (no Docker)
make dev-frontend          # Local frontend (no Docker)
make dev-oracle            # Local Oracle service (no Docker)

# Production
./scripts/deploy.sh        # Full deployment script
docker compose up -d       # Start all (Docker)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d  # Production mode

# Maintenance
make backup                # Database backup
make restore               # Database restore
./scripts/health-check.sh  # Check all services
./scripts/production_readiness_check.sh  # Pre-deploy checklist
./scripts/rollback.sh      # Rollback to previous version
```

### Service Ports

| Service      | Dev Port | Prod Port | Protocol |
| ------------ | -------- | --------- | -------- |
| Frontend     | 5173     | 80        | HTTP     |
| API          | 8000     | 8000      | HTTP     |
| Nginx        | 80/443   | 80/443    | HTTP/S   |
| PostgreSQL   | 5432     | 5432      | TCP      |
| Redis        | 6379     | 6379      | TCP      |
| Oracle gRPC  | 50052    | 50052     | gRPC     |
| Scanner gRPC | 50051    | 50051     | gRPC     |
| Prometheus   | 9090     | 9090      | HTTP     |
