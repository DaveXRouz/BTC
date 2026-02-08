"""Memory tab — AI Learning Dashboard."""

import csv
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime
from gui.theme import COLORS, FONTS
from gui.widgets import StyledButton, StatsCard, AIInsightPanel


class MemoryTab:
    """Displays scan memory, learning stats, recommendations."""

    def __init__(self, parent, app=None):
        self.parent = parent
        self.app = app
        self._build_ui()
        self._subscribe_events()
        self._refresh()

    def _build_ui(self):
        main = tk.Frame(self.parent, bg=COLORS["bg"], padx=12, pady=8)
        main.pack(fill="both", expand=True)

        tk.Label(
            main,
            text="Memory",
            font=FONTS["heading"],
            fg=COLORS["accent"],
            bg=COLORS["bg"],
        ).pack(anchor="w", pady=(0, 6))

        # Row 0: XP / Level display
        level_frame = tk.LabelFrame(
            main,
            text="  AI Level  ",
            font=FONTS["body"],
            fg=COLORS["ai_accent"],
            bg=COLORS["ai_bg"],
            bd=1,
            relief="solid",
            padx=12,
            pady=6,
        )
        level_frame.pack(fill="x", pady=(0, 8))
        level_frame.configure(
            highlightbackground=COLORS["ai_border"], highlightthickness=1
        )

        level_info_row = tk.Frame(level_frame, bg=COLORS["ai_bg"])
        level_info_row.pack(fill="x")

        self._level_name_label = tk.Label(
            level_info_row,
            text="Level 1 — Novice",
            font=FONTS["subhead"],
            fg=COLORS["ai_text"],
            bg=COLORS["ai_bg"],
        )
        self._level_name_label.pack(side="left")

        self._xp_label = tk.Label(
            level_info_row,
            text="XP: 0",
            font=FONTS["mono_sm"],
            fg=COLORS["ai_text"],
            bg=COLORS["ai_bg"],
        )
        self._xp_label.pack(side="right")

        # XP progress bar
        self._xp_bar = tk.Canvas(
            level_frame, height=12, bg=COLORS["bg_input"], highlightthickness=0
        )
        self._xp_bar.pack(fill="x", pady=(4, 2))

        self._capabilities_label = tk.Label(
            level_frame,
            text="",
            font=FONTS["small"],
            fg=COLORS["ai_text"],
            bg=COLORS["ai_bg"],
            anchor="w",
        )
        self._capabilities_label.pack(fill="x")

        # Row 1: Lifetime Stats cards
        stats_row = tk.Frame(main, bg=COLORS["bg"])
        stats_row.pack(fill="x", pady=(0, 8))

        self._cards = {}
        for key, title in [
            ("sessions", "Sessions"),
            ("keys", "Keys Tested"),
            ("high_scores", "High Scores"),
            ("best", "Best Score"),
            ("avg_speed", "Avg Speed"),
            ("duration", "Total Time"),
        ]:
            card = StatsCard(stats_row, title=title, value="0")
            card.pack(side="left", fill="both", expand=True, padx=2)
            self._cards[key] = card

        # Row 2: Scoring + Patterns | Recommendations
        row2 = tk.Frame(main, bg=COLORS["bg"])
        row2.pack(fill="both", expand=True, pady=(0, 8))

        # Left: Scoring Effectiveness + Pattern Memory
        left = tk.Frame(row2, bg=COLORS["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self._build_scoring_panel(left)
        self._build_patterns_panel(left)

        # Right: Recommendations + Controls
        right = tk.Frame(row2, bg=COLORS["bg"])
        right.pack(side="left", fill="both", expand=True, padx=(4, 0))
        self._build_recommendations_panel(right)
        self._build_controls(right)

    # ─── Scoring Effectiveness ───
    def _build_scoring_panel(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="  Scoring Effectiveness  ",
            font=FONTS["body"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            bd=1,
            relief="solid",
            padx=12,
            pady=6,
        )
        frame.pack(fill="x", pady=(0, 6))

        self._scoring_labels = {}
        for key, label, default in [
            ("attempts", "Total Attempts:", "0"),
            ("correct", "Solved:", "0"),
            ("success_rate", "Success Rate:", "0%"),
            ("avg_winner", "Avg Winner Score:", "\u2014"),
            ("best_type", "Best Puzzle Type:", "\u2014"),
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
            self._scoring_labels[key] = lbl

        # Weight display
        tk.Label(
            frame,
            text="Factor Weights:",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
        ).pack(anchor="w", pady=(4, 0))

        self._weight_labels = {}
        for key, label in [
            ("math", "Math:"),
            ("numer", "Numerology:"),
            ("learn", "Learned:"),
        ]:
            row = tk.Frame(frame, bg=COLORS["bg_card"])
            row.pack(fill="x", pady=1)
            tk.Label(
                row,
                text=label,
                font=FONTS["small"],
                fg=COLORS["text_dim"],
                bg=COLORS["bg_card"],
                width=14,
                anchor="e",
            ).pack(side="left")
            lbl = tk.Label(
                row,
                text="\u2014",
                font=FONTS["mono_sm"],
                fg=COLORS["text"],
                bg=COLORS["bg_card"],
            )
            lbl.pack(side="right")
            self._weight_labels[key] = lbl

    # ─── Pattern Memory ───
    def _build_patterns_panel(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="  Scan Memory Timeline  ",
            font=FONTS["body"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            bd=1,
            relief="solid",
            padx=8,
            pady=4,
        )
        frame.pack(fill="both", expand=True)

        self._sessions_listbox = tk.Listbox(
            frame,
            font=FONTS["mono_sm"],
            bg=COLORS["bg_card"],
            fg=COLORS["text"],
            selectbackground=COLORS["bg_hover"],
            height=8,
            bd=0,
        )
        self._sessions_listbox.pack(fill="both", expand=True)

    # ─── Recommendations ───
    def _build_recommendations_panel(self, parent):
        self.ai_panel = AIInsightPanel(parent, title="AI Recommendations")
        self.ai_panel.pack(fill="x", pady=(0, 6))
        self.ai_panel.set_result("Loading recommendations...")

    # ─── Controls ───
    def _build_controls(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="  Controls  ",
            font=FONTS["body"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            bd=1,
            relief="solid",
            padx=12,
            pady=8,
        )
        frame.pack(fill="x", pady=(0, 6))

        # Model dropdown
        model_row = tk.Frame(frame, bg=COLORS["bg_card"])
        model_row.pack(fill="x", pady=2)
        tk.Label(
            model_row,
            text="AI Model:",
            font=FONTS["small"],
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
        ).pack(side="left")
        self._model_var = tk.StringVar(value="sonnet")
        model_combo = ttk.Combobox(
            model_row,
            textvariable=self._model_var,
            values=["haiku", "sonnet", "opus"],
            state="readonly",
            width=10,
            font=FONTS["small"],
        )
        model_combo.pack(side="left", padx=(4, 0))

        # Learn Now button
        self._learn_btn = StyledButton(
            frame,
            text="Learn Now",
            command=self._learn_now,
            bg=COLORS["ai_accent"],
            fg="white",
            font=FONTS["small"],
            padx=10,
            pady=4,
            tooltip="Trigger AI learning from scan data",
        )
        self._learn_btn.pack(fill="x", pady=2)

        StyledButton(
            frame,
            text="Recalculate Weights",
            command=self._recalculate,
            bg=COLORS["bg_button"],
            fg="white",
            font=FONTS["small"],
            padx=10,
            pady=4,
            tooltip="Recalculate scoring factor weights from data",
        ).pack(fill="x", pady=2)

        StyledButton(
            frame,
            text="Export Memory CSV",
            command=self._export_csv,
            bg=COLORS["bg_button"],
            fg="white",
            font=FONTS["small"],
            padx=10,
            pady=4,
            tooltip="Export scan memory sessions to CSV file",
        ).pack(fill="x", pady=2)

        StyledButton(
            frame,
            text="Export Vault CSV",
            command=self._export_vault_csv,
            bg=COLORS["bg_button"],
            fg="white",
            font=FONTS["small"],
            padx=10,
            pady=4,
            tooltip="Export vault findings to CSV file",
        ).pack(fill="x", pady=2)

        StyledButton(
            frame,
            text="Export Vault JSON",
            command=self._export_vault_json,
            bg=COLORS["bg_button"],
            fg="white",
            font=FONTS["small"],
            padx=10,
            pady=4,
            tooltip="Export vault findings to JSON file",
        ).pack(fill="x", pady=2)

        StyledButton(
            frame,
            text="Flush Memory to Disk",
            command=self._flush,
            bg=COLORS["bg_button"],
            fg="white",
            font=FONTS["small"],
            padx=10,
            pady=4,
            tooltip="Force write all memory data to disk",
        ).pack(fill="x", pady=2)

        StyledButton(
            frame,
            text="Refresh",
            command=self._refresh,
            bg=COLORS["bg_success"],
            fg="white",
            font=FONTS["small"],
            padx=10,
            pady=4,
            tooltip="Refresh all stats and displays",
        ).pack(fill="x", pady=2)

    # ═══ Refresh ═══

    def _refresh(self):
        """Refresh all data displays."""
        self._refresh_memory_stats()
        self._refresh_scoring()
        self._refresh_sessions()
        self._refresh_recommendations()
        self._refresh_level()

        # Auto-refresh every 30s
        self.parent.after(30000, self._refresh)

    def _refresh_memory_stats(self):
        try:
            from engines.memory import get_summary

            s = get_summary()
            self._cards["sessions"].set_value(str(s.get("total_sessions", 0)))
            self._cards["keys"].set_value(f"{s.get('total_keys', 0):,}")
            self._cards["high_scores"].set_value(str(s.get("high_score_count", 0)))
            best = s.get("top_score", 0)
            self._cards["best"].set_value(f"{best:.3f}" if best else "0")
            avg_spd = s.get("avg_speed", 0)
            self._cards["avg_speed"].set_value(f"{avg_spd:,.0f}/s" if avg_spd else "0")
            hrs = s.get("total_duration_hours", 0)
            self._cards["duration"].set_value(f"{hrs:.1f}h" if hrs else "0")
        except Exception:
            pass

    def _refresh_scoring(self):
        try:
            from engines.learning import get_solve_stats, get_weights, confidence_level

            stats = get_solve_stats()
            self._scoring_labels["attempts"].config(text=str(stats["total_attempts"]))
            self._scoring_labels["correct"].config(text=str(stats["total_correct"]))
            self._scoring_labels["success_rate"].config(
                text=f"{stats['success_rate']:.1%}"
            )
            self._scoring_labels["avg_winner"].config(
                text=f"{stats['avg_winner_score']:.3f}"
            )
            self._scoring_labels["best_type"].config(text=stats["best_puzzle_type"])

            conf = confidence_level()
            bars = int(conf * 5)
            bar_str = "\u25a0" * bars + "\u25a1" * (5 - bars)
            self._scoring_labels["confidence"].config(text=f"{bar_str} {conf:.0%}")

            weights = get_weights()
            if weights:
                self._weight_labels["math"].config(
                    text=f"{weights.get('math_weight', 0.4):.0%}"
                )
                self._weight_labels["numer"].config(
                    text=f"{weights.get('numerology_weight', 0.3):.0%}"
                )
                self._weight_labels["learn"].config(
                    text=f"{weights.get('learned_weight', 0.3):.0%}"
                )
        except Exception:
            pass

    def _refresh_sessions(self):
        self._sessions_listbox.delete(0, tk.END)
        try:
            from engines.memory import get_memory

            sessions = get_memory().get("sessions", [])
            for s in sessions[-20:]:
                mode = s.get("mode", "?")
                puzzle = s.get("puzzle", "")
                keys = s.get("keys_tested", 0)
                score = s.get("best_score", 0)
                ts = s.get("timestamp", "")[:16]
                self._sessions_listbox.insert(
                    0, f"{ts}  {mode:<8} P{puzzle:<4} {keys:>8,} keys  best:{score:.3f}"
                )
        except Exception:
            pass

    def _refresh_recommendations(self):
        # Try learner recommendations first, fall back to legacy memory
        try:
            from engines.learner import get_recommendations, get_insights

            recs = get_recommendations()
            insights = get_insights(limit=5)

            parts = []
            if insights:
                parts.append("Recent Insights:")
                parts.extend(f"  \u2022 {i}" for i in insights)
            if recs:
                parts.append("\nRecommendations:")
                parts.extend(f"  \u2022 {r}" for r in recs)

            if parts:
                self.ai_panel.set_result("\n".join(parts))
                return
        except Exception:
            pass

        try:
            from engines.memory import get_recommendations

            recs = get_recommendations()
            if recs:
                text = "\n".join(f"\u2022 {r}" for r in recs)
            else:
                text = "No recommendations yet. Start scanning to build memory."
            self.ai_panel.set_result(text)
        except Exception:
            self.ai_panel.set_result("Memory engine unavailable.")

    def _refresh_level(self):
        """Refresh XP/Level display from learner engine."""
        try:
            from engines.learner import get_level

            level = get_level()
            lvl = level.get("level", 1)
            name = level.get("name", "Novice")
            xp = level.get("xp", 0)
            xp_next = level.get("xp_next")
            caps = level.get("capabilities", [])

            self._level_name_label.config(text=f"Level {lvl} \u2014 {name}")
            xp_text = f"XP: {xp}"
            if xp_next:
                xp_text += f" / {xp_next}"
            self._xp_label.config(text=xp_text)

            # Draw XP bar
            self._xp_bar.delete("all")
            w = self._xp_bar.winfo_width() or 200
            self._xp_bar.create_rectangle(
                0, 0, w, 12, fill=COLORS["bg_input"], outline=""
            )
            if xp_next and xp_next > 0:
                progress = min(1.0, xp / xp_next)
                fill_w = int(w * progress)
                if fill_w > 0:
                    self._xp_bar.create_rectangle(
                        0, 0, fill_w, 12, fill=COLORS["ai_accent"], outline=""
                    )

            if caps:
                self._capabilities_label.config(text=" | ".join(caps))
        except Exception:
            pass

    # ═══ Actions ═══

    def _learn_now(self):
        """Trigger AI learning in a background thread."""
        model = self._model_var.get()
        self._learn_btn.config(state="disabled", text="Learning...")
        self.ai_panel.set_loading(f"AI learning with {model}...")

        def _do_learn():
            try:
                from engines.learner import learn
                from engines.session_manager import get_session_stats
            except ImportError:
                self.parent.after(
                    0,
                    self._handle_learn_result,
                    {
                        "insights": ["Learner engine not available"],
                        "recommendations": [],
                    },
                )
                return

            try:
                session_data = get_session_stats()
            except Exception:
                session_data = {}

            try:
                result = learn(session_data, model=model)
            except Exception as e:
                result = {"insights": [f"Learning failed: {e}"], "recommendations": []}

            self.parent.after(0, self._handle_learn_result, result)

        threading.Thread(target=_do_learn, daemon=True).start()

    def _handle_learn_result(self, result):
        """Handle learn result on main thread."""
        self._learn_btn.config(state="normal", text="Learn Now")

        insights = result.get("insights", [])
        recs = result.get("recommendations", [])

        parts = []
        if insights:
            parts.append("Insights:")
            parts.extend(f"  \u2022 {i}" for i in insights)
        if recs:
            parts.append("\nRecommendations:")
            parts.extend(f"  \u2022 {r}" for r in recs)

        if parts:
            self.ai_panel.set_result("\n".join(parts))
        else:
            self.ai_panel.set_result("No insights generated.")

        self._refresh_level()

    def _recalculate(self):
        try:
            from engines.learning import recalculate_weights

            recalculate_weights()
            self._refresh_scoring()
        except Exception:
            pass

    def _export_csv(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="nps_memory_export.csv",
        )
        if not filepath:
            return

        try:
            from engines.memory import get_memory

            data = get_memory()
            sessions = data.get("sessions", [])

            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                if sessions:
                    writer.writerow(sessions[0].keys())
                    for s in sessions:
                        writer.writerow(s.values())
        except Exception:
            pass

    def _export_vault_csv(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="nps_vault_export.csv",
        )
        if not filepath:
            return
        try:
            from engines.vault import export_csv

            export_csv(filepath)
        except Exception:
            pass

    def _export_vault_json(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="nps_vault_export.json",
        )
        if not filepath:
            return
        try:
            from engines.vault import export_json

            export_json(filepath)
        except Exception:
            pass

    def _flush(self):
        try:
            from engines.memory import flush_to_disk

            flush_to_disk()
        except Exception:
            pass

    def _subscribe_events(self):
        """Subscribe to events for live updates."""
        try:
            from engines import events

            events.subscribe(events.LEVEL_UP, self._on_level_up, gui_root=self.parent)
            events.subscribe(
                events.FINDING_FOUND, self._on_finding, gui_root=self.parent
            )
        except Exception:
            pass

    def _on_level_up(self, data):
        """Handle LEVEL_UP — refresh level display."""
        self._refresh_level()

    def _on_finding(self, data):
        """Handle FINDING_FOUND — refresh stats."""
        self._refresh_memory_stats()
