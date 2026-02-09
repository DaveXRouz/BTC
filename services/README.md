# NPS Backend Services

## Overview

NPS splits the legacy monolith into two specialized backend services, each with a gRPC interface defined in `proto/`.

## Services

### Scanner (Rust)

High-performance key scanner rewritten in Rust for maximum throughput.

- **Location:** `scanner/`
- **Language:** Rust (Cargo project)
- **Interface:** gRPC (scanner.proto)
- **Responsibilities:** Key generation, address derivation, balance checking, checkpoint management
- **Legacy reference:** Python crypto files preserved in `scanner/docs/v3_*_reference.py`

See `scanner/README.md` for details.

### Oracle (Python)

FC60 numerology engine, oracle readings, AI learning, and strategy intelligence.

- **Location:** `oracle/`
- **Language:** Python 3.8+
- **Interface:** gRPC (oracle.proto)
- **Responsibilities:** Oracle readings, numerology analysis, timing advice, scoring, AI learning
- **Legacy reuse:** All legacy engines, solvers, and logic modules copied as-is

See `oracle/README.md` for details.

## Communication

```
Frontend  ->  API Gateway (FastAPI)  ->  Scanner (gRPC)
                                     ->  Oracle (gRPC)
```

Services do not communicate with each other directly. The API gateway orchestrates all cross-service operations.

## Shared Contracts

Protobuf definitions in `proto/` are the source of truth:

- `scanner.proto` — Scanner service interface
- `oracle.proto` — Oracle service interface

Generate client/server stubs with `make proto` from the project root.
