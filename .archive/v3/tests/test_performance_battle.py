"""
Performance & Stress Tests for NPS
====================================
Benchmarks throughput, concurrency, and resource bounds for core modules.
Uses generous thresholds suitable for CI runners.

Tests:
  1.  test_hybrid_score_throughput         - 1K hybrid_score calls < 5s
  2.  test_compute_jdn_throughput          - 10K compute_jdn calls < 2s
  3.  test_numerology_reduce_throughput    - 100K numerology_reduce calls < 2s
  4.  test_config_get_throughput           - 100K config.get() lookups < 2s
  5.  test_key_scorer_lru_at_50k           - 50K scores, cache capped at 10K
  6.  test_vault_10k_writes                - 10K vault writes < 30s (I/O bound)
  7.  test_events_50k_emissions            - 50K emissions, deque stays at 100
  8.  test_encrypt_decrypt_1000            - 1K encrypt/decrypt roundtrips < 10s
  9.  test_concurrent_vault_50_threads     - 50 threads x 100 writes, no corruption
  10. test_concurrent_config_20_threads    - 20 threads set+save, final state ok
  11. test_concurrent_events_10_threads    - 10 threads subscribe/emit/unsubscribe
  12. test_scoring_batch_performance       - score_batch of 500 keys < 5s
  13. test_numerology_reduce_large_numbers - reduce up to 10^18, no overflow
  14. test_config_get_nonexistent_key_fast - 100K get() misses < 2s
  15. test_events_deque_bounded            - 1000 emissions, deque len == 100
"""

import json
import os
import random
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

# ── path setup ──
sys.path.insert(0, str(Path(__file__).parent.parent))

from engines import fc60, numerology, config, events, security, vault
from engines.scoring import hybrid_score, score_batch
from logic.key_scorer import KeyScorer


class TestHybridScoreThroughput(unittest.TestCase):
    """1K hybrid_score calls must complete within 5 seconds."""

    def test_hybrid_score_throughput(self):
        keys = [random.randint(1, 2**64) for _ in range(1000)]
        start = time.time()
        for k in keys:
            result = hybrid_score(k)
            self.assertIn("final_score", result)
        elapsed = time.time() - start
        self.assertLess(elapsed, 5.0, f"1K hybrid_score took {elapsed:.2f}s (limit 5s)")


class TestComputeJdnThroughput(unittest.TestCase):
    """10K compute_jdn calls must complete within 2 seconds."""

    def test_compute_jdn_throughput(self):
        dates = [
            (random.randint(1900, 2100), random.randint(1, 12), random.randint(1, 28))
            for _ in range(10000)
        ]
        start = time.time()
        for y, m, d in dates:
            jdn = fc60.compute_jdn(y, m, d)
            self.assertIsInstance(jdn, int)
        elapsed = time.time() - start
        self.assertLess(elapsed, 2.0, f"10K compute_jdn took {elapsed:.2f}s (limit 2s)")


class TestNumerologyReduceThroughput(unittest.TestCase):
    """100K numerology_reduce calls must complete within 2 seconds."""

    def test_numerology_reduce_throughput(self):
        numbers = [random.randint(1, 10000) for _ in range(100000)]
        start = time.time()
        for n in numbers:
            result = numerology.numerology_reduce(n)
            self.assertTrue(1 <= result <= 33)
        elapsed = time.time() - start
        self.assertLess(
            elapsed, 2.0, f"100K numerology_reduce took {elapsed:.2f}s (limit 2s)"
        )


