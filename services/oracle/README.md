# V4 Oracle Service (Python)

## Overview

Python-based Oracle service providing FC60 numerology, oracle readings, AI learning, and strategic intelligence. This service reuses V3 engines, solvers, and logic modules with minimal modification.

## Architecture

```
oracle_service/
  server.py         — gRPC server entry point
  engines/          — V3 engines (21 files, copied as-is)
  solvers/          — V3 solvers (7 files, copied as-is)
  logic/            — V3 logic modules (6 files, copied as-is)
  grpc_gen/         — Generated protobuf stubs
```

## V3 Engine Reuse

All V3 engine files are copied directly into this service. They are categorized by adaptation needs:

### Pure Computation (no changes needed)

- `fc60.py` — FC60 numerology (966 LOC)
- `numerology.py` — Pythagorean numerology (294 LOC)
- `math_analysis.py` — Mathematical analysis (160 LOC)
- `scoring.py` — Key scoring weights (290 LOC)
- `oracle.py` — Oracle readings (1,493 LOC)

### AI/ML (minor adaptation for V4 persistence)

- `ai_engine.py` — Claude CLI integration (569 LOC)
- `scanner_brain.py` — AI learning/suggestions (572 LOC)
- `learning.py` — XP/level learning (439 LOC)
- `learner.py` — Pattern learning (307 LOC)

### Operational (needs V4 adaptation)

- `config.py` — Will switch from config.json to environment variables
- `logger.py` — Will integrate with centralized logging
- `health.py` — Will expose gRPC health checks
- `vault.py` — Will use PostgreSQL instead of JSONL
- `security.py` — Will add AES-256-GCM (ENC4:) alongside V3 legacy decrypt
- `events.py` — Will adapt for gRPC streaming instead of GUI callbacks
- `session_manager.py`, `terminal_manager.py` — Will use PostgreSQL
- `notifier.py` — Telegram bot (moves to API layer in later phase)
- `memory.py`, `perf.py`, `balance.py` — Reference/utility

### Solvers

- `number_solver.py`, `name_solver.py`, `date_solver.py` — Oracle-type (run natively)
- `unified_solver.py`, `scanner_solver.py`, `btc_solver.py` — Reference (Rust replaces these)

### Logic

- `strategy_engine.py` — Level-gated strategy brain
- `timing_advisor.py` — Cosmic timing alignment
- `pattern_tracker.py` — Pattern analysis
- `key_scorer.py` — LRU-cached scoring
- `range_optimizer.py` — Smart range selection
- `history_manager.py` — Throttled persistence

## gRPC Interface

Defined in `proto/oracle.proto`. Key RPCs:

- `GetReading` — Oracle reading for a key/address
- `GetTiming` — Current cosmic timing quality
- `GetStrategy` — Strategy recommendations
- `AnalyzePattern` — Pattern analysis

## Key Commands

```bash
# Run service
python -m oracle_service.server

# Run tests
pytest tests/ -v

# Generate gRPC stubs
python -m grpc_tools.protoc -I../proto --python_out=oracle_service/grpc_gen --grpc_python_out=oracle_service/grpc_gen ../proto/oracle.proto
```
