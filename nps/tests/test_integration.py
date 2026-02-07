"""
Integration tests for NPS — Cross-component interactions.

Tests verify that modules work together correctly: config propagation,
security + vault encryption, events pub/sub with vault/learner,
terminal lifecycle, learner + strategy gating, session tracking,
health monitoring, and full pipeline scenarios.

30 tests across 8 categories (C1-C8).
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
from unittest.mock import MagicMock, patch

# Ensure nps/ is on sys.path so engine imports resolve
sys.path.insert(0, str(Path(__file__).parent.parent))

from engines import config as cfg
from engines import events
from engines import health
from engines import learner
from engines import security
from engines import session_manager
from engines import terminal_manager
from engines import vault


class _TempDirMixin:
    """Mixin that creates a temporary directory and resets all module state."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp(prefix="nps_integ_")
        self._tmppath = Path(self._tmpdir)

        # --- config ---
        self._orig_config_path = cfg._CONFIG_PATH
        cfg._CONFIG_PATH = self._tmppath / "config.json"
        cfg._config = None

        # --- security ---
        self._orig_salt_file = security.SALT_FILE
        self._orig_data_dir_sec = security.DATA_DIR
        security.DATA_DIR = self._tmppath / "security"
        security.SALT_FILE = security.DATA_DIR / ".vault_salt"
        security.reset()

        # --- vault ---
        self._orig_vault_findings = vault.FINDINGS_DIR
        self._orig_vault_sessions = vault.SESSIONS_DIR
        self._orig_vault_summaries = vault.SUMMARIES_DIR
        vault.FINDINGS_DIR = self._tmppath / "findings"
        vault.SESSIONS_DIR = vault.FINDINGS_DIR / "sessions"
        vault.SUMMARIES_DIR = vault.FINDINGS_DIR / "summaries"
        vault._current_session = None
        vault._session_count = 0
        vault._total_findings = 0
        vault._findings_since_summary = 0

        # --- events ---
        events.clear()

        # --- learner ---
        self._orig_learner_data_dir = learner.DATA_DIR
        self._orig_learner_state_file = learner.STATE_FILE
        learner.DATA_DIR = self._tmppath / "learning"
        learner.STATE_FILE = learner.DATA_DIR / "learning_state.json"
        learner._state = None

        # --- session_manager ---
        self._orig_sm_sessions_dir = session_manager.SESSIONS_DIR
        session_manager.SESSIONS_DIR = self._tmppath / "sessions"

        # --- terminal_manager ---
        terminal_manager.reset()

        # --- health ---
        health.reset()

    def tearDown(self):
        # Restore config
        cfg._CONFIG_PATH = self._orig_config_path
        cfg._config = None

        # Restore security
        security.reset()
        security.DATA_DIR = self._orig_data_dir_sec
        security.SALT_FILE = self._orig_salt_file

        # Restore vault
        vault.FINDINGS_DIR = self._orig_vault_findings
        vault.SESSIONS_DIR = self._orig_vault_sessions
        vault.SUMMARIES_DIR = self._orig_vault_summaries
        vault._current_session = None
        vault._session_count = 0
        vault._total_findings = 0
        vault._findings_since_summary = 0

        # Restore events
        events.clear()

        # Restore learner
        learner.DATA_DIR = self._orig_learner_data_dir
        learner.STATE_FILE = self._orig_learner_state_file
        learner._state = None

        # Restore session_manager
        session_manager.SESSIONS_DIR = self._orig_sm_sessions_dir

        # Restore terminal_manager
        terminal_manager.reset()

        # Restore health
        health.reset()

        # Remove temp dir
        shutil.rmtree(self._tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# C1: Config propagation (4 tests)
# ---------------------------------------------------------------------------
class TestC1ConfigPropagation(_TempDirMixin, unittest.TestCase):
    """Config set/get/validate/save/load integration."""

    def test_config_set_readable_by_modules(self):
        """C1.1 - config.set() value is immediately readable via config.get()."""
        cfg.load_config()
        cfg.set("scanner.batch_size", 2500, path=str(cfg._CONFIG_PATH))
        self.assertEqual(cfg.get("scanner.batch_size"), 2500)
        # Also readable via a fresh get() from another hypothetical module
        self.assertEqual(cfg.get("scanner.batch_size"), 2500)

    def test_config_validate_after_set(self):
        """C1.2 - Setting an out-of-range value is corrected by validate()."""
        cfg.load_config()
        # batch_size must be in [100, 100000]; set to 50 (invalid)
        cfg._config["scanner"]["batch_size"] = 50
        warnings = cfg.validate()
        corrected = cfg.get("scanner.batch_size")
        self.assertEqual(corrected, 1000)  # reset to default
        self.assertTrue(any("batch_size" in w for w in warnings))

    def test_config_deep_merge_on_load(self):
        """C1.3 - Loading partial config fills missing keys from DEFAULT_CONFIG."""
        partial = {"telegram": {"bot_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"}}
        with open(cfg._CONFIG_PATH, "w") as f:
            json.dump(partial, f)

        loaded = cfg.load_config()
        # The partial key is preserved
        self.assertEqual(
            loaded["telegram"]["bot_token"], "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        )
        # Missing sections are filled from defaults
        self.assertIn("scanner", loaded)
        self.assertEqual(
            loaded["scanner"]["batch_size"], cfg.DEFAULT_CONFIG["scanner"]["batch_size"]
        )
        self.assertIn("vault", loaded)

    def test_config_save_load_roundtrip(self):
        """C1.4 - Save config, reset in-memory, reload, verify data matches."""
        cfg.load_config()
        cfg.set("scanner.threads", 4, path=str(cfg._CONFIG_PATH))
        cfg.set("telegram.enabled", False, path=str(cfg._CONFIG_PATH))
        saved_snapshot = copy.deepcopy(cfg._config)

        # Reset in-memory state and reload
        cfg._config = None
        reloaded = cfg.load_config()
        self.assertEqual(reloaded["scanner"]["threads"], 4)
        self.assertEqual(reloaded["telegram"]["enabled"], False)
        # Deep comparison of interesting sections
        self.assertEqual(reloaded["scanner"], saved_snapshot["scanner"])
        self.assertEqual(reloaded["telegram"], saved_snapshot["telegram"])


# ---------------------------------------------------------------------------
# C2: Security + Vault (4 tests)
# ---------------------------------------------------------------------------
class TestC2SecurityVault(_TempDirMixin, unittest.TestCase):
    """Security encryption integrates with vault storage."""

    def test_vault_encrypts_sensitive_fields(self):
        """C2.5 - record_finding encrypts private_key in JSONL when password set."""
        security.DATA_DIR.mkdir(parents=True, exist_ok=True)
        security.set_master_password("s3cret!")
        vault.init_vault()
        vault.start_session("enc_test")

        vault.record_finding(
            {
                "address": "1TestAddr",
                "private_key": "5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ",
                "chain": "btc",
            }
        )

        # Read raw JSONL on disk
        with open(vault.FINDINGS_DIR / "vault_live.jsonl") as f:
            raw = json.loads(f.readline())

        self.assertTrue(raw["private_key"].startswith("ENC:"))
        # Non-sensitive fields stay plain
        self.assertEqual(raw["address"], "1TestAddr")
        self.assertEqual(raw["chain"], "btc")

    def test_vault_decrypt_roundtrip(self):
        """C2.6 - Encrypted finding decrypts back to original via get_findings."""
        security.DATA_DIR.mkdir(parents=True, exist_ok=True)
        security.set_master_password("roundtrip_pw")
        vault.init_vault()
        vault.start_session("dec_test")

        original_key = "L1aW4aubDFB7yfxxxxxSomeFakePrivateKey123"
        vault.record_finding(
            {
                "address": "1Roundtrip",
                "private_key": original_key,
                "chain": "eth",
            }
        )

        findings = vault.get_findings(decrypt_keys=True)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["private_key"], original_key)
        self.assertEqual(findings[0]["address"], "1Roundtrip")

    def test_security_reset_blocks_decrypt(self):
        """C2.7 - After security.reset(), decrypting ENC: data raises ValueError."""
        security.DATA_DIR.mkdir(parents=True, exist_ok=True)
        security.set_master_password("temp_pw")
        encrypted = security.encrypt("top_secret_data")
        self.assertTrue(encrypted.startswith("ENC:"))

        security.reset()
        with self.assertRaises(ValueError):
            security.decrypt(encrypted)

    def test_vault_no_password_stores_plain(self):
        """C2.8 - Without password, vault stores PLAIN: prefix for sensitive fields."""
        # security is reset in setUp -- no password set
        vault.init_vault()
        vault.start_session("plain_test")

        vault.record_finding(
            {
                "address": "1Plain",
                "private_key": "KwDiBf89QgGbjEhKnhXJuH7LrciVrZi3qYjgd9M7rFU73sVHnoWn",
                "chain": "btc",
            }
        )

        with open(vault.FINDINGS_DIR / "vault_live.jsonl") as f:
            raw = json.loads(f.readline())

        self.assertTrue(raw["private_key"].startswith("PLAIN:"))
        # The actual value follows the prefix
        self.assertIn(
            "KwDiBf89QgGbjEhKnhXJuH7LrciVrZi3qYjgd9M7rFU73sVHnoWn", raw["private_key"]
        )


# ---------------------------------------------------------------------------
# C3: Vault + Events (4 tests)
# ---------------------------------------------------------------------------
class TestC3VaultEvents(_TempDirMixin, unittest.TestCase):
    """Vault and event bus work together."""

    def test_record_finding_emits_event(self):
        """C3.9 - Verify event subscription/emission pattern with FINDING_FOUND."""
        # vault.record_finding doesn't emit events itself; the solver does.
        # So we test the subscription + manual emit pattern that the solver uses.
        received = []
        events.subscribe(events.FINDING_FOUND, lambda d: received.append(d))

        vault.init_vault()
        vault.start_session("event_test")
        finding = {"address": "1EvtTest", "chain": "btc", "balance": 1.5}
        vault.record_finding(finding)

        # Simulate what the solver does after recording a finding
        events.emit(events.FINDING_FOUND, finding)

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["address"], "1EvtTest")
        self.assertEqual(received[0]["balance"], 1.5)

    def test_event_subscribe_receive(self):
        """C3.10 - Basic subscribe + emit delivers data to callback."""
        received = []
        events.subscribe(events.SCAN_STARTED, lambda d: received.append(d))
        events.emit(events.SCAN_STARTED, {"mode": "both", "chains": ["btc"]})

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["mode"], "both")

    def test_vault_summary_reflects_writes(self):
        """C3.11 - get_summary() total matches number of recorded findings."""
        vault.init_vault()
        vault.start_session("count_test")

        n = 7
        for i in range(n):
            vault.record_finding({"address": f"addr_{i}", "chain": "btc", "balance": 0})

        summary = vault.get_summary()
        self.assertEqual(summary["total"], n)
        self.assertEqual(summary["by_chain"]["btc"], n)
        self.assertEqual(summary["sessions"], 1)

    def test_vault_shutdown_event_safe(self):
        """C3.12 - Shutdown during active event handlers doesn't crash."""
        errors = []

        def slow_handler(data):
            try:
                time.sleep(0.05)
            except Exception as e:
                errors.append(e)

        events.subscribe(events.SHUTDOWN, slow_handler)
        vault.init_vault()
        vault.start_session("safe_shutdown")
        vault.record_finding({"address": "safe", "chain": "btc"})

        # Emit shutdown in a thread while vault shuts down
        t = threading.Thread(target=lambda: events.emit(events.SHUTDOWN, {}))
        t.start()
        vault.shutdown()
        t.join(timeout=2)

        self.assertEqual(len(errors), 0)