class TestConfigGetThroughput(unittest.TestCase):
    """100K config.get() lookups must complete within 2 seconds."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._cfg_path = os.path.join(self._tmp, "config.json")
        config.load_config(self._cfg_path)

    def tearDown(self):
        config._config = None
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_config_get_throughput(self):
        # Ensure config is loaded
        val = config.get("scanner.batch_size", 1000)
        self.assertIsNotNone(val)

        start = time.time()
        for _ in range(100000):
            config.get("scanner.batch_size", 1000)
        elapsed = time.time() - start
        self.assertLess(elapsed, 2.0, f"100K config.get took {elapsed:.2f}s (limit 2s)")


class TestKeyScorerLRU(unittest.TestCase):
    """Score 50K keys; LRU cache must stay at 10K max."""

    def test_key_scorer_lru_at_50k(self):
        scorer = KeyScorer()
        for i in range(50000):
            scorer.score_key(random.randint(1, 2**64))
        cache_sz = scorer.cache_size()
        self.assertLessEqual(
            cache_sz, 10000, f"Cache size {cache_sz} exceeds LRU max 10000"
        )
        # Must have actually stored some entries
        self.assertGreater(cache_sz, 0)


class TestVault10kWrites(unittest.TestCase):
    """10K vault writes must complete within 30 seconds."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        # Redirect vault directories to temp
        vault.DATA_DIR = Path(self._tmp)
        vault.FINDINGS_DIR = vault.DATA_DIR / "findings"
        vault.SESSIONS_DIR = vault.FINDINGS_DIR / "sessions"
        vault.SUMMARIES_DIR = vault.FINDINGS_DIR / "summaries"
        vault.init_vault()
        vault.start_session("perf_test")
        # Reset security so encrypt_dict is a no-op (PLAIN: prefix)
        security.reset()

    def tearDown(self):
        # Restore original paths
        vault.DATA_DIR = Path(__file__).parent.parent / "data"
        vault.FINDINGS_DIR = vault.DATA_DIR / "findings"
        vault.SESSIONS_DIR = vault.FINDINGS_DIR / "sessions"
        vault.SUMMARIES_DIR = vault.FINDINGS_DIR / "summaries"
        vault._current_session = None
        vault._session_count = 0
        vault._total_findings = 0
        vault._findings_since_summary = 0
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_vault_10k_writes(self):
        start = time.time()
        for i in range(10000):
            ok = vault.record_finding(
                {
                    "address": f"1BTC{i:08d}",
                    "chain": "btc",
                    "balance": 0.0,
                }
            )
            self.assertTrue(ok)
        elapsed = time.time() - start
        self.assertLess(
            elapsed, 30.0, f"10K vault writes took {elapsed:.2f}s (limit 30s)"
        )

        # Verify count
        summary = vault.get_summary()
        self.assertEqual(summary["total"], 10000)


class TestEvents50kEmissions(unittest.TestCase):
    """50K event emissions; _recent_events deque must stay at 100."""

    def setUp(self):
        events.clear()

    def tearDown(self):
        events.clear()

    def test_events_50k_emissions(self):
        counter = {"n": 0}

        def handler(data):
            counter["n"] += 1

        events.subscribe("PERF_TEST", handler)

        start = time.time()
        for i in range(50000):
            events.emit("PERF_TEST", {"i": i})
        elapsed = time.time() - start

        # deque bounded
        self.assertLessEqual(len(events._recent_events), 100)
        # handler called for all
        self.assertEqual(counter["n"], 50000)
        # Reasonable time (no strict limit, just sanity)
        self.assertLess(elapsed, 30.0, f"50K emissions took {elapsed:.2f}s")


class TestEncryptDecrypt1000(unittest.TestCase):
    """1K encrypt/decrypt roundtrips must complete within 10 seconds."""

    def setUp(self):
        security.reset()
        security.set_master_password("perf-test-password-123")

    def tearDown(self):
        security.reset()

    def test_encrypt_decrypt_1000(self):
        payloads = [f"secret_key_{i}_{'x' * 64}" for i in range(1000)]
        start = time.time()
        for p in payloads:
            enc = security.encrypt(p)
            self.assertTrue(enc.startswith("ENC:"))
            dec = security.decrypt(enc)
            self.assertEqual(dec, p)
        elapsed = time.time() - start
        self.assertLess(
            elapsed, 10.0, f"1K encrypt/decrypt took {elapsed:.2f}s (limit 10s)"
        )


