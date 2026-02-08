"""Hunter tab — unified BTC Puzzle + Scanner mission control."""

import time
import tkinter as tk
from tkinter import ttk
from gui.theme import COLORS, FONTS, CURRENCY_SYMBOLS
from gui.widgets import (
    StyledButton,
    StatsCard,
    LogPanel,
    AIInsightPanel,
    HighScoreAlertPanel,
    AnimatedProgress,
    ThrottledUpdater,
    LiveFeedTable,
)


class HunterTab:
    """Combined puzzle solver + multi-chain scanner in one tab."""

    def __init__(self, parent, app=None):
        self.parent = parent
        self.app = app
        self._puzzle_solver = None
        self._scanner_solver = None
        self._puzzle_terminal_id = None
        self._scanner_terminal_id = None
        self._build_ui()

    def _build_ui(self):
        main = tk.Frame(self.parent, bg=COLORS["bg"], padx=12, pady=8)
        main.pack(fill="both", expand=True)

        # Header
        tk.Label(
            main,
            text="Hunter",
            font=FONTS["heading"],
            fg=COLORS["accent"],
            bg=COLORS["bg"],
        ).pack(anchor="w", pady=(0, 6))

        # Top row: Puzzle controls | Scanner controls
        top = tk.Frame(main, bg=COLORS["bg"])
        top.pack(fill="x", pady=(0, 6))
        self._build_puzzle_controls(top)
        self._build_scanner_controls(top)

        # Middle: Stats row
        stats_row = tk.Frame(main, bg=COLORS["bg"])
        stats_row.pack(fill="x", pady=(0, 6))
        self._build_puzzle_stats(stats_row)
        self._build_scanner_stats(stats_row)

        # Live Feed (unified)
        tk.Label(
            main,
            text="Live Feed",
            font=FONTS["subhead"],
            fg=COLORS["text"],
            bg=COLORS["bg"],
        ).pack(anchor="w", pady=(4, 2))
        self._feed_parent = main
        self._feed_bottom = None  # set after bottom frame is packed
        self._scanner_feed_cols = []  # track active scanner columns
        self._default_feed_cols = (
            "Time",
            "Source",
            "Key/Seed",
            "\u20bf BTC",
            "\u039e ETH",
            "Score",
        )
        self._default_feed_widths = (70, 80, 140, 180, 180, 60)
        self.feed = LiveFeedTable(
            main,
            columns=self._default_feed_cols,
            col_widths=self._default_feed_widths,
            height=10,
        )
        self.feed.pack(fill="both", expand=True, pady=(0, 6))

        # Bottom: High Score Alert + AI Insight
        bottom = tk.Frame(main, bg=COLORS["bg"])
        bottom.pack(fill="x")
        self._feed_bottom = bottom
        self.high_score_panel = HighScoreAlertPanel(bottom)
        self.high_score_panel.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.ai_panel = AIInsightPanel(bottom, title="AI Insight")
        self.ai_panel.pack(side="left", fill="both", expand=True, padx=(4, 0))
        self.ai_panel.set_unavailable()

        # Throttled updaters
        self._feed_updater = ThrottledUpdater(self.parent, min_interval_ms=100)
        self._puzzle_stats_updater = ThrottledUpdater(self.parent, min_interval_ms=500)
        self._scanner_stats_updater = ThrottledUpdater(self.parent, min_interval_ms=500)

    # ─── Puzzle Controls ───
    def _build_puzzle_controls(self, parent):
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

        # Puzzle selector
        row1 = tk.Frame(frame, bg=COLORS["bg_card"])
        row1.pack(fill="x", pady=2)
        tk.Label(
            row1,
            text="Puzzle:",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
        ).pack(side="left")

        self._puzzle_var = tk.StringVar(value="66")
        puzzle_options = [
            "20",
            "25",
            "30",
            "35",
            "40",
            "45",
            "50",
            "55",
            "60",
            "65",
            "66",
            "67",
            "68",
            "69",
            "70",
            "75",
            "80",
            "85",
            "90",
            "95",
            "100",
            "105",
            "110",
            "115",
            "120",
            "125",
            "130",
        ]
        self._puzzle_combo = ttk.Combobox(
            row1,
            textvariable=self._puzzle_var,
            values=puzzle_options,
            width=8,
            state="readonly",
        )
        self._puzzle_combo.pack(side="left", padx=(8, 0))

        # Strategy selector
        tk.Label(
            row1,
            text="Strategy:",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
        ).pack(side="left", padx=(12, 0))

        self._strategy_var = tk.StringVar(value="hybrid")
        for strat in ["random", "mystic", "hybrid", "oracle"]:
            tk.Radiobutton(
                row1,
                text=strat.capitalize(),
                variable=self._strategy_var,
                value=strat,
                font=FONTS["small"],
                fg=COLORS["text"],
                bg=COLORS["bg_card"],
                selectcolor=COLORS["bg_input"],
                activebackground=COLORS["bg_card"],
            ).pack(side="left", padx=2)

        # Buttons
        row2 = tk.Frame(frame, bg=COLORS["bg_card"])
        row2.pack(fill="x", pady=(4, 0))
        self._puzzle_start_btn = StyledButton(
            row2,
            text="Start Puzzle",
            command=self._start_puzzle,
            bg=COLORS["bg_success"],
            fg="white",
            font=FONTS["small"],
            padx=12,
            pady=4,
            tooltip="Start solving the selected puzzle number",
        )
        self._puzzle_start_btn.pack(side="left", padx=(0, 4))
        self._puzzle_stop_btn = StyledButton(
            row2,
            text="Stop",
            command=self._stop_puzzle,
            bg=COLORS["bg_danger"],
            fg="white",
            font=FONTS["small"],
            padx=12,
            pady=4,
            state="disabled",
            tooltip="Stop the puzzle solver",
        )
        self._puzzle_stop_btn.pack(side="left")

    # ─── Scanner Controls ───
    def _build_scanner_controls(self, parent):
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

        row1 = tk.Frame(frame, bg=COLORS["bg_card"])
        row1.pack(fill="x", pady=2)
        tk.Label(
            row1,
            text="Mode:",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
        ).pack(side="left")

        self._scan_mode_var = tk.StringVar(value="both")
        for mode in ["random", "bip39", "both"]:
            tk.Radiobutton(
                row1,
                text=mode.capitalize(),
                variable=self._scan_mode_var,
                value=mode,
                font=FONTS["small"],
                fg=COLORS["text"],
                bg=COLORS["bg_card"],
                selectcolor=COLORS["bg_input"],
                activebackground=COLORS["bg_card"],
            ).pack(side="left", padx=4)

        self._scan_balance_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            row1,
            text="Online balance",
            variable=self._scan_balance_var,
            font=FONTS["small"],
            fg=COLORS["text"],
            bg=COLORS["bg_card"],
            selectcolor=COLORS["bg_input"],
            activebackground=COLORS["bg_card"],
        ).pack(side="left", padx=(12, 0))

        # Chain / token selection row
        chain_row = tk.Frame(frame, bg=COLORS["bg_card"])
        chain_row.pack(fill="x", pady=2)
        tk.Label(
            chain_row,
            text="Chains:",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
        ).pack(side="left")

        self._chain_vars = {}
        chain_defs = [
            ("btc", "BTC", True),
            ("eth", "ETH", True),
            ("usdt", "USDT", False),
            ("usdc", "USDC", False),
            ("dai", "DAI", False),
            ("wbtc", "WBTC", False),
        ]
        for key, label, default_on in chain_defs:
            var = tk.BooleanVar(value=default_on)
            self._chain_vars[key] = var
            color = CURRENCY_SYMBOLS.get(label, {}).get("color", COLORS["text"])
            tk.Checkbutton(
                chain_row,
                text=label,
                variable=var,
                font=FONTS["small"],
                fg=color,
                bg=COLORS["bg_card"],
                selectcolor=COLORS["bg_input"],
                activebackground=COLORS["bg_card"],
            ).pack(side="left", padx=3)

        row2 = tk.Frame(frame, bg=COLORS["bg_card"])
        row2.pack(fill="x", pady=(4, 0))
        self._scan_start_btn = StyledButton(
            row2,
            text="Start Scanner",
            command=self._start_scanner,
            bg=COLORS["bg_success"],
            fg="white",
            font=FONTS["small"],
            padx=12,
            pady=4,
            tooltip="Start scanning with selected chains and mode",
        )
        self._scan_start_btn.pack(side="left", padx=(0, 4))
        self._scan_stop_btn = StyledButton(
            row2,
            text="Stop",
            command=self._stop_scanner,
            bg=COLORS["bg_danger"],
            fg="white",
            font=FONTS["small"],
            padx=12,
            pady=4,
            state="disabled",
            tooltip="Stop the scanner",
        )
        self._scan_stop_btn.pack(side="left")

    # ─── Puzzle Stats ───
    def _build_puzzle_stats(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="  Puzzle Stats  ",
            font=FONTS["body"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            bd=1,
            relief="solid",
            padx=12,
            pady=4,
        )
        frame.pack(side="left", fill="both", expand=True, padx=(0, 4))

        self._pstat_labels = {}
        for key, label in [
            ("keys", "Keys:"),
            ("speed", "Speed:"),
            ("best", "Best Score:"),
            ("progress", "Progress:"),
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
                text="0",
                font=FONTS["mono_sm"],
                fg=COLORS["text"],
                bg=COLORS["bg_card"],
            )
            lbl.pack(side="right")
            self._pstat_labels[key] = lbl

    # ─── Scanner Stats ───
    def _build_scanner_stats(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="  Scanner Stats  ",
            font=FONTS["body"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            bd=1,
            relief="solid",
            padx=12,
            pady=4,
        )
        frame.pack(side="left", fill="both", expand=True, padx=(4, 0))

        self._sstat_labels = {}
        for key, label in [
            ("keys", "Keys:"),
            ("seeds", "Seeds:"),
            ("speed", "Speed:"),
            ("hits", "Hits:"),
            ("strategy", "Strategy:"),
            ("patterns", "Patterns:"),
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
                text="0",
                font=FONTS["mono_sm"],
                fg=COLORS["text"],
                bg=COLORS["bg_card"],
            )
            lbl.pack(side="right")
            self._sstat_labels[key] = lbl

    # ═══ Puzzle solver control ═══

    def _start_puzzle(self):
        if self._puzzle_terminal_id:
            return
        try:
            from engines.terminal_manager import create_terminal, start_terminal
            from engines.session_manager import start_session
            from engines.events import emit, SCAN_STARTED

            puzzle_num = int(self._puzzle_var.get())
            strategy = self._strategy_var.get()

            settings = {
                "mode": "random_key",
                "puzzle_enabled": True,
                "puzzle_number": puzzle_num,
                "strategy": strategy,
                "chains": ["btc"],
                "tokens": [],
                "online_check": False,
                "use_brain": False,
                "callback": self._puzzle_callback,
            }

            tid = create_terminal(settings)
            if not tid:
                self._log_activity("Max terminals reached", "error")
                return

            self._puzzle_terminal_id = tid
            start_terminal(tid)

            try:
                start_session(tid, settings)
            except Exception:
                pass

            self._puzzle_start_btn.config(state="disabled")
            self._puzzle_stop_btn.config(state="normal")

            emit(
                SCAN_STARTED,
                {"terminal_id": tid, "type": "puzzle", "puzzle": puzzle_num},
            )

            self._notify_dashboard(
                "puzzle",
                {
                    "status": "Running",
                    "puzzle": puzzle_num,
                    "strategy": strategy,
                    "keys_tested": 0,
                    "speed": 0,
                    "best_score": 0,
                },
            )
        except Exception as e:
            self._log_activity(f"Puzzle start error: {e}", "error")

    def _stop_puzzle(self):
        if self._puzzle_terminal_id:
            try:
                from engines.terminal_manager import (
                    stop_terminal,
                    get_terminal_stats,
                    remove_terminal,
                )
                from engines.session_manager import end_session
                from engines.learner import add_xp
                from engines.events import emit, SCAN_STOPPED

                stats = get_terminal_stats(self._puzzle_terminal_id) or {}
                stop_terminal(self._puzzle_terminal_id)

                try:
                    end_session(self._puzzle_terminal_id, stats)
                except Exception:
                    pass

                try:
                    keys = stats.get("keys_tested", 0)
                    xp = max(1, keys // 10000)
                    add_xp(xp, "puzzle_session")
                except Exception:
                    pass

                # Record to legacy memory
                try:
                    from engines.memory import record_session

                    record_session(
                        {
                            "mode": "puzzle",
                            "puzzle": int(self._puzzle_var.get()),
                            "strategy": self._strategy_var.get(),
                            "keys_tested": stats.get("keys_tested", 0),
                            "best_score": stats.get("high_score", 0),
                            "duration": stats.get("elapsed", 0),
                        }
                    )
                except Exception:
                    pass

                try:
                    remove_terminal(self._puzzle_terminal_id)
                except Exception:
                    pass

                emit(
                    SCAN_STOPPED,
                    {"terminal_id": self._puzzle_terminal_id, "type": "puzzle"},
                )
            except Exception:
                pass

            self._puzzle_terminal_id = None

        # Also stop legacy solver if active
        if self._puzzle_solver:
            self._puzzle_solver.stop()
            if self.app:
                self.app.unregister_solver_v2(self._puzzle_solver)
            self._puzzle_solver = None

        self._puzzle_start_btn.config(state="normal")
        self._puzzle_stop_btn.config(state="disabled")
        self._notify_dashboard("puzzle", {"status": "Stopped"})

    def _puzzle_callback(self, data):
        """Called from solver thread — schedule GUI update."""
        self.parent.after(0, self._handle_puzzle_data, data)

    def _handle_puzzle_data(self, data):
        """Process puzzle solver data on main thread."""

        # Update stats (throttled)
        def _update_stats():
            self._pstat_labels["keys"].config(text=f"{data.get('keys_tested', 0):,}")
            self._pstat_labels["speed"].config(text=f"{data.get('speed', 0):,.0f}/s")
            self._pstat_labels["best"].config(text=f"{data.get('best_score', 0):.3f}")
            prog = data.get("progress", 0)
            self._pstat_labels["progress"].config(text=f"{prog:.1f}%")

        self._puzzle_stats_updater.maybe_update(_update_stats)

        # Feed entry (throttled)
        def _update_feed():
            key_hex = data.get("key", "")[:16]
            btc_addr = data.get("address", "")[:24]
            eth_addr = data.get("eth_address", "")[:24]
            score = data.get("score", 0)
            ts = time.strftime("%H:%M:%S")
            tag = "high_score" if score >= 0.7 else "normal"
            self.feed.insert_row(
                (
                    ts,
                    f"P#{data.get('puzzle_number', '?')}",
                    key_hex,
                    btc_addr,
                    eth_addr,
                    f"{score:.2f}",
                ),
                tag=tag,
            )

        self._feed_updater.maybe_update(_update_feed)

        # Dashboard update
        self._notify_dashboard(
            "puzzle",
            {
                "status": "Running",
                "puzzle": data.get("puzzle_number"),
                "strategy": data.get("strategy"),
                "keys_tested": data.get("keys_tested", 0),
                "speed": data.get("speed", 0),
                "best_score": data.get("best_score", 0),
            },
        )

        # High score alert + memory recording
        score = data.get("score", 0)
        if score >= 0.7:
            self.high_score_panel.show_alert(data)
            self._log_activity(
                f"High score! {score:.3f} key={data.get('key', '')[:20]}",
                "gold",
            )
            try:
                from engines.memory import record_high_score

                record_high_score(
                    key_hex=data.get("key", ""),
                    score=score,
                    addresses=[data.get("address", ""), data.get("eth_address", "")],
                )
            except Exception:
                pass

        # Check if solver stopped
        if data.get("status") == "stopped":
            self._stop_puzzle()

    # ═══ Scanner control ═══

    def _start_scanner(self):
        if self._scanner_terminal_id:
            return
        try:
            from engines.terminal_manager import create_terminal, start_terminal
            from engines.session_manager import start_session
            from engines.events import emit, SCAN_STARTED

            mode = self._scan_mode_var.get()
            # Map UI mode names to UnifiedSolver mode names
            mode_map = {"random": "random_key", "bip39": "seed_phrase", "both": "both"}
            solver_mode = mode_map.get(mode, mode)
            balance = self._scan_balance_var.get()

            selected_chains = [
                c
                for c, v in self._chain_vars.items()
                if v.get() and c in ("btc", "eth")
            ]
            selected_tokens = [
                c.upper()
                for c, v in self._chain_vars.items()
                if v.get() and c not in ("btc", "eth")
            ]

            if not selected_chains:
                self._log_activity("Select at least one chain (BTC or ETH)", "error")
                return

            self._rebuild_feed_table(selected_chains, selected_tokens)

            settings = {
                "mode": solver_mode,
                "puzzle_enabled": False,
                "chains": selected_chains,
                "tokens": selected_tokens,
                "online_check": balance,
                "use_brain": True,
                "callback": self._scanner_callback,
            }

            tid = create_terminal(settings)
            if not tid:
                self._log_activity("Max terminals reached", "error")
                return

            self._scanner_terminal_id = tid
            start_terminal(tid)

            try:
                start_session(tid, settings)
            except Exception:
                pass

            self._scan_start_btn.config(state="disabled")
            self._scan_stop_btn.config(state="normal")

            emit(
                SCAN_STARTED,
                {"terminal_id": tid, "type": "scanner", "mode": solver_mode},
            )

            self._notify_dashboard(
                "scanner",
                {
                    "status": "Running",
                    "mode": mode,
                    "keys_tested": 0,
                    "seeds_tested": 0,
                    "speed": 0,
                    "hits": 0,
                },
            )
        except Exception as e:
            self._log_activity(f"Scanner start error: {e}", "error")

    def _stop_scanner(self):
        if self._scanner_terminal_id:
            try:
                from engines.terminal_manager import (
                    stop_terminal,
                    get_terminal_stats,
                    remove_terminal,
                )
                from engines.session_manager import end_session
                from engines.learner import add_xp
                from engines.events import emit, SCAN_STOPPED

                stats = get_terminal_stats(self._scanner_terminal_id) or {}
                stop_terminal(self._scanner_terminal_id)

                try:
                    end_session(self._scanner_terminal_id, stats)
                except Exception:
                    pass

                try:
                    keys = stats.get("keys_tested", 0)
                    xp = max(1, keys // 10000)
                    add_xp(xp, "scanner_session")
                except Exception:
                    pass

                # Record to legacy memory
                try:
                    from engines.memory import record_session

                    record_session(
                        {
                            "mode": "scanner",
                            "puzzle": 0,
                            "strategy": self._scan_mode_var.get(),
                            "keys_tested": stats.get("keys_tested", 0),
                            "best_score": 0,
                            "duration": stats.get("elapsed", 0),
                        }
                    )
                except Exception:
                    pass

                try:
                    remove_terminal(self._scanner_terminal_id)
                except Exception:
                    pass

                emit(
                    SCAN_STOPPED,
                    {"terminal_id": self._scanner_terminal_id, "type": "scanner"},
                )
            except Exception:
                pass

            self._scanner_terminal_id = None

        # Also stop legacy solver if active
        if self._scanner_solver:
            self._scanner_solver.stop()
            if self.app:
                self.app.unregister_solver_v2(self._scanner_solver)
            self._scanner_solver = None

        self._scan_start_btn.config(state="normal")
        self._scan_stop_btn.config(state="disabled")
        self._rebuild_feed_table()  # restore default columns
        self._notify_dashboard("scanner", {"status": "Stopped"})

    def _scanner_callback(self, data):
        """Called from scanner thread."""
        self.parent.after(0, self._handle_scanner_data, data)

    def _handle_scanner_data(self, data):
        """Process scanner data on main thread."""

        # Handle brain events
        if data.get("status") == "brain_strategy":
            brain_status = data.get("brain_status", {})
            self._sstat_labels["strategy"].config(
                text=brain_status.get("strategy", "-")
            )
            self._sstat_labels["patterns"].config(text="0")
            # Activate AI panel for brain
            if brain_status.get("ai_recommendation"):
                self.ai_panel.set_result(brain_status["ai_recommendation"])
            return

        if data.get("status") == "brain_insight":
            insight = data.get("brain_insight", {})
            self.ai_panel.set_result(insight.get("recommendation", ""))
            return

        if data.get("status") == "brain_summary":
            summary = data.get("brain_summary", {})
            recs = summary.get("next_recommendations", [])
            text = recs[0] if recs else summary.get("session_summary", "")
            self.ai_panel.set_result(text)
            return

        def _update_stats():
            self._sstat_labels["keys"].config(text=f"{data.get('keys_tested', 0):,}")
            self._sstat_labels["seeds"].config(text=f"{data.get('seeds_tested', 0):,}")
            self._sstat_labels["speed"].config(text=f"{data.get('speed', 0):,.0f}/s")
            self._sstat_labels["hits"].config(text=str(data.get("hits", 0)))

        self._scanner_stats_updater.maybe_update(_update_stats)

        def _update_feed():
            feed = data.get("live_feed", [])
            if not feed:
                return
            entry = feed[-1]
            addrs = entry.get("addresses", {})
            balances = entry.get("balances", {})
            src = entry.get("source", "scan")[:12]
            ts = time.strftime("%H:%M:%S")
            tag = "hit" if entry.get("has_balance") else "dim"

            # Key/Seed: show mnemonic snippet for seeds, key hex for random
            if entry.get("type") == "seed" and entry.get("mnemonic"):
                words = entry["mnemonic"].split()[:3]
                key_seed = " ".join(words) + "..."
            else:
                key_seed = entry.get("key_hex", "")[:20]

            # Build dynamic columns matching _scanner_feed_cols
            row = [ts, src, key_seed]
            for col_type, col_key in self._scanner_feed_cols:
                if col_type == "chain":
                    row.append(addrs.get(col_key, "-")[:24])
                elif col_type == "token":
                    # Show token balance if online check was done, else ETH addr
                    tok_data = balances.get("tokens", {}).get(col_key.upper(), {})
                    if tok_data.get("balance"):
                        row.append(str(tok_data["balance"]))
                    elif entry.get("checked_online"):
                        row.append("0")
                    else:
                        row.append(addrs.get("eth", "-")[:20])

            # Balance column — summarize all available balance info
            if entry.get("has_balance") and not entry.get("checked_online"):
                bal_text = "Rich list!"
            elif entry.get("checked_online") and balances:
                parts = []
                history_parts = []
                btc_bal = balances.get("btc", {})
                if btc_bal and btc_bal.get("success"):
                    if btc_bal.get("balance_btc"):
                        parts.append(f"BTC:{btc_bal['balance_btc']:.8f}")
                    if btc_bal.get("has_history"):
                        tx = btc_bal.get("tx_count", 0)
                        funded = btc_bal.get("funded_sum_sat", 0) / 1e8
                        history_parts.append(f"BTC:{tx}tx/${funded:.4f}")
                eth_bal = balances.get("eth", {})
                if eth_bal and eth_bal.get("success"):
                    if eth_bal.get("balance_eth"):
                        parts.append(f"ETH:{eth_bal['balance_eth']:.6f}")
                for tok_name, tok_data in balances.get("tokens", {}).items():
                    if tok_data.get("balance"):
                        parts.append(f"{tok_name}:{tok_data['balance']}")
                if parts:
                    bal_text = " | ".join(parts)
                elif history_parts:
                    bal_text = "$0 (" + ", ".join(history_parts) + ")"
                else:
                    bal_text = "$0"
            else:
                bal_text = "$0"
            row.append(bal_text)

            self.feed.insert_row(tuple(row), tag=tag)

        self._feed_updater.maybe_update(_update_feed)

        self._notify_dashboard(
            "scanner",
            {
                "status": "Running",
                "mode": self._scan_mode_var.get(),
                "keys_tested": data.get("keys_tested", 0),
                "seeds_tested": data.get("seeds_tested", 0),
                "speed": data.get("speed", 0),
                "hits": data.get("hits", 0),
            },
        )

        for entry in data.get("live_feed", []):
            if entry.get("has_balance"):
                addrs = entry.get("addresses", {})
                self._log_activity(
                    f"BALANCE FOUND! BTC:{addrs.get('btc', '')} ETH:{addrs.get('eth', '')}",
                    "success",
                )

    # ═══ Helpers ═══

    def _rebuild_feed_table(self, selected_chains=None, selected_tokens=None):
        """Destroy and recreate the LiveFeedTable with columns matching selection.

        When called with no args (or None), restores the default puzzle columns.
        """
        self.feed.pack_forget()
        self.feed.destroy()

        if selected_chains is None:
            # Default / puzzle mode
            cols = self._default_feed_cols
            widths = self._default_feed_widths
            self._scanner_feed_cols = []
        else:
            # Build dynamic columns: Time, Source, Key/Seed, then one per chain/token
            cols = ["Time", "Source", "Key/Seed"]
            widths = [70, 80, 140]
            col_keys = []  # parallel list to track what each column maps to

            for chain in selected_chains:
                sym = CURRENCY_SYMBOLS.get(chain.upper(), {}).get(
                    "symbol", chain.upper()
                )
                cols.append(f"{sym} {chain.upper()}")
                widths.append(180)
                col_keys.append(("chain", chain))

            for token in selected_tokens or []:
                sym = CURRENCY_SYMBOLS.get(token.upper(), {}).get(
                    "symbol", token.upper()
                )
                cols.append(f"{sym} {token.upper()}")
                widths.append(140)
                col_keys.append(("token", token))

            cols.append("Balance")
            widths.append(120)

            cols = tuple(cols)
            widths = tuple(widths)
            self._scanner_feed_cols = col_keys

        self.feed = LiveFeedTable(
            self._feed_parent,
            columns=cols,
            col_widths=widths,
            height=10,
        )
        # Pack before the bottom frame
        self.feed.pack(fill="both", expand=True, pady=(0, 6), before=self._feed_bottom)

    def _notify_dashboard(self, mission_type, data):
        """Push status to dashboard if available."""
        if not self.app or not hasattr(self.app, "dashboard"):
            return
        try:
            if mission_type == "puzzle":
                self.app.dashboard.update_puzzle_status(data)
            else:
                self.app.dashboard.update_scanner_status(data)
        except Exception:
            pass

    def _log_activity(self, text, tag="info"):
        """Log to dashboard's live activity."""
        if self.app and hasattr(self.app, "dashboard"):
            try:
                self.app.dashboard.update_live_activity(
                    {
                        "text": text,
                        "type": tag,
                    }
                )
            except Exception:
                pass

    def stop_all(self):
        """Stop all active missions (called on app close)."""
        # Stop terminal-managed solvers
        if self._puzzle_terminal_id:
            try:
                from engines.terminal_manager import stop_terminal

                stop_terminal(self._puzzle_terminal_id)
            except Exception:
                pass
            self._puzzle_terminal_id = None
        if self._scanner_terminal_id:
            try:
                from engines.terminal_manager import stop_terminal

                stop_terminal(self._scanner_terminal_id)
            except Exception:
                pass
            self._scanner_terminal_id = None
        # Stop legacy solvers
        if self._puzzle_solver and self._puzzle_solver.running:
            self._puzzle_solver.stop()
        if self._scanner_solver and self._scanner_solver.running:
            self._scanner_solver.stop()
