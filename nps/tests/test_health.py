"""Tests for engines.health module."""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engines import health


class TestHealth(unittest.TestCase):

    def setUp(self):
        health.reset()

    def tearDown(self):
        health.reset()

    def test_start_stop(self):
        """start_monitoring and stop_monitoring work cleanly."""
        health.start_monitoring(interval=5)
        self.assertTrue(health._running)
        health.stop_monitoring()
        self.assertFalse(health._running)

    def test_initial_status_empty(self):
        """Status is empty before monitoring starts."""
        status = health.get_status()
        self.assertEqual(status, {})

    def test_is_healthy_unknown(self):
        """is_healthy returns False for unknown endpoint."""
        self.assertFalse(health.is_healthy("nonexistent"))

    def test_status_populated_after_check(self):
        """After monitoring runs briefly, status is populated."""
        health.start_monitoring(interval=2)
        time.sleep(8)  # Wait for at least one check cycle
        health.stop_monitoring()
        status = health.get_status()
        # At least one endpoint should have been checked
        self.assertGreater(len(status), 0)
        for name, info in status.items():
            self.assertIn("healthy", info)
            self.assertIn("last_check", info)


if __name__ == "__main__":
    unittest.main()