class TestConcurrentVault50Threads(unittest.TestCase):
    """50 threads x 100 writes = 5000 findings; no corruption; < 30s."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        vault.DATA_DIR = Path(self._tmp)
        vault.FINDINGS_DIR = vault.DATA_DIR / "findings"
        vault.SESSIONS_DIR = vault.FINDINGS_DIR / "sessions"
        vault.SUMMARIES_DIR = vault.FINDINGS_DIR / "summaries"
        vault.init_vault()
        vault.start_session("concurrent_test")
        security.reset()

    def tearDown(self):
        vault.DATA_DIR = Path(__file__).parent.parent / "data"
        vault.FINDINGS_DIR = vault.DATA_DIR / "findings"
        vault.SESSIONS_DIR = vault.FINDINGS_DIR / "sessions"
        vault.SUMMARIES_DIR = vault.FINDINGS_DIR / "summaries"
        vault._current_session = None
        vault._session_count = 0
        vault._total_findings = 0
        vault._findings_since_summary = 0
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_concurrent_vault_50_threads(self):
        errors = []

        def writer(thread_id):
            try:
                for j in range(100):
                    ok = vault.record_finding(
                        {
                            "address": f"1BTC_t{thread_id}_j{j}",
                            "chain": "btc",
                            "balance": 0.0,
                            "thread": thread_id,
                        }
                    )
                    if not ok:
                        errors.append(f"Thread {thread_id} write {j} failed")
            except Exception as e:
                errors.append(f"Thread {thread_id} exception: {e}")

        threads = []
        start = time.time()
        for t in range(50):
            th = threading.Thread(target=writer, args=(t,))
            threads.append(th)
            th.start()

        for th in threads:
            th.join(timeout=30)

        elapsed = time.time() - start
        self.assertEqual(errors, [], f"Errors: {errors}")
        self.assertLess(elapsed, 30.0, f"50-thread vault writes took {elapsed:.2f}s")

        # Verify all 5000 lines written (read the JSONL file directly)
        vault_path = vault.FINDINGS_DIR / "vault_live.jsonl"
        self.assertTrue(vault_path.exists())
        with open(vault_path, "r") as f:
            lines = [l.strip() for l in f if l.strip()]
        self.assertEqual(len(lines), 5000, f"Expected 5000 lines, got {len(lines)}")

        # Each line must be valid JSON
        for line in lines:
            entry = json.loads(line)
            self.assertIn("address", entry)


class TestConcurrentConfig20Threads(unittest.TestCase):
    """20 threads set+save config concurrently; final state must be consistent."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._cfg_path = os.path.join(self._tmp, "config.json")
        config.load_config(self._cfg_path)

    def tearDown(self):
        config._config = None
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_concurrent_config_20_threads(self):
        errors = []

        def setter(thread_id):
            try:
                for j in range(50):
                    config.set(
                        f"test.thread_{thread_id}", f"val_{j}", path=self._cfg_path
                    )
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")

        threads = []
        start = time.time()
        for t in range(20):
            th = threading.Thread(target=setter, args=(t,))
            threads.append(th)
            th.start()

        for th in threads:
            th.join(timeout=30)

        elapsed = time.time() - start
        self.assertEqual(errors, [], f"Errors: {errors}")
        self.assertLess(elapsed, 30.0, f"20-thread config writes took {elapsed:.2f}s")

        # Final state: all 20 thread keys must exist
        for t in range(20):
            val = config.get(f"test.thread_{t}")
            self.assertIsNotNone(val, f"Key test.thread_{t} missing from final config")

        # Config file must be valid JSON
        with open(self._cfg_path, "r") as f:
            data = json.load(f)
        self.assertIn("test", data)


