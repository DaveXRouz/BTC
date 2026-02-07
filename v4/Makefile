# NPS V4 — Build & Development Commands

.PHONY: help dev up down build test lint migrate clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── Docker ───

up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

build: ## Build all Docker images
	docker compose build

logs: ## Tail logs from all services
	docker compose logs -f

restart: ## Restart all services
	docker compose restart

# ─── Development ───

dev-api: ## Run API service locally (no Docker)
	cd api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Run frontend dev server
	cd frontend && npm run dev

dev-oracle: ## Run Oracle service locally
	cd services/oracle && python -m oracle_service.server

# ─── Database ───

migrate: ## Run database migrations
	docker compose exec postgres psql -U nps -d nps -f /docker-entrypoint-initdb.d/init.sql

migrate-v3: ## Migrate V3 data to V4 PostgreSQL
	cd database/migrations && python migrate_all.py

# ─── Testing ───

test: ## Run all tests
	cd api && python -m pytest tests/ -v
	cd services/oracle && python -m pytest tests/ -v
	cd services/scanner && cargo test
	cd frontend && npm test

test-api: ## Run API tests only
	cd api && python -m pytest tests/ -v

test-oracle: ## Run Oracle service tests only
	cd services/oracle && python -m pytest tests/ -v

test-scanner: ## Run Scanner (Rust) tests only
	cd services/scanner && cargo test

test-frontend: ## Run frontend tests only
	cd frontend && npm test

# ─── Code Quality ───

lint: ## Run linters
	cd api && ruff check .
	cd services/oracle && ruff check .
	cd frontend && npm run lint
	cd services/scanner && cargo clippy

format: ## Auto-format code
	cd api && ruff format .
	cd services/oracle && ruff format .
	cd frontend && npm run format
	cd services/scanner && cargo fmt

# ─── Protobuf ───

proto: ## Generate gRPC code from proto files
	python -m grpc_tools.protoc -I proto/ --python_out=api/app/grpc_gen/ --grpc_python_out=api/app/grpc_gen/ proto/*.proto
	python -m grpc_tools.protoc -I proto/ --python_out=services/oracle/oracle_service/grpc_gen/ --grpc_python_out=services/oracle/oracle_service/grpc_gen/ proto/oracle.proto

# ─── Utilities ───

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	cd services/scanner && cargo clean 2>/dev/null || true

backup: ## Backup PostgreSQL database
	./scripts/backup.sh

restore: ## Restore PostgreSQL database from backup
	./scripts/restore.sh
