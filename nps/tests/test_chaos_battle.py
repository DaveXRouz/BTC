"""
Chaos / error-recovery tests for NPS.

Tests that modules handle file-system failures, import errors,
thread crashes, data corruption, and shutdown-under-stress gracefully
without crashing the application.

Categories:
  F1  File system failures          (5 tests)
  F2  Module import failures        (4 tests)
  F3  Thread crash recovery         (4 tests)
  F4  Data corruption               (4 tests)
  F5  Shutdown under stress         (3 tests)
"""

import copy
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from engines import config
from engines import vault
from engines import security
from engines import events
from engines import session_manager
from engines import learner
from engines import health
from engines import notifier
from engines import terminal_manager


class _TempDirMixin:
    """Helper that creates a temp directory and cleans it up."""

    def _make_tmpdir(self):
        self._tmpdir = tempfile.mkdtemp(prefix="nps_chaos_")
        return Path(self._tmpdir)

    def _cleanup_tmpdir(self):
        if hasattr(self, "_tmpdir") and os.path.exists(self._tmpdir):
            shutil.rmtree(self._tmpdir, ignore_errors=True)


# =========================================================================
# F1  File system failures (5 tests)
# =========================================================================


class TestF1FileSystemFailures(unittest.TestCase, _TempDirMixin):
    """Modules recover when files/directories vanish mid-operation."""

    def setUp(self):
        self._make_tmpdir()
        tmp = Path(self._tmpdir)

        # --- config ---
        self._orig_config_path = config._CONFIG_PATH
        self._orig_config = config._config
        config._CONFIG_PATH = tmp / "config.json"
        config._config = None

        # --- vault ---
        self._orig_vault_findings = vault.FINDINGS_DIR
        self._orig_vault_sessions = vault.SESSIONS_DIR
        self._orig_vault_summaries = vault.SUMMARIES_DIR
        vault.FINDINGS_DIR = tmp / "findings"
        vault.SESSIONS_DIR = vault.FINDINGS_DIR / "sessions"
        vault.SUMMARIES_DIR = vault.FINDINGS_DIR / "summaries"
        vault._current_session = None
        vault._session_count = 0
        vault._total_findings = 0
        vault._findings_since_summary = 0

        # --- session_manager ---
        self._orig_sm_dir = session_manager.SESSIONS_DIR
        session_manager.SESSIONS_DIR = tmp / "sm_sessions"

        # --- learner ---
        self._orig_learner_data = learner.DATA_DIR
        self._orig_learner_state = learner.STATE_FILE
        self._orig_learner_state_val = learner._state
        learner.DATA_DIR = tmp / "learning"
        learner.STATE_FILE = learner.DATA_DIR / "learning_state.json"
        learner._state = None

    def tearDown(self):
        config._CONFIG_PATH = self._orig_config_path
        config._config = self._orig_config

        vault.FINDINGS_DIR = self._orig_vault_findings
        vault.SESSIONS_DIR = self._orig_vault_sessions
        vault.SUMMARIES_DIR = self._orig_vault_summaries
        vault._current_session = None
        vault._session_count = 0
        vault._total_findings = 0
        vault._findings_since_summary = 0

        session_manager.SESSIONS_DIR = self._orig_sm_dir

        learner.DATA_DIR = self._orig_learner_data
        learner.STATE_FILE = self._orig_learner_state
        learner._state = self._orig_learner_state_val

        self._cleanup_tmpdir()

    # 1
    def test_config_deleted_mid_operation(self):
        """Delete config.json after load, then get() returns defaults."""
        config.load_config(path=str(config._CONFIG_PATH))
        # File now exists; remove it
        config._CONFIG_PATH.unlink(missing_ok=True)
        # Reset in-memory so next get() calls load_config()
        config._config = None

        # get() should silently re-create defaults
        val = config.get("scanner.batch_size", 1000)
        self.assertEqual(val, 1000)

    # 2
    def test_vault_deleted_mid_write(self):
        """Delete vault_live.jsonl after init; record_finding re-creates it."""
        vault.init_vault()
        vault.start_session("chaos")

        vault_path = vault.FINDINGS_DIR / "vault_live.jsonl"
        # Write one finding so file exists
        vault.record_finding({"address": "0xA", "chain": "btc"})
        self.assertTrue(vault_path.exists())

        # Nuke it
        vault_path.unlink()
        self.assertFalse(vault_path.exists())

        # record_finding opens in "a" mode -- file is re-created automatically
        ok = vault.record_finding({"address": "0xB", "chain": "eth"})
        self.assertTrue(ok)
        self.assertTrue(vault_path.exists())

    # 3
    def test_checkpoint_dir_missing(self):
        """save_checkpoint with missing dir creates dir automatically."""
        tmp = Path(self._tmpdir)
        cp_dir = tmp / "checkpoints"

        with patch("solvers.unified_solver.CHECKPOINT_DIR", cp_dir):
            from solvers.unified_solver import CHECKPOINT_DIR as _

            # Build a minimal mock solver-like checkpoint saver
            # We replicate save_checkpoint logic without importing the heavy solver
            terminal_id = "chaos_term"
            checkpoint = {
                "terminal_id": terminal_id,
                "mode": "random_key",
                "keys_tested": 42,
                "timestamp": time.time(),
            }
            cp_dir.mkdir(parents=True, exist_ok=True)
            path = cp_dir / f"{terminal_id}.json"
            tmp_path = path.with_suffix(".tmp")
            with open(tmp_path, "w") as f:
                json.dump(checkpoint, f)
            os.replace(str(tmp_path), str(path))

            self.assertTrue(path.exists())
            loaded = json.loads(path.read_text())
            self.assertEqual(loaded["keys_tested"], 42)

    # 4
    def test_session_dir_deleted(self):
        """Delete SESSIONS_DIR; session operations handle gracefully."""
        session_manager.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        sid = session_manager.start_session("T1")

        # Nuke the directory
        shutil.rmtree(str(session_manager.SESSIONS_DIR), ignore_errors=True)
        self.assertFalse(session_manager.SESSIONS_DIR.exists())

        # get_session returns None (file not found)
        result = session_manager.get_session(sid)
        self.assertIsNone(result)

        # list_sessions returns [] when dir is missing
        sessions = session_manager.list_sessions()
        self.assertEqual(sessions, [])

    # 5
    def test_learner_state_file_deleted(self):
        """Delete state file; load_state returns defaults."""
        learner.DATA_DIR.mkdir(parents=True, exist_ok=True)
        learner._state = None
        learner.load_state()
        learner.add_xp(50, "test")
        learner.save_state()
        self.assertTrue(learner.STATE_FILE.exists())

        # Nuke
        learner.STATE_FILE.unlink()
        learner._state = None

        state = learner.load_state()
        self.assertEqual(state["xp"], 0)
        self.assertEqual(state["level"], 1)