# ---------------------------------------------------------------------------
# C4: Terminal + Solver (4 tests, mock UnifiedSolver)
# ---------------------------------------------------------------------------
class TestC4TerminalSolver(_TempDirMixin, unittest.TestCase):
    """Terminal manager with mocked UnifiedSolver."""

    def _make_mock_solver(self):
        solver = MagicMock()
        solver.running = True
        solver._thread = MagicMock()
        solver._thread.join = MagicMock()
        solver.get_stats.return_value = {
            "keys_tested": 5000,
            "speed": 250.0,
            "hits": 0,
        }
        return solver

    @patch("solvers.unified_solver.UnifiedSolver")
    def test_terminal_create_start_stop(self, MockSolver):
        """C4.13 - Full terminal lifecycle: create -> start -> stop."""
        MockSolver.return_value = self._make_mock_solver()

        tid = terminal_manager.create_terminal({"mode": "random_key"})
        self.assertIsNotNone(tid)

        started = terminal_manager.start_terminal(tid)
        self.assertTrue(started)

        terminals = terminal_manager.list_terminals()
        running = [t for t in terminals if t["status"] == "running"]
        self.assertEqual(len(running), 1)

        stopped = terminal_manager.stop_terminal(tid)
        self.assertTrue(stopped)

        terminals = terminal_manager.list_terminals()
        stopped_list = [t for t in terminals if t["status"] == "stopped"]
        self.assertEqual(len(stopped_list), 1)

    @patch("solvers.unified_solver.UnifiedSolver")
    def test_terminal_stats_from_solver(self, MockSolver):
        """C4.14 - get_terminal_stats returns solver stats."""
        mock_solver = self._make_mock_solver()
        MockSolver.return_value = mock_solver

        tid = terminal_manager.create_terminal()
        terminal_manager.start_terminal(tid)

        stats = terminal_manager.get_terminal_stats(tid)
        self.assertEqual(stats["keys_tested"], 5000)
        self.assertEqual(stats["speed"], 250.0)
        self.assertEqual(stats["status"], "running")

    def test_terminal_max_limit(self):
        """C4.15 - Creating more than MAX_TERMINALS returns None."""
        for i in range(terminal_manager.MAX_TERMINALS):
            tid = terminal_manager.create_terminal({"label": f"T{i}"})
            self.assertIsNotNone(tid)

        # Next one should fail
        overflow = terminal_manager.create_terminal({"label": "overflow"})
        self.assertIsNone(overflow)

    @patch("solvers.unified_solver.UnifiedSolver")
    def test_terminal_remove_requires_stop(self, MockSolver):
        """C4.16 - Removing a running terminal returns False."""
        MockSolver.return_value = self._make_mock_solver()

        tid = terminal_manager.create_terminal()
        terminal_manager.start_terminal(tid)

        # Cannot remove while running
        removed = terminal_manager.remove_terminal(tid)
        self.assertFalse(removed)

        # Stop first, then remove
        terminal_manager.stop_terminal(tid)
        removed = terminal_manager.remove_terminal(tid)
        self.assertTrue(removed)
        self.assertEqual(len(terminal_manager.list_terminals()), 0)


