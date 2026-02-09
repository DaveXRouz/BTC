# Legacy Tkinter GUI

This directory contains the legacy Tkinter desktop GUI, preserved as reference for the current React frontend migration.

## Files

| File               | Description                                            |
| ------------------ | ------------------------------------------------------ |
| `dashboard_tab.py` | Multi-terminal command center (up to 10 terminals)     |
| `hunter_tab.py`    | Unified scanner controls (random_key/seed_phrase/both) |
| `oracle_tab.py`    | Question mode + name cipher interface                  |
| `memory_tab.py`    | AI learning center with XP/level display               |
| `settings_tab.py`  | Telegram config, security, scanner defaults            |
| `widgets.py`       | Shared UI components (ToolTip, StyledButton)           |
| `theme.py`         | Color scheme and styling constants                     |

## Dual-GUI Strategy

NPS supports two frontends:

1. **React Web UI** (`frontend/src/`) — Primary target. Modern web-based interface with real-time WebSocket updates.
2. **Tkinter Desktop GUI** (this directory) — Legacy reference. May be adapted for local-only mode in later phases.

The React frontend replaces all 5 Tkinter tabs with equivalent web pages:

- Dashboard Tab -> `pages/Dashboard.tsx`
- Hunter Tab -> `pages/Scanner.tsx`
- Oracle Tab -> `pages/Oracle.tsx`
- Memory Tab -> `pages/Learning.tsx`
- Settings Tab -> `pages/Settings.tsx`

## Notes

- These files are **read-only reference copies** from `nps/gui/`.
- Do not modify these files — edit the legacy originals in `nps/gui/` if needed.
- The React migration should preserve all user-facing features from these tabs.