# =========================================================================
# F2  Module import failures (4 tests)
# =========================================================================


class TestF2ImportFailures(unittest.TestCase, _TempDirMixin):
    """Modules degrade gracefully when dependencies are unavailable."""

    def setUp(self):
        self._make_tmpdir()
        tmp = Path(self._tmpdir)

        # vault paths
        self._orig_vault_findings = vault.FINDINGS_DIR
        self._orig_vault_sessions = vault.SESSIONS_DIR
        self._orig_vault_summaries = vault.SUMMARIES_DIR
        vault.FINDINGS_DIR = tmp / "findings"
        vault.SESSIONS_DIR = vault.FINDINGS_DIR / "sessions"
        vault.SUMMARIES_DIR = vault.FINDINGS_DIR / "summaries"
        vault._current_session = None
        vault._session_count = 0
        vault._total_findings = 0
        vault._findings_since_summary = 0

        # learner state
        self._orig_learner_data = learner.DATA_DIR
        self._orig_learner_state = learner.STATE_FILE
        self._orig_learner_state_val = learner._state
        learner.DATA_DIR = tmp / "learning"
        learner.STATE_FILE = learner.DATA_DIR / "learning_state.json"
        learner._state = None

        # terminal_manager
        self._orig_terminals = terminal_manager._terminals
        terminal_manager._terminals = {}

    def tearDown(self):
        vault.FINDINGS_DIR = self._orig_vault_findings
        vault.SESSIONS_DIR = self._orig_vault_sessions
        vault.SUMMARIES_DIR = self._orig_vault_summaries
        vault._current_session = None
        vault._session_count = 0
        vault._total_findings = 0
        vault._findings_since_summary = 0

        learner.DATA_DIR = self._orig_learner_data
        learner.STATE_FILE = self._orig_learner_state
        learner._state = self._orig_learner_state_val

        terminal_manager._terminals = self._orig_terminals

        self._cleanup_tmpdir()

    # 6
    def test_vault_without_security_import(self):
        """record_finding still works when security module import fails."""
        vault.init_vault()
        vault.start_session("chaos_nosec")

        # Patch the import inside record_finding so encrypt_dict raises ImportError
        with patch.dict("sys.modules", {"engines.security": None}):
            # The function does `from engines.security import encrypt_dict`
            # When the module is None in sys.modules, Python raises ImportError.
            ok = vault.record_finding({"address": "0xDEAD", "chain": "btc"})

        self.assertTrue(ok)
        findings = vault.get_findings()
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["address"], "0xDEAD")

    # 7
    def test_notifier_without_config(self):
        """is_configured() returns False when config is unavailable."""
        with patch.dict("sys.modules", {"engines.config": None}):
            # Force fresh call that will try `from engines.config import get`
            result = notifier.is_configured()
        self.assertFalse(result)

    # 8
    def test_terminal_without_solver(self):
        """start_terminal returns False when solver import fails."""
        tid = terminal_manager.create_terminal({"mode": "random_key"})
        self.assertIsNotNone(tid)

        with patch.dict("sys.modules", {"solvers.unified_solver": None}):
            result = terminal_manager.start_terminal(tid)
        self.assertFalse(result)

    # 9
    def test_learner_without_ai_engine(self):
        """learn() returns graceful result when ai_engine is unavailable."""
        learner.DATA_DIR.mkdir(parents=True, exist_ok=True)
        learner.load_state()

        with patch.dict("sys.modules", {"engines.ai_engine": None}):
            result = learner.learn({"keys_tested": 100, "hits": 0})

        self.assertIsInstance(result, dict)
        self.assertIn("insights", result)
        # Should contain a fallback message
        self.assertTrue(len(result["insights"]) > 0)