# ---------------------------------------------------------------------------
# C5: Learner + Strategy (4 tests)
# ---------------------------------------------------------------------------
class TestC5LearnerStrategy(_TempDirMixin, unittest.TestCase):
    """Learner XP/levels gate strategy engine behaviour."""

    def test_level_gates_strategy(self):
        """C5.17 - At level 1, strategy engine returns 'random' strategy."""
        learner.DATA_DIR.mkdir(parents=True, exist_ok=True)
        learner.load_state()  # fresh state -> level 1
        self.assertEqual(learner.get_level()["level"], 1)

        from logic.strategy_engine import StrategyEngine

        se = StrategyEngine()
        result = se.initialize(mode="both")
        self.assertEqual(result["strategy"], "random")
        self.assertIn("Level 1", result["reasoning"])

    def test_xp_accumulation_levels_up(self):
        """C5.18 - Adding enough XP changes learner level."""
        learner.DATA_DIR.mkdir(parents=True, exist_ok=True)
        learner.load_state()
        self.assertEqual(learner.get_level()["level"], 1)

        # Level 2 requires 100 XP
        learner.add_xp(50, reason="test1")
        self.assertEqual(learner.get_level()["level"], 1)
        learner.add_xp(50, reason="test2")
        self.assertEqual(learner.get_level()["level"], 2)
        self.assertEqual(learner.get_level()["xp"], 100)

    def test_level_up_emits_event(self):
        """C5.19 - Crossing XP threshold emits LEVEL_UP event."""
        learner.DATA_DIR.mkdir(parents=True, exist_ok=True)
        learner.load_state()

        received = []
        events.subscribe(events.LEVEL_UP, lambda d: received.append(d))

        # Go from level 1 to level 2 (100 XP)
        learner.add_xp(150, reason="big_gain")

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["old_level"], 1)
        self.assertEqual(received[0]["new_level"], 2)
        self.assertEqual(received[0]["name"], "Student")

    def test_strategy_finalize_awards_xp(self):
        """C5.20 - strategy.finalize() calls learner.add_xp for session work."""
        learner.DATA_DIR.mkdir(parents=True, exist_ok=True)
        learner.load_state()
        initial_xp = learner.get_level()["xp"]

        from logic.strategy_engine import StrategyEngine

        se = StrategyEngine()
        se.initialize(mode="random_key")

        summary = se.finalize({"keys_tested": 5000, "hits": 1})
        # XP = 5000 // 1000 + 1 * 50 = 5 + 50 = 55
        self.assertEqual(learner.get_level()["xp"], initial_xp + 55)
        self.assertIn("final_stats", summary)
        self.assertEqual(summary["final_stats"]["keys_tested"], 5000)


