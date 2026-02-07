#!/bin/bash
# NPS V4 — Deploy script
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V4_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== NPS V4 Deployment ==="
echo "Directory: $V4_DIR"

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "ERROR: docker not found"; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "ERROR: docker compose not found"; exit 1; }

# Check .env file
if [ ! -f "$V4_DIR/.env" ]; then
    echo "WARNING: .env file not found. Copying from .env.example..."
    cp "$V4_DIR/.env.example" "$V4_DIR/.env"
    echo "IMPORTANT: Edit $V4_DIR/.env before deploying to production!"
fi

# Build all images
echo "Building Docker images..."
cd "$V4_DIR"
docker compose build

# Run database migrations
echo "Running database initialization..."
docker compose up -d postgres redis
sleep 5  # Wait for postgres to be ready

# Start all services
echo "Starting all services..."
docker compose up -d

# Health check
echo "Waiting for services to be healthy..."
sleep 10
docker compose ps

echo ""
echo "=== Deployment Complete ==="
echo "Frontend: http://localhost:80"
echo "API:      http://localhost:8000/api/health"
echo "API docs: http://localhost:8000/docs"
