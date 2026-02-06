"""Tests for puzzle solvers."""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestNumberSolver(unittest.TestCase):

    def _solve(self, sequence):
        from solvers.number_solver import NumberSolver

        results = []

        def cb(data):
            if data.get("solution"):
                results.extend(data["solution"])

        solver = NumberSolver(sequence, callback=cb)
        solver.running = True
        import time

        solver.start_time = time.time()
        solver.solve()
        return results

    def test_geometric(self):
        results = self._solve([2, 4, 8, 16])
        predictions = [r["prediction"] for r in results]
        self.assertIn(32, predictions)

    def test_fibonacci(self):
        results = self._solve([1, 1, 2, 3, 5])
        predictions = [r["prediction"] for r in results]
        self.assertIn(8, predictions)

    def test_squares(self):
        results = self._solve([1, 4, 9, 16])
        predictions = [r["prediction"] for r in results]
        self.assertIn(25, predictions)

    def test_arithmetic(self):
        results = self._solve([2, 4, 6, 8])
        predictions = [r["prediction"] for r in results]
        self.assertIn(10, predictions)


class TestNameSolver(unittest.TestCase):

    def test_returns_all_fields(self):
        from solvers.name_solver import NameSolver

        result = {}

        def cb(data):
            if data.get("solution"):
                result.update(data["solution"])

        solver = NameSolver(
            "DAVE", birth_year=1990, birth_month=1, birth_day=15, callback=cb
        )
        solver.running = True
        import time

        solver.start_time = time.time()
        solver.solve()
        self.assertIn("expression", result)
        self.assertIn("soul_urge", result)
        self.assertIn("personality", result)
        self.assertIn("life_path", result)
        self.assertIn("fc60_token", result)


class TestDateSolver(unittest.TestCase):

    def test_returns_fc60_output(self):
        from solvers.date_solver import DateSolver

        result = {}

        def cb(data):
            if data.get("solution"):
                result.update(data["solution"])

        solver = DateSolver(["2026-02-06"], callback=cb)
        solver.running = True
        import time

        solver.start_time = time.time()
        solver.solve()
        self.assertIn("analyses", result)
        self.assertTrue(len(result["analyses"]) > 0)
        self.assertIn("FC60:", result["analyses"][0])


if __name__ == "__main__":
    unittest.main()
