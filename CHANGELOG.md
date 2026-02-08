# Changelog

All notable changes to NPS V4 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- V3 file migration: all engines, solvers, logic modules copied to Oracle service
- V3 reference files for Rust scanner (crypto, keccak, bip39, balance)
- Legacy Tkinter GUI preserved in `frontend/desktop-gui/legacy/`
- Per-layer README documentation for all 8 service directories
- Architecture overview (`docs/architecture/OVERVIEW.md`)
- Migration guide (`docs/migration/V3_TO_V4_GUIDE.md`)
- REST API reference (`docs/api/ENDPOINTS.md`)
- MIT License

## [4.0.0-alpha.0] - 2026-02-08

### Added

- 93-file scaffolding across 7-layer distributed architecture
- React + TypeScript + Tailwind frontend with 6 pages
- FastAPI REST + WebSocket gateway with 6 routers and Pydantic models
- Rust scanner service structure (Cargo project with modules)
- Python Oracle service structure with gRPC interface
- Protobuf contracts: `scanner.proto` (35 messages) and `oracle.proto` (25 messages)
- PostgreSQL schema with 10 tables (`init.sql`)
- Docker Compose 7-container orchestration
- Nginx reverse proxy configuration
- Prometheus monitoring setup
- Deployment scripts (deploy, backup, restore, rollback)
- JWT + API key authentication middleware
- AES-256-GCM encryption with V3 legacy decrypt support
