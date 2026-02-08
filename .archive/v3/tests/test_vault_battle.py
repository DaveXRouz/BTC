"""Battle tests for engines.vault module.

Stress tests, concurrency tests, corruption recovery, edge cases,
and export validation for the Findings Vault.
"""

import csv
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engines import vault


class TestVaultBattle(unittest.TestCase):
    """Battle-hardened tests for the vault module."""

    def setUp(self):
        """Use temp directories for vault storage and reset module state."""
        self._tmpdir = tempfile.mkdtemp()
        self._orig_findings = vault.FINDINGS_DIR
        self._orig_sessions = vault.SESSIONS_DIR
        self._orig_summaries = vault.SUMMARIES_DIR
        self._orig_data = vault.DATA_DIR

        vault.DATA_DIR = Path(self._tmpdir) / "data"
        vault.FINDINGS_DIR = vault.DATA_DIR / "findings"
        vault.SESSIONS_DIR = vault.FINDINGS_DIR / "sessions"
        vault.SUMMARIES_DIR = vault.FINDINGS_DIR / "summaries"

        vault._current_session = None
        vault._session_count = 0
        vault._total_findings = 0
        vault._findings_since_summary = 0

    def tearDown(self):
        """Restore original paths and clean up temp directory."""
        vault.FINDINGS_DIR = self._orig_findings
        vault.SESSIONS_DIR = self._orig_sessions
        vault.SUMMARIES_DIR = self._orig_summaries
        vault.DATA_DIR = self._orig_data

        vault._current_session = None
        vault._session_count = 0
        vault._total_findings = 0
        vault._findings_since_summary = 0
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    # ------------------------------------------------------------------ #
    # 1. Rapid writes stress test
    # ------------------------------------------------------------------ #
    def test_rapid_writes_1000(self):
        """Record 1000 findings rapidly and verify the count matches."""
        vault.init_vault()
        vault.start_session("rapid")

        for i in range(1000):
            result = vault.record_finding({"address": f"addr_{i}", "chain": "btc"})
            self.assertTrue(result)

        self.assertEqual(vault._total_findings, 1000)
        findings = vault.get_findings(limit=2000)
        self.assertEqual(len(findings), 1000)

    # ------------------------------------------------------------------ #
    # 2. Concurrent 50 threads
    # ------------------------------------------------------------------ #
    def test_concurrent_50_threads(self):
        """50 threads each writing 10 findings, total must be exactly 500."""
        vault.init_vault()
        vault.start_session("concurrent_50")

        errors = []
        barrier = threading.Barrier(50)

        def writer(tid):
            try:
                barrier.wait(timeout=5)
            except threading.BrokenBarrierError:
                pass
            for i in range(10):
                try:
                    vault.record_finding({"address": f"t{tid}_a{i}", "chain": "eth"})
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=writer, args=(t,)) for t in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        self.assertEqual(len(errors), 0, f"Thread errors: {errors}")
        self.assertEqual(vault._total_findings, 500)
        findings = vault.get_findings(limit=1000)
        self.assertEqual(len(findings), 500)

    # ------------------------------------------------------------------ #
    # 3. Corrupt JSONL recovery
    # ------------------------------------------------------------------ #
    def test_corrupt_jsonl_recovery(self):
        """get_findings skips corrupt lines mixed with valid ones."""
        vault.init_vault()
        vault_path = vault.FINDINGS_DIR / "vault_live.jsonl"

        valid_entry_1 = json.dumps(
            {"address": "good1", "chain": "btc", "timestamp": 1.0, "session": "x"}
        )
        valid_entry_2 = json.dumps(
            {"address": "good2", "chain": "eth", "timestamp": 2.0, "session": "x"}
        )
        corrupt_lines = [
            "NOT VALID JSON{{{",
            '{"address": "incomplete',
            "",
            "{bad: json, no quotes}",
        ]

        with open(vault_path, "w") as f:
            f.write(valid_entry_1 + "\n")
            for bad in corrupt_lines:
                f.write(bad + "\n")
            f.write(valid_entry_2 + "\n")

        findings = vault.get_findings(limit=100)
        self.assertEqual(len(findings), 2)
        addresses = [f["address"] for f in findings]
        self.assertIn("good1", addresses)
        self.assertIn("good2", addresses)

    # ------------------------------------------------------------------ #
    # 4. Export CSV empty vault
    # ------------------------------------------------------------------ #
    def test_export_csv_empty(self):
        """Export empty vault produces CSV with headers only."""
        vault.init_vault()

        output = vault.export_csv()
        self.assertTrue(os.path.exists(output))

        with open(output, "r") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Should have exactly 1 row (the header)
        self.assertEqual(len(rows), 1)
        header = rows[0]
        self.assertIn("timestamp", header)
        self.assertIn("address", header)
        self.assertIn("chain", header)

    # ------------------------------------------------------------------ #
    # 5. Export CSV with data
    # ------------------------------------------------------------------ #
    def test_export_csv_with_data(self):
        """Export vault with 5 findings produces correct CSV rows."""
        vault.init_vault()
        vault.start_session("csv_data")

        for i in range(5):
            vault.record_finding(
                {
                    "address": f"csv_addr_{i}",
                    "chain": "btc",
                    "balance": float(i),
                }
            )

        output = vault.export_csv()
        self.assertTrue(os.path.exists(output))

        with open(output, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 5)
        for i, row in enumerate(rows):
            self.assertEqual(row["address"], f"csv_addr_{i}")
            self.assertEqual(row["chain"], "btc")

    # ------------------------------------------------------------------ #
    # 6. Export JSON with data
    # ------------------------------------------------------------------ #
    def test_export_json_with_data(self):
        """Export vault with 5 findings produces valid JSON array."""
        vault.init_vault()
        vault.start_session("json_data")

        for i in range(5):
            vault.record_finding(
                {
                    "address": f"json_addr_{i}",
                    "chain": "eth",
                    "balance": i * 0.5,
                }
            )

        output = vault.export_json()
        self.assertTrue(os.path.exists(output))

        with open(output, "r") as f:
            data = json.load(f)

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 5)
        for i, entry in enumerate(data):
            self.assertEqual(entry["address"], f"json_addr_{i}")
            self.assertEqual(entry["chain"], "eth")
            self.assertIn("timestamp", entry)
            self.assertIn("session", entry)

    # ------------------------------------------------------------------ #
    # 7. Finding not dict
    # ------------------------------------------------------------------ #
    def test_finding_not_dict(self):
        """record_finding with non-dict argument returns False."""
        vault.init_vault()
        vault.start_session("type_check")

        self.assertFalse(vault.record_finding(42))
        self.assertFalse(vault.record_finding("string"))
        self.assertFalse(vault.record_finding([1, 2, 3]))
        self.assertFalse(vault.record_finding(None))
        self.assertFalse(vault.record_finding(True))

        # Total findings should remain 0
        self.assertEqual(vault._total_findings, 0)

    # ------------------------------------------------------------------ #
    # 8. Finding with balance
    # ------------------------------------------------------------------ #
    def test_finding_with_balance(self):
        """Findings with balance > 0 appear in with_balance count."""
        vault.init_vault()
        vault.start_session("balance_test")

        vault.record_finding({"address": "a1", "chain": "btc", "balance": 0})
        vault.record_finding({"address": "a2", "chain": "btc", "balance": 1.5})
        vault.record_finding({"address": "a3", "chain": "eth", "balance": 0.001})
        vault.record_finding({"address": "a4", "chain": "btc", "balance": 0})

        summary = vault.get_summary()
        self.assertEqual(summary["total"], 4)
        self.assertEqual(summary["with_balance"], 2)

    # ------------------------------------------------------------------ #
    # 9. Summary by chain
    # ------------------------------------------------------------------ #
    def test_summary_by_chain(self):
        """Findings on different chains show correct by_chain counts."""
        vault.init_vault()
        vault.start_session("chains")

        chains = ["btc", "btc", "eth", "bsc", "polygon", "eth", "btc"]
        for i, chain in enumerate(chains):
            vault.record_finding({"address": f"addr_{i}", "chain": chain})

        summary = vault.get_summary()
        self.assertEqual(summary["by_chain"]["btc"], 3)
        self.assertEqual(summary["by_chain"]["eth"], 2)
        self.assertEqual(summary["by_chain"]["bsc"], 1)
        self.assertEqual(summary["by_chain"]["polygon"], 1)
        self.assertEqual(summary["total"], 7)

    # ------------------------------------------------------------------ #
    # 10. Session lifecycle
    # ------------------------------------------------------------------ #
    def test_session_lifecycle(self):
        """start_session -> record findings -> shutdown creates meta file."""
        vault.init_vault()
        session_id = vault.start_session("lifecycle")

        for i in range(5):
            vault.record_finding({"address": f"lc_{i}", "chain": "btc"})

        vault.shutdown()

        meta_path = vault.SESSIONS_DIR / f"{session_id}_meta.json"
        self.assertTrue(meta_path.exists(), f"Meta file not found: {meta_path}")

        with open(meta_path) as f:
            meta = json.load(f)

        self.assertEqual(meta["session_id"], session_id)
        self.assertEqual(meta["findings"], 5)
        self.assertIn("started", meta)
        self.assertIn("ended", meta)
        self.assertIn("duration", meta)
        self.assertGreater(meta["duration"], 0)

    # ------------------------------------------------------------------ #
    # 11. Multiple sessions
    # ------------------------------------------------------------------ #
    def test_multiple_sessions(self):
        """Starting 3 sessions sequentially yields session_count = 3."""
        vault.init_vault()

        ids = []
        for name in ("session_a", "session_b", "session_c"):
            sid = vault.start_session(name)
            ids.append(sid)
            vault.record_finding({"address": f"addr_{name}", "chain": "btc"})

        self.assertEqual(vault._session_count, 3)
        # Each session_id should be unique
        self.assertEqual(len(set(ids)), 3)

        summary = vault.get_summary()
        self.assertEqual(summary["sessions"], 3)

    # ------------------------------------------------------------------ #
    # 12. Auto summary at 100
    # ------------------------------------------------------------------ #
    def test_auto_summary_at_100(self):
        """Recording 100+ findings triggers automatic summary file creation."""
        vault.init_vault()
        vault.start_session("auto_summary")

        # Before: no summary files
        summaries_before = list(vault.SUMMARIES_DIR.glob("summary_*.json"))
        self.assertEqual(len(summaries_before), 0)

        for i in range(101):
            vault.record_finding({"address": f"s_{i}", "chain": "btc"})

        summaries_after = list(vault.SUMMARIES_DIR.glob("summary_*.json"))
        self.assertGreaterEqual(len(summaries_after), 1)

        # Verify summary content
        with open(summaries_after[0]) as f:
            summary_data = json.load(f)
        self.assertIn("total", summary_data)
        self.assertIn("generated_at", summary_data)

    # ------------------------------------------------------------------ #
    # 13. get_findings limit
    # ------------------------------------------------------------------ #
    def test_get_findings_limit(self):
        """get_findings with limit returns only that many (most recent)."""
        vault.init_vault()
        vault.start_session("limit_test")

        for i in range(20):
            vault.record_finding({"address": f"limit_{i}", "chain": "btc", "index": i})

        findings = vault.get_findings(limit=5)
        self.assertEqual(len(findings), 5)

        # The returned findings should be the last 5 (most recent)
        indices = [f.get("index") for f in findings]
        expected = list(range(15, 20))
        self.assertEqual(indices, expected)

    # ------------------------------------------------------------------ #
    # 14. get_findings default limit
    # ------------------------------------------------------------------ #
    def test_get_findings_default_limit(self):
        """Default limit of get_findings is 100."""
        vault.init_vault()
        vault.start_session("default_limit")

        for i in range(150):
            vault.record_finding({"address": f"dl_{i}", "chain": "btc"})

        findings = vault.get_findings()
        self.assertEqual(len(findings), 100)

    # ------------------------------------------------------------------ #
    # 15. Record finding no session
    # ------------------------------------------------------------------ #
    def test_record_finding_no_session(self):
        """Record finding without start_session uses 'unknown' session."""
        vault.init_vault()

        result = vault.record_finding({"address": "orphan", "chain": "btc"})
        self.assertTrue(result)

        findings = vault.get_findings()
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["session"], "unknown")

    # ------------------------------------------------------------------ #
    # 16. Shutdown writes meta
    # ------------------------------------------------------------------ #
    def test_shutdown_writes_meta(self):
        """Shutdown creates session meta JSON with ended and duration fields."""
        vault.init_vault()
        session_id = vault.start_session("shutdown_meta")
        time.sleep(0.05)  # Ensure measurable duration
        vault.record_finding({"address": "meta_test", "chain": "btc"})
        vault.shutdown()

        meta_path = vault.SESSIONS_DIR / f"{session_id}_meta.json"
        self.assertTrue(meta_path.exists())

        with open(meta_path) as f:
            meta = json.load(f)

        self.assertIn("ended", meta)
        self.assertIn("duration", meta)
        self.assertIsInstance(meta["ended"], float)
        self.assertIsInstance(meta["duration"], float)
        self.assertGreater(meta["ended"], meta["started"])
        self.assertGreater(meta["duration"], 0)

    # ------------------------------------------------------------------ #
    # 17. Vault size in summary
    # ------------------------------------------------------------------ #
    def test_vault_size_in_summary(self):
        """Summary includes non-zero vault_size after writes."""
        vault.init_vault()
        vault.start_session("size_check")

        # Before any writes, vault_live.jsonl may not exist
        summary_before = vault.get_summary()
        self.assertEqual(summary_before["vault_size"], 0)

        for i in range(10):
            vault.record_finding(
                {"address": f"size_{i}", "chain": "btc", "data": "x" * 100}
            )

        summary_after = vault.get_summary()
        self.assertGreater(summary_after["vault_size"], 0)
        self.assertGreater(
            summary_after["vault_size"], 500
        )  # 10 entries with padding should be > 500 bytes

    # ------------------------------------------------------------------ #
    # 18. Concurrent session start
    # ------------------------------------------------------------------ #
    def test_concurrent_session_start(self):
        """5 threads calling start_session simultaneously all succeed."""
        vault.init_vault()

        session_ids = []
        lock = threading.Lock()
        barrier = threading.Barrier(5)

        def start(name):
            try:
                barrier.wait(timeout=5)
            except threading.BrokenBarrierError:
                pass
            sid = vault.start_session(name)
            with lock:
                session_ids.append(sid)

        threads = [
            threading.Thread(target=start, args=(f"concurrent_{i}",)) for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        self.assertEqual(len(session_ids), 5)
        self.assertEqual(vault._session_count, 5)
        # All session IDs should be strings
        for sid in session_ids:
            self.assertIsInstance(sid, str)

    # ------------------------------------------------------------------ #
    # 19. Export CSV with custom path
    # ------------------------------------------------------------------ #
    def test_export_csv_path_custom(self):
        """export_csv with a custom path writes to that location."""
        vault.init_vault()
        vault.start_session("custom_csv")

        for i in range(3):
            vault.record_finding({"address": f"cust_{i}", "chain": "btc", "balance": 0})

        custom_path = os.path.join(self._tmpdir, "my_custom_export.csv")
        output = vault.export_csv(output_path=custom_path)

        self.assertEqual(output, custom_path)
        self.assertTrue(os.path.exists(custom_path))

        with open(custom_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 3)
        # Default vault_export.csv should NOT exist
        default_path = vault.FINDINGS_DIR / "vault_export.csv"
        self.assertFalse(default_path.exists())

    # ------------------------------------------------------------------ #
    # 20. Atomic write in export_json
    # ------------------------------------------------------------------ #
    def test_atomic_write_export_json(self):
        """export_json uses tmp + os.replace for atomic writes; no .tmp leftover."""
        vault.init_vault()
        vault.start_session("atomic_json")

        for i in range(5):
            vault.record_finding({"address": f"atomic_{i}", "chain": "btc"})

        custom_path = os.path.join(self._tmpdir, "atomic_export.json")
        output = vault.export_json(output_path=custom_path)

        # The final file must exist
        self.assertTrue(os.path.exists(output))
        self.assertEqual(output, custom_path)

        # The .tmp file should NOT remain after atomic replace
        tmp_path = custom_path + ".tmp"
        self.assertFalse(os.path.exists(tmp_path))

        # Verify the JSON content is valid
        with open(output, "r") as f:
            data = json.load(f)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 5)


if __name__ == "__main__":
    unittest.main()