# ---------------------------------------------------------------------------
# C6: Session + Vault (3 tests)
# ---------------------------------------------------------------------------
class TestC6SessionVault(_TempDirMixin, unittest.TestCase):
    """Session manager and vault track findings together."""

    def test_session_tracks_findings(self):
        """C6.21 - Vault session tracks finding count; shutdown writes metadata."""
        vault.init_vault()
        sid = vault.start_session("tracker")
        vault.record_finding({"address": "a1", "chain": "btc"})
        vault.record_finding({"address": "a2", "chain": "eth"})
        vault.shutdown()

        meta_path = vault.SESSIONS_DIR / f"{sid}_meta.json"
        self.assertTrue(meta_path.exists())
        with open(meta_path) as f:
            meta = json.load(f)
        self.assertEqual(meta["findings"], 2)
        self.assertIn("duration", meta)
        self.assertGreater(meta["duration"], 0)

    def test_session_manager_parallel(self):
        """C6.22 - Multiple session_manager sessions aggregate stats."""
        session_manager.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

        sid1 = session_manager.start_session("T1", {"mode": "random_key"})
        sid2 = session_manager.start_session("T2", {"mode": "seed_phrase"})

        session_manager.end_session(sid1, {"keys_tested": 1000, "hits": 1})
        session_manager.end_session(sid2, {"keys_tested": 2000, "hits": 0})

        stats = session_manager.get_session_stats()
        self.assertEqual(stats["total_sessions"], 2)
        self.assertEqual(stats["total_keys"], 3000)
        self.assertEqual(stats["total_hits"], 1)

    def test_session_metadata_persistence(self):
        """C6.23 - start, end with stats, get_session returns all fields."""
        session_manager.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

        sid = session_manager.start_session("T_meta", {"mode": "both"})
        session_manager.end_session(
            sid,
            {
                "keys_tested": 500,
                "seeds_tested": 100,
                "hits": 2,
            },
        )

        session = session_manager.get_session(sid)
        self.assertIsNotNone(session)
        self.assertEqual(session["session_id"], sid)
        self.assertEqual(session["terminal_id"], "T_meta")
        self.assertIsNotNone(session["ended"])
        self.assertGreater(session["duration"], 0)
        self.assertEqual(session["stats"]["keys_tested"], 500)
        self.assertEqual(session["stats"]["hits"], 2)
        self.assertEqual(session["settings"]["mode"], "both")


