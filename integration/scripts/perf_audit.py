#!/usr/bin/env python3
"""Performance audit script for NPS Oracle endpoints.

Benchmarks all Oracle endpoints, computes statistics (p50, p95, p99, mean, min, max),
compares against performance targets, supports warm-up, concurrency, and baseline
comparison.

Usage:
    python3 integration/scripts/perf_audit.py
    python3 integration/scripts/perf_audit.py -n 30 --warmup 5 --concurrent 4
    python3 integration/scripts/perf_audit.py -n 20 --compare baseline_before.json
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

TARGETS: dict[str, dict[str, str | int]] = {
    "health": {"method": "GET", "path": "/api/health", "target_ms": 50},
    "user_creation": {"method": "POST", "path": "/api/oracle/users", "target_ms": 500},
    "user_list": {"method": "GET", "path": "/api/oracle/users", "target_ms": 200},
    "reading": {"method": "POST", "path": "/api/oracle/reading", "target_ms": 5000},
    "question": {"method": "POST", "path": "/api/oracle/question", "target_ms": 5000},
    "name_reading": {"method": "POST", "path": "/api/oracle/name", "target_ms": 5000},
    "daily_insight": {"method": "GET", "path": "/api/oracle/daily", "target_ms": 2000},
    "reading_history": {
        "method": "GET",
        "path": "/api/oracle/readings",
        "target_ms": 200,
    },
    "multi_user_2": {
        "method": "POST",
        "path": "/api/oracle/reading/multi-user",
        "target_ms": 8000,
    },
    "multi_user_5": {
        "method": "POST",
        "path": "/api/oracle/reading/multi-user",
        "target_ms": 8000,
    },
}

# Request payloads
PAYLOADS: dict[str, dict] = {
    "user_creation": {
        "name": "PerfAudit_User",
        "birthday": "1990-06-15",
        "mother_name": "PerfMother",
        "country": "US",
        "city": "BenchCity",
    },
    "reading": {"datetime": "2024-06-15T14:30:00+00:00"},
    "question": {"question": "Will this benchmark pass?"},
    "name_reading": {"name": "Performance Test"},
    "multi_user_2": {
        "users": [
            {"name": "Bench_A", "birth_year": 1990, "birth_month": 3, "birth_day": 15},
            {"name": "Bench_B", "birth_year": 1985, "birth_month": 7, "birth_day": 22},
        ],
        "primary_user_index": 0,
        "include_interpretation": False,
    },
    "multi_user_5": {
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
}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="NPS Performance Audit")
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=20,
        help="Measured iterations per endpoint (default: 20)",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=3,
        help="Warm-up iterations, not counted (default: 3)",
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=1,
        help="Concurrent requests per endpoint (default: 1)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="JSON output file path (default: auto)",
    )
    parser.add_argument(
        "--compare",
        type=str,
        default=None,
        help="Compare against previous baseline JSON file",
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
    endpoint_name: str = "",
) -> tuple[list[float], int, list[int]]:
    """Run n requests with given concurrency level.

    Returns:
        Tuple of (times, errors, created_user_ids).
    """
    times: list[float] = []
    errors = 0
    created_ids: list[int] = []

    def _single_request(idx: int) -> tuple[float | None, int | None]:
        try:
            if endpoint_name == "user_creation" and payload:
                p = dict(payload)
                p["name"] = f"PerfAudit_User_{idx}_{int(time.time())}"
                resp, ms = make_request(session, method, url, p)
                uid = resp.json().get("id") if resp.status_code == 201 else None
                return (ms if resp.status_code < 400 else None, uid)
            resp, ms = make_request(session, method, url, payload)
            return (ms if resp.status_code < 400 else None, None)
        except Exception:
            return (None, None)

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(_single_request, i) for i in range(n)]
        for future in as_completed(futures):
            ms, uid = future.result()
            if ms is not None:
                times.append(ms)
            else:
                errors += 1
            if uid is not None:
                created_ids.append(uid)

    return times, errors, created_ids


def compare_baselines(current: dict, baseline_path: str) -> list[str]:
    """Compare current results against a previous baseline file.

    Returns list of comparison lines.
    """
    lines: list[str] = []
    try:
        baseline = json.loads(Path(baseline_path).read_text())
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return [f"  WARNING: Cannot load baseline: {exc}"]

    prev_endpoints = baseline.get("endpoints", {})
    for name, data in current.items():
        prev = prev_endpoints.get(name)
        if not prev:
            continue
        prev_p95 = prev.get("p95_ms")
        curr_p95 = data.get("p95_ms")
        if prev_p95 is None or curr_p95 is None:
            continue

        if prev_p95 > 0:
            change_pct = ((curr_p95 - prev_p95) / prev_p95) * 100
        else:
            change_pct = 0.0

        if change_pct < -20:
            tag = "IMPROVED"
        elif change_pct > 20:
            tag = "REGRESSION"
        else:
            tag = "STABLE"

        lines.append(
            f"  [{tag:>10s}] {name:20s}  "
            f"p95: {prev_p95:.0f}ms -> {curr_p95:.0f}ms  ({change_pct:+.1f}%)"
        )

    return lines


def run_audit() -> None:
    """Run the full performance audit."""
    args = parse_args()
    iterations = max(1, args.iterations)
    warmup = max(0, args.warmup)
    concurrency = max(1, args.concurrent)

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

    print("=" * 70)
    print("NPS Performance Audit")
    print(f"API: {API_BASE_URL}")
    print(f"Iterations: {iterations} | Warm-up: {warmup} | Concurrency: {concurrency}")
    print("=" * 70)
    print()

    results: dict[str, dict] = {}
    passed = 0
    failed = 0
    all_created_user_ids: list[int] = []

    for endpoint_name, config in TARGETS.items():
        method = str(config["method"])
        url = f"{API_BASE_URL}{config['path']}"
        target = int(config["target_ms"])
        payload = PAYLOADS.get(endpoint_name)

        # Warm-up phase (discarded)
        for _ in range(warmup):
            try:
                if endpoint_name == "user_creation" and payload:
                    p = dict(payload)
                    p["name"] = f"PerfWarmup_{int(time.time())}"
                    resp, _ = make_request(session, method, url, p)
                    if resp.status_code == 201:
                        uid = resp.json().get("id")
                        if uid:
                            all_created_user_ids.append(uid)
                else:
                    make_request(session, method, url, payload)
            except Exception:
                pass

        # Measured phase
        if concurrency > 1:
            times, errors, created_ids = run_concurrent(
                session, method, url, payload, iterations, concurrency, endpoint_name
            )
            all_created_user_ids.extend(created_ids)
        else:
            times: list[float] = []
            errors = 0
            for i in range(iterations):
                try:
                    if endpoint_name == "user_creation" and payload:
                        p = dict(payload)
                        p["name"] = f"PerfAudit_User_{i}_{int(time.time())}"
                        resp, ms = make_request(session, method, url, p)
                        if resp.status_code == 201:
                            uid = resp.json().get("id")
                            if uid:
                                all_created_user_ids.append(uid)
                    else:
                        resp, ms = make_request(session, method, url, payload)

                    if resp.status_code < 400:
                        times.append(ms)
                    else:
                        errors += 1
                except Exception:
                    errors += 1

        stats = compute_stats(times)
        target_passed = stats["p95"] is not None and stats["p95"] < target
        if target_passed:
            passed += 1
            status_str = "PASS"
        else:
            failed += 1
            status_str = "FAIL"

        results[endpoint_name] = {
            "p50_ms": stats["p50"],
            "p95_ms": stats["p95"],
            "p99_ms": stats["p99"],
            "mean_ms": stats["mean"],
            "min_ms": stats["min"],
            "max_ms": stats["max"],
            "target_ms": target,
            "passed": target_passed,
            "errors": errors,
            "samples": len(times),
        }

        p50_str = f"{stats['p50']:.0f}ms" if stats["p50"] else "N/A"
        p95_str = f"{stats['p95']:.0f}ms" if stats["p95"] else "N/A"
        p99_str = f"{stats['p99']:.0f}ms" if stats["p99"] else "N/A"
        print(
            f"  [{status_str}] {endpoint_name:20s}  "
            f"p50={p50_str:>8s}  p95={p95_str:>8s}  p99={p99_str:>8s}  "
            f"target=<{target}ms"
        )

    # Cleanup created users
    for uid in all_created_user_ids:
        try:
            session.delete(f"{API_BASE_URL}/api/oracle/users/{uid}")
        except Exception:
            pass

    # Write performance baseline
    baseline = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": "Auto-generated by perf_audit.py",
        "config": {
            "iterations": iterations,
            "warmup": warmup,
            "concurrent": concurrency,
        },
        "endpoints": {},
        "summary": {
            "total_endpoints": len(results),
            "passed": passed,
            "failed": failed,
        },
    }
    for name, data in results.items():
        baseline["endpoints"][name] = {
            "p50_ms": data["p50_ms"],
            "p95_ms": data["p95_ms"],
            "p99_ms": data["p99_ms"],
            "mean_ms": data["mean_ms"],
            "min_ms": data["min_ms"],
            "max_ms": data["max_ms"],
            "target_ms": data["target_ms"],
            "passed": data["passed"],
        }

    reports_dir = Path(__file__).resolve().parents[1] / "reports"
    reports_dir.mkdir(exist_ok=True)

    if args.output:
        baseline_path = Path(args.output)
    else:
        baseline_path = reports_dir / "performance_baseline.json"

    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_text(json.dumps(baseline, indent=2) + "\n")

    print()
    print("=" * 70)
    print(f"Results: {passed}/{passed + failed} endpoints within target")
    print(f"Baseline saved to: {baseline_path}")

    # Compare against previous baseline
    if args.compare:
        print()
        print("Comparison against baseline:")
        comparison_lines = compare_baselines(results, args.compare)
        for line in comparison_lines:
            print(line)

    print("=" * 70)

    if failed > 0:
        print(f"\nWARNING: {failed} endpoint(s) exceeded performance targets")
        sys.exit(1)
    else:
        print("\nAll endpoints within performance targets.")
        sys.exit(0)


if __name__ == "__main__":
    run_audit()
