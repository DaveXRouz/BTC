"""Dashboard tab — V3 War Room overview."""

import threading
import tkinter as tk
from datetime import datetime
from gui.theme import COLORS, FONTS
from gui.widgets import StatsCard, AIInsightPanel, StyledButton, LogPanel


class DashboardTab:
    """War Room: current moment, mission status, quick stats, live activity."""

    def __init__(self, parent, app=None):
        self.parent = parent
        self.app = app
        self._build_ui()
        self._subscribe_events()
        self._refresh_moment()
        self._start_stats_poll()

    def _build_ui(self):
        main = tk.Frame(self.parent, bg=COLORS["bg"], padx=16, pady=12)
        main.pack(fill="both", expand=True)

        # Header
        tk.Label(
            main,
            text="War Room",
            font=FONTS["heading"],
            fg=COLORS["accent"],
            bg=COLORS["bg"],
        ).pack(anchor="w", pady=(0, 8))

        # ── Row 1: Current Moment ──
        self._build_moment_panel(main)

        # ── Row 2: Mission Status (puzzle + scanner side by side) ──
        mission_frame = tk.Frame(main, bg=COLORS["bg"])
        mission_frame.pack(fill="x", pady=(0, 8))
        self._build_puzzle_status(mission_frame)
        self._build_scanner_status(mission_frame)

        # ── Row 2.5: Terminal Cards ──
        self._build_terminals_section(main)

        # ── Row 3: Quick Stats | AI Brain | Comms ──
        row3 = tk.Frame(main, bg=COLORS["bg"])
        row3.pack(fill="x", pady=(0, 8))
        self._build_quick_stats(row3)
        self._build_ai_brain(row3)
        self._build_comms_card(row3)

        # ── Row 4: Live Activity Feed ──
        tk.Label(
            main,
            text="Live Activity",
            font=FONTS["subhead"],
            fg=COLORS["text"],
            bg=COLORS["bg"],
        ).pack(anchor="w", pady=(4, 2))
        self.activity_log = LogPanel(main, height=8)
        self.activity_log.pack(fill="both", expand=True)
        self.activity_log.log("NPS V3 started. Awaiting missions.", "info")

    # ─── Current Moment ───
    def _build_moment_panel(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="  Current Moment  ",
            font=FONTS["body"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            bd=1,
            relief="solid",
            padx=12,
            pady=6,
        )
        frame.pack(fill="x", pady=(0, 8))

        row = tk.Frame(frame, bg=COLORS["bg_card"])
        row.pack(fill="x")

        self.fc60_label = tk.Label(
            row,
            text="FC60: loading...",
            font=FONTS["mono_lg"],
            fg=COLORS["gold"],
            bg=COLORS["bg_card"],
        )
        self.fc60_label.pack(side="left")

        self.moon_label = tk.Label(
            row,
            text="",
            font=FONTS["body"],
            fg=COLORS["purple"],
            bg=COLORS["bg_card"],
            padx=24,
        )
        self.moon_label.pack(side="left")

        self.gz_label = tk.Label(
            row,
            text="",
            font=FONTS["body"],
            fg=COLORS["text"],
            bg=COLORS["bg_card"],
        )
        self.gz_label.pack(side="left")

        self.energy_label = tk.Label(
            frame,
            text="",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            wraplength=800,
            justify="left",
        )
        self.energy_label.pack(fill="x", pady=(2, 0))

    # ─── Puzzle Status ───
    def _build_puzzle_status(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="  Puzzle Mission  ",
            font=FONTS["body"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            bd=1,
            relief="solid",
            padx=12,
            pady=6,
        )
        frame.pack(side="left", fill="both", expand=True, padx=(0, 4))

        self._puzzle_labels = {}
        for key, label, default in [
            ("status", "Status:", "Idle"),
            ("puzzle", "Puzzle:", "—"),
            ("strategy", "Strategy:", "—"),
            ("keys", "Keys Tested:", "0"),
            ("speed", "Speed:", "0/s"),
            ("best_score", "Best Score:", "—"),
        ]:
            row = tk.Frame(frame, bg=COLORS["bg_card"])
            row.pack(fill="x", pady=1)
            tk.Label(
                row,
                text=label,
                font=FONTS["small"],
                fg=COLORS["text_dim"],
                bg=COLORS["bg_card"],
            ).pack(side="left")
            lbl = tk.Label(
                row,
                text=default,
                font=FONTS["mono_sm"],
                fg=COLORS["text"],
                bg=COLORS["bg_card"],
            )
            lbl.pack(side="right")
            self._puzzle_labels[key] = lbl

    # ─── Scanner Status ───
    def _build_scanner_status(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="  Scanner Mission  ",
            font=FONTS["body"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            bd=1,
            relief="solid",
            padx=12,
            pady=6,
        )
        frame.pack(side="left", fill="both", expand=True, padx=(4, 0))

        self._scanner_labels = {}
        for key, label, default in [
            ("status", "Status:", "Idle"),
            ("mode", "Mode:", "—"),
            ("keys", "Keys Tested:", "0"),
            ("seeds", "Seeds Tested:", "0"),
            ("speed", "Speed:", "0/s"),
            ("hits", "Hits:", "0"),
        ]:
            row = tk.Frame(frame, bg=COLORS["bg_card"])
            row.pack(fill="x", pady=1)
            tk.Label(
                row,
                text=label,
                font=FONTS["small"],
                fg=COLORS["text_dim"],
                bg=COLORS["bg_card"],
            ).pack(side="left")
            lbl = tk.Label(
                row,
                text=default,
                font=FONTS["mono_sm"],
                fg=COLORS["text"],
                bg=COLORS["bg_card"],
            )
            lbl.pack(side="right")
            self._scanner_labels[key] = lbl

    # ─── Terminals Section ───
    def _build_terminals_section(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="  Terminals  ",
            font=FONTS["body"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            bd=1,
            relief="solid",
            padx=8,
            pady=4,
        )
        frame.pack(fill="x", pady=(0, 8))

        # Header with New Terminal button
        header = tk.Frame(frame, bg=COLORS["bg_card"])
        header.pack(fill="x", pady=(0, 4))
        StyledButton(
            header,
            text="New Terminal",
            command=self._create_terminal,
            bg=COLORS["bg_button"],
            fg=COLORS["text_bright"],
            font=FONTS["small"],
            padx=8,
            pady=2,
            tooltip="Create a new scanner terminal (max 10)",
        ).pack(side="left")

        self._terminal_count_label = tk.Label(
            header,
            text="0 terminals",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
        )
        self._terminal_count_label.pack(side="right")

        # Scrollable terminal cards area
        self._terminals_frame = tk.Frame(frame, bg=COLORS["bg_card"])
        self._terminals_frame.pack(fill="x")
        self._terminal_widgets = {}

        self._refresh_terminals()

    def _refresh_terminals(self):
        """Refresh terminal cards."""
        try:
            from engines.terminal_manager import list_terminals, get_terminal_stats
        except ImportError:
            return

        terminals = list_terminals()
        self._terminal_count_label.config(text=f"{len(terminals)} terminal(s)")

        # Clear existing widgets
        for widget in self._terminals_frame.winfo_children():
            widget.destroy()
        self._terminal_widgets = {}

        if not terminals:
            tk.Label(
                self._terminals_frame,
                text="No terminals. Click 'New Terminal' to create one.",
                font=FONTS["small"],
                fg=COLORS["text_dim"],
                bg=COLORS["bg_card"],
            ).pack(pady=4)
            return

        for term_info in terminals:
            tid = term_info["id"]
            status = term_info["status"]
            stats = get_terminal_stats(tid) or {}

            card = tk.Frame(
                self._terminals_frame,
                bg=COLORS["bg_input"],
                bd=1,
                relief="solid",
                padx=8,
                pady=4,
            )
            card.pack(fill="x", pady=2)

            # Status dot + ID
            info_row = tk.Frame(card, bg=COLORS["bg_input"])
            info_row.pack(fill="x")

            dot_color = {
                "running": COLORS["success"],
                "paused": COLORS["warning"],
                "stopped": COLORS["error"],
                "created": COLORS["accent"],
            }.get(status, COLORS["text_dim"])

            tk.Label(
                info_row,
                text="\u25cf",
                font=FONTS["small"],
                fg=dot_color,
                bg=COLORS["bg_input"],
            ).pack(side="left")

            tk.Label(
                info_row,
                text=f" {tid}",
                font=FONTS["mono_sm"],
                fg=COLORS["text"],
                bg=COLORS["bg_input"],
            ).pack(side="left")

            tk.Label(
                info_row,
                text=status.upper(),
                font=FONTS["small"],
                fg=dot_color,
                bg=COLORS["bg_input"],
            ).pack(side="left", padx=(8, 0))

            # Stats
            keys = stats.get("keys_tested", 0)
            speed = stats.get("speed", 0)
            mode = term_info.get("settings", {}).get("mode", "?")

            tk.Label(
                info_row,
                text=f"Mode: {mode}  |  Keys: {keys:,}  |  {speed:,.0f}/s",
                font=FONTS["mono_sm"],
                fg=COLORS["text"],
                bg=COLORS["bg_input"],
            ).pack(side="right")

            # Control buttons
            btn_row = tk.Frame(card, bg=COLORS["bg_input"])
            btn_row.pack(fill="x", pady=(2, 0))

            if status in ("created", "stopped"):
                StyledButton(
                    btn_row,
                    text="Start",
                    command=lambda t=tid: self._start_terminal(t),
                    bg=COLORS["bg_success"],
                    fg=COLORS["text_bright"],
                    font=FONTS["small"],
                    padx=6,
                    pady=1,
                ).pack(side="left", padx=(0, 4))
            elif status == "running":
                StyledButton(
                    btn_row,
                    text="Pause",
                    command=lambda t=tid: self._pause_terminal(t),
                    bg=COLORS["warning"],
                    fg=COLORS["text_bright"],
                    font=FONTS["small"],
                    padx=6,
                    pady=1,
                ).pack(side="left", padx=(0, 4))
                StyledButton(
                    btn_row,
                    text="Stop",
                    command=lambda t=tid: self._stop_terminal(t),
                    bg=COLORS["bg_danger"],
                    fg=COLORS["text_bright"],
                    font=FONTS["small"],
                    padx=6,
                    pady=1,
                ).pack(side="left", padx=(0, 4))
            elif status == "paused":
                StyledButton(
                    btn_row,
                    text="Resume",
                    command=lambda t=tid: self._resume_terminal(t),
                    bg=COLORS["bg_success"],
                    fg=COLORS["text_bright"],
                    font=FONTS["small"],
                    padx=6,
                    pady=1,
                ).pack(side="left", padx=(0, 4))
                StyledButton(
                    btn_row,
                    text="Stop",
                    command=lambda t=tid: self._stop_terminal(t),
                    bg=COLORS["bg_danger"],
                    fg=COLORS["text_bright"],
                    font=FONTS["small"],
                    padx=6,
                    pady=1,
                ).pack(side="left", padx=(0, 4))

        # Auto-refresh every 5 seconds
        self.parent.after(5000, self._refresh_terminals)

    def _create_terminal(self):
        def _do():
            from engines.terminal_manager import create_terminal

            create_terminal()
            self.parent.after(0, self._refresh_terminals)

        threading.Thread(target=_do, daemon=True).start()

    def _start_terminal(self, terminal_id):
        def _do():
            from engines.terminal_manager import start_terminal

            start_terminal(terminal_id)
            self.parent.after(0, self._refresh_terminals)

        threading.Thread(target=_do, daemon=True).start()

    def _stop_terminal(self, terminal_id):
        def _do():
            from engines.terminal_manager import stop_terminal

            stop_terminal(terminal_id)
            self.parent.after(0, self._refresh_terminals)

        threading.Thread(target=_do, daemon=True).start()

    def _pause_terminal(self, terminal_id):
        def _do():
            from engines.terminal_manager import pause_terminal

            pause_terminal(terminal_id)
            self.parent.after(0, self._refresh_terminals)

        threading.Thread(target=_do, daemon=True).start()

    def _resume_terminal(self, terminal_id):
        def _do():
            from engines.terminal_manager import resume_terminal

            resume_terminal(terminal_id)
            self.parent.after(0, self._refresh_terminals)

        threading.Thread(target=_do, daemon=True).start()

    # ─── Quick Stats ───
    def _build_quick_stats(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="  Quick Stats  ",
            font=FONTS["body"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            bd=1,
            relief="solid",
            padx=12,
            pady=6,
        )
        frame.pack(side="left", fill="both", expand=True, padx=(0, 4))

        self._stat_labels = {}
        for key, label, default in [
            ("total_ops", "Total Operations:", "0"),
            ("total_speed", "Combined Speed:", "0/s"),
            ("learning", "Learning:", "0 solves"),
            ("confidence", "Confidence:", "0%"),
        ]:
            row = tk.Frame(frame, bg=COLORS["bg_card"])
            row.pack(fill="x", pady=1)
            tk.Label(
                row,
                text=label,
                font=FONTS["small"],
                fg=COLORS["text_dim"],
                bg=COLORS["bg_card"],
            ).pack(side="left")
            lbl = tk.Label(
                row,
                text=default,
                font=FONTS["mono_sm"],
                fg=COLORS["text"],
                bg=COLORS["bg_card"],
            )
            lbl.pack(side="right")
            self._stat_labels[key] = lbl

    # ─── AI Brain ───
    def _build_ai_brain(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="  AI Brain  ",
            font=FONTS["body"],
            fg=COLORS["ai_accent"],
            bg=COLORS["ai_bg"],
            bd=1,
            relief="solid",
            padx=12,
            pady=6,
        )
        frame.pack(side="left", fill="both", expand=True, padx=(4, 4))
        frame.configure(highlightbackground=COLORS["ai_border"], highlightthickness=1)

        self._ai_label = tk.Label(
            frame,
            text="\u2014",
            font=FONTS["small"],
            fg=COLORS["ai_text"],
            bg=COLORS["ai_bg"],
            wraplength=300,
            justify="left",
            anchor="nw",
        )
        self._ai_label.pack(fill="both", expand=True)

    # ─── Comms ───
    def _build_comms_card(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="  Comms  ",
            font=FONTS["body"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            bd=1,
            relief="solid",
            padx=12,
            pady=6,
        )
        frame.pack(side="left", fill="both", expand=True, padx=(4, 0))

        self._comms_labels = {}
        for key, label, default in [
            ("ai", "AI:", "OFF"),
            ("telegram", "Telegram:", "OFF"),
            ("memory", "Memory:", "0 sessions"),
        ]:
            row = tk.Frame(frame, bg=COLORS["bg_card"])
            row.pack(fill="x", pady=1)
            tk.Label(
                row,
                text=label,
                font=FONTS["small"],
                fg=COLORS["text_dim"],
                bg=COLORS["bg_card"],
            ).pack(side="left")
            lbl = tk.Label(
                row,
                text=default,
                font=FONTS["mono_sm"],
                fg=COLORS["text"],
                bg=COLORS["bg_card"],
            )
            lbl.pack(side="right")
            self._comms_labels[key] = lbl

        # Health dots row
        health_row = tk.Frame(frame, bg=COLORS["bg_card"])
        health_row.pack(fill="x", pady=(4, 0))
        tk.Label(
            health_row,
            text="Endpoints:",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
        ).pack(side="left")

        self._health_dots = {}
        for endpoint in ["blockstream", "eth_rpc", "bsc", "polygon"]:
            short = {
                "blockstream": "BTC",
                "eth_rpc": "ETH",
                "bsc": "BSC",
                "polygon": "POLY",
            }.get(endpoint, endpoint)
            dot_frame = tk.Frame(health_row, bg=COLORS["bg_card"])
            dot_frame.pack(side="left", padx=(4, 0))
            dot_label = tk.Label(
                dot_frame,
                text=f"\u25cf {short}",
                font=FONTS["body"],
                fg=COLORS["text_dim"],
                bg=COLORS["bg_card"],
            )
            dot_label.pack()
            self._health_dots[endpoint] = dot_label

        self._refresh_comms()

    # ═══ Public update methods (called from Hunter tab / main) ═══

    def update_puzzle_status(self, data):
        """Update puzzle mission status from Hunter tab callback."""
        mapping = {
            "status": data.get("status", ""),
            "puzzle": str(data.get("puzzle", "")),
            "strategy": data.get("strategy", ""),
            "keys": f"{data.get('keys_tested', 0):,}",
            "speed": f"{data.get('speed', 0):,.0f}/s",
            "best_score": (
                f"{data.get('best_score', 0):.3f}"
                if data.get("best_score")
                else "\u2014"
            ),
        }
        for k, v in mapping.items():
            if k in self._puzzle_labels:
                self._puzzle_labels[k].config(text=v)
                if k == "status":
                    color = COLORS["success"] if v == "Running" else COLORS["text"]
                    self._puzzle_labels[k].config(fg=color)

    def update_scanner_status(self, data):
        """Update scanner mission status from Hunter tab callback."""
        mapping = {
            "status": data.get("status", ""),
            "mode": data.get("mode", ""),
            "keys": f"{data.get('keys_tested', 0):,}",
            "seeds": f"{data.get('seeds_tested', 0):,}",
            "speed": f"{data.get('speed', 0):,.0f}/s",
            "hits": str(data.get("hits", 0)),
        }
        for k, v in mapping.items():
            if k in self._scanner_labels:
                self._scanner_labels[k].config(text=v)
                if k == "status":
                    color = COLORS["success"] if v == "Running" else COLORS["text"]
                    self._scanner_labels[k].config(fg=color)

    def update_live_activity(self, entry):
        """Add an entry to the live activity feed."""
        tag = "info"
        if entry.get("type") == "hit":
            tag = "success"
        elif entry.get("type") == "high_score":
            tag = "gold"
        elif entry.get("type") == "error":
            tag = "error"
        self.activity_log.log(entry.get("text", str(entry)), tag)

    def refresh_stats(self):
        """Refresh quick stats + comms from current app state."""
        if self.app and hasattr(self.app, "get_solver_stats"):
            stats = self.app.get_solver_stats()
            self._stat_labels["total_ops"].config(
                text=f"{stats.get('total_operations', 0):,}"
            )
            self._stat_labels["total_speed"].config(
                text=f"{stats.get('total_speed', 0):,.0f}/s"
            )

        try:
            from engines.learning import get_solve_stats, confidence_level

            ss = get_solve_stats()
            conf = confidence_level()
            self._stat_labels["learning"].config(text=f"{ss['total_attempts']} solves")
            bars = int(conf * 5)
            bar_str = "\u25a0" * bars + "\u25a1" * (5 - bars)
            self._stat_labels["confidence"].config(text=f"{bar_str} {conf:.0%}")
        except Exception:
            pass

        self._refresh_comms()

    # ═══ Internal refresh ═══

    def _refresh_moment(self):
        """Refresh the current FC60 moment display."""
        try:
            from engines.fc60 import encode_fc60, get_time_context

            now = datetime.now()
            result = encode_fc60(
                now.year, now.month, now.day, now.hour, now.minute, now.second
            )
            self.fc60_label.config(text=f"FC60: {result['stamp']}")
            self.moon_label.config(
                text=f"{result['moon_phase']} {result['moon_name']} "
                f"({result['moon_illumination']:.0f}%)"
            )
            self.gz_label.config(text=f"GZ: {result['gz_name']}")
            self.energy_label.config(
                text=f"{result['moon_meaning']}  |  {get_time_context(now.hour)}"
            )
        except Exception:
            self.fc60_label.config(text="FC60: (loading...)")

        self.refresh_stats()
        self._refresh_ai_brain()
        self.parent.after(60000, self._refresh_moment)

    def _refresh_ai_brain(self):
        """Show last AI insight or dash."""
        try:
            from engines.ai_engine import is_available, _last_insight

            if is_available():
                text = _last_insight if _last_insight else "\u2014"
                self._ai_label.config(text=text)
            else:
                self._ai_label.config(text="AI offline")
        except Exception:
            self._ai_label.config(text="\u2014")

    def _refresh_comms(self):
        """Refresh comms card: AI, Telegram, Memory, Health."""
        try:
            from engines.ai_engine import is_available

            self._comms_labels["ai"].config(
                text="ON" if is_available() else "OFF",
                fg=COLORS["success"] if is_available() else COLORS["text_dim"],
            )
        except Exception:
            pass

        try:
            from engines.notifier import is_configured

            self._comms_labels["telegram"].config(
                text="ON" if is_configured() else "OFF",
                fg=COLORS["success"] if is_configured() else COLORS["text_dim"],
            )
        except Exception:
            pass

        try:
            from engines.memory import get_summary

            summary = get_summary()
            self._comms_labels["memory"].config(
                text=f"{summary.get('total_sessions', 0)} sessions"
            )
        except Exception:
            pass

        # Health dots
        try:
            from engines.health import get_status

            status = get_status()
            for endpoint, dot_label in self._health_dots.items():
                info = status.get(endpoint)
                if info is None:
                    color = COLORS["text_dim"]  # gray = unchecked
                elif info.get("healthy"):
                    color = COLORS["success"]  # green
                else:
                    color = COLORS["error"]  # red
                short = {
                    "blockstream": "BTC",
                    "eth_rpc": "ETH",
                    "bsc": "BSC",
                    "polygon": "POLY",
                }.get(endpoint, endpoint)
                dot_label.config(text=f"\u25cf {short}", fg=color)
        except Exception:
            pass

    # ═══ Event Subscriptions ═══

    def _subscribe_events(self):
        """Subscribe to system events for live updates."""
        try:
            from engines import events

            events.subscribe(
                events.FINDING_FOUND, self._on_finding, gui_root=self.parent
            )
            events.subscribe(
                events.HEALTH_CHANGED, self._on_health_changed, gui_root=self.parent
            )
            events.subscribe(events.LEVEL_UP, self._on_level_up, gui_root=self.parent)
            events.subscribe(
                events.TERMINAL_STATUS_CHANGED,
                self._on_terminal_change,
                gui_root=self.parent,
            )
        except Exception:
            pass

    def _on_finding(self, data):
        """Handle FINDING_FOUND event."""
        addr = data.get("address", "")[:24]
        chain = data.get("chain", "?")
        self.activity_log.log(f"FINDING: {chain.upper()} balance at {addr}", "success")

    def _on_health_changed(self, data):
        """Handle HEALTH_CHANGED event — update health dot color."""
        endpoint = data.get("endpoint")
        healthy = data.get("healthy")
        if endpoint and endpoint in self._health_dots:
            color = COLORS["success"] if healthy else COLORS["error"]
            short = {
                "blockstream": "BTC",
                "eth_rpc": "ETH",
                "bsc": "BSC",
                "polygon": "POLY",
            }.get(endpoint, endpoint)
            self._health_dots[endpoint].config(text=f"\u25cf {short}", fg=color)

    def _on_level_up(self, data):
        """Handle LEVEL_UP event."""
        name = data.get("name", "?")
        new_level = data.get("new_level", "?")
        self.activity_log.log(f"LEVEL UP! Now Level {new_level} — {name}", "gold")
        # Update AI brain label
        self._ai_label.config(text=f"AI Level {new_level}: {name}")

    def _on_terminal_change(self, data):
        """Handle TERMINAL_STATUS_CHANGED event — refresh terminal cards."""
        self._refresh_terminals()

    def _start_stats_poll(self):
        """Poll terminal stats every 1 second for live dashboard updates."""
        try:
            from engines.terminal_manager import get_all_stats, get_active_count

            all_stats = get_all_stats()
            total_ops = 0
            total_speed = 0
            for tid, stats in all_stats.items():
                if stats:
                    total_ops += stats.get("keys_tested", 0)
                    total_speed += stats.get("speed", 0)

            self._stat_labels["total_ops"].config(text=f"{total_ops:,}")
            self._stat_labels["total_speed"].config(text=f"{total_speed:,.0f}/s")
        except Exception:
            pass

        self.parent.after(1000, self._start_stats_poll)