# ---------------------------------------------------------------------------
# C7: Health + Events (3 tests)
# ---------------------------------------------------------------------------
class TestC7HealthEvents(_TempDirMixin, unittest.TestCase):
    """Health monitoring integrates with event bus."""

    @patch("engines.health._check_endpoint")
    def test_health_status_change_emits_event(self, mock_check):
        """C7.24 - Health status change emits HEALTH_CHANGED event."""
        received = []
        events.subscribe(events.HEALTH_CHANGED, lambda d: received.append(d))

        # Simulate: first check all healthy, second check blockstream goes down
        call_count = [0]

        def check_side_effect(name, url, timeout=5):
            call_count[0] += 1
            if name == "blockstream" and call_count[0] > len(health.DEFAULT_ENDPOINTS):
                return False  # second round: blockstream is down
            return True

        mock_check.side_effect = check_side_effect

        # Start monitoring with very short interval
        health.start_monitoring(interval=1)
        # Wait enough for two monitoring rounds
        time.sleep(3.5)
        health.stop_monitoring()

        # At least one HEALTH_CHANGED event for blockstream going from True->False
        blockstream_events = [e for e in received if e.get("endpoint") == "blockstream"]
        self.assertGreaterEqual(len(blockstream_events), 1)
        self.assertFalse(blockstream_events[0]["healthy"])

    def test_health_get_status_format(self):
        """C7.25 - get_status returns expected dict format."""
        # Manually inject status entries (as health._monitor_loop would)
        with health._lock:
            health._status["blockstream"] = {
                "healthy": True,
                "last_check": time.time(),
                "url": "https://blockstream.info/api/blocks/tip/height",
            }
            health._status["eth_rpc"] = {
                "healthy": False,
                "last_check": time.time(),
                "url": "https://eth.llamarpc.com",
            }

        status = health.get_status()
        self.assertIn("blockstream", status)
        self.assertIn("eth_rpc", status)
        self.assertTrue(status["blockstream"]["healthy"])
        self.assertFalse(status["eth_rpc"]["healthy"])
        self.assertIn("last_check", status["blockstream"])
        self.assertIn("url", status["blockstream"])

    def test_health_reset_clears(self):
        """C7.26 - reset() clears status dict and stops monitoring."""
        with health._lock:
            health._status["test_ep"] = {"healthy": True, "last_check": 0, "url": "x"}

        health.reset()
        status = health.get_status()
        self.assertEqual(status, {})


