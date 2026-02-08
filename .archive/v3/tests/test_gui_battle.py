"""
GUI smoke tests — verify module importability and class/attribute existence
without requiring a display or creating tkinter windows/widgets.

Wave 6: ~15 tests.
"""

import inspect
import os
import sys
import unittest
from pathlib import Path

# Allow imports from the nps package
sys.path.insert(0, str(Path(__file__).parent.parent))


@unittest.skipUnless(
    os.environ.get("DISPLAY") or sys.platform == "darwin",
    "No display available — skipping GUI smoke tests",
)
class TestGUIBattle(unittest.TestCase):
    """Smoke tests for GUI modules — importability and attribute checks only."""

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def test_import_theme(self):
        """gui.theme module imports successfully."""
        import gui.theme  # noqa: F401

    def test_colors_dict_exists(self):
        """COLORS dict has at least 10 entries."""
        from gui.theme import COLORS

        self.assertIsInstance(COLORS, dict)
        self.assertGreaterEqual(len(COLORS), 10)

    def test_fonts_dict_exists(self):
        """FONTS dict has at least 5 entries."""
        from gui.theme import FONTS

        self.assertIsInstance(FONTS, dict)
        self.assertGreaterEqual(len(FONTS), 5)

    def test_theme_colors_keys(self):
        """COLORS contains required core keys: bg, text, accent."""
        from gui.theme import COLORS

        for key in ("bg", "text", "accent"):
            self.assertIn(key, COLORS, f"COLORS missing required key '{key}'")

    # ------------------------------------------------------------------
    # Widgets
    # ------------------------------------------------------------------

    def test_import_widgets(self):
        """gui.widgets module imports successfully."""
        import gui.widgets  # noqa: F401

    def test_tooltip_class_exists(self):
        """ToolTip class exists and has __init__."""
        from gui.widgets import ToolTip

        self.assertTrue(inspect.isclass(ToolTip))
        self.assertTrue(hasattr(ToolTip, "__init__"))

    def test_styled_button_class_exists(self):
        """StyledButton class exists."""
        from gui.widgets import StyledButton

        self.assertTrue(inspect.isclass(StyledButton))

    # ------------------------------------------------------------------
    # Dashboard tab
    # ------------------------------------------------------------------

    def test_import_dashboard_tab(self):
        """gui.dashboard_tab module imports successfully."""
        import gui.dashboard_tab  # noqa: F401

    def test_dashboard_tab_class(self):
        """DashboardTab class exists in gui.dashboard_tab."""
        from gui.dashboard_tab import DashboardTab

        self.assertTrue(inspect.isclass(DashboardTab))

    # ------------------------------------------------------------------
    # Hunter tab
    # ------------------------------------------------------------------

    def test_import_hunter_tab(self):
        """gui.hunter_tab module imports successfully."""
        import gui.hunter_tab  # noqa: F401

    def test_hunter_tab_class(self):
        """HunterTab class exists in gui.hunter_tab."""
        from gui.hunter_tab import HunterTab

        self.assertTrue(inspect.isclass(HunterTab))

    # ------------------------------------------------------------------
    # Oracle tab
    # ------------------------------------------------------------------

    def test_import_oracle_tab(self):
        """gui.oracle_tab module imports successfully."""
        import gui.oracle_tab  # noqa: F401

    # ------------------------------------------------------------------
    # Memory tab
    # ------------------------------------------------------------------

    def test_import_memory_tab(self):
        """gui.memory_tab module imports successfully."""
        import gui.memory_tab  # noqa: F401

    # ------------------------------------------------------------------
    # Settings tab
    # ------------------------------------------------------------------

    def test_import_settings_tab(self):
        """gui.settings_tab module imports successfully."""
        import gui.settings_tab  # noqa: F401

    # ------------------------------------------------------------------
    # Cross-cutting: all tab classes are actually classes
    # ------------------------------------------------------------------

    def test_all_tabs_are_classes(self):
        """All 5 tab classes are real classes (inspect.isclass)."""
        from gui.dashboard_tab import DashboardTab
        from gui.hunter_tab import HunterTab
        from gui.oracle_tab import OracleTab
        from gui.memory_tab import MemoryTab
        from gui.settings_tab import SettingsTab

        for cls in (DashboardTab, HunterTab, OracleTab, MemoryTab, SettingsTab):
            self.assertTrue(
                inspect.isclass(cls),
                f"{cls.__name__} is not a class",
            )


if __name__ == "__main__":
    unittest.main()
