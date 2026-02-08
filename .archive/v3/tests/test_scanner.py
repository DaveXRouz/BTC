"""Tests for the ScannerSolver multi-chain scanner."""

import time
import unittest


class TestScannerSolver(unittest.TestCase):

    def test_init_random_key(self):
        """ScannerSolver initializes in random_key mode."""
        from solvers.scanner_solver import ScannerSolver

        s = ScannerSolver("random_key")
        self.assertEqual(s.mode, "random_key")
        self.assertEqual(s.get_name(), "Multi-Chain Scanner")

    def test_init_seed_phrase(self):
        """ScannerSolver initializes in seed_phrase mode."""
        from solvers.scanner_solver import ScannerSolver

        s = ScannerSolver("seed_phrase")
        self.assertEqual(s.mode, "seed_phrase")

    def test_init_both(self):
        """ScannerSolver initializes in both mode."""
        from solvers.scanner_solver import ScannerSolver

        s = ScannerSolver("both")
        self.assertEqual(s.mode, "both")

    def test_invalid_mode_raises(self):
        """Invalid mode raises ValueError."""
        from solvers.scanner_solver import ScannerSolver

        with self.assertRaises(ValueError):
            ScannerSolver("invalid_mode")

    def test_start_stop_cleanly(self):
        """Scanner starts and stops cleanly within 2 seconds."""
        from solvers.scanner_solver import ScannerSolver

        results = []
        s = ScannerSolver(
            "random_key",
            callback=lambda d: results.append(d),
            check_balance_online=False,
        )
        s.start()
        time.sleep(1.5)
        s.stop()
        if s._thread:
            s._thread.join(timeout=2)
        self.assertFalse(s.running)

    def test_callback_receives_keys(self):
        """Callback receives data with required keys."""
        from solvers.scanner_solver import ScannerSolver

        results = []
        s = ScannerSolver(
            "random_key",
            callback=lambda d: results.append(d),
            check_balance_online=False,
        )
        s.start()
        time.sleep(1.5)
        s.stop()
        if s._thread:
            s._thread.join(timeout=2)
        # Filter to running status callbacks (brain events don't have speed/live_feed)
        running = [r for r in results if r.get("status") == "running"]
        if running:
            data = running[-1]
            self.assertIn("status", data)
            self.assertIn("speed", data)
            self.assertIn("keys_tested", data)
            self.assertIn("live_feed", data)

    def test_local_check_empty_rich_list(self):
        """Local check with address not in rich list returns False."""
        from solvers.scanner_solver import ScannerSolver

        s = ScannerSolver("random_key", check_balance_online=False)
        self.assertFalse(s._local_check("1NotInRichList"))

    def test_rich_list_loads(self):
        """Rich list is loaded and non-empty."""
        from solvers.scanner_solver import _load_rich_list

        rich = _load_rich_list()
        self.assertGreater(len(rich), 0)

    def test_chains_parameter(self):
        """ScannerSolver accepts chains parameter and uses it."""
        from solvers.scanner_solver import ScannerSolver

        s = ScannerSolver("random_key", chains=["btc"], check_balance_online=False)
        self.assertEqual(s.chains, ["btc"])
        self.assertNotIn("eth", s.chains)

    def test_default_chains_backward_compat(self):
        """Default chains include btc and eth when no chains param given."""
        from solvers.scanner_solver import ScannerSolver

        s = ScannerSolver("random_key", check_balance_online=False)
        self.assertIn("btc", s.chains)
        self.assertIn("eth", s.chains)

    def test_live_feed_entry_structure(self):
        """Feed entries emitted by scanner contain source, addresses, has_balance."""
        from solvers.scanner_solver import ScannerSolver

        results = []
        s = ScannerSolver(
            "random_key",
            callback=lambda d: results.append(d),
            check_balance_online=False,
        )
        # Use a small batch size so the batch completes quickly and emits
        s.batch_size = 50
        s.start()
        time.sleep(6)
        s.stop()
        if s._thread:
            s._thread.join(timeout=2)
        # Find a callback with live_feed data
        feed_data = [r for r in results if r.get("live_feed")]
        self.assertTrue(
            len(feed_data) > 0, "Expected at least one callback with live_feed"
        )
        entry = feed_data[-1]["live_feed"][-1]
        self.assertIn("source", entry)
        self.assertIn("addresses", entry)
        self.assertIn("has_balance", entry)


if __name__ == "__main__":
    unittest.main()
