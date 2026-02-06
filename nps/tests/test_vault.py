"""Tests for engines.vault module."""

import json
import os
import shutil
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engines import vault


class TestVault(unittest.TestCase):

    def setUp(self):
        """Use temp directories for vault storage."""
        self._tmpdir = tempfile.mkdtemp()
        self._orig_findings = vault.FINDINGS_DIR
        self._orig_sessions = vault.SESSIONS_DIR
        self._orig_summaries = vault.SUMMARIES_DIR

        vault.FINDINGS_DIR = vault.Path(self._tmpdir) / "findings"
        vault.SESSIONS_DIR = vault.FINDINGS_DIR / "sessions"
        vault.SUMMARIES_DIR = vault.FINDINGS_DIR / "summaries"
        vault._current_session = None
        vault._session_count = 0
        vault._total_findings = 0
        vault._findings_since_summary = 0

    def tearDown(self):
        vault.FINDINGS_DIR = self._orig_findings
        vault.SESSIONS_DIR = self._orig_sessions
        vault.SUMMARIES_DIR = self._orig_summaries
        vault._current_session = None
        vault._session_count = 0
        vault._total_findings = 0
        vault._findings_since_summary = 0
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_init_vault(self):
        """init_vault creates all required directories."""
        vault.init_vault()
        self.assertTrue(vault.FINDINGS_DIR.exists())
        self.assertTrue(vault.SESSIONS_DIR.exists())
        self.assertTrue(vault.SUMMARIES_DIR.exists())

    def test_start_session(self):
        """start_session returns a session_id string."""
        vault.init_vault()
        session_id = vault.start_session("test_scan")
        self.assertIsInstance(session_id, str)
        self.assertTrue(session_id.startswith("test_scan_"))

    def test_record_finding_jsonl(self):
        """record_finding appends to vault_live.jsonl."""
        vault.init_vault()
        vault.start_session("test")
        result = vault.record_finding(
            {
                "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                "chain": "btc",
                "balance": 0,
            }
        )
        self.assertTrue(result)

        jsonl_path = vault.FINDINGS_DIR / "vault_live.jsonl"
        self.assertTrue(jsonl_path.exists())
        with open(jsonl_path) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        entry = json.loads(lines[0])
        self.assertEqual(entry["address"], "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")

    def test_record_finding_adds_metadata(self):
        """record_finding adds timestamp and session."""
        vault.init_vault()
        vault.start_session("meta_test")
        vault.record_finding({"address": "test", "chain": "eth"})
        findings = vault.get_findings()
        self.assertEqual(len(findings), 1)
        self.assertIn("timestamp", findings[0])
        self.assertIn("session", findings[0])

    def test_sensitive_fields_encrypted(self):
        """Sensitive fields are encrypted when password is set."""
        vault.init_vault()
        vault.start_session("enc_test")

        # Set up encryption
        from engines import security

        security.reset()
        orig_salt = security.SALT_FILE
        security.SALT_FILE = vault.Path(self._tmpdir) / ".salt"
        try:
            security.set_master_password("testpass")
            vault.record_finding(
                {
                    "address": "1Test",
                    "private_key": "5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ",
                    "chain": "btc",
                }
            )

            # Read raw JSONL — private_key should be encrypted
            with open(vault.FINDINGS_DIR / "vault_live.jsonl") as f:
                entry = json.loads(f.readline())
            self.assertTrue(entry["private_key"].startswith("ENC:"))
            self.assertEqual(entry["address"], "1Test")
        finally:
            security.reset()
            security.SALT_FILE = orig_salt

    def test_get_findings_with_limit(self):
        """get_findings respects limit parameter."""
        vault.init_vault()
        vault.start_session("limit_test")
        for i in range(10):
            vault.record_finding({"address": f"addr_{i}", "chain": "btc"})
        findings = vault.get_findings(limit=3)
        self.assertEqual(len(findings), 3)

    def test_get_summary(self):
        """get_summary returns correct counts."""
        vault.init_vault()
        vault.start_session("summary_test")
        vault.record_finding({"chain": "btc", "balance": 0})
        vault.record_finding({"chain": "eth", "balance": 1.5})
        vault.record_finding({"chain": "btc", "balance": 0.1})

        summary = vault.get_summary()
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["with_balance"], 2)
        self.assertEqual(summary["by_chain"]["btc"], 2)
        self.assertEqual(summary["by_chain"]["eth"], 1)

    def test_export_csv(self):
        """export_csv creates a valid CSV file."""
        vault.init_vault()
        vault.start_session("csv_test")
        vault.record_finding({"address": "addr1", "chain": "btc", "balance": 0})

        output = vault.export_csv()
        self.assertTrue(os.path.exists(output))
        with open(output) as f:
            content = f.read()
        self.assertIn("address", content)
        self.assertIn("addr1", content)

    def test_export_json(self):
        """export_json creates a valid JSON file."""
        vault.init_vault()
        vault.start_session("json_test")
        vault.record_finding({"address": "addr2", "chain": "eth", "balance": 0})

        output = vault.export_json()
        self.assertTrue(os.path.exists(output))
        with open(output) as f:
            data = json.load(f)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["address"], "addr2")

    def test_concurrent_writes(self):
        """10 threads each writing 10 findings don't corrupt the vault."""
        vault.init_vault()
        vault.start_session("thread_test")

        errors = []

        def writer(thread_id):
            for i in range(10):
                try:
                    vault.record_finding(
                        {
                            "address": f"t{thread_id}_a{i}",
                            "chain": "btc",
                        }
                    )
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=writer, args=(t,)) for t in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)
        findings = vault.get_findings(limit=200)
        self.assertEqual(len(findings), 100)

    def test_summary_at_100_findings(self):
        """A summary file is generated after 100 findings."""
        vault.init_vault()
        vault.start_session("summary_100")

        for i in range(101):
            vault.record_finding({"address": f"a{i}", "chain": "btc"})

        summaries = list(vault.SUMMARIES_DIR.glob("summary_*.json"))
        self.assertGreaterEqual(len(summaries), 1)

    def test_shutdown(self):
        """shutdown creates session metadata and final summary."""
        vault.init_vault()
        session_id = vault.start_session("shutdown_test")
        vault.record_finding({"address": "final", "chain": "btc"})
        vault.shutdown()

        # Session metadata file should exist
        meta_path = vault.SESSIONS_DIR / f"{session_id}_meta.json"
        self.assertTrue(meta_path.exists())
        with open(meta_path) as f:
            meta = json.load(f)
        self.assertEqual(meta["session_id"], session_id)
        self.assertIn("ended", meta)
        self.assertIn("duration", meta)

    def test_invalid_finding_returns_false(self):
        """Passing non-dict to record_finding returns False."""
        vault.init_vault()
        vault.start_session("invalid_test")
        self.assertFalse(vault.record_finding("not a dict"))
        self.assertFalse(vault.record_finding(None))


if __name__ == "__main__":
    unittest.main()