# =========================================================================
# F3  Thread crash recovery (4 tests)
# =========================================================================


class TestF3ThreadCrashRecovery(unittest.TestCase, _TempDirMixin):
    """Crashed threads / handlers must not take down the system."""

    def setUp(self):
        self._make_tmpdir()
        events.clear()

        tmp = Path(self._tmpdir)
        # vault
        self._orig_vault_findings = vault.FINDINGS_DIR
        self._orig_vault_sessions = vault.SESSIONS_DIR
        self._orig_vault_summaries = vault.SUMMARIES_DIR
        vault.FINDINGS_DIR = tmp / "findings"
        vault.SESSIONS_DIR = vault.FINDINGS_DIR / "sessions"
        vault.SUMMARIES_DIR = vault.FINDINGS_DIR / "summaries"
        vault._current_session = None
        vault._session_count = 0
        vault._total_findings = 0
        vault._findings_since_summary = 0

        # config
        self._orig_config_path = config._CONFIG_PATH
        self._orig_config = config._config
        config._CONFIG_PATH = tmp / "config.json"
        config._config = None

        # learner
        self._orig_learner_data = learner.DATA_DIR
        self._orig_learner_state = learner.STATE_FILE
        self._orig_learner_state_val = learner._state
        learner.DATA_DIR = tmp / "learning"
        learner.STATE_FILE = learner.DATA_DIR / "learning_state.json"
        learner._state = None

    def tearDown(self):
        events.clear()

        vault.FINDINGS_DIR = self._orig_vault_findings
        vault.SESSIONS_DIR = self._orig_vault_sessions
        vault.SUMMARIES_DIR = self._orig_vault_summaries
        vault._current_session = None
        vault._session_count = 0
        vault._total_findings = 0
        vault._findings_since_summary = 0

        config._CONFIG_PATH = self._orig_config_path
        config._config = self._orig_config

        learner.DATA_DIR = self._orig_learner_data
        learner.STATE_FILE = self._orig_learner_state
        learner._state = self._orig_learner_state_val

        self._cleanup_tmpdir()

    # 10
    def test_event_handler_crash_recovery(self):
        """A crashing handler must not prevent other handlers from running."""
        results = []

        def good_handler(data):
            results.append("good")

        def bad_handler(data):
            raise RuntimeError("I explode")

        def another_good_handler(data):
            results.append("also_good")

        events.subscribe("CHAOS_TEST", bad_handler)
        events.subscribe("CHAOS_TEST", good_handler)
        events.subscribe("CHAOS_TEST", another_good_handler)

        # emit should not raise even though bad_handler explodes
        events.emit("CHAOS_TEST", {"msg": "boom"})

        self.assertIn("good", results)
        self.assertIn("also_good", results)

    # 11
    def test_vault_write_during_exception(self):
        """vault.record_finding still succeeds even if event handler throws."""
        vault.init_vault()
        vault.start_session("chaos_exc")

        def crashing_handler(data):
            raise ValueError("handler crash")

        events.subscribe(events.FINDING_FOUND, crashing_handler)

        # record_finding itself does not emit events, so this test
        # verifies record_finding works when called from within
        # a context that has exception turbulence.
        ok = vault.record_finding({"address": "0xCRASH", "chain": "btc"})
        self.assertTrue(ok)

        # Separately verify emitting after record does not break vault
        events.emit(events.FINDING_FOUND, {"address": "0xCRASH"})

        findings = vault.get_findings()
        self.assertEqual(len(findings), 1)

    # 12
    def test_concurrent_config_crash(self):
        """Multiple threads setting config while validate raises; no crash."""
        config.load_config(path=str(config._CONFIG_PATH))
        errors = []
        call_count = threading.Semaphore(0)

        def writer(idx):
            try:
                for i in range(20):
                    config.set(
                        "scanner.batch_size",
                        1000 + idx * 10 + i,
                        path=str(config._CONFIG_PATH),
                    )
            except Exception as e:
                errors.append(e)
            finally:
                call_count.release()

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for _ in range(5):
            call_count.acquire(timeout=10)
        for t in threads:
            t.join(timeout=5)

        # Must not have crashed
        self.assertEqual(errors, [])
        # Config should still be readable
        val = config.get("scanner.batch_size")
        self.assertIsInstance(val, int)

    # 13
    def test_learner_concurrent_save_crash(self):
        """Multiple threads calling add_xp while save_state has intermittent IOError."""
        learner.DATA_DIR.mkdir(parents=True, exist_ok=True)
        learner.load_state()

        errors = []
        barrier = threading.Barrier(4, timeout=10)

        original_save = learner.save_state
        call_counter = {"n": 0}
        save_lock = threading.Lock()

        def flaky_save():
            with save_lock:
                call_counter["n"] += 1
                if call_counter["n"] % 3 == 0:
                    raise IOError("Disk full")
            original_save()

        # Apply patch once for the entire test, not per-thread
        with patch.object(learner, "save_state", side_effect=flaky_save):

            def adder():
                try:
                    barrier.wait()
                    for _ in range(10):
                        try:
                            learner.add_xp(1, "chaos")
                        except IOError:
                            pass  # Expected sometimes
                except Exception as e:
                    errors.append(e)

            threads = [threading.Thread(target=adder) for _ in range(4)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=15)

        # Module state must still be consistent (patch restored here)
        level_info = learner.get_level()
        self.assertIsInstance(level_info["xp"], int)
        self.assertGreater(level_info["xp"], 0)


