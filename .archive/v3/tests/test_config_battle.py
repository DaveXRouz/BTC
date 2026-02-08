"""Battle tests for the config module.

Stress-tests covering corrupt files, concurrency, deep merge edge cases,
type coercion, auto-fill, atomic writes, and all V3 validate() range checks.
"""

import copy
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from engines import config


class TestConfigBattle(unittest.TestCase):
    """15 battle tests for engines.config resilience."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._config_path = os.path.join(self._tmpdir, "config.json")
        config._config = None

    def tearDown(self):
        config._config = None
        # Clean up any files created during the test
        for name in os.listdir(self._tmpdir):
            filepath = os.path.join(self._tmpdir, name)
            try:
                os.remove(filepath)
            except OSError:
                pass
        try:
            os.rmdir(self._tmpdir)
        except OSError:
            pass

    def _load_with(self, overrides):
        """Set _config directly from defaults + overrides (bypasses load_config)."""
        cfg = copy.deepcopy(config.DEFAULT_CONFIG)
        for key_path, value in overrides.items():
            keys = key_path.split(".")
            current = cfg
            for k in keys[:-1]:
                current = current.setdefault(k, {})
            current[keys[-1]] = value
        config._config = cfg

    # ------------------------------------------------------------------
    # 1. Corrupt JSON recovery
    # ------------------------------------------------------------------
    def test_corrupt_json_recovery(self):
        """Loading a file with invalid JSON falls back to defaults."""
        with open(self._config_path, "w") as f:
            f.write("{this is not valid json!!!")

        cfg = config.load_config(path=self._config_path)

        # Must return a usable config identical to defaults
        self.assertIsInstance(cfg, dict)
        self.assertIn("telegram", cfg)
        self.assertIn("scanner", cfg)
        self.assertEqual(cfg["scanner"]["batch_size"], 1000)
        self.assertEqual(cfg["terminals"]["max_terminals"], 10)

    # ------------------------------------------------------------------
    # 2. Concurrent set() from 10 threads
    # ------------------------------------------------------------------
    def test_concurrent_set(self):
        """10 threads each calling set() with unique keys; all keys survive."""
        config.load_config(path=self._config_path)

        errors = []

        def worker(idx):
            try:
                config.set(f"battle.thread_{idx}", idx, path=self._config_path)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        self.assertEqual(errors, [], f"Thread errors: {errors}")

        # Every key must be present in the in-memory config
        for i in range(10):
            val = config.get(f"battle.thread_{i}")
            self.assertEqual(val, i, f"Missing or wrong value for thread_{i}")

    # ------------------------------------------------------------------
    # 3. Deep merge with 3+ levels of nesting
    # ------------------------------------------------------------------
    def test_deep_merge_nested(self):
        """_deep_merge handles three-plus levels of nested dicts."""
        base = {"a": {"b": {"c": {"d": 1, "e": 2}, "f": 3}}}
        override = {"a": {"b": {"c": {"d": 99}}}}

        result = config._deep_merge(base, override)

        self.assertEqual(result["a"]["b"]["c"]["d"], 99, "Override value should win")
        self.assertEqual(result["a"]["b"]["c"]["e"], 2, "Sibling key preserved")
        self.assertEqual(result["a"]["b"]["f"], 3, "Uncle key preserved")

    # ------------------------------------------------------------------
    # 4. Deep merge adds new top-level sections
    # ------------------------------------------------------------------
    def test_deep_merge_new_keys(self):
        """_deep_merge adds entirely new top-level sections from override."""
        base = {"existing": {"key": 1}}
        override = {"brand_new_section": {"alpha": "A", "beta": "B"}}

        result = config._deep_merge(base, override)

        self.assertIn("brand_new_section", result)
        self.assertEqual(result["brand_new_section"]["alpha"], "A")
        self.assertEqual(result["brand_new_section"]["beta"], "B")
        self.assertEqual(result["existing"]["key"], 1, "Existing section untouched")

    # ------------------------------------------------------------------
    # 5. Type coercion: string batch_size triggers validation warning
    # ------------------------------------------------------------------
    def test_type_coercion_in_validate(self):
        """String batch_size '1000' is not an int and triggers a validation warning."""
        self._load_with({"scanner.batch_size": "1000"})

        warnings = config.validate()

        batch_warnings = [w for w in warnings if "batch_size" in w]
        self.assertTrue(
            len(batch_warnings) > 0,
            "Expected a warning about non-int batch_size",
        )
        # After validation the value should be reset to the int default
        self.assertEqual(config.get("scanner.batch_size"), 1000)

    # ------------------------------------------------------------------
    # 6. Missing section auto-filled from defaults
    # ------------------------------------------------------------------
    def test_missing_section_auto_fill(self):
        """Loading config that omits 'security' section fills it from defaults."""
        partial = copy.deepcopy(config.DEFAULT_CONFIG)
        del partial["security"]
        with open(self._config_path, "w") as f:
            json.dump(partial, f)

        cfg = config.load_config(path=self._config_path)

        self.assertIn("security", cfg)
        self.assertEqual(
            cfg["security"]["encryption_enabled"],
            config.DEFAULT_CONFIG["security"]["encryption_enabled"],
        )

    # ------------------------------------------------------------------
    # 7. save_config_updates merges without losing existing keys
    # ------------------------------------------------------------------
    def test_save_config_updates_merge(self):
        """save_config_updates merges new data while preserving existing keys."""
        config.load_config(path=self._config_path)
        config.set(
            "telegram.bot_token",
            "123456789012345678901:TestToken",
            path=self._config_path,
        )

        # Now merge in a scanner update -- telegram must survive
        config.save_config_updates(
            {"scanner": {"batch_size": 2000}}, path=self._config_path
        )

        self.assertEqual(config.get("scanner.batch_size"), 2000)
        self.assertEqual(
            config.get("telegram.bot_token"),
            "123456789012345678901:TestToken",
            "Existing telegram token was clobbered by save_config_updates",
        )
        # Verify disk agrees
        with open(self._config_path) as f:
            disk = json.load(f)
        self.assertEqual(disk["scanner"]["batch_size"], 2000)
        self.assertEqual(
            disk["telegram"]["bot_token"], "123456789012345678901:TestToken"
        )

    # ------------------------------------------------------------------
    # 8. reset_defaults clears custom keys
    # ------------------------------------------------------------------
    def test_reset_defaults_clears_custom(self):
        """reset_defaults wipes custom keys and restores factory settings."""
        config.load_config(path=self._config_path)
        config.set("custom_section.custom_key", "custom_value", path=self._config_path)
        self.assertEqual(config.get("custom_section.custom_key"), "custom_value")

        config.reset_defaults(path=self._config_path)

        self.assertIsNone(
            config.get("custom_section.custom_key"),
            "Custom key should be gone after reset_defaults",
        )
        self.assertNotIn("custom_section", config._config)
        # Standard defaults must be intact
        self.assertEqual(config.get("scanner.batch_size"), 1000)
        self.assertEqual(config.get("terminals.max_terminals"), 10)

    # ------------------------------------------------------------------
    # 9. validate: invalid scanner.mode resets to "both"
    # ------------------------------------------------------------------
    def test_validate_scanner_mode_invalid(self):
        """Invalid scanner.mode triggers reset to 'both'."""
        self._load_with({"scanner.mode": "turbo"})

        warnings = config.validate()

        mode_warnings = [w for w in warnings if "scanner.mode" in w]
        self.assertTrue(len(mode_warnings) > 0, "Expected scanner.mode warning")
        self.assertEqual(config.get("scanner.mode"), "both")

    # ------------------------------------------------------------------
    # 10. validate: valid scanner.mode passes
    # ------------------------------------------------------------------
    def test_validate_scanner_mode_valid(self):
        """Each valid scanner.mode passes without a mode warning."""
        for mode in ("random_key", "seed_phrase", "both"):
            self._load_with({"scanner.mode": mode})
            warnings = config.validate()
            mode_warnings = [w for w in warnings if "scanner.mode" in w]
            self.assertEqual(
                len(mode_warnings),
                0,
                f"Unexpected warning for valid mode '{mode}': {mode_warnings}",
            )
            self.assertEqual(config.get("scanner.mode"), mode)

    # ------------------------------------------------------------------
    # 11. validate: checkpoint_interval below 1000 resets
    # ------------------------------------------------------------------
    def test_validate_checkpoint_interval_low(self):
        """checkpoint_interval < 1000 triggers reset to 100000."""
        self._load_with({"scanner.checkpoint_interval": 500})

        warnings = config.validate()

        cp_warnings = [w for w in warnings if "checkpoint_interval" in w]
        self.assertTrue(len(cp_warnings) > 0, "Expected checkpoint_interval warning")
        self.assertEqual(config.get("scanner.checkpoint_interval"), 100000)

    # ------------------------------------------------------------------
    # 12. validate: checkpoint_interval above 10 000 000 resets
    # ------------------------------------------------------------------
    def test_validate_checkpoint_interval_high(self):
        """checkpoint_interval > 10 000 000 triggers reset to 100000."""
        self._load_with({"scanner.checkpoint_interval": 99_999_999})

        warnings = config.validate()

        cp_warnings = [w for w in warnings if "checkpoint_interval" in w]
        self.assertTrue(len(cp_warnings) > 0, "Expected checkpoint_interval warning")
        self.assertEqual(config.get("scanner.checkpoint_interval"), 100000)

    # ------------------------------------------------------------------
    # 13. validate: max_terminals outside [1, 20] resets to 10
    # ------------------------------------------------------------------
    def test_validate_terminals_max(self):
        """max_terminals outside [1, 20] triggers reset to 10."""
        for bad_value in (0, -5, 21, 100):
            self._load_with({"terminals.max_terminals": bad_value})
            warnings = config.validate()
            term_warnings = [w for w in warnings if "max_terminals" in w]
            self.assertTrue(
                len(term_warnings) > 0,
                f"Expected max_terminals warning for value {bad_value}",
            )
            self.assertEqual(
                config.get("terminals.max_terminals"),
                10,
                f"max_terminals not reset for value {bad_value}",
            )

    # ------------------------------------------------------------------
    # 14. validate: health interval outside [10, 3600] resets to 60
    # ------------------------------------------------------------------
    def test_validate_health_interval(self):
        """health.interval_seconds outside [10, 3600] triggers reset to 60."""
        for bad_value in (1, 9, 3601, 99999):
            self._load_with({"health.interval_seconds": bad_value})
            warnings = config.validate()
            health_warnings = [w for w in warnings if "interval_seconds" in w]
            self.assertTrue(
                len(health_warnings) > 0,
                f"Expected interval_seconds warning for value {bad_value}",
            )
            self.assertEqual(
                config.get("health.interval_seconds"),
                60,
                f"interval_seconds not reset for value {bad_value}",
            )

    # ------------------------------------------------------------------
    # 15. Atomic write leaves no leftover .tmp file
    # ------------------------------------------------------------------
    def test_atomic_write_no_leftover_tmp(self):
        """After save_config, no .tmp file remains in the directory."""
        config.load_config(path=self._config_path)
        config.save_config(path=self._config_path)

        tmp_path = self._config_path + ".tmp"
        # Path(...).with_suffix('.tmp') is what config uses internally;
        # replicate both possible names to be thorough.
        tmp_path_pathlib = str(Path(self._config_path).with_suffix(".tmp"))

        self.assertFalse(
            os.path.exists(tmp_path),
            f"Leftover .tmp file found: {tmp_path}",
        )
        self.assertFalse(
            os.path.exists(tmp_path_pathlib),
            f"Leftover .tmp file found: {tmp_path_pathlib}",
        )

        # Also verify the real config file exists and is valid JSON
        self.assertTrue(os.path.exists(self._config_path))
        with open(self._config_path) as f:
            data = json.load(f)
        self.assertIn("scanner", data)


if __name__ == "__main__":
    unittest.main()
