"""Memory tab — AI Learning Dashboard."""

import csv
import json
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
from gui.theme import COLORS, FONTS
from gui.widgets import StyledButton, StatsCard, AIInsightPanel


class MemoryTab:
    """Displays scan memory, learning stats, recommendations."""

    def __init__(self, parent, app=None):
        self.parent = parent
        self.app = app
        self._build_ui()
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

        StyledButton(
            frame,
            text="Recalculate Weights",
            command=self._recalculate,
            bg=COLORS["bg_button"],
            fg="white",
            font=FONTS["small"],
            padx=10,
            pady=4,
        ).pack(fill="x", pady=2)

        StyledButton(
            frame,
            text="Export CSV",
            command=self._export_csv,
            bg=COLORS["bg_button"],
            fg="white",
            font=FONTS["small"],
            padx=10,
            pady=4,
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
        ).pack(fill="x", pady=2)

    # ═══ Refresh ═══

    def _refresh(self):
        """Refresh all data displays."""
        self._refresh_memory_stats()
        self._refresh_scoring()
        self._refresh_sessions()
        self._refresh_recommendations()

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

    # ═══ Actions ═══

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

    def _flush(self):
        try:
            from engines.memory import flush_to_disk

            flush_to_disk()
        except Exception:
            pass