class TestConcurrentEvents10Threads(unittest.TestCase):
    """10 threads subscribe/emit/unsubscribe concurrently; no crashes."""

    def setUp(self):
        events.clear()

    def tearDown(self):
        events.clear()

    def test_concurrent_events_10_threads(self):
        errors = []
        total_emitted = threading.atomic = {"count": 0}
        count_lock = threading.Lock()

        def worker(thread_id):
            try:
                handler_calls = {"n": 0}

                def handler(data):
                    handler_calls["n"] += 1

                event_name = f"CONC_EVENT_{thread_id}"
                events.subscribe(event_name, handler)

                for j in range(200):
                    events.emit(event_name, {"thread": thread_id, "j": j})

                events.unsubscribe(event_name, handler)

                # Emit after unsubscribe -- handler should not fire
                events.emit(event_name, {"after_unsub": True})

                # handler_calls should be 200 (not 201)
                if handler_calls["n"] != 200:
                    errors.append(
                        f"Thread {thread_id}: expected 200 calls, got {handler_calls['n']}"
                    )
            except Exception as e:
                errors.append(f"Thread {thread_id} exception: {e}")

        threads = []
        start = time.time()
        for t in range(10):
            th = threading.Thread(target=worker, args=(t,))
            threads.append(th)
            th.start()

        for th in threads:
            th.join(timeout=15)

        elapsed = time.time() - start
        self.assertEqual(errors, [], f"Errors: {errors}")
        self.assertLess(elapsed, 15.0, f"10-thread events took {elapsed:.2f}s")

        # Deque should be bounded
        self.assertLessEqual(len(events._recent_events), 100)


class TestScoringBatchPerformance(unittest.TestCase):
    """score_batch of 500 keys must complete within 5 seconds."""

    def test_scoring_batch_performance(self):
        keys = [random.randint(1, 2**64) for _ in range(500)]
        start = time.time()
        results = score_batch(keys)
        elapsed = time.time() - start
        self.assertEqual(len(results), 500)
        # Results sorted by score descending
        scores = [r[1]["final_score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertLess(
            elapsed, 5.0, f"score_batch(500) took {elapsed:.2f}s (limit 5s)"
        )


class TestNumerologyReduceLargeNumbers(unittest.TestCase):
    """numerology_reduce must handle numbers up to 10^18 without overflow."""

    def test_numerology_reduce_large_numbers(self):
        large_numbers = [
            10**6,
            10**9,
            10**12,
            10**15,
            10**18,
            999999999999999999,
            123456789012345678,
            2**63,
        ]
        start = time.time()
        for n in large_numbers:
            result = numerology.numerology_reduce(n)
            # Must reduce to single digit or master number
            self.assertTrue(
                1 <= result <= 9 or result in (11, 22, 33),
                f"numerology_reduce({n}) = {result} is out of range",
            )
        elapsed = time.time() - start
        self.assertLess(elapsed, 2.0, f"Large number reduction took {elapsed:.2f}s")

        # Bulk: 10K random large numbers
        for _ in range(10000):
            n = random.randint(10**12, 10**18)
            result = numerology.numerology_reduce(n)
            self.assertTrue(1 <= result <= 9 or result in (11, 22, 33))


class TestConfigGetNonexistentKeyFast(unittest.TestCase):
    """100K get() calls with nonexistent keys must complete within 2 seconds."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._cfg_path = os.path.join(self._tmp, "config.json")
        config.load_config(self._cfg_path)

    def tearDown(self):
        config._config = None
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_config_get_nonexistent_key_fast(self):
        start = time.time()
        for i in range(100000):
            result = config.get(f"nonexistent.deep.path.key_{i % 100}", "default_val")
            self.assertEqual(result, "default_val")
        elapsed = time.time() - start
        self.assertLess(
            elapsed, 2.0, f"100K nonexistent key lookups took {elapsed:.2f}s (limit 2s)"
        )


class TestEventsDequeBounded(unittest.TestCase):
    """After 1000 emissions, _recent_events deque length must stay at 100."""

    def setUp(self):
        events.clear()

    def tearDown(self):
        events.clear()

    def test_events_deque_bounded(self):
        for i in range(1000):
            events.emit("BOUND_TEST", {"i": i})

        deque_len = len(events._recent_events)
        self.assertEqual(
            deque_len, 100, f"Deque length is {deque_len}, expected exactly 100"
        )

        # Most recent event should be i=999
        last = events._recent_events[-1]
        self.assertEqual(last["data"]["i"], 999)

        # Oldest event should be i=900
        first = events._recent_events[0]
        self.assertEqual(first["data"]["i"], 900)


if __name__ == "__main__":
    unittest.main()
