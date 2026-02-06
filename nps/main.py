"""
NPS — Numerology Puzzle Solver
================================
Desktop application combining numerology (FC60 + Pythagorean + Chinese Calendar + Lunar)
with mathematical analysis for puzzle solving. Now with multi-chain scanning,
Telegram notifications, BIP39 seed generation, and headless mode.

Launch (GUI):      python main.py
Launch (headless): python main.py --headless
"""

import argparse
import signal
import sys
import os
import threading
import time
import logging
import tkinter as tk
from tkinter import ttk

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def setup_logging():
    """Configure application logging."""
    from pathlib import Path

    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    try:
        file_handler = logging.FileHandler(str(data_dir / "nps.log"), mode="a")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s")
        )
        logging.getLogger().addHandler(file_handler)
    except Exception:
        pass


class NPSApp:
    """Main application class."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NPS — Numerology Puzzle Solver V3")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        # Theme imports (before configure so COLORS is available)
        from gui.theme import COLORS, FONTS

        self.root.configure(bg=COLORS["bg"])

        # Security: prompt for master key before loading data
        self._init_security()

        # Initialize vault
        try:
            from engines.vault import init_vault

            init_vault()
        except Exception:
            pass

        # Start health monitoring
        try:
            from engines.health import start_monitoring

            start_monitoring()
        except Exception:
            pass

        self.active_solvers = []
        self.solver_registry = {}

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Dark title bar on Windows
        try:
            import ctypes

            self.root.update()
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(ctypes.c_int(1)),
                ctypes.sizeof(ctypes.c_int),
            )
        except Exception:
            pass

        # Configure notebook style
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.TNotebook", background=COLORS["bg"], borderwidth=0)
        style.configure(
            "Dark.TNotebook.Tab",
            background=COLORS["bg_card"],
            foreground=COLORS["text"],
            padding=[16, 6],
            font=FONTS["tab_title"],
        )
        style.map(
            "Dark.TNotebook.Tab",
            background=[("selected", COLORS["bg_input"])],
            foreground=[("selected", COLORS["text_bright"])],
        )

        # Notebook
        self.notebook = ttk.Notebook(self.root, style="Dark.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        # Create tabs
        self._create_tabs(COLORS)

        # Status bar
        self._create_status_bar(COLORS, FONTS)

        # Keyboard shortcuts
        self._bind_shortcuts()

        # Telegram command poller
        self._tg_running = False
        self._start_telegram_poller()

    def _init_security(self):
        """Prompt for master password at startup (encryption at rest)."""
        try:
            from engines.security import (
                has_salt,
                set_master_password,
                is_encrypted_mode,
            )
            from gui.widgets import ask_master_password

            first_time = not has_salt()
            password = ask_master_password(self.root, first_time=first_time)
            if password:
                set_master_password(password)
                logging.getLogger(__name__).info("Encryption enabled")
            else:
                logging.getLogger(__name__).info("Running without encryption")
        except Exception as e:
            logging.getLogger(__name__).warning(f"Security init skipped: {e}")

    def _bind_shortcuts(self):
        """Bind keyboard shortcuts: Cmd+1-5 switch tabs, Ctrl+R refresh dashboard."""
        for i in range(1, 6):
            self.root.bind(f"<Command-{i}>", lambda e, idx=i - 1: self._switch_tab(idx))
            self.root.bind(f"<Control-{i}>", lambda e, idx=i - 1: self._switch_tab(idx))

        self.root.bind("<Control-r>", lambda e: self._refresh_dashboard())
        self.root.bind("<Command-r>", lambda e: self._refresh_dashboard())

    def _switch_tab(self, index):
        """Switch to a notebook tab by index."""
        try:
            if index < self.notebook.index("end"):
                self.notebook.select(index)
        except Exception:
            pass

    def _refresh_dashboard(self):
        """Refresh dashboard tab (Ctrl+R shortcut)."""
        if hasattr(self, "dashboard"):
            self.dashboard.refresh_stats()
            self.dashboard._refresh_terminals()

    def _create_tabs(self, COLORS):
        from gui.dashboard_tab import DashboardTab
        from gui.hunter_tab import HunterTab
        from gui.oracle_tab import OracleTab
        from gui.memory_tab import MemoryTab
        from gui.settings_tab import SettingsTab

        # Tab 1: Dashboard (War Room)
        dash_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(dash_frame, text="  Dashboard  ")
        self.dashboard = DashboardTab(dash_frame, app=self)

        # Tab 2: Hunter (Puzzle + Scanner)
        hunter_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(hunter_frame, text="  Hunter  ")
        self.hunter_tab = HunterTab(hunter_frame, app=self)

        # Tab 3: Oracle (Sign + Name)
        oracle_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(oracle_frame, text="  Oracle  ")
        self.oracle_tab = OracleTab(oracle_frame, app=self)

        # Tab 4: Memory (Learning Dashboard)
        memory_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(memory_frame, text="  Memory  ")
        self.memory_tab = MemoryTab(memory_frame, app=self)

        # Tab 5: Settings & Connections
        settings_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(settings_frame, text="  Settings  ")
        self.settings_tab = SettingsTab(settings_frame, app=self)

    def _create_status_bar(self, COLORS, FONTS):
        status = tk.Frame(self.root, bg=COLORS["bg_card"], bd=1, relief="solid")
        status.pack(fill="x", side="bottom")

        self.status_label = tk.Label(
            status,
            text="Ready",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            padx=12,
            pady=4,
        )
        self.status_label.pack(side="left")

        self.learning_label = tk.Label(
            status,
            text="Learning: 0 solves",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            padx=12,
            pady=4,
        )
        self.learning_label.pack(side="left")

        self.conf_label = tk.Label(
            status,
            text="Confidence: 0.00",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            padx=12,
            pady=4,
        )
        self.conf_label.pack(side="right")

        # Telegram status
        try:
            from engines.notifier import is_configured

            tg_text = "Telegram: ON" if is_configured() else "Telegram: Not configured"
        except Exception:
            tg_text = "Telegram: Not configured"
        self.telegram_label = tk.Label(
            status,
            text=tg_text,
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            padx=12,
            pady=4,
        )
        self.telegram_label.pack(side="right")

        # Encryption status
        try:
            from engines.security import is_encrypted_mode

            enc_text = "Encrypted" if is_encrypted_mode() else "Not Encrypted"
            enc_fg = (
                COLORS["text_dim"]
                if is_encrypted_mode()
                else COLORS.get("warning", "#FFA500")
            )
        except Exception:
            enc_text = "Not Encrypted"
            enc_fg = COLORS.get("warning", "#FFA500")
        self.enc_label = tk.Label(
            status,
            text=enc_text,
            font=FONTS["small"],
            fg=enc_fg,
            bg=COLORS["bg_card"],
            padx=12,
            pady=4,
        )
        self.enc_label.pack(side="right")

        # AI status indicator
        from gui.widgets import AIStatusIndicator

        self.ai_status = AIStatusIndicator(status)
        self.ai_status.pack(side="right")

        self._update_status_bar()

    def _update_status_bar(self):
        try:
            from engines.learning import get_solve_stats, confidence_level

            stats = get_solve_stats()
            conf = confidence_level()
            self.learning_label.config(
                text=f"Learning: {stats['total_attempts']} solves"
            )
            dots = int(conf * 3)
            dot_str = "◆" * dots + "●" * (3 - dots)
            self.conf_label.config(text=f"Confidence: {conf:.2f}  {dot_str}")
        except Exception:
            pass
        self.root.after(10000, self._update_status_bar)

    def register_solver(self, solver):
        self.active_solvers.append(solver)

    def unregister_solver(self, solver):
        if solver in self.active_solvers:
            self.active_solvers.remove(solver)

    def register_solver_v2(self, solver, solver_type="puzzle"):
        """Register solver with type info for the dashboard."""
        self.active_solvers.append(solver)
        self.solver_registry[id(solver)] = {
            "solver": solver,
            "type": solver_type,
            "description": solver.get_description(),
        }

    def unregister_solver_v2(self, solver):
        """Unregister a v2 solver."""
        if solver in self.active_solvers:
            self.active_solvers.remove(solver)
        self.solver_registry.pop(id(solver), None)

    def get_solver_stats(self):
        """Return combined stats for all registered solvers."""
        result = {"solvers": [], "total_operations": 0, "total_speed": 0}
        for sid, info in list(self.solver_registry.items()):
            solver = info["solver"]
            if not solver.running:
                continue
            stats = solver.get_stats() if hasattr(solver, "get_stats") else {}
            ops = stats.get("keys_tested", stats.get("candidates_tested", 0))
            speed = stats.get("speed", 0)
            result["solvers"].append(
                {
                    "type": info["type"],
                    "description": info["description"],
                    "operations": ops,
                    "speed": speed,
                }
            )
            result["total_operations"] += ops
            result["total_speed"] += speed
        return result

    def _start_telegram_poller(self):
        """Start background thread to poll Telegram for commands."""
        try:
            from engines.notifier import is_configured

            if not is_configured():
                return
        except Exception:
            return

        self._tg_running = True

        def _poll_loop():
            while self._tg_running:
                try:
                    from engines.notifier import poll_telegram_commands

                    cmds = poll_telegram_commands(timeout=2)
                    for cmd in cmds:
                        self.root.after(0, self._handle_gui_telegram_cmd, cmd)
                except Exception:
                    pass

        threading.Thread(target=_poll_loop, daemon=True).start()

    def _handle_gui_telegram_cmd(self, cmd):
        """Handle a Telegram command in GUI mode."""
        parts = cmd.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        try:
            from engines.notifier import (
                send_message_with_buttons,
                send_message,
                CONTROL_BUTTONS,
            )
        except Exception:
            return

        if cmd == "/status":
            stats = self.get_solver_stats()
            solvers = stats.get("solvers", [])
            lines = ["<b>NPS Status (GUI)</b>"]
            for s in solvers:
                lines.append(
                    f"{s['type'].capitalize()}: {s['description']} — "
                    f"{s['operations']:,} ops | {s['speed']:,.0f}/s"
                )
            if not solvers:
                lines.append("No active solvers")
            lines.append(
                f"Combined: {stats['total_operations']:,} ops | "
                f"{stats['total_speed']:,.0f}/s"
            )
            send_message_with_buttons("\n".join(lines), CONTROL_BUTTONS)
        elif cmd == "/pause":
            for solver in list(self.active_solvers):
                if solver.running:
                    solver.stop()
            send_message_with_buttons("<b>All solvers paused.</b>", CONTROL_BUTTONS)
        elif cmd == "/resume":
            send_message_with_buttons(
                "<b>Use the GUI to start solvers.</b>", CONTROL_BUTTONS
            )
        elif cmd == "/stop":
            for solver in list(self.active_solvers):
                if solver.running:
                    solver.stop()
            send_message_with_buttons("<b>All solvers stopped.</b>", CONTROL_BUTTONS)
        elif cmd == "/sign":
            if not arg:
                send_message("Usage: /sign <sign text>")
            else:
                try:
                    from engines.oracle import read_sign

                    result = read_sign(arg)
                    interp = result.get("interpretation", "No interpretation")
                    send_message(f"<b>Oracle: {arg}</b>\n{interp}")
                except Exception as e:
                    send_message(f"Oracle error: {e}")
        elif cmd == "/name":
            if not arg:
                send_message("Usage: /name <name>")
            else:
                try:
                    from engines.oracle import read_name

                    result = read_name(arg)
                    expr = result.get("expression", "?")
                    soul = result.get("soul_urge", "?")
                    send_message(
                        f"<b>Name: {arg}</b>\nExpression: {expr}\nSoul Urge: {soul}"
                    )
                except Exception as e:
                    send_message(f"Name error: {e}")
        elif cmd == "/memory":
            try:
                from engines.memory import get_summary

                s = get_summary()
                send_message(
                    f"<b>Memory Stats</b>\n"
                    f"Sessions: {s.get('total_sessions', 0)}\n"
                    f"Keys: {s.get('total_keys', 0):,}\n"
                    f"High Scores: {s.get('high_score_count', 0)}\n"
                    f"Best: {s.get('top_score', 0):.3f}"
                )
            except Exception as e:
                send_message(f"Memory error: {e}")
        elif cmd == "/perf":
            try:
                from engines.perf import perf

                summary = perf.summary()
                if summary:
                    lines = ["<b>Performance</b>"]
                    for name, stats in summary.items():
                        lines.append(
                            f"{name}: avg={stats['avg']*1000:.1f}ms n={stats['count']}"
                        )
                    send_message("\n".join(lines))
                else:
                    send_message("No performance data yet.")
            except Exception as e:
                send_message(f"Perf error: {e}")
        elif cmd == "/help":
            from engines.notifier import COMMANDS

            lines = ["<b>Available Commands</b>"]
            for c, desc in COMMANDS.items():
                lines.append(f"  {c} — {desc}")
            send_message("\n".join(lines))

    def _on_close(self):
        """Stop all running solvers and flush memory before closing."""
        self._tg_running = False

        # Stop health monitoring
        try:
            from engines.health import stop_monitoring

            stop_monitoring()
        except Exception:
            pass

        # Stop hunter tab solvers
        if hasattr(self, "hunter_tab"):
            try:
                self.hunter_tab.stop_all()
            except Exception:
                pass

        for solver in self.active_solvers:
            solver.stop()

        deadline = time.time() + 2.0
        for solver in self.active_solvers:
            if solver._thread and solver._thread.is_alive():
                remaining = max(0.1, deadline - time.time())
                solver._thread.join(timeout=remaining)

        # Flush vault
        try:
            from engines.vault import shutdown as vault_shutdown

            vault_shutdown()
        except Exception:
            pass

        # Flush memory to disk
        try:
            from engines.memory import shutdown as memory_shutdown

            memory_shutdown()
        except Exception:
            pass

        self.root.destroy()

    def run(self):
        self.root.mainloop()


def run_headless(config_path=None):
    """Run NPS in headless mode (no GUI) — for server/cloud deployment."""
    logger = logging.getLogger("headless")

    # Load config
    from engines.config import load_config, get

    if config_path:
        load_config(path=config_path)
    else:
        load_config()

    # Security: check for master password in env
    try:
        from engines.security import set_master_password, is_encrypted_mode

        master_pw = os.environ.get("NPS_MASTER_PASSWORD")
        if master_pw:
            set_master_password(master_pw)
            logger.info("Encryption enabled via NPS_MASTER_PASSWORD")
        else:
            logger.info("No NPS_MASTER_PASSWORD set — running without encryption")
    except Exception as e:
        logger.warning(f"Security init skipped: {e}")

    # Initialize vault
    try:
        from engines.vault import init_vault

        init_vault()
    except Exception:
        pass

    print("=" * 60)
    print("NPS — Headless Scanner Mode")
    print("=" * 60)
    print("WARNING: Random scanning odds are ~1 in 10^41.")
    print("This is for educational and research purposes only.")
    print("=" * 60)

    # Telegram startup notification
    try:
        from engines.notifier import send_message, is_configured

        if is_configured():
            send_message("<b>NPS Headless Started</b>\nScanner is now running.")
            print("Telegram: Connected")
        else:
            print("Telegram: Not configured (set chat_id in config.json)")
    except Exception:
        print("Telegram: Not available")

    # Signal handling for graceful shutdown
    scanner = None
    running = True

    def signal_handler(sig, frame):
        nonlocal running
        print("\nShutdown signal received...")
        running = False
        if scanner:
            scanner.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start scanner
    mode = get("headless.scanner_mode", "both")
    print(f"Starting scanner in '{mode}' mode...")

    from solvers.scanner_solver import ScannerSolver

    def headless_callback(data):
        speed = data.get("speed", 0)
        tested = data.get("keys_tested", 0)
        seeds = data.get("seeds_tested", 0)
        hits = data.get("hits", 0)
        print(
            f"\r  Keys: {tested:,}  Seeds: {seeds:,}  Speed: {speed:.0f}/s  Hits: {hits}",
            end="",
            flush=True,
        )

    def _handle_telegram_command(cmd, scnr):
        """Handle a Telegram command in headless mode."""
        nonlocal running, scanner
        cmd = cmd.lower().strip()
        try:
            from engines.notifier import send_message_with_buttons, CONTROL_BUTTONS
        except Exception:
            return

        if cmd == "/status":
            stats = scnr.get_stats() if scnr else {}
            elapsed_hrs = stats.get("elapsed", 0) / 3600
            msg = (
                f"<b>NPS Status</b>\n"
                f"Keys: {stats.get('keys_tested', 0):,}\n"
                f"Seeds: {stats.get('seeds_tested', 0):,}\n"
                f"Speed: {stats.get('speed', 0):.0f}/s\n"
                f"Hits: {stats.get('hits', 0)}\n"
                f"Uptime: {elapsed_hrs:.1f}h"
            )
            send_message_with_buttons(msg, CONTROL_BUTTONS)
        elif cmd == "/pause":
            if scnr and scnr.running:
                scnr.stop()
                send_message_with_buttons("<b>Scanner paused.</b>", CONTROL_BUTTONS)
                logger.info("Scanner paused via Telegram")
        elif cmd == "/resume":
            if not scnr or not scnr.running:
                scanner = ScannerSolver(
                    mode=mode, callback=headless_callback, check_balance_online=True
                )
                scanner.start()
                send_message_with_buttons("<b>Scanner resumed.</b>", CONTROL_BUTTONS)
                logger.info("Scanner resumed via Telegram")
        elif cmd == "/stop":
            running = False
            if scnr:
                scnr.stop()
            send_message_with_buttons("<b>Scanner stopping...</b>", CONTROL_BUTTONS)
            logger.info("Scanner stop requested via Telegram")

    scanner = ScannerSolver(
        mode=mode, callback=headless_callback, check_balance_online=True
    )
    scanner.start()

    # Main loop: sleep, periodic status, Telegram polling
    last_status = time.time()
    status_interval = get("headless.status_interval_hours", 24) * 3600

    try:
        while running and scanner.running:
            # Poll Telegram with 2s long-poll (acts as both sleep and listener)
            try:
                from engines.notifier import poll_telegram_commands, is_configured

                if is_configured():
                    cmds = poll_telegram_commands(timeout=2)
                    for cmd in cmds:
                        _handle_telegram_command(cmd, scanner)
                else:
                    time.sleep(2)
            except Exception:
                time.sleep(2)

            # Daily status
            if time.time() - last_status >= status_interval:
                last_status = time.time()
                stats = scanner.get_stats()
                elapsed = stats.get("elapsed", 0)
                hrs = elapsed / 3600
                try:
                    from engines.notifier import notify_daily_status, is_configured

                    if is_configured():
                        notify_daily_status(
                            {
                                "keys_tested": stats.get("keys_tested", 0),
                                "seeds_tested": stats.get("seeds_tested", 0),
                                "online_checks": stats.get("online_checks", 0),
                                "hits": stats.get("hits", 0),
                                "uptime": f"{hrs:.1f} hours",
                            }
                        )
                except Exception:
                    pass
    except KeyboardInterrupt:
        pass

    # Graceful shutdown
    print("\nShutting down...")
    if scanner:
        scanner.stop()
        if scanner._thread:
            scanner._thread.join(timeout=5)

    # Final stats
    stats = scanner.get_stats()
    print(
        f"Final stats: {stats.get('keys_tested', 0):,} keys, "
        f"{stats.get('seeds_tested', 0):,} seeds, {stats.get('hits', 0)} hits"
    )

    # Flush vault
    try:
        from engines.vault import shutdown as vault_shutdown

        vault_shutdown()
    except Exception:
        pass

    # Flush memory to disk
    try:
        from engines.memory import shutdown as memory_shutdown

        memory_shutdown()
    except Exception:
        pass

    # Telegram shutdown notification
    try:
        from engines.notifier import send_message, is_configured

        if is_configured():
            send_message(
                f"<b>NPS Headless Stopped</b>\n"
                f"Keys: {stats.get('keys_tested', 0):,}\n"
                f"Seeds: {stats.get('seeds_tested', 0):,}\n"
                f"Hits: {stats.get('hits', 0)}"
            )
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(
        description="NPS — Numerology Puzzle Solver with Multi-Chain Scanner"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (no GUI, scanner only)",
    )
    parser.add_argument(
        "--config", type=str, default=None, help="Path to custom config.json file"
    )
    parser.add_argument(
        "--profile", action="store_true", help="Print timing info on startup"
    )
    args = parser.parse_args()

    setup_logging()

    if args.profile:
        t0 = time.time()

    if args.headless:
        run_headless(args.config)
    else:
        app = NPSApp()
        if args.profile:
            print(f"Startup time: {time.time() - t0:.2f}s")
        app.run()


if __name__ == "__main__":
    main()
