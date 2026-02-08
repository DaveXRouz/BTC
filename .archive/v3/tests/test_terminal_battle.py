"""Battle tests for engines.terminal_manager module.

Stress tests covering concurrency, edge cases, and lifecycle operations.
All tests that trigger start_terminal mock UnifiedSolver to avoid
real solver imports and background threads.
"""

import os
import sys
import threading
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engines import terminal_manager


def _make_mock_solver():
    """Create a mock UnifiedSolver instance with required attributes."""
    solver = MagicMock()
    solver.running = True
    solver._thread = MagicMock()
    solver._thread.join = MagicMock()
    solver.get_stats.return_value = {
        "keys_tested": 42,
        "speed": 10.0,
        "mode": "random_key",
    }
    return solver


class TestTerminalBattle(unittest.TestCase):
    """Battle tests for terminal_manager edge cases and concurrency."""

    def setUp(self):
        terminal_manager.reset()

    def tearDown(self):
        terminal_manager.reset()

    # ------------------------------------------------------------------
    # 1. Max terminals + one more returns None
    # ------------------------------------------------------------------
    def test_max_terminals_plus_one(self):
        """Creating MAX_TERMINALS+1 terminals: last returns None."""
        ids = []
        for i in range(terminal_manager.MAX_TERMINALS):
            tid = terminal_manager.create_terminal({"mode": "random_key"})
            self.assertIsNotNone(tid, f"Terminal {i+1} should succeed")
            ids.append(tid)

        # The 11th must fail
        overflow = terminal_manager.create_terminal({"mode": "random_key"})
        self.assertIsNone(overflow, "Should return None beyond MAX_TERMINALS")

        # Verify exactly MAX_TERMINALS exist
        self.assertEqual(
            len(terminal_manager.list_terminals()), terminal_manager.MAX_TERMINALS
        )

    # ------------------------------------------------------------------
    # 2. Rapid create-stop-remove cycle 20 times
    # ------------------------------------------------------------------
    @patch("engines.terminal_manager.start_terminal")
    def test_rapid_create_remove(self, mock_start):
        """Create, start, stop, remove a terminal 20 times in a row."""
        mock_start.return_value = True

        for i in range(20):
            tid = terminal_manager.create_terminal({"iteration": i})
            self.assertIsNotNone(tid, f"Iteration {i}: create should succeed")

            # Manually set status to stopped so remove works
            with terminal_manager._lock:
                terminal_manager._terminals[tid]["status"] = "stopped"

            removed = terminal_manager.remove_terminal(tid)
            self.assertTrue(removed, f"Iteration {i}: remove should succeed")

        # All removed, nothing left
        self.assertEqual(len(terminal_manager.list_terminals()), 0)

    # ------------------------------------------------------------------
    # 3. Concurrent creation race: 10 threads, no duplicates, max respected
    # ------------------------------------------------------------------
    def test_concurrent_create_race(self):
        """10 threads each creating a terminal simultaneously."""
        results = []
        barrier = threading.Barrier(10)

        def create_one():
            barrier.wait()
            tid = terminal_manager.create_terminal({"mode": "random_key"})
            results.append(tid)

        threads = [threading.Thread(target=create_one) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        # All 10 should succeed (MAX_TERMINALS is 10)
        non_none = [r for r in results if r is not None]
        self.assertEqual(len(non_none), 10)

        # All IDs should be unique
        self.assertEqual(len(set(non_none)), 10, "All terminal IDs must be unique")

        # Verify list matches
        self.assertEqual(len(terminal_manager.list_terminals()), 10)

    # ------------------------------------------------------------------
    # 4. Cannot remove a running terminal
    # ------------------------------------------------------------------
    @patch("solvers.unified_solver.UnifiedSolver", return_value=_make_mock_solver())
    def test_remove_running_terminal_fails(self, MockSolver):
        """remove_terminal returns False when terminal is running."""
        tid = terminal_manager.create_terminal({"mode": "random_key"})
        started = terminal_manager.start_terminal(tid)
        self.assertTrue(started, "start_terminal should succeed with mock")

        result = terminal_manager.remove_terminal(tid)
        self.assertFalse(result, "Should not remove a running terminal")

        # Clean up
        terminal_manager.stop_terminal(tid)

    # ------------------------------------------------------------------
    # 5. stop_terminal on nonexistent ID returns False
    # ------------------------------------------------------------------
    def test_stop_nonexistent(self):
        """stop_terminal with a fake ID returns False."""
        result = terminal_manager.stop_terminal("fake_id_12345")
        self.assertFalse(result)

    # ------------------------------------------------------------------
    # 6. pause_terminal on nonexistent ID returns False
    # ------------------------------------------------------------------
    def test_pause_nonexistent(self):
        """pause_terminal with a fake ID returns False."""
        result = terminal_manager.pause_terminal("fake_id_12345")
        self.assertFalse(result)

    # ------------------------------------------------------------------
    # 7. Settings dict is preserved on the terminal
    # ------------------------------------------------------------------
    def test_create_with_settings(self):
        """Settings dict passed to create_terminal is stored."""
        settings = {
            "mode": "seed_phrase",
            "puzzle_enabled": True,
            "puzzle_number": 130,
            "chains": ["btc", "eth", "bsc"],
        }
        tid = terminal_manager.create_terminal(settings)
        terminals = terminal_manager.list_terminals()
        found = [t for t in terminals if t["id"] == tid]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["settings"], settings)

    # ------------------------------------------------------------------
    # 8. list_terminals returns correct format
    # ------------------------------------------------------------------
    def test_list_terminals_format(self):
        """list_terminals returns dicts with id, status, settings keys."""
        terminal_manager.create_terminal({"mode": "random_key"})
        terminal_manager.create_terminal({"mode": "seed_phrase"})
        terminal_manager.create_terminal()

        listing = terminal_manager.list_terminals()
        self.assertEqual(len(listing), 3)

        for entry in listing:
            self.assertIn("id", entry)
            self.assertIn("status", entry)
            self.assertIn("settings", entry)
            self.assertIsInstance(entry["id"], str)
            self.assertIsInstance(entry["status"], str)
            self.assertIsInstance(entry["settings"], dict)

    # ------------------------------------------------------------------
    # 9. get_active_count with mixed running/stopped
    # ------------------------------------------------------------------
    @patch("solvers.unified_solver.UnifiedSolver")
    def test_get_active_count(self, MockSolverClass):
        """get_active_count returns only running terminal count."""
        MockSolverClass.return_value = _make_mock_solver()

        t1 = terminal_manager.create_terminal({"mode": "random_key"})
        t2 = terminal_manager.create_terminal({"mode": "random_key"})
        t3 = terminal_manager.create_terminal({"mode": "random_key"})

        # Start t1 and t2, leave t3 as created
        terminal_manager.start_terminal(t1)
        terminal_manager.start_terminal(t2)

        self.assertEqual(terminal_manager.get_active_count(), 2)

        # Stop t1
        terminal_manager.stop_terminal(t1)
        self.assertEqual(terminal_manager.get_active_count(), 1)

        # Stop t2
        terminal_manager.stop_terminal(t2)
        self.assertEqual(terminal_manager.get_active_count(), 0)

    # ------------------------------------------------------------------
    # 10. stop_all returns count of actually stopped terminals
    # ------------------------------------------------------------------
    @patch("solvers.unified_solver.UnifiedSolver")
    def test_stop_all_returns_count(self, MockSolverClass):
        """stop_all returns the number of terminals it actually stopped."""
        MockSolverClass.return_value = _make_mock_solver()

        t1 = terminal_manager.create_terminal({"mode": "random_key"})
        t2 = terminal_manager.create_terminal({"mode": "random_key"})
        t3 = terminal_manager.create_terminal({"mode": "random_key"})

        # Start only 2 of 3
        terminal_manager.start_terminal(t1)
        terminal_manager.start_terminal(t2)

        count = terminal_manager.stop_all()
        self.assertEqual(count, 2, "stop_all should report 2 stopped")

    # ------------------------------------------------------------------
    # 11. start_all returns count of actually started terminals
    # ------------------------------------------------------------------
    @patch("solvers.unified_solver.UnifiedSolver")
    def test_start_all_returns_count(self, MockSolverClass):
        """start_all returns the number of terminals it actually started."""
        MockSolverClass.return_value = _make_mock_solver()

        terminal_manager.create_terminal({"mode": "random_key"})
        terminal_manager.create_terminal({"mode": "random_key"})
        terminal_manager.create_terminal({"mode": "random_key"})

        count = terminal_manager.start_all()
        self.assertEqual(count, 3, "start_all should start all 3 created terminals")

        # Calling start_all again should start 0 (all already running)
        count2 = terminal_manager.start_all()
        self.assertEqual(count2, 0, "No additional terminals to start")

        # Clean up
        terminal_manager.stop_all()

    # ------------------------------------------------------------------
    # 12. Two terminals with same settings get unique IDs
    # ------------------------------------------------------------------
    def test_double_create_unique_ids(self):
        """Two terminals created with identical settings have unique IDs."""
        settings = {"mode": "random_key", "chains": ["btc"]}
        t1 = terminal_manager.create_terminal(settings)
        t2 = terminal_manager.create_terminal(settings)

        self.assertIsNotNone(t1)
        self.assertIsNotNone(t2)
        self.assertNotEqual(t1, t2, "Terminal IDs must be unique")

    # ------------------------------------------------------------------
    # 13. get_terminal_stats without a solver returns basic dict
    # ------------------------------------------------------------------
    def test_get_stats_no_solver(self):
        """get_terminal_stats for a terminal with no solver returns basic info."""
        tid = terminal_manager.create_terminal({"mode": "random_key"})
        stats = terminal_manager.get_terminal_stats(tid)

        self.assertIsNotNone(stats)
        self.assertIn("status", stats)
        self.assertEqual(stats["status"], "created")
        self.assertEqual(stats["keys_tested"], 0)
        self.assertEqual(stats["speed"], 0)

    # ------------------------------------------------------------------
    # 14. reset clears all terminals
    # ------------------------------------------------------------------
    @patch("solvers.unified_solver.UnifiedSolver")
    def test_reset_clears_all(self, MockSolverClass):
        """reset() removes all terminals including running ones."""
        mock_solver = _make_mock_solver()
        MockSolverClass.return_value = mock_solver

        t1 = terminal_manager.create_terminal({"mode": "random_key"})
        t2 = terminal_manager.create_terminal({"mode": "random_key"})
        terminal_manager.start_terminal(t1)

        terminal_manager.reset()

        self.assertEqual(len(terminal_manager.list_terminals()), 0)
        self.assertEqual(terminal_manager.get_active_count(), 0)
        self.assertIsNone(terminal_manager.get_terminal_stats(t1))
        self.assertIsNone(terminal_manager.get_terminal_stats(t2))

    # ------------------------------------------------------------------
    # 15. Stop then remove succeeds
    # ------------------------------------------------------------------
    @patch("solvers.unified_solver.UnifiedSolver")
    def test_remove_after_stop(self, MockSolverClass):
        """A terminal can be removed after it is stopped."""
        MockSolverClass.return_value = _make_mock_solver()

        tid = terminal_manager.create_terminal({"mode": "random_key"})
        terminal_manager.start_terminal(tid)

        # Cannot remove while running
        self.assertFalse(terminal_manager.remove_terminal(tid))

        # Stop it
        terminal_manager.stop_terminal(tid)

        # Now removal should succeed
        self.assertTrue(terminal_manager.remove_terminal(tid))
        self.assertEqual(len(terminal_manager.list_terminals()), 0)


if __name__ == "__main__":
    unittest.main()