# ---------------------------------------------------------------------------
# C8: Full Pipeline (4 tests)
# ---------------------------------------------------------------------------
class TestC8FullPipeline(_TempDirMixin, unittest.TestCase):
    """End-to-end pipeline scenarios."""

    def test_config_to_vault_pipeline(self):
        """C8.27 - Load config, init vault, start session, record, shutdown."""
        # Step 1: Load config
        loaded = cfg.load_config()
        self.assertIsNotNone(loaded)

        # Step 2: Init vault
        vault.init_vault()
        self.assertTrue(vault.FINDINGS_DIR.exists())

        # Step 3: Start session
        sid = vault.start_session("pipeline")
        self.assertIsNotNone(sid)

        # Step 4: Record finding (unencrypted since no password)
        result = vault.record_finding(
            {
                "address": "1PipelineTest",
                "chain": "btc",
                "balance": 0.001,
            }
        )
        self.assertTrue(result)

        # Step 5: Verify finding exists
        findings = vault.get_findings()
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["address"], "1PipelineTest")

        # Step 6: Shutdown
        vault.shutdown()
        meta_path = vault.SESSIONS_DIR / f"{sid}_meta.json"
        self.assertTrue(meta_path.exists())

    def test_multi_component_lifecycle(self):
        """C8.28 - Config + vault + session + events all work together."""
        # Load config
        cfg.load_config()

        # Set up event tracking
        all_events = []
        events.subscribe(
            events.FINDING_FOUND, lambda d: all_events.append(("finding", d))
        )
        events.subscribe(events.LEVEL_UP, lambda d: all_events.append(("levelup", d)))

        # Init vault and learner
        vault.init_vault()
        learner.DATA_DIR.mkdir(parents=True, exist_ok=True)
        learner.load_state()

        # Start vault session
        vault.start_session("multi")

        # Record findings and emit events (as solver would)
        for i in range(3):
            finding = {"address": f"addr_{i}", "chain": "btc", "balance": 0}
            vault.record_finding(finding)
            events.emit(events.FINDING_FOUND, finding)

        # Add XP to trigger level up
        learner.add_xp(150, reason="multi_test")

        # Verify state
        self.assertEqual(len(all_events), 4)  # 3 findings + 1 level_up
        self.assertEqual(vault.get_summary()["total"], 3)
        self.assertEqual(learner.get_level()["level"], 2)

        vault.shutdown()

    def test_shutdown_sequence(self):
        """C8.29 - Stop all components in order without errors."""
        # Initialize everything
        cfg.load_config()
        security.DATA_DIR.mkdir(parents=True, exist_ok=True)
        security.set_master_password("shutdown_test_pw")
        vault.init_vault()
        vault.start_session("shutdown_seq")
        learner.DATA_DIR.mkdir(parents=True, exist_ok=True)
        learner.load_state()
        session_manager.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        sm_sid = session_manager.start_session("T_shutdown")

        # Record some data
        vault.record_finding(
            {
                "address": "1Shutdown",
                "private_key": "L1aW4aubDFB7yfxxxxxShutdownKey",
                "chain": "btc",
            }
        )
        learner.add_xp(10, reason="shutdown_test")

        # Shutdown in order: health -> terminals -> vault -> session
        errors = []
        try:
            health.reset()
        except Exception as e:
            errors.append(("health", e))

        try:
            terminal_manager.reset()
        except Exception as e:
            errors.append(("terminal", e))

        try:
            vault.shutdown()
        except Exception as e:
            errors.append(("vault", e))

        try:
            session_manager.end_session(sm_sid, {"keys_tested": 100})
        except Exception as e:
            errors.append(("session", e))

        try:
            events.emit(events.SHUTDOWN, {})
        except Exception as e:
            errors.append(("events", e))

        self.assertEqual(len(errors), 0, f"Shutdown errors: {errors}")

    def test_fresh_start_no_state(self):
        """C8.30 - All modules start clean with no prior data files."""
        # Verify nothing exists yet in temp dir
        self.assertFalse((self._tmppath / "findings").exists())
        self.assertFalse((self._tmppath / "learning").exists())
        self.assertFalse((self._tmppath / "sessions").exists())

        # Load config (creates file from defaults)
        loaded = cfg.load_config()
        self.assertEqual(
            loaded["scanner"]["batch_size"], cfg.DEFAULT_CONFIG["scanner"]["batch_size"]
        )

        # Learner starts at level 1
        learner.DATA_DIR.mkdir(parents=True, exist_ok=True)
        learner.load_state()
        self.assertEqual(learner.get_level()["level"], 1)
        self.assertEqual(learner.get_level()["xp"], 0)

        # Vault starts empty
        vault.init_vault()
        summary = vault.get_summary()
        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["sessions"], 0)

        # Events are clean
        recent = events.get_recent_events()
        self.assertEqual(len(recent), 0)

        # Health is clean
        self.assertEqual(health.get_status(), {})

        # No terminals
        self.assertEqual(len(terminal_manager.list_terminals()), 0)

        # Session manager has no sessions
        session_manager.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        sessions = session_manager.list_sessions()
        self.assertEqual(len(sessions), 0)


if __name__ == "__main__":
    unittest.main()
