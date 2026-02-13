#!/usr/bin/env python3
"""Reading Benchmark -- measures reading generation performance.

Runs N reading requests and reports p50/p95/p99 response times.
Supports multiple reading types (time, name, question, daily, multi-user).

Usage:
    python3 integration/scripts/benchmark_readings.py -n 50 --type reading
    python3 integration/scripts/benchmark_readings.py -n 20 --type question --concurrent 4
    python3 integration/scripts/benchmark_readings.py -n 10 --type all
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# ─── Configuration ──────────────────────────────────────────────────────────

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_SECRET_KEY = os.environ.get("API_SECRET_KEY", "")

# Load from .env if available
_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
if _ENV_PATH.exists():
    for line in _ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if key and key not in os.environ:
                os.environ[key] = value
    API_SECRET_KEY = os.environ.get("API_SECRET_KEY", API_SECRET_KEY)

# Reading type configurations
READING_TYPES: dict[str, dict] = {
    "reading": {
        "method": "POST",
        "path": "/api/oracle/reading",
        "payload": {"datetime": "2024-06-15T14:30:00+00:00"},
        "target_ms": 5000,
    },
    "question": {
        "method": "POST",
        "path": "/api/oracle/question",
        "payload": {"question": "Will the benchmark pass?"},
        "target_ms": 5000,
    },
    "name": {
        "method": "POST",
        "path": "/api/oracle/name",
        "payload": {"name": "Performance Test"},
        "target_ms": 5000,
    },
    "daily": {
        "method": "GET",
        "path": "/api/oracle/daily",
        "payload": None,
        "target_ms": 2000,
    },
    "multi_user_2": {
        "method": "POST",
        "path": "/api/oracle/reading/multi-user",
        "payload": {
            "users": [
                {
                    "name": "Bench_A",
                    "birth_year": 1990,
                    "birth_month": 3,
                    "birth_day": 15,
                },
                {
                    "name": "Bench_B",
                    "birth_year": 1985,
                    "birth_month": 7,
                    "birth_day": 22,
                },
            ],
            "primary_user_index": 0,
            "include_interpretation": False,
        },
        "target_ms": 8000,
    },
    "multi_user_5": {
        "method": "POST",
        "path": "/api/oracle/reading/multi-user",
        "payload": {
            "users": [
                {
                    "name": f"Bench5_{i}",
                    "birth_year": 1980 + i,
                    "birth_month": (i % 12) + 1,
                    "birth_day": 10 + i,
                }
                for i in range(5)
            ],
            "primary_user_index": 0,
            "include_interpretation": False,
        },
        "target_ms": 8000,
    },
}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    valid_types = list(READING_TYPES.keys()) + ["all"]
    parser = argparse.ArgumentParser(description="NPS Reading Benchmark")
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=20,
        help="Number of measured iterations per type (default: 20)",
    )
    parser.add_argument(
        "--type",
        type=str,
        default="all",
        choices=valid_types,
        help="Reading type to benchmark (default: all)",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=3,
        help="Warm-up iterations before measurement (default: 3)",
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=1,
        help="Concurrent requests per type (default: 1)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="JSON output file (default: integration/reports/reading_benchmark.json)",
    )
    return parser.parse_args()


def make_request(
    session: requests.Session,
    method: str,
    url: str,
    payload: dict | None = None,
) -> tuple[requests.Response, float]:
    """Make a timed HTTP request and return (response, elapsed_ms)."""
    start = time.perf_counter()
    if method == "GET":
        resp = session.get(url, timeout=30)
    elif method == "POST":
        resp = session.post(url, json=payload, timeout=30)
    else:
        resp = session.request(method, url, json=payload, timeout=30)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return resp, elapsed_ms


def compute_stats(times: list[float]) -> dict[str, float | None]:
    """Compute p50, p95, p99, mean, min, max from a list of times."""
    if not times:
        return {
            "p50": None,
            "p95": None,
            "p99": None,
            "mean": None,
            "min": None,
            "max": None,
        }
    sorted_times = sorted(times)
    n = len(sorted_times)
    return {
        "p50": round(sorted_times[int(n * 0.50)], 1),
        "p95": round(sorted_times[min(int(n * 0.95), n - 1)], 1),
        "p99": round(sorted_times[min(int(n * 0.99), n - 1)], 1),
        "mean": round(statistics.mean(times), 1),
        "min": round(min(times), 1),
        "max": round(max(times), 1),
    }


def run_concurrent(
    session: requests.Session,
    method: str,
    url: str,
    payload: dict | None,
    n: int,
    concurrency: int,
) -> tuple[list[float], int]:
    """Run n requests with given concurrency level.

    Returns:
        Tuple of (times, errors).
    """
    times: list[float] = []
    errors = 0

    def _single_request() -> float | None:
        try:
            resp, ms = make_request(session, method, url, payload)
            return ms if resp.status_code < 400 else None
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(_single_request) for _ in range(n)]
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                times.append(result)
            else:
                errors += 1

    return times, errors


def benchmark_type(
    session: requests.Session,
    type_name: str,
    config: dict,
    count: int,
    warmup: int,
    concurrency: int,
) -> dict:
    """Benchmark a single reading type.

    Returns:
        Dict with stats, target, passed flag, samples, errors.
    """
    method = config["method"]
    url = f"{API_BASE_URL}{config['path']}"
    payload = config["payload"]
    target_ms = config["target_ms"]

    # Warm-up phase (discarded)
    for _ in range(warmup):
        try:
            make_request(session, method, url, payload)
        except Exception:
            pass

    # Measured phase
    if concurrency > 1:
        times, errors = run_concurrent(
            session, method, url, payload, count, concurrency
        )
    else:
        times = []
        errors = 0
        for i in range(count):
            try:
                resp, ms = make_request(session, method, url, payload)
                if resp.status_code < 400:
                    times.append(ms)
                else:
                    errors += 1
            except Exception:
                errors += 1
            # Progress indicator for long-running benchmarks
            if count >= 10 and (i + 1) % 5 == 0:
                print(f"    {type_name}: {i + 1}/{count} iterations complete")

    stats = compute_stats(times)
    target_passed = stats["p95"] is not None and stats["p95"] < target_ms

    return {
        "p50_ms": stats["p50"],
        "p95_ms": stats["p95"],
        "p99_ms": stats["p99"],
        "mean_ms": stats["mean"],
        "min_ms": stats["min"],
        "max_ms": stats["max"],
        "target_ms": target_ms,
        "passed": target_passed,
        "samples": len(times),
        "errors": errors,
    }


def run_benchmark() -> None:
    """Run the reading benchmark."""
    args = parse_args()
    count = max(1, args.count)
    warmup = max(0, args.warmup)
    concurrency = max(1, args.concurrent)
    reading_type = args.type

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {API_SECRET_KEY}",
            "Content-Type": "application/json",
        }
    )

    # Check API is reachable
    try:
        resp = session.get(f"{API_BASE_URL}/api/health", timeout=5)
        if resp.status_code != 200:
            print(
                f"ERROR: API returned {resp.status_code} at {API_BASE_URL}/api/health"
            )
            sys.exit(1)
    except requests.ConnectionError:
        print(f"ERROR: Cannot connect to API at {API_BASE_URL}")
        print(
            "Make sure the API server is running: cd api && uvicorn app.main:app --port 8000"
        )
        sys.exit(1)

    # Determine which types to benchmark
    if reading_type == "all":
        types_to_run = dict(READING_TYPES)
    else:
        types_to_run = {reading_type: READING_TYPES[reading_type]}

    print("=" * 70)
    print("NPS Reading Benchmark")
    print(f"API: {API_BASE_URL}")
    print(
        f"Types: {', '.join(types_to_run.keys())} | "
        f"Iterations: {count} | Warm-up: {warmup} | Concurrency: {concurrency}"
    )
    print("=" * 70)
    print()

    results: dict[str, dict] = {}
    total_passed = 0
    total_failed = 0

    for type_name, config in types_to_run.items():
        print(f"  Benchmarking: {type_name}...")
        result = benchmark_type(session, type_name, config, count, warmup, concurrency)
        results[type_name] = result

        status = "PASS" if result["passed"] else "FAIL"
        if result["passed"]:
            total_passed += 1
        else:
            total_failed += 1

        p50_str = f"{result['p50_ms']:.0f}ms" if result["p50_ms"] else "N/A"
        p95_str = f"{result['p95_ms']:.0f}ms" if result["p95_ms"] else "N/A"
        p99_str = f"{result['p99_ms']:.0f}ms" if result["p99_ms"] else "N/A"
        print(
            f"  [{status}] {type_name:20s}  "
            f"p50={p50_str:>8s}  p95={p95_str:>8s}  p99={p99_str:>8s}  "
            f"target=<{result['target_ms']}ms"
        )
        print()

    # Write JSON report
    report = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "config": {
            "iterations": count,
            "warmup": warmup,
            "concurrent": concurrency,
        },
        "results": results,
        "summary": {
            "total_types": len(results),
            "passed": total_passed,
            "failed": total_failed,
        },
    }

    reports_dir = Path(__file__).resolve().parents[1] / "reports"
    reports_dir.mkdir(exist_ok=True)

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = reports_dir / "reading_benchmark.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n")

    print("=" * 70)
    print(
        f"Results: {total_passed}/{total_passed + total_failed} reading types within target"
    )
    print(f"Report saved to: {output_path}")
    print("=" * 70)

    if total_failed > 0:
        print(f"\nWARNING: {total_failed} reading type(s) exceeded performance targets")
        sys.exit(1)
    else:
        print("\nAll reading types within performance targets.")
        sys.exit(0)


if __name__ == "__main__":
    run_benchmark()
