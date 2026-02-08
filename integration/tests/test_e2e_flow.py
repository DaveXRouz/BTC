"""Phase 5: End-to-end single-user flow with timing measurements."""

import json
import time
from pathlib import Path

import pytest

from conftest import api_url

# Performance targets (milliseconds)
TARGETS = {
    "user_creation": 500,
    "user_list": 200,
    "reading": 5000,
    "question": 5000,
    "name_reading": 5000,
    "daily_insight": 2000,
    "reading_history": 200,
    "single_reading": 200,
    "user_update": 500,
    "user_delete": 500,
    "multi_user_reading": 8000,
}


def timed_request(client, method, url, **kwargs):
    """Execute a request and return (response, elapsed_ms)."""
    start = time.perf_counter()
    resp = getattr(client, method)(url, **kwargs)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return resp, elapsed_ms


@pytest.mark.e2e
class TestEndToEndFlow:
    """Complete scripted flow simulating a single user session."""

    def test_full_oracle_flow(self, api_client):
        """Run the complete Oracle flow and record timings."""
        timings = {}

        # 1. Create user
        resp, ms = timed_request(
            api_client,
            "post",
            api_url("/api/oracle/users"),
            json={
                "name": "IntTest_E2E",
                "birthday": "1990-06-15",
                "mother_name": "E2EMother",
                "country": "US",
                "city": "San Francisco",
            },
        )
        assert resp.status_code == 201, f"Create user failed: {resp.text}"
        user_id = resp.json()["id"]
        timings["user_creation"] = ms
        print(
            f"\n  1. Create user:     {ms:.1f}ms (target: <{TARGETS['user_creation']}ms)"
        )

        # 2. List users
        resp, ms = timed_request(api_client, "get", api_url("/api/oracle/users"))
        assert resp.status_code == 200
        users = resp.json()
        assert users["total"] >= 1
        timings["user_list"] = ms
        print(f"  2. List users:      {ms:.1f}ms (target: <{TARGETS['user_list']}ms)")

        # 3. Create reading
        resp, ms = timed_request(
            api_client,
            "post",
            api_url("/api/oracle/reading"),
            json={"datetime": "2024-06-15T14:30:00+00:00"},
        )
        assert resp.status_code == 200, f"Create reading failed: {resp.text}"
        reading_data = resp.json()
        assert "fc60" in reading_data
        assert "numerology" in reading_data
        timings["reading"] = ms
        print(f"  3. Oracle reading:  {ms:.1f}ms (target: <{TARGETS['reading']}ms)")

        # 4. Ask question
        resp, ms = timed_request(
            api_client,
            "post",
            api_url("/api/oracle/question"),
            json={"question": "Is the integration working correctly?"},
        )
        assert resp.status_code == 200
        q_data = resp.json()
        assert "answer" in q_data
        timings["question"] = ms
        print(f"  4. Question:        {ms:.1f}ms (target: <{TARGETS['question']}ms)")

        # 5. Name cipher
        resp, ms = timed_request(
            api_client,
            "post",
            api_url("/api/oracle/name"),
            json={"name": "NPS Integration"},
        )
        assert resp.status_code == 200
        name_data = resp.json()
        assert "destiny_number" in name_data
        timings["name_reading"] = ms
        print(
            f"  5. Name cipher:     {ms:.1f}ms (target: <{TARGETS['name_reading']}ms)"
        )

        # 6. Daily insight
        resp, ms = timed_request(api_client, "get", api_url("/api/oracle/daily"))
        assert resp.status_code == 200
        daily_data = resp.json()
        assert "date" in daily_data
        timings["daily_insight"] = ms
        print(
            f"  6. Daily insight:   {ms:.1f}ms (target: <{TARGETS['daily_insight']}ms)"
        )

        # 7. Reading history
        resp, ms = timed_request(api_client, "get", api_url("/api/oracle/readings"))
        assert resp.status_code == 200
        history = resp.json()
        assert history["total"] >= 1
        timings["reading_history"] = ms
        print(
            f"  7. Reading history: {ms:.1f}ms (target: <{TARGETS['reading_history']}ms)"
        )

        # 8. Single reading retrieval
        if history["readings"]:
            reading_id = history["readings"][0]["id"]
            resp, ms = timed_request(
                api_client, "get", api_url(f"/api/oracle/readings/{reading_id}")
            )
            assert resp.status_code == 200
            timings["single_reading"] = ms
            print(
                f"  8. Single reading:  {ms:.1f}ms (target: <{TARGETS['single_reading']}ms)"
            )

        # 9. Update user
        resp, ms = timed_request(
            api_client,
            "put",
            api_url(f"/api/oracle/users/{user_id}"),
            json={"city": "Los Angeles"},
        )
        assert resp.status_code == 200
        assert resp.json()["city"] == "Los Angeles"
        timings["user_update"] = ms
        print(f"  9. Update user:     {ms:.1f}ms (target: <{TARGETS['user_update']}ms)")

        # 10. Multi-user reading
        resp, ms = timed_request(
            api_client,
            "post",
            api_url("/api/oracle/reading/multi-user"),
            json={
                "users": [
                    {
                        "name": "E2E_A",
                        "birth_year": 1990,
                        "birth_month": 3,
                        "birth_day": 15,
                    },
                    {
                        "name": "E2E_B",
                        "birth_year": 1985,
                        "birth_month": 7,
                        "birth_day": 22,
                    },
                ],
                "primary_user_index": 0,
                "include_interpretation": False,
            },
        )
        assert resp.status_code == 200, f"Multi-user reading failed: {resp.text}"
        timings["multi_user_reading"] = ms
        print(
            f"  10. Multi-user:     {ms:.1f}ms (target: <{TARGETS['multi_user_reading']}ms)"
        )

        # 11. Delete user (cleanup)
        resp, ms = timed_request(
            api_client, "delete", api_url(f"/api/oracle/users/{user_id}")
        )
        assert resp.status_code == 200
        timings["user_delete"] = ms
        print(f"  11. Delete user:    {ms:.1f}ms (target: <{TARGETS['user_delete']}ms)")

        # Save performance baseline
        baseline = {
            "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "endpoints": {},
        }
        for key, elapsed in timings.items():
            target = TARGETS.get(key, 1000)
            baseline["endpoints"][key] = {
                "p50_ms": round(elapsed, 1),
                "p95_ms": round(elapsed * 1.3, 1),  # estimate from single run
                "target_ms": target,
                "passed": elapsed < target,
            }

        # Count passed/failed
        passed = sum(1 for v in baseline["endpoints"].values() if v["passed"])
        total = len(baseline["endpoints"])
        baseline["summary"] = {
            "total_endpoints": total,
            "passed": passed,
            "failed": total - passed,
        }

        # Write to reports
        reports_dir = Path(__file__).resolve().parents[1] / "reports"
        reports_dir.mkdir(exist_ok=True)
        baseline_path = reports_dir / "performance_baseline.json"
        baseline_path.write_text(json.dumps(baseline, indent=2) + "\n")
        print(f"\n  Performance baseline saved to: {baseline_path}")
        print(f"  Results: {passed}/{total} endpoints within target")

        # All targets should pass
        for key, elapsed in timings.items():
            target = TARGETS.get(key, 1000)
            assert (
                elapsed < target
            ), f"Endpoint '{key}' took {elapsed:.1f}ms, target is <{target}ms"
