"""Tests for solvers.unified_solver module."""

import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from solvers.unified_solver import UnifiedSolver, CHECKPOINT_DIR


class TestUnifiedSolver(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_cp_dir = UnifiedSolver.__module__
        # Redirect checkpoint dir
        import solvers.unified_solver as mod

        self._orig_dir = mod.CHECKPOINT_DIR
        mod.CHECKPOINT_DIR = mod.Path(self._tmpdir) / "checkpoints"

    def tearDown(self):
        import solvers.unified_solver as mod

        mod.CHECKPOINT_DIR = self._orig_dir
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_init_random_key(self):
        """UnifiedSolver initializes in random_key mode."""
        solver = UnifiedSolver(mode="random_key")
        self.assertEqual(solver.mode, "random_key")
        self.assertFalse(solver.puzzle_enabled)

    def test_init_seed_phrase(self):
        """UnifiedSolver initializes in seed_phrase mode."""
        solver = UnifiedSolver(mode="seed_phrase")
        self.assertEqual(solver.mode, "seed_phrase")

    def test_init_both(self):
        """UnifiedSolver initializes in both mode."""
        solver = UnifiedSolver(mode="both")
        self.assertEqual(solver.mode, "both")

    def test_init_with_puzzle(self):
        """UnifiedSolver with puzzle enabled stores puzzle config."""
        solver = UnifiedSolver(mode="random_key", puzzle_enabled=True, puzzle_number=66)
        self.assertTrue(solver.puzzle_enabled)
        self.assertEqual(solver.puzzle_number, 66)

    def test_init_all_params(self):
        """UnifiedSolver accepts all constructor parameters."""
        solver = UnifiedSolver(
            mode="both",
            puzzle_enabled=True,
            puzzle_number=66,
            strategy="mystic",
            chains=["btc", "eth", "bsc"],
            tokens=["USDT"],
            online_check=True,
            check_every_n=1000,
            use_brain=True,
            terminal_id="test_terminal",
        )
        self.assertEqual(solver.chains, ["btc", "eth", "bsc"])
        self.assertEqual(solver.tokens, ["USDT"])
        self.assertTrue(solver.online_check)
        self.assertEqual(solver.terminal_id, "test_terminal")

    def test_get_name(self):
        """get_name returns descriptive name."""
        solver = UnifiedSolver(mode="random_key")
        self.assertIn("random_key", solver.get_name())

    def test_get_description(self):
        """get_description includes mode info."""
        solver = UnifiedSolver(mode="both", puzzle_enabled=True, puzzle_number=66)
        desc = solver.get_description()
        self.assertIn("both", desc)
        self.assertIn("66", desc)

    def test_stats_initial(self):
        """get_stats returns dict with expected keys."""
        solver = UnifiedSolver(mode="random_key")
        solver.start_time = time.time()
        stats = solver.get_stats()
        self.assertIn("keys_tested", stats)
        self.assertIn("seeds_tested", stats)
        self.assertIn("speed", stats)
        self.assertIn("hits", stats)
        self.assertIn("elapsed", stats)
        self.assertIn("mode", stats)
        self.assertIn("terminal_id", stats)
        self.assertEqual(stats["keys_tested"], 0)

    def test_start_stop_cleanly(self):
        """Solver starts and stops cleanly within 2 seconds."""
        results = []

        def callback(data):
            results.append(data)

        solver = UnifiedSolver(mode="random_key", callback=callback)
        solver.start()
        time.sleep(1)
        self.assertTrue(solver.running)
        solver.stop()
        if solver._thread:
            solver._thread.join(timeout=3)
        self.assertFalse(solver.running)
        # Should have generated some keys
        self.assertGreater(solver._keys_tested, 0)

    def test_pause_resume(self):
        """Pause and resume work correctly."""
        solver = UnifiedSolver(mode="random_key")
        solver.start()
        time.sleep(0.5)

        solver.pause()
        self.assertTrue(solver._paused)
        keys_at_pause = solver._keys_tested
        time.sleep(0.3)
        # Should not have advanced much while paused
        keys_while_paused = solver._keys_tested
        self.assertAlmostEqual(keys_at_pause, keys_while_paused, delta=2000)

        solver.resume()
        self.assertFalse(solver._paused)
        time.sleep(0.5)
        self.assertGreater(solver._keys_tested, keys_at_pause)

        solver.stop()
        if solver._thread:
            solver._thread.join(timeout=3)

    def test_checkpoint_save(self):
        """save_checkpoint creates a JSON file."""
        import solvers.unified_solver as mod

        solver = UnifiedSolver(mode="random_key", terminal_id="test_cp")
        solver.start_time = time.time()
        solver._keys_tested = 500
        solver.save_checkpoint()

        cp_path = mod.CHECKPOINT_DIR / "test_cp.json"
        self.assertTrue(cp_path.exists())
        with open(cp_path) as f:
            data = json.load(f)
        self.assertEqual(data["terminal_id"], "test_cp")
        self.assertEqual(data["keys_tested"], 500)
        self.assertEqual(data["mode"], "random_key")

    def test_checkpoint_resume(self):
        """resume_from_checkpoint restores solver state."""
        import solvers.unified_solver as mod

        # Create a checkpoint
        solver = UnifiedSolver(
            mode="both",
            puzzle_enabled=True,
            puzzle_number=66,
            terminal_id="resume_test",
        )
        solver.start_time = time.time()
        solver._keys_tested = 12345
        solver._seeds_tested = 100
        solver._hits = 2
        solver._high_score = 0.85
        solver.save_checkpoint()

        # Resume from it
        cp_path = mod.CHECKPOINT_DIR / "resume_test.json"
        restored = UnifiedSolver.resume_from_checkpoint(str(cp_path))
        self.assertEqual(restored.mode, "both")
        self.assertTrue(restored.puzzle_enabled)
        self.assertEqual(restored.puzzle_number, 66)
        self.assertEqual(restored._keys_tested, 12345)
        self.assertEqual(restored._seeds_tested, 100)
        self.assertEqual(restored._hits, 2)
        self.assertAlmostEqual(restored._high_score, 0.85)

    def test_list_checkpoints(self):
        """list_checkpoints returns checkpoint paths."""
        import solvers.unified_solver as mod

        mod.CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

        # Create two checkpoints
        for name in ["t1", "t2"]:
            path = mod.CHECKPOINT_DIR / f"{name}.json"
            with open(path, "w") as f:
                json.dump({"terminal_id": name}, f)

        cps = UnifiedSolver.list_checkpoints()
        self.assertEqual(len(cps), 2)

    def test_seed_phrase_mode(self):
        """Seed phrase mode generates seeds."""
        solver = UnifiedSolver(mode="seed_phrase")
        solver.start()
        time.sleep(1)
        solver.stop()
        if solver._thread:
            solver._thread.join(timeout=3)
        self.assertGreater(solver._seeds_tested, 0)

    def test_thread_safety(self):
        """Multiple concurrent get_stats calls don't crash."""
        solver = UnifiedSolver(mode="random_key")
        solver.start()
        time.sleep(0.3)

        errors = []

        def reader():
            for _ in range(50):
                try:
                    solver.get_stats()
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=reader) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        solver.stop()
        if solver._thread:
            solver._thread.join(timeout=3)
        self.assertEqual(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
