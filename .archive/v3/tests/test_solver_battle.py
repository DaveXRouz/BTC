"""
Battle tests for solvers/unified_solver.py — UnifiedSolver.

Exercises start/stop, pause/resume, checkpoints, stats, callbacks,
and edge cases with all heavy engine imports mocked out.
"""

import json
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Path setup — let us import from the app root
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# We need to mock heavy engine modules *before* importing UnifiedSolver
# so that top-level and in-method imports inside solve() don't blow up.
# ---------------------------------------------------------------------------


def _create_mock_bip39():
    m = MagicMock()
    m.generate_random_keys_batch.return_value = [42, 99, 123]
    m.privkey_to_all_addresses.return_value = {"btc": "1FAKE", "eth": "0xFAKE"}
    m.generate_mnemonic.return_value = "abandon " * 11 + "about"
    m.mnemonic_to_seed.return_value = b"\x00" * 64
    m.derive_all_chains.return_value = {
        "btc": [{"address": "1BTC"}],
        "eth": [{"address": "0xETH"}],
    }
    return m


# Save originals so we can restore after import
_MOCKED_MODULES = [
    "engines.bip39",
    "engines.vault",
    "engines.scoring",
    "engines.balance",
    "engines.events",
]
_originals = {k: sys.modules.get(k) for k in _MOCKED_MODULES}

_mock_bip39 = _create_mock_bip39()
_mock_vault_mod = MagicMock()
_mock_vault_mod.start_session = MagicMock()
_mock_vault_mod.shutdown = MagicMock()
_mock_vault_mod.record_finding = MagicMock()

_mock_scoring = MagicMock()
_mock_scoring.hybrid_score.return_value = {"total_score": 0.5}

_mock_balance = MagicMock()
_mock_balance.check_all_balances.return_value = {"has_any_balance": False}

_mock_events_mod = MagicMock()
_mock_events_mod.emit = MagicMock()
_mock_events_mod.CHECKPOINT_SAVED = "CHECKPOINT_SAVED"
_mock_events_mod.FINDING_FOUND = "FINDING_FOUND"

sys.modules["engines.bip39"] = _mock_bip39
sys.modules["engines.vault"] = _mock_vault_mod
sys.modules["engines.scoring"] = _mock_scoring
sys.modules["engines.balance"] = _mock_balance
sys.modules["engines.events"] = _mock_events_mod

from solvers.unified_solver import UnifiedSolver, CHECKPOINT_DIR  # noqa: E402

# Restore original modules now that UnifiedSolver is imported
for _mod_name, _orig in _originals.items():
    if _orig is not None:
        sys.modules[_mod_name] = _orig
    else:
        sys.modules.pop(_mod_name, None)


