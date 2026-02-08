"""Tests for engines/errors.py — Error handling utilities."""

import json
import os
import tempfile
import unittest

from engines.errors import Result, safe_callback, safe_file_read


class TestResult(unittest.TestCase):
    def test_ok(self):
        r = Result.ok(42)
        self.assertTrue(r.success)
        self.assertEqual(r.value, 42)
        self.assertIsNone(r.error)

    def test_ok_none(self):
        r = Result.ok()
        self.assertTrue(r.success)
        self.assertIsNone(r.value)

    def test_fail(self):
        r = Result.fail("something broke")
        self.assertFalse(r.success)
        self.assertIsNone(r.value)
        self.assertEqual(r.error, "something broke")

    def test_bool_ok(self):
        self.assertTrue(bool(Result.ok(1)))

    def test_bool_fail(self):
        self.assertFalse(bool(Result.fail("err")))

    def test_repr_ok(self):
        r = Result.ok(42)
        self.assertIn("42", repr(r))

    def test_repr_fail(self):
        r = Result.fail("oops")
        self.assertIn("oops", repr(r))


class TestSafeCallback(unittest.TestCase):
    def test_normal_execution(self):
        @safe_callback()
        def add(a, b):
            return a + b

        self.assertEqual(add(2, 3), 5)

    def test_exception_caught(self):
        @safe_callback()
        def boom():
            raise RuntimeError("test error")

        # Should not raise
        result = boom()
        self.assertIsNone(result)

    def test_status_updater_called(self):
        errors = []

        @safe_callback(status_updater=lambda msg: errors.append(msg))
        def boom():
            raise ValueError("bad value")

        boom()
        self.assertEqual(len(errors), 1)
        self.assertIn("bad value", errors[0])

    def test_preserves_name(self):
        @safe_callback()
        def my_func():
            pass

        self.assertEqual(my_func.__name__, "my_func")


class TestSafeFileRead(unittest.TestCase):
    def test_read_valid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"key": "value"}, f)
            path = f.name
        try:
            r = safe_file_read(path)
            self.assertTrue(r.success)
            self.assertEqual(r.value["key"], "value")
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        r = safe_file_read("/nonexistent/path.json")
        self.assertFalse(r.success)
        self.assertIn("not found", r.error)

    def test_file_not_found_with_default(self):
        r = safe_file_read("/nonexistent/path.json", default={"empty": True})
        self.assertTrue(r.success)
        self.assertEqual(r.value["empty"], True)

    def test_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json {{{")
            path = f.name
        try:
            r = safe_file_read(path)
            self.assertFalse(r.success)
            self.assertIn("Invalid JSON", r.error)
        finally:
            os.unlink(path)

    def test_invalid_json_with_default(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{bad")
            path = f.name
        try:
            r = safe_file_read(path, default=[])
            self.assertTrue(r.success)
            self.assertEqual(r.value, [])
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