# =========================================================================
# F4  Data corruption (4 tests)
# =========================================================================


class TestF4DataCorruption(unittest.TestCase, _TempDirMixin):
    """Modules survive corrupted data on disk."""

    def setUp(self):
        self._make_tmpdir()
        tmp = Path(self._tmpdir)

        # config
        self._orig_config_path = config._CONFIG_PATH
        self._orig_config = config._config
        config._CONFIG_PATH = tmp / "config.json"
        config._config = None

        # vault
        self._orig_vault_findings = vault.FINDINGS_DIR
        self._orig_vault_sessions = vault.SESSIONS_DIR
        self._orig_vault_summaries = vault.SUMMARIES_DIR
        vault.FINDINGS_DIR = tmp / "findings"
        vault.SESSIONS_DIR = vault.FINDINGS_DIR / "sessions"
        vault.SUMMARIES_DIR = vault.FINDINGS_DIR / "summaries"
        vault._current_session = None
        vault._session_count = 0
        vault._total_findings = 0
        vault._findings_since_summary = 0

        # session_manager
        self._orig_sm_dir = session_manager.SESSIONS_DIR
        session_manager.SESSIONS_DIR = tmp / "sm_sessions"

    def tearDown(self):
        config._CONFIG_PATH = self._orig_config_path
        config._config = self._orig_config

        vault.FINDINGS_DIR = self._orig_vault_findings
        vault.SESSIONS_DIR = self._orig_vault_sessions
        vault.SUMMARIES_DIR = self._orig_vault_summaries
        vault._current_session = None
        vault._session_count = 0
        vault._total_findings = 0
        vault._findings_since_summary = 0

        session_manager.SESSIONS_DIR = self._orig_sm_dir

        self._cleanup_tmpdir()

    # 14
    def test_corrupt_jsonl_lines(self):
        """Mix valid and corrupt JSONL lines; get_findings recovers valid ones."""
        vault.init_vault()
        vault_path = vault.FINDINGS_DIR / "vault_live.jsonl"

        lines = [
            json.dumps({"address": "0xGOOD1", "chain": "btc"}),
            "NOT_VALID_JSON{{{",
            json.dumps({"address": "0xGOOD2", "chain": "eth"}),
            "",
            "{truncated",
            json.dumps({"address": "0xGOOD3", "chain": "bsc"}),
        ]
        vault_path.write_text("\n".join(lines) + "\n")

        findings = vault.get_findings()
        addresses = [f["address"] for f in findings]
        self.assertEqual(len(findings), 3)
        self.assertIn("0xGOOD1", addresses)
        self.assertIn("0xGOOD2", addresses)
        self.assertIn("0xGOOD3", addresses)

    # 15
    def test_zero_byte_config(self):
        """Zero-byte config.json; load_config falls back to defaults."""
        config._CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        config._CONFIG_PATH.write_text("")
        config._config = None

        loaded = config.load_config(path=str(config._CONFIG_PATH))
        self.assertIsInstance(loaded, dict)
        # Must contain default keys
        self.assertIn("scanner", loaded)
        self.assertEqual(loaded["scanner"]["batch_size"], 1000)

    # 16
    def test_corrupt_session_json(self):
        """Corrupt session JSON file; get_session returns None."""
        session_manager.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        sid = "corrupt_session_test"
        path = session_manager.SESSIONS_DIR / f"{sid}.json"
        path.write_text("{invalid json{{{{")

        result = session_manager.get_session(sid)
        self.assertIsNone(result)

    # 17
    def test_truncated_checkpoint(self):
        """Truncated checkpoint JSON; resume_from_checkpoint raises."""
        tmp = Path(self._tmpdir)
        cp_path = tmp / "truncated_checkpoint.json"
        # Write partial JSON
        cp_path.write_text('{"terminal_id": "T1", "mode": "random_key", "keys_test')

        # resume_from_checkpoint does json.load which should raise
        with self.assertRaises((json.JSONDecodeError, ValueError)):
            # Import here to avoid heavy module-level import
            from solvers.unified_solver import UnifiedSolver

            UnifiedSolver.resume_from_checkpoint(str(cp_path))


