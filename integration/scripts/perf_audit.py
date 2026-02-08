#!/usr/bin/env python3
"""Performance audit script for NPS V4 Oracle endpoints.

Benchmarks all Oracle endpoints, computes statistics (p50, p95, mean, min, max),
compares against performance targets, and outputs results.

Usage:
    python3 integration/scripts/perf_audit.py
"""

import json
import os
import statistics
import sys
import time
from pathlib import Path

import requests

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

ITERATIONS = 5  # Number of times to test each endpoint

TARGETS = {
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
PAYLOADS = {
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


def make_request(session, method, url, payload=None):
    """Make a timed HTTP request and return (response, elapsed_ms)."""
    start = time.perf_counter()
    if method == "GET":
        resp = session.get(url, timeout=30)
    elif method == "POST":
        resp = session.post(url, json=payload, timeout=30)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return resp, elapsed_ms


def compute_stats(times):
    """Compute p50, p95, mean, min, max from a list of times."""
    if not times:
        return {"p50": None, "p95": None, "mean": None, "min": None, "max": None}
    sorted_times = sorted(times)
    n = len(sorted_times)
    p50_idx = int(n * 0.5)
    p95_idx = min(int(n * 0.95), n - 1)
    return {
        "p50": round(sorted_times[p50_idx], 1),
        "p95": round(sorted_times[p95_idx], 1),
        "mean": round(statistics.mean(times), 1),
        "min": round(min(times), 1),
        "max": round(max(times), 1),
    }


def run_audit():
    """Run the full performance audit."""
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
    print("NPS V4 Performance Audit")
    print(f"API: {API_BASE_URL}")
    print(f"Iterations per endpoint: {ITERATIONS}")
    print("=" * 70)
    print()

    results = {}
    passed = 0
    failed = 0
    created_user_ids = []

    for endpoint_name, config in TARGETS.items():
        method = config["method"]
        url = f"{API_BASE_URL}{config['path']}"
        target = config["target_ms"]
        payload = PAYLOADS.get(endpoint_name)

        times = []
        errors = 0

        for i in range(ITERATIONS):
            try:
                # For user creation, use unique names
                if endpoint_name == "user_creation" and payload:
                    p = dict(payload)
                    p["name"] = f"PerfAudit_User_{i}_{int(time.time())}"
                    resp, ms = make_request(session, method, url, p)
                    if resp.status_code == 201:
                        created_user_ids.append(resp.json().get("id"))
                else:
                    resp, ms = make_request(session, method, url, payload)

                if resp.status_code < 400:
                    times.append(ms)
                else:
                    errors += 1
            except Exception as e:
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
        print(
            f"  [{status_str}] {endpoint_name:20s}  p50={p50_str:>8s}  p95={p95_str:>8s}  target=<{target}ms"
        )

    # Cleanup created users
    for uid in created_user_ids:
        try:
            session.delete(f"{API_BASE_URL}/api/oracle/users/{uid}")
        except Exception:
            pass

    # Write performance baseline
    baseline = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": "Auto-generated by perf_audit.py",
        "iterations": ITERATIONS,
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
            "mean_ms": data["mean_ms"],
            "min_ms": data["min_ms"],
            "max_ms": data["max_ms"],
            "target_ms": data["target_ms"],
            "passed": data["passed"],
        }

    reports_dir = Path(__file__).resolve().parents[1] / "reports"
    reports_dir.mkdir(exist_ok=True)
    baseline_path = reports_dir / "performance_baseline.json"
    baseline_path.write_text(json.dumps(baseline, indent=2) + "\n")

    print()
    print("=" * 70)
    print(f"Results: {passed}/{passed + failed} endpoints within target")
    print(f"Baseline saved to: {baseline_path}")
    print("=" * 70)

    if failed > 0:
        print(f"\nWARNING: {failed} endpoint(s) exceeded performance targets")
        sys.exit(1)
    else:
        print("\nAll endpoints within performance targets.")
        sys.exit(0)


if __name__ == "__main__":
    run_audit()
