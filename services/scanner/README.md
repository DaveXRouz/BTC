# NPS Scanner Service (Rust)

## Overview

High-performance key scanner rewritten in Rust for maximum throughput. Replaces the legacy Python scanner (`unified_solver.py`, `btc_solver.py`, `scanner_solver.py`) with native performance.

## Architecture

```
src/
  main.rs           — Entry point, gRPC server startup
  crypto/           — secp256k1, address derivation
  scanner/          — Multi-threaded scan loop, checkpoints
  balance/          — Async balance checking (reqwest)
  scoring/          — Key scoring (must match Python Oracle weights)
  grpc/             — gRPC server implementing scanner.proto
```

## Legacy Reference Files

The `docs/` directory contains legacy Python implementations as reference for the Rust rewrite:

| Reference File            | Legacy Source            | Purpose                                               |
| ------------------------- | ------------------------ | ----------------------------------------------------- |
| `v3_crypto_reference.py`  | `nps/engines/crypto.py`  | secp256k1, address generation, key derivation         |
| `v3_keccak_reference.py`  | `nps/engines/keccak.py`  | Keccak-256 for Ethereum addresses                     |
| `v3_bip39_reference.py`   | `nps/engines/bip39.py`   | BIP39 mnemonic generation/validation                  |
| `v3_balance_reference.py` | `nps/engines/balance.py` | Multi-chain balance checking (BTC, ETH, BSC, Polygon) |

## Performance Targets

- Key generation: 10,000+ keys/sec per thread
- Multi-threaded scanning with configurable thread count
- Checkpoint saves every N keys (configurable, default 10,000)
- Async balance checking to avoid blocking scan threads

## gRPC Interface

Defined in `proto/scanner.proto`. Key RPCs:

- `StartScan` — Begin scanning with parameters
- `StopScan` — Graceful stop with checkpoint
- `GetStatus` — Current scan progress
- `GetCheckpoint` — Load/save checkpoint state

## Scoring Consistency

The Rust scoring engine **must produce identical scores** to the Python Oracle scoring engine for the same input. Shared test vectors will be maintained in `proto/` to verify cross-language consistency.

## Key Commands

```bash
# Build
cargo build --release

# Run tests
cargo test

# Run with gRPC server
cargo run -- --port 50051
```
