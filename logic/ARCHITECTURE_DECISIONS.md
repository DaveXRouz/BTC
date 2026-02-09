# Architecture Decisions — Why We Chose X Over Y

> Each decision includes options considered, choice made, and reasoning.

---

## 1. Microservices Over Monolith

**Choice:** Split legacy monolith into separate Scanner (Rust), Oracle (Python), API (FastAPI), Frontend (React).
**Why:** Scanner needs Rust performance. Oracle needs Python AI. Different runtimes, independent scaling/deployment.

## 2. PostgreSQL Over SQLite

**Choice:** PostgreSQL for all data storage.
**Why:** Millions of rows need partitioning + indexes. Complex joins across findings/patterns/users. Battle-tested reliability.

## 3. FastAPI Over Flask/Django

**Choice:** FastAPI for API gateway.
**Why:** Async-native (critical for non-blocking I/O), auto-generated Swagger docs, Pydantic validation, WebSocket support built-in.

## 4. React Over Vue/Svelte

**Choice:** React + TypeScript + Tailwind.
**Why:** Largest ecosystem for i18n, RTL, calendar pickers. TypeScript strict mode catches bugs at compile time. Vite for fast dev.

## 5. Rust Over Go for Scanner

**Choice:** Rust for scanning engine.
**Why:** Crypto operations (secp256k1, SHA-256) are CPU-bound. Rust is 10-50x faster than Python. No GC pauses. Target: 5000+ keys/sec.
**Status:** Stub only. Future project.

## 6. gRPC Over REST for Service-to-Service

**Choice:** gRPC + Protocol Buffers between API↔Oracle and API↔Scanner.
**Why:** Type-safe contracts, binary encoding (faster than JSON), streaming support, auto-generated code from `.proto` files.

## 7. API-Only AI (NOT CLI)

**Choice:** Anthropic Python SDK (HTTP API) for all AI calls. **NEVER** Claude CLI.
**Why:** CLI requires installation on every server. Can't mock in tests. Not async-compatible. Breaks in Docker. This is a **hard rule**.

## 8. AES-256-GCM Encryption (Reuse Legacy)

**Choice:** Same encryption pattern as the legacy version with `ENC4:` prefix.
**Why:** Legacy encryption is battle-tested. Reusing proven crypto is safer than inventing new. Legacy `ENC:` kept for migration.

## 9. Simple SESSION_LOG.md Over Complex State

**Choice:** Plain markdown file for session tracking.
**Why:** Claude Code reads markdown natively. Human-readable. Git-friendly. Low maintenance.

## 10. Hybrid Rebuild (Keep Infra, Rewrite Oracle)

**Choice:** Keep infrastructure (Docker, DB, API skeleton, tests), rewrite Oracle logic.
**Why:** Infrastructure is solid. Oracle needs new reading types, bilingual support, Abjad numerology, improved AI. Saves time, reduces risk.