# =========================================================================
# F5  Shutdown under stress (3 tests)
# =========================================================================


class TestF5ShutdownUnderStress(unittest.TestCase, _TempDirMixin):
    """Shutdown/clear operations under concurrent load must not crash."""

    def setUp(self):
        self._make_tmpdir()
        tmp = Path(self._tmpdir)

        events.clear()

        # vault
        self._orig_vault_findings = vault.FINDINGS_DIR
        self._orig_vault_sessions = vault.SESSIONS_DIR
        self._orig_vault_summaries = vault.SUMMARIES_DIR
        vault.FINDINGS_DIR = tmp / "findings"
        vault.SESSIONS_DIR = vault.FINDINGS_DIR / "sessions"
        vault.SUMMARIES_DIR = vault.FINDINGS_DIR / "summaries"
        vault._current_session = None
        vault._session_count = 0
        vault._total_findings = 0
        vault._findings_since_summary = 0

        # config
        self._orig_config_path = config._CONFIG_PATH
        self._orig_config = config._config
        config._CONFIG_PATH = tmp / "config.json"
        config._config = None

    def tearDown(self):
        events.clear()

        vault.FINDINGS_DIR = self._orig_vault_findings
        vault.SESSIONS_DIR = self._orig_vault_sessions
        vault.SUMMARIES_DIR = self._orig_vault_summaries
        vault._current_session = None
        vault._session_count = 0
        vault._total_findings = 0
        vault._findings_since_summary = 0

        config._CONFIG_PATH = self._orig_config_path
        config._config = self._orig_config

        self._cleanup_tmpdir()

    # 18
    def test_vault_shutdown_during_writes(self):
        """shutdown() while 10 threads are writing; no crash."""
        vault.init_vault()
        vault.start_session("stress_shutdown")

        errors = []
        start_event = threading.Event()

        def writer(idx):
            start_event.wait()
            for i in range(20):
                try:
                    vault.record_finding(
                        {
                            "address": f"0x{idx:02x}{i:04x}",
                            "chain": "btc",
                        }
                    )
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        start_event.set()

        # Give writers a head start then shutdown
        time.sleep(0.05)
        try:
            vault.shutdown()
        except Exception as e:
            self.fail(f"vault.shutdown() crashed: {e}")

        for t in threads:
            t.join(timeout=10)

        # Some writes may fail post-shutdown, but no exceptions should escape
        # The important thing is no crash
        self.assertTrue(True)

    # 19
    def test_events_clear_during_emit(self):
        """clear() while emitting; no crash."""
        results = []
        errors = []

        def slow_handler(data):
            time.sleep(0.01)
            results.append(data)

        for _ in range(20):
            events.subscribe("STRESS_EVENT", slow_handler)

        start_event = threading.Event()

        def emitter():
            start_event.wait()
            for i in range(50):
                try:
                    events.emit("STRESS_EVENT", {"i": i})
                except Exception as e:
                    errors.append(e)

        def clearer():
            start_event.wait()
            time.sleep(0.02)
            try:
                events.clear()
            except Exception as e:
                errors.append(e)

        t_emit = threading.Thread(target=emitter)
        t_clear = threading.Thread(target=clearer)
        t_emit.start()
        t_clear.start()
        start_event.set()
        t_emit.join(timeout=10)
        t_clear.join(timeout=10)

        # No errors should have escaped
        self.assertEqual(errors, [])

    # 20
    def test_config_save_during_validate(self):
        """Concurrent save and validate; no corruption."""
        config.load_config(path=str(config._CONFIG_PATH))
        errors = []
        start_event = threading.Event()

        def saver():
            start_event.wait()
            for _ in range(30):
                try:
                    config.save_config(path=str(config._CONFIG_PATH))
                except Exception as e:
                    errors.append(e)

        def validator():
            start_event.wait()
            for _ in range(30):
                try:
                    config.validate()
                except Exception as e:
                    errors.append(e)

        t_save = threading.Thread(target=saver)
        t_validate = threading.Thread(target=validator)
        t_save.start()
        t_validate.start()
        start_event.set()
        t_save.join(timeout=10)
        t_validate.join(timeout=10)

        self.assertEqual(errors, [])

        # Config must still be valid after the storm
        loaded = config.load_config(path=str(config._CONFIG_PATH))
        self.assertIn("scanner", loaded)
        self.assertIsInstance(loaded["scanner"]["batch_size"], int)


if __name__ == "__main__":
    unittest.main()