class TestSolverBattle(unittest.TestCase):
    """Battle tests for UnifiedSolver."""

    def setUp(self):
        """Inject mocks for engine modules used by UnifiedSolver at runtime."""
        self._patches = []
        for mod_name, mock_obj in [
            ("engines.bip39", _create_mock_bip39()),
            ("engines.vault", _mock_vault_mod),
            ("engines.scoring", _mock_scoring),
            ("engines.balance", _mock_balance),
            ("engines.events", _mock_events_mod),
        ]:
            # Only patch if the solve() method will do a runtime import
            pass
        # Reset mock call counts
        _mock_vault_mod.reset_mock()
        _mock_scoring.reset_mock()
        _mock_balance.reset_mock()
        _mock_events_mod.reset_mock()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_solver(self, **kwargs):
        """Create a UnifiedSolver with sane defaults for testing."""
        defaults = dict(
            mode="random_key",
            puzzle_enabled=False,
            puzzle_number=None,
            strategy="hybrid",
            chains=["btc"],
            tokens=["USDT"],
            online_check=False,
            check_every_n=5000,
            use_brain=False,
            terminal_id="test_terminal",
            callback=None,
        )
        defaults.update(kwargs)
        return UnifiedSolver(**defaults)

    def _tmp_checkpoint_dir(self):
        """Create a temporary directory to act as CHECKPOINT_DIR."""
        return Path(tempfile.mkdtemp(prefix="nps_cp_"))

    # ------------------------------------------------------------------
    # 1. test_rapid_start_stop
    # ------------------------------------------------------------------
    def test_rapid_start_stop(self):
        """Start the solver then immediately stop it — should not hang."""
        solver = self._make_solver()
        solver.start()
        # Give the thread a moment to spin up
        time.sleep(0.05)
        solver.stop()
        # Allow thread to terminate
        if solver._thread:
            solver._thread.join(timeout=2)
        self.assertFalse(solver.running)

    # ------------------------------------------------------------------
    # 2. test_pause_resume
    # ------------------------------------------------------------------
    def test_pause_resume(self):
        """Pause blocks scanning; resume un-blocks it."""
        solver = self._make_solver()
        solver.start()
        time.sleep(0.05)

        solver.pause()
        self.assertTrue(solver._paused)
        self.assertFalse(solver._pause_event.is_set())

        solver.resume()
        self.assertFalse(solver._paused)
        self.assertTrue(solver._pause_event.is_set())

        solver.stop()
        if solver._thread:
            solver._thread.join(timeout=2)

    # ------------------------------------------------------------------
    # 3. test_corrupt_checkpoint_load
    # ------------------------------------------------------------------
    def test_corrupt_checkpoint_load(self):
        """Loading a corrupt checkpoint file should raise."""
        tmp = self._tmp_checkpoint_dir()
        corrupt_file = tmp / "corrupt.json"
        corrupt_file.write_text("NOT VALID JSON {{{")

        with self.assertRaises(json.JSONDecodeError):
            UnifiedSolver.resume_from_checkpoint(str(corrupt_file))

    # ------------------------------------------------------------------
    # 4. test_double_start
    # ------------------------------------------------------------------
    def test_double_start(self):
        """Calling start() twice should be a no-op the second time."""
        solver = self._make_solver()
        solver.start()
        first_thread = solver._thread
        time.sleep(0.05)

        solver.start()  # second call
        self.assertIs(
            solver._thread, first_thread, "Second start() should not spawn a new thread"
        )

        solver.stop()
        if solver._thread:
            solver._thread.join(timeout=2)

    # ------------------------------------------------------------------
    # 5. test_double_stop
    # ------------------------------------------------------------------
    def test_double_stop(self):
        """Calling stop() on an already-stopped solver should not crash."""
        tmp = self._tmp_checkpoint_dir()
        with patch.object(
            type(UnifiedSolver),
            "_UnifiedSolver__class_checkpoint_dir",
            tmp,
            create=True,
        ):
            solver = self._make_solver()
            solver.stop()  # first stop (never started)
            solver.stop()  # second stop — should be harmless
            self.assertFalse(solver.running)

    # ------------------------------------------------------------------
    # 6. test_save_checkpoint_creates_file
    # ------------------------------------------------------------------
    def test_save_checkpoint_creates_file(self):
        """save_checkpoint() should write a .json file to CHECKPOINT_DIR."""
        tmp = self._tmp_checkpoint_dir()
        solver = self._make_solver(terminal_id="ckpt_test")
        solver.start_time = time.time()

        import solvers.unified_solver as us_mod

        original_dir = us_mod.CHECKPOINT_DIR
        us_mod.CHECKPOINT_DIR = tmp
        try:
            solver.save_checkpoint()
            expected = tmp / "ckpt_test.json"
            self.assertTrue(
                expected.exists(), f"Checkpoint file should exist at {expected}"
            )
        finally:
            us_mod.CHECKPOINT_DIR = original_dir

    # ------------------------------------------------------------------
    # 7. test_checkpoint_content
    # ------------------------------------------------------------------
    def test_checkpoint_content(self):
        """Checkpoint JSON should contain all expected keys."""
        tmp = self._tmp_checkpoint_dir()
        solver = self._make_solver(terminal_id="content_test")
        solver.start_time = time.time()
        solver._keys_tested = 42
        solver._seeds_tested = 7
        solver._hits = 1

        import solvers.unified_solver as us_mod

        original_dir = us_mod.CHECKPOINT_DIR
        us_mod.CHECKPOINT_DIR = tmp
        try:
            solver.save_checkpoint()
            with open(tmp / "content_test.json") as f:
                data = json.load(f)

            required_keys = [
                "terminal_id",
                "mode",
                "puzzle_enabled",
                "puzzle_number",
                "strategy",
                "chains",
                "tokens",
                "keys_tested",
                "seeds_tested",
                "hits",
                "online_checks",
                "high_score",
                "timestamp",
                "use_brain",
                "online_check",
                "check_every_n",
            ]
            for key in required_keys:
                self.assertIn(key, data, f"Checkpoint missing key: {key}")

            self.assertEqual(data["keys_tested"], 42)
            self.assertEqual(data["seeds_tested"], 7)
            self.assertEqual(data["hits"], 1)
            self.assertEqual(data["terminal_id"], "content_test")
        finally:
            us_mod.CHECKPOINT_DIR = original_dir

    # ------------------------------------------------------------------
    # 8. test_resume_from_checkpoint
    # ------------------------------------------------------------------
    def test_resume_from_checkpoint(self):
        """resume_from_checkpoint should restore stats from a checkpoint file."""
        tmp = self._tmp_checkpoint_dir()
        cp_data = {
            "terminal_id": "resume_test",
            "mode": "seed_phrase",
            "puzzle_enabled": True,
            "puzzle_number": 66,
            "strategy": "sequential",
            "chains": ["btc", "eth"],
            "tokens": ["USDT"],
            "keys_tested": 500_000,
            "seeds_tested": 1_200,
            "hits": 3,
            "online_checks": 100,
            "high_score": 0.87,
            "use_brain": True,
            "online_check": True,
            "check_every_n": 1000,
            "timestamp": time.time(),
        }
        cp_file = tmp / "resume_test.json"
        with open(cp_file, "w") as f:
            json.dump(cp_data, f)

        solver = UnifiedSolver.resume_from_checkpoint(str(cp_file))

        self.assertEqual(solver.terminal_id, "resume_test")
        self.assertEqual(solver.mode, "seed_phrase")
        self.assertTrue(solver.puzzle_enabled)
        self.assertEqual(solver.puzzle_number, 66)
        self.assertEqual(solver._keys_tested, 500_000)
        self.assertEqual(solver._seeds_tested, 1_200)
        self.assertEqual(solver._hits, 3)
        self.assertEqual(solver._online_checks, 100)
        self.assertAlmostEqual(solver._high_score, 0.87)
        self.assertTrue(solver.use_brain)
        self.assertTrue(solver.online_check)

    # ------------------------------------------------------------------
    # 9. test_list_checkpoints_empty
    # ------------------------------------------------------------------
    def test_list_checkpoints_empty(self):
        """list_checkpoints returns empty list when dir does not exist."""
        tmp = Path(tempfile.mkdtemp(prefix="nps_empty_"))
        non_existent = tmp / "no_such_dir"

        import solvers.unified_solver as us_mod

        original_dir = us_mod.CHECKPOINT_DIR
        us_mod.CHECKPOINT_DIR = non_existent
        try:
            result = UnifiedSolver.list_checkpoints()
            self.assertEqual(result, [])
        finally:
            us_mod.CHECKPOINT_DIR = original_dir

    # ------------------------------------------------------------------
    # 10. test_list_checkpoints_with_files
    # ------------------------------------------------------------------
    def test_list_checkpoints_with_files(self):
        """list_checkpoints returns sorted list of .json files."""
        tmp = self._tmp_checkpoint_dir()
        (tmp / "alpha.json").write_text("{}")
        (tmp / "beta.json").write_text("{}")
        (tmp / "gamma.json").write_text("{}")
        (tmp / "not_checkpoint.txt").write_text("ignore me")

        import solvers.unified_solver as us_mod

        original_dir = us_mod.CHECKPOINT_DIR
        us_mod.CHECKPOINT_DIR = tmp
        try:
            result = UnifiedSolver.list_checkpoints()
            names = [p.name for p in result]
            self.assertEqual(len(names), 3)
            self.assertIn("alpha.json", names)
            self.assertIn("beta.json", names)
            self.assertIn("gamma.json", names)
            self.assertNotIn("not_checkpoint.txt", names)
            # Verify sorted
            self.assertEqual(names, sorted(names))
        finally:
            us_mod.CHECKPOINT_DIR = original_dir

    # ------------------------------------------------------------------
    # 11. test_get_stats_format
    # ------------------------------------------------------------------
    def test_get_stats_format(self):
        """get_stats() should return a dict with all documented keys."""
        solver = self._make_solver(terminal_id="stats_test")
        solver.start_time = time.time()

        stats = solver.get_stats()

        expected_keys = {
            "keys_tested",
            "seeds_tested",
            "speed",
            "hits",
            "online_checks",
            "high_score",
            "elapsed",
            "paused",
            "mode",
            "puzzle_enabled",
            "puzzle_number",
            "terminal_id",
            "chains",
        }
        self.assertEqual(set(stats.keys()), expected_keys)
        self.assertIsInstance(stats["speed"], float)
        self.assertIsInstance(stats["elapsed"], float)
        self.assertEqual(stats["terminal_id"], "stats_test")

    # ------------------------------------------------------------------
    # 12. test_callback_receives_data
    # ------------------------------------------------------------------
    def test_callback_receives_data(self):
        """The callback function should be invoked with a dict payload."""
        received = []

        def cb(data):
            received.append(data)

        solver = self._make_solver(callback=cb)
        solver.start()
        # Let the solver run briefly so it emits at least one progress update
        deadline = time.time() + 3
        while time.time() < deadline and not received:
            time.sleep(0.05)

        solver.stop()
        if solver._thread:
            solver._thread.join(timeout=2)

        self.assertTrue(
            len(received) > 0, "Callback should have been called at least once"
        )
        # Each payload should be a dict
        for item in received:
            self.assertIsInstance(item, dict)

    # ------------------------------------------------------------------
    # 13. test_get_name_format
    # ------------------------------------------------------------------
    def test_get_name_format(self):
        """get_name() includes mode and (if enabled) puzzle number."""
        solver_no_puzzle = self._make_solver(mode="seed_phrase", puzzle_enabled=False)
        name = solver_no_puzzle.get_name()
        self.assertIn("seed_phrase", name)
        self.assertIn("Unified", name)
        self.assertNotIn("P", name)

        solver_puzzle = self._make_solver(
            mode="random_key", puzzle_enabled=True, puzzle_number=66
        )
        name_p = solver_puzzle.get_name()
        self.assertIn("random_key", name_p)
        self.assertIn("P66", name_p)

    # ------------------------------------------------------------------
    # 14. test_get_description
    # ------------------------------------------------------------------
    def test_get_description(self):
        """get_description() includes mode string."""
        solver = self._make_solver(mode="both")
        desc = solver.get_description()
        self.assertIn("both", desc)
        self.assertIn("Unified", desc)

        solver_p = self._make_solver(
            mode="random_key", puzzle_enabled=True, puzzle_number=130
        )
        desc_p = solver_p.get_description()
        self.assertIn("random_key", desc_p)
        self.assertIn("130", desc_p)

    # ------------------------------------------------------------------
    # 15. test_solver_modes
    # ------------------------------------------------------------------
    def test_solver_modes(self):
        """Creating a solver with each mode stores the mode correctly."""
        for mode in ("random_key", "seed_phrase", "both"):
            solver = self._make_solver(mode=mode)
            self.assertEqual(solver.mode, mode, f"Mode mismatch for {mode}")
            # Also check stats reflect the mode
            solver.start_time = time.time()
            stats = solver.get_stats()
            self.assertEqual(stats["mode"], mode)

    # ------------------------------------------------------------------
    # 16. test_stop_unpauses_first
    # ------------------------------------------------------------------
    def test_stop_unpauses_first(self):
        """stop() should set _pause_event so a paused thread can exit."""
        solver = self._make_solver()
        solver.start()
        time.sleep(0.05)

        # Pause the solver
        solver.pause()
        self.assertFalse(solver._pause_event.is_set(), "Should be paused/cleared")

        # Now stop — stop() must set _pause_event before joining
        solver.stop()
        self.assertTrue(
            solver._pause_event.is_set(),
            "stop() should set _pause_event so the thread can unblock and exit",
        )

        if solver._thread:
            solver._thread.join(timeout=2)
        self.assertFalse(solver.running)


if __name__ == "__main__":
    unittest.main()
