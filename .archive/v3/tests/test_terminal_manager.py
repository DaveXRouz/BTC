"""Tests for engines.terminal_manager module."""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engines import terminal_manager


class TestTerminalManager(unittest.TestCase):

    def setUp(self):
        terminal_manager.reset()

    def tearDown(self):
        terminal_manager.reset()

    def test_create_terminal(self):
        """create_terminal returns a terminal_id string."""
        tid = terminal_manager.create_terminal({"mode": "random_key"})
        self.assertIsInstance(tid, str)
        self.assertIn("T", tid)

    def test_max_terminals(self):
        """Cannot create more than MAX_TERMINALS."""
        for i in range(terminal_manager.MAX_TERMINALS):
            tid = terminal_manager.create_terminal()
            self.assertIsNotNone(tid)

        # 11th should fail
        tid = terminal_manager.create_terminal()
        self.assertIsNone(tid)

    def test_start_stop(self):
        """Start and stop a terminal."""
        tid = terminal_manager.create_terminal({"mode": "random_key"})
        self.assertTrue(terminal_manager.start_terminal(tid))
        time.sleep(0.5)
        self.assertEqual(terminal_manager.get_active_count(), 1)

        self.assertTrue(terminal_manager.stop_terminal(tid))
        self.assertEqual(terminal_manager.get_active_count(), 0)

    def test_remove_terminal(self):
        """Can remove a stopped terminal."""
        tid = terminal_manager.create_terminal()
        self.assertTrue(terminal_manager.remove_terminal(tid))
        self.assertEqual(len(terminal_manager.list_terminals()), 0)

    def test_remove_running_fails(self):
        """Cannot remove a running terminal."""
        tid = terminal_manager.create_terminal({"mode": "random_key"})
        terminal_manager.start_terminal(tid)
        time.sleep(0.3)
        self.assertFalse(terminal_manager.remove_terminal(tid))
        terminal_manager.stop_terminal(tid)

    def test_get_stats(self):
        """get_terminal_stats returns dict with status."""
        tid = terminal_manager.create_terminal({"mode": "random_key"})
        terminal_manager.start_terminal(tid)
        time.sleep(0.5)
        stats = terminal_manager.get_terminal_stats(tid)
        self.assertIn("status", stats)
        self.assertIn("keys_tested", stats)
        terminal_manager.stop_terminal(tid)

    def test_get_all_stats(self):
        """get_all_stats returns dict for all terminals."""
        t1 = terminal_manager.create_terminal({"mode": "random_key"})
        t2 = terminal_manager.create_terminal({"mode": "seed_phrase"})
        result = terminal_manager.get_all_stats()
        self.assertIn(t1, result)
        self.assertIn(t2, result)

    def test_list_terminals(self):
        """list_terminals returns list with id and status."""
        terminal_manager.create_terminal()
        terminal_manager.create_terminal()
        terminals = terminal_manager.list_terminals()
        self.assertEqual(len(terminals), 2)
        self.assertIn("id", terminals[0])
        self.assertIn("status", terminals[0])

    def test_start_all_stop_all(self):
        """start_all and stop_all work correctly."""
        for _ in range(3):
            terminal_manager.create_terminal({"mode": "random_key"})

        started = terminal_manager.start_all()
        self.assertEqual(started, 3)
        time.sleep(0.5)
        self.assertEqual(terminal_manager.get_active_count(), 3)

        stopped = terminal_manager.stop_all()
        self.assertEqual(stopped, 3)
        self.assertEqual(terminal_manager.get_active_count(), 0)


if __name__ == "__main__":
    unittest.main()
